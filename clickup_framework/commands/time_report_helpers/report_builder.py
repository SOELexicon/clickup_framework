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
            SCHEDULE_START, CLOSED_STATUS_TYPES, HEX_COLOR
Functions:  resolve_report_timezone, timezone_label, local_date, local_datetime,
            local_midnight_ms, week_start_for, resolve_report_range, range_bounds_ms,
            format_hours, hours_value, format_estimate_label, open_work_label,
            task_updated_after, task_info_from_task, safe_color, build_task_index,
            rollup_time_estimates,
            derive_task_activities, derive_schedule_items, derive_open_work,
            derive_comment_activities, build_time_report
"""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta, tzinfo
from decimal import Decimal
from typing import Any, Dict, Iterable, List, Optional, Tuple

REPORT_SCHEMA_VERSION = 3
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

# ClickUp colours go into style="" attributes; only plain hex survives.
HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{3,8}$")


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


def format_estimate_label(item: Dict[str, Any]) -> str:
    """
    Purpose:    One line for a task's own time estimate and the total including subtasks.
    Usage:      Empty when neither is set. Both are shown when either is set, so a leaf
                task reads "Est 4h / Total 4h" and a parent with subtasks can differ.
    Version:    0.1.0
    Changes:    [v0.1.0] Initial.
    """
    parts = []
    if item.get("estimate"):
        parts.append(f"Est {item['estimate']}")
    if item.get("total_estimate"):
        parts.append(f"Total {item['total_estimate']}")
    return " / ".join(parts)


def estimates_for(
    tasks: Iterable[Dict[str, Any]], task_ids: Iterable[str]
) -> Dict[str, Dict[str, Any]]:
    """
    Purpose:    Time estimate fields for tasks that have tracked time.
    Usage:      Includes tasks the user booked time to but is not assigned to, so the
                timesheet can show the real estimate instead of a zero.
    Version:    0.1.0
    Changes:    [v0.1.0] Initial.
    """
    task_list = [task for task in tasks if isinstance(task, dict)]
    rollup = rollup_time_estimates(task_list)
    parents: Dict[str, str] = {}
    for task in task_list:
        if not task.get("id"):
            continue
        parent = task.get("parent")
        parents[str(task["id"])] = "" if parent in (None, "", "null") else str(parent)
    estimates: Dict[str, Dict[str, Any]] = {}
    for task_id in task_ids:
        if not task_id:
            continue
        estimates[str(task_id)] = {
            **_estimate_fields(str(task_id), rollup),
            "parent_id": parents.get(str(task_id), ""),
        }
    return estimates


def open_work_label(item: Dict[str, Any]) -> str:
    """Badge text for an assigned task: Done, Overdue, Due today, In progress, or blank."""
    if item.get("closed"):
        return "Done"
    if item.get("overdue"):
        return "Overdue"
    if item.get("due_today"):
        return "Due today"
    if item.get("in_progress"):
        return "In progress"
    return ""


def task_updated_after(task: Dict[str, Any], start_ms: int) -> bool:
    """Return True when the task's date_updated is strictly after ``start_ms``."""
    updated = _to_ms(task.get("date_updated"))
    return updated is not None and updated > start_ms


def _to_ms(value: Any) -> Optional[int]:
    """Parse ClickUp's string-or-int millisecond timestamps."""
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _estimate_ms(task: Dict[str, Any]) -> int:
    """Return a task's own time_estimate in ms, or 0 when it is unset."""
    ms = _to_ms(task.get("time_estimate"))
    if ms is None or ms <= 0:
        return 0
    return ms


def _estimate_fields(task_id: str, rollup: Dict[str, Tuple[int, int]]) -> Dict[str, Any]:
    """Attach display strings for a task's own estimate and its rolled-up total."""
    own, total = rollup.get(str(task_id), (0, 0))
    return {
        "estimate_ms": own,
        "estimate": format_hours(own) if own else "",
        "total_estimate_ms": total,
        "total_estimate": format_hours(total) if total else "",
    }


