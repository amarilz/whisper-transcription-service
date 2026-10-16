
import io
from unittest.mock import MagicMock, patch

import pytest
import re
from fastapi.testclient import TestClient

from app.main import app
from app.version import get_version


@pytest.fixture
def mock_service():
    service = MagicMock()

    service.model_path = "/models/large-v3-turbo.pt"
    service.device = "cpu"

    service.transcribe.return_value = {
        "text": "Faccio una registrazione di prova.",
        "language": "it"
    }

    return service


@pytest.fixture
def client(mock_service):
    with patch(
        "app.main.TranscriptionService",
        return_value=mock_service
    ):
        with TestClient(app) as test_client:
            yield test_client


def test_version_format():
    assert re.fullmatch(
        r"\d+\.\d+\.\d+",
        get_version()
    )


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "model": "large-v3-turbo.pt",
        "device": "cpu",
        "version": get_version()
    }


def test_transcribe_success(client, mock_service):
    response = client.post(
        "/transcribe",
        files={
            "file": (
                "test.mp3",
                io.BytesIO(b"fake audio content"),
                "audio/mpeg"
            )
        }
    )

    assert response.status_code == 200

    assert response.json() == {
        "text": "Faccio una registrazione di prova.",
        "language": "it"
    }

    mock_service.transcribe.assert_called_once()

    kwargs = mock_service.transcribe.call_args.kwargs

    assert kwargs["language"] == "Italian"
    assert kwargs["audio_path"]


def test_transcribe_english(client, mock_service):
    response = client.post(
        "/transcribe?language=English",
        files={
            "file": (
                "test.mp3",
                io.BytesIO(b"fake audio content"),
                "audio/mpeg"
            )
        }
    )

    assert response.status_code == 200

    kwargs = mock_service.transcribe.call_args.kwargs

    assert kwargs["language"] == "English"


def test_transcribe_missing_file(client):
    response = client.post("/transcribe")

    assert response.status_code == 422


def test_transcribe_file_too_large(client, mock_service):
    with patch("app.main.MAX_FILE_SIZE", 10):
        response = client.post(
            "/transcribe",
            files={
                "file": (
                    "large.mp3",
                    io.BytesIO(b"12345678901"),
                    "audio/mpeg"
                )
            }
        )

    assert response.status_code == 413
    mock_service.transcribe.assert_not_called()


def test_transcribe_model_error(client, mock_service):
    mock_service.transcribe.side_effect = RuntimeError(
        "Model execution failed"
    )

    response = client.post(
        "/transcribe",
        files={
            "file": (
                "test.mp3",
                io.BytesIO(b"fake audio content"),
                "audio/mpeg"
            )
        }
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Audio transcription failed"


def test_transcribe_empty_file(client, mock_service):
    response = client.post(
        "/transcribe",
        files={
            "file": (
                "empty.mp3",
                io.BytesIO(b""),
                "audio/mpeg"
            )
        }
    )

    assert response.status_code == 200
    mock_service.transcribe.assert_called_once()
