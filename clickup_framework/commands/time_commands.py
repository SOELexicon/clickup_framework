"""Time tracking commands for ClickUp Framework CLI.

Variables:  COMMAND_METADATA, REPORT_FORMATS, REPORT_FILE_EXTENSIONS, REPORT_MAX_TASK_PAGES,
            REPORT_COMMENT_PAGE_SIZE, REPORT_WEEK_START
Functions:  _parse_date_to_ms, _parse_report_date, _coerce_entries, _coerce_entry, _entry_task,
            _entry_task_id, _entry_task_name, _entry_user_id, _entry_user_name,
            _entry_description, _entry_start_ms, _entry_end_ms, _entry_duration_ms,
            _entry_is_running, _format_description_cell, _report_entry, _report_file_name,
            time_start_command, time_stop_command, time_status_command, time_list_command,
            time_add_command, time_delete_command, time_report_command, register_command
Classes:    TimeCommandBase, TimeStartCommand, TimeStopCommand, TimeStatusCommand,
            TimeListCommand, TimeAddCommand, TimeDeleteCommand, TimeReportCommand
"""

from __future__ import annotations

import re
import sys
from datetime import date, datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional, Tuple

from clickup_framework.commands.base_command import BaseCommand
from clickup_framework.commands.time_report_helpers import (
    build_time_report,
    derive_comment_activities,
    derive_open_work,
    derive_schedule_items,
    derive_task_activities,
    estimates_for,
    local_midnight_ms,
    range_bounds_ms,
    render_html,
    render_json,
    render_markdown,
    resolve_report_range,
    resolve_report_timezone,
    task_info_from_task,
    task_updated_after,
    timezone_label,
)
from clickup_framework.resources import TimeAPI
from clickup_framework.utils import format_duration, format_timestamp, parse_duration_to_ms
from clickup_framework.utils.argparse_helpers import raw_text_formatter
from clickup_framework.commands.utils import add_common_args


COMMAND_METADATA = {
    "category": "⏱️  Time Tracking",
    "commands": [
        {
            "name": "time",
            "args": "start|stop|status|list|add|delete|report [options]",
            "description": (
                "Start, stop, inspect, list, add, and delete ClickUp time entries, "
                "or build a read-only weekly timesheet report"
            ),
        }
    ],
}

REPORT_FORMATS = ("html", "json", "markdown")
REPORT_FILE_EXTENSIONS = {"html": "html", "json": "json", "markdown": "md"}
# Safety valve on the assigned-tasks scan: 20 pages x 100 tasks is far more than one person
# updates in a few weeks, and far less than an accidental whole-workspace crawl.
REPORT_MAX_TASK_PAGES = 20
# ClickUp's task comment endpoint hands back the 25 most recent comments per call.
REPORT_COMMENT_PAGE_SIZE = 25
# Weeks run Monday to Sunday, matching week_start_day=1 on the ClickUp user profile.
REPORT_WEEK_START = 0


def _sidebar_index(value: Any) -> int:
    """ClickUp sidebar orderindex, or a large number when it is missing."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return 1_000_000_000


def _parse_date_to_ms(value: str, *, end_of_day: bool = False) -> int:
    """Parse a YYYY-MM-DD date string into a local Unix timestamp in ms."""
    try:
        date_value = datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"Invalid date '{value}'. Use YYYY-MM-DD.") from exc

    if end_of_day:
        date_value = date_value + timedelta(days=1) - timedelta(milliseconds=1)

    return int(date_value.timestamp() * 1000)


def _parse_report_date(value: Optional[str]) -> Optional[date]:
    """Parse an optional YYYY-MM-DD string into a calendar date."""
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(f"Invalid date '{value}'. Use YYYY-MM-DD.") from exc


def _coerce_entries(result: Any) -> List[Dict[str, Any]]:
    """Normalize varied ClickUp time-entry responses to a list of entry dicts."""
    if result is None:
        return []
    if isinstance(result, list):
        return [item for item in result if isinstance(item, dict)]
    if not isinstance(result, dict):
        return []

    data = result.get("data")
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        return [data]
    if "id" in result:
        return [result]
    return []


def _coerce_entry(result: Any) -> Optional[Dict[str, Any]]:
    """Normalize a ClickUp time-entry response to a single entry dict."""
    entries = _coerce_entries(result)
    return entries[0] if entries else None


def _entry_task(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Return the task payload or a best-effort fallback task object."""
    task = entry.get("task")
    if isinstance(task, dict):
        return task

    task_id = entry.get("tid") or entry.get("task_id")
    if task_id:
        return {"id": str(task_id)}

    return {}


def _entry_task_id(entry: Dict[str, Any]) -> str:
    """Return the best-known task ID for an entry."""
    task = _entry_task(entry)
    return str(task.get("id") or entry.get("tid") or entry.get("task_id") or "")


def _entry_task_name(entry: Dict[str, Any]) -> str:
    """Return the best-known task name for an entry."""
    task = _entry_task(entry)
    return task.get("name") or entry.get("task_name") or "Unknown task"


def _entry_user_name(entry: Dict[str, Any]) -> str:
    """Return the best-known username for an entry."""
    user = entry.get("user")
    if isinstance(user, dict):
        return user.get("username") or user.get("name") or "Unknown"
    return "Unknown"


