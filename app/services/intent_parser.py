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


NAV_MAP: list[tuple[re.Pattern[str], NavigateTarget]] = [
    (re.compile(r"\b(tablero|board)\b"), NavigateTarget.BOARD),
    (re.compile(r"\b(calendario|calendar)\b"), NavigateTarget.CALENDAR),
    (re.compile(r"\b(informe|workspace|tiempo|reporte)\b"), NavigateTarget.WORKSPACE),
    (re.compile(r"\b(estados?)\b"), NavigateTarget.STATUSES),
    (re.compile(r"\b(categorias?)\b"), NavigateTarget.CATEGORIES),
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


def parse_intent(raw_text: str, default_work_date: date | None = None) -> ParsedIntent:
    """Parser determinista de comandos en español (sin LLM)."""
    today = default_work_date or date.today()
    raw = raw_text.strip()
    text = _normalize(raw)
    work_date = _parse_relative_date(text, today) or today
    duration = _extract_duration_minutes(text)

    if re.search(r"\b(ayuda|help|comandos|que puedes hacer)\b", text):
        return ParsedIntent(
            intent=IntentName.HELP,
            confidence=0.99,
            raw_text=raw,
            work_date=work_date,
        )

    for pattern, target in NAV_MAP:
        if re.search(r"\b(abre|abrir|ir|ve|navega|muestra|mostrar|ve a|ir a)\b", text) and pattern.search(text):
            return ParsedIntent(
                intent=IntentName.NAVIGATE,
                confidence=0.95,
                navigate_to=target,
                work_date=work_date,
                raw_text=raw,
            )
        if pattern.fullmatch(text.strip()):
            return ParsedIntent(
                intent=IntentName.NAVIGATE,
                confidence=0.9,
                navigate_to=target,
                work_date=work_date,
                raw_text=raw,
            )

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

    if re.search(r"\b(completa|completar|marca|marcar|termina|terminar)\b.*\b(tarea)?\b", text):
        query = _strip_prefixes(
            text,
            [
                r"^(completa|completar|marca|marcar|termina|terminar)\s+(la\s+)?(tarea\s+)?(como\s+completada\s+)?",
                r"^(marca|marcar)\s+(como\s+)?(completada|completa|hecha)\s+(la\s+)?(tarea\s+)?",
            ],
        )
        query = re.sub(r"\b(hoy|manana|ayer)\b", "", query).strip(" .,;:-")
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
        query = None
        match = re.search(r"\b(?:en|para)\s+(?:la\s+)?(?:tarea\s+)?(.+)$", text)
        if match:
            query = match.group(1).strip(" .,;:-")
            query = re.sub(r"\b(hoy|manana|ayer)\b", "", query).strip(" .,;:-")
            query = re.sub(r"\d+\s*(minutos?|mins?|min|horas?|hrs?|h)\b", "", query).strip(" .,;:-")
        return ParsedIntent(
            intent=IntentName.ADD_TIME,
            confidence=0.88 if duration else 0.55,
            duration_minutes=duration,
            task_query=query or None,
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
        content = re.sub(r"\bpara\s+el\s+\d{1,2}[\/\-]\d{1,2}(?:[\/\-]\d{2,4})?\b", "", content).strip(" .,;:-")
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
        title = re.sub(r"\bpara\s+el\s+\d{1,2}[\/\-]\d{1,2}(?:[\/\-]\d{2,4})?\b", "", title).strip(" .,;:-")
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


HELP_TEXT = """Comandos de voz — DailyTime

ACTIVAR VOZ
- Pulsa el icono de ondas (esquina inferior derecha).

NUEVA TAREA (formulario paso a paso)
1. Di: "nueva tarea"
2. Dicta campos: "título …", "fecha mañana", "categoría …", "estado …", "inicio 9:00", "fin 10:30"
3. Di: "guardar" (o "cancelar" para cerrar)

NUEVA NOTA (formulario paso a paso)
1. Di: "nueva nota" o "crea una nota que diga …"
2. Dicta: "contenido …", "título …", "categoría …", "estado …", "fecha …"
3. Di: "guardar"

CONSULTAS
- "muestra las tareas de hoy" / "lista las notas"

ACCIONES
- "completa la tarea revisar informe"
- "registra 30 minutos en la tarea revisar informe"

NAVEGAR
- "abre el tablero" / "abre el calendario" / "abre estados" / "abre categorías"

AYUDA
- "ayuda"
"""
