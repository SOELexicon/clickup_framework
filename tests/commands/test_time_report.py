"""Tests for the read-only ``cum time report`` timesheet command and its helpers."""

from __future__ import annotations

import json
from argparse import Namespace
from datetime import date, datetime, timedelta, timezone
from unittest.mock import Mock, patch

import pytest

from clickup_framework.client import ClickUpClient
from clickup_framework.commands.time_commands import TimeReportCommand
from clickup_framework.commands.time_report_helpers import (
    build_time_report,
    derive_comment_activities,
    derive_open_work,
    derive_schedule_items,
    derive_task_activities,
    format_hours,
    render_html,
    render_json,
    render_markdown,
    resolve_report_range,
    resolve_report_timezone,
)
from clickup_framework.commands.time_report_helpers.report_builder import local_midnight_ms

UTC = timezone.utc
HOUR = 3_600_000
USER = {"id": "42", "username": "Ada", "email": "ada@example.com"}


def _ms(year, month, day, hour=0, minute=0):
    return int(datetime(year, month, day, hour, minute, tzinfo=UTC).timestamp() * 1000)


def _entry(start_ms, duration_ms, task_id="t1", name="Task One", **extra):
    return {
        "id": f"e{start_ms}",
        "task_id": task_id,
        "task_name": name,
        "task_url": f"https://app.clickup.com/t/{task_id}",
        "status": "in progress",
        "location": "Folder / List",
        "start_ms": start_ms,
        "end_ms": start_ms + duration_ms,
        "duration_ms": duration_ms,
        "description": extra.pop("description", ""),
        "running": extra.pop("running", False),
        "billable": False,
        **extra,
    }


def _report(
    entries,
    activities=(),
    start=date(2026, 10, 5),
    end=date(2026, 10, 18),
    schedule=(),
    open_work=(),
):
    return build_time_report(
        user=USER,
        workspace_id="team-1",
        entries=entries,
        activities=activities,
        start=start,
        end=end,
        tz=UTC,
        tz_label="UTC",
        notes=["a note"],
        generated_at=datetime(2026, 10, 12, 9, 0, tzinfo=UTC),
        schedule=schedule,
        open_work=open_work,
    )


# ==================== range and calendar ====================


def test_default_range_is_current_monday_to_sunday():
    assert resolve_report_range(date(2026, 10, 14)) == (date(2026, 10, 12), date(2026, 10, 18))


def test_weeks_extend_backwards_in_whole_weeks():
    assert resolve_report_range(date(2026, 10, 14), weeks=3) == (
        date(2026, 9, 28),
        date(2026, 10, 18),
    )


def test_explicit_and_partial_ranges():
    today = date(2026, 10, 14)
    assert resolve_report_range(today, start=date(2026, 10, 1), end=date(2026, 10, 3)) == (
        date(2026, 10, 1),
        date(2026, 10, 3),
    )
    assert resolve_report_range(today, start=date(2026, 10, 1)) == (
        date(2026, 10, 1),
        date(2026, 10, 18),
    )
    assert resolve_report_range(today, weeks=2, end=date(2026, 9, 9)) == (
        date(2026, 8, 31),
        date(2026, 9, 9),
    )


def test_start_after_end_is_rejected():
    with pytest.raises(ValueError):
        resolve_report_range(date(2026, 10, 14), start=date(2026, 10, 9), end=date(2026, 10, 1))


def test_day_boundaries_survive_the_october_clock_change():
    london = resolve_report_timezone("Europe/London")
    if london is None:
        pytest.skip("IANA time zone data not available on this machine")
    day_ms = local_midnight_ms(date(2026, 10, 26), london) - local_midnight_ms(
        date(2026, 10, 25), london
    )
    assert day_ms == 25 * HOUR


def test_unknown_timezone_falls_back_to_system_local():
    assert resolve_report_timezone("Not/AZone") is None
    assert resolve_report_timezone(None) is None