def _entry_user_id(entry: Dict[str, Any]) -> str:
    """Return the entry owner's user ID as a string, or empty when absent."""
    user = entry.get("user")
    if isinstance(user, dict) and user.get("id") is not None:
        return str(user["id"])
    return ""


def _entry_description(entry: Dict[str, Any]) -> str:
    """Return a safe description string."""
    return (entry.get("description") or "").strip()


def _entry_start_ms(entry: Dict[str, Any]) -> Optional[int]:
    """Return the entry start timestamp in ms when available."""
    value = entry.get("start")
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _entry_end_ms(entry: Dict[str, Any]) -> Optional[int]:
    """Return the entry end timestamp in ms when available."""
    value = entry.get("end")
    if value in (None, ""):
        value = entry.get("at")
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _entry_duration_ms(entry: Dict[str, Any]) -> int:
    """Return entry duration in ms, inferring running timers from start time."""
    try:
        duration = int(entry.get("duration") or 0)
    except (TypeError, ValueError):
        duration = 0

    if duration < 0:
        start = _entry_start_ms(entry)
        if start is not None:
            return max(int(datetime.now().timestamp() * 1000) - start, 0)
        return abs(duration)

    if duration == 0:
        start = _entry_start_ms(entry)
        end = _entry_end_ms(entry)
        if start is not None and end is not None and end >= start:
            return end - start

    return duration


def _entry_is_running(entry: Dict[str, Any]) -> bool:
    """Return True when the time entry appears to be running."""
    try:
        duration = int(entry.get("duration") or 0)
    except (TypeError, ValueError):
        duration = 0

    return duration < 0 or (_entry_start_ms(entry) is not None and _entry_end_ms(entry) is None)


def _format_description_cell(description: str, width: int = 32) -> str:
    """Trim descriptions to a stable table width."""
    if len(description) <= width:
        return description
    return description[: width - 3] + "..."