def rollup_time_estimates(tasks: Iterable[Dict[str, Any]]) -> Dict[str, Tuple[int, int]]:
    """
    Purpose:    Map each task id to (own estimate ms, total including descendant subtasks).
    Usage:      ClickUp's team-task payload with subtasks=true stores each task's own
                ``time_estimate``, not the UI rollup. The total is that value plus every
                descendant present in ``tasks``. A subtask assigned to someone else is
                absent from an assignee-filtered cache, so a parent total can be short
                of the number ClickUp shows when rollup is on.
    Version:    0.1.0
    Changes:    [v0.1.0] Initial.
    """
    by_id: Dict[str, Dict[str, Any]] = {}
    child_ids: Dict[str, List[str]] = {}
    for task in tasks:
        if not isinstance(task, dict) or not task.get("id"):
            continue
        task_id = str(task["id"])
        by_id[task_id] = task
        parent = task.get("parent")
        if parent not in (None, "", "null"):
            kids = child_ids.setdefault(str(parent), [])
            if task_id not in kids:
                kids.append(task_id)

    totals: Dict[str, int] = {}

    def total(task_id: str, stack: set) -> int:
        if task_id in totals:
            return totals[task_id]
        if task_id in stack:
            return 0
        stack.add(task_id)
        own = _estimate_ms(by_id.get(task_id, {}))
        summed = own + sum(total(child_id, stack) for child_id in child_ids.get(task_id, []))
        stack.remove(task_id)
        totals[task_id] = summed
        return summed

    return {task_id: (_estimate_ms(task), total(task_id, set())) for task_id, task in by_id.items()}


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


def safe_color(value: Any) -> str:
    """
    Purpose:    Return a CSS hex colour, or "" for anything else.
    Usage:      ClickUp colours end up inside style="" attributes, so they get a strict
                allow-list rather than an escape: "#abc" passes, "red;}</style>" does not.
    Version:    0.1.0
    Changes:    [v0.1.0] Initial.
    """
    text = str(value or "").strip()
    return text if HEX_COLOR.match(text) else ""


def _iso_day(ms: Optional[int], tz: Optional[tzinfo]) -> str:
    return local_date(ms, tz).isoformat() if ms is not None else ""


def _richness(task: Dict[str, Any]) -> int:
    """Rough count of populated fields, so a full payload beats a compact subtask stub."""
    return sum(1 for value in task.values() if value not in (None, "", [], {}))


