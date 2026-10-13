"""
Self-contained HTML renderer for the ``cum time report`` timesheet.

One file, no scripts, no web fonts, no CDN: it has to open from a downloads folder on
a train with no signal and still look like someone cared. Light and dark themes follow
the OS. Every piece of ClickUp text goes through html.escape, because task names are
user input and user input has opinions about angle brackets. Colours only reach a
style="" attribute after report_builder.safe_color has vetted them as plain hex.

The page runs full width: the task tables carry a dozen columns (who, status, dates,
estimates, booked, tracked, priority, tags), and a 1180px column was hiding most of them.

Variables:  PAGE_CSS, OPEN_WORK_HEADERS, OPEN_WORK_COLUMNS
Functions:  render_html (plus private _plural, _e, _link, _tile, _detail, _ink, _short_date,
            _task_cell, _who_cell, _status_cell, _date_cell, _due_cell, _hours_cell,
            _priority_cell, _tags_cell, _day_strip, _task_matrix, _estimate_footer,
            _week_estimate_totals, _entries_table, _touched_table, _scheduled_table,
            _work_badge, _open_work_section, _day_details, _all_tasks)
"""

from __future__ import annotations

from datetime import date
from html import escape
from typing import Any, Dict, List, Optional

from .report_builder import format_hours, open_work_label, safe_color