def _report_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten a raw ClickUp time entry into the shape the report builder consumes."""
    task = _entry_task(entry)
    status = task.get("status")
    location = entry.get("task_location") if isinstance(entry.get("task_location"), dict) else {}
    location_text = " / ".join(
        part
        for part in (location.get("folder_name"), location.get("list_name"))
        if part and part != "hidden"
    )
    task_id = _entry_task_id(entry)
    return {
        "id": str(entry.get("id") or ""),
        "task_id": task_id,
        "task_name": _entry_task_name(entry) if task_id else "(no task)",
        "task_url": entry.get("task_url") or "",
        "status": status.get("status") if isinstance(status, dict) else (status or ""),
        "location": location_text,
        "start_ms": _entry_start_ms(entry),
        "end_ms": _entry_end_ms(entry),
        "duration_ms": _entry_duration_ms(entry),
        "description": _entry_description(entry),
        "running": _entry_is_running(entry),
        "billable": bool(entry.get("billable")),
    }


def _report_file_name(report: Dict[str, Any], output_format: str) -> str:
    """Default file name, e.g. time_report_craig_2026-10-06_2026-10-12.html."""
    who = report["user"].get("username") or report["user"].get("id") or "user"
    slug = re.sub(r"[^A-Za-z0-9]+", "-", str(who)).strip("-").lower() or "user"
    extension = REPORT_FILE_EXTENSIONS[output_format]
    return f"time_report_{slug}_{report['range']['start']}_{report['range']['end']}.{extension}"


class TimeCommandBase(BaseCommand):
    """Shared wiring and helpers for time tracking commands."""

    def _team_id(self) -> str:
        team_arg = getattr(self.args, "team_id", None) or getattr(self.args, "team", None) or "current"
        return self.resolve_id("workspace", team_arg)

    def _time_api(self) -> TimeAPI:
        return TimeAPI(self.client)

    def _optional_task_id(self, task_value: Optional[str]) -> Optional[str]:
        if not task_value:
            return None
        return self.resolve_id("task", task_value)

    def _fetch_current_entry(self, team_id: str) -> Optional[Dict[str, Any]]:
        return _coerce_entry(self.client.get_current_time_entry(team_id))

    def _print_timer_status(self, entry: Dict[str, Any]) -> None:
        task_id = _entry_task_id(entry)
        task_name = _entry_task_name(entry)
        started = _entry_start_ms(entry)
        description = _entry_description(entry)
        elapsed = format_duration(_entry_duration_ms(entry))

        self.print("⏱️  Current Timer")
        self.print("")
        self.print(f"Task: {task_name} [{task_id or 'unknown'}]")
        if started is not None:
            self.print(f"Started: {format_timestamp(started, include_time=True)} ({elapsed} ago)")
        else:
            self.print(f"Elapsed: {elapsed}")
        if description:
            self.print(f"Description: {description}")
        self.print("")
        self.print("Use 'cum time stop' to stop the timer")


class TimeStartCommand(TimeCommandBase):
    """Start time tracking on a task."""

    def execute(self):
        team_id = self._team_id()
        task_id = self.resolve_id("task", self.args.task_id)
        task = self.client.get_task(task_id)

        entry = self.client.start_time_entry(
            team_id,
            tid=task_id,
            description=self.args.description,
        )

        started_entry = _coerce_entry(entry) or {"tid": task_id, "description": self.args.description}
        started = _entry_start_ms(started_entry) or int(datetime.now().timestamp() * 1000)

        self.print_success(f"Timer started on task: {task.get('name', 'Unknown task')}")
        self.print(f"Task ID: {task_id}")
        self.print(f"Started at: {format_timestamp(started, include_time=True)}")
        if self.args.description:
            self.print(f"Description: {self.args.description}")
        self.print("")
        self.print("Use 'cum time stop' to stop the timer")


class TimeStopCommand(TimeCommandBase):
    """Stop the currently running timer."""

    def execute(self):
        team_id = self._team_id()
        current_entry = self._fetch_current_entry(team_id)
        if not current_entry:
            self.error("No running timer found")

        expected_task_id = self._optional_task_id(getattr(self.args, "task_id", None))
        actual_task_id = _entry_task_id(current_entry)
        if expected_task_id and expected_task_id != actual_task_id:
            self.error(
                f"Current timer is running on task {actual_task_id or 'unknown'}, "
                f"not {expected_task_id}"
            )

        stop_result = self.client.stop_time_entry(team_id)
        stopped_entry = _coerce_entry(stop_result) or current_entry
        duration_str = format_duration(_entry_duration_ms(stopped_entry))
        started = _entry_start_ms(current_entry)
        stopped = _entry_end_ms(stopped_entry) or int(datetime.now().timestamp() * 1000)

        self.print_success("Timer stopped")
        self.print(f"Task: {_entry_task_name(current_entry)}")
        self.print(f"Duration: {duration_str}")
        if started is not None:
            self.print(f"Started: {format_timestamp(started, include_time=True)}")
        self.print(f"Stopped: {format_timestamp(stopped, include_time=True)}")


class TimeStatusCommand(TimeCommandBase):
    """Show the currently running timer."""

    def execute(self):
        team_id = self._team_id()
        current_entry = self._fetch_current_entry(team_id)
        if not current_entry:
            self.print("No timer is currently running.")
            return
        
        # Determine output
        task_id = _entry_task_id(current_entry)
        task_name = _entry_task_name(current_entry)
        started = _entry_start_ms(current_entry)
        description = _entry_description(current_entry)
        elapsed = format_duration(_entry_duration_ms(current_entry))

        lines = [
            "⏱️  Current Timer",
            "",
            f"Task: {task_name} [{task_id or 'unknown'}]"
        ]
        if started is not None:
            lines.append(f"Started: {format_timestamp(started, include_time=True)} ({elapsed} ago)")
        else:
            lines.append(f"Elapsed: {elapsed}")
        if description:
            lines.append(f"Description: {description}")
        lines.append("")
        lines.append("Use 'cum time stop' to stop the timer")
        
        output = "\n".join(lines)
        self.handle_output(
            data=current_entry,
            console_output=output
        )


class TimeListCommand(TimeCommandBase):
    """List time entries for a task or workspace filters."""

    def execute(self):
        team_id = self._team_id()
        task_id = self._optional_task_id(self.args.task_id)

        start_date = _parse_date_to_ms(self.args.start_date) if self.args.start_date else None
        end_date = _parse_date_to_ms(self.args.end_date, end_of_day=True) if self.args.end_date else None

        result = self._time_api().get_entries(
            team_id=team_id,
            task_id=task_id,
            assignee=self.args.assignee,
            start_date=start_date,
            end_date=end_date,
        )
        entries = _coerce_entries(result)

        if not entries:
            self.print("No time entries found.")
            return

        self.print("⏱️  Time Entries")
        self.print("")

        if task_id:
            try:
                task = self.client.get_task(task_id)
                self.print(f"Task: {task.get('name', 'Unknown task')} [{task_id}]")
            except Exception:
                self.print(f"Task: {task_id}")
            self.print("")

        show_task_column = not task_id
        headers = ["Date", "User", "Duration"]
        if show_task_column:
            headers.append("Task")
        headers.append("Description")

        rows = []
        total_ms = 0
        for entry in entries:
            start = _entry_start_ms(entry)
            date_str = format_timestamp(start, include_time=False) if start is not None else "Unknown"
            duration_ms = _entry_duration_ms(entry)
            total_ms += duration_ms
            row = [
                date_str,
                _entry_user_name(entry),
                format_duration(duration_ms),
            ]
            if show_task_column:
                row.append(_entry_task_name(entry))
            row.append(_format_description_cell(_entry_description(entry) or "-"))
            rows.append(row)

        divider = "-+-".join("-" * widths[index] for index in range(len(headers)))
        
        output_lines = [header_line, divider]
        for row in rows:
            output_lines.append(" | ".join(str(cell).ljust(widths[index]) for index, cell in enumerate(row)))
        output_lines.append("")
        output_lines.append(f"Total: {format_duration(total_ms)}")
        
        console_output = "\n".join(output_lines)
        
        self.handle_output(
            data=entries,
            console_output=console_output
        )


class TimeAddCommand(TimeCommandBase):
    """Create a manual time entry for past or current work."""

    def execute(self):
        team_id = self._team_id()
        task_id = self.resolve_id("task", self.args.task_id)
        duration_ms = parse_duration_to_ms(self.args.duration)

        if self.args.date:
            start_ms = _parse_date_to_ms(self.args.date)
        else:
            now_ms = int(datetime.now().timestamp() * 1000)
            start_ms = now_ms - duration_ms

        entry = self._time_api().create_entry(
            team_id=team_id,
            task_id=task_id,
            duration=duration_ms,
            description=self.args.description,
            start=start_ms,
        )
        created_entry = _coerce_entry(entry) or {"tid": task_id, "duration": duration_ms, "start": start_ms}

        self.print_success("Time entry created")
        self.print(f"Task ID: {task_id}")
        self.print(f"Duration: {format_duration(duration_ms)}")
        self.print(f"Start: {format_timestamp(_entry_start_ms(created_entry) or start_ms, include_time=True)}")
        if self.args.description:
            self.print(f"Description: {self.args.description}")


class TimeDeleteCommand(TimeCommandBase):
    """Delete a time entry."""

    def execute(self):
        team_id = self._team_id()
        entry = _coerce_entry(self.client.get_time_entry(team_id, self.args.timer_id))

        if not self.args.force:
            summary = self.args.timer_id
            if entry:
                summary = f"{self.args.timer_id} ({format_duration(_entry_duration_ms(entry))} on {_entry_task_name(entry)})"
            response = input(f"Delete time entry {summary}? [y/N]: ")
            if response.lower() not in {"y", "yes"}:
                self.print("Cancelled.")
                return

        self.client.delete_time_entry(team_id, self.args.timer_id)
        self.print_success(f"Deleted time entry {self.args.timer_id}")


class TimeReportCommand(TimeCommandBase):
    """
    Purpose:    Read-only timesheet: tracked time per day, per week, per task, plus the tasks
                a user touched each day. Defaults to the token owner; any member's ID can be
                passed instead (ClickUp only shows other people's time to Owners and Admins).
    Usage:      cum time report [user_id] [--weeks N | --start-date D --end-date D]
                                [--format html|json|markdown] [--output-file PATH]
                                [--timezone ZONE] [--no-touched] [--no-scheduled] [--team ID]
                Only GET endpoints are called. Nothing in ClickUp is created, edited or
                persisted locally apart from the report file itself.
    Version:    0.4.0
    Changes:    [v0.1.0] Initial: weekly/daily/task rollup, touched-task signals (tracked,
                commented, created; plus actor-unknown closes/updates on assigned tasks),
                HTML (default), JSON and Markdown output.
                [v0.2.0] Per-day "due or starting" list for assigned tasks whose due date
                or start date falls on the day; --no-scheduled to skip it.
                [v0.3.0] Assigned tasks are cached once, then the schedule and the
                in-progress/overdue list are derived from that cache. The list includes
                open tasks due after today whose start date is today or earlier, or blank,
                and open tasks overdue from before today. Each row shows the task's own
                time estimate and the total including subtasks in the cache.
                [v0.4.0] Tasks with tracked time are included even when the user is not
                the assignee, and the week matrix shows Est and Total est.
    """

    def execute(self):
        team_id = self._team_id()
        me = self._authorized_user()
        target = self._target_user(team_id, me)
        target_id = str(target.get("id") or "")
        is_self = target_id == str(me.get("id"))

        tz_name = getattr(self.args, "timezone", None) or me.get("timezone")
        tz = resolve_report_timezone(tz_name)
        tz_text = timezone_label(tz, tz_name)
        today = datetime.now(tz).date() if tz else date.today()

        try:
            start, end = resolve_report_range(
                today,
                weeks=getattr(self.args, "weeks", 1),
                start=_parse_report_date(getattr(self.args, "start_date", None)),
                end=_parse_report_date(getattr(self.args, "end_date", None)),
                week_start=REPORT_WEEK_START,
            )
        except ValueError as exc:
            self.error(str(exc))
        start_ms, end_ms = range_bounds_ms(start, end, tz)

        who = target.get("username") or target_id
        self.print_info(f"Reading time entries for {who} ({start} to {end}, {tz_text})...")
        entries = self._fetch_entries(team_id, target_id, is_self, start_ms, end_ms)

        notes = [
            f"Days are bucketed in {tz_text}. A time entry counts in full toward the day it "
            "started, even if it runs past midnight.",
        ]
        if not is_self and not getattr(self.args, "timezone", None):
            notes.append(
                f"ClickUp does not expose other members' time zones, so this report uses "
                f"{tz_text} (the token owner's). Pass --timezone to override."
            )

        want_touched = not getattr(self.args, "no_touched", False)
        want_scheduled = not getattr(self.args, "no_scheduled", False)

        # One cached read of the assigned tasks. Touched signals only need the ones
        # updated in range; the schedule and the in-progress/overdue list need the
        # whole open set, because a due-date filter drops anything due outside the week.
        cache: List[Dict[str, Any]] = []
        if want_touched or want_scheduled:
            cache = self._load_assigned_cache(
                team_id, target_id, start_ms, end_ms, notes, include_open=want_scheduled
            )

        tracked_ms: Dict[str, int] = {}
        for entry in entries:
            tracked_id = entry.get("task_id") or ""
            if tracked_id:
                tracked_ms[tracked_id] = tracked_ms.get(tracked_id, 0) + int(
                    entry.get("duration_ms") or 0
                )
        if tracked_ms:
            cache = self._merge_tracked_tasks(cache, set(tracked_ms), notes)
        estimate_fields = estimates_for(cache, tracked_ms) if tracked_ms else {}

        activities: List[Dict[str, Any]] = []
        if want_touched:
            recent_assigned = [task for task in cache if task_updated_after(task, start_ms)]
            activities = self._collect_activities(
                target_id, entries, recent_assigned, start_ms, end_ms, notes
            )
        else:
            notes.append("Touched-task scan skipped (--no-touched); only tracked tasks are listed.")

        schedule: List[Dict[str, Any]] = []
        open_work: List[Dict[str, Any]] = []
        if want_scheduled:
            today_start_ms = local_midnight_ms(today, tz)
            today_end_ms = local_midnight_ms(today + timedelta(days=1), tz) - 1
            list_order = self._location_order(team_id, cache, notes)
            schedule, open_work = self._collect_schedule(
                cache,
                start_ms,
                end_ms,
                today_start_ms,
                today_end_ms,
                notes,
                list_order,
                tracked_ms,
            )

        report = build_time_report(
            user={**target, "id": target_id},
            workspace_id=team_id,
            entries=entries,
            activities=activities,
            start=start,
            end=end,
            tz=tz,
            tz_label=tz_text,
            week_start=REPORT_WEEK_START,
            notes=notes,
            schedule=schedule,
            open_work=open_work,
            estimates=estimate_fields,
        )
        self._emit(report)

    # ---------- user resolution ----------

    def _authorized_user(self) -> Dict[str, Any]:
        result = self.client.get_authorized_user()
        if isinstance(result, dict) and isinstance(result.get("user"), dict):
            return result["user"]
        return result if isinstance(result, dict) else {}

    def _target_user(self, team_id: str, me: Dict[str, Any]) -> Dict[str, Any]:
        """Return the token owner, or the workspace member matching the requested ID."""
        requested = getattr(self.args, "user_id_flag", None) or getattr(self.args, "user_id", None)
        if not requested or str(requested) == str(me.get("id")):
            return me
        requested = str(requested).strip()
        if not requested.isdigit():
            self.error(f"User ID must be numeric, got '{requested}'.")

        # The member list rides along on the workspace payload; the dedicated get-user
        # endpoint is Enterprise-only, so this is the polite way to learn a name.
        try:
            workspaces = self.client.get_authorized_workspaces()
        except Exception:
            workspaces = {}
        for team in (workspaces or {}).get("teams", []):
            if str(team.get("id")) != str(team_id):
                continue
            for member in team.get("members", []):
                user = member.get("user") if isinstance(member, dict) else None
                if isinstance(user, dict) and str(user.get("id")) == requested:
                    return user
        self.print_warning(f"User {requested} is not a member of workspace {team_id} (or hidden).")
        return {"id": requested}

    # ---------- data fetching (GET only) ----------

    def _fetch_entries(
        self, team_id: str, target_id: str, is_self: bool, start_ms: int, end_ms: int
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {
            # ClickUp treats start_date as exclusive, so an entry that begins on the
            # first millisecond of the range (local midnight) never comes back.
            "start_date": start_ms - 1,
            "end_date": end_ms + 1,
            "include_location_names": "true",
        }
        if not is_self:
            params["assignee"] = target_id
        try:
            result = self.client.get_time_entries(team_id, **params)
        except Exception as exc:
            if is_self:
                raise
            self.error(
                f"Could not read time entries for user {target_id}: {exc}\n"
                "Viewing another member's time needs a Workspace Owner or Admin token."
            )

        raw_entries = _coerce_entries(result)
        owned = [e for e in raw_entries if _entry_user_id(e) in ("", target_id)]
        if raw_entries and not owned:
            # ClickUp can quietly ignore the assignee filter for non-admins and hand back the
            # caller's own entries. Better an honest error than someone else's timesheet.
            self.error(
                f"ClickUp returned time entries for a different user than {target_id}. "
                "Viewing another member's time needs a Workspace Owner or Admin token."
            )
        reported = []
        for entry in owned:
            started = _entry_start_ms(entry)
            if started is None or started < start_ms or started > end_ms:
                continue
            reported.append(_report_entry(entry))
        return reported

    def _fetch_task_pages(
        self, team_id: str, notes: List[str], label: str, **filters: Any
    ) -> List[Dict[str, Any]]:
        """
        Page through GET /team/{id}/task with ``filters`` (subtasks always included).
        A failure becomes a report note rather than a crash: the timesheet half of the
        report is still worth having when the task half can't be read.
        """
        tasks: List[Dict[str, Any]] = []
        try:
            for page in range(REPORT_MAX_TASK_PAGES):
                result = self.client.get_team_tasks(team_id, subtasks=True, page=page, **filters)
                batch = result.get("tasks", []) if isinstance(result, dict) else []
                tasks.extend(task for task in batch if isinstance(task, dict))
                if not batch or result.get("last_page", True):
                    return tasks
        except Exception as exc:
            notes.append(f"Could not read {label} ({exc}); related lists may be incomplete.")
            return tasks
        notes.append(
            f"Stopped reading {label} after {REPORT_MAX_TASK_PAGES} pages; "
            "related lists may be incomplete."
        )
        return tasks

    def _collect_activities(
        self,
        target_id: str,
        entries: List[Dict[str, Any]],
        assigned: List[Dict[str, Any]],
        start_ms: int,
        end_ms: int,
        notes: List[str],
    ) -> List[Dict[str, Any]]:
        """Build touched-task signals from assigned tasks and the user's comments."""
        activities = derive_task_activities(assigned, target_id, start_ms, end_ms)

        candidates: Dict[str, Dict[str, Any]] = {}
        for task in assigned:
            info = task_info_from_task(task)
            candidates[info["task_id"]] = info
        for entry in entries:
            if entry["task_id"] and entry["task_id"] not in candidates:
                candidates[entry["task_id"]] = {
                    "task_id": entry["task_id"],
                    "name": entry["task_name"],
                    "url": entry["task_url"],
                    "status": entry["status"],
                    "location": entry["location"],
                }

        if candidates:
            self.print_info(f"Scanning comments on {len(candidates)} task(s)...")
        truncated: List[str] = []
        failed = 0
        for task_id, info in candidates.items():
            try:
                result = self.client.get_task_comments(task_id)
            except Exception:
                failed += 1
                continue
            comments = result.get("comments", []) if isinstance(result, dict) else []
            activities.extend(
                derive_comment_activities(info, comments, target_id, start_ms, end_ms)
            )
            dates = [int(c["date"]) for c in comments if str(c.get("date") or "").isdigit()]
            if len(comments) >= REPORT_COMMENT_PAGE_SIZE and dates and min(dates) >= start_ms:
                truncated.append(info["name"])

        notes.append(
            "Touched tasks: tracked time, comments and tasks created are the user's own "
            "activity. 'Closed' and 'Last updated' are timestamps on tasks assigned to the user; "
            "ClickUp's public API does not say who made those changes, and 'Last updated' only "
            "reflects the most recent change. Only tasks with tracked time or assigned to the "
            "user are scanned, and threaded replies are not included."
        )
        if truncated:
            notes.append(
                f"Only the {REPORT_COMMENT_PAGE_SIZE} most recent comments are read per task; "
                f"{len(truncated)} busy task(s) may have older in-range comments not counted: "
                + ", ".join(truncated[:10])
                + ("..." if len(truncated) > 10 else "")
            )
        if failed:
            notes.append(f"Comments could not be read for {failed} task(s).")
        return activities

    def _load_assigned_cache(
        self,
        team_id: str,
        target_id: str,
        start_ms: int,
        end_ms: int,
        notes: List[str],
        include_open: bool,
    ) -> List[Dict[str, Any]]:
        """
        Read the assigned tasks once and return them deduped by id.

        Closed tasks updated in the range cover touched signals and start dates on work
        that has since been closed. When the schedule is wanted, open tasks are read with
        no date filter and merged in last, so a task due next month or overdue from last
        month is in the cache even though a due-date window would have dropped it.
        """
        updated = self._fetch_task_pages(
            team_id,
            notes,
            "assigned tasks updated in range",
            assignees=[target_id],
            date_updated_gt=start_ms,
            include_closed=True,
        )
        if not include_open:
            return updated

        due = self._fetch_task_pages(
            team_id,
            notes,
            "assigned tasks due in range",
            assignees=[target_id],
            due_date_gt=start_ms - 1,
            due_date_lt=end_ms + 1,
            include_closed=True,
        )
        open_assigned = self._fetch_task_pages(
            team_id,
            notes,
            "open assigned tasks",
            assignees=[target_id],
            include_closed=False,
        )
        merged: Dict[str, Dict[str, Any]] = {}
        for task in (*due, *updated, *open_assigned):
            if isinstance(task, dict) and task.get("id"):
                merged[str(task["id"])] = task
        return list(merged.values())

    def _collect_schedule(
        self,
        cache: List[Dict[str, Any]],
        start_ms: int,
        end_ms: int,
        today_start_ms: int,
        today_end_ms: int,
        notes: List[str],
        list_order: Dict[str, Tuple[int, int, int]],
        tracked_ms: Dict[str, int],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Build the per-day schedule and the assigned-task list from ``cache``."""
        notes.append(
            "Due or starting: tasks assigned to the user whose due date or start date falls "
            "on the day. Overdue on that list means the task was still open after its due day. "
            "Start dates come from open assigned tasks and tasks updated during the range, so a "
            "task closed before the range began is not listed by its start date."
        )
        notes.append(
            "Assigned and tracked tasks are grouped by folder and list in sidebar order. "
            "A task you booked time to is included even when you are not the assignee, so "
            "its time estimate is not left at zero. In progress: due after today, start date "
            "today or earlier or blank. Overdue: due before today. Time estimate is the "
            "task's own estimate. Total time estimate adds subtasks in the cache."
        )
        return (
            derive_schedule_items(cache, start_ms, end_ms),
            derive_open_work(
                cache, today_start_ms, today_end_ms, list_order, tracked_ms=tracked_ms
            ),
        )

    def _merge_tracked_tasks(
        self,
        cache: List[Dict[str, Any]],
        tracked_ids: set,
        notes: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Add tasks that have tracked time but were not in the assignee cache.

        Subtasks of those tasks are kept for the rolled-up total and marked so they
        are not listed on their own unless time was booked to them directly.
        """
        known = {str(task.get("id")) for task in cache if isinstance(task, dict) and task.get("id")}
        missing = [task_id for task_id in tracked_ids if task_id not in known]
        if not missing:
            return cache
        fetched: List[Dict[str, Any]] = []
        failed = 0
        for task_id in missing:
            try:
                task = self.client.get_task(task_id, include_subtasks=True)
            except Exception:
                failed += 1
                continue
            if not isinstance(task, dict) or not task.get("id"):
                failed += 1
                continue
            fetched.append(task)
            known.add(str(task["id"]))
            for sub in task.get("subtasks") or []:
                if not isinstance(sub, dict) or not sub.get("id"):
                    continue
                sub_id = str(sub["id"])
                if sub_id in known:
                    continue
                parent = sub.get("parent") or task["id"]
                rollup_only = sub_id not in tracked_ids
                fetched.append({**sub, "parent": parent, "_rollup_only": rollup_only})
                known.add(sub_id)
        if failed:
            notes.append(
                f"Could not read {failed} task(s) with tracked time; their estimates may be missing."
            )
        elif fetched:
            notes.append(
                "Tasks with tracked time are listed even when you are not the assignee."
            )
        return [*cache, *fetched]

    def _location_order(
        self, team_id: str, tasks: List[Dict[str, Any]], notes: List[str]
    ) -> Dict[str, Tuple[int, int, int]]:
        """
        Map each list id to (space index, folder order, list order).

        Space index follows the order ClickUp returns spaces. Folder and list order
        are the orderindex values from the sidebar. Only spaces that contain one of
        ``tasks`` are read.
        """
        needed = set()
        for task in tasks:
            space = task.get("space") if isinstance(task.get("space"), dict) else {}
            if space.get("id"):
                needed.add(str(space["id"]))
        if not needed:
            return {}
        try:
            result = self.client.get_team_spaces(team_id)
        except Exception as exc:
            notes.append(f"Could not read spaces ({exc}); assigned tasks are grouped by name.")
            return {}
        spaces = result.get("spaces") if isinstance(result, dict) else None
        if not isinstance(spaces, list):
            return {}

        order: Dict[str, Tuple[int, int, int]] = {}
        for space_index, space in enumerate(spaces):
            if not isinstance(space, dict):
                continue
            space_id = str(space.get("id") or "")
            if space_id not in needed:
                continue
            space_name = space.get("name") or space_id
            try:
                folder_result = self.client.get_space_folders(space_id)
                folders = folder_result.get("folders") if isinstance(folder_result, dict) else []
            except Exception as exc:
                notes.append(f"Could not read folders in {space_name} ({exc}).")
                folders = []
            for folder in folders or []:
                if not isinstance(folder, dict):
                    continue
                folder_index = _sidebar_index(folder.get("orderindex"))
                for task_list in folder.get("lists") or []:
                    if isinstance(task_list, dict) and task_list.get("id"):
                        order[str(task_list["id"])] = (
                            space_index,
                            folder_index,
                            _sidebar_index(task_list.get("orderindex")),
                        )
            try:
                loose_result = self.client.get_space_lists(space_id)
                loose = loose_result.get("lists") if isinstance(loose_result, dict) else []
            except Exception as exc:
                notes.append(f"Could not read lists in {space_name} ({exc}).")
                loose = []
            for task_list in loose or []:
                if isinstance(task_list, dict) and task_list.get("id"):
                    order[str(task_list["id"])] = (
                        space_index,
                        _sidebar_index(task_list.get("orderindex")),
                        0,
                    )
        return order

    # ---------- output ----------

    def _emit(self, report: Dict[str, Any]) -> None:
        output_format = getattr(self.args, "format", None) or "html"
        renderers = {"html": render_html, "json": render_json, "markdown": render_markdown}
        text = renderers[output_format](report)

        path = getattr(self.args, "report_output_file", None)
        if output_format == "html" and not path:
            path = _report_file_name(report, output_format)

        summary = report["summary"]
        self.print_info(
            f"Tracked {summary['total']} across {summary['days_tracked']} day(s) on "
            f"{summary['task_count']} task(s); {summary['touched_task_count']} task(s) touched."
        )
        if path:
            self._write_text_output_file(path, text)
        else:
            sys.stdout.write(text)


def time_start_command(args):
    TimeStartCommand(args, command_name="time").execute()


def time_stop_command(args):
    TimeStopCommand(args, command_name="time").execute()


def time_status_command(args):
    TimeStatusCommand(args, command_name="time").execute()


def time_list_command(args):
    TimeListCommand(args, command_name="time").execute()


def time_add_command(args):
    TimeAddCommand(args, command_name="time").execute()


def time_delete_command(args):
    TimeDeleteCommand(args, command_name="time").execute()


def time_report_command(args):
    TimeReportCommand(args, command_name="time").execute()


def register_command(subparsers):
    """Register time tracking commands."""
    parser = subparsers.add_parser(
        "time",
        help="Manage ClickUp time tracking entries and running timers",
        formatter_class=raw_text_formatter(),
        description=(
            "Start, stop, inspect, list, add, and delete ClickUp time entries, or build a "
            "read-only timesheet report. Defaults to the current workspace for team "
            "resolution and supports the 'current' task context keyword where a task ID "
            "is expected."
        ),
        epilog=(
            "Examples:\n"
            "  cum time start current --description \"Working on implementation\"\n"
            "  cum time stop\n"
            "  cum time status\n"
            "  cum time list current --start-date 2026-04-01 --end-date 2026-04-05\n"
            "  cum time add current 2h30m --description \"Yesterday's work\" --date 2026-04-04\n"
            "  cum time delete <timer_id> --force\n"
            "  cum time report\n"
            "  cum time report 12345678 --weeks 4 --format markdown -o team_member.md\n"
        ),
    )
    time_subparsers = parser.add_subparsers(dest="time_command", help="Time tracking command")

    start_parser = time_subparsers.add_parser("start", help="Start time tracking on a task")
    start_parser.add_argument("task_id", help='Task ID or "current"')
    start_parser.add_argument("--team", dest="team_id", help='Workspace/team ID (defaults to "current")')
    start_parser.add_argument("--description", help="Optional timer description")
    add_common_args(start_parser)
    start_parser.set_defaults(func=time_start_command)

    stop_parser = time_subparsers.add_parser("stop", help="Stop the currently running timer")
    stop_parser.add_argument("--team", dest="team_id", help='Workspace/team ID (defaults to "current")')
    stop_parser.add_argument("--task", dest="task_id", help="Require the running timer to belong to this task")
    add_common_args(stop_parser)
    stop_parser.set_defaults(func=time_stop_command)

    status_parser = time_subparsers.add_parser("status", help="Show the currently running timer")
    status_parser.add_argument("--team", dest="team_id", help='Workspace/team ID (defaults to "current")')
    add_common_args(status_parser)
    status_parser.set_defaults(func=time_status_command)

    list_parser = time_subparsers.add_parser("list", help="List time entries")
    list_parser.add_argument("task_id", nargs="?", help='Optional task ID or "current"')
    list_parser.add_argument("--team", dest="team_id", help='Workspace/team ID (defaults to "current")')
    list_parser.add_argument("--assignee", type=int, help="Filter by user ID")
    list_parser.add_argument("--start-date", help="Start date filter in YYYY-MM-DD format")
    list_parser.add_argument("--end-date", help="End date filter in YYYY-MM-DD format")
    add_common_args(list_parser)
    list_parser.set_defaults(func=time_list_command)

    add_parser = time_subparsers.add_parser("add", help="Add a manual time entry")
    add_parser.add_argument("task_id", help='Task ID or "current"')
    add_parser.add_argument("duration", help='Duration such as "2h30m", "90m", or "1.5h"')
    add_parser.add_argument("--team", dest="team_id", help='Workspace/team ID (defaults to "current")')
    add_parser.add_argument("--description", help="Description for the manual time entry")
    add_parser.add_argument("--date", help="Work date in YYYY-MM-DD format (defaults to now-duration)")
    add_common_args(add_parser)
    add_parser.set_defaults(func=time_add_command)

    delete_parser = time_subparsers.add_parser("delete", help="Delete a time entry")
    delete_parser.add_argument("timer_id", help="Time entry/timer ID")
    delete_parser.add_argument("--team", dest="team_id", help='Workspace/team ID (defaults to "current")')
    delete_parser.add_argument("--force", "-f", action="store_true", help="Skip confirmation prompt")
    add_common_args(delete_parser)
    delete_parser.set_defaults(func=time_delete_command)

    # No add_common_args here on purpose: its -O/--output defaults to console, and this
    # report defaults to an HTML file. Read-only: every API call it makes is a GET.
    report_parser = time_subparsers.add_parser(
        "report",
        help="Read-only timesheet: time per day/week/task and tasks touched each day",
        formatter_class=raw_text_formatter(),
        description=(
            "Build a read-only timesheet for a user: tracked time for each day of each "
            "week, the tasks it was tracked against, and the tasks the user touched each "
            "day (tracked time, comments, tasks created, plus closes/updates on tasks "
            "assigned to them), and assigned tasks due or starting each day. Also lists "
            "every open task assigned to the user, plus tasks they booked time to even "
            "when they are not the assignee, grouped by folder and list, with each "
            "task's time estimate and the total including "
            "subtasks. Defaults to the token owner and the current week. Nothing in "
            "ClickUp is created or changed."
        ),
        epilog=(
            "Examples:\n"
            "  cum time report                              # you, this week, HTML file\n"
            "  cum time report --weeks 4                    # last 4 weeks\n"
            "  cum time report 12345678                     # another member (admin token)\n"
            "  cum time report --start-date 2026-09-01 --end-date 2026-09-30 -f json\n"
            "  cum time report -f markdown -o timesheet.md\n"
        ),
    )
    report_parser.add_argument(
        "user_id", nargs="?", help="ClickUp user ID to report on (defaults to you, the token owner)"
    )
    report_parser.add_argument(
        "--user-id", dest="user_id_flag", metavar="USER_ID", help="Same as the positional user_id"
    )
    report_parser.add_argument(
        "--team", dest="team_id", help='Workspace/team ID (defaults to "current")'
    )
    report_parser.add_argument(
        "--weeks",
        type=int,
        default=1,
        help="Whole weeks to cover, ending with the current week (default: 1)",
    )
    report_parser.add_argument("--start-date", help="Range start in YYYY-MM-DD (overrides --weeks)")
    report_parser.add_argument("--end-date", help="Range end in YYYY-MM-DD")
    report_parser.add_argument(
        "-f",
        "--format",
        choices=REPORT_FORMATS,
        default="html",
        help="Report format (default: html, written to a file)",
    )
    report_parser.add_argument(
        "-o",
        "--output-file",
        "--to-file",
        dest="report_output_file",
        metavar="PATH",
        help=(
            "Write the report to PATH. HTML defaults to "
            "time_report_<user>_<start>_<end>.html; JSON and Markdown default to stdout"
        ),
    )
    report_parser.add_argument(
        "--timezone",
        help="IANA time zone for day boundaries (default: your ClickUp profile time zone)",
    )
    report_parser.add_argument(
        "--no-touched",
        action="store_true",
        help="Skip the comment and assigned-task activity scan (tracked tasks still listed)",
    )
    report_parser.add_argument(
        "--no-scheduled",
        action="store_true",
        help="Skip the per-day list of assigned tasks due or starting that day",
    )
    report_parser.set_defaults(func=time_report_command)
