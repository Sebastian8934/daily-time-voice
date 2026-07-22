from __future__ import annotations

from datetime import date

from app.models.schemas import CommandResponse, IntentName, ParsedIntent
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
            IntentName.CREATE_TASK: self._open_task_form,
            IntentName.CREATE_NOTE: self._open_note_form,
            IntentName.OPEN_TASK_FORM: self._open_task_form,
            IntentName.OPEN_NOTE_FORM: self._open_note_form,
            IntentName.COMPLETE_TASK: self._complete_task,
            IntentName.ADD_TIME: self._add_time,
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
        target = intent.navigate_to.value if intent.navigate_to else None
        path = f"/{target}" if target else None
        labels = {
            "board": "tablero",
            "calendar": "calendario",
            "workspace": "informe de tiempo",
            "statuses": "estados",
            "categories": "categorías",
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
            hint = (
                f"Contenido listo. Sigue dictando título, categoría o estado, o di «guardar»."
            )

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
                message=f"No encontré una tarea que coincida con «{intent.task_query}» el {work_date.isoformat()}.",
                dry_run=False,
            )

        # Mantener campos requeridos del update
        body = {
            "title": task.get("title"),
            "workDate": task.get("workDate"),
            "startTime": task.get("startTime"),
            "endTime": task.get("endTime"),
            "parentTaskId": task.get("parentTaskId"),
            "statusId": task.get("statusId"),
            "categoryId": task.get("categoryId"),
            "sortOrder": task.get("sortOrder", 0),
            "durationMinutes": task.get("durationMinutes", 0),
            "isCompleted": True,
        }

        # Si hay estados, preferir uno final
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
            return CommandResponse(
                success=True,
                transcript=intent.raw_text,
                intent=intent.intent,
                confidence=intent.confidence,
                message=(
                    f"[dry-run] Registraría {intent.duration_minutes} min"
                    + (f" en «{intent.task_query}»" if intent.task_query else "")
                    + "."
                ),
                dry_run=True,
            )

        task_id = None
        if intent.task_query:
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

        created = await self.client.create_time_entry(
            work_date=work_date,
            duration_minutes=intent.duration_minutes,
            task_item_id=task_id,
            description=intent.raw_text,
        )
        target = f" en «{intent.task_query}»" if intent.task_query else ""
        return CommandResponse(
            success=True,
            transcript=intent.raw_text,
            intent=intent.intent,
            confidence=intent.confidence,
            message=f"Registrados {intent.duration_minutes} minutos{target}.",
            navigate_to="/workspace",
            data=created,
            dry_run=False,
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