def build_task_index(
    tasks: Iterable[Dict[str, Any]],
    tz: Optional[tzinfo],
    today: date,
) -> Dict[str, Dict[str, Any]]:
    """
    Purpose:    One detail record per task the report already read, keyed by task id.
    Usage:      Renderers look rows up here by task_id to show assignees, status, priority,
                tags, start/due/created/updated/closed dates, estimates (own and rolled up
                with the same rollup as the open-work list) and time booked by everyone
                (ClickUp's time_spent, which counts all users, not just the report user).
                Dates are calendar dates in ``tz``; the team-task payload has no "has a time"
                flag, so times are never shown. Missing tasks simply have no entry.
    Version:    0.1.0
    Changes:    [v0.1.0] Initial.
    """
    best: Dict[str, Dict[str, Any]] = {}
    for task in tasks:
        if not isinstance(task, dict) or not task.get("id"):
            continue
        key = str(task["id"])
        if key not in best or _richness(task) > _richness(best[key]):
            best[key] = task

    rollup = rollup_time_estimates(best.values())
    names = {key: task.get("name") or NO_TASK_NAME for key, task in best.items()}
    index: Dict[str, Dict[str, Any]] = {}
    for key, task in best.items():
        status = task.get("status") if isinstance(task.get("status"), dict) else {}
        priority = task.get("priority") if isinstance(task.get("priority"), dict) else {}
        creator = task.get("creator") if isinstance(task.get("creator"), dict) else {}
        parent = task.get("parent")
        parent_id = "" if parent in (None, "", "null") else str(parent)
        due_ms = _to_ms(task.get("due_date"))
        closed_ms = _to_ms(task.get("date_done")) or _to_ms(task.get("date_closed"))
        booked_ms = max(_to_ms(task.get("time_spent")) or 0, 0)
        assignees = [
            {
                "id": str(person.get("id") or ""),
                "username": person.get("username") or person.get("email") or "",
                "initials": person.get("initials") or "",
                "color": safe_color(person.get("color")),
            }
            for person in task.get("assignees") or []
            if isinstance(person, dict)
        ]
        index[key] = {
            **task_info_from_task(task),
            **_estimate_fields(key, rollup),
            "custom_id": task.get("custom_id") or "",
            "status_type": status.get("type") or "",
            "status_color": safe_color(status.get("color")),
            "closed": _task_is_closed(task),
            "priority": priority.get("priority") or "",
            "priority_color": safe_color(priority.get("color")),
            "assignees": assignees,
            "creator": creator.get("username") or "",
            "tags": [
                tag["name"]
                for tag in task.get("tags") or []
                if isinstance(tag, dict) and tag.get("name")
            ],
            "points": task.get("points"),
            "start_date": _iso_day(_to_ms(task.get("start_date")), tz),
            "due_date": _iso_day(due_ms, tz),
            "due_in_days": (
                (local_date(due_ms, tz) - today).days if due_ms is not None else None
            ),
            "date_created": _iso_day(_to_ms(task.get("date_created")), tz),
            "date_updated": _iso_day(_to_ms(task.get("date_updated")), tz),
            "date_closed": _iso_day(closed_ms, tz),
            "booked_ms": booked_ms,
            "booked": format_hours(booked_ms) if booked_ms else "",
            "parent_id": parent_id,
            "parent_name": names.get(parent_id, "") if parent_id else "",
        }
    return index


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
                Work that is already underway or overdue from before the window is not a
                date landing on a day; derive_open_work lists that separately.
    Version:    0.2.0
    Changes:    [v0.1.0] Initial.
                [v0.2.0] Each item carries the task's own time estimate and the total
                including descendant subtasks from the same payload.
    """
    task_list = [task for task in tasks if isinstance(task, dict)]
    rollup = rollup_time_estimates(task_list)
    seen = set()
    items: List[Dict[str, Any]] = []
    for task in task_list:
        if not task.get("id") or task["id"] in seen:
            continue
        seen.add(task["id"])
        info = {
            **task_info_from_task(task),
            **_estimate_fields(str(task["id"]), rollup),
            "closed": _task_is_closed(task),
        }
        for kind, field in ((SCHEDULE_DUE, "due_date"), (SCHEDULE_START, "start_date")):
            at_ms = _to_ms(task.get(field))
            if _in_window(at_ms, start_ms, end_ms):
                items.append({**info, "kind": kind, "at_ms": at_ms})
    return items


def _decimal_order(value: Any) -> Decimal:
    """ClickUp order indexes are long decimal strings; keep them exact for sorting."""
    if value in (None, ""):
        return Decimal("1e30")
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal("1e30")


def _order_tasks_in_list(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Parent task, then its subtasks, each run in ClickUp list order."""
    ids = {task["task_id"] for task in tasks}
    children: Dict[str, List[Dict[str, Any]]] = {}
    roots: List[Dict[str, Any]] = []
    for task in tasks:
        parent = task.get("parent_id") or ""
        if parent and parent in ids:
            children.setdefault(parent, []).append(task)
        else:
            roots.append(task)

    def order_key(task: Dict[str, Any]) -> Tuple[Decimal, str]:
        return (_decimal_order(task.get("orderindex")), task["name"].lower())

    ordered: List[Dict[str, Any]] = []

    def walk(task: Dict[str, Any], nested: bool) -> None:
        ordered.append({**task, "nested": nested})
        for child in sorted(children.get(task["task_id"], []), key=order_key):
            walk(child, True)

    for root in sorted(roots, key=order_key):
        walk(root, False)
    return ordered


