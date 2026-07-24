from __future__ import annotations

import re
import unicodedata
from datetime import date, timedelta

from app.models.schemas import IntentName, NavigateTarget, ParsedIntent


def _normalize(text: str) -> str:
    text = text.strip().lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = re.sub(r"\s+", " ", text)
    return text


def _parse_relative_date(text: str, today: date) -> date | None:
    if re.search(r"\bhoy\b", text):
        return today
    if re.search(r"\bmanana\b", text):
        return today + timedelta(days=1)
    if re.search(r"\bayer\b", text):
        return today - timedelta(days=1)

    match = re.search(
        r"\b(\d{1,2})[\/\-](\d{1,2})(?:[\/\-](\d{2,4}))?\b",
        text,
    )
    if match:
        day = int(match.group(1))
        month = int(match.group(2))
        year = int(match.group(3)) if match.group(3) else today.year
        if year < 100:
            year += 2000
        try:
            return date(year, month, day)
        except ValueError:
            return None
    return None


def _extract_duration_minutes(text: str) -> int | None:
    match = re.search(r"(\d+)\s*(horas?|hrs?|h)\b", text)
    if match:
        return int(match.group(1)) * 60

    match = re.search(r"(\d+)\s*(minutos?|mins?|min)\b", text)
    if match:
        return int(match.group(1))

    match = re.search(r"(\d+)\s*y\s*media\s*(horas?|hrs?|h)?", text)
    if match:
        return int(match.group(1)) * 60 + 30

    return None


def _strip_prefixes(text: str, patterns: list[str]) -> str:
    for pattern in patterns:
        cleaned = re.sub(pattern, "", text, count=1).strip(" .,;:-")
        if cleaned != text:
            return cleaned
    return text


def _clean_query(text: str) -> str:
    text = re.sub(r"\b(hoy|manana|ayer)\b", "", text).strip(" .,;:-")
    return text


def _career_catalog_kind(text: str) -> str | None:
    """Detect career catalog kind from speech. Application-status before bare estado."""
    if re.search(r"\bestados?\s+de\s+(postulacion|solicitud)\b", text):
        return "application-statuses"
    if re.search(r"\bempresas?\b", text):
        return "companies"
    if re.search(r"\b(cargos?|puestos?)\b", text):
        return "positions"
    if re.search(r"\bubicaciones?\b", text):
        return "locations"
    if re.search(r"\btecnologias?\b", text):
        return "technologies"
    # Navigate phrases for career catalogs — not a field kind
    if re.search(r"\bcatalogos?\s+(de\s+)?carrera\b", text) or "datos reutilizables" in text:
        return None
    if re.search(r"\bcarreras?\b", text) or re.search(r"\barea profesional\b", text):
        return "fields"
    return None


_CAREER_KIND_LABEL = (
    r"(estados?\s+de\s+(postulacion|solicitud)|empresas?|cargos?|puestos?|"
    r"ubicaciones?|tecnologias?|carreras?|area profesional)"
)


NAV_MAP: list[tuple[re.Pattern[str], NavigateTarget]] = [
    (re.compile(r"\b(datos reutilizables|catalogos? de carrera|catalogos? carrera)\b"), NavigateTarget.CAREER_CATALOGS),
    (re.compile(r"\bservicios?\s+de\s+(la\s+)?boveda\b"), NavigateTarget.VAULT_SERVICES),
    (re.compile(r"\bexperiencias?(?:\s+laborales?)?\b"), NavigateTarget.EXPERIENCES),
    (re.compile(r"\b(postulaciones?|solicitudes?)\b"), NavigateTarget.APPLICATIONS),
    (re.compile(r"\b(tablero|board)\b"), NavigateTarget.BOARD),
    (re.compile(r"\b(calendario|calendar)\b"), NavigateTarget.CALENDAR),
    (re.compile(r"\b(informe|workspace|tiempo|reporte)\b"), NavigateTarget.WORKSPACE),
    (re.compile(r"\b(estados?)\b"), NavigateTarget.STATUSES),
    (re.compile(r"\b(categorias?)\b"), NavigateTarget.CATEGORIES),
    (re.compile(r"\b(personas?|gente)\b"), NavigateTarget.PEOPLE),
    (re.compile(r"\b(proyectos?)\b"), NavigateTarget.PROJECTS),
    (re.compile(r"\b(boveda|vault|credenciales?)\b"), NavigateTarget.VAULT),
    (re.compile(r"\b(dia|day)\b"), NavigateTarget.DAY),
    (re.compile(r"\b(tareas?)\b"), NavigateTarget.TASKS),
    (re.compile(r"\b(notas?)\b"), NavigateTarget.NOTES),
]


NOTE_OPEN_PREFIXES = [
    r"^(abre|abrir|muestra|mostrar)\s+(el\s+)?(formulario\s+de\s+)?(nueva\s+)?(nota|notas)\s*",
    r"^(crea|crear|agrega|agregar)\s+(una\s+)?(nueva\s+)?nota\s*(que\s+diga|con\s+texto|con\s+contenido|titulada|llamada)?\s*",
    r"^nueva\s+nota\s*",
    r"^nota\s*",
]

TASK_OPEN_PREFIXES = [
    r"^(abre|abrir|muestra|mostrar)\s+(el\s+)?(formulario\s+de\s+)?(nueva\s+)?(tarea|tareas)\s*",
    r"^(crea|crear|agrega|agregar)\s+(una\s+)?(nueva\s+)?tarea\s*(llamada|con\s+nombre|titulada)?\s*",
    r"^nueva\s+tarea\s*",
    r"^tarea\s*",
]

