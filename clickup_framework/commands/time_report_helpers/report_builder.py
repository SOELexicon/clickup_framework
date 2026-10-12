"""
Pure aggregation for the ``cum time report`` timesheet.

Nothing in here talks to ClickUp. The command layer fetches raw API payloads, flattens
them into small dicts, and hands them over; this module turns those into a week -> day ->
task rollup that the HTML, Markdown and JSON renderers all share. Keeping it pure means
the arithmetic (the part people actually argue about at invoice time) is unit-testable
without a token.

Variables:  REPORT_SCHEMA_VERSION, WEEKDAY_NAMES, MS_PER_HOUR, MS_PER_MINUTE, DAYS_PER_WEEK,
            SIGNAL_TRACKED, SIGNAL_COMMENTED, SIGNAL_CREATED, SIGNAL_CLOSED, SIGNAL_UPDATED,
            ATTRIBUTED_SIGNALS, SIGNAL_ORDER, NO_TASK_ID, NO_TASK_NAME, SCHEDULE_DUE,
            SCHEDULE_START, CLOSED_STATUS_TYPES
Functions:  resolve_report_timezone, timezone_label, local_date, local_datetime,
            local_midnight_ms, week_start_for, resolve_report_range, range_bounds_ms,
            format_hours, hours_value, task_info_from_task, derive_task_activities,
            derive_schedule_items, derive_comment_activities, build_time_report
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, tzinfo
from typing import Any, Dict, Iterable, List, Optional, Tuple

REPORT_SCHEMA_VERSION = 1
WEEKDAY_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
MS_PER_MINUTE = 60_000
MS_PER_HOUR = 3_600_000
DAYS_PER_WEEK = 7

# Signal kinds. The first three are things the user demonstrably did; the last two are
# task timestamps on tasks assigned to them, where ClickUp's public API won't say who
# pulled the trigger. The report keeps that distinction visible rather than flattering
# anyone with edits a colleague made.
SIGNAL_TRACKED = "tracked"
SIGNAL_COMMENTED = "commented"
SIGNAL_CREATED = "created"
SIGNAL_CLOSED = "closed"
SIGNAL_UPDATED = "updated"
ATTRIBUTED_SIGNALS = frozenset({SIGNAL_TRACKED, SIGNAL_COMMENTED, SIGNAL_CREATED})
SIGNAL_ORDER = (SIGNAL_TRACKED, SIGNAL_COMMENTED, SIGNAL_CREATED, SIGNAL_CLOSED, SIGNAL_UPDATED)

NO_TASK_ID = ""
NO_TASK_NAME = "(no task)"

# Schedule kinds: a task's due date or start date landing on a day. Not activity, just
# the calendar, so they live in their own list rather than padding out "touched".
SCHEDULE_DUE = "due"
SCHEDULE_START = "start"
CLOSED_STATUS_TYPES = frozenset({"closed", "done"})


# ==================== Time zone and calendar helpers ====================


def resolve_report_timezone(name: Optional[str]) -> Optional[tzinfo]:
    """
    Purpose:    Turn an IANA zone name into a tzinfo, or None for "system local time".
    Usage:      tz = resolve_report_timezone("Europe/London")
                None means callers fall back to the OS zone via naive datetimes, which is
                also what happens on a Windows box without the tzdata package installed.
    Version:    0.1.0
    Changes:    [v0.1.0] Initial.
    """
    if not name:
        return None
    try:
        from zoneinfo import ZoneInfo

        return ZoneInfo(name)
    except Exception:
        return None


def timezone_label(tz: Optional[tzinfo], requested: Optional[str] = None) -> str:
    """Return a human label for the zone the report was bucketed in."""
    if tz is not None:
        return str(getattr(tz, "key", None) or tz)
    if requested:
        return f"system local time ({requested} unavailable)"
    return "system local time"


def local_date(ms: int, tz: Optional[tzinfo]) -> date:
    """Return the calendar date a millisecond timestamp falls on in ``tz``."""
    seconds = ms / 1000
    if tz is None:
        return datetime.fromtimestamp(seconds).date()
    return datetime.fromtimestamp(seconds, tz).date()


def local_datetime(ms: int, tz: Optional[tzinfo]) -> datetime:
    """Return an aware (or OS-local naive) datetime for a millisecond timestamp."""
    seconds = ms / 1000
    if tz is None:
        return datetime.fromtimestamp(seconds)
    return datetime.fromtimestamp(seconds, tz)


def local_midnight_ms(day: date, tz: Optional[tzinfo]) -> int:
    """
    Purpose:    Millisecond timestamp of 00:00 on ``day`` in ``tz``.
    Usage:      Built from the calendar date rather than by adding 86_400_000 per day,
                so the 23 and 25 hour days either side of a DST change land correctly.
    Version:    0.1.0
    Changes:    [v0.1.0] Initial.
    """
    if tz is None:
        return int(datetime(day.year, day.month, day.day).timestamp() * 1000)
    return int(datetime(day.year, day.month, day.day, tzinfo=tz).timestamp() * 1000)


def week_start_for(day: date, week_start: int = 0) -> date:
    """Return the first day of the week containing ``day`` (0 = Monday, 6 = Sunday)."""
    return day - timedelta(days=(day.weekday() - week_start) % DAYS_PER_WEEK)


def resolve_report_range(
    today: date,
    weeks: int = 1,
    start: Optional[date] = None,
    end: Optional[date] = None,
    week_start: int = 0,
) -> Tuple[date, date]:
    """
    Purpose:    Work out the inclusive date range the report covers.
    Usage:      No dates: the last ``weeks`` whole weeks ending with the current week.
                Start only: start through the end of the current week.
                End only: ``weeks`` whole weeks ending with the week containing ``end``.
                Both: exactly what was asked for.
    Version:    0.1.0
    Changes:    [v0.1.0] Initial.
    """
    weeks = max(int(weeks or 1), 1)
    if start and end:
        resolved = (start, end)
    elif start:
        resolved = (start, week_start_for(today, week_start) + timedelta(days=DAYS_PER_WEEK - 1))
    else:
        anchor = week_start_for(end or today, week_start)
        first = anchor - timedelta(days=DAYS_PER_WEEK * (weeks - 1))
        last = end or anchor + timedelta(days=DAYS_PER_WEEK - 1)
        resolved = (first, last)

    if resolved[0] > resolved[1]:
        raise ValueError(
            f"Start date {resolved[0].isoformat()} is after end date {resolved[1].isoformat()}."
        )
    return resolved


def range_bounds_ms(start: date, end: date, tz: Optional[tzinfo]) -> Tuple[int, int]:
    """Return [start-of-first-day, end-of-last-day] in ms for API filters."""
    return local_midnight_ms(start, tz), local_midnight_ms(end + timedelta(days=1), tz) - 1


# ==================== Formatting helpers ====================


def format_hours(ms: int) -> str:
    """
    Purpose:    Timesheet-style duration, always in hours and minutes.
    Usage:      format_hours(137_700_000) -> "38h 15m". The shared format_duration helper
                rolls 24h into "1d", which is lovely for timers and baffling on a timesheet.
    Version:    0.1.0
    Changes:    [v0.1.0] Initial.
    """
    if not ms or ms <= 0:
        return "0m"
    minutes = round(ms / MS_PER_MINUTE)
    if minutes == 0:
        return "<1m"
    hours, mins = divmod(minutes, 60)
    if hours and mins:
        return f"{hours}h {mins}m"
    if hours:
        return f"{hours}h"
    return f"{mins}m"


def hours_value(ms: int) -> float:
    """Return a duration as decimal hours rounded to 2 places, for spreadsheets."""
    return round((ms or 0) / MS_PER_HOUR, 2)


def _to_ms(value: Any) -> Optional[int]:
    """Parse ClickUp's string-or-int millisecond timestamps."""
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _in_window(ms: Optional[int], start_ms: int, end_ms: int) -> bool:
    return ms is not None and start_ms <= ms <= end_ms