def test_format_hours_is_timesheet_friendly():
    assert format_hours(0) == "0m"
    assert format_hours(20_000) == "<1m"
    assert format_hours(HOUR) == "1h"
    assert format_hours(45 * 60_000) == "45m"
    assert format_hours(38 * HOUR + 15 * 60_000) == "38h 15m"


# ==================== aggregation ====================


def test_totals_roll_up_by_day_week_and_task():
    entries = [
        _entry(_ms(2026, 10, 6, 9), 2 * HOUR, description="build"),
        _entry(_ms(2026, 10, 6, 13), HOUR, task_id="t2", name="Task Two"),
        _entry(_ms(2026, 10, 9, 10), 30 * 60_000, description="review"),
        _entry(_ms(2026, 10, 13, 8), 3 * HOUR),
    ]
    report = _report(entries)

    assert report["summary"]["total_ms"] == 6.5 * HOUR
    assert report["summary"]["entry_count"] == 4
    assert report["summary"]["days_tracked"] == 3
    assert report["summary"]["task_count"] == 2
    assert [w["week_start"] for w in report["weeks"]] == ["2026-10-05", "2026-10-12"]
    assert [len(w["days"]) for w in report["weeks"]] == [7, 7]

    week_one = report["weeks"][0]
    assert week_one["total_ms"] == 3.5 * HOUR
    tue = week_one["days"][1]
    assert tue["date"] == "2026-10-06" and tue["total_ms"] == 3 * HOUR
    assert [t["task_id"] for t in tue["tasks"]] == ["t1", "t2"]

    task_one = next(t for t in week_one["tasks"] if t["task_id"] == "t1")
    assert task_one["per_day"] == {"2026-10-06": 2 * HOUR, "2026-10-09": 30 * 60_000}
    assert task_one["total_ms"] == 2.5 * HOUR

    overall_t1 = next(t for t in report["tasks"] if t["task_id"] == "t1")
    assert overall_t1["total_ms"] == 5.5 * HOUR and overall_t1["entry_count"] == 3


def test_entry_crossing_midnight_counts_toward_start_day():
    report = _report([_entry(_ms(2026, 10, 6, 23), 2 * HOUR)])
    days = {d["date"]: d["total_ms"] for d in report["weeks"][0]["days"]}
    assert days["2026-10-06"] == 2 * HOUR
    assert days["2026-10-07"] == 0


def test_entries_outside_range_are_ignored_and_running_flagged():
    entries = [
        _entry(_ms(2026, 10, 4, 9), HOUR),
        _entry(_ms(2026, 10, 7, 9), HOUR, running=True),
    ]
    report = _report(entries)
    assert report["summary"]["entry_count"] == 1
    assert report["summary"]["running_entries"] == 1
    entry = report["weeks"][0]["days"][2]["entries"][0]
    assert entry["running"] is True and entry["end_time"] == ""


# ==================== touched tasks ====================


def _task(task_id, *, creator="42", created=None, updated=None, closed=None):
    return {
        "id": task_id,
        "name": f"Task {task_id}",
        "url": f"https://app.clickup.com/t/{task_id}",
        "status": {"status": "open"},
        "creator": {"id": int(creator)},
        "date_created": str(created) if created else None,
        "date_updated": str(updated) if updated else None,
        "date_closed": str(closed) if closed else None,
        "folder": {"name": "hidden"},
        "list": {"name": "Backlog"},
    }


def test_task_activities_label_attribution_honestly():
    start_ms, end_ms = _ms(2026, 10, 5), _ms(2026, 10, 19) - 1
    tasks = [
        _task("a", created=_ms(2026, 10, 6, 9)),
        _task("b", creator="99", created=_ms(2026, 10, 6, 9), updated=_ms(2026, 10, 8, 9)),
        _task("c", updated=_ms(2026, 10, 9, 17), closed=_ms(2026, 10, 9, 17)),
        _task("d", created=_ms(2026, 9, 1)),
    ]
    report = _report([], derive_task_activities(tasks, "42", start_ms, end_ms))
    days = {d["date"]: d for w in report["weeks"] for d in w["days"]}

    created = days["2026-10-06"]["touched"]
    assert [t["task_id"] for t in created] == ["a"]
    assert created[0]["attributed"] is True
    assert created[0]["location"] == "Backlog"

    updated = days["2026-10-08"]["touched"][0]
    assert updated["task_id"] == "b" and updated["attributed"] is False
    assert updated["signals"][0]["kind"] == "updated"
    assert "actor unknown" in updated["signals"][0]["label"]

    closed = days["2026-10-09"]["touched"][0]
    assert [s["kind"] for s in closed["signals"]] == ["closed"]

    assert report["summary"]["touched_task_count"] == 1


