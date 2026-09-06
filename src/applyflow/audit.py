"""Read-only semantic integrity audits for application records."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Iterable

from .models import Application, ApplicationStatus


_TERMINAL = {ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWN}
_SUBMITTED = {
    ApplicationStatus.APPLIED,
    ApplicationStatus.INTERVIEWING,
    ApplicationStatus.OFFER,
}


class AuditSeverity(str, Enum):
    """Machine-readable severity for an integrity finding."""

    ERROR = "error"
    WARNING = "warning"


class AuditCode(str, Enum):
    """Stable identifiers for supported integrity checks."""

    MISSING_HISTORY = "missing_history"
    STATUS_HISTORY_MISMATCH = "status_history_mismatch"
    UPDATED_BEFORE_CREATED = "updated_before_created"
    INVALID_STATUS_TRANSITION = "invalid_status_transition"
    TIMESTAMP_WITHOUT_TIMEZONE = "timestamp_without_timezone"
    ACTIVITY_OUT_OF_ORDER = "activity_out_of_order"
    ACTIVITY_OUTSIDE_RECORD_WINDOW = "activity_outside_record_window"
    FUTURE_TIMESTAMP = "future_timestamp"
    FUTURE_APPLIED_DATE = "future_applied_date"
    MISSING_APPLIED_DATE = "missing_applied_date"
    TERMINAL_FOLLOW_UP = "terminal_follow_up"
    DUPLICATE_ACTIVE_OPPORTUNITY = "duplicate_active_opportunity"


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


@dataclass(frozen=True)
class AuditFinding:
    """A value-free integrity finding."""

    code: AuditCode
    severity: AuditSeverity


@dataclass(frozen=True)
class FindingCount:
    """Aggregate count for one stable finding code and severity."""

    code: AuditCode
    severity: AuditSeverity
    count: int


@dataclass(frozen=True)
class AuditResult:
    """Aggregate audit result that never contains application values."""

    as_of: date
    records_checked: int
    findings: tuple[AuditFinding, ...]

    @property
    def finding_count(self) -> int:
        return len(self.findings)

    @property
    def counts(self) -> tuple[FindingCount, ...]:
        grouped = Counter((item.code, item.severity) for item in self.findings)
        return tuple(
            FindingCount(code=code, severity=severity, count=count)
            for (code, severity), count in sorted(
                grouped.items(),
                key=lambda item: (item[0][1].value, item[0][0].value),
            )
        )

    @property
    def error_count(self) -> int:
        return sum(item.severity == AuditSeverity.ERROR for item in self.findings)

    @property
    def warning_count(self) -> int:
        return sum(item.severity == AuditSeverity.WARNING for item in self.findings)

    @property
    def healthy(self) -> bool:
        return not self.findings


def _is_aware(value: datetime) -> bool:
    return value.tzinfo is not None and value.utcoffset() is not None


def audit_applications(
    applications: Iterable[Application],
    *,
    as_of: date,
) -> AuditResult:
    """Audit record relationships without changing or exposing stored values."""

    records = tuple(applications)
    findings: list[AuditFinding] = []
    for application in records:
        if not application.history:
            findings.append(
                AuditFinding(AuditCode.MISSING_HISTORY, AuditSeverity.ERROR)
            )
        elif application.history[-1].status != application.status:
            findings.append(
                AuditFinding(
                    AuditCode.STATUS_HISTORY_MISMATCH,
                    AuditSeverity.ERROR,
                )
            )
        for previous, current in zip(application.history, application.history[1:]):
            if (
                current.status != previous.status
                and current.status not in _ALLOWED_TRANSITIONS[previous.status]
            ):
                findings.append(
                    AuditFinding(
                        AuditCode.INVALID_STATUS_TRANSITION,
                        AuditSeverity.ERROR,
                    )
                )
                break
        timestamps = (
            application.created_at,
            application.updated_at,
            *(activity.at for activity in application.history),
        )
        timestamps_are_aware = all(_is_aware(value) for value in timestamps)
        if not timestamps_are_aware:
            findings.append(
                AuditFinding(
                    AuditCode.TIMESTAMP_WITHOUT_TIMEZONE,
                    AuditSeverity.ERROR,
                )
            )
        else:
            if application.updated_at < application.created_at:
                findings.append(
                    AuditFinding(
                        AuditCode.UPDATED_BEFORE_CREATED,
                        AuditSeverity.ERROR,
                    )
                )
            if any(
                current.at < previous.at
                for previous, current in zip(
                    application.history,
                    application.history[1:],
                )
            ):
                findings.append(
                    AuditFinding(
                        AuditCode.ACTIVITY_OUT_OF_ORDER,
                        AuditSeverity.ERROR,
                    )
                )
            if any(
                activity.at < application.created_at
                or activity.at > application.updated_at
                for activity in application.history
            ):
                findings.append(
                    AuditFinding(
                        AuditCode.ACTIVITY_OUTSIDE_RECORD_WINDOW,
                        AuditSeverity.ERROR,
                    )
                )
            if any(value.date() > as_of for value in timestamps):
                findings.append(
                    AuditFinding(
                        AuditCode.FUTURE_TIMESTAMP,
                        AuditSeverity.WARNING,
                    )
                )
        if application.applied_on is not None and application.applied_on > as_of:
            findings.append(
                AuditFinding(
                    AuditCode.FUTURE_APPLIED_DATE,
                    AuditSeverity.WARNING,
                )
            )
        reached_submitted_stage = (
            application.status in _SUBMITTED
            or any(activity.status in _SUBMITTED for activity in application.history)
        )
        if reached_submitted_stage and application.applied_on is None:
            findings.append(
                AuditFinding(
                    AuditCode.MISSING_APPLIED_DATE,
                    AuditSeverity.ERROR,
                )
            )
        if application.status in _TERMINAL and application.follow_up_on is not None:
            findings.append(
                AuditFinding(
                    AuditCode.TERMINAL_FOLLOW_UP,
                    AuditSeverity.ERROR,
                )
            )

    seen_active: set[tuple[str, str]] = set()
    for application in records:
        if application.status in _TERMINAL:
            continue
        key = (application.company.casefold(), application.role.casefold())
        if key in seen_active:
            findings.append(
                AuditFinding(
                    AuditCode.DUPLICATE_ACTIVE_OPPORTUNITY,
                    AuditSeverity.WARNING,
                )
            )
        else:
            seen_active.add(key)

    return AuditResult(
        as_of=as_of,
        records_checked=len(records),
        findings=tuple(
            sorted(findings, key=lambda item: (item.severity.value, item.code.value))
        ),
    )
