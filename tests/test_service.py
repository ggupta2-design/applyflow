from datetime import date, datetime, timezone

import pytest

from applyflow.models import ApplicationError, ApplicationStatus
from applyflow.service import (
    create_application,
    due_follow_ups,
    get_application,
    list_applications,
    schedule_follow_up,
    transition_application,
)
from applyflow.storage import ApplicationStore


NOW = datetime(2026, 8, 31, 18, 0, tzinfo=timezone.utc)


def test_creates_and_filters_applications(tmp_path):
    store = ApplicationStore(tmp_path / "applications.json")
    saved = create_application(
        store,
        company="Example",
        role="Analyst",
        application_id="saved-1",
        now=NOW,
    )
    applied = create_application(
        store,
        company="Other",
        role="Operations Intern",
        status=ApplicationStatus.APPLIED,
        application_id="applied-1",
        now=NOW,
    )

    assert saved.status == ApplicationStatus.SAVED
    assert applied.applied_on == date(2026, 8, 31)
    assert list_applications(store, status=ApplicationStatus.APPLIED) == (applied,)
    assert list_applications(store, company="example") == (saved,)
    assert get_application(store, "saved-1") == saved


def test_prevents_duplicate_active_opportunities(tmp_path):
    store = ApplicationStore(tmp_path / "applications.json")
    create_application(
        store,
        company="Example",
        role="Data Analyst",
        application_id="first",
        now=NOW,
    )
    with pytest.raises(ApplicationError, match="already exists"):
        create_application(
            store,
            company=" example ",
            role="data analyst",
            application_id="second",
            now=NOW,
        )


def test_enforces_status_transitions_and_history(tmp_path):
    store = ApplicationStore(tmp_path / "applications.json")
    created = create_application(
        store,
        company="Example",
        role="Analyst",
        application_id="app-1",
        now=NOW,
    )
    applied = transition_application(
        store,
        created.id,
        ApplicationStatus.APPLIED,
        note="Submitted on employer site",
        now=NOW,
    )
    interviewing = transition_application(
        store,
        created.id,
        ApplicationStatus.INTERVIEWING,
        now=NOW,
    )

    assert applied.applied_on == date(2026, 8, 31)
    assert applied.history[-1].note == "Submitted on employer site"
    assert interviewing.status == ApplicationStatus.INTERVIEWING
    assert len(interviewing.history) == 3
    with pytest.raises(ApplicationError, match="Cannot move"):
        transition_application(store, created.id, ApplicationStatus.SAVED, now=NOW)


def test_schedules_and_finds_due_follow_ups(tmp_path):
    store = ApplicationStore(tmp_path / "applications.json")
    created = create_application(
        store,
        company="Example",
        role="Analyst",
        application_id="app-1",
        follow_up_on=date(2026, 9, 2),
        now=NOW,
    )
    create_application(
        store,
        company="Later",
        role="Engineer",
        application_id="app-2",
        follow_up_on=date(2026, 9, 10),
        now=NOW,
    )

    assert due_follow_ups(store, as_of=date(2026, 9, 2)) == (created,)
    cleared = schedule_follow_up(store, created.id, None, now=NOW)
    assert cleared.follow_up_on is None
    assert cleared.history[-1].note == "Follow-up cleared"


def test_terminal_status_clears_and_blocks_follow_ups(tmp_path):
    store = ApplicationStore(tmp_path / "applications.json")
    created = create_application(
        store,
        company="Example",
        role="Analyst",
        status=ApplicationStatus.APPLIED,
        application_id="app-1",
        follow_up_on=date(2026, 9, 2),
        now=NOW,
    )
    rejected = transition_application(
        store,
        created.id,
        ApplicationStatus.REJECTED,
        now=NOW,
    )
    assert rejected.follow_up_on is None
    with pytest.raises(ApplicationError, match="Cannot schedule"):
        schedule_follow_up(store, created.id, date(2026, 9, 5), now=NOW)