PERSON_OPEN_PREFIXES = [
    r"^(abre|abrir)\s+(el\s+)?(formulario\s+de\s+)?(nueva\s+)?persona\s*",
    r"^(crea|crear|agrega|agregar)\s+(una\s+)?(nueva\s+)?persona\s*(llamada|con\s+nombre|titulada)?\s*",
    r"^nueva\s+persona\s*",
]

PROJECT_OPEN_PREFIXES = [
    r"^(abre|abrir)\s+(el\s+)?(formulario\s+de\s+)?(nuevo\s+)?proyecto\s*",
    r"^(crea|crear|agrega|agregar)\s+(un\s+)?(nuevo\s+)?proyecto\s*(llamado|con\s+nombre|titulado)?\s*",
    r"^nuevo\s+proyecto\s*",
]

STATUS_OPEN_PREFIXES = [
    r"^(abre|abrir)\s+(el\s+)?(formulario\s+de\s+)?(nuevo\s+)?estado\s*",
    r"^(crea|crear|agrega|agregar)\s+(un\s+)?(nuevo\s+)?estado\s*(llamado|con\s+nombre|titulado)?\s*",
    r"^nuevo\s+estado\s*",
]

CATEGORY_OPEN_PREFIXES = [
    r"^(abre|abrir)\s+(el\s+)?(formulario\s+de\s+)?(nueva\s+)?categoria\s*",
    r"^(crea|crear|agrega|agregar)\s+(una\s+)?(nueva\s+)?categoria\s*(llamada|con\s+nombre|titulada)?\s*",
    r"^nueva\s+categoria\s*",
]

VAULT_ACCOUNT_OPEN_PREFIXES = [
    r"^(abre|abrir)\s+(el\s+)?(formulario\s+de\s+)?(nueva\s+)?cuenta(\s+de\s+boveda)?\s*",
    r"^(crea|crear|agrega|agregar)\s+(una\s+)?(nueva\s+)?cuenta(\s+de\s+(la\s+)?boveda)?\s*(llamada|con\s+nombre)?\s*",
    r"^nueva\s+cuenta(\s+de\s+(la\s+)?boveda)?\s*",
]

VAULT_PASSWORD_OPEN_PREFIXES = [
    r"^(abre|abrir)\s+(el\s+)?(formulario\s+de\s+)?(nueva\s+)?(contrasena|credencial)\s*",
    r"^(crea|crear|agrega|agregar|guarda|guardar)\s+(una\s+)?(nueva\s+)?(contrasena|credencial)\s*(llamada|para|de)?\s*",
    r"^nueva\s+(contrasena|credencial)\s*",
]

CAREER_CATALOG_OPEN_PREFIXES = [
    r"^(abre|abrir)\s+(el\s+)?(formulario\s+de\s+)?(nueva?\s+|nuevo\s+)?",
    r"^(crea|crear|agrega|agregar)\s+(una?\s+|un\s+)?(nueva?\s+|nuevo\s+)?",
    r"^(nueva|nuevo)\s+",
]

WORK_EXPERIENCE_OPEN_PREFIXES = [
    r"^(abre|abrir)\s+(el\s+)?(formulario\s+de\s+)?(nueva\s+)?experiencia(\s+laboral)?\s*",
    r"^(crea|crear|agrega|agregar)\s+(una\s+)?(nueva\s+)?experiencia(\s+laboral)?\s*(en|de|llamada)?\s*",
    r"^nueva\s+experiencia(\s+laboral)?\s*",
]

JOB_APPLICATION_OPEN_PREFIXES = [
    r"^(abre|abrir)\s+(el\s+)?(formulario\s+de\s+)?(nueva\s+)?(postulacion|solicitud)\s*",
    r"^(crea|crear|agrega|agregar)\s+(una\s+)?(nueva\s+)?(postulacion|solicitud)\s*(en|de|llamada|para)?\s*",
    r"^nueva\s+(postulacion|solicitud)\s*",
]

VAULT_SERVICE_OPEN_PREFIXES = [
    r"^(abre|abrir)\s+(el\s+)?(formulario\s+de\s+)?(nuevo\s+)?servicio(\s+de\s+(la\s+)?boveda)?\s*",
    r"^(crea|crear|agrega|agregar)\s+(un\s+)?(nuevo\s+)?servicio(\s+de\s+(la\s+)?boveda)?\s*(llamado|con\s+nombre)?\s*",
    r"^nuevo\s+servicio(\s+de\s+(la\s+)?boveda)?\s*",
]

EDIT_PREFIXES = [
    r"^(edita|editar|modifica|modificar|abre|abrir)\s+(el\s+)?(formulario\s+(de\s+)?)?(de\s+)?",
    r"^(edita|editar|modifica|modificar)\s+",
]

DELETE_PREFIXES = [
    r"^(elimina|eliminar|borra|borrar|quita|quitar)\s+(la\s+|el\s+|las\s+|los\s+)?",
]


