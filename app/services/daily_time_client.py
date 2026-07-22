from __future__ import annotations

from datetime import date
from typing import Any

import httpx

from app.config import get_settings


class DailyTimeApiError(Exception):
    def __init__(self, message: str, status_code: int | None = None, errors: list[str] | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.errors = errors or []


class DailyTimeClient:
    """Cliente HTTP hacia la API ASP.NET de DailyTime."""

    def __init__(self, base_url: str | None = None, timeout: float = 30.0):
        settings = get_settings()
        self.base_url = (base_url or settings.daily_time_api_url).rstrip("/")
        self.timeout = timeout

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(
            timeout=self.timeout,
            verify=False,
            follow_redirects=True,
        ) as client:
            response = await client.request(
                method,
                url,
                params=params,
                json=json,
                headers={"Content-Type": "application/json", "Accept": "application/json"},
            )

        if response.is_redirect:
            location = response.headers.get("location", "")
            raise DailyTimeApiError(
                "DailyTime redirigió la petición ("
                f"{response.status_code}). Usa la URL HTTPS en DAILY_TIME_API_URL"
                + (f" → {location}" if location else ""),
                response.status_code,
            )

        try:
            payload = response.json()
        except ValueError as exc:
            snippet = (response.text or "").strip()[:120]
            raise DailyTimeApiError(
                f"Respuesta inválida de DailyTime ({response.status_code})"
                + (f": {snippet}" if snippet else ""),
                response.status_code,
            ) from exc

        if response.is_error or not payload.get("success", False):
            raise DailyTimeApiError(
                payload.get("message") or f"Error HTTP {response.status_code}",
                response.status_code,
                payload.get("errors"),
            )

        return payload.get("data")

    async def health_probe(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0, verify=False, follow_redirects=True) as client:
                response = await client.get(f"{self.base_url}/swagger/index.html")
                return response.status_code < 500
        except httpx.HTTPError:
            return False

    async def list_tasks(self, work_date: date, to_date: date | None = None) -> list[dict[str, Any]]:
        end = to_date or work_date
        data = await self._request(
            "GET",
            "/api/taskitems",
            params={"fromDate": work_date.isoformat(), "toDate": end.isoformat()},
        )
        return data or []

    async def create_task(
        self,
        *,
        title: str,
        work_date: date,
        status_id: int | None = None,
        category_id: int | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "title": title,
            "workDate": work_date.isoformat(),
            "sortOrder": 0,
            "durationMinutes": 0,
        }
        if status_id is not None:
            body["statusId"] = status_id
        if category_id is not None:
            body["categoryId"] = category_id
        return await self._request("POST", "/api/taskitems", json=body)

    async def update_task(self, task_id: int, body: dict[str, Any]) -> dict[str, Any]:
        return await self._request("PUT", f"/api/taskitems/{task_id}", json=body)

    async def get_task(self, task_id: int) -> dict[str, Any]:
        return await self._request("GET", f"/api/taskitems/{task_id}")

    async def list_notes(self, work_date: date, to_date: date | None = None) -> list[dict[str, Any]]:
        end = to_date or work_date
        data = await self._request(
            "GET",
            "/api/notes",
            params={"fromDate": work_date.isoformat(), "toDate": end.isoformat()},
        )
        return data or []

    async def create_note(
        self,
        *,
        content: str,
        title: str | None = None,
        work_date: date | None = None,
        status_id: int | None = None,
        category_id: int | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "content": content,
            "sortOrder": 0,
            "durationMinutes": 0,
        }
        if title:
            body["title"] = title
        if work_date is not None:
            body["workDate"] = work_date.isoformat()
        if status_id is not None:
            body["statusId"] = status_id
        if category_id is not None:
            body["categoryId"] = category_id
        return await self._request("POST", "/api/notes", json=body)

    async def create_time_entry(
        self,
        *,
        work_date: date,
        duration_minutes: int,
        task_item_id: int | None = None,
        note_id: int | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "workDate": work_date.isoformat(),
            "durationMinutes": duration_minutes,
        }
        if task_item_id is not None:
            body["taskItemId"] = task_item_id
        if note_id is not None:
            body["noteId"] = note_id
        if description:
            body["description"] = description
        return await self._request("POST", "/api/timeentries", json=body)

    async def list_statuses(self, item_type: str | None = None) -> list[dict[str, Any]]:
        params = {"itemType": item_type} if item_type else None
        data = await self._request("GET", "/api/statuses", params=params)
        return data or []

    async def list_categories(self, item_type: str | None = None) -> list[dict[str, Any]]:
        params = {"itemType": item_type} if item_type else None
        data = await self._request("GET", "/api/categories", params=params)
        return data or []

    async def find_task_by_title(self, work_date: date, query: str) -> dict[str, Any] | None:
        tasks = await self.list_tasks(work_date)
        needle = query.strip().lower()
        if not needle:
            return None

        exact = next((t for t in tasks if (t.get("title") or "").lower() == needle), None)
        if exact:
            return exact

        return next(
            (t for t in tasks if needle in (t.get("title") or "").lower()),
            None,
        )
