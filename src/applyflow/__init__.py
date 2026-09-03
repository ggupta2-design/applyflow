"""Local-first job application workflow automation."""

from .activity import ActivityRecord, application_timeline, recent_activity
from .analytics import (
    PipelineSummary,
    StaleApplication,
    StatusCount,
    find_stale_applications,
    summarize_pipeline,
)
from .models import Activity, Application, ApplicationError, ApplicationStatus
from .planning import ActionItem, ActionKind, ActionPlan, build_action_plan
from .service import (
    add_application_note,
    create_application,
    due_follow_ups,
    get_application,
    list_applications,
    schedule_follow_up,
    transition_application,
)
from .storage import ApplicationStore, StorageError

__all__ = [
    "Activity",
    "ActivityRecord",
    "ActionItem",
    "ActionKind",
    "ActionPlan",
    "PipelineSummary",
    "StaleApplication",
    "StatusCount",
    "Application",
    "ApplicationError",
    "ApplicationStatus",
    "ApplicationStore",
    "StorageError",
    "add_application_note",
    "application_timeline",
    "build_action_plan",
    "create_application",
    "due_follow_ups",
    "find_stale_applications",
    "get_application",
    "list_applications",
    "recent_activity",
    "schedule_follow_up",
    "summarize_pipeline",
    "transition_application",
    "__version__",
]
__version__ = "0.4.0"