def parse_intent(raw_text: str, default_work_date: date | None = None) -> ParsedIntent:
    """Parser determinista de comandos en español (sin LLM)."""
    today = default_work_date or date.today()
    raw = raw_text.strip()
    text = _normalize(raw)
    work_date = _parse_relative_date(text, today) or today
    duration = _extract_duration_minutes(text)

    if re.search(r"\b(ayuda|help|comandos|manual|que puedes hacer)\b", text):
        return ParsedIntent(
            intent=IntentName.HELP,
            confidence=0.99,
            raw_text=raw,
            work_date=work_date,
        )

    # Calendario: antes de navegar genérico
    calendar = _parse_calendar(text, work_date, raw)
    if calendar:
        return calendar

    # Filtros del informe
    workspace_filter = _parse_workspace_filter(text, work_date, raw)
    if workspace_filter:
        return workspace_filter

    # Completar nota (antes que completar tarea)
    if re.search(r"\b(completa|completar|marca|marcar|termina|terminar)\b.*\bnota\b", text):
        query = _strip_prefixes(
            text,
            [
                r"^(completa|completar|marca|marcar|termina|terminar)\s+(la\s+)?(nota\s+)?(como\s+completada\s+)?",
                r"^(marca|marcar)\s+(como\s+)?(completada|completa|hecha)\s+(la\s+)?(nota\s+)?",
            ],
        )
        query = _clean_query(query)
        return ParsedIntent(
            intent=IntentName.COMPLETE_NOTE,
            confidence=0.9 if query else 0.5,
            note_query=query or None,
            work_date=work_date,
            raw_text=raw,
        )

    # Eliminar
    delete_intent = _parse_delete(text, work_date, raw)
    if delete_intent:
        return delete_intent

    # Editar / abrir formulario de edición
    edit_intent = _parse_edit(text, work_date, raw)
    if edit_intent:
        return edit_intent

    # Catálogo de carrera (antes de estado genérico / navegar)
    career_kind = _career_catalog_kind(text)
    if career_kind and (
        re.search(r"\b(nueva|nuevo|crea|crear|agrega|agregar)\b", text)
        or re.search(r"\b(abre|abrir)\b.*\bformulario\b", text)
    ):
        name = _strip_prefixes(text, CAREER_CATALOG_OPEN_PREFIXES)
        name = re.sub(
            rf"^{_CAREER_KIND_LABEL}\s*(llamad[oa]|con\s+nombre|titulad[oa])?\s*",
            "",
            name,
        ).strip(" .,;:-")
        intent = (
            IntentName.OPEN_CAREER_CATALOG_FORM if not name else IntentName.CREATE_CAREER_CATALOG
        )
        return ParsedIntent(
            intent=intent,
            confidence=0.93 if name else 0.9,
            title=name or None,
            work_date=work_date,
            raw_text=raw,
            slots={"catalog_kind": career_kind},
        )

    # Experiencia laboral
    if (
        re.search(r"\b(nueva|nuevo|crea|crear|agrega|agregar)\b.*\bexperiencia\b", text)
        or re.search(r"\b(abre|abrir)\b.*\bformulario\b.*\bexperiencia\b", text)
        or text in {"experiencia", "nueva experiencia", "crear experiencia", "experiencia laboral"}
    ):
        title = _strip_prefixes(text, WORK_EXPERIENCE_OPEN_PREFIXES).strip(" .,;:-")
        intent = (
            IntentName.OPEN_WORK_EXPERIENCE_FORM if not title else IntentName.CREATE_WORK_EXPERIENCE
        )
        return ParsedIntent(
            intent=intent,
            confidence=0.93 if title else 0.9,
            title=title or None,
            work_date=work_date,
            raw_text=raw,
        )

    # Postulación / solicitud
    if (
        re.search(r"\b(nueva|nuevo|crea|crear|agrega|agregar)\b.*\b(postulacion|solicitud)\b", text)
        or re.search(r"\b(abre|abrir)\b.*\bformulario\b.*\b(postulacion|solicitud)\b", text)
        or text
        in {
            "postulacion",
            "solicitud",
            "nueva postulacion",
            "nueva solicitud",
            "crear postulacion",
            "crear solicitud",
        }
    ):
        title = _strip_prefixes(text, JOB_APPLICATION_OPEN_PREFIXES).strip(" .,;:-")
        intent = (
            IntentName.OPEN_JOB_APPLICATION_FORM if not title else IntentName.CREATE_JOB_APPLICATION
        )
        return ParsedIntent(
            intent=intent,
            confidence=0.93 if title else 0.9,
            title=title or None,
            work_date=work_date,
            raw_text=raw,
        )

    # Servicio de bóveda
    if (
        re.search(r"\b(nueva|nuevo|crea|crear|agrega|agregar)\b.*\bservicio\b", text)
        or re.search(r"\b(abre|abrir)\b.*\bformulario\b.*\bservicio\b", text)
        or text
        in {
            "servicio",
            "nuevo servicio",
            "crear servicio",
            "nuevo servicio de boveda",
            "servicio de boveda",
        }
    ):
        name = _strip_prefixes(text, VAULT_SERVICE_OPEN_PREFIXES).strip(" .,;:-")
        intent = IntentName.OPEN_VAULT_SERVICE_FORM if not name else IntentName.CREATE_VAULT_SERVICE
        return ParsedIntent(
            intent=intent,
            confidence=0.92 if name else 0.9,
            title=name or None,
            work_date=work_date,
            raw_text=raw,
        )

    # Catálogos / bóveda: crear (antes de navegar)
    if (
        re.search(r"\b(nueva|nuevo|crea|crear|agrega|agregar)\b.*\bpersona\b", text)
        or re.search(r"\b(abre|abrir)\b.*\bformulario\b.*\bpersona\b", text)
        or text in {"persona", "nueva persona", "crear persona"}
    ):
        name = _strip_prefixes(text, PERSON_OPEN_PREFIXES).strip(" .,;:-")
        intent = IntentName.OPEN_PERSON_FORM if not name else IntentName.CREATE_PERSON
        return ParsedIntent(
            intent=intent,
            confidence=0.93 if name else 0.9,
            title=name or None,
            work_date=work_date,
            raw_text=raw,
        )

    if (
        re.search(r"\b(nueva|nuevo|crea|crear|agrega|agregar)\b.*\bproyecto\b", text)
        or re.search(r"\b(abre|abrir)\b.*\bformulario\b.*\bproyecto\b", text)
        or text in {"proyecto", "nuevo proyecto", "crear proyecto"}
    ):
        name = _strip_prefixes(text, PROJECT_OPEN_PREFIXES).strip(" .,;:-")
        intent = IntentName.OPEN_PROJECT_FORM if not name else IntentName.CREATE_PROJECT
        return ParsedIntent(
            intent=intent,
            confidence=0.93 if name else 0.9,
            title=name or None,
            work_date=work_date,
            raw_text=raw,
        )

    if (
        re.search(r"\b(nueva|nuevo|crea|crear|agrega|agregar)\b.*\bestado\b", text)
        or re.search(r"\b(abre|abrir)\b.*\bformulario\b.*\bestado\b", text)
        or text in {"estado", "nuevo estado", "crear estado"}
    ):
        name = _strip_prefixes(text, STATUS_OPEN_PREFIXES).strip(" .,;:-")
        intent = IntentName.OPEN_STATUS_FORM if not name else IntentName.CREATE_STATUS
        return ParsedIntent(
            intent=intent,
            confidence=0.93 if name else 0.9,
            title=name or None,
            work_date=work_date,
            raw_text=raw,
        )

    if (
        re.search(r"\b(nueva|nuevo|crea|crear|agrega|agregar)\b.*\bcategoria\b", text)
        or re.search(r"\b(abre|abrir)\b.*\bformulario\b.*\bcategoria\b", text)
        or text in {"categoria", "nueva categoria", "crear categoria"}
    ):
        name = _strip_prefixes(text, CATEGORY_OPEN_PREFIXES).strip(" .,;:-")
        intent = IntentName.OPEN_CATEGORY_FORM if not name else IntentName.CREATE_CATEGORY
        return ParsedIntent(
            intent=intent,
            confidence=0.93 if name else 0.9,
            title=name or None,
            work_date=work_date,
            raw_text=raw,
        )

    if (
        re.search(r"\b(nueva|nuevo|crea|crear|agrega|agregar)\b.*\bcuenta\b.*\b(boveda)?\b", text)
        or re.search(r"\b(abre|abrir)\b.*\bformulario\b.*\bcuenta\b", text)
        or text in {"nueva cuenta", "nueva cuenta de boveda", "crear cuenta boveda"}
    ):
        name = _strip_prefixes(text, VAULT_ACCOUNT_OPEN_PREFIXES).strip(" .,;:-")
        intent = (
            IntentName.OPEN_VAULT_ACCOUNT_FORM if not name else IntentName.CREATE_VAULT_ACCOUNT
        )
        return ParsedIntent(
            intent=intent,
            confidence=0.92 if name else 0.9,
            title=name or None,
            work_date=work_date,
            raw_text=raw,
        )

    if (
        re.search(r"\b(nueva|nuevo|crea|crear|agrega|agregar|guarda|guardar)\b.*\b(contrasena|credencial)\b", text)
        or re.search(r"\b(abre|abrir)\b.*\bformulario\b.*\b(contrasena|credencial)\b", text)
        or text in {"contrasena", "credencial", "nueva contrasena", "nueva credencial"}
    ):
        name = _strip_prefixes(text, VAULT_PASSWORD_OPEN_PREFIXES).strip(" .,;:-")
        intent = (
            IntentName.OPEN_VAULT_PASSWORD_FORM if not name else IntentName.CREATE_VAULT_PASSWORD
        )
        return ParsedIntent(
            intent=intent,
            confidence=0.92 if name else 0.9,
            title=name or None,
            work_date=work_date,
            raw_text=raw,
        )

    # Listar catálogos (antes de navegar con "muestra personas")
    list_intent = _parse_list(text, work_date, raw)
    if list_intent:
        return list_intent

    nav_action = re.compile(r"\b(abre|abrir|ir|ve|navega|muestra|mostrar|ve a|ir a)\b")
    nav_action_strict = re.compile(r"\b(abre|abrir|ir|ve|navega|ve a|ir a)\b")
    for pattern, target in NAV_MAP:
        action = (
            nav_action_strict
            if target in {NavigateTarget.TASKS, NavigateTarget.NOTES}
            else nav_action
        )
        if action.search(text) and pattern.search(text):
            return ParsedIntent(
                intent=IntentName.NAVIGATE,
                confidence=0.95,
                navigate_to=target,
                work_date=work_date,
                raw_text=raw,
            )
        if target in {NavigateTarget.TASKS, NavigateTarget.NOTES}:
            continue
        if pattern.fullmatch(text.strip()):
            return ParsedIntent(
                intent=IntentName.NAVIGATE,
                confidence=0.9,
                navigate_to=target,
                work_date=work_date,
                raw_text=raw,
            )

    # "servicios" solo con abre/ir (no fullmatch del término suelto)
    if nav_action_strict.search(text) and re.search(r"\bservicios?\b", text):
        return ParsedIntent(
            intent=IntentName.NAVIGATE,
            confidence=0.95,
            navigate_to=NavigateTarget.VAULT_SERVICES,
            work_date=work_date,
            raw_text=raw,
        )

    if re.search(r"\b(completa|completar|marca|marcar|termina|terminar)\b.*\b(tarea)?\b", text):
        query = _strip_prefixes(
            text,
            [
                r"^(completa|completar|marca|marcar|termina|terminar)\s+(la\s+)?(tarea\s+)?(como\s+completada\s+)?",
                r"^(marca|marcar)\s+(como\s+)?(completada|completa|hecha)\s+(la\s+)?(tarea\s+)?",
            ],
        )
        query = _clean_query(query)
        return ParsedIntent(
            intent=IntentName.COMPLETE_TASK,
            confidence=0.9 if query else 0.5,
            task_query=query or None,
            work_date=work_date,
            raw_text=raw,
        )

    if re.search(r"\b(registra|registrar|anota|anotar|agrega|agregar)\b.*\b(tiempo|minutos|horas|hora)\b", text) or (
        duration and re.search(r"\b(en|para)\b.*\b(tarea|nota)?\b", text)
    ):
        task_query = None
        note_query = None
        note_match = re.search(r"\b(?:en|para)\s+(?:la\s+)?nota\s+(.+)$", text)
        task_match = re.search(r"\b(?:en|para)\s+(?:la\s+)?tarea\s+(.+)$", text)
        generic_match = re.search(r"\b(?:en|para)\s+(?:la\s+)?(.+)$", text)

        if note_match:
            note_query = _clean_query(note_match.group(1))
            note_query = re.sub(r"\d+\s*(minutos?|mins?|min|horas?|hrs?|h)\b", "", note_query).strip(
                " .,;:-"
            )
        elif task_match:
            task_query = _clean_query(task_match.group(1))
            task_query = re.sub(r"\d+\s*(minutos?|mins?|min|horas?|hrs?|h)\b", "", task_query).strip(
                " .,;:-"
            )
        elif generic_match:
            task_query = _clean_query(generic_match.group(1))
            task_query = re.sub(r"\d+\s*(minutos?|mins?|min|horas?|hrs?|h)\b", "", task_query).strip(
                " .,;:-"
            )
            if task_query in {"tarea", "nota"}:
                task_query = None

        return ParsedIntent(
            intent=IntentName.ADD_TIME,
            confidence=0.88 if duration else 0.55,
            duration_minutes=duration,
            task_query=task_query or None,
            note_query=note_query or None,
            work_date=work_date,
            raw_text=raw,
        )

    if (
        re.search(r"\b(abre|abrir|nueva|nuevo|crea|crear)\b.*\b(nota)\b", text)
        or text.startswith("nota ")
        or text in {"nota", "nueva nota", "crear nota"}
    ):
        content = _strip_prefixes(text, NOTE_OPEN_PREFIXES)
        content = re.sub(r"\b(para\s+)?(hoy|manana|ayer)\b", "", content).strip(" .,;:-")
        content = re.sub(r"\bpara\s+el\s+\d{1,2}[\/\-]\d{1,2}(?:[\/\-]\d{2,4})?\b", "", content).strip(
            " .,;:-"
        )
        title = None
        if " titulada " in content:
            parts = content.split(" titulada ", 1)
            content, title = parts[0].strip(), parts[1].strip()
        elif " titulo " in content:
            parts = content.split(" titulo ", 1)
            content, title = parts[0].strip(), parts[1].strip()
        intent = IntentName.OPEN_NOTE_FORM if not content and not title else IntentName.CREATE_NOTE
        return ParsedIntent(
            intent=intent,
            confidence=0.92 if content or title else 0.88,
            content=content or None,
            title=title,
            work_date=work_date,
            raw_text=raw,
        )

    if (
        re.search(r"\b(abre|abrir|nueva|nuevo|crea|crear)\b.*\b(tarea)\b", text)
        or text.startswith("tarea ")
        or text in {"tarea", "nueva tarea", "crear tarea"}
    ):
        title = _strip_prefixes(text, TASK_OPEN_PREFIXES)
        title = re.sub(r"\b(para\s+)?(hoy|manana|ayer)\b", "", title).strip(" .,;:-")
        title = re.sub(r"\bpara\s+el\s+\d{1,2}[\/\-]\d{1,2}(?:[\/\-]\d{2,4})?\b", "", title).strip(
            " .,;:-"
        )
        intent = IntentName.OPEN_TASK_FORM if not title else IntentName.CREATE_TASK
        return ParsedIntent(
            intent=intent,
            confidence=0.94 if title else 0.88,
            title=title or None,
            work_date=work_date,
            raw_text=raw,
        )

    return ParsedIntent(
        intent=IntentName.UNKNOWN,
        confidence=0.2,
        work_date=work_date,
        raw_text=raw,
    )


