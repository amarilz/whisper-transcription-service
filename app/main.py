
import os
import time
import logging
import tempfile

from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Request

from app.config import MODEL_PATH, DEFAULT_LANGUAGE, MAX_FILE_SIZE
from app.transcription_service import TranscriptionService
from app.version import get_version

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("whisper-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    service = TranscriptionService(MODEL_PATH)
    service.load_model()

    app.state.transcription_service = service

    try:
        yield
    finally:
        app.state.transcription_service = None
        logger.info("Whisper service stopped")


app = FastAPI(
    title="Local Whisper Turbo API",
    version=get_version(),
    lifespan=lifespan
)


@app.get("/health")
def health(request: Request):
    service = request.app.state.transcription_service

    return {
        "status": "ok",
        "model": os.path.basename(service.model_path),
        "device": service.device,
        "version": app.version
    }


@app.post("/transcribe")
def transcribe(
    request: Request,
    file: UploadFile = File(...),
    language: str = Query(default=DEFAULT_LANGUAGE)
):
    start_time = time.perf_counter()
    temp_path = None
    file_size = 0

    try:
        suffix = os.path.splitext(
            file.filename or ""
        )[1] or ".audio"

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix
        ) as temp:
            temp_path = temp.name

            while chunk := file.file.read(1024 * 1024):
                file_size += len(chunk)

                if file_size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail="Audio file exceeds maximum size of 100 MB"
                    )

                temp.write(chunk)

        service = request.app.state.transcription_service

        result = service.transcribe(
            audio_path=temp_path,
            language=language
        )

        text = result["text"].strip()
        elapsed = time.perf_counter() - start_time

        logger.info(
            "Transcription completed | filename=%s | size=%.2f MB | duration=%.2fs | language=%s | text=%s",
            file.filename,
            file_size / (1024 * 1024),
            elapsed,
            result["language"],
            text
        )

        return {
            "text": text,
            "language": result["language"]
        }

    except HTTPException:
        raise

    except Exception:
        logger.exception(
            "Transcription failed | filename=%s",
            file.filename
        )

        raise HTTPException(
            status_code=500,
            detail="Audio transcription failed"
        )

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
