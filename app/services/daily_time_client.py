from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import httpx

from app.config import get_settings


class DailyTimeApiError(Exception):
    def __init__(self, message: str, status_code: int | None = None, errors: list[str] | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.errors = errors or []


def _match_by_name(items: list[dict[str, Any]], query: str, *keys: str) -> dict[str, Any] | None:
    needle = query.strip().lower()
    if not needle:
        return None

    def label(item: dict[str, Any]) -> str:
        for key in keys:
            value = item.get(key)
            if value:
                return str(value).lower()
        return ""

    exact = next((item for item in items if label(item) == needle), None)
    if exact:
        return exact
    return next((item for item in items if needle in label(item)), None)


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

    async def list_tasks_around(self, work_date: date, days: int = 45) -> list[dict[str, Any]]:
        start = work_date - timedelta(days=days)
        end = work_date + timedelta(days=days)
        return await self.list_tasks(start, end)

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

    async def delete_task(self, task_id: int) -> Any:
        return await self._request("DELETE", f"/api/taskitems/{task_id}")

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

    async def list_notes_around(self, work_date: date, days: int = 45) -> list[dict[str, Any]]:
        start = work_date - timedelta(days=days)
        end = work_date + timedelta(days=days)
        return await self.list_notes(start, end)

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

    async def update_note(self, note_id: int, body: dict[str, Any]) -> dict[str, Any]:
        return await self._request("PUT", f"/api/notes/{note_id}", json=body)

    async def delete_note(self, note_id: int) -> Any:
        return await self._request("DELETE", f"/api/notes/{note_id}")

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

    async def list_people(self, only_active: bool | None = None) -> list[dict[str, Any]]:
        params = {"onlyActive": str(only_active).lower()} if only_active is not None else None
        data = await self._request("GET", "/api/people", params=params)
        return data or []

    async def list_projects(self, only_active: bool | None = None) -> list[dict[str, Any]]:
        params = {"onlyActive": str(only_active).lower()} if only_active is not None else None
        data = await self._request("GET", "/api/projects", params=params)
        return data or []

    async def delete_person(self, person_id: int) -> Any:
        return await self._request("DELETE", f"/api/people/{person_id}")

    async def delete_project(self, project_id: int) -> Any:
        return await self._request("DELETE", f"/api/projects/{project_id}")

    async def delete_status(self, status_id: int) -> Any:
        return await self._request("DELETE", f"/api/statuses/{status_id}")

    async def delete_category(self, category_id: int) -> Any:
        return await self._request("DELETE", f"/api/categories/{category_id}")

    async def list_vault_accounts(self) -> list[dict[str, Any]]:
        data = await self._request("GET", "/api/vault/accounts")
        return data or []

    async def list_vault_passwords(self, account_id: int) -> list[dict[str, Any]]:
        data = await self._request("GET", f"/api/vault/accounts/{account_id}/passwords")
        return data or []

    async def delete_vault_account(self, account_id: int) -> Any:
        return await self._request("DELETE", f"/api/vault/accounts/{account_id}")

    async def delete_vault_password(self, password_id: int) -> Any:
        return await self._request("DELETE", f"/api/vault/passwords/{password_id}")

    async def find_task_by_title(self, work_date: date, query: str) -> dict[str, Any] | None:
        tasks = await self.list_tasks_around(work_date)
        return _match_by_name(tasks, query, "title")

    async def find_note_by_title(self, work_date: date, query: str) -> dict[str, Any] | None:
        notes = await self.list_notes_around(work_date)
        needle = query.strip().lower()
        if not needle:
            return None

        exact_title = next(
            (n for n in notes if (n.get("title") or "").lower() == needle),
            None,
        )
        if exact_title:
            return exact_title

        partial = next(
            (
                n
                for n in notes
                if needle in (n.get("title") or "").lower()
                or needle in (n.get("content") or "").lower()
            ),
            None,
        )
        return partial

    async def find_person_by_name(self, query: str) -> dict[str, Any] | None:
        return _match_by_name(await self.list_people(), query, "name")

    async def find_project_by_name(self, query: str) -> dict[str, Any] | None:
        return _match_by_name(await self.list_projects(), query, "name")

    async def find_status_by_name(self, query: str) -> dict[str, Any] | None:
        return _match_by_name(await self.list_statuses(), query, "name")

    async def find_category_by_name(self, query: str) -> dict[str, Any] | None:
        return _match_by_name(await self.list_categories(), query, "name")

    async def find_vault_account_by_name(self, query: str) -> dict[str, Any] | None:
        return _match_by_name(await self.list_vault_accounts(), query, "name")

    async def find_vault_password_by_service(self, query: str) -> dict[str, Any] | None:
        accounts = await self.list_vault_accounts()
        for account in accounts:
            passwords = await self.list_vault_passwords(int(account["id"]))
            match = _match_by_name(passwords, query, "serviceName", "username")
            if match:
                match = {**match, "accountId": account["id"], "accountName": account.get("name")}
                return match
        return None

    async def list_career_catalog(
        self, kind: str, only_active: bool | None = True
    ) -> list[dict[str, Any]]:
        params = {"onlyActive": str(only_active).lower()} if only_active is not None else None
        data = await self._request("GET", f"/api/career/{kind}", params=params)
        return data or []

    async def delete_career_catalog(self, kind: str, catalog_id: int) -> Any:
        return await self._request("DELETE", f"/api/career/{kind}/{catalog_id}")

    async def find_career_catalog_by_name(self, kind: str, query: str) -> dict[str, Any] | None:
        return _match_by_name(await self.list_career_catalog(kind), query, "name")

    async def list_vault_services(self, only_active: bool | None = True) -> list[dict[str, Any]]:
        params = {"onlyActive": str(only_active).lower()} if only_active is not None else None
        data = await self._request("GET", "/api/vault/services", params=params)
        return data or []

    async def delete_vault_service(self, service_id: int) -> Any:
        return await self._request("DELETE", f"/api/vault/services/{service_id}")

    async def find_vault_service_by_name(self, query: str) -> dict[str, Any] | None:
        return _match_by_name(await self.list_vault_services(), query, "name")

    async def list_work_experiences(self) -> list[dict[str, Any]]:
        data = await self._request("GET", "/api/work-experiences")
        return data or []

    async def delete_work_experience(self, experience_id: int) -> Any:
        return await self._request("DELETE", f"/api/work-experiences/{experience_id}")

    async def find_work_experience(self, query: str) -> dict[str, Any] | None:
        needle = query.strip().lower()
        if not needle:
            return None
        items = await self.list_work_experiences()

        def labels(item: dict[str, Any]) -> list[str]:
            company = str(item.get("companyName") or "").lower()
            position = str(item.get("positionName") or "").lower()
            combo = f"{company} {position}".strip()
            return [value for value in (company, position, combo) if value]

        exact = next(
            (item for item in items if any(needle == label for label in labels(item))),
            None,
        )
        if exact:
            return exact
        return next(
            (item for item in items if any(needle in label for label in labels(item))),
            None,
        )

    async def list_job_applications(self) -> list[dict[str, Any]]:
        data = await self._request("GET", "/api/job-applications")
        return data or []

    async def delete_job_application(self, application_id: int) -> Any:
        return await self._request("DELETE", f"/api/job-applications/{application_id}")

    async def find_job_application(self, query: str) -> dict[str, Any] | None:
        needle = query.strip().lower()
        if not needle:
            return None
        items = await self.list_job_applications()

        def labels(item: dict[str, Any]) -> list[str]:
            company = str(item.get("companyName") or "").lower()
            position = str(item.get("positionName") or "").lower()
            combo = f"{company} {position}".strip()
            return [value for value in (company, position, combo) if value]

        exact = next(
            (item for item in items if any(needle == label for label in labels(item))),
            None,
        )
        if exact:
            return exact
        return next(
            (item for item in items if any(needle in label for label in labels(item))),
            None,
        )