def _parse_calendar(text: str, work_date: date, raw: str) -> ParsedIntent | None:
    if re.search(r"\b(ve a|ir a|muestra|mostrar|abre|abrir)?\s*(el\s+)?hoy\b", text) and (
        re.search(r"\b(calendario|hoy)\b", text)
    ):
        if "calendario" in text or text.strip() in {"hoy", "ve a hoy", "ir a hoy", "muestra hoy"}:
            return ParsedIntent(
                intent=IntentName.CALENDAR_NAVIGATE,
                confidence=0.94,
                work_date=work_date,
                raw_text=raw,
                slots={"action": "today"},
                navigate_to=NavigateTarget.CALENDAR,
            )

    mode = None
    if re.search(r"\b(vista\s+)?(dia|day)\b", text):
        mode = "day"
    elif re.search(r"\b(vista\s+)?(semana|week)\b", text):
        mode = "week"
    elif re.search(r"\b(vista\s+)?(mes|month)\b", text):
        mode = "month"
    elif re.search(r"\b(vista\s+)?(ano|año|year)\b", text):
        mode = "year"

    action = None
    unit = mode
    if re.search(r"\b(anterior|previo|pasad[oa]|atras)\b", text):
        action = "prev"
    elif re.search(r"\b(siguiente|proxima|proximo|adelante)\b", text):
        action = "next"

    if action and (
        mode
        or re.search(r"\b(calendario|semana|mes|dia|ano)\b", text)
        or re.search(r"\b(anterior|siguiente)\b", text)
    ):
        if not unit:
            if re.search(r"\bsemana\b", text):
                unit = "week"
            elif re.search(r"\bmes\b", text):
                unit = "month"
            elif re.search(r"\bdia\b", text):
                unit = "day"
            elif re.search(r"\b(ano|año)\b", text):
                unit = "year"
            else:
                unit = "week"
        return ParsedIntent(
            intent=IntentName.CALENDAR_NAVIGATE,
            confidence=0.93,
            work_date=work_date,
            raw_text=raw,
            slots={"action": action, "unit": unit, "mode": mode or unit},
            navigate_to=NavigateTarget.CALENDAR,
        )

    if mode and re.search(r"\b(calendario|vista)\b", text):
        return ParsedIntent(
            intent=IntentName.CALENDAR_NAVIGATE,
            confidence=0.9,
            work_date=work_date,
            raw_text=raw,
            slots={"action": "set_mode", "mode": mode},
            navigate_to=NavigateTarget.CALENDAR,
        )

    return None