def derive_open_work(
    tasks: Iterable[Dict[str, Any]],
    today_start_ms: int,
    today_end_ms: int,
    list_order: Optional[Dict[str, Tuple[int, int, int]]] = None,
    tracked_ms: Optional[Dict[str, int]] = None,
) -> List[Dict[str, Any]]:
    """
    Purpose:    List open assigned tasks, plus any task the user booked time to.
    Usage:      Closed tasks are left out unless their id is in ``tracked_ms``. Tasks
                marked ``_rollup_only`` exist so a parent total can include subtasks and
                are not listed themselves. Overdue means the due date is before today.
                In progress means the due date is after today and the start date is today
                or earlier, or blank. ``list_order`` maps a list id to (space index,
                folder order, list order). Subtasks sit under their parent.
    Version:    0.4.0
    Changes:    [v0.1.0] Initial: overdue and in-progress tasks only.
                [v0.2.0] Every open assigned task, grouped by folder and list order.
                [v0.3.0] Tasks with tracked time stay in the list even when the user
                is not the assignee.
                [v0.4.0] Closed tasks (present only because time was booked) carry
                closed=True and are never flagged overdue, due today or in progress.
    """
    task_list = [task for task in tasks if isinstance(task, dict)]
    rollup = rollup_time_estimates(task_list)
    tracked = {str(task_id): int(ms or 0) for task_id, ms in (tracked_ms or {}).items() if task_id}
    positions = list_order or {}
    unknown = (1_000_000_000, 1_000_000_000, 1_000_000_000)
    seen = set()
    items: List[Dict[str, Any]] = []
    for task in task_list:
        if not task.get("id") or task["id"] in seen:
            continue
        seen.add(task["id"])
        task_key = str(task["id"])
        if task.get("_rollup_only") and task_key not in tracked:
            continue
        if _task_is_closed(task) and task_key not in tracked:
            continue
        due_ms = _to_ms(task.get("due_date"))
        start_ms = _to_ms(task.get("start_date"))
        # Closed tasks are only here because time was booked to them; a finished task is
        # done, not overdue, however late it finished.
        closed = _task_is_closed(task)
        overdue = not closed and due_ms is not None and due_ms < today_start_ms
        due_today = not closed and due_ms is not None and today_start_ms <= due_ms <= today_end_ms
        in_progress = (
            not closed
            and due_ms is not None
            and due_ms > today_end_ms
            and (start_ms is None or start_ms <= today_end_ms)
        )
        parent = task.get("parent")
        parent_id = "" if parent in (None, "", "null") else str(parent)
        task_list_obj = task.get("list") if isinstance(task.get("list"), dict) else {}
        list_id = str(task_list_obj.get("id") or "")
        rank = positions.get(list_id, unknown)
        info = task_info_from_task(task)
        items.append(
            {
                **info,
                **_estimate_fields(str(task["id"]), rollup),
                "parent_id": parent_id,
                "list_id": list_id,
                "closed": closed,
                "overdue": overdue,
                "in_progress": in_progress,
                "due_today": due_today,
                "tracked_ms": tracked.get(task_key, 0),
                "due_ms": due_ms,
                "start_ms": start_ms,
                "orderindex": (
                    "" if task.get("orderindex") in (None, "") else str(task.get("orderindex"))
                ),
                "space_index": rank[0],
                "folder_index": rank[1],
                "list_index": rank[2],
                "nested": False,
            }
        )

    groups: Dict[str, List[Dict[str, Any]]] = {}
    for item in items:
        groups.setdefault(item["list_id"] or item["location"], []).append(item)
    ordered_groups = sorted(
        groups.values(),
        key=lambda group: (
            group[0]["space_index"],
            group[0]["folder_index"],
            group[0]["list_index"],
            group[0]["location"].lower(),
        ),
    )
    flattened: List[Dict[str, Any]] = []
    for group in ordered_groups:
        flattened.extend(_order_tasks_in_list(group))
    return flattened


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
        {
            **_new_task_bucket(item),
            "closed": bool(item.get("closed")),
            "due": False,
            "starts": False,
            "overdue": False,
            "estimate_ms": item.get("estimate_ms") or 0,
            "estimate": item.get("estimate") or "",
            "total_estimate_ms": item.get("total_estimate_ms") or 0,
            "total_estimate": item.get("total_estimate") or "",
        },
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