def test_comment_activities_only_count_the_users_comments_in_range():
    info = {"task_id": "x", "name": "X", "url": "", "status": "", "location": ""}
    comments = [
        {"user": {"id": 42}, "date": str(_ms(2026, 10, 7, 10))},
        {"user": {"id": 42}, "date": str(_ms(2026, 10, 7, 11))},
        {"user": {"id": 7}, "date": str(_ms(2026, 10, 7, 12))},
        {"user": {"id": 42}, "date": str(_ms(2026, 9, 1))},
    ]
    activities = derive_comment_activities(
        info, comments, "42", _ms(2026, 10, 5), _ms(2026, 10, 19)
    )
    report = _report([_entry(_ms(2026, 10, 7, 9), HOUR, task_id="x", name="X")], activities)

    touched = report["weeks"][0]["days"][2]["touched"][0]
    assert [s["label"] for s in touched["signals"]] == ["Tracked 1h (1 entry)", "2 comments"]
    assert touched["attributed"] is True


# ==================== due / start dates ====================


def test_schedule_items_dedupe_merge_and_flag_overdue():
    start_ms, end_ms = _ms(2026, 10, 5), _ms(2026, 10, 19) - 1
    same_day = _task("m")
    same_day.update(due_date=str(_ms(2026, 10, 7, 17)), start_date=str(_ms(2026, 10, 7, 9)))
    overdue = _task("o")
    overdue["due_date"] = str(_ms(2026, 10, 6, 17))
    done = _task("d", closed=_ms(2026, 10, 6, 12))
    done["due_date"] = str(_ms(2026, 10, 6, 17))
    future = _task("f")
    future["due_date"] = str(_ms(2026, 10, 16, 17))
    outside = _task("x")
    outside["due_date"] = str(_ms(2026, 11, 2))

    tasks = [same_day, overdue, done, future, outside, dict(overdue)]
    items = derive_schedule_items(tasks, start_ms, end_ms)
    assert sorted(i["task_id"] + i["kind"] for i in items) == [
        "ddue", "fdue", "mdue", "mstart", "odue",
    ]

    report = _report([], schedule=items)
    days = {d["date"]: d for w in report["weeks"] for d in w["days"]}

    merged = days["2026-10-07"]["scheduled"]
    assert len(merged) == 1 and merged[0]["due"] and merged[0]["starts"]

    tue = days["2026-10-06"]["scheduled"]
    assert [(s["task_id"], s["overdue"], s["closed"]) for s in tue] == [
        ("o", True, False),
        ("d", False, True),
    ]
    assert days["2026-10-16"]["scheduled"][0]["overdue"] is False
    assert report["summary"]["due_count"] == 4
    assert report["summary"]["starting_count"] == 1
    # Report "today" is 2026-10-12, so both open tasks due earlier that week are overdue.
    assert merged[0]["overdue"] is True
    assert report["summary"]["overdue_count"] == 2

    html_text = render_html(report)
    assert "Due or starting" in html_text and "Overdue" in html_text
    markdown_text = render_markdown(report)
    assert "Due or starting:" in markdown_text and ": Overdue" in markdown_text