def _parse_workspace_filter(text: str, work_date: date, raw: str) -> ParsedIntent | None:
    clear = re.search(
        r"\b(quita|quitar|limpia|limpiar|borra|borrar|sin)\b.*\b(filtro|filtros)\b"
        r"|\b(todas?\s+las\s+personas|todos\s+los\s+proyectos|sin\s+filtro)\b",
        text,
    )
    if clear and (
        re.search(r"\b(informe|workspace|filtro|tiempo)\b", text)
        or "filtro" in text
        or "todas las personas" in text
        or "todos los proyectos" in text
    ):
        return ParsedIntent(
            intent=IntentName.FILTER_WORKSPACE,
            confidence=0.92,
            work_date=work_date,
            raw_text=raw,
            slots={"clear": True},
            navigate_to=NavigateTarget.WORKSPACE,
        )

    person = None
    project = None

    person_match = re.search(
        r"\b(?:filtra|filtrar|filtro|informe|muestra|mostrar)\b.*\b(?:por\s+)?persona\s+(.+?)(?:\s+y\s+proyecto\s+(.+))?$",
        text,
    )
    project_match = re.search(
        r"\b(?:filtra|filtrar|filtro|informe|muestra|mostrar)\b.*\b(?:por\s+|de\s+)?proyecto\s+(.+)$",
        text,
    )
    informe_person = re.search(r"\binforme\s+(?:de\s+)?(?:la\s+)?persona\s+(.+)$", text)
    informe_project = re.search(r"\binforme\s+(?:de\s+)?(?:el\s+|del\s+)?proyecto\s+(.+)$", text)

    if person_match:
        person = _clean_query(person_match.group(1))
        if person_match.group(2):
            project = _clean_query(person_match.group(2))
    elif informe_person:
        person = _clean_query(informe_person.group(1))
    elif project_match:
        project = _clean_query(project_match.group(1))
    elif informe_project:
        project = _clean_query(informe_project.group(1))
    elif re.search(r"\bfiltra\b.*\bpersona\b", text) or re.search(r"\bfiltra\b.*\bproyecto\b", text):
        # filtra por persona Juan / filtra proyecto X
        m = re.search(r"\bpersona\s+(.+)$", text)
        if m:
            person = _clean_query(m.group(1))
        m = re.search(r"\bproyecto\s+(.+)$", text)
        if m:
            project = _clean_query(m.group(1))

    if person or project:
        return ParsedIntent(
            intent=IntentName.FILTER_WORKSPACE,
            confidence=0.93,
            work_date=work_date,
            raw_text=raw,
            slots={
                "person_name": person,
                "project_name": project,
                "clear": False,
            },
            navigate_to=NavigateTarget.WORKSPACE,
        )
    return None


