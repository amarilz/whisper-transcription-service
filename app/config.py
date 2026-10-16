
import os

MODEL_PATH = os.getenv(
    "WHISPER_MODEL_PATH",
    "/models/large-v3-turbo.pt"
)

DEFAULT_LANGUAGE = os.getenv(
    "WHISPER_LANGUAGE",
    "Italian"
)

MAX_FILE_SIZE = 100 * 1024 * 1024
