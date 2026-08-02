from __future__ import annotations

from datetime import date
from typing import Any
from urllib.parse import urlencode

from app.models.schemas import CommandResponse, IntentName, NavigateTarget, ParsedIntent
from app.services.daily_time_client import DailyTimeApiError, DailyTimeClient
from app.services.intent_parser import HELP_TEXT


class ActionExecutor:
    def __init__(self, client: DailyTimeClient | None = None):
        self.client = client or DailyTimeClient()

    async def execute(
        self,
        intent: ParsedIntent,
        *,
        dry_run: bool = False,
    ) -> CommandResponse:
        handlers = {
            IntentName.HELP: self._help,
            IntentName.NAVIGATE: self._navigate,
            IntentName.LIST_TASKS: self._list_tasks,
            IntentName.LIST_NOTES: self._list_notes,
            IntentName.LIST_PEOPLE: self._list_people,
            IntentName.LIST_PROJECTS: self._list_projects,
            IntentName.LIST_STATUSES: self._list_statuses,
            IntentName.LIST_CATEGORIES: self._list_categories,
            IntentName.CREATE_TASK: self._open_task_form,
            IntentName.CREATE_NOTE: self._open_note_form,
            IntentName.OPEN_TASK_FORM: self._open_task_form,
            IntentName.OPEN_NOTE_FORM: self._open_note_form,
            IntentName.OPEN_PERSON_FORM: self._open_person_form,
            IntentName.CREATE_PERSON: self._open_person_form,
            IntentName.OPEN_PROJECT_FORM: self._open_project_form,
            IntentName.CREATE_PROJECT: self._open_project_form,
            IntentName.OPEN_STATUS_FORM: self._open_status_form,
            IntentName.CREATE_STATUS: self._open_status_form,
            IntentName.OPEN_CATEGORY_FORM: self._open_category_form,
            IntentName.CREATE_CATEGORY: self._open_category_form,
            IntentName.OPEN_VAULT_ACCOUNT_FORM: self._open_vault_account_form,
            IntentName.CREATE_VAULT_ACCOUNT: self._open_vault_account_form,
            IntentName.OPEN_VAULT_PASSWORD_FORM: self._open_vault_password_form,
            IntentName.CREATE_VAULT_PASSWORD: self._open_vault_password_form,
            IntentName.OPEN_CAREER_CATALOG_FORM: self._open_career_catalog_form,
            IntentName.CREATE_CAREER_CATALOG: self._open_career_catalog_form,
            IntentName.OPEN_WORK_EXPERIENCE_FORM: self._open_work_experience_form,
            IntentName.CREATE_WORK_EXPERIENCE: self._open_work_experience_form,
            IntentName.OPEN_JOB_APPLICATION_FORM: self._open_job_application_form,
            IntentName.CREATE_JOB_APPLICATION: self._open_job_application_form,
            IntentName.OPEN_VAULT_SERVICE_FORM: self._open_vault_service_form,
            IntentName.CREATE_VAULT_SERVICE: self._open_vault_service_form,
            IntentName.OPEN_EDIT_TASK_FORM: self._open_edit_task_form,
            IntentName.OPEN_EDIT_NOTE_FORM: self._open_edit_note_form,
            IntentName.OPEN_EDIT_PERSON_FORM: self._open_edit_person_form,
            IntentName.OPEN_EDIT_PROJECT_FORM: self._open_edit_project_form,
            IntentName.OPEN_EDIT_STATUS_FORM: self._open_edit_status_form,
            IntentName.OPEN_EDIT_CATEGORY_FORM: self._open_edit_category_form,
            IntentName.OPEN_EDIT_VAULT_ACCOUNT_FORM: self._open_edit_vault_account_form,
            IntentName.OPEN_EDIT_VAULT_PASSWORD_FORM: self._open_edit_vault_password_form,
            IntentName.OPEN_EDIT_CAREER_CATALOG_FORM: self._open_edit_career_catalog_form,
            IntentName.OPEN_EDIT_WORK_EXPERIENCE_FORM: self._open_edit_work_experience_form,
            IntentName.OPEN_EDIT_JOB_APPLICATION_FORM: self._open_edit_job_application_form,
            IntentName.OPEN_EDIT_VAULT_SERVICE_FORM: self._open_edit_vault_service_form,
            IntentName.LIST_WORK_EXPERIENCES: self._list_work_experiences,
            IntentName.LIST_JOB_APPLICATIONS: self._list_job_applications,
            IntentName.COMPLETE_TASK: self._complete_task,
            IntentName.COMPLETE_NOTE: self._complete_note,
            IntentName.DELETE_TASK: self._delete_task,
            IntentName.DELETE_NOTE: self._delete_note,
            IntentName.DELETE_PERSON: self._delete_person,
            IntentName.DELETE_PROJECT: self._delete_project,
            IntentName.DELETE_STATUS: self._delete_status,
            IntentName.DELETE_CATEGORY: self._delete_category,
            IntentName.DELETE_VAULT_ACCOUNT: self._delete_vault_account,
            IntentName.DELETE_VAULT_PASSWORD: self._delete_vault_password,
            IntentName.DELETE_CAREER_CATALOG: self._delete_career_catalog,
            IntentName.DELETE_WORK_EXPERIENCE: self._delete_work_experience,
            IntentName.DELETE_JOB_APPLICATION: self._delete_job_application,
            IntentName.DELETE_VAULT_SERVICE: self._delete_vault_service,
            IntentName.ADD_TIME: self._add_time,
            IntentName.FILTER_WORKSPACE: self._filter_workspace,
            IntentName.CALENDAR_NAVIGATE: self._calendar_navigate,
            IntentName.UNKNOWN: self._unknown,
        }
        handler = handlers[intent.intent]
        try:
            return await handler(intent, dry_run=dry_run)
        except DailyTimeApiError as exc:
            return CommandResponse(
                success=False,
                transcript=intent.raw_text,
                intent=intent.intent,
                confidence=intent.confidence,
                message=str(exc),
                dry_run=dry_run,
            )

    async def _help(self, intent: ParsedIntent, *, dry_run: bool) -> CommandResponse:
        return CommandResponse(
            success=True,
            transcript=intent.raw_text,
            intent=intent.intent,
            confidence=intent.confidence,
            message=HELP_TEXT.strip(),
            dry_run=dry_run,
        )

    async def _navigate(self, intent: ParsedIntent, *, dry_run: bool) -> CommandResponse:
        target_enum = intent.navigate_to
        target = target_enum.value if target_enum else None
        paths = {
            NavigateTarget.CAREER_CATALOGS: "/career/catalogs",
            NavigateTarget.VAULT_SERVICES: "/vault/services",
            NavigateTarget.CAREER_PORTALS: "/career/portals",
        }
        if target_enum is None:
            path = None
        else:
            path = paths.get(target_enum, f"/{target_enum.value}")
        labels = {
            "board": "tablero",
            "calendar": "calendario",
            "workspace": "informe de tiempo",
            "statuses": "estados",
            "categories": "categorías",
            "people": "personas",
            "projects": "proyectos",
            "vault": "bóveda",
            "day": "día",
            "tasks": "tareas",
            "notes": "notas",
            "experiences": "experiencias",
            "applications": "postulaciones",
            "career-catalogs": "datos reutilizables",
            "career-portals": "portales de ofertas",
            "vault-services": "servicios de bóveda",
        }
        label = labels.get(target or "", target or "destino desconocido")
        return CommandResponse(
            success=True,
            transcript=intent.raw_text,
            intent=intent.intent,
            confidence=intent.confidence,
            message=f"Navegar a {label}." if not dry_run else f"[dry-run] Navegaría a {label}.",
            navigate_to=path,
            data={"route": path},
            dry_run=dry_run,
        )

    async def _list_named(
        self,
        intent: ParsedIntent,
        *,
        dry_run: bool,
        label: str,
        fetch,
        line_fn,
    ) -> CommandResponse:
        if dry_run:
            return CommandResponse(
                success=True,
                transcript=intent.raw_text,
                intent=intent.intent,
                confidence=intent.confidence,
                message=f"[dry-run] Listaría {label}.",
                dry_run=True,
            )

        items = await fetch()
        if not items:
            message = f"No hay {label}."
        else:
            lines = [line_fn(item) for item in items[:20]]
            more = "" if len(items) <= 20 else f"\n… y {len(items) - 20} más."
            message = f"{label.capitalize()} ({len(items)}):\n" + "\n".join(lines) + more

        return CommandResponse(
            success=True,
            transcript=intent.raw_text,
            intent=intent.intent,
            confidence=intent.confidence,
            message=message,
            data=items,
            dry_run=False,
        )

    async def _list_tasks(self, intent: ParsedIntent, *, dry_run: bool) -> CommandResponse:
        work_date = intent.work_date or date.today()
        if dry_run:
            return CommandResponse(
                success=True,
                transcript=intent.raw_text,
                intent=intent.intent,
                confidence=intent.confidence,
                message=f"[dry-run] Listaría tareas del {work_date.isoformat()}.",
                dry_run=True,
            )

        tasks = await self.client.list_tasks(work_date)
        if not tasks:
            message = f"No hay tareas para el {work_date.isoformat()}."
        else:
            lines = [f"- {t.get('title')} (#{t.get('id')})" for t in tasks[:15]]
            more = "" if len(tasks) <= 15 else f"\n… y {len(tasks) - 15} más."
            message = f"Tareas del {work_date.isoformat()} ({len(tasks)}):\n" + "\n".join(lines) + more

        return CommandResponse(
            success=True,
            transcript=intent.raw_text,
            intent=intent.intent,
            confidence=intent.confidence,
            message=message,
            data=tasks,
            dry_run=False,
        )

    async def _list_notes(self, intent: ParsedIntent, *, dry_run: bool) -> CommandResponse:
        work_date = intent.work_date or date.today()
        if dry_run:
            return CommandResponse(
                success=True,
                transcript=intent.raw_text,
                intent=intent.intent,
                confidence=intent.confidence,
                message=f"[dry-run] Listaría notas del {work_date.isoformat()}.",
                dry_run=True,
            )

        notes = await self.client.list_notes(work_date)
        if not notes:
            message = f"No hay notas para el {work_date.isoformat()}."
        else:
            lines = []
            for note in notes[:15]:
                title = note.get("title") or (note.get("content") or "")[:40]
                lines.append(f"- {title} (#{note.get('id')})")
            more = "" if len(notes) <= 15 else f"\n… y {len(notes) - 15} más."
            message = f"Notas del {work_date.isoformat()} ({len(notes)}):\n" + "\n".join(lines) + more

        return CommandResponse(
            success=True,
            transcript=intent.raw_text,
            intent=intent.intent,
            confidence=intent.confidence,
            message=message,
            data=notes,
            dry_run=False,
        )

    async def _list_people(self, intent: ParsedIntent, *, dry_run: bool) -> CommandResponse:
        return await self._list_named(
            intent,
            dry_run=dry_run,
            label="personas",
            fetch=self.client.list_people,
            line_fn=lambda p: f"- {p.get('name')} (#{p.get('id')})",
        )

    async def _list_projects(self, intent: ParsedIntent, *, dry_run: bool) -> CommandResponse:
        return await self._list_named(
            intent,
            dry_run=dry_run,
            label="proyectos",
            fetch=self.client.list_projects,
            line_fn=lambda p: f"- {p.get('name')} (#{p.get('id')})",
        )

    async def _list_statuses(self, intent: ParsedIntent, *, dry_run: bool) -> CommandResponse:
        return await self._list_named(
            intent,
            dry_run=dry_run,
            label="estados",
            fetch=self.client.list_statuses,
            line_fn=lambda s: f"- {s.get('name')} ({s.get('itemType')}) (#{s.get('id')})",
        )

    async def _list_categories(self, intent: ParsedIntent, *, dry_run: bool) -> CommandResponse:
        return await self._list_named(
            intent,
            dry_run=dry_run,
            label="categorías",
            fetch=self.client.list_categories,
            line_fn=lambda c: f"- {c.get('name')} ({c.get('itemType')}) (#{c.get('id')})",
        )

    async def _list_work_experiences(self, intent: ParsedIntent, *, dry_run: bool) -> CommandResponse:
        return await self._list_named(
            intent,
            dry_run=dry_run,
            label="experiencias",
            fetch=self.client.list_work_experiences,
            line_fn=lambda e: (
                f"- {e.get('companyName')} · {e.get('positionName')} (#{e.get('id')})"
            ),
        )

    async def _list_job_applications(self, intent: ParsedIntent, *, dry_run: bool) -> CommandResponse:
        return await self._list_named(
            intent,
            dry_run=dry_run,
            label="postulaciones",
            fetch=self.client.list_job_applications,
            line_fn=lambda a: (
                f"- {a.get('companyName')} · {a.get('positionName')}"
                f" [{a.get('statusName')}] (#{a.get('id')})"
            ),
        )

    async def _open_task_form(self, intent: ParsedIntent, *, dry_run: bool) -> CommandResponse:
        work_date = intent.work_date or date.today()
        draft = {
            "title": intent.title or "",
            "workDate": work_date.isoformat(),
            "startTime": intent.start_time,
            "endTime": intent.end_time,
            "statusName": intent.status_name,
            "categoryName": intent.category_name,
        }
        draft = {key: value for key, value in draft.items() if value}

        if dry_run:
            return CommandResponse(
                success=True,
                transcript=intent.raw_text,
                intent=intent.intent,
                confidence=intent.confidence,
                message=f"[dry-run] Abriría el formulario de tarea con {draft or 'campos vacíos'}.",
                data=draft,
                requires_confirmation=True,
                dry_run=True,
            )

        hint = (
            "Formulario de tarea abierto. Dicta campos como «título …», «categoría …», "
            "«estado …», «fecha mañana» y di «guardar» al terminar."
        )
        if intent.title:
            hint = (
                f"Título «{intent.title}» listo. Sigue dictando categoría, estado u horario, "
                "o di «guardar»."
            )

        return CommandResponse(
            success=True,
            transcript=intent.raw_text,
            intent=IntentName.OPEN_TASK_FORM,
            confidence=intent.confidence,
            message=hint,
            navigate_to="/board",
            data=draft,
            requires_confirmation=True,
            dry_run=False,
        )

    async def _open_note_form(self, intent: ParsedIntent, *, dry_run: bool) -> CommandResponse:
        work_date = intent.work_date or date.today()
        draft = {
            "title": intent.title or "",
            "content": intent.content or "",
            "workDate": work_date.isoformat(),
            "startTime": intent.start_time,
            "endTime": intent.end_time,
            "statusName": intent.status_name,
            "categoryName": intent.category_name,
        }
        draft = {key: value for key, value in draft.items() if value}

        if dry_run:
            return CommandResponse(
                success=True,
                transcript=intent.raw_text,
                intent=intent.intent,
                confidence=intent.confidence,
                message=f"[dry-run] Abriría el formulario de nota con {draft or 'campos vacíos'}.",
                data=draft,
                requires_confirmation=True,
                dry_run=True,
            )

        hint = (
            "Formulario de nota abierto. Dicta «contenido …», «título …», «categoría …» "
            "y di «guardar» al terminar."
        )
        if intent.content:
            hint = "Contenido listo. Sigue dictando título, categoría o estado, o di «guardar»."

        return CommandResponse(
            success=True,
            transcript=intent.raw_text,
            intent=IntentName.OPEN_NOTE_FORM,
            confidence=intent.confidence,
            message=hint,
            navigate_to="/board",
            data=draft,
            requires_confirmation=True,
            dry_run=False,
        )

    def _open_named_form(
        self,
        intent: ParsedIntent,
        *,
        dry_run: bool,
        open_intent: IntentName,
        label: str,
        route: str,
        hint_empty: str,
        draft_extra: dict | None = None,
    ) -> CommandResponse:
        draft = {"name": intent.title or "", **(draft_extra or {})}
        if intent.title:
            draft["title"] = intent.title
        draft = {key: value for key, value in draft.items() if value not in (None, "")}

        if dry_run:
            return CommandResponse(
                success=True,
                transcript=intent.raw_text,
                intent=intent.intent,
                confidence=intent.confidence,
                message=f"[dry-run] Abriría el formulario de {label} con {draft or 'campos vacíos'}.",
                data=draft,
                requires_confirmation=True,
                dry_run=True,
            )

        hint = hint_empty
        if intent.title:
            hint = f"Nombre «{intent.title}» listo. Sigue dictando campos o di «guardar»."

        return CommandResponse(
            success=True,
            transcript=intent.raw_text,
            intent=open_intent,
            confidence=intent.confidence,
            message=hint,
            navigate_to=route,
            data=draft,
            requires_confirmation=True,
            dry_run=False,
        )

    async def _open_person_form(self, intent: ParsedIntent, *, dry_run: bool) -> CommandResponse:
        return self._open_named_form(
            intent,
            dry_run=dry_run,
            open_intent=IntentName.OPEN_PERSON_FORM,
            label="persona",
            route="/people",
            hint_empty="Formulario de persona abierto. Dicta «nombre …», «descripción …» y «guardar».",
        )

    async def _open_project_form(self, intent: ParsedIntent, *, dry_run: bool) -> CommandResponse:
        return self._open_named_form(
            intent,
            dry_run=dry_run,
            open_intent=IntentName.OPEN_PROJECT_FORM,
            label="proyecto",
            route="/projects",
            hint_empty="Formulario de proyecto abierto. Dicta «nombre …», «descripción …» y «guardar».",
        )

    async def _open_status_form(self, intent: ParsedIntent, *, dry_run: bool) -> CommandResponse:
        return self._open_named_form(
            intent,
            dry_run=dry_run,
            open_intent=IntentName.OPEN_STATUS_FORM,
            label="estado",
            route="/statuses",
            hint_empty=(
                "Formulario de estado abierto. Dicta «nombre …», «tipo tarea|nota», "
                "«color rojo» y «guardar»."
            ),
        )

    async def _open_category_form(self, intent: ParsedIntent, *, dry_run: bool) -> CommandResponse:
        return self._open_named_form(
            intent,
            dry_run=dry_run,
            open_intent=IntentName.OPEN_CATEGORY_FORM,
            label="categoría",
            route="/categories",
            hint_empty=(
                "Formulario de categoría abierto. Dicta «nombre …», «tipo tarea|nota» y «guardar»."
            ),
        )

    async def _open_vault_account_form(
        self, intent: ParsedIntent, *, dry_run: bool
    ) -> CommandResponse:
        return self._open_named_form(
            intent,
            dry_run=dry_run,
            open_intent=IntentName.OPEN_VAULT_ACCOUNT_FORM,
            label="cuenta de bóveda",
            route="/vault",
            hint_empty="Formulario de cuenta abierto. Dicta «nombre …» y «guardar».",
        )

    async def _open_vault_password_form(
        self, intent: ParsedIntent, *, dry_run: bool
    ) -> CommandResponse:
        draft = {
            "serviceName": intent.title or "",
            "name": intent.title or "",
        }
        draft = {key: value for key, value in draft.items() if value}

        if dry_run:
            return CommandResponse(
                success=True,
                transcript=intent.raw_text,
                intent=intent.intent,
                confidence=intent.confidence,
                message=f"[dry-run] Abriría el formulario de contraseña con {draft or 'campos vacíos'}.",
                data=draft,
                requires_confirmation=True,
                dry_run=True,
            )

        hint = (
            "Formulario de contraseña abierto. Dicta «servicio …», «usuario …», "
            "«contraseña …» y «guardar»."
        )
        if intent.title:
            hint = f"Servicio «{intent.title}» listo. Dicta usuario y contraseña, o di «guardar»."

        return CommandResponse(
            success=True,
            transcript=intent.raw_text,
            intent=IntentName.OPEN_VAULT_PASSWORD_FORM,
            confidence=intent.confidence,
            message=hint,
            navigate_to="/vault",
            data=draft,
            requires_confirmation=True,
            dry_run=False,
        )

    async def _open_career_catalog_form(
        self, intent: ParsedIntent, *, dry_run: bool
    ) -> CommandResponse:
        kind = (intent.slots or {}).get("catalog_kind") or "companies"
        return self._open_named_form(
            intent,
            dry_run=dry_run,
            open_intent=IntentName.OPEN_CAREER_CATALOG_FORM,
            label=f"dato reutilizable ({kind})",
            route="/career/catalogs",
            hint_empty=(
                "Formulario de dato reutilizable abierto. Dicta «nombre …», "
                "«descripción …» y «guardar»."
            ),
            draft_extra={"catalogKind": kind},
        )

    async def _open_vault_service_form(
        self, intent: ParsedIntent, *, dry_run: bool
    ) -> CommandResponse:
        return self._open_named_form(
            intent,
            dry_run=dry_run,
            open_intent=IntentName.OPEN_VAULT_SERVICE_FORM,
            label="servicio de bóveda",
            route="/vault/services",
            hint_empty="Formulario de servicio abierto. Dicta «nombre …», «url …» y «guardar».",
        )

    def _open_company_hint_form(
        self,
        intent: ParsedIntent,
        *,
        dry_run: bool,
        open_intent: IntentName,
        label: str,
        route: str,
        hint_empty: str,
    ) -> CommandResponse:
        draft: dict[str, Any] = {}
        if intent.title:
            draft["companyName"] = intent.title
            draft["title"] = intent.title

        if dry_run:
            return CommandResponse(
                success=True,
                transcript=intent.raw_text,
                intent=intent.intent,
                confidence=intent.confidence,
                message=f"[dry-run] Abriría el formulario de {label} con {draft or 'campos vacíos'}.",
                data=draft,
                requires_confirmation=True,
                dry_run=True,
            )

        hint = hint_empty
        if intent.title:
            hint = f"Empresa «{intent.title}» lista. Sigue dictando campos o di «guardar»."

        return CommandResponse(
            success=True,
            transcript=intent.raw_text,
            intent=open_intent,
            confidence=intent.confidence,
            message=hint,
            navigate_to=route,
            data=draft,
            requires_confirmation=True,
            dry_run=False,
        )

    async def _open_work_experience_form(
        self, intent: ParsedIntent, *, dry_run: bool
    ) -> CommandResponse:
        return self._open_company_hint_form(
            intent,
            dry_run=dry_run,
            open_intent=IntentName.OPEN_WORK_EXPERIENCE_FORM,
            label="experiencia laboral",
            route="/experiences",
            hint_empty=(
                "Formulario de experiencia abierto. Dicta empresa, cargo y fechas, "
                "luego «guardar»."
            ),
        )

    async def _open_job_application_form(
        self, intent: ParsedIntent, *, dry_run: bool
    ) -> CommandResponse:
        return self._open_company_hint_form(
            intent,
            dry_run=dry_run,
            open_intent=IntentName.OPEN_JOB_APPLICATION_FORM,
            label="postulación",
            route="/applications",
            hint_empty=(
                "Formulario de postulación abierto. Dicta empresa, cargo y estado, "
                "luego «guardar»."
            ),
        )

    def _missing_query(self, intent: ParsedIntent, example: str) -> CommandResponse:
        return CommandResponse(
            success=False,
            transcript=intent.raw_text,
            intent=intent.intent,
            confidence=intent.confidence,
            message=f"Indica el nombre. Ejemplo: {example}",
            dry_run=False,
        )

    async def _open_edit_task_form(self, intent: ParsedIntent, *, dry_run: bool) -> CommandResponse:
        if not intent.task_query:
            return self._missing_query(intent, "edita la tarea revisar informe")
        work_date = intent.work_date or date.today()
        if dry_run:
            return CommandResponse(
                success=True,
                transcript=intent.raw_text,
                intent=intent.intent,
                confidence=intent.confidence,
                message=f"[dry-run] Abriría edición de tarea «{intent.task_query}».",
                requires_confirmation=True,
                dry_run=True,
            )
        task = await self.client.find_task_by_title(work_date, intent.task_query)
        if not task:
            return CommandResponse(
                success=False,
                transcript=intent.raw_text,
                intent=intent.intent,
                confidence=intent.confidence,
                message=f"No encontré la tarea «{intent.task_query}».",
                dry_run=False,
            )
        draft = {
            "id": task.get("id"),
            "title": task.get("title"),
            "workDate": task.get("workDate"),
            "startTime": task.get("startTime"),
            "endTime": task.get("endTime"),
            "statusId": task.get("statusId"),
            "categoryId": task.get("categoryId"),
            "personId": task.get("personId"),
            "projectId": task.get("projectId"),
            "sortOrder": task.get("sortOrder", 0),
            "durationMinutes": task.get("durationMinutes", 0),
            "parentTaskId": task.get("parentTaskId"),
            "isCompleted": task.get("isCompleted", False),
        }
        return CommandResponse(
            success=True,
            transcript=intent.raw_text,
            intent=intent.intent,
            confidence=intent.confidence,
            message=f"Editando tarea «{task.get('title')}». Dicta cambios y di «guardar».",
            navigate_to="/board",
            data=draft,
            requires_confirmation=True,
            dry_run=False,
        )

    async def _open_edit_note_form(self, intent: ParsedIntent, *, dry_run: bool) -> CommandResponse:
        query = intent.note_query or intent.task_query
        if not query:
            return self._missing_query(intent, "edita la nota comprar leche")
        work_date = intent.work_date or date.today()
        if dry_run:
            return CommandResponse(
                success=True,
                transcript=intent.raw_text,
                intent=intent.intent,
                confidence=intent.confidence,
                message=f"[dry-run] Abriría edición de nota «{query}».",
                requires_confirmation=True,
                dry_run=True,
            )
        note = await self.client.find_note_by_title(work_date, query)
        if not note:
            return CommandResponse(
                success=False,
                transcript=intent.raw_text,
                intent=intent.intent,
                confidence=intent.confidence,
                message=f"No encontré la nota «{query}».",
                dry_run=False,
            )
        draft = {
            "id": note.get("id"),
            "title": note.get("title"),
            "content": note.get("content"),
            "workDate": note.get("workDate"),
            "startTime": note.get("startTime"),
            "endTime": note.get("endTime"),
            "statusId": note.get("statusId"),
            "categoryId": note.get("categoryId"),
            "personId": note.get("personId"),
            "projectId": note.get("projectId"),
            "sortOrder": note.get("sortOrder", 0),
            "durationMinutes": note.get("durationMinutes", 0),
            "parentNoteId": note.get("parentNoteId"),
        }
        return CommandResponse(
            success=True,
            transcript=intent.raw_text,
            intent=intent.intent,
            confidence=intent.confidence,
            message=(
                f"Editando nota «{note.get('title') or (note.get('content') or '')[:40]}». "
                "Dicta cambios y di «guardar»."
            ),
            navigate_to="/board",
            data=draft,
            requires_confirmation=True,
            dry_run=False,
        )

    async def _open_edit_catalog(
        self,
        intent: ParsedIntent,
        *,
        dry_run: bool,
        label: str,
        route: str,
        find,
        draft_fn,
        example: str,
    ) -> CommandResponse:
        if not intent.task_query:
            return self._missing_query(intent, example)
        if dry_run:
            return CommandResponse(
                success=True,
                transcript=intent.raw_text,
                intent=intent.intent,
                confidence=intent.confidence,
                message=f"[dry-run] Abriría edición de {label} «{intent.task_query}».",
                requires_confirmation=True,
                dry_run=True,
            )
        entity = await find(intent.task_query)
        if not entity:
            return CommandResponse(
                success=False,
                transcript=intent.raw_text,
                intent=intent.intent,
                confidence=intent.confidence,
                message=f"No encontré {label} «{intent.task_query}».",
                dry_run=False,
            )
        draft = draft_fn(entity)
        return CommandResponse(
            success=True,
            transcript=intent.raw_text,
            intent=intent.intent,
            confidence=intent.confidence,
            message=f"Editando {label} «{draft.get('name') or draft.get('serviceName')}». Dicta cambios y di «guardar».",
            navigate_to=route,
            data=draft,
            requires_confirmation=True,
            dry_run=False,
        )

    async def _open_edit_person_form(self, intent: ParsedIntent, *, dry_run: bool) -> CommandResponse:
        return await self._open_edit_catalog(
            intent,
            dry_run=dry_run,
            label="persona",
            route="/people",
            find=self.client.find_person_by_name,
            example="edita la persona Juan",
            draft_fn=lambda p: {
                "id": p.get("id"),
                "name": p.get("name"),
                "description": p.get("description") or "",
                "isActive": p.get("isActive", True),
            },
        )

    async def _open_edit_project_form(self, intent: ParsedIntent, *, dry_run: bool) -> CommandResponse:
        return await self._open_edit_catalog(
            intent,
            dry_run=dry_run,
            label="proyecto",
            route="/projects",
            find=self.client.find_project_by_name,
            example="edita el proyecto rediseño",
            draft_fn=lambda p: {
                "id": p.get("id"),
                "name": p.get("name"),
                "description": p.get("description") or "",
                "isActive": p.get("isActive", True),
            },
        )

    async def _open_edit_status_form(self, intent: ParsedIntent, *, dry_run: bool) -> CommandResponse:
        return await self._open_edit_catalog(
            intent,
            dry_run=dry_run,
            label="estado",
            route="/statuses",
            find=self.client.find_status_by_name,
            example="edita el estado en progreso",
            draft_fn=lambda s: {
                "id": s.get("id"),
                "name": s.get("name"),
                "description": s.get("description") or "",
                "color": s.get("color") or "#64748B",
                "isFinal": s.get("isFinal", False),
                "itemType": s.get("itemType") or "task",
            },
        )

    async def _open_edit_category_form(self, intent: ParsedIntent, *, dry_run: bool) -> CommandResponse:
        return await self._open_edit_catalog(
            intent,
            dry_run=dry_run,
            label="categoría",
            route="/categories",
            find=self.client.find_category_by_name,
            example="edita la categoría trabajo",
            draft_fn=lambda c: {
                "id": c.get("id"),
                "name": c.get("name"),
                "description": c.get("description") or "",
                "itemType": c.get("itemType") or "task",
                "isActive": c.get("isActive", True),
            },
        )

    async def _open_edit_vault_account_form(
        self, intent: ParsedIntent, *, dry_run: bool
    ) -> CommandResponse:
        return await self._open_edit_catalog(
            intent,
            dry_run=dry_run,
            label="cuenta de bóveda",
            route="/vault",
            find=self.client.find_vault_account_by_name,
            example="edita la cuenta principal",
            draft_fn=lambda a: {
                "id": a.get("id"),
                "name": a.get("name"),
                "description": a.get("description") or "",
            },
        )

    async def _open_edit_vault_password_form(
        self, intent: ParsedIntent, *, dry_run: bool
    ) -> CommandResponse:
        return await self._open_edit_catalog(
            intent,
            dry_run=dry_run,
            label="contraseña",
            route="/vault",
            find=self.client.find_vault_password_by_service,
            example="edita la contraseña Gmail",
            draft_fn=lambda p: {
                "id": p.get("id"),
                "accountId": p.get("accountId"),
                "serviceName": p.get("serviceName"),
                "username": p.get("username") or "",
                "password": p.get("password") or "",
                "url": p.get("url") or "",
                "notes": p.get("notes") or "",
                "tags": p.get("tags") or "",
            },
        )

    async def _open_edit_career_catalog_form(
        self, intent: ParsedIntent, *, dry_run: bool
    ) -> CommandResponse:
        kind = (intent.slots or {}).get("catalog_kind")
        if not kind:
            return self._missing_query(intent, "edita la empresa Google")
        return await self._open_edit_catalog(
            intent,
            dry_run=dry_run,
            label=f"dato reutilizable ({kind})",
            route="/career/catalogs",
            find=lambda q: self.client.find_career_catalog_by_name(kind, q),
            example="edita la empresa Google",
            draft_fn=lambda c: {
                "id": c.get("id"),
                "name": c.get("name"),
                "description": c.get("description") or "",
                "color": c.get("color"),
                "catalogKind": kind,
            },
        )

    async def _open_edit_vault_service_form(
        self, intent: ParsedIntent, *, dry_run: bool
    ) -> CommandResponse:
        return await self._open_edit_catalog(
            intent,
            dry_run=dry_run,
            label="servicio de bóveda",
            route="/vault/services",
            find=self.client.find_vault_service_by_name,
            example="edita el servicio GitHub",
            draft_fn=lambda s: {
                "id": s.get("id"),
                "name": s.get("name"),
                "url": s.get("url") or "",
                "notes": s.get("notes") or "",
                "isActive": s.get("isActive", True),
            },
        )

    async def _open_edit_work_experience_form(
        self, intent: ParsedIntent, *, dry_run: bool
    ) -> CommandResponse:
        if not intent.task_query:
            return self._missing_query(intent, "edita la experiencia Microsoft")
        if dry_run:
            return CommandResponse(
                success=True,
                transcript=intent.raw_text,
                intent=intent.intent,
                confidence=intent.confidence,
                message=f"[dry-run] Abriría edición de experiencia «{intent.task_query}».",
                requires_confirmation=True,
                dry_run=True,
            )
        entity = await self.client.find_work_experience(intent.task_query)
        if not entity:
            return CommandResponse(
                success=False,
                transcript=intent.raw_text,
                intent=intent.intent,
                confidence=intent.confidence,
                message=f"No encontré experiencia «{intent.task_query}».",
                dry_run=False,
            )
        draft = {
            "id": entity.get("id"),
            "companyId": entity.get("companyId"),
            "companyName": entity.get("companyName"),
            "positionId": entity.get("positionId"),
            "positionName": entity.get("positionName"),
            "locationId": entity.get("locationId"),
            "fieldId": entity.get("fieldId"),
            "startDate": entity.get("startDate"),
            "endDate": entity.get("endDate"),
            "isCurrent": entity.get("isCurrent", False),
            "summary": entity.get("summary") or "",
            "achievements": entity.get("achievements") or "",
            "technologyIds": entity.get("technologyIds") or [],
        }
        label = f"{entity.get('companyName')} · {entity.get('positionName')}"
        return CommandResponse(
            success=True,
            transcript=intent.raw_text,
            intent=intent.intent,
            confidence=intent.confidence,
            message=f"Editando experiencia «{label}». Dicta cambios y di «guardar».",
            navigate_to="/experiences",
            data=draft,
            requires_confirmation=True,
            dry_run=False,
        )

    async def _open_edit_job_application_form(
        self, intent: ParsedIntent, *, dry_run: bool
    ) -> CommandResponse:
        if not intent.task_query:
            return self._missing_query(intent, "edita la postulación Google")
        if dry_run:
            return CommandResponse(
                success=True,
                transcript=intent.raw_text,
                intent=intent.intent,
                confidence=intent.confidence,
                message=f"[dry-run] Abriría edición de postulación «{intent.task_query}».",
                requires_confirmation=True,
                dry_run=True,
            )
        entity = await self.client.find_job_application(intent.task_query)
        if not entity:
            return CommandResponse(
                success=False,
                transcript=intent.raw_text,
                intent=intent.intent,
                confidence=intent.confidence,
                message=f"No encontré postulación «{intent.task_query}».",
                dry_run=False,
            )
        draft = {
            "id": entity.get("id"),
            "companyId": entity.get("companyId"),
            "companyName": entity.get("companyName"),
            "positionId": entity.get("positionId"),
            "positionName": entity.get("positionName"),
            "locationId": entity.get("locationId"),
            "fieldId": entity.get("fieldId"),
            "statusId": entity.get("statusId"),
            "statusName": entity.get("statusName"),
            "appliedAt": entity.get("appliedAt"),
            "url": entity.get("url") or "",
            "contact": entity.get("contact") or "",
            "notes": entity.get("notes") or "",
            "workExperienceId": entity.get("workExperienceId"),
        }
        label = f"{entity.get('companyName')} · {entity.get('positionName')}"
        return CommandResponse(
            success=True,
            transcript=intent.raw_text,
            intent=intent.intent,
            confidence=intent.confidence,
            message=f"Editando postulación «{label}». Dicta cambios y di «guardar».",
            navigate_to="/applications",
            data=draft,
            requires_confirmation=True,
            dry_run=False,
        )

    async def _complete_task(self, intent: ParsedIntent, *, dry_run: bool) -> CommandResponse:
        if not intent.task_query:
            return CommandResponse(
                success=False,
                transcript=intent.raw_text,
                intent=intent.intent,
                confidence=intent.confidence,
                message="Indica qué tarea completar. Ejemplo: completa la tarea revisar informe",
                dry_run=dry_run,
            )

        work_date = intent.work_date or date.today()
        if dry_run:
            return CommandResponse(
                success=True,
                transcript=intent.raw_text,
                intent=intent.intent,
                confidence=intent.confidence,
                message=f"[dry-run] Buscaría y completaría «{intent.task_query}».",
                dry_run=True,
            )

        task = await self.client.find_task_by_title(work_date, intent.task_query)
        if not task:
            return CommandResponse(
                success=False,
                transcript=intent.raw_text,
                intent=intent.intent,
                confidence=intent.confidence,
                message=f"No encontré una tarea que coincida con «{intent.task_query}».",
                dry_run=False,
            )

        body = {
            "title": task.get("title"),
            "workDate": task.get("workDate"),
            "startTime": task.get("startTime"),
            "endTime": task.get("endTime"),
            "parentTaskId": task.get("parentTaskId"),
            "statusId": task.get("statusId"),
            "categoryId": task.get("categoryId"),
            "personId": task.get("personId"),
            "projectId": task.get("projectId"),
            "sortOrder": task.get("sortOrder", 0),
            "durationMinutes": task.get("durationMinutes", 0),
            "isCompleted": True,
        }

        statuses = await self.client.list_statuses("task")
        final_status = next((s for s in statuses if s.get("isFinal")), None)
        if final_status:
            body["statusId"] = final_status["id"]

        updated = await self.client.update_task(int(task["id"]), body)
        return CommandResponse(
            success=True,
            transcript=intent.raw_text,
            intent=intent.intent,
            confidence=intent.confidence,
            message=f"Tarea completada: «{updated.get('title')}».",
            navigate_to="/board",
            data=updated,
            dry_run=False,
        )

    async def _complete_note(self, intent: ParsedIntent, *, dry_run: bool) -> CommandResponse:
        query = intent.note_query or intent.task_query
        if not query:
            return CommandResponse(
                success=False,
                transcript=intent.raw_text,
                intent=intent.intent,
                confidence=intent.confidence,
                message="Indica qué nota completar. Ejemplo: completa la nota comprar leche",
                dry_run=dry_run,
            )

        work_date = intent.work_date or date.today()
        if dry_run:
            return CommandResponse(
                success=True,
                transcript=intent.raw_text,
                intent=intent.intent,
                confidence=intent.confidence,
                message=f"[dry-run] Completaría la nota «{query}».",
                dry_run=True,
            )

        note = await self.client.find_note_by_title(work_date, query)
        if not note:
            return CommandResponse(
                success=False,
                transcript=intent.raw_text,
                intent=intent.intent,
                confidence=intent.confidence,
                message=f"No encontré una nota que coincida con «{query}».",
                dry_run=False,
            )

        body = {
            "title": note.get("title"),
            "content": note.get("content"),
            "workDate": note.get("workDate"),
            "startTime": note.get("startTime"),
            "endTime": note.get("endTime"),
            "parentNoteId": note.get("parentNoteId"),
            "statusId": note.get("statusId"),
            "categoryId": note.get("categoryId"),
            "personId": note.get("personId"),
            "projectId": note.get("projectId"),
            "sortOrder": note.get("sortOrder", 0),
            "durationMinutes": note.get("durationMinutes", 0),
        }

        statuses = await self.client.list_statuses("note")
        final_status = next((s for s in statuses if s.get("isFinal")), None)
        if final_status:
            body["statusId"] = final_status["id"]
        else:
            return CommandResponse(
                success=False,
                transcript=intent.raw_text,
                intent=intent.intent,
                confidence=intent.confidence,
                message="No hay un estado final configurado para notas.",
                dry_run=False,
            )

        updated = await self.client.update_note(int(note["id"]), body)
        label = updated.get("title") or (updated.get("content") or "")[:40]
        return CommandResponse(
            success=True,
            transcript=intent.raw_text,
            intent=intent.intent,
            confidence=intent.confidence,
            message=f"Nota completada: «{label}».",
            navigate_to="/board",
            data=updated,
            dry_run=False,
        )

    async def _delete_by_query(
        self,
        intent: ParsedIntent,
        *,
        dry_run: bool,
        label: str,
        query: str | None,
        example: str,
        find,
        delete,
        name_fn,
        route: str,
    ) -> CommandResponse:
        if not query:
            return self._missing_query(intent, example)
        if dry_run:
            return CommandResponse(
                success=True,
                transcript=intent.raw_text,
                intent=intent.intent,
                confidence=intent.confidence,
                message=f"[dry-run] Eliminaría {label} «{query}».",
                dry_run=True,
            )
        entity = await find(query)
        if not entity:
            return CommandResponse(
                success=False,
                transcript=intent.raw_text,
                intent=intent.intent,
                confidence=intent.confidence,
                message=f"No encontré {label} «{query}».",
                dry_run=False,
            )
        name = name_fn(entity)
        await delete(int(entity["id"]))
        return CommandResponse(
            success=True,
            transcript=intent.raw_text,
            intent=intent.intent,
            confidence=intent.confidence,
            message=f"{label.capitalize()} eliminad{'a' if label.endswith('a') else 'o'}: «{name}».",
            navigate_to=route,
            data={"id": entity.get("id"), "name": name},
            dry_run=False,
        )

    async def _delete_task(self, intent: ParsedIntent, *, dry_run: bool) -> CommandResponse:
        work_date = intent.work_date or date.today()
        return await self._delete_by_query(
            intent,
            dry_run=dry_run,
            label="tarea",
            query=intent.task_query,
            example="elimina la tarea revisar informe",
            find=lambda q: self.client.find_task_by_title(work_date, q),
            delete=self.client.delete_task,
            name_fn=lambda t: t.get("title"),
            route="/board",
        )

    async def _delete_note(self, intent: ParsedIntent, *, dry_run: bool) -> CommandResponse:
        work_date = intent.work_date or date.today()
        query = intent.note_query or intent.task_query
        return await self._delete_by_query(
            intent,
            dry_run=dry_run,
            label="nota",
            query=query,
            example="borra la nota comprar leche",
            find=lambda q: self.client.find_note_by_title(work_date, q),
            delete=self.client.delete_note,
            name_fn=lambda n: n.get("title") or (n.get("content") or "")[:40],
            route="/board",
        )

    async def _delete_person(self, intent: ParsedIntent, *, dry_run: bool) -> CommandResponse:
        return await self._delete_by_query(
            intent,
            dry_run=dry_run,
            label="persona",
            query=intent.task_query,
            example="elimina la persona Juan",
            find=self.client.find_person_by_name,
            delete=self.client.delete_person,
            name_fn=lambda p: p.get("name"),
            route="/people",
        )

    async def _delete_project(self, intent: ParsedIntent, *, dry_run: bool) -> CommandResponse:
        return await self._delete_by_query(
            intent,
            dry_run=dry_run,
            label="proyecto",
            query=intent.task_query,
            example="elimina el proyecto rediseño",
            find=self.client.find_project_by_name,
            delete=self.client.delete_project,
            name_fn=lambda p: p.get("name"),
            route="/projects",
        )

    async def _delete_status(self, intent: ParsedIntent, *, dry_run: bool) -> CommandResponse:
        return await self._delete_by_query(
            intent,
            dry_run=dry_run,
            label="estado",
            query=intent.task_query,
            example="elimina el estado pendiente",
            find=self.client.find_status_by_name,
            delete=self.client.delete_status,
            name_fn=lambda s: s.get("name"),
            route="/statuses",
        )

    async def _delete_category(self, intent: ParsedIntent, *, dry_run: bool) -> CommandResponse:
        return await self._delete_by_query(
            intent,
            dry_run=dry_run,
            label="categoría",
            query=intent.task_query,
            example="elimina la categoría trabajo",
            find=self.client.find_category_by_name,
            delete=self.client.delete_category,
            name_fn=lambda c: c.get("name"),
            route="/categories",
        )

    async def _delete_vault_account(self, intent: ParsedIntent, *, dry_run: bool) -> CommandResponse:
        return await self._delete_by_query(
            intent,
            dry_run=dry_run,
            label="cuenta",
            query=intent.task_query,
            example="elimina la cuenta principal",
            find=self.client.find_vault_account_by_name,
            delete=self.client.delete_vault_account,
            name_fn=lambda a: a.get("name"),
            route="/vault",
        )

    async def _delete_vault_password(self, intent: ParsedIntent, *, dry_run: bool) -> CommandResponse:
        return await self._delete_by_query(
            intent,
            dry_run=dry_run,
            label="contraseña",
            query=intent.task_query,
            example="elimina la contraseña Gmail",
            find=self.client.find_vault_password_by_service,
            delete=self.client.delete_vault_password,
            name_fn=lambda p: p.get("serviceName"),
            route="/vault",
        )

    async def _delete_career_catalog(self, intent: ParsedIntent, *, dry_run: bool) -> CommandResponse:
        kind = (intent.slots or {}).get("catalog_kind")
        if not kind:
            return self._missing_query(intent, "elimina la empresa Google")
        return await self._delete_by_query(
            intent,
            dry_run=dry_run,
            label="dato reutilizable",
            query=intent.task_query,
            example="elimina la empresa Google",
            find=lambda q: self.client.find_career_catalog_by_name(kind, q),
            delete=lambda item_id: self.client.delete_career_catalog(kind, item_id),
            name_fn=lambda c: c.get("name"),
            route="/career/catalogs",
        )

    async def _delete_vault_service(self, intent: ParsedIntent, *, dry_run: bool) -> CommandResponse:
        return await self._delete_by_query(
            intent,
            dry_run=dry_run,
            label="servicio",
            query=intent.task_query,
            example="elimina el servicio GitHub",
            find=self.client.find_vault_service_by_name,
            delete=self.client.delete_vault_service,
            name_fn=lambda s: s.get("name"),
            route="/vault/services",
        )

    async def _delete_work_experience(self, intent: ParsedIntent, *, dry_run: bool) -> CommandResponse:
        return await self._delete_by_query(
            intent,
            dry_run=dry_run,
            label="experiencia",
            query=intent.task_query,
            example="elimina la experiencia Microsoft",
            find=self.client.find_work_experience,
            delete=self.client.delete_work_experience,
            name_fn=lambda e: f"{e.get('companyName')} · {e.get('positionName')}",
            route="/experiences",
        )

    async def _delete_job_application(self, intent: ParsedIntent, *, dry_run: bool) -> CommandResponse:
        return await self._delete_by_query(
            intent,
            dry_run=dry_run,
            label="postulación",
            query=intent.task_query,
            example="elimina la postulación Google",
            find=self.client.find_job_application,
            delete=self.client.delete_job_application,
            name_fn=lambda a: f"{a.get('companyName')} · {a.get('positionName')}",
            route="/applications",
        )

    async def _add_time(self, intent: ParsedIntent, *, dry_run: bool) -> CommandResponse:
        if not intent.duration_minutes or intent.duration_minutes <= 0:
            return CommandResponse(
                success=False,
                transcript=intent.raw_text,
                intent=intent.intent,
                confidence=intent.confidence,
                message="Indica la duración. Ejemplo: registra 30 minutos en la tarea revisar informe",
                dry_run=dry_run,
            )

        work_date = intent.work_date or date.today()
        if dry_run:
            target = ""
            if intent.note_query:
                target = f" en la nota «{intent.note_query}»"
            elif intent.task_query:
                target = f" en la tarea «{intent.task_query}»"
            return CommandResponse(
                success=True,
                transcript=intent.raw_text,
                intent=intent.intent,
                confidence=intent.confidence,
                message=f"[dry-run] Registraría {intent.duration_minutes} min{target}.",
                dry_run=True,
            )

        task_id = None
        note_id = None
        target_label = ""

        if intent.note_query:
            note = await self.client.find_note_by_title(work_date, intent.note_query)
            if not note:
                return CommandResponse(
                    success=False,
                    transcript=intent.raw_text,
                    intent=intent.intent,
                    confidence=intent.confidence,
                    message=f"No encontré la nota «{intent.note_query}» para registrar tiempo.",
                    dry_run=False,
                )
            note_id = int(note["id"])
            target_label = f" en «{intent.note_query}»"
        elif intent.task_query:
            task = await self.client.find_task_by_title(work_date, intent.task_query)
            if not task:
                return CommandResponse(
                    success=False,
                    transcript=intent.raw_text,
                    intent=intent.intent,
                    confidence=intent.confidence,
                    message=f"No encontré la tarea «{intent.task_query}» para registrar tiempo.",
                    dry_run=False,
                )
            task_id = int(task["id"])
            target_label = f" en «{intent.task_query}»"

        created = await self.client.create_time_entry(
            work_date=work_date,
            duration_minutes=intent.duration_minutes,
            task_item_id=task_id,
            note_id=note_id,
            description=intent.raw_text,
        )
        return CommandResponse(
            success=True,
            transcript=intent.raw_text,
            intent=intent.intent,
            confidence=intent.confidence,
            message=f"Registrados {intent.duration_minutes} minutos{target_label}.",
            navigate_to="/workspace",
            data=created,
            dry_run=False,
        )

    async def _filter_workspace(self, intent: ParsedIntent, *, dry_run: bool) -> CommandResponse:
        slots = intent.slots or {}
        if slots.get("clear"):
            path = "/workspace?person=all&project=all"
            return CommandResponse(
                success=True,
                transcript=intent.raw_text,
                intent=intent.intent,
                confidence=intent.confidence,
                message="Filtros del informe limpiados." if not dry_run else "[dry-run] Limpiaría filtros.",
                navigate_to=path,
                data={"personId": "all", "projectId": "all", "clear": True},
                dry_run=dry_run,
            )

        person_id: Any = "all"
        project_id: Any = "all"
        parts: list[str] = []

        person_name = slots.get("person_name")
        project_name = slots.get("project_name")

        if person_name:
            if dry_run:
                parts.append(f"persona «{person_name}»")
            else:
                person = await self.client.find_person_by_name(person_name)
                if not person:
                    return CommandResponse(
                        success=False,
                        transcript=intent.raw_text,
                        intent=intent.intent,
                        confidence=intent.confidence,
                        message=f"No encontré la persona «{person_name}».",
                        dry_run=False,
                    )
                person_id = int(person["id"])
                parts.append(f"persona «{person.get('name')}»")

        if project_name:
            if dry_run:
                parts.append(f"proyecto «{project_name}»")
            else:
                project = await self.client.find_project_by_name(project_name)
                if not project:
                    return CommandResponse(
                        success=False,
                        transcript=intent.raw_text,
                        intent=intent.intent,
                        confidence=intent.confidence,
                        message=f"No encontré el proyecto «{project_name}».",
                        dry_run=False,
                    )
                project_id = int(project["id"])
                parts.append(f"proyecto «{project.get('name')}»")

        query = urlencode({"person": person_id, "project": project_id})
        path = f"/workspace?{query}"
        label = " y ".join(parts) if parts else "sin filtros"
        return CommandResponse(
            success=True,
            transcript=intent.raw_text,
            intent=intent.intent,
            confidence=intent.confidence,
            message=(
                f"Informe filtrado por {label}."
                if not dry_run
                else f"[dry-run] Filtraría informe por {label}."
            ),
            navigate_to=path,
            data={"personId": person_id, "projectId": project_id},
            dry_run=dry_run,
        )

    async def _calendar_navigate(self, intent: ParsedIntent, *, dry_run: bool) -> CommandResponse:
        slots = intent.slots or {}
        action = slots.get("action") or "today"
        mode = slots.get("mode")
        unit = slots.get("unit")
        labels = {
            "today": "hoy",
            "prev": "periodo anterior",
            "next": "periodo siguiente",
            "set_mode": f"vista {mode}" if mode else "vista",
        }
        message = f"Calendario: {labels.get(action, action)}."
        if dry_run:
            message = f"[dry-run] {message}"
        return CommandResponse(
            success=True,
            transcript=intent.raw_text,
            intent=intent.intent,
            confidence=intent.confidence,
            message=message,
            navigate_to="/calendar",
            data={"action": action, "mode": mode, "unit": unit},
            dry_run=dry_run,
        )

    async def _unknown(self, intent: ParsedIntent, *, dry_run: bool) -> CommandResponse:
        return CommandResponse(
            success=False,
            transcript=intent.raw_text,
            intent=intent.intent,
            confidence=intent.confidence,
            message="No entendí el comando. Di «ayuda» para ver ejemplos.",
            dry_run=dry_run,
        )
