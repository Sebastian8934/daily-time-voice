from __future__ import annotations

from datetime import date

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.config import get_settings
from app.models.schemas import (
    CommandRequest,
    CommandResponse,
    IntentName,
    ParsedIntent,
    TranscribeResponse,
)
from app.services.action_executor import ActionExecutor
from app.services.intent_parser import HELP_TEXT, parse_intent
from app.services.speech import SpeechServiceError, transcribe_audio

router = APIRouter(prefix="/api/voice", tags=["voice"])


def _resolve_work_date(override: date | None) -> date | None:
    settings = get_settings()
    if override:
        return override
    if settings.default_work_date:
        return date.fromisoformat(settings.default_work_date)
    return date.today()


@router.get("/help")
async def help_commands() -> dict:
    return {
        "message": HELP_TEXT.strip(),
        "examples": [
            "crea una tarea llamada revisar informe para mañana",
            "crea una nota que diga comprar leche",
            "muestra las tareas de hoy",
            "completa la tarea revisar informe",
            "registra 30 minutos en la tarea revisar informe",
            "abre el tablero",
            "abre el calendario",
            "ayuda",
        ],
    }


@router.post("/parse", response_model=ParsedIntent)
async def parse_command(body: CommandRequest) -> ParsedIntent:
    """Solo interpreta el texto; no ejecuta nada en DailyTime."""
    return parse_intent(body.text, _resolve_work_date(body.work_date))


@router.post("/command", response_model=CommandResponse)
async def run_command(body: CommandRequest) -> CommandResponse:
    """Interpreta y ejecuta un comando de texto contra la API .NET."""
    intent = parse_intent(body.text, _resolve_work_date(body.work_date))
    executor = ActionExecutor()
    return await executor.execute(intent, dry_run=body.dry_run)


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(audio: UploadFile = File(...)) -> TranscribeResponse:
    """Transcribe audio a texto (requiere ENABLE_WHISPER=true)."""
    data = await audio.read()
    try:
        transcript, engine = await transcribe_audio(data, audio.filename or "audio.wav")
    except SpeechServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return TranscribeResponse(transcript=transcript, engine=engine)


@router.post("/command/audio", response_model=CommandResponse)
async def run_audio_command(
    audio: UploadFile = File(...),
    work_date: date | None = Form(default=None),
    dry_run: bool = Form(default=False),
) -> CommandResponse:
    """Transcribe audio y ejecuta el comando resultante."""
    data = await audio.read()
    try:
        transcript, _engine = await transcribe_audio(data, audio.filename or "audio.wav")
    except SpeechServiceError as exc:
        return CommandResponse(
            success=False,
            transcript="",
            intent=IntentName.UNKNOWN,
            confidence=0.0,
            message=str(exc),
            dry_run=dry_run,
        )

    intent = parse_intent(transcript, _resolve_work_date(work_date))
    executor = ActionExecutor()
    return await executor.execute(intent, dry_run=dry_run)