def _strip_entity_label(query: str, labels: str) -> str:
    return re.sub(
        rf"^(la\s+|el\s+|las\s+|los\s+)?(formulario\s+(de\s+)?)?({labels})\s*",
        "",
        query,
    ).strip(" .,;:-")


def _parse_delete(text: str, work_date: date, raw: str) -> ParsedIntent | None:
    if not re.search(r"\b(elimina|eliminar|borra|borrar|quita|quitar)\b", text):
        return None

    # Career catalog kinds before bare "estado"
    career_mapping = [
        (r"\bestados?\s+de\s+(postulacion|solicitud)\b", "application-statuses"),
        (r"\bempresas?\b", "companies"),
        (r"\b(cargos?|puestos?)\b", "positions"),
        (r"\bubicaciones?\b", "locations"),
        (r"\btecnologias?\b", "technologies"),
        (r"\bcarreras?\b", "fields"),
        (r"\barea profesional\b", "fields"),
    ]
    for pattern, kind in career_mapping:
        if re.search(pattern, text):
            query = _strip_prefixes(text, DELETE_PREFIXES)
            query = _strip_entity_label(query, _CAREER_KIND_LABEL)
            query = _clean_query(query)
            return ParsedIntent(
                intent=IntentName.DELETE_CAREER_CATALOG,
                confidence=0.9 if query else 0.5,
                task_query=query or None,
                work_date=work_date,
                raw_text=raw,
                slots={"catalog_kind": kind},
            )

    mapping = [
        (r"\bexperiencias?\b", IntentName.DELETE_WORK_EXPERIENCE, "task_query", r"experiencias?(\s+laborales?)?"),
        (r"\b(postulaciones?|solicitudes?)\b", IntentName.DELETE_JOB_APPLICATION, "task_query", r"(postulaciones?|solicitudes?)"),
        (r"\bservicio(\s+de\s+(la\s+)?boveda)?\b", IntentName.DELETE_VAULT_SERVICE, "task_query", r"servicio(\s+de\s+(la\s+)?boveda)?"),
        (r"\btarea\b", IntentName.DELETE_TASK, "task_query", r"tarea"),
        (r"\bnota\b", IntentName.DELETE_NOTE, "note_query", r"nota"),
        (r"\bpersona\b", IntentName.DELETE_PERSON, "task_query", r"persona"),
        (r"\bproyecto\b", IntentName.DELETE_PROJECT, "task_query", r"proyecto"),
        (r"\bestado\b", IntentName.DELETE_STATUS, "task_query", r"estado"),
        (r"\bcategoria\b", IntentName.DELETE_CATEGORY, "task_query", r"categoria"),
        (r"\bcuenta(\s+de\s+(la\s+)?boveda)?\b", IntentName.DELETE_VAULT_ACCOUNT, "task_query", r"cuenta(\s+de\s+(la\s+)?boveda)?"),
        (r"\b(contrasena|credencial)\b", IntentName.DELETE_VAULT_PASSWORD, "task_query", r"(contrasena|credencial)"),
    ]

    for pattern, intent, field, label in mapping:
        if re.search(pattern, text):
            query = _strip_prefixes(text, DELETE_PREFIXES)
            query = _strip_entity_label(query, label)
            query = _clean_query(query)
            kwargs: dict = {
                "intent": intent,
                "confidence": 0.9 if query else 0.5,
                "work_date": work_date,
                "raw_text": raw,
            }
            if field == "note_query":
                kwargs["note_query"] = query or None
            else:
                kwargs["task_query"] = query or None
            return ParsedIntent(**kwargs)
    return None


