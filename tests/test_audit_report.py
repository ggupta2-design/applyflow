import json
from datetime import date, datetime, timezone

from applyflow.audit import audit_applications
from applyflow.models import Application, ApplicationStatus
from applyflow.report import format_integrity_audit


def private_record():
    now = datetime(2026, 9, 6, 18, 0, tzinfo=timezone.utc)
    return Application(
        id="private-id",
        company="Sensitive Company",
        role="Confidential Role",
        status=ApplicationStatus.APPLIED,
        source_url="https://secret.example/jobs/1",
        applied_on=None,
        created_at=now,
        updated_at=now,
        history=(),
    )


def test_json_audit_report_contains_only_aggregate_findings():
    result = audit_applications(
        (private_record(),),
        as_of=date(2026, 9, 6),
    )

    output = format_integrity_audit(result, as_json=True)
    payload = json.loads(output)

    assert payload["records_checked"] == 1
    assert payload["healthy"] is False
    assert payload["error_count"] == 2
    assert {item["code"] for item in payload["findings"]} == {
        "missing_applied_date",
        "missing_history",
    }
    for secret in (
        "private-id",
        "Sensitive Company",
        "Confidential Role",
        "secret.example",
    ):
        assert secret not in output


def test_readable_audit_report_lists_counts_not_records():
    result = audit_applications(
        (private_record(),),
        as_of=date(2026, 9, 6),
    )

    output = format_integrity_audit(result)

    assert "Status: issues detected" in output
    assert "Records checked: 1" in output
    assert "missing_history: 1 (error)" in output
    assert "Sensitive Company" not in output


def test_healthy_audit_report_is_explicit():
    result = audit_applications((), as_of=date(2026, 9, 6))

    assert format_integrity_audit(result).endswith("Findings: none")
    assert json.loads(format_integrity_audit(result, as_json=True))["healthy"] is True
