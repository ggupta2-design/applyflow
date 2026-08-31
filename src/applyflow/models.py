"""Validated domain models for application tracking."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any
from urllib.parse import urlparse


class ApplicationError(ValueError):
    """Raised when an application record is invalid."""


class ApplicationStatus(str, Enum):
    SAVED = "saved"
    APPLIED = "applied"
    INTERVIEWING = "interviewing"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


@dataclass(frozen=True)
class Activity:
    """One timestamped change in an application's history."""

    at: datetime
    status: ApplicationStatus
    note: str | None = None


@dataclass(frozen=True)
class Application:
    """A local job application record."""

    id: str
    company: str
    role: str
    status: ApplicationStatus = ApplicationStatus.SAVED
    source_url: str | None = None
    applied_on: date | None = None
    follow_up_on: date | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    history: tuple[Activity, ...] = ()


def validate_text(value: str, field_name: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ApplicationError(f"{field_name} cannot be blank")
    return cleaned


def validate_url(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    parsed = urlparse(cleaned)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ApplicationError("source_url must be an http or https URL")
    return cleaned


def application_to_dict(application: Application) -> dict[str, Any]:
    """Serialize an application deterministically."""

    return {
        "id": application.id,
        "company": application.company,
        "role": application.role,
        "status": application.status.value,
        "source_url": application.source_url,
        "applied_on": application.applied_on.isoformat() if application.applied_on else None,
        "follow_up_on": (
            application.follow_up_on.isoformat() if application.follow_up_on else None
        ),
        "created_at": application.created_at.isoformat(),
        "updated_at": application.updated_at.isoformat(),
        "history": [
            {
                "at": item.at.isoformat(),
                "status": item.status.value,
                "note": item.note,
            }
            for item in application.history
        ],
    }


def application_from_dict(payload: Any) -> Application:
    """Load a strict application record from JSON-compatible data."""

    expected = {
        "id",
        "company",
        "role",
        "status",
        "source_url",
        "applied_on",
        "follow_up_on",
        "created_at",
        "updated_at",
        "history",
    }
    if not isinstance(payload, dict) or set(payload) != expected:
        raise ApplicationError("Application record has missing or unknown fields")
    try:
        status = ApplicationStatus(payload["status"])
        created_at = datetime.fromisoformat(payload["created_at"])
        updated_at = datetime.fromisoformat(payload["updated_at"])
        applied_on = date.fromisoformat(payload["applied_on"]) if payload["applied_on"] else None
        follow_up_on = (
            date.fromisoformat(payload["follow_up_on"]) if payload["follow_up_on"] else None
        )
        history = tuple(
            Activity(
                at=datetime.fromisoformat(item["at"]),
                status=ApplicationStatus(item["status"]),
                note=item["note"],
            )
            for item in payload["history"]
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ApplicationError("Application record contains invalid values") from exc
    return Application(
        id=validate_text(payload["id"], "id"),
        company=validate_text(payload["company"], "company"),
        role=validate_text(payload["role"], "role"),
        status=status,
        source_url=validate_url(payload["source_url"]),
        applied_on=applied_on,
        follow_up_on=follow_up_on,
        created_at=created_at,
        updated_at=updated_at,
        history=history,
    )
