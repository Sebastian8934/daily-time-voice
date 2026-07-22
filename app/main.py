from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.config import get_settings
from app.routers import health, voice

settings = get_settings()

app = FastAPI(
    title="DailyTime Voice API",
    description=(
        "API en Python para controlar DailyTime por voz o texto. "
        "Interpreta comandos en español y llama a la API ASP.NET existente."
    ),
    version=__version__,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(voice.router)


@app.get("/")
async def root() -> dict:
    return {
        "name": "DailyTime Voice API",
        "version": __version__,
        "docs": "/docs",
        "health": "/health",
        "command": "POST /api/voice/command",
    }
