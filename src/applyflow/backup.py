"""Validated, content-safe backups for local ApplyFlow stores."""

from __future__ import annotations

import hashlib
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
