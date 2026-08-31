import json

import pytest

from applyflow.models import Application, ApplicationStatus
from applyflow.storage import ApplicationStore, StorageError


def test_missing_store_loads_as_empty(tmp_path):
    store = ApplicationStore(tmp_path / "applications.json")
    assert store.load() == ()


def test_store_round_trip_and_schema_version(tmp_path):
    path = tmp_path / "data" / "applications.json"
    store = ApplicationStore(path)
    application = Application(
        id="abc123",
        company="Example",
        role="Analyst",
        status=ApplicationStatus.SAVED,
    )

    assert store.save((application,)) == path
    assert store.load() == (application,)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["applications"][0]["id"] == "abc123"
    assert not list(path.parent.glob("*.tmp"))


@pytest.mark.parametrize(
    "content,message",
    [
        ("not json", "not valid JSON"),
        ('{"schema_version": 99, "applications": []}', "Unsupported"),
        ('{"schema_version": 1}', "must contain only"),
    ],
)
def test_rejects_malformed_stores(tmp_path, content, message):
    path = tmp_path / "applications.json"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(StorageError, match=message):
        ApplicationStore(path).load()


def test_rejects_duplicate_application_ids(tmp_path):
    store = ApplicationStore(tmp_path / "applications.json")
    application = Application(id="same", company="One", role="Analyst")
    duplicate = Application(id="same", company="Two", role="Engineer")
    with pytest.raises(StorageError, match="duplicate"):
        store.save((application, duplicate))
