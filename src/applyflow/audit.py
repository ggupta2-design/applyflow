"""Read-only semantic integrity audits for application records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Iterable

from .models import Application


class AuditSeverity(str, Enum):
    """Machine-readable severity for an integrity finding."""

    ERROR = "error"
    WARNING = "warning"


class AuditCode(str, Enum):
    """Stable identifiers for supported integrity checks."""

    MISSING_HISTORY = "missing_history"
    STATUS_HISTORY_MISMATCH = "status_history_mismatch"
    UPDATED_BEFORE_CREATED = "updated_before_created"


@dataclass(frozen=True)
class AuditFinding:
    """A value-free integrity finding."""

    code: AuditCode
    severity: AuditSeverity


@dataclass(frozen=True)
class AuditResult:
    """Aggregate audit result that never contains application values."""

    as_of: date
    records_checked: int
    findings: tuple[AuditFinding, ...]

    @property
    def error_count(self) -> int:
        return sum(item.severity == AuditSeverity.ERROR for item in self.findings)

    @property
    def warning_count(self) -> int:
        return sum(item.severity == AuditSeverity.WARNING for item in self.findings)

    @property
    def healthy(self) -> bool:
        return not self.findings


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
        if application.updated_at < application.created_at:
            findings.append(
                AuditFinding(
                    AuditCode.UPDATED_BEFORE_CREATED,
                    AuditSeverity.ERROR,
                )
            )

    return AuditResult(
        as_of=as_of,
        records_checked=len(records),
        findings=tuple(
            sorted(findings, key=lambda item: (item.severity.value, item.code.value))
        ),
    )