def _parse_edit(text: str, work_date: date, raw: str) -> ParsedIntent | None:
    if not re.search(r"\b(edita|editar|modifica|modificar)\b", text):
        return None

    career_mapping = [
        (r"\bestados?\s+de\s+(postulacion|solicitud)\b", "application-statuses"),
        (r"\bempresas?\b", "companies"),
        (r"\b(cargos?|puestos?)\b", "positions"),
        (r"\bubicaciones?\b", "locations"),
        (r"\btecnologias?\b", "technologies"),
        (r"\bcarreras?\b", "fields"),
        (r"\barea profesional\b", "fields"),
    ]
    for pattern, kind in career_mapping:
        if re.search(pattern, text):
            query = _strip_prefixes(text, EDIT_PREFIXES)
            query = _strip_entity_label(query, _CAREER_KIND_LABEL)
            query = _clean_query(query)
            return ParsedIntent(
                intent=IntentName.OPEN_EDIT_CAREER_CATALOG_FORM,
                confidence=0.92 if query else 0.55,
                task_query=query or None,
                work_date=work_date,
                raw_text=raw,
                slots={"catalog_kind": kind},
            )

    mapping = [
        (r"\bexperiencias?\b", IntentName.OPEN_EDIT_WORK_EXPERIENCE_FORM, r"experiencias?(\s+laborales?)?"),
        (r"\b(postulaciones?|solicitudes?)\b", IntentName.OPEN_EDIT_JOB_APPLICATION_FORM, r"(postulaciones?|solicitudes?)"),
        (r"\bservicio(\s+de\s+(la\s+)?boveda)?\b", IntentName.OPEN_EDIT_VAULT_SERVICE_FORM, r"servicio(\s+de\s+(la\s+)?boveda)?"),
        (r"\btarea\b", IntentName.OPEN_EDIT_TASK_FORM, r"tarea"),
        (r"\bnota\b", IntentName.OPEN_EDIT_NOTE_FORM, r"nota"),
        (r"\bpersona\b", IntentName.OPEN_EDIT_PERSON_FORM, r"persona"),
        (r"\bproyecto\b", IntentName.OPEN_EDIT_PROJECT_FORM, r"proyecto"),
        (r"\bestado\b", IntentName.OPEN_EDIT_STATUS_FORM, r"estado"),
        (r"\bcategoria\b", IntentName.OPEN_EDIT_CATEGORY_FORM, r"categoria"),
        (r"\bcuenta(\s+de\s+(la\s+)?boveda)?\b", IntentName.OPEN_EDIT_VAULT_ACCOUNT_FORM, r"cuenta(\s+de\s+(la\s+)?boveda)?"),
        (r"\b(contrasena|credencial)\b", IntentName.OPEN_EDIT_VAULT_PASSWORD_FORM, r"(contrasena|credencial)"),
    ]

    for pattern, intent, label in mapping:
        if re.search(pattern, text):
            query = _strip_prefixes(text, EDIT_PREFIXES)
            query = _strip_entity_label(query, label)
            query = _clean_query(query)
            return ParsedIntent(
                intent=intent,
                confidence=0.92 if query else 0.55,
                task_query=query or None,
                note_query=query or None if intent == IntentName.OPEN_EDIT_NOTE_FORM else None,
                work_date=work_date,
                raw_text=raw,
            )
    return None


