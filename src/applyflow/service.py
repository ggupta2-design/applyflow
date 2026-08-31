"""Application workflow operations."""

from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timezone
from uuid import uuid4

from .models import (
    Activity,
    Application,
    ApplicationError,
    ApplicationStatus,
    validate_text,
    validate_url,
)
from .storage import ApplicationStore


def create_application(
    store: ApplicationStore,
    *,
    company: str,
    role: str,
    status: ApplicationStatus = ApplicationStatus.SAVED,
    source_url: str | None = None,
    applied_on: date | None = None,
    follow_up_on: date | None = None,
    now: datetime | None = None,
    application_id: str | None = None,
) -> Application:
    """Create one validated record without duplicating the same active opportunity."""

    clean_company = validate_text(company, "company")
    clean_role = validate_text(role, "role")
    applications = store.load()
    terminal = {
        ApplicationStatus.REJECTED,
        ApplicationStatus.WITHDRAWN,
    }
    duplicate = next(
        (
            item
            for item in applications
            if item.company.casefold() == clean_company.casefold()
            and item.role.casefold() == clean_role.casefold()
            and item.status not in terminal
        ),
        None,
    )
    if duplicate is not None:
        raise ApplicationError(
            f"Active application already exists for {clean_role} at {clean_company}: "
            f"{duplicate.id}"
        )

    timestamp = now or datetime.now(timezone.utc)
    record_id = validate_text(application_id or uuid4().hex[:12], "id")
    if status == ApplicationStatus.APPLIED and applied_on is None:
        applied_on = timestamp.date()
    application = Application(
        id=record_id,
        company=clean_company,
        role=clean_role,
        status=status,
        source_url=validate_url(source_url),
        applied_on=applied_on,
        follow_up_on=follow_up_on,
        created_at=timestamp,
        updated_at=timestamp,
        history=(Activity(at=timestamp, status=status, note="Application created"),),
    )
    store.save((*applications, application))
    return application


def list_applications(
    store: ApplicationStore,
    *,
    status: ApplicationStatus | None = None,
    company: str | None = None,
) -> tuple[Application, ...]:
    """Return records deterministically with optional exact filters."""

    applications = store.load()
    company_filter = company.strip().casefold() if company else None
    selected = (
        item
        for item in applications
        if (status is None or item.status == status)
        and (company_filter is None or item.company.casefold() == company_filter)
    )
    return tuple(
        sorted(
            selected,
            key=lambda item: (item.updated_at, item.company.casefold(), item.role.casefold()),
            reverse=True,
        )
    )


def get_application(store: ApplicationStore, application_id: str) -> Application:
    clean_id = validate_text(application_id, "application_id")
    application = next((item for item in store.load() if item.id == clean_id), None)
    if application is None:
        raise ApplicationError(f"Application not found: {clean_id}")
    return application



_ALLOWED_TRANSITIONS: dict[ApplicationStatus, frozenset[ApplicationStatus]] = {
    ApplicationStatus.SAVED: frozenset(
        {ApplicationStatus.APPLIED, ApplicationStatus.WITHDRAWN}
    ),
    ApplicationStatus.APPLIED: frozenset(
        {
            ApplicationStatus.INTERVIEWING,
            ApplicationStatus.REJECTED,
            ApplicationStatus.WITHDRAWN,
        }
    ),
    ApplicationStatus.INTERVIEWING: frozenset(
        {
            ApplicationStatus.OFFER,
            ApplicationStatus.REJECTED,
            ApplicationStatus.WITHDRAWN,
        }
    ),
    ApplicationStatus.OFFER: frozenset({ApplicationStatus.WITHDRAWN}),
    ApplicationStatus.REJECTED: frozenset(),
    ApplicationStatus.WITHDRAWN: frozenset(),
}


def transition_application(
    store: ApplicationStore,
    application_id: str,
    status: ApplicationStatus,
    *,
    note: str | None = None,
    now: datetime | None = None,
) -> Application:
    """Move an application through a valid stage and preserve its history."""

    applications = store.load()
    current = next((item for item in applications if item.id == application_id), None)
    if current is None:
        raise ApplicationError(f"Application not found: {application_id}")
    if status not in _ALLOWED_TRANSITIONS[current.status]:
        raise ApplicationError(
            f"Cannot move application from {current.status.value} to {status.value}"
        )

    timestamp = now or datetime.now(timezone.utc)
    clean_note = note.strip() if note and note.strip() else None
    terminal = status in {ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWN}
    updated = replace(
        current,
        status=status,
        applied_on=(
            current.applied_on
            or (timestamp.date() if status == ApplicationStatus.APPLIED else None)
        ),
        follow_up_on=None if terminal else current.follow_up_on,
        updated_at=timestamp,
        history=(
            *current.history,
            Activity(at=timestamp, status=status, note=clean_note),
        ),
    )
    store.save(tuple(updated if item.id == updated.id else item for item in applications))
    return updated



def schedule_follow_up(
    store: ApplicationStore,
    application_id: str,
    follow_up_on: date | None,
    *,
    now: datetime | None = None,
) -> Application:
    """Set or clear a follow-up date without contacting anyone."""

    applications = store.load()
    current = next((item for item in applications if item.id == application_id), None)
    if current is None:
        raise ApplicationError(f"Application not found: {application_id}")
    if current.status in {ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWN}:
        raise ApplicationError(
            f"Cannot schedule a follow-up for a {current.status.value} application"
        )

    timestamp = now or datetime.now(timezone.utc)
    action = (
        f"Follow-up scheduled for {follow_up_on.isoformat()}"
        if follow_up_on
        else "Follow-up cleared"
    )
    updated = replace(
        current,
        follow_up_on=follow_up_on,
        updated_at=timestamp,
        history=(
            *current.history,
            Activity(at=timestamp, status=current.status, note=action),
        ),
    )
    store.save(tuple(updated if item.id == updated.id else item for item in applications))
    return updated


def due_follow_ups(
    store: ApplicationStore,
    *,
    as_of: date | None = None,
) -> tuple[Application, ...]:
    """Return active follow-ups due on or before a selected date."""

    target = as_of or date.today()
    terminal = {ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWN}
    return tuple(
        sorted(
            (
                item
                for item in store.load()
                if item.follow_up_on is not None
                and item.follow_up_on <= target
                and item.status not in terminal
            ),
            key=lambda item: (
                item.follow_up_on or target,
                item.company.casefold(),
                item.role.casefold(),
            ),
        )
    )
