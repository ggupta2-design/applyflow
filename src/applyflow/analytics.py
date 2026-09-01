"""Read-only analytics for the local application pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .models import Application, ApplicationStatus


@dataclass(frozen=True)
class StatusCount:
    """Count of applications currently in one workflow stage."""

    status: ApplicationStatus
    count: int


@dataclass(frozen=True)
class PipelineSummary:
    """Value-focused aggregate pipeline metrics."""

    total: int
    active: int
    terminal: int
    submitted: int
    reached_interview: int
    reached_offer: int
    interview_rate: float
    offer_rate: float
    status_counts: tuple[StatusCount, ...]


def summarize_pipeline(applications: Iterable[Application]) -> PipelineSummary:
    """Summarize stages and milestone conversion without changing records."""

    records = tuple(applications)
    terminal_statuses = {ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWN}
    counts = tuple(
        StatusCount(
            status=status,
            count=sum(item.status == status for item in records),
        )
        for status in ApplicationStatus
    )
    submitted_records = tuple(item for item in records if item.applied_on is not None)

    def reached(application: Application, statuses: set[ApplicationStatus]) -> bool:
        return application.status in statuses or any(
            activity.status in statuses for activity in application.history
        )

    interview_statuses = {ApplicationStatus.INTERVIEWING, ApplicationStatus.OFFER}
    reached_interview = sum(reached(item, interview_statuses) for item in submitted_records)
    reached_offer = sum(
        reached(item, {ApplicationStatus.OFFER}) for item in submitted_records
    )
    submitted = len(submitted_records)
    return PipelineSummary(
        total=len(records),
        active=sum(item.status not in terminal_statuses for item in records),
        terminal=sum(item.status in terminal_statuses for item in records),
        submitted=submitted,
        reached_interview=reached_interview,
        reached_offer=reached_offer,
        interview_rate=(reached_interview / submitted * 100) if submitted else 0.0,
        offer_rate=(reached_offer / submitted * 100) if submitted else 0.0,
        status_counts=counts,
    )
