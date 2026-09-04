import json
from pathlib import Path

from applyflow.backup import BackupSummary
from applyflow.report import format_backup_summary


SUMMARY = BackupSummary(
    path=Path("/private/home/garima/applyflow.backup.json"),
    application_count=3,
    sha256="a" * 64,
)


def test_formats_readable_backup_metadata_without_parent_path():
    text = format_backup_summary(SUMMARY, action="created")

    assert "Backup created" in text
    assert "Applications: 3" in text
    assert f"SHA-256: {'a' * 64}" in text
    assert "applyflow.backup.json" in text
    assert "/private/home/garima" not in text


def test_formats_machine_readable_backup_metadata():
    payload = json.loads(
        format_backup_summary(
            SUMMARY,
            action="verified",
            as_json=True,
        )
    )

    assert payload == {
        "action": "verified",
        "application_count": 3,
        "file": "applyflow.backup.json",
        "sha256": "a" * 64,
    }
