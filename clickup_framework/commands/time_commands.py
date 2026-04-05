"""Time tracking commands for ClickUp Framework CLI."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional

from clickup_framework.commands.base_command import BaseCommand
from clickup_framework.resources import TimeAPI
from clickup_framework.utils import format_duration, format_timestamp, parse_duration_to_ms
from clickup_framework.utils.argparse_helpers import raw_text_formatter


COMMAND_METADATA = {
    "category": "⏱️  Time Tracking",
    "commands": [
        {
            "name": "time",
            "args": "start|stop|status|list|add|delete [options]",
            "description": "Start, stop, inspect, list, add, and delete ClickUp time entries",
        }
    ],
}


def _parse_date_to_ms(value: str, *, end_of_day: bool = False) -> int:
    """Parse a YYYY-MM-DD date string into a local Unix timestamp in ms."""
    try:
        date_value = datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"Invalid date '{value}'. Use YYYY-MM-DD.") from exc

    if end_of_day:
        date_value = date_value + timedelta(days=1) - timedelta(milliseconds=1)

    return int(date_value.timestamp() * 1000)


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
        self._print_timer_status(current_entry)


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

        widths = [max(len(header), *(len(str(row[index])) for row in rows)) for index, header in enumerate(headers)]
        header_line = " | ".join(header.ljust(widths[index]) for index, header in enumerate(headers))
        divider = "-+-".join("-" * widths[index] for index in range(len(headers)))
        self.print(header_line)
        self.print(divider)
        for row in rows:
            self.print(" | ".join(str(cell).ljust(widths[index]) for index, cell in enumerate(row)))

        self.print("")
        self.print(f"Total: {format_duration(total_ms)}")


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


def register_command(subparsers):
    """Register time tracking commands."""
    parser = subparsers.add_parser(
        "time",
        help="Manage ClickUp time tracking entries and running timers",
        formatter_class=raw_text_formatter(),
        description=(
            "Start, stop, inspect, list, add, and delete ClickUp time entries. "
            "Defaults to the current workspace for team resolution and supports "
            "the 'current' task context keyword where a task ID is expected."
        ),
        epilog=(
            "Examples:\n"
            "  cum time start current --description \"Working on implementation\"\n"
            "  cum time stop\n"
            "  cum time status\n"
            "  cum time list current --start-date 2026-04-01 --end-date 2026-04-05\n"
            "  cum time add current 2h30m --description \"Yesterday's work\" --date 2026-04-04\n"
            "  cum time delete <timer_id> --force\n"
        ),
    )
    time_subparsers = parser.add_subparsers(dest="time_command", help="Time tracking command")

    start_parser = time_subparsers.add_parser("start", help="Start time tracking on a task")
    start_parser.add_argument("task_id", help='Task ID or "current"')
    start_parser.add_argument("--team", dest="team_id", help='Workspace/team ID (defaults to "current")')
    start_parser.add_argument("--description", help="Optional timer description")
    start_parser.set_defaults(func=time_start_command)

    stop_parser = time_subparsers.add_parser("stop", help="Stop the currently running timer")
    stop_parser.add_argument("--team", dest="team_id", help='Workspace/team ID (defaults to "current")')
    stop_parser.add_argument("--task", dest="task_id", help="Require the running timer to belong to this task")
    stop_parser.set_defaults(func=time_stop_command)

    status_parser = time_subparsers.add_parser("status", help="Show the currently running timer")
    status_parser.add_argument("--team", dest="team_id", help='Workspace/team ID (defaults to "current")')
    status_parser.set_defaults(func=time_status_command)

    list_parser = time_subparsers.add_parser("list", help="List time entries")
    list_parser.add_argument("task_id", nargs="?", help='Optional task ID or "current"')
    list_parser.add_argument("--team", dest="team_id", help='Workspace/team ID (defaults to "current")')
    list_parser.add_argument("--assignee", type=int, help="Filter by user ID")
    list_parser.add_argument("--start-date", help="Start date filter in YYYY-MM-DD format")
    list_parser.add_argument("--end-date", help="End date filter in YYYY-MM-DD format")
    list_parser.set_defaults(func=time_list_command)

    add_parser = time_subparsers.add_parser("add", help="Add a manual time entry")
    add_parser.add_argument("task_id", help='Task ID or "current"')
    add_parser.add_argument("duration", help='Duration such as "2h30m", "90m", or "1.5h"')
    add_parser.add_argument("--team", dest="team_id", help='Workspace/team ID (defaults to "current")')
    add_parser.add_argument("--description", help="Description for the manual time entry")
    add_parser.add_argument("--date", help="Work date in YYYY-MM-DD format (defaults to now-duration)")
    add_parser.set_defaults(func=time_add_command)

    delete_parser = time_subparsers.add_parser("delete", help="Delete a time entry")
    delete_parser.add_argument("timer_id", help="Time entry/timer ID")
    delete_parser.add_argument("--team", dest="team_id", help='Workspace/team ID (defaults to "current")')
    delete_parser.add_argument("--force", "-f", action="store_true", help="Skip confirmation prompt")
    delete_parser.set_defaults(func=time_delete_command)
