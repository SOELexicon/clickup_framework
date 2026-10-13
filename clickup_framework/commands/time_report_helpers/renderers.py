"""
JSON and Markdown renderers for the ``cum time report`` timesheet.

Both take the dict produced by report_builder.build_time_report and return a string.
The JSON is the report dict as-is (durations in ms, decimal hours and display strings),
so anything downstream can re-total it without parsing "38h 15m".

Variables:  OPEN_WORK_MD_HEADER, OPEN_WORK_MD_DIVIDER
Functions:  render_json, render_markdown (plus private _md_cell, _md_link, _md_detail,
            _md_people, _md_date, _md_due, _md_hours, _week_table, _task_matrix,
            _schedule_label, _open_work_lines, _day_detail)
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from .report_builder import format_estimate_label, format_hours, open_work_label

OPEN_WORK_MD_HEADER = (
    "| Task | Assignees | Status | Start | Due | Est | Total est | Booked (all users) | "
    "Tracked (you) | Priority | Tags | Updated | Flag |"
)
OPEN_WORK_MD_DIVIDER = (
    "| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- | --- |"
)


def render_json(report: Dict[str, Any]) -> str:
    """Serialise the report dict as stable, human-readable JSON."""
    return json.dumps(report, indent=2, default=str, ensure_ascii=False)


def _md_cell(text: Any) -> str:
    """Escape a value for a Markdown table cell (pipes and newlines break the grid)."""
    return str(text if text is not None else "").replace("|", "\\|").replace("\n", " ").strip()


def _md_link(name: str, url: str) -> str:
    label = str(name).replace("[", "\\[").replace("]", "\\]")
    if url and url.startswith(("http://", "https://")):
        return f"[{label}]({url})"
    return label


def _md_detail(report: Dict[str, Any], task_id: Any) -> Dict[str, Any]:
    return (report.get("task_index") or {}).get(task_id or "") or {}


def _md_people(detail: Dict[str, Any]) -> str:
    if not detail:
        return "-"
    names = [person.get("username") for person in detail.get("assignees") or []]
    return _md_cell(", ".join(name for name in names if name)) or "Unassigned"


def _md_date(iso: str) -> str:
    return iso or "-"


def _md_due(detail: Dict[str, Any]) -> str:
    iso = detail.get("due_date") or ""
    if not iso:
        return "-"
    days = detail.get("due_in_days")
    if days is None or detail.get("closed"):
        return iso
    if days < 0:
        return f"{iso} ({-days}d overdue)"
    if days == 0:
        return f"{iso} (today)"
    return f"{iso} (in {days}d)"


def _md_hours(ms: Any) -> str:
    return format_hours(int(ms)) if ms else "-"


def _week_table(week: Dict[str, Any]) -> List[str]:
    lines = [
        "| Day | Date | Tracked | Tasks touched | Due / starting |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for day in week["days"]:
        tracked = day["total"] if day["total_ms"] else "-"
        lines.append(
            f"| {day['weekday']} | {day['date']} | {tracked} | {len(day['touched']) or '-'} | "
            f"{len(day['scheduled']) or '-'} |"
        )
    lines.append(f"| **Total** | | **{week['total']}** | | |")
    return lines


def _task_matrix(report: Dict[str, Any], week: Dict[str, Any]) -> List[str]:
    if not week["tasks"]:
        return ["_No time tracked this week._"]
    days = week["days"]
    header = (
        "| Task | Assignees | Status | "
        + " | ".join(day["weekday"] for day in days)
        + " | Tracked (you) | Est | Total est | Booked (all users) |"
    )
    divider = (
        "| --- | --- | --- | " + " | ".join("---:" for _ in days) + " | ---: | ---: | ---: | ---: |"
    )
    lines = [header, divider]
    for task in week["tasks"]:
        detail = _md_detail(report, task.get("task_id"))
        cells = []
        for day in days:
            ms = task["per_day"].get(day["date"], 0)
            cells.append(format_hours(ms) if ms else "")
        lines.append(
            f"| {_md_cell(_md_link(task['name'], task['url']))} | {_md_people(detail)} | "
            f"{_md_cell(detail.get('status') or task.get('status')) or '-'} | "
            + " | ".join(cells)
            + f" | **{task['total']}** | {task.get('estimate') or '-'} | "
            f"{task.get('total_estimate') or '-'} | {_md_hours(detail.get('booked_ms'))} |"
        )
    lines.append(
        "| **Total** | | | "
        + " | ".join(day["total"] if day["total_ms"] else "" for day in days)
        + f" | **{week['total']}** | | | |"
    )
    return lines


def _schedule_label(item: Dict[str, Any]) -> str:
    parts = []
    if item["due"]:
        parts.append("Overdue" if item["overdue"] else "Due")
    if item["starts"]:
        parts.append("Starts")
    if item["closed"]:
        parts.append("Done")
    estimate = format_estimate_label(item)
    if estimate:
        parts.append(estimate)
    return ", ".join(parts)


def _open_work_lines(report: Dict[str, Any]) -> List[str]:
    items = report.get("open_work") or []
    if not items:
        return []
    summary = report["summary"]
    lines = [
        "## Assigned and tracked",
        "",
        f"{summary.get('open_work_count', 0)} assigned "
        f"({summary.get('open_work_in_progress_count', 0)} in progress, "
        f"{summary.get('open_work_overdue_count', 0)} overdue). "
        f"Time estimated {summary.get('open_work_estimate', '0m')}, "
        f"total time estimated {summary.get('open_work_total_estimate', '0m')}.",
        "",
    ]
    current = None
    for item in items:
        location = item.get("location") or "No list"
        if location != current:
            if current is not None:
                lines.append("")
            lines.extend([f"### {location}", "", OPEN_WORK_MD_HEADER, OPEN_WORK_MD_DIVIDER])
            current = location
        detail = _md_detail(report, item.get("task_id"))
        prefix = "&nbsp;&nbsp;&nbsp;&nbsp;" if item.get("nested") else ""
        tags = ", ".join(detail.get("tags") or [])
        lines.append(
            f"| {prefix}{_md_cell(_md_link(item['name'], item['url']))} | "
            f"{_md_people(detail)} | {_md_cell(item.get('status')) or '-'} | "
            f"{_md_date(detail.get('start_date', ''))} | {_md_due(detail)} | "
            f"{item.get('estimate') or '-'} | {item.get('total_estimate') or '-'} | "
            f"{_md_hours(detail.get('booked_ms'))} | {_md_hours(item.get('tracked_ms'))} | "
            f"{_md_cell((detail.get('priority') or '').title()) or '-'} | "
            f"{_md_cell(tags) or '-'} | {_md_date(detail.get('date_updated', ''))} | "
            f"{open_work_label(item) or '-'} |"
        )
    lines.append("")
    return lines


def _day_detail(report: Dict[str, Any], day: Dict[str, Any]) -> List[str]:
    if not day["entries"] and not day["touched"] and not day["scheduled"]:
        return []
    lines = [f"#### {day['label']} ({day['total']})", ""]

    if day["entries"]:
        lines.append("Time entries:")
        lines.append("")
        lines.append("| Time | Duration | Task | Description |")
        lines.append("| --- | ---: | --- | --- |")
        for entry in day["entries"]:
            span = entry["start_time"]
            if entry["running"]:
                span += " (running)"
            elif entry["end_time"]:
                span += f" to {entry['end_time']}"
            lines.append(
                f"| {span} | {entry['duration']} | "
                f"{_md_cell(_md_link(entry['task_name'], entry['task_url']))} | "
                f"{_md_cell(entry['description']) or '-'} |"
            )
        lines.append("")

    if day["touched"]:
        lines.append("Tasks touched:")
        lines.append("")
        for touched in day["touched"]:
            signals = ", ".join(signal["label"] for signal in touched["signals"])
            where = f" ({touched['location']})" if touched.get("location") else ""
            status = f" [{touched['status']}]" if touched.get("status") else ""
            people = _md_people(_md_detail(report, touched.get("task_id")))
            lines.append(
                f"- {_md_link(touched['name'], touched['url'])}{status}{where} "
                f"(assignees: {people}): {signals}"
            )
        lines.append("")

    if day["scheduled"]:
        lines.append("Due or starting:")
        lines.append("")
        for item in day["scheduled"]:
            where = f" ({item['location']})" if item.get("location") else ""
            status = f" [{item['status']}]" if item.get("status") else ""
            detail = _md_detail(report, item.get("task_id"))
            booked = _md_hours(detail.get("booked_ms"))
            starts = _md_date(detail.get("start_date", ""))
            lines.append(
                f"- {_md_link(item['name'], item['url'])}{status}{where} "
                f"(assignees: {_md_people(detail)}; start {starts}; "
                f"booked {booked}): {_schedule_label(item)}"
            )
        lines.append("")
    return lines


def render_markdown(report: Dict[str, Any]) -> str:
    """
    Purpose:    Render the report as GitHub-flavoured Markdown.
    Usage:      text = render_markdown(build_time_report(...))
    Version:    0.4.0
    Changes:    [v0.1.0] Initial: summary, per-week day table, task x day matrix, day detail.
                [v0.2.0] Due / starting column and per-day "Due or starting" list.
                [v0.3.0] In progress and overdue section, with time estimate and total.
                [v0.4.0] Assigned and tracked as one table per location; assignees, dates,
                booked (all users) and tracked (you) columns from the task_index.
    """
    user = report["user"]
    summary = report["summary"]
    rng = report["range"]
    who = user["username"] or user["id"]

    lines = [
        f"# Time report: {who}",
        "",
        f"- User: {who} (ID {user['id']})",
        f"- Range: {rng['start']} to {rng['end']} (weeks start {rng['week_start']})",
        f"- Time zone: {report['timezone']}",
        f"- Generated: {report['generated_at']}",
        "",
        "## Summary",
        "",
        f"- Total tracked: **{summary['total']}** ({summary['hours']} h)",
        f"- Time entries: {summary['entry_count']}",
        f"- Tasks tracked against: {summary['task_count']}",
        f"- Days with tracked time: {summary['days_tracked']}",
        f"- Average per tracked day: {summary['average_per_tracked_day']}",
        f"- Tasks touched by the user: {summary['touched_task_count']}",
        f"- Due in range: {summary.get('due_count', 0)} "
        f"(overdue and still open: {summary.get('overdue_count', 0)})",
        f"- Starting in range: {summary.get('starting_count', 0)}",
        f"- Assigned: {summary.get('open_work_count', 0)} "
        f"({summary.get('open_work_in_progress_count', 0)} in progress, "
        f"{summary.get('open_work_overdue_count', 0)} overdue)",
        f"- Time estimated on that work: {summary.get('open_work_estimate', '0m')}",
        f"- Total time estimated on that work: {summary.get('open_work_total_estimate', '0m')}",
    ]
    if summary["running_entries"]:
        lines.append(f"- Running timers included up to now: {summary['running_entries']}")
    lines.append("")
    lines.extend(_open_work_lines(report))

    for week in report["weeks"]:
        lines.extend([f"## {week['label']} ({week['total']})", ""])
        lines.extend(_week_table(week))
        lines.extend(["", "### Tasks tracked this week", ""])
        lines.extend(_task_matrix(report, week))
        detail: List[str] = []
        for day in week["days"]:
            detail.extend(_day_detail(report, day))
        if detail:
            lines.extend(["", "### Daily detail", ""])
            lines.extend(detail)
        lines.append("")

    if len(report["weeks"]) > 1 and report["tasks"]:
        lines.extend(["## All tasks in range", ""])
        lines.append(
            "| Task | Location | Assignees | Status | Start | Due | Entries | Tracked (you) | "
            "Est | Total est | Booked (all users) |"
        )
        lines.append("| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |")
        for task in report["tasks"]:
            detail = _md_detail(report, task.get("task_id"))
            lines.append(
                f"| {_md_cell(_md_link(task['name'], task['url']))} | "
                f"{_md_cell(task['location']) or '-'} | {_md_people(detail)} | "
                f"{_md_cell(detail.get('status') or task['status']) or '-'} | "
                f"{_md_date(detail.get('start_date', ''))} | {_md_due(detail)} | "
                f"{task['entry_count']} | {task['total']} | {task.get('estimate') or '-'} | "
                f"{task.get('total_estimate') or '-'} | {_md_hours(detail.get('booked_ms'))} |"
            )
        lines.append("")

    if report["notes"]:
        lines.extend(["## Notes", ""])
        lines.extend(f"- {note}" for note in report["notes"])
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
