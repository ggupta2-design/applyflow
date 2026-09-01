"""Local-first job application workflow automation."""

from .analytics import (
    PipelineSummary,
    StaleApplication,
    StatusCount,
    find_stale_applications,
    summarize_pipeline,
)
from .models import Activity, Application, ApplicationError, ApplicationStatus
from .service import (
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
    "PipelineSummary",
    "StaleApplication",
    "StatusCount",
    "Application",
    "ApplicationError",
    "ApplicationStatus",
    "ApplicationStore",
    "StorageError",
    "create_application",
    "due_follow_ups",
    "find_stale_applications",
    "get_application",
    "list_applications",
    "schedule_follow_up",
    "summarize_pipeline",
    "transition_application",
    "__version__",
]
__version__ = "0.2.0"