PAGE_CSS = """
:root {
  --bg: #f6f7f9; --surface: #ffffff; --surface-2: #f0f2f5; --border: #dfe3e8;
  --text: #1c2430; --muted: #5d6b7a; --faint: #8a96a3;
  --accent: #2563eb; --accent-soft: #dbe6fd; --bar: #3b82f6; --bar-empty: #e6eaef;
  --weak: #8a6d1f; --weak-soft: #fbf1d6; --running: #0f8a5f;
  --due: #7c3aed; --due-soft: #ede4fd; --start: #0f766e; --start-soft: #d7f2ee;
  --over: #b42318; --over-soft: #fde3e0;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #12161c; --surface: #1a2029; --surface-2: #212833; --border: #2e3744;
    --text: #e4e9ef; --muted: #a2adb9; --faint: #6f7b88;
    --accent: #7aa7ff; --accent-soft: #1f2f4d; --bar: #5b8def; --bar-empty: #27303c;
    --weak: #e0c06a; --weak-soft: #3a3220; --running: #4fd1a0;
    --due: #c4a5ff; --due-soft: #2d2348; --start: #5fd3c4; --start-soft: #17332f;
    --over: #ff8a80; --over-soft: #45201d;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--bg); color: var(--text);
  font: 14px/1.5 -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}
main { width: 100%; padding: 24px 28px 64px; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
h1 { font-size: 26px; margin: 0 0 4px; letter-spacing: -0.01em; }
h2 { font-size: 19px; margin: 0; }
h3 { font-size: 14px; margin: 22px 0 10px; color: var(--muted); text-transform: uppercase;
     letter-spacing: 0.06em; }
.meta { color: var(--muted); display: flex; flex-wrap: wrap; gap: 6px 18px; margin-bottom: 22px; }
.tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px;
         margin-bottom: 28px; }
.tile { background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
        padding: 14px 16px; }
.tile .k { color: var(--muted); font-size: 12px; }
.tile .v { font-size: 22px; font-weight: 650; margin-top: 2px; font-variant-numeric: tabular-nums; }
section.week { background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
               padding: 18px 18px 8px; margin-bottom: 22px; }
.week-head { display: flex; justify-content: space-between; align-items: baseline; gap: 12px;
             flex-wrap: wrap; margin-bottom: 10px; }
.pill { background: var(--accent-soft); color: var(--accent); border-radius: 999px;
        padding: 2px 12px; font-weight: 650; font-variant-numeric: tabular-nums;
        white-space: nowrap; }
.days { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 8px;
        margin-top: 16px; }
.day { background: var(--surface-2); border-radius: 8px; padding: 10px 8px 8px;
       text-align: center; }
.day.weekend { opacity: 0.75; }
.day .wd { font-weight: 650; }
.day .dt { color: var(--muted); font-size: 12px; }
.bar { height: 64px; display: flex; align-items: flex-end; justify-content: center;
       margin: 8px 0 6px; }
.bar span { width: 60%; max-width: 36px; background: var(--bar); border-radius: 4px 4px 0 0;
            min-height: 2px; }
.bar span.zero { background: var(--bar-empty); }
.day .tot { font-weight: 650; font-variant-numeric: tabular-nums; }
.day .tch { color: var(--faint); font-size: 11px; }
.scroll { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-variant-numeric: tabular-nums; }
th, td { padding: 6px 8px; border-bottom: 1px solid var(--border); text-align: left;
         vertical-align: top; }
th { color: var(--muted); font-weight: 600; font-size: 12px; white-space: nowrap; }
td.n, th.n { text-align: right; white-space: nowrap; }
td.d { white-space: nowrap; }
td.empty { color: var(--faint); }
tfoot td { font-weight: 650; border-bottom: none; }
table.dense td { font-size: 13px; }
table.dense td.task { min-width: 260px; }
tr.grp td { background: var(--surface-2); font-weight: 650; border-bottom: none;
            padding-top: 8px; }
tr.nested td.task { padding-left: 28px; }
tr.closed td.task a { color: var(--muted); text-decoration: line-through; }
.sub { color: var(--faint); font-size: 12px; }
.late { color: var(--over); font-size: 12px; font-weight: 600; }
.soon { color: var(--due); font-size: 12px; font-weight: 600; }
.who { display: inline-flex; align-items: center; gap: 5px; margin: 1px 10px 1px 0;
       white-space: nowrap; }
.av { display: inline-grid; place-items: center; width: 20px; height: 20px; border-radius: 50%;
      font-size: 9px; font-weight: 700; background: var(--surface-2); color: var(--text);
      border: 1px solid var(--border); }
.st { white-space: nowrap; }
.st i { display: inline-block; width: 9px; height: 9px; border-radius: 50%; margin-right: 6px;
        background: var(--faint); vertical-align: 0; }
.tag { display: inline-block; font-size: 11px; border-radius: 4px; padding: 0 6px;
       margin: 1px 4px 1px 0; background: var(--surface-2); color: var(--muted); }
details { border-top: 1px solid var(--border); padding: 8px 0; }
details:first-of-type { border-top: none; }
summary { cursor: pointer; display: flex; gap: 12px; align-items: baseline; flex-wrap: wrap; }
summary .lbl { font-weight: 650; min-width: 140px; }
summary .sub { margin-left: auto; }
.detail { padding: 6px 0 4px 4px; }
.badge { display: inline-block; font-size: 11px; border-radius: 6px; padding: 1px 7px;
         margin: 2px 4px 0 0; background: var(--accent-soft); color: var(--accent);
         white-space: nowrap; }
.badge.weak { background: var(--weak-soft); color: var(--weak); }
.badge.run { background: transparent; color: var(--running); border: 1px solid var(--running); }
.badge.due { background: var(--due-soft); color: var(--due); }
.badge.start { background: var(--start-soft); color: var(--start); }
.badge.over { background: var(--over-soft); color: var(--over); font-weight: 650; }
.badge.done { background: var(--surface-2); color: var(--faint); }
.notes { color: var(--muted); font-size: 13px; }
.notes li { margin-bottom: 4px; }
.legend { color: var(--faint); font-size: 12px; margin-top: 6px; }
@media (max-width: 720px) {
  main { padding: 20px 16px 48px; }
  .days { grid-template-columns: repeat(4, minmax(0, 1fr)); }
  summary .sub { margin-left: 0; }
}
"""


def _plural(count: int, singular: str, plural: str) -> str:
    return f"{count} {singular if count == 1 else plural}"


