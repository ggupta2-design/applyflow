"""Local-first job application workflow automation."""

from .activity import ActivityRecord, application_timeline, recent_activity
from .analytics import (
    PipelineSummary,
    StaleApplication,
    StatusCount,
    find_stale_applications,
    summarize_pipeline,
)
from .backup import BackupSummary, create_backup, restore_backup, verify_backup
from .models import Activity, Application, ApplicationError, ApplicationStatus
from .planning import ActionItem, ActionKind, ActionPlan, build_action_plan
from .review import WeeklyReview, build_weekly_review
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
    "WeeklyReview",
    "Application",
    "ApplicationError",
    "ApplicationStatus",
    "ApplicationStore",
    "BackupSummary",
    "StorageError",
    "add_application_note",
    "application_timeline",
    "build_action_plan",
    "build_weekly_review",
    "create_application",
    "create_backup",
    "due_follow_ups",
    "find_stale_applications",
    "get_application",
    "list_applications",
    "recent_activity",
    "restore_backup",
    "schedule_follow_up",
    "summarize_pipeline",
    "transition_application",
    "verify_backup",
    "__version__",
]
__version__ = "0.6.0"
