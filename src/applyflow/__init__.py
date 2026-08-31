"""Local-first job application workflow automation."""

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
    "Application",
    "ApplicationError",
    "ApplicationStatus",
    "ApplicationStore",
    "StorageError",
    "create_application",
    "due_follow_ups",
    "get_application",
    "list_applications",
    "schedule_follow_up",
    "transition_application",
    "__version__",
]
__version__ = "0.1.0"