def test_open_work_includes_overdue_and_future_due_with_blank_or_past_start():
    today = date(2026, 10, 12)
    today_start = local_midnight_ms(today, UTC)
    today_end = local_midnight_ms(today + timedelta(days=1), UTC) - 1

    future_blank = _task("blank")
    future_blank["due_date"] = str(_ms(2026, 11, 2, 17))
    future_blank["time_estimate"] = 4 * HOUR

    started = _task("gone")
    started["start_date"] = str(_ms(2026, 10, 1, 9))
    started["due_date"] = str(_ms(2026, 10, 20, 17))
    started["time_estimate"] = HOUR
    child = _task("sub")
    child["parent"] = "gone"
    child["due_date"] = str(_ms(2026, 10, 20, 17))
    child["time_estimate"] = 2 * HOUR

    overdue = _task("old")
    overdue["due_date"] = str(_ms(2026, 9, 1, 17))

    starts_today = _task("today")
    starts_today["start_date"] = str(_ms(2026, 10, 12, 9))
    starts_today["due_date"] = str(_ms(2026, 10, 20, 17))

    starts_later = _task("later")
    starts_later["start_date"] = str(_ms(2026, 10, 15, 9))
    starts_later["due_date"] = str(_ms(2026, 11, 1, 17))

    due_today = _task("due")
    due_today["due_date"] = str(_ms(2026, 10, 12, 17))

    closed = _task("done", closed=_ms(2026, 9, 2))
    closed["due_date"] = str(_ms(2026, 9, 1, 17))

    tasks = [
        future_blank,
        started,
        dict(started),
        child,
        overdue,
        starts_today,
        starts_later,
        due_today,
        closed,
        _task("none"),
    ]
    items = derive_open_work(tasks, today_start, today_end)
    assert [item["task_id"] for item in items] == ["old", "gone", "sub", "today", "blank"]
    assert items[0]["overdue"] is True and items[1]["in_progress"] is True
    assert items[1]["estimate_ms"] == HOUR
    assert items[1]["total_estimate_ms"] == 3 * HOUR
    assert items[2]["estimate_ms"] == 2 * HOUR and items[2]["total_estimate_ms"] == 2 * HOUR
    assert items[4]["estimate"] == "4h" and items[4]["total_estimate"] == "4h"

    report = _report([], open_work=items)
    assert report["summary"]["open_work_overdue_count"] == 1
    assert report["summary"]["open_work_in_progress_count"] == 4
    # "gone" already includes "sub", so the plate total is 3h + 4h, not 3h + 2h + 4h.
    assert report["summary"]["open_work_total_estimate_ms"] == 7 * HOUR
    assert report["summary"]["open_work_estimate_ms"] == 7 * HOUR

    html_text = render_html(report)
    assert "In progress and overdue" in html_text
    assert "Est 1h / Total 3h" in html_text
    assert "Task later" not in html_text
    markdown_text = render_markdown(report)
    assert "## In progress and overdue" in markdown_text
    assert "Est 4h / Total 4h" in markdown_text

    scheduled = derive_schedule_items(
        [started, child], _ms(2026, 10, 20), _ms(2026, 10, 21) - 1
    )
    due = next(item for item in scheduled if item["task_id"] == "gone")
    assert due["total_estimate_ms"] == 3 * HOUR


# ==================== renderers ====================


def test_renderers_escape_task_names():
    nasty = '<script>alert(1)</script> | [x]'
    report = _report([_entry(_ms(2026, 10, 6, 9), HOUR, name=nasty, description="a|b")])

    html_text = render_html(report)
    assert "<script>" not in html_text
    assert "&lt;script&gt;" in html_text
    assert "<link" not in html_text and "src=" not in html_text

    markdown_text = render_markdown(report)
    assert "\\| \\[x\\]" in markdown_text
    assert "a\\|b" in markdown_text

    assert json.loads(render_json(report))["summary"]["total_ms"] == HOUR


def test_markdown_lists_weeks_days_and_notes():
    report = _report([_entry(_ms(2026, 10, 6, 9), HOUR)])
    text = render_markdown(report)
    assert "## Week 41: 5 Oct to 11 Oct 2026 (1h)" in text
    assert "#### Tue 6 Oct 2026 (1h)" in text
    assert "## All tasks in range" in text
    assert "- a note" in text
    em_dash = chr(0x2014)
    assert em_dash not in text and em_dash not in render_html(report)


