"""Strict, atomic JSON storage for ApplyFlow."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from .models import Application, ApplicationError, application_from_dict, application_to_dict


class StorageError(ValueError):
    """Raised when the local application store cannot be used safely."""


class ApplicationStore:
    """A versioned JSON application repository."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load(self) -> tuple[Application, ...]:
        if not self.path.exists():
            return ()
        if not self.path.is_file():
            raise StorageError(f"Store path is not a file: {self.path}")
        try:
            payload: Any = json.loads(self.path.read_text(encoding="utf-8"))
        except UnicodeDecodeError as exc:
            raise StorageError(f"Store is not valid UTF-8: {self.path}") from exc
        except json.JSONDecodeError as exc:
            raise StorageError(f"Store is not valid JSON at line {exc.lineno}") from exc
        except OSError as exc:
            raise StorageError(f"Could not read store: {self.path}") from exc

        if not isinstance(payload, dict) or set(payload) != {"schema_version", "applications"}:
            raise StorageError("Store must contain only schema_version and applications")
        if payload["schema_version"] != 1:
            raise StorageError(f"Unsupported store schema_version: {payload['schema_version']}")
        if not isinstance(payload["applications"], list):
            raise StorageError("Store applications must be a list")
        try:
            applications = tuple(application_from_dict(item) for item in payload["applications"])
        except ApplicationError as exc:
            raise StorageError(str(exc)) from exc
        ids = [item.id for item in applications]
        if len(ids) != len(set(ids)):
            raise StorageError("Store contains duplicate application ids")
        return applications

    def save(self, applications: tuple[Application, ...]) -> Path:
        ids = [item.id for item in applications]
        if len(ids) != len(set(ids)):
            raise StorageError("Cannot save duplicate application ids")
        payload = {
            "schema_version": 1,
            "applications": [application_to_dict(item) for item in applications],
        }
        content = json.dumps(payload, indent=2, sort_keys=True) + "\n"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                delete=False,
            ) as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
                temporary = Path(handle.name)
            os.replace(temporary, self.path)
        except OSError as exc:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
            raise StorageError(f"Could not write store: {self.path}") from exc
        return self.path