# ==================== Activity derivation ====================


def task_info_from_task(task: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten a ClickUp task payload into the small dict the report carries around."""
    status = task.get("status")
    status_name = status.get("status") if isinstance(status, dict) else status
    folder = task.get("folder") if isinstance(task.get("folder"), dict) else {}
    task_list = task.get("list") if isinstance(task.get("list"), dict) else {}
    location_parts = [
        part
        for part in (folder.get("name"), task_list.get("name"))
        if part and part != "hidden"
    ]
    return {
        "task_id": str(task.get("id") or NO_TASK_ID),
        "name": task.get("name") or NO_TASK_NAME,
        "url": task.get("url") or "",
        "status": status_name or "",
        "location": " / ".join(location_parts),
    }


def derive_task_activities(
    tasks: Iterable[Dict[str, Any]],
    user_id: str,
    start_ms: int,
    end_ms: int,
) -> List[Dict[str, Any]]:
    """
    Purpose:    Turn task timestamps into dated activity signals for the user.
    Usage:      ``tasks`` are raw ClickUp task payloads (typically tasks assigned to the
                user and updated in range). Produces:
                  created  - creator is the user and date_created is in range (attributed)
                  closed   - date_done/date_closed in range (actor unknown)
                  updated  - date_updated in range and not the same day as a close
                             (actor unknown, and only the most recent change survives)
    Version:    0.1.0
    Changes:    [v0.1.0] Initial.
    """
    user_key = str(user_id)
    activities: List[Dict[str, Any]] = []
    for task in tasks:
        if not isinstance(task, dict) or not task.get("id"):
            continue
        info = task_info_from_task(task)
        creator = task.get("creator") if isinstance(task.get("creator"), dict) else {}

        created_ms = _to_ms(task.get("date_created"))
        if str(creator.get("id")) == user_key and _in_window(created_ms, start_ms, end_ms):
            activities.append({**info, "kind": SIGNAL_CREATED, "at_ms": created_ms})

        closed_ms = _to_ms(task.get("date_done")) or _to_ms(task.get("date_closed"))
        if _in_window(closed_ms, start_ms, end_ms):
            activities.append({**info, "kind": SIGNAL_CLOSED, "at_ms": closed_ms})

        updated_ms = _to_ms(task.get("date_updated"))
        if _in_window(updated_ms, start_ms, end_ms):
            activities.append(
                {**info, "kind": SIGNAL_UPDATED, "at_ms": updated_ms, "_pair_ms": closed_ms}
            )
    return activities


def _task_is_closed(task: Dict[str, Any]) -> bool:
    status = task.get("status") if isinstance(task.get("status"), dict) else {}
    if status.get("type") in CLOSED_STATUS_TYPES:
        return True
    return bool(_to_ms(task.get("date_closed")) or _to_ms(task.get("date_done")))


def derive_schedule_items(
    tasks: Iterable[Dict[str, Any]],
    start_ms: int,
    end_ms: int,
) -> List[Dict[str, Any]]:
    """
    Purpose:    Pull due dates and start dates that land inside the report window.
    Usage:      ``tasks`` are raw ClickUp task payloads, possibly from several overlapping
                queries; duplicates are collapsed by task ID. Each in-range date becomes one
                item with kind "due" or "start" and the task's closed state, so the day
                view can say "due today, already done" or "due last Tuesday, still open".
    Version:    0.1.0
    Changes:    [v0.1.0] Initial.
    """
    seen = set()
    items: List[Dict[str, Any]] = []
    for task in tasks:
        if not isinstance(task, dict) or not task.get("id") or task["id"] in seen:
            continue
        seen.add(task["id"])
        info = {**task_info_from_task(task), "closed": _task_is_closed(task)}
        for kind, field in ((SCHEDULE_DUE, "due_date"), (SCHEDULE_START, "start_date")):
            at_ms = _to_ms(task.get(field))
            if _in_window(at_ms, start_ms, end_ms):
                items.append({**info, "kind": kind, "at_ms": at_ms})
    return items


def derive_comment_activities(
    task_info: Dict[str, Any],
    comments: Iterable[Dict[str, Any]],
    user_id: str,
    start_ms: int,
    end_ms: int,
) -> List[Dict[str, Any]]:
    """Return one ``commented`` signal per in-range comment the user wrote on a task."""
    user_key = str(user_id)
    activities = []
    for comment in comments:
        if not isinstance(comment, dict):
            continue
        author = comment.get("user") if isinstance(comment.get("user"), dict) else {}
        at_ms = _to_ms(comment.get("date"))
        if str(author.get("id")) == user_key and _in_window(at_ms, start_ms, end_ms):
            activities.append({**task_info, "kind": SIGNAL_COMMENTED, "at_ms": at_ms})
    return activities


# ==================== Report assembly ====================


def _signal_label(kind: str, count: int, duration_ms: int = 0) -> str:
    if kind == SIGNAL_TRACKED:
        entries = "entry" if count == 1 else "entries"
        return f"Tracked {format_hours(duration_ms)} ({count} {entries})"
    if kind == SIGNAL_COMMENTED:
        return "1 comment" if count == 1 else f"{count} comments"
    if kind == SIGNAL_CREATED:
        return "Created"
    if kind == SIGNAL_CLOSED:
        return "Closed (assigned task, actor unknown)"
    return "Last updated (assigned task, actor unknown)"


def _task_key(item: Dict[str, Any]) -> str:
    return item.get("task_id") or NO_TASK_ID


def _new_task_bucket(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "task_id": item.get("task_id") or NO_TASK_ID,
        "name": item.get("name") or item.get("task_name") or NO_TASK_NAME,
        "url": item.get("url") or item.get("task_url") or "",
        "status": item.get("status") or item.get("task_status") or "",
        "location": item.get("location") or "",
    }


def _entry_record(entry: Dict[str, Any], tz: Optional[tzinfo]) -> Dict[str, Any]:
    start_dt = local_datetime(entry["start_ms"], tz)
    end_ms = entry.get("end_ms")
    end_dt = local_datetime(end_ms, tz) if end_ms else None
    return {
        "id": entry.get("id") or "",
        "task_id": entry.get("task_id") or NO_TASK_ID,
        "task_name": entry.get("task_name") or NO_TASK_NAME,
        "task_url": entry.get("task_url") or "",
        "start_at": start_dt.isoformat(timespec="seconds"),
        "start_time": start_dt.strftime("%H:%M"),
        "end_time": end_dt.strftime("%H:%M") if end_dt and not entry.get("running") else "",
        "duration_ms": entry["duration_ms"],
        "duration": format_hours(entry["duration_ms"]),
        "hours": hours_value(entry["duration_ms"]),
        "description": entry.get("description") or "",
        "running": bool(entry.get("running")),
        "billable": bool(entry.get("billable")),
    }


def _empty_day(day: date) -> Dict[str, Any]:
    return {
        "date": day.isoformat(),
        "weekday": WEEKDAY_NAMES[day.weekday()],
        "label": f"{WEEKDAY_NAMES[day.weekday()]} {day.day} {day.strftime('%b %Y')}",
        "total_ms": 0,
        "entries": [],
        "_tasks": {},
        "_touched": {},
        "_scheduled": {},
    }


def _schedule(day: Dict[str, Any], item: Dict[str, Any], overdue: bool) -> None:
    """Record a due/start date on a day, merging both onto one row when they coincide."""
    bucket = day["_scheduled"].setdefault(
        _task_key(item),
        {**_new_task_bucket(item), "closed": bool(item.get("closed")), "due": False,
         "starts": False, "overdue": False},
    )
    if item.get("kind") == SCHEDULE_DUE:
        bucket["due"] = True
        bucket["overdue"] = overdue
    else:
        bucket["starts"] = True


def _touch(day: Dict[str, Any], item: Dict[str, Any], kind: str, duration_ms: int = 0) -> None:
    key = _task_key(item)
    bucket = day["_touched"].setdefault(key, {**_new_task_bucket(item), "_signals": {}})
    signal = bucket["_signals"].setdefault(kind, {"count": 0, "duration_ms": 0})
    signal["count"] += 1
    signal["duration_ms"] += duration_ms


def _finalise_day(day: Dict[str, Any]) -> Dict[str, Any]:
    tasks = sorted(day.pop("_tasks").values(), key=lambda t: (-t["duration_ms"], t["name"]))
    for task in tasks:
        task["duration"] = format_hours(task["duration_ms"])
        task["hours"] = hours_value(task["duration_ms"])

    touched = []
    for bucket in day.pop("_touched").values():
        raw_signals = bucket.pop("_signals")
        # A close usually bumps date_updated too; one fact is enough, so drop the echo.
        if SIGNAL_CLOSED in raw_signals:
            raw_signals.pop(SIGNAL_UPDATED, None)
        signals = [
            {
                "kind": kind,
                "count": raw_signals[kind]["count"],
                "attributed": kind in ATTRIBUTED_SIGNALS,
                "label": _signal_label(
                    kind, raw_signals[kind]["count"], raw_signals[kind]["duration_ms"]
                ),
            }
            for kind in SIGNAL_ORDER
            if kind in raw_signals
        ]
        tracked_ms = raw_signals.get(SIGNAL_TRACKED, {}).get("duration_ms", 0)
        touched.append(
            {
                **bucket,
                "attributed": any(signal["attributed"] for signal in signals),
                "tracked_ms": tracked_ms,
                "signals": signals,
            }
        )
    touched.sort(key=lambda t: (not t["attributed"], -t["tracked_ms"], t["name"].lower()))

    # Open work first (overdue at the very top), finished work after: the list exists to
    # answer "what is on my plate", and done things are context, not plate.
    scheduled = sorted(
        day.pop("_scheduled").values(),
        key=lambda s: (s["closed"], not s["overdue"], not s["due"], s["name"].lower()),
    )

    day["entries"].sort(key=lambda e: e["start_at"])
    day["tasks"] = tasks
    day["touched"] = touched
    day["scheduled"] = scheduled
    day["total"] = format_hours(day["total_ms"])
    day["hours"] = hours_value(day["total_ms"])
    return day


def _task_rollup(days: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate finalised days into per-task totals with a per-day breakdown."""
    rollup: Dict[str, Dict[str, Any]] = {}
    for day in days:
        for task in day["tasks"]:
            bucket = rollup.setdefault(
                _task_key(task),
                {**_new_task_bucket(task), "total_ms": 0, "entry_count": 0, "per_day": {}},
            )
            bucket["total_ms"] += task["duration_ms"]
            bucket["entry_count"] += task["entry_count"]
            bucket["per_day"][day["date"]] = task["duration_ms"]
    tasks = sorted(rollup.values(), key=lambda t: (-t["total_ms"], t["name"].lower()))
    for task in tasks:
        task["total"] = format_hours(task["total_ms"])
        task["hours"] = hours_value(task["total_ms"])
    return tasks


def build_time_report(
    *,
    user: Dict[str, Any],
    workspace_id: str,
    entries: Iterable[Dict[str, Any]],
    activities: Iterable[Dict[str, Any]],
    start: date,
    end: date,
    tz: Optional[tzinfo],
    tz_label: str,
    week_start: int = 0,
    notes: Optional[List[str]] = None,
    generated_at: Optional[datetime] = None,
    schedule: Iterable[Dict[str, Any]] = (),
) -> Dict[str, Any]:
    """
    Purpose:    Assemble the full report dict shared by every renderer.
    Usage:      ``entries`` are flattened time entries with keys id, task_id, task_name,
                task_url, status, location, start_ms, end_ms, duration_ms, description,
                running, billable. ``activities`` come from derive_task_activities and
                derive_comment_activities; ``schedule`` from derive_schedule_items. Entries
                are bucketed by their start time, so a 22:00-01:00 stint counts in full
                toward the day it began.
    Version:    0.2.0
    Changes:    [v0.1.0] Initial: weeks -> days -> tasks, touched tasks with signal labels.
                [v0.2.0] Per-day "scheduled" list: tasks whose due or start date falls on
                the day, with closed and overdue flags.
    """
    generated = generated_at or datetime.now().astimezone()
    today = local_date(int(generated.timestamp() * 1000), tz)

    days_by_date: Dict[date, Dict[str, Any]] = {}
    cursor = start
    while cursor <= end:
        days_by_date[cursor] = _empty_day(cursor)
        cursor += timedelta(days=1)

    running_entries = 0
    entry_count = 0
    for entry in entries:
        start_ms = entry.get("start_ms")
        if start_ms is None:
            continue
        day = days_by_date.get(local_date(start_ms, tz))
        if day is None:
            continue
        duration_ms = max(int(entry.get("duration_ms") or 0), 0)
        entry = {**entry, "duration_ms": duration_ms}
        entry_count += 1
        running_entries += 1 if entry.get("running") else 0

        day["total_ms"] += duration_ms
        day["entries"].append(_entry_record(entry, tz))
        task = day["_tasks"].setdefault(
            _task_key(entry),
            {**_new_task_bucket(entry), "duration_ms": 0, "entry_count": 0, "descriptions": []},
        )
        task["duration_ms"] += duration_ms
        task["entry_count"] += 1
        description = (entry.get("description") or "").strip()
        if description and description not in task["descriptions"]:
            task["descriptions"].append(description)
        _touch(day, entry, SIGNAL_TRACKED, duration_ms)

    for activity in activities:
        at_ms = activity.get("at_ms")
        if at_ms is None:
            continue
        activity_date = local_date(at_ms, tz)
        day = days_by_date.get(activity_date)
        if day is None:
            continue
        pair_ms = activity.get("_pair_ms")
        if (
            activity.get("kind") == SIGNAL_UPDATED
            and pair_ms is not None
            and local_date(pair_ms, tz) == activity_date
        ):
            continue
        _touch(day, activity, activity.get("kind", SIGNAL_UPDATED))

    for item in schedule:
        at_ms = item.get("at_ms")
        if at_ms is None:
            continue
        item_date = local_date(at_ms, tz)
        day = days_by_date.get(item_date)
        if day is None:
            continue
        _schedule(day, item, overdue=not item.get("closed") and item_date < today)

    days = [_finalise_day(days_by_date[key]) for key in sorted(days_by_date)]

    weeks: List[Dict[str, Any]] = []
    for day in days:
        day_date = date.fromisoformat(day["date"])
        first = week_start_for(day_date, week_start)
        if not weeks or weeks[-1]["_start"] != first:
            iso_year, iso_week, _ = first.isocalendar()
            weeks.append({"_start": first, "iso_week": iso_week, "iso_year": iso_year, "days": []})
        weeks[-1]["days"].append(day)

    for week in weeks:
        week_days = week["days"]
        first_day = date.fromisoformat(week_days[0]["date"])
        last_day = date.fromisoformat(week_days[-1]["date"])
        week.pop("_start")
        week["week_start"] = first_day.isoformat()
        week["week_end"] = last_day.isoformat()
        week["label"] = (
            f"Week {week['iso_week']}: {first_day.day} {first_day.strftime('%b')} to "
            f"{last_day.day} {last_day.strftime('%b %Y')}"
        )
        week["total_ms"] = sum(day["total_ms"] for day in week_days)
        week["total"] = format_hours(week["total_ms"])
        week["hours"] = hours_value(week["total_ms"])
        week["tasks"] = _task_rollup(week_days)

    overall_tasks = _task_rollup(days)
    total_ms = sum(day["total_ms"] for day in days)
    days_tracked = sum(1 for day in days if day["total_ms"] > 0)
    touched_ids = {
        touched["task_id"] for day in days for touched in day["touched"] if touched["attributed"]
    }
    scheduled = [item for day in days for item in day["scheduled"]]

    return {
        "report": "clickup_time_report",
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at": generated.isoformat(timespec="seconds"),
        "workspace_id": str(workspace_id),
        "user": {
            "id": str(user.get("id") or ""),
            "username": user.get("username") or "",
            "email": user.get("email") or "",
        },
        "timezone": tz_label,
        "range": {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "week_start": WEEKDAY_NAMES[week_start],
        },
        "summary": {
            "total_ms": total_ms,
            "total": format_hours(total_ms),
            "hours": hours_value(total_ms),
            "entry_count": entry_count,
            "task_count": len(overall_tasks),
            "days_tracked": days_tracked,
            "average_per_tracked_day": format_hours(
                total_ms // days_tracked if days_tracked else 0
            ),
            "running_entries": running_entries,
            "touched_task_count": len(touched_ids),
            "due_count": sum(1 for item in scheduled if item["due"]),
            "starting_count": sum(1 for item in scheduled if item["starts"]),
            "overdue_count": sum(1 for item in scheduled if item["overdue"]),
        },
        "weeks": weeks,
        "tasks": overall_tasks,
        "notes": list(notes or []),
    }
