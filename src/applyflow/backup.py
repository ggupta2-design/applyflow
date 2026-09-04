"""Validated, content-safe backups for local ApplyFlow stores."""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from pathlib import Path

from .storage import ApplicationStore, StorageError


@dataclass(frozen=True)
class BackupSummary:
    """Value-free metadata describing a validated store snapshot."""

    path: Path
    application_count: int
    sha256: str


def _digest(path: Path) -> str:
    hasher = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                hasher.update(chunk)
    except OSError as exc:
        raise StorageError(f"Could not read backup: {path}") from exc
    return hasher.hexdigest()


def _require_source(path: Path) -> None:
    if not path.exists():
        raise StorageError(f"Source store does not exist: {path}")
    if not path.is_file():
        raise StorageError(f"Source store is not a file: {path}")


def _require_new_destination(source: Path, destination: Path) -> None:
    if source.resolve() == destination.resolve():
        raise StorageError("Backup destination must differ from source store")
    if destination.exists():
        raise StorageError(f"Backup destination already exists: {destination}")


def create_backup(
    source: ApplicationStore,
    destination: str | Path,
) -> BackupSummary:
    """Validate and copy a store atomically without replacing any file."""

    target = Path(destination)
    _require_source(source.path)
    _require_new_destination(source.path, target)
    applications = source.load()
    ApplicationStore(target).save(applications)
    return BackupSummary(
        path=target,
        application_count=len(applications),
        sha256=_digest(target),
    )


def verify_backup(
    path: str | Path,
    *,
    expected_sha256: str | None = None,
) -> BackupSummary:
    """Validate a backup store and optionally compare its SHA-256 digest."""

    target = Path(path)
    _require_source(target)
    applications = ApplicationStore(target).load()
    digest = _digest(target)
    if expected_sha256 is not None:
        expected = expected_sha256.strip().lower()
        if len(expected) != 64 or any(character not in "0123456789abcdef" for character in expected):
            raise StorageError("expected_sha256 must be a 64-character hexadecimal digest")
        if not hmac.compare_digest(digest, expected):
            raise StorageError("Backup checksum does not match expected SHA-256")

    return BackupSummary(
        path=target,
        application_count=len(applications),
        sha256=digest,
    )


def restore_backup(
    backup: str | Path,
    destination: str | Path,
    *,
    confirmed: bool = False,
) -> BackupSummary:
    """Restore a validated backup only to a new, explicitly confirmed path."""

    if not confirmed:
        raise StorageError("Restore requires explicit confirmation")

    source = Path(backup)
    target = Path(destination)
    _require_source(source)
    _require_new_destination(source, target)
    applications = ApplicationStore(source).load()
    ApplicationStore(target).save(applications)
    return BackupSummary(
        path=target,
        application_count=len(applications),
        sha256=_digest(target),
    )