def _parse_list(text: str, work_date: date, raw: str) -> ParsedIntent | None:
    if re.search(r"\b(lista|listar|muestra|mostrar|dame|ver)\b.*\b(tareas?)\b", text) or text in {
        "tareas",
        "mis tareas",
    }:
        return ParsedIntent(
            intent=IntentName.LIST_TASKS,
            confidence=0.93,
            work_date=work_date,
            raw_text=raw,
        )

    if re.search(r"\b(lista|listar|muestra|mostrar|dame|ver)\b.*\b(notas?)\b", text) or text in {
        "notas",
        "mis notas",
    }:
        return ParsedIntent(
            intent=IntentName.LIST_NOTES,
            confidence=0.93,
            work_date=work_date,
            raw_text=raw,
        )

    if re.search(r"\b(lista|listar|muestra|mostrar|dame|ver)\b.*\b(personas?|gente)\b", text) or text in {
        "personas",
        "mis personas",
    }:
        return ParsedIntent(
            intent=IntentName.LIST_PEOPLE,
            confidence=0.93,
            work_date=work_date,
            raw_text=raw,
        )

    if re.search(r"\b(lista|listar|muestra|mostrar|dame|ver)\b.*\b(proyectos?)\b", text) or text in {
        "proyectos",
        "mis proyectos",
    }:
        return ParsedIntent(
            intent=IntentName.LIST_PROJECTS,
            confidence=0.93,
            work_date=work_date,
            raw_text=raw,
        )

    if re.search(r"\b(lista|listar|muestra|mostrar|dame|ver)\b.*\b(estados?)\b", text) or text in {
        "estados",
        "mis estados",
    }:
        return ParsedIntent(
            intent=IntentName.LIST_STATUSES,
            confidence=0.93,
            work_date=work_date,
            raw_text=raw,
        )

    if re.search(r"\b(lista|listar|muestra|mostrar|dame|ver)\b.*\b(categorias?)\b", text) or text in {
        "categorias",
        "mis categorias",
    }:
        return ParsedIntent(
            intent=IntentName.LIST_CATEGORIES,
            confidence=0.93,
            work_date=work_date,
            raw_text=raw,
        )

    if re.search(
        r"\b(lista|listar|muestra|mostrar|dame|ver)\b.*\bexperiencias?(?:\s+laborales?)?\b",
        text,
    ) or text in {"experiencias", "mis experiencias", "experiencias laborales"}:
        return ParsedIntent(
            intent=IntentName.LIST_WORK_EXPERIENCES,
            confidence=0.93,
            work_date=work_date,
            raw_text=raw,
        )

    if re.search(
        r"\b(lista|listar|muestra|mostrar|dame|ver)\b.*\b(postulaciones?|solicitudes?)\b",
        text,
    ) or text in {"postulaciones", "solicitudes", "mis postulaciones", "mis solicitudes"}:
        return ParsedIntent(
            intent=IntentName.LIST_JOB_APPLICATIONS,
            confidence=0.93,
            work_date=work_date,
            raw_text=raw,
        )

    return None


HELP_TEXT = """Comandos de voz — DailyTime

ACTIVAR VOZ
- Pulsa el icono de ondas (esquina inferior derecha).

NUEVA TAREA / NOTA (formulario paso a paso)
1. Di: "nueva tarea" o "nueva nota"
2. Dicta campos: título/contenido, fecha, categoría, estado, persona, proyecto, horas
3. Di: "guardar"

EDITAR
- "edita la tarea revisar informe"
- "edita la persona Juan" / "edita el proyecto rediseño"
- "edita la empresa Google" / "edita la experiencia Microsoft"

ELIMINAR
- "elimina la tarea revisar informe"
- "borra la nota comprar leche"
- "elimina la persona Juan"
- "elimina la postulación Google"

COMPLETAR
- "completa la tarea revisar informe"
- "completa la nota comprar leche"

REGISTRAR TIEMPO
- "registra 30 minutos en la tarea revisar informe"
- "registra 15 minutos en la nota reunión"

CATÁLOGOS
- "nueva persona" / "nuevo proyecto" / "nuevo estado" / "nueva categoría"
- "lista las personas" / "muestra los proyectos" / "lista estados"

CARRERA
- "nueva empresa" / "nuevo cargo" / "nueva ubicación" / "nueva tecnología" / "nueva carrera"
- "nuevo estado de postulación"
- "nueva experiencia" / "nueva postulación"
- "lista experiencias" / "lista postulaciones"
- "abre datos reutilizables" / "abre experiencias" / "abre postulaciones"

BÓVEDA
- "nueva cuenta de bóveda" / "nueva contraseña" / "nuevo servicio de bóveda"
- "edita la contraseña Gmail" / "elimina la cuenta principal"
- "abre servicios de la bóveda" / "abre servicios"

INFORME DE TIEMPO
- "abre el informe"
- "filtra por persona Juan" / "informe de proyecto rediseño"
- "quita el filtro"

CALENDARIO
- "abre el calendario"
- "ve a hoy" / "semana anterior" / "mes siguiente"
- "vista semana" / "vista mes"

NAVEGAR
- "abre el tablero" / "abre personas" / "abre la bóveda"
- "abre datos reutilizables" / "abre experiencias" / "abre postulaciones" / "abre servicios"

AYUDA
- "ayuda" / "manual" / "qué puedes hacer"
"""
