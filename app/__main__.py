"""Punto de entrada: python -m app  ó  uvicorn app.main:app --reload"""

import uvicorn

from app.config import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.voice_api_host,
        port=settings.voice_api_port,
        reload=True,
    )


if __name__ == "__main__":
    main()