def _stamp_estimates(
    tasks: List[Dict[str, Any]], estimates: Dict[str, Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Copy time-estimate fields onto rolled-up tracked tasks."""
    if not estimates:
        return tasks
    for task in tasks:
        extra = estimates.get(task.get("task_id") or "")
        if extra:
            task.update(extra)
    return tasks


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


def _plate_estimate_totals(open_work: List[Dict[str, Any]]) -> Tuple[int, int]:
    """
    Sum own estimates, and rolled-up totals without counting a subtask twice.

    A subtask whose parent is also on the plate is already inside the parent's total.
    """
    on_plate = {item["task_id"] for item in open_work}
    own = sum(int(item.get("estimate_ms") or 0) for item in open_work)
    total = sum(
        int(item.get("total_estimate_ms") or 0)
        for item in open_work
        if item.get("parent_id") not in on_plate
    )
    return own, total


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
    open_work: Iterable[Dict[str, Any]] = (),
    estimates: Optional[Dict[str, Dict[str, Any]]] = None,
    task_index: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Purpose:    Assemble the full report dict shared by every renderer.
    Usage:      ``entries`` are flattened time entries with keys id, task_id, task_name,
                task_url, status, location, start_ms, end_ms, duration_ms, description,
                running, billable. ``activities`` come from derive_task_activities and
                derive_comment_activities; ``schedule`` from derive_schedule_items;
                ``open_work`` from derive_open_work. Entries are bucketed by their start
                time, so a 22:00-01:00 stint counts in full toward the day it began.
    Version:    0.4.0
    Changes:    [v0.1.0] Initial: weeks -> days -> tasks, touched tasks with signal labels.
                [v0.2.0] Per-day "scheduled" list: tasks whose due or start date falls on
                the day, with closed and overdue flags.
                [v0.3.0] Open-work list (in progress or overdue as of today) with own and
                rolled-up time estimates.
                [v0.4.0] ``task_index`` from build_task_index is emitted as-is so every
                renderer can show assignees, dates, priority, tags and booked time.
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
        week["tasks"] = _stamp_estimates(_task_rollup(week_days), estimates or {})

    overall_tasks = _stamp_estimates(_task_rollup(days), estimates or {})
    total_ms = sum(day["total_ms"] for day in days)
    days_tracked = sum(1 for day in days if day["total_ms"] > 0)
    touched_ids = {
        touched["task_id"] for day in days for touched in day["touched"] if touched["attributed"]
    }
    scheduled = [item for day in days for item in day["scheduled"]]
    plate = list(open_work)
    plate_own_ms, plate_total_ms = _plate_estimate_totals(plate)

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
            "open_work_count": len(plate),
            "open_work_overdue_count": sum(1 for item in plate if item.get("overdue")),
            "open_work_in_progress_count": sum(1 for item in plate if item.get("in_progress")),
            "open_work_estimate_ms": plate_own_ms,
            "open_work_estimate": format_hours(plate_own_ms),
            "open_work_total_estimate_ms": plate_total_ms,
            "open_work_total_estimate": format_hours(plate_total_ms),
        },
        "weeks": weeks,
        "tasks": overall_tasks,
        "open_work": plate,
        "task_index": dict(task_index or {}),
        "notes": list(notes or []),
    }
