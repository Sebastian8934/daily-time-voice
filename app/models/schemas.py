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
    OPEN_PERSON_FORM = "open_person_form"
    CREATE_PERSON = "create_person"
    OPEN_PROJECT_FORM = "open_project_form"
    CREATE_PROJECT = "create_project"
    OPEN_STATUS_FORM = "open_status_form"
    CREATE_STATUS = "create_status"
    OPEN_CATEGORY_FORM = "open_category_form"
    CREATE_CATEGORY = "create_category"
    OPEN_VAULT_ACCOUNT_FORM = "open_vault_account_form"
    CREATE_VAULT_ACCOUNT = "create_vault_account"
    OPEN_VAULT_PASSWORD_FORM = "open_vault_password_form"
    CREATE_VAULT_PASSWORD = "create_vault_password"
    OPEN_CAREER_CATALOG_FORM = "open_career_catalog_form"
    CREATE_CAREER_CATALOG = "create_career_catalog"
    OPEN_EDIT_CAREER_CATALOG_FORM = "open_edit_career_catalog_form"
    DELETE_CAREER_CATALOG = "delete_career_catalog"
    OPEN_WORK_EXPERIENCE_FORM = "open_work_experience_form"
    CREATE_WORK_EXPERIENCE = "create_work_experience"
    OPEN_EDIT_WORK_EXPERIENCE_FORM = "open_edit_work_experience_form"
    DELETE_WORK_EXPERIENCE = "delete_work_experience"
    OPEN_JOB_APPLICATION_FORM = "open_job_application_form"
    CREATE_JOB_APPLICATION = "create_job_application"
    OPEN_EDIT_JOB_APPLICATION_FORM = "open_edit_job_application_form"
    DELETE_JOB_APPLICATION = "delete_job_application"
    OPEN_VAULT_SERVICE_FORM = "open_vault_service_form"
    CREATE_VAULT_SERVICE = "create_vault_service"
    OPEN_EDIT_VAULT_SERVICE_FORM = "open_edit_vault_service_form"
    DELETE_VAULT_SERVICE = "delete_vault_service"
    OPEN_EDIT_TASK_FORM = "open_edit_task_form"
    OPEN_EDIT_NOTE_FORM = "open_edit_note_form"
    OPEN_EDIT_PERSON_FORM = "open_edit_person_form"
    OPEN_EDIT_PROJECT_FORM = "open_edit_project_form"
    OPEN_EDIT_STATUS_FORM = "open_edit_status_form"
    OPEN_EDIT_CATEGORY_FORM = "open_edit_category_form"
    OPEN_EDIT_VAULT_ACCOUNT_FORM = "open_edit_vault_account_form"
    OPEN_EDIT_VAULT_PASSWORD_FORM = "open_edit_vault_password_form"
    LIST_TASKS = "list_tasks"
    LIST_NOTES = "list_notes"
    LIST_PEOPLE = "list_people"
    LIST_PROJECTS = "list_projects"
    LIST_STATUSES = "list_statuses"
    LIST_CATEGORIES = "list_categories"
    LIST_WORK_EXPERIENCES = "list_work_experiences"
    LIST_JOB_APPLICATIONS = "list_job_applications"
    COMPLETE_TASK = "complete_task"
    COMPLETE_NOTE = "complete_note"
    DELETE_TASK = "delete_task"
    DELETE_NOTE = "delete_note"
    DELETE_PERSON = "delete_person"
    DELETE_PROJECT = "delete_project"
    DELETE_STATUS = "delete_status"
    DELETE_CATEGORY = "delete_category"
    DELETE_VAULT_ACCOUNT = "delete_vault_account"
    DELETE_VAULT_PASSWORD = "delete_vault_password"
    ADD_TIME = "add_time"
    FILTER_WORKSPACE = "filter_workspace"
    CALENDAR_NAVIGATE = "calendar_navigate"
    NAVIGATE = "navigate"
    HELP = "help"
    UNKNOWN = "unknown"


class NavigateTarget(str, Enum):
    BOARD = "board"
    CALENDAR = "calendar"
    WORKSPACE = "workspace"
    STATUSES = "statuses"
    CATEGORIES = "categories"
    PEOPLE = "people"
    PROJECTS = "projects"
    VAULT = "vault"
    DAY = "day"
    TASKS = "tasks"
    NOTES = "notes"
    EXPERIENCES = "experiences"
    APPLICATIONS = "applications"
    CAREER_CATALOGS = "career-catalogs"
    VAULT_SERVICES = "vault-services"


class ParsedIntent(BaseModel):
    intent: IntentName
    confidence: float = 0.0
    title: str | None = None
    content: str | None = None
    work_date: date | None = None
    duration_minutes: int | None = None
    task_query: str | None = None
    note_query: str | None = None
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
