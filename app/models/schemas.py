from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class IntentName(str, Enum):
    CREATE_TASK = "create_task"
    CREATE_NOTE = "create_note"
    OPEN_TASK_FORM = "open_task_form"
    OPEN_NOTE_FORM = "open_note_form"
    LIST_TASKS = "list_tasks"
    LIST_NOTES = "list_notes"
    COMPLETE_TASK = "complete_task"
    ADD_TIME = "add_time"
    NAVIGATE = "navigate"
    HELP = "help"
    UNKNOWN = "unknown"


class NavigateTarget(str, Enum):
    BOARD = "board"
    CALENDAR = "calendar"
    WORKSPACE = "workspace"
    STATUSES = "statuses"
    CATEGORIES = "categories"


class ParsedIntent(BaseModel):
    intent: IntentName
    confidence: float = 0.0
    title: str | None = None
    content: str | None = None
    work_date: date | None = None
    duration_minutes: int | None = None
    task_query: str | None = None
    navigate_to: NavigateTarget | None = None
    raw_text: str = ""
    slots: dict[str, Any] = Field(default_factory=dict)
    form_field: str | None = None
    form_value: str | None = None
    status_name: str | None = None
    category_name: str | None = None
    start_time: str | None = None
    end_time: str | None = None


class CommandRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Comando en español")
    work_date: date | None = None
    dry_run: bool = False


class CommandResponse(BaseModel):
    success: bool
    transcript: str
    intent: IntentName
    confidence: float
    message: str
    navigate_to: str | None = None
    data: Any = None
    dry_run: bool = False
    requires_confirmation: bool = False


class TranscribeResponse(BaseModel):
    transcript: str
    engine: str


class HealthResponse(BaseModel):
    status: str
    version: str
    daily_time_api_url: str
    whisper_enabled: bool