def _e(value: Any) -> str:
    return escape(str(value if value is not None else ""), quote=True)


def _link(name: str, url: str) -> str:
    if url and str(url).startswith(("http://", "https://")):
        return f'<a href="{_e(url)}" target="_blank" rel="noopener">{_e(name)}</a>'
    return _e(name)


def _tile(label: str, value: Any) -> str:
    return (
        f'<div class="tile"><div class="k">{_e(label)}</div>'
        f'<div class="v">{_e(value)}</div></div>'
    )


# ==================== shared task cells ====================


def _detail(report: Dict[str, Any], task_id: Optional[str]) -> Dict[str, Any]:
    """Task index record for a row, or {} when the task could not be read."""
    return (report.get("task_index") or {}).get(task_id or "") or {}


def _ink(color: str) -> str:
    """Black or white initials, whichever reads better on ``color``."""
    hexes = color.lstrip("#")
    if len(hexes) in (3, 4):
        hexes = "".join(ch * 2 for ch in hexes[:3])
    try:
        red, green, blue = (int(hexes[i : i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return "#ffffff"
    return "#111111" if (0.299 * red + 0.587 * green + 0.114 * blue) > 150 else "#ffffff"


def _short_date(iso: str) -> str:
    if not iso:
        return ""
    day = date.fromisoformat(iso)
    return f"{day.day} {day.strftime('%b %Y')}"


def _task_cell(row: Dict[str, Any], detail: Dict[str, Any], show_location: bool = False) -> str:
    name = row.get("name") or row.get("task_name") or detail.get("name") or "(no task)"
    url = row.get("url") or row.get("task_url") or detail.get("url") or ""
    task_id = row.get("task_id") or detail.get("task_id") or ""
    bits = []
    ident = detail.get("custom_id") or task_id
    if ident:
        bits.append(_e(ident))
    if detail.get("parent_name") and not row.get("nested"):
        bits.append("in " + _e(detail["parent_name"]))
    location = row.get("location") or detail.get("location")
    if show_location and location:
        bits.append(_e(location))
    sub = f'<div class="sub">{" &middot; ".join(bits)}</div>' if bits else ""
    return f'<td class="task">{_link(name, url)}{sub}</td>'


def _who_cell(detail: Dict[str, Any]) -> str:
    if not detail:
        return '<td class="empty">-</td>'
    people = detail.get("assignees") or []
    if not people:
        return '<td><span class="sub">Unassigned</span></td>'
    chips = []
    for person in people:
        color = safe_color(person.get("color"))
        style = f' style="background:{color};color:{_ink(color)}"' if color else ""
        initials = person.get("initials") or (person.get("username") or "?")[:2].upper()
        chips.append(
            f'<span class="who"><span class="av"{style}>{_e(initials)}</span>'
            f'{_e(person.get("username"))}</span>'
        )
    return f"<td>{''.join(chips)}</td>"


def _status_cell(row: Dict[str, Any], detail: Dict[str, Any]) -> str:
    status = detail.get("status") or row.get("status") or ""
    if not status:
        return '<td class="empty">-</td>'
    color = safe_color(detail.get("status_color"))
    dot = f'<i style="background:{color}"></i>' if color else "<i></i>"
    return f'<td><span class="st">{dot}{_e(status)}</span></td>'


def _date_cell(iso: str) -> str:
    if not iso:
        return '<td class="d empty">-</td>'
    return f'<td class="d">{_e(_short_date(iso))}</td>'


def _due_cell(detail: Dict[str, Any]) -> str:
    iso = detail.get("due_date") or ""
    if not iso:
        return '<td class="d empty">-</td>'
    hint = ""
    days = detail.get("due_in_days")
    if days is not None and not detail.get("closed"):
        if days < 0:
            hint = f'<div class="late">{-days}d overdue</div>'
        elif days == 0:
            hint = '<div class="soon">due today</div>'
        else:
            hint = f'<div class="sub">in {days}d</div>'
    return f'<td class="d">{_e(_short_date(iso))}{hint}</td>'


def _hours_cell(ms: Any, strong: bool = False) -> str:
    value = int(ms or 0)
    if not value:
        return '<td class="n empty">-</td>'
    text = _e(format_hours(value))
    return f'<td class="n"><strong>{text}</strong></td>' if strong else f'<td class="n">{text}</td>'


def _priority_cell(detail: Dict[str, Any]) -> str:
    priority = detail.get("priority") or ""
    if not priority:
        return '<td class="empty">-</td>'
    color = safe_color(detail.get("priority_color"))
    dot = f'<i style="background:{color}"></i>' if color else "<i></i>"
    return f'<td><span class="st">{dot}{_e(priority.title())}</span></td>'


def _tags_cell(detail: Dict[str, Any]) -> str:
    tags = detail.get("tags") or []
    if not tags:
        return '<td class="empty">-</td>'
    return "<td>" + "".join(f'<span class="tag">{_e(tag)}</span>' for tag in tags) + "</td>"


def _row_class(row: Dict[str, Any], detail: Dict[str, Any]) -> str:
    classes = []
    if row.get("nested"):
        classes.append("nested")
    if detail.get("closed") or row.get("closed"):
        classes.append("closed")
    return f' class="{" ".join(classes)}"' if classes else ""


def _estimate(row: Dict[str, Any], detail: Dict[str, Any], field: str) -> int:
    return int(row.get(field) or detail.get(field) or 0)


# ==================== week sections ====================


def _day_strip(week: Dict[str, Any], max_day_ms: int) -> str:
    cells = []
    for day in week["days"]:
        pct = round(day["total_ms"] / max_day_ms * 100) if max_day_ms else 0
        bar_class = "" if day["total_ms"] else ' class="zero"'
        weekend = " weekend" if day["weekday"] in ("Sat", "Sun") else ""
        due = sum(1 for item in day["scheduled"] if item["due"])
        parts = [
            f"{count} {text}"
            for count, text in ((len(day["touched"]), "touched"), (due, "due"))
            if count
        ]
        touched_text = " &middot; ".join(parts) or "&nbsp;"
        cells.append(
            f'<div class="day{weekend}"><div class="wd">{_e(day["weekday"])}</div>'
            f'<div class="dt">{_e(day["date"][5:])}</div>'
            f'<div class="bar"><span{bar_class} style="height:{max(pct, 3)}%"></span></div>'
            f'<div class="tot">{_e(day["total"] if day["total_ms"] else "-")}</div>'
            f'<div class="tch">{touched_text}</div></div>'
        )
    return f'<div class="days">{"".join(cells)}</div>'


def _task_matrix(report: Dict[str, Any], week: Dict[str, Any]) -> str:
    if not week["tasks"]:
        return '<p class="sub">No time tracked this week.</p>'
    days = week["days"]
    head = "".join(f'<th class="n">{_e(day["weekday"])}</th>' for day in days)
    rows = []
    for task in week["tasks"]:
        detail = _detail(report, task.get("task_id"))
        cells = []
        for day in days:
            ms = task["per_day"].get(day["date"], 0)
            if ms:
                cells.append(f'<td class="n">{_e(format_hours(ms))}</td>')
            else:
                cells.append('<td class="n empty">&middot;</td>')
        rows.append(
            f"<tr{_row_class(task, detail)}>{_task_cell(task, detail, show_location=True)}"
            f"{_who_cell(detail)}{_status_cell(task, detail)}{_due_cell(detail)}"
            f"{''.join(cells)}{_hours_cell(task['total_ms'], strong=True)}"
            f"{_hours_cell(_estimate(task, detail, 'estimate_ms'))}"
            f"{_hours_cell(_estimate(task, detail, 'total_estimate_ms'))}"
            f"{_hours_cell(detail.get('booked_ms'))}</tr>"
        )
    foot = "".join(
        f'<td class="n">{_e(day["total"]) if day["total_ms"] else ""}</td>' for day in days
    )
    estimate_ms, total_estimate_ms = _week_estimate_totals(week["tasks"])
    return (
        '<div class="scroll"><table class="dense"><thead><tr><th>Task</th><th>Assignees</th>'
        f'<th>Status</th><th>Due</th>{head}<th class="n">Tracked (you)</th>'
        '<th class="n">Est</th><th class="n">Total est</th><th class="n">Booked (all users)</th>'
        f'</tr></thead><tbody>{"".join(rows)}</tbody>'
        f'<tfoot><tr><td colspan="4">Total</td>{foot}<td class="n">{_e(week["total"])}</td>'
        f'<td class="n">{_e(_estimate_footer(estimate_ms))}</td>'
        f'<td class="n">{_e(_estimate_footer(total_estimate_ms))}</td><td></td></tr></tfoot>'
        "</table></div>"
    )


def _estimate_footer(ms: int) -> str:
    return format_hours(ms) if ms else "-"


def _week_estimate_totals(tasks: List[Dict[str, Any]]) -> tuple:
    """Own estimates, and rolled-up totals without counting a listed subtask twice."""
    ids = {task.get("task_id") for task in tasks}
    own = sum(int(task.get("estimate_ms") or 0) for task in tasks)
    total = sum(
        int(task.get("total_estimate_ms") or 0)
        for task in tasks
        if task.get("parent_id") not in ids
    )
    return own, total


# ==================== day detail ====================


def _entries_table(report: Dict[str, Any], day: Dict[str, Any]) -> str:
    rows = []
    for entry in day["entries"]:
        detail = _detail(report, entry.get("task_id"))
        if entry["running"]:
            span = f'{_e(entry["start_time"])} <span class="badge run">running</span>'
        elif entry["end_time"]:
            span = f'{_e(entry["start_time"])} to {_e(entry["end_time"])}'
        else:
            span = _e(entry["start_time"])
        description = _e(entry["description"]) or '<span class="sub">-</span>'
        rows.append(
            f'<tr><td class="d">{span}</td><td class="n">{_e(entry["duration"])}</td>'
            f"{_task_cell(entry, detail)}{_who_cell(detail)}{_status_cell(entry, detail)}"
            f"<td>{description}</td></tr>"
        )
    return (
        '<div class="scroll"><table class="dense"><thead><tr><th>Time</th>'
        '<th class="n">Duration</th><th>Task</th><th>Assignees</th><th>Status</th>'
        f'<th>Description</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>'
    )


def _touched_table(report: Dict[str, Any], day: Dict[str, Any]) -> str:
    rows = []
    for touched in day["touched"]:
        detail = _detail(report, touched.get("task_id"))
        badges = "".join(
            '<span class="badge{}">{}</span>'.format(
                "" if signal["attributed"] else " weak", _e(signal["label"])
            )
            for signal in touched["signals"]
        )
        rows.append(
            f"<tr{_row_class(touched, detail)}>{_task_cell(touched, detail, show_location=True)}"
            f"{_who_cell(detail)}{_status_cell(touched, detail)}{_due_cell(detail)}"
            f"<td>{badges}</td></tr>"
        )
    return (
        '<div class="scroll"><table class="dense"><thead><tr><th>Task</th><th>Assignees</th>'
        f'<th>Status</th><th>Due</th><th>Activity</th></tr></thead><tbody>{"".join(rows)}'
        "</tbody></table></div>"
    )


def _scheduled_table(report: Dict[str, Any], day: Dict[str, Any]) -> str:
    rows = []
    for item in day["scheduled"]:
        detail = _detail(report, item.get("task_id"))
        badges = []
        if item["due"]:
            badges.append(
                '<span class="badge over">Overdue</span>'
                if item["overdue"]
                else '<span class="badge due">Due</span>'
            )
        if item["starts"]:
            badges.append('<span class="badge start">Starts</span>')
        if item["closed"]:
            badges.append('<span class="badge done">Done</span>')
        rows.append(
            f"<tr{_row_class(item, detail)}>{_task_cell(item, detail, show_location=True)}"
            f"{_who_cell(detail)}{_status_cell(item, detail)}"
            f"{_date_cell(detail.get('start_date', ''))}{_due_cell(detail)}"
            f"{_hours_cell(_estimate(item, detail, 'estimate_ms'))}"
            f"{_hours_cell(_estimate(item, detail, 'total_estimate_ms'))}"
            f"{_hours_cell(detail.get('booked_ms'))}<td>{''.join(badges)}</td></tr>"
        )
    return (
        '<div class="scroll"><table class="dense"><thead><tr><th>Task</th><th>Assignees</th>'
        '<th>Status</th><th>Start</th><th>Due</th><th class="n">Est</th>'
        '<th class="n">Total est</th><th class="n">Booked (all users)</th><th>Flags</th>'
        f'</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'
    )


def _day_details(report: Dict[str, Any], week: Dict[str, Any]) -> str:
    blocks = []
    for day in week["days"]:
        if not day["entries"] and not day["touched"] and not day["scheduled"]:
            continue
        parts = [
            _plural(len(day["entries"]), "entry", "entries"),
            _plural(len(day["tasks"]), "tracked task", "tracked tasks"),
            f"{len(day['touched'])} touched",
        ]
        if day["scheduled"]:
            parts.append(f"{len(day['scheduled'])} due or starting")
        sub = " &middot; ".join(parts)
        body = []
        if day["entries"]:
            body.append("<h3>Time entries</h3>" + _entries_table(report, day))
        if day["touched"]:
            body.append("<h3>Tasks touched</h3>" + _touched_table(report, day))
        if day["scheduled"]:
            body.append("<h3>Due or starting</h3>" + _scheduled_table(report, day))
        blocks.append(
            f'<details><summary><span class="lbl">{_e(day["label"])}</span>'
            f'<span class="pill">{_e(day["total"])}</span><span class="sub">{sub}</span></summary>'
            f'<div class="detail">{"".join(body)}</div></details>'
        )
    if not blocks:
        return ""
    return "<h3>Daily detail</h3>" + "".join(blocks)


# ==================== assigned and tracked ====================


def _work_badge(item: Dict[str, Any]) -> str:
    label = open_work_label(item)
    if label == "Done":
        return '<span class="badge done">Done</span>'
    if label == "Overdue":
        return '<span class="badge over">Overdue</span>'
    if label == "Due today":
        return '<span class="badge due">Due today</span>'
    if label == "In progress":
        return '<span class="badge start">In progress</span>'
    return ""


OPEN_WORK_HEADERS = (
    "<th>Task</th><th>Assignees</th><th>Status</th><th>Start</th><th>Due</th>"
    '<th class="n">Est</th><th class="n">Total est</th><th class="n">Booked (all users)</th>'
    '<th class="n">Tracked (you)</th><th>Priority</th><th>Tags</th><th>Updated</th>'
    "<th>Flag</th>"
)
OPEN_WORK_COLUMNS = 13


def _open_work_section(report: Dict[str, Any]) -> str:
    """
    Purpose:    The "Assigned and tracked" table: every open assigned task plus anything
                the user booked time to, grouped by folder / list in sidebar order.
    Usage:      One header row per location, subtasks indented under their parent.
    Version:    0.2.0
    Changes:    [v0.1.0] Bulleted list per location with status, tracked and estimates.
                [v0.2.0] Full table: assignees, status, start, due (with overdue hint),
                estimates, booked by all users, tracked by the user, priority, tags,
                last updated and the overdue / due today / in progress flag.
    """
    items = report.get("open_work") or []
    if not items:
        return ""
    summary = report["summary"]
    rows: List[str] = []
    current = None
    tracked_total = 0
    for item in items:
        key = (item.get("list_id") or "", item.get("location") or "No list")
        if key != current:
            current = key
            count = sum(
                1
                for other in items
                if (other.get("list_id") or "", other.get("location") or "No list") == key
            )
            rows.append(
                f'<tr class="grp"><td colspan="{OPEN_WORK_COLUMNS}">{_e(key[1])} '
                f'<span class="sub">{_plural(count, "task", "tasks")}</span></td></tr>'
            )
        detail = _detail(report, item.get("task_id"))
        tracked_total += int(item.get("tracked_ms") or 0)
        rows.append(
            f"<tr{_row_class(item, detail)}>{_task_cell(item, detail)}{_who_cell(detail)}"
            f"{_status_cell(item, detail)}{_date_cell(detail.get('start_date', ''))}"
            f"{_due_cell(detail)}{_hours_cell(item.get('estimate_ms'))}"
            f"{_hours_cell(item.get('total_estimate_ms'))}{_hours_cell(detail.get('booked_ms'))}"
            f"{_hours_cell(item.get('tracked_ms'))}{_priority_cell(detail)}{_tags_cell(detail)}"
            f"{_date_cell(detail.get('date_updated', ''))}<td>{_work_badge(item)}</td></tr>"
        )
    pill = (
        f"{summary.get('open_work_count', len(items))} tasks &middot; "
        f"total est {_e(summary.get('open_work_total_estimate', '0m'))}"
    )
    foot = (
        '<tfoot><tr><td colspan="5">Total</td>'
        f'<td class="n">{_e(_estimate_footer(summary.get("open_work_estimate_ms", 0)))}</td>'
        f'<td class="n">{_e(_estimate_footer(summary.get("open_work_total_estimate_ms", 0)))}'
        f'</td><td></td><td class="n">{_e(_estimate_footer(tracked_total))}</td>'
        '<td colspan="4"></td></tr></tfoot>'
    )
    return (
        '<section class="week"><div class="week-head"><h2>Assigned and tracked</h2>'
        f'<span class="pill">{pill}</span></div><div class="scroll"><table class="dense">'
        f'<thead><tr>{OPEN_WORK_HEADERS}</tr></thead><tbody>{"".join(rows)}</tbody>{foot}'
        "</table></div></section>"
    )


def _all_tasks(report: Dict[str, Any]) -> str:
    if len(report["weeks"]) < 2 or not report["tasks"]:
        return ""
    rows = []
    for task in report["tasks"]:
        detail = _detail(report, task.get("task_id"))
        rows.append(
            f"<tr{_row_class(task, detail)}>{_task_cell(task, detail, show_location=True)}"
            f"{_who_cell(detail)}{_status_cell(task, detail)}{_priority_cell(detail)}"
            f"{_date_cell(detail.get('start_date', ''))}{_due_cell(detail)}"
            f'<td class="n">{task["entry_count"]}</td>'
            f"{_hours_cell(task['total_ms'], strong=True)}"
            f"{_hours_cell(_estimate(task, detail, 'estimate_ms'))}"
            f"{_hours_cell(_estimate(task, detail, 'total_estimate_ms'))}"
            f"{_hours_cell(detail.get('booked_ms'))}"
            f"{_date_cell(detail.get('date_updated', ''))}</tr>"
        )
    return (
        '<section class="week"><div class="week-head"><h2>All tasks in range</h2>'
        f'<span class="pill">{_e(report["summary"]["total"])}</span></div>'
        '<div class="scroll"><table class="dense"><thead><tr><th>Task</th><th>Assignees</th>'
        '<th>Status</th><th>Priority</th><th>Start</th><th>Due</th><th class="n">Entries</th>'
        '<th class="n">Tracked (you)</th><th class="n">Est</th><th class="n">Total est</th>'
        '<th class="n">Booked (all users)</th><th>Updated</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></div></section>'
    )


def render_html(report: Dict[str, Any]) -> str:
    """
    Purpose:    Render the report as a single self-contained HTML page.
    Usage:      html_text = render_html(build_time_report(...))
    Version:    0.4.0
    Changes:    [v0.1.0] Initial: tiles, per-week day strip, task x day matrix, day detail
                with time entries and touched tasks (actor-unknown signals styled apart).
                [v0.2.0] Due / starting list.
                [v0.3.0] In progress and overdue section, with time estimate and total.
                [v0.4.0] Full width. Every task list is a table with assignees, status,
                dates, estimates, booked (all users) and tracked (you) columns, read from
                the report's task_index.
    """
    user = report["user"]
    summary = report["summary"]
    rng = report["range"]
    who = user["username"] or user["id"]
    max_day_ms = max(
        (day["total_ms"] for week in report["weeks"] for day in week["days"]), default=0
    )

    tiles = [
        _tile("Total tracked", summary["total"]),
        _tile("Decimal hours", summary["hours"]),
        _tile("Days with time", summary["days_tracked"]),
        _tile("Avg per tracked day", summary["average_per_tracked_day"]),
        _tile("Tasks tracked", summary["task_count"]),
        _tile("Tasks touched", summary["touched_task_count"]),
        _tile("Due in range", summary.get("due_count", 0)),
        _tile("Starting in range", summary.get("starting_count", 0)),
        _tile("Assigned", summary.get("open_work_count", 0)),
        _tile("In progress", summary.get("open_work_in_progress_count", 0)),
        _tile("Overdue", summary.get("open_work_overdue_count", 0)),
        _tile("Time estimated", summary.get("open_work_estimate", "0m")),
        _tile("Total estimated", summary.get("open_work_total_estimate", "0m")),
    ]

    weeks_html: List[str] = []
    for week in report["weeks"]:
        weeks_html.append(
            '<section class="week"><div class="week-head">'
            f'<h2>{_e(week["label"])}</h2><span class="pill">{_e(week["total"])}</span></div>'
            f"{_day_strip(week, max_day_ms)}<h3>Tasks tracked</h3>{_task_matrix(report, week)}"
            f"{_day_details(report, week)}</section>"
        )

    notes = ""
    if report["notes"]:
        notes = (
            '<section class="notes"><h3>Notes</h3><ul>'
            + "".join(f"<li>{_e(note)}</li>" for note in report["notes"])
            + "</ul></section>"
        )

    running = ""
    if summary["running_entries"]:
        running = f"<span>Running timers counted up to now: {summary['running_entries']}</span>"

    title = f"Time report: {who} ({rng['start']} to {rng['end']})"
    return (
        "<!doctype html>\n"
        '<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{_e(title)}</title><style>{PAGE_CSS}</style></head><body><main>"
        f"<h1>Time report: {_e(who)}</h1>"
        '<div class="meta">'
        f"<span>User ID {_e(user['id'])}</span>"
        f"<span>{_e(rng['start'])} to {_e(rng['end'])}</span>"
        f"<span>Time zone: {_e(report['timezone'])}</span>"
        f"<span>Workspace {_e(report['workspace_id'])}</span>"
        f"<span>Generated {_e(report['generated_at'])}</span>{running}</div>"
        f'<div class="tiles">{"".join(tiles)}</div>'
        f"{_open_work_section(report)}{''.join(weeks_html)}{_all_tasks(report)}{notes}"
        '<p class="legend">Blue badges are activity attributed to the user (tracked time, '
        "comments, tasks created). Amber badges are timestamps on tasks assigned to the user "
        "where ClickUp does not say who made the change. Due and Starts mark tasks assigned "
        "to the user whose due or start date falls on that day. In progress means the due "
        "date is after today and the start date is today or earlier, or blank. Overdue means "
        "still open with a due date before today. Est is the task's own time estimate; "
        "Total est adds subtasks included in the assigned-task cache. Booked (all users) is "
        "ClickUp's time spent on the task by everyone, all time. Tracked (you) is the "
        "report user's time on the task inside this date range.</p>"
        "</main></body></html>\n"
    )