# ==================== command (read-only) ====================


def _command_args(tmp_path, **overrides):
    values = dict(
        user_id=None,
        user_id_flag=None,
        team_id=None,
        weeks=1,
        start_date="2026-10-05",
        end_date="2026-10-11",
        format="html",
        report_output_file=str(tmp_path / "report.html"),
        timezone="UTC",
        no_touched=False,
        no_scheduled=False,
        colorize=False,
    )
    values.update(overrides)
    return Namespace(**values)


def _raw_entry(user_id="42"):
    return {
        "id": "e1",
        "task": {"id": "t1", "name": "Task One", "status": {"status": "open"}},
        "task_url": "https://app.clickup.com/t/t1",
        "task_location": {"folder_name": "hidden", "list_name": "Backlog"},
        "user": {"id": int(user_id), "username": "Ada"},
        "start": str(_ms(2026, 10, 6, 9)),
        "end": str(_ms(2026, 10, 6, 11)),
        "duration": str(2 * HOUR),
        "description": "deep work",
    }


def _mock_client():
    client = Mock()
    client.get_authorized_user.return_value = {"user": {**USER, "id": 42, "timezone": "UTC"}}
    client.get_time_entries.return_value = {"data": [_raw_entry()]}
    client.get_team_tasks.return_value = {"tasks": [], "last_page": True}
    client.get_task_comments.return_value = {"comments": []}
    client.get_authorized_workspaces.return_value = {
        "teams": [{"id": "team-1", "members": [{"user": {"id": 7, "username": "Bob"}}]}]
    }
    return client


def _run(args, client):
    context = Mock()
    context.get_ansi_output.return_value = False
    with patch("clickup_framework.commands.base_command.get_context_manager", return_value=context):
        with patch("clickup_framework.commands.base_command.ClickUpClient", return_value=client):
            command = TimeReportCommand(args, command_name="time")
            with patch.object(command, "resolve_id", return_value="team-1"):
                command.execute()


def test_report_only_calls_read_endpoints_and_writes_html(tmp_path):
    client = _mock_client()
    _run(_command_args(tmp_path), client)

    called = {name.split(".")[0] for name, _, _ in client.method_calls}
    assert called, "expected API reads"
    assert all(name.startswith("get_") for name in called), called

    params = client.get_time_entries.call_args.kwargs
    assert "assignee" not in params
    assert params["include_location_names"] == "true"
    client.get_task_comments.assert_called_once_with("t1")

    html_text = (tmp_path / "report.html").read_text(encoding="utf-8")
    assert "Task One" in html_text and "2h" in html_text


def test_report_json_to_stdout_for_another_user(tmp_path, capsys):
    client = _mock_client()
    client.get_time_entries.return_value = {"data": [_raw_entry(user_id="7")]}
    args = _command_args(tmp_path, user_id="7", format="json", report_output_file=None)
    _run(args, client)

    assert client.get_time_entries.call_args.kwargs["assignee"] == "7"
    payload = json.loads(capsys.readouterr().out)
    assert payload["user"]["username"] == "Bob"
    assert payload["summary"]["total_ms"] == 2 * HOUR


def test_report_refuses_entries_belonging_to_someone_else(tmp_path):
    client = _mock_client()
    args = _command_args(tmp_path, user_id="7")
    with pytest.raises(SystemExit):
        _run(args, client)
    assert not (tmp_path / "report.html").exists()


def test_report_explains_permission_errors_for_other_users(tmp_path, capsys):
    client = _mock_client()
    client.get_time_entries.side_effect = RuntimeError("403 Forbidden")
    with pytest.raises(SystemExit):
        _run(_command_args(tmp_path, user_id="7"), client)
    assert "Owner or Admin" in capsys.readouterr().err


def test_no_touched_and_no_scheduled_skip_task_reads(tmp_path):
    client = _mock_client()
    _run(_command_args(tmp_path, no_touched=True, no_scheduled=True), client)
    client.get_team_tasks.assert_not_called()
    client.get_task_comments.assert_not_called()


