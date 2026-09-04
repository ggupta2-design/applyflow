from pathlib import Path

import pytest

from applyflow.backup import create_backup, verify_backup
from applyflow.models import Application
from applyflow.storage import ApplicationStore, StorageError


def _store(path: Path) -> ApplicationStore:
    store = ApplicationStore(path)
    store.save(
        (
            Application(
                id="app-1",
                company="Example",
                role="Analyst",
            ),
        )
    )
    return store


def test_creates_validated_backup_without_changing_source(tmp_path):
    source = _store(tmp_path / "applications.json")
    original = source.path.read_bytes()
    destination = tmp_path / "backups" / "applications.backup.json"

    summary = create_backup(source, destination)

    assert summary.path == destination
    assert summary.application_count == 1
    assert len(summary.sha256) == 64
    assert ApplicationStore(destination).load() == source.load()
    assert source.path.read_bytes() == original


def test_backup_refuses_existing_destination(tmp_path):
    source = _store(tmp_path / "applications.json")
    destination = tmp_path / "existing.json"
    destination.write_text("keep me", encoding="utf-8")

    with pytest.raises(StorageError, match="already exists"):
        create_backup(source, destination)

    assert destination.read_text(encoding="utf-8") == "keep me"


def test_backup_refuses_missing_or_same_source(tmp_path):
    missing = ApplicationStore(tmp_path / "missing.json")
    with pytest.raises(StorageError, match="does not exist"):
        create_backup(missing, tmp_path / "backup.json")

    source = _store(tmp_path / "applications.json")
    with pytest.raises(StorageError, match="must differ"):
        create_backup(source, source.path)


def test_backup_rejects_malformed_source_before_writing(tmp_path):
    source_path = tmp_path / "applications.json"
    source_path.write_text("not json", encoding="utf-8")
    destination = tmp_path / "backup.json"

    with pytest.raises(StorageError, match="not valid JSON"):
        create_backup(ApplicationStore(source_path), destination)

    assert not destination.exists()


def test_verifies_backup_and_expected_checksum(tmp_path):
    source = _store(tmp_path / "applications.json")
    backup = create_backup(source, tmp_path / "backup.json")

    verified = verify_backup(
        backup.path,
        expected_sha256=backup.sha256.upper(),
    )

    assert verified == backup


def test_detects_checksum_mismatch(tmp_path):
    source = _store(tmp_path / "applications.json")
    backup = create_backup(source, tmp_path / "backup.json")

    with pytest.raises(StorageError, match="does not match"):
        verify_backup(backup.path, expected_sha256="0" * 64)


@pytest.mark.parametrize("digest", ["", "abc", "g" * 64])
def test_rejects_invalid_expected_checksums(tmp_path, digest):
    source = _store(tmp_path / "applications.json")
    backup = create_backup(source, tmp_path / "backup.json")

    with pytest.raises(StorageError, match="64-character hexadecimal"):
        verify_backup(backup.path, expected_sha256=digest)


def test_verification_rejects_invalid_backup_schema(tmp_path):
    path = tmp_path / "backup.json"
    path.write_text('{"schema_version": 99, "applications": []}', encoding="utf-8")

    with pytest.raises(StorageError, match="Unsupported"):
        verify_backup(path)
