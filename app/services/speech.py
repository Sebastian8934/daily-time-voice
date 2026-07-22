from __future__ import annotations

import tempfile
from pathlib import Path

from app.config import get_settings


class SpeechServiceError(Exception):
    pass


def whisper_available() -> bool:
    settings = get_settings()
    if not settings.enable_whisper:
        return False
    try:
        import whisper  # noqa: F401

        return True
    except ImportError:
        return False


async def transcribe_audio(file_bytes: bytes, filename: str = "audio.wav") -> tuple[str, str]:
    """Transcribe audio con Whisper local si está habilitado."""
    settings = get_settings()
    if not settings.enable_whisper:
        raise SpeechServiceError(
            "Whisper está desactivado. Envía texto a /api/voice/command "
            "o activa ENABLE_WHISPER=true e instala openai-whisper."
        )

    try:
        import whisper
    except ImportError as exc:
        raise SpeechServiceError(
            "openai-whisper no está instalado. Ejecuta: pip install openai-whisper"
        ) from exc

    suffix = Path(filename).suffix or ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(file_bytes)
        temp_path = Path(tmp.name)

    try:
        model = whisper.load_model("base")
        result = model.transcribe(str(temp_path), language="es")
        transcript = (result.get("text") or "").strip()
        if not transcript:
            raise SpeechServiceError("No se detectó voz en el audio.")
        return transcript, "whisper-base"
    finally:
        temp_path.unlink(missing_ok=True)
