import json
from datetime import datetime, timezone

from applyflow.cli import run
from applyflow.service import create_application
from applyflow.storage import ApplicationStore


def test_add_list_move_and_schedule_workflow(tmp_path, capsys):
    data = tmp_path / "applications.json"

    assert run(
        [
            "--data",
            str(data),
            "add",
            "--company",
            "Example",
            "--role",
            "Data Analyst",
            "--status",
            "applied",
            "--follow-up-on",
            "2026-09-05",
            "--json",
        ]
    ) == 0
    added = json.loads(capsys.readouterr().out)
    application_id = added["applications"][0]["id"]

    assert run(["--data", str(data), "list", "--status", "applied", "--json"]) == 0
    listed = json.loads(capsys.readouterr().out)
    assert listed["count"] == 1
    assert listed["applications"][0]["company"] == "Example"

    assert run(
        [
            "--data",
            str(data),
            "move",
            application_id,
            "interviewing",
            "--note",
            "Phone screen booked",
            "--json",
        ]
    ) == 0
    moved = json.loads(capsys.readouterr().out)
    assert moved["applications"][0]["status"] == "interviewing"

    assert run(
        [
            "--data",
            str(data),
            "schedule",
            application_id,
            "--clear",
            "--json",
        ]
    ) == 0
    scheduled = json.loads(capsys.readouterr().out)
    assert scheduled["applications"][0]["follow_up_on"] is None


def test_due_command_uses_automation_friendly_statuses(tmp_path, capsys):
    data = tmp_path / "applications.json"
    assert run(
        [
            "--data",
            str(data),
            "add",
            "--company",
            "Example",
            "--role",
            "Analyst",
            "--follow-up-on",
            "2026-09-01",
        ]
    ) == 0
    capsys.readouterr()

    assert run(
        ["--data", str(data), "due", "--as-of", "2026-09-01", "--json"]
    ) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["count"] == 1
    assert payload["as_of"] == "2026-09-01"

    assert run(
        ["--data", str(data), "due", "--as-of", "2026-08-31", "--json"]
    ) == 0
    assert json.loads(capsys.readouterr().out)["count"] == 0


def test_cli_reports_duplicate_and_transition_errors(tmp_path, capsys):
    data = tmp_path / "applications.json"
    command = [
        "--data",
        str(data),
        "add",
        "--company",
        "Example",
        "--role",
        "Analyst",
    ]
    assert run(command) == 0
    output = capsys.readouterr().out
    application_id = output.split("|")[0].split("- ")[1].strip()

    assert run(command) == 2
    assert "already exists" in capsys.readouterr().err

    assert run(
        ["--data", str(data), "move", application_id, "offer"]
    ) == 2
    assert "Cannot move" in capsys.readouterr().err


def test_cli_rejects_malformed_store(tmp_path, capsys):
    data = tmp_path / "applications.json"
    data.write_text("not json", encoding="utf-8")
    assert run(["--data", str(data), "list"]) == 2
    assert "not valid JSON" in capsys.readouterr().err



