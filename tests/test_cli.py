import json

from applyflow.cli import run


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
