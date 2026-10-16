
import logging
import threading

logger = logging.getLogger("whisper-service")


class TranscriptionService:

    def __init__(self, model_path: str):
        self.model_path = model_path
        self.device = "cpu"
        self.model = None
        self.lock = threading.Lock()

    def load_model(self):
        import torch
        import whisper

        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        logger.info(
            "Loading Whisper model from %s on %s",
            self.model_path,
            self.device
        )

        self.model = whisper.load_model(
            self.model_path,
            device=self.device
        )

        logger.info("Whisper model loaded successfully")

    def transcribe(self, audio_path: str, language: str):
        if self.model is None:
            raise RuntimeError("Whisper model is not loaded")

        with self.lock:
            return self.model.transcribe(
                audio_path,
                language=language,
                task="transcribe",
                fp16=(self.device == "cuda")
            )