def test_pipeline_command_reports_stage_metrics(tmp_path, capsys):
    data = tmp_path / "applications.json"
    assert run(
        [
            "--data",
            str(data),
            "add",
            "--company",
            "Example",
            "--role",
            "Analyst",
            "--status",
            "applied",
        ]
    ) == 0
    capsys.readouterr()
    assert run(
        [
            "--data",
            str(data),
            "add",
            "--company",
            "Other",
            "--role",
            "Engineer",
        ]
    ) == 0
    capsys.readouterr()

    assert run(["--data", str(data), "pipeline", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["total"] == 2
    assert payload["submitted"] == 1
    assert payload["status_counts"]["applied"] == 1
    assert payload["status_counts"]["saved"] == 1



def test_stale_command_uses_review_exit_statuses(tmp_path, capsys):
    data = tmp_path / "applications.json"
    create_application(
        ApplicationStore(data),
        company="Example",
        role="Analyst",
        application_id="old",
        now=datetime(2026, 8, 1, tzinfo=timezone.utc),
    )

    assert run(
        [
            "--data",
            str(data),
            "stale",
            "--as-of",
            "2026-09-01",
            "--inactive-days",
            "14",
            "--json",
        ]
    ) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["count"] == 1
    assert payload["applications"][0]["inactive_days"] == 31

    assert run(
        [
            "--data",
            str(data),
            "stale",
            "--as-of",
            "2026-08-10",
            "--inactive-days",
            "14",
            "--json",
        ]
    ) == 0
    assert json.loads(capsys.readouterr().out)["count"] == 0



def test_stale_command_rejects_invalid_thresholds(tmp_path, capsys):
    data = tmp_path / "applications.json"
    assert run(
        [
            "--data",
            str(data),
            "stale",
            "--as-of",
            "2026-09-01",
            "--inactive-days",
            "0",
        ]
    ) == 2
    assert "positive integer" in capsys.readouterr().err


def test_note_command_records_note_without_echoing_it(tmp_path, capsys):
    data = tmp_path / "applications.json"
    store = ApplicationStore(data)
    application = create_application(
        store,
        company="Example",
        role="Analyst",
        application_id="app-1",
    )
    private_note = "Recruiter prefers a private contact channel"

    assert run(
        [
            "--data",
            str(data),
            "note",
            application.id,
            "--text",
            private_note,
            "--json",
        ]
    ) == 0
    output = capsys.readouterr().out
    payload = json.loads(output)

    assert payload["applications"][0]["id"] == application.id
    assert private_note not in output
    assert ApplicationStore(data).load()[0].history[-1].note == private_note


def test_note_command_rejects_blank_text(tmp_path, capsys):
    data = tmp_path / "applications.json"
    application = create_application(
        ApplicationStore(data),
        company="Example",
        role="Analyst",
        application_id="app-1",
    )

    assert run(
        ["--data", str(data), "note", application.id, "--text", "   "]
    ) == 2
    assert "note cannot be blank" in capsys.readouterr().err


def test_history_command_requires_explicit_note_disclosure(tmp_path, capsys):
    data = tmp_path / "applications.json"
    application = create_application(
        ApplicationStore(data),
        company="Example",
        role="Analyst",
        application_id="app-1",
    )
    private_note = "Private preparation details"
    assert run(
        ["--data", str(data), "note", application.id, "--text", private_note]
    ) == 0
    capsys.readouterr()

    assert run(
        ["--data", str(data), "history", application.id, "--json"]
    ) == 0
    hidden_output = capsys.readouterr().out
    hidden = json.loads(hidden_output)
    assert hidden["notes_included"] is False
    assert private_note not in hidden_output

    assert run(
        [
            "--data",
            str(data),
            "history",
            application.id,
            "--include-notes",
            "--json",
        ]
    ) == 0
    included = json.loads(capsys.readouterr().out)
    assert included["notes_included"] is True
    assert included["activity"][-1]["note"] == private_note


def test_activity_command_filters_dates_and_limits_results(tmp_path, capsys):
    data = tmp_path / "applications.json"
    store = ApplicationStore(data)
    create_application(
        store,
        company="Older",
        role="Analyst",
        application_id="old",
        now=datetime(2026, 8, 30, tzinfo=timezone.utc),
    )
    create_application(
        store,
        company="Recent",
        role="Engineer",
        application_id="new",
        now=datetime(2026, 9, 2, tzinfo=timezone.utc),
    )

    assert run(
        [
            "--data",
            str(data),
            "activity",
            "--since",
            "2026-09-01",
            "--limit",
            "1",
            "--json",
        ]
    ) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["count"] == 1
    assert payload["activity"][0]["application_id"] == "new"
    assert payload["notes_included"] is False


def test_activity_command_rejects_invalid_limit(tmp_path, capsys):
    data = tmp_path / "applications.json"

    assert run(
        ["--data", str(data), "activity", "--limit", "0"]
    ) == 2
    assert "positive integer" in capsys.readouterr().err


def test_plan_command_reports_prioritized_actions(tmp_path, capsys):
    data = tmp_path / "applications.json"
    store = ApplicationStore(data)
    create_application(
        store,
        company="Overdue",
        role="Analyst",
        application_id="overdue",
        follow_up_on=datetime(2026, 9, 1).date(),
        now=datetime(2026, 8, 20, tzinfo=timezone.utc),
    )
    create_application(
        store,
        company="Upcoming",
        role="Engineer",
        application_id="upcoming",
        follow_up_on=datetime(2026, 9, 5).date(),
        now=datetime(2026, 9, 2, tzinfo=timezone.utc),
    )

    assert run(
        [
            "--data",
            str(data),
            "plan",
            "--as-of",
            "2026-09-03",
            "--horizon-days",
            "7",
            "--json",
        ]
    ) == 1
    payload = json.loads(capsys.readouterr().out)

    assert payload["count"] == 2
    assert [item["kind"] for item in payload["actions"]] == [
        "overdue_follow_up",
        "upcoming_follow_up",
    ]
    assert payload["actions"][0]["application"]["id"] == "overdue"


def test_plan_command_returns_zero_for_empty_plan(tmp_path, capsys):
    data = tmp_path / "applications.json"

    assert run(
        ["--data", str(data), "plan", "--as-of", "2026-09-03", "--json"]
    ) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["count"] == 0
    assert payload["truncated"] is False
