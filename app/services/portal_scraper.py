"""Skeleton de captura de portales con Playwright.

Instalar cuando se active el worker:
  pip install playwright
  playwright install chromium

Uso previsto: leer JobPortal desde la API .NET y recorrer URL + ScrapeConfig.
"""

from __future__ import annotations

from typing import Any


async def scrape_portal(portal: dict[str, Any]) -> dict[str, Any]:
    """Abre el portal y extrae ofertas. Requiere Playwright instalado."""
    try:
        from playwright.async_api import async_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Playwright no está instalado. Ejecuta: pip install playwright && playwright install chromium"
        ) from exc

    url = portal.get("url") or ""
    if not url:
        raise ValueError("El portal no tiene URL.")

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        title = await page.title()
        await browser.close()

    return {
        "portalId": portal.get("id"),
        "portalName": portal.get("name"),
        "pageTitle": title,
        "offers": [],
        "status": "smoke_ok",
        "message": "Conexión Playwright OK. Falta mapear selectores de ofertas.",
    }