def test_no_touched_still_reads_schedule_but_not_comments(tmp_path):
    client = _mock_client()
    _run(_command_args(tmp_path, no_touched=True), client)
    client.get_task_comments.assert_not_called()
    filters = [call.kwargs for call in client.get_team_tasks.call_args_list]
    assert any("due_date_gt" in f and f["include_closed"] for f in filters)
    assert any("date_updated_gt" in f for f in filters)
    assert any(f.get("include_closed") is False for f in filters)
    assert all(f["assignees"] == ["42"] and f["subtasks"] for f in filters)


def test_schedule_lists_due_and_start_dates_from_the_command(tmp_path, capsys):
    client = _mock_client()
    due_task = _task("s1", updated=_ms(2026, 9, 1))
    due_task["due_date"] = str(_ms(2026, 10, 8, 16))
    due_task["start_date"] = str(_ms(2026, 10, 6, 9))
    client.get_team_tasks.return_value = {"tasks": [due_task], "last_page": True}
    _run(_command_args(tmp_path, format="json", report_output_file=None), client)

    days = {d["date"]: d for w in json.loads(capsys.readouterr().out)["weeks"] for d in w["days"]}
    assert [s["task_id"] for s in days["2026-10-08"]["scheduled"]] == ["s1"]
    assert days["2026-10-08"]["scheduled"][0]["due"] is True
    assert days["2026-10-06"]["scheduled"][0]["starts"] is True


def test_plate_uses_cached_open_tasks_the_due_filter_would_drop(tmp_path, capsys):
    client = _mock_client()
    today = datetime.now(UTC).date()
    future = today + timedelta(days=40)
    past = today - timedelta(days=40)
    later = today + timedelta(days=10)

    spanning = _task("span")
    spanning["due_date"] = str(_ms(future.year, future.month, future.day, 12))
    spanning["start_date"] = str(_ms(past.year, past.month, past.day, 12))
    spanning["time_estimate"] = 2 * HOUR
    child = _task("kid")
    child["parent"] = "span"
    child["due_date"] = str(_ms(future.year, future.month, future.day, 12))
    child["time_estimate"] = HOUR
    overdue = _task("late")
    overdue["due_date"] = str(_ms(past.year, past.month, past.day, 12))
    overdue["time_estimate"] = 30 * 60_000
    not_started = _task("wait")
    not_started["start_date"] = str(_ms(later.year, later.month, later.day, 12))
    not_started["due_date"] = str(_ms(future.year, future.month, future.day, 12))

    def get_team_tasks(team_id, **kwargs):
        if kwargs.get("due_date_gt") is not None or kwargs.get("date_updated_gt") is not None:
            return {"tasks": [], "last_page": True}
        return {"tasks": [spanning, child, overdue, not_started], "last_page": True}

    client.get_team_tasks.side_effect = get_team_tasks
    _run(_command_args(tmp_path, format="json", report_output_file=None), client)
    output = capsys.readouterr().out
    payload = json.loads(output)

    plate = {item["task_id"]: item for item in payload["open_work"]}
    assert set(plate) == {"span", "kid", "late"}
    assert plate["late"]["overdue"] is True
    assert plate["span"]["in_progress"] is True
    assert plate["span"]["estimate_ms"] == 2 * HOUR
    assert plate["span"]["total_estimate_ms"] == 3 * HOUR
    assert payload["summary"]["open_work_total_estimate_ms"] == 3 * HOUR + 30 * 60_000
    assert "Task wait" not in output


def test_boolean_query_params_are_lowercase_for_clickup():
    client = ClickUpClient(api_token="pk_test")
    response = Mock(status_code=200)
    response.json.return_value = {"tasks": [], "last_page": True}
    client.session = Mock()
    client.session.request.return_value = response
    client.rate_limiter = Mock()

    client.get_team_tasks("team-1", subtasks=True, include_closed=False, assignees=["42"])

    params = client.session.request.call_args.kwargs["params"]
    assert params["subtasks"] == "true"
    assert params["include_closed"] == "false"
    assert params["assignees[]"] == ["42"]
