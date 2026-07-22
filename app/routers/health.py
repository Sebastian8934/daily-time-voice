from fastapi import APIRouter

from app import __version__
from app.config import get_settings
from app.models.schemas import HealthResponse
from app.services.daily_time_client import DailyTimeClient
from app.services.speech import whisper_available

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        version=__version__,
        daily_time_api_url=settings.daily_time_api_url,
        whisper_enabled=whisper_available(),
    )


@router.get("/health/upstream")
async def health_upstream() -> dict:
    client = DailyTimeClient()
    reachable = await client.health_probe()
    return {
        "dailyTimeApi": settings_url(),
        "reachable": reachable,
    }


def settings_url() -> str:
    return get_settings().daily_time_api_url
