
import re
import unicodedata
from pathlib import Path

import pytest

from app.config import MODEL_PATH
from app.transcription_service import TranscriptionService


AUDIO_PATH = Path(__file__).parent / "fixtures" / "test.m4a"
EXPECTED_TEXT = "Questo è un piccolo test"


def normalize_text(text: str) -> str:
    # Confronto case insensitive
    text = text.casefold()

    # Rimuove tutti i caratteri di punteggiatura Unicode
    text = "".join(
        char
        for char in text
        if not unicodedata.category(char).startswith("P")
    )

    # Normalizza spazi, tab e newline
    return re.sub(r"\s+", " ", text).strip()


@pytest.mark.integration
def test_real_audio_transcription():
    assert AUDIO_PATH.is_file(), (
        f"Audio file not found: {AUDIO_PATH}"
    )

    service = TranscriptionService(MODEL_PATH)
    service.load_model()

    result = service.transcribe(
        audio_path=str(AUDIO_PATH),
        language="Italian"
    )

    actual_text = normalize_text(result["text"])
    expected_text = normalize_text(EXPECTED_TEXT)

    assert actual_text == expected_text, (
        f"Expected: {expected_text!r}\n"
        f"Actual:   {actual_text!r}"
    )
