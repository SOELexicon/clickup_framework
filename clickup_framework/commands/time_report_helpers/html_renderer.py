"""
Self-contained HTML renderer for the ``cum time report`` timesheet.

One file, no scripts, no web fonts, no CDN: it has to open from a downloads folder on
a train with no signal and still look like someone cared. Light and dark themes follow
the OS. Every piece of ClickUp text goes through html.escape, because task names are
user input and user input has opinions about angle brackets.

Variables:  PAGE_CSS
Functions:  render_html (plus private _plural, _e, _link, _tile, _day_strip, _task_matrix,
            _entries_table, _touched_list, _scheduled_list, _open_work_section,
            _day_details, _all_tasks)
"""

from __future__ import annotations

from html import escape
from typing import Any, Dict, List

from .report_builder import format_estimate_label, format_hours

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
main { max-width: 1180px; margin: 0 auto; padding: 28px 16px 64px; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
h1 { font-size: 26px; margin: 0 0 4px; letter-spacing: -0.01em; }
h2 { font-size: 19px; margin: 0; }
h3 { font-size: 14px; margin: 22px 0 10px; color: var(--muted); text-transform: uppercase;
     letter-spacing: 0.06em; }
.meta { color: var(--muted); display: flex; flex-wrap: wrap; gap: 6px 18px; margin-bottom: 22px; }
.tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px;
         margin-bottom: 28px; }
.tile { background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
        padding: 14px 16px; }
.tile .k { color: var(--muted); font-size: 12px; }
.tile .v { font-size: 22px; font-weight: 650; margin-top: 2px; font-variant-numeric: tabular-nums; }
section.week { background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
               padding: 18px 18px 8px; margin-bottom: 22px; }
.week-head { display: flex; justify-content: space-between; align-items: baseline; gap: 12px;
             flex-wrap: wrap; }
.pill { background: var(--accent-soft); color: var(--accent); border-radius: 999px;
        padding: 2px 12px; font-weight: 650; font-variant-numeric: tabular-nums; }
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
th { color: var(--muted); font-weight: 600; font-size: 12px; }
td.n, th.n { text-align: right; white-space: nowrap; }
td.empty { color: var(--faint); }
tfoot td { font-weight: 650; border-bottom: none; }
.sub { color: var(--faint); font-size: 12px; }
details { border-top: 1px solid var(--border); padding: 8px 0; }
details:first-of-type { border-top: none; }
summary { cursor: pointer; display: flex; gap: 12px; align-items: baseline; flex-wrap: wrap; }
summary .lbl { font-weight: 650; min-width: 140px; }
summary .sub { margin-left: auto; }
.detail { padding: 6px 0 4px 4px; }
ul.touched { list-style: none; padding: 0; margin: 6px 0 0; }
ul.touched li { padding: 6px 0; border-bottom: 1px dashed var(--border); }
ul.touched li:last-child { border-bottom: none; }
.badge { display: inline-block; font-size: 11px; border-radius: 6px; padding: 1px 7px;
         margin: 2px 4px 0 0; background: var(--accent-soft); color: var(--accent); }
.badge.weak { background: var(--weak-soft); color: var(--weak); }
.badge.run { background: transparent; color: var(--running); border: 1px solid var(--running); }
.badge.due { background: var(--due-soft); color: var(--due); }
.badge.start { background: var(--start-soft); color: var(--start); }
.badge.over { background: var(--over-soft); color: var(--over); font-weight: 650; }
.badge.done { background: var(--surface-2); color: var(--faint); }
ul.touched li.closed > a { color: var(--muted); text-decoration: line-through; }
.notes { color: var(--muted); font-size: 13px; }
.notes li { margin-bottom: 4px; }
.legend { color: var(--faint); font-size: 12px; margin-top: 6px; }
@media (max-width: 720px) {
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


def _task_matrix(week: Dict[str, Any]) -> str:
    if not week["tasks"]:
        return '<p class="sub">No time tracked this week.</p>'
    days = week["days"]
    head = "".join(f'<th class="n">{_e(day["weekday"])}</th>' for day in days)
    rows = []
    for task in week["tasks"]:
        cells = []
        for day in days:
            ms = task["per_day"].get(day["date"], 0)
            if ms:
                cells.append(f'<td class="n">{_e(format_hours(ms))}</td>')
            else:
                cells.append('<td class="n empty">&middot;</td>')
        where = f'<div class="sub">{_e(task["location"])}</div>' if task["location"] else ""
        rows.append(
            f"<tr><td>{_link(task['name'], task['url'])}{where}</td>{''.join(cells)}"
            f'<td class="n"><strong>{_e(task["total"])}</strong></td></tr>'
        )
    foot = "".join(
        f'<td class="n">{_e(day["total"]) if day["total_ms"] else ""}</td>' for day in days
    )
    return (
        '<div class="scroll"><table><thead><tr><th>Task</th>'
        f'{head}<th class="n">Total</th></tr></thead><tbody>{"".join(rows)}</tbody>'
        f'<tfoot><tr><td>Total</td>{foot}<td class="n">{_e(week["total"])}</td></tr></tfoot>'
        "</table></div>"
    )


def _entries_table(day: Dict[str, Any]) -> str:
    rows = []
    for entry in day["entries"]:
        if entry["running"]:
            span = f'{_e(entry["start_time"])} <span class="badge run">running</span>'
        elif entry["end_time"]:
            span = f'{_e(entry["start_time"])} to {_e(entry["end_time"])}'
        else:
            span = _e(entry["start_time"])
        description = _e(entry["description"]) or '<span class="sub">-</span>'
        rows.append(
            f'<tr><td>{span}</td><td class="n">{_e(entry["duration"])}</td>'
            f'<td>{_link(entry["task_name"], entry["task_url"])}</td>'
            f"<td>{description}</td></tr>"
        )
    return (
        '<div class="scroll"><table><thead><tr><th>Time</th><th class="n">Duration</th>'
        f'<th>Task</th><th>Description</th></tr></thead><tbody>{"".join(rows)}</tbody>'
        "</table></div>"
    )


def _touched_list(day: Dict[str, Any]) -> str:
    items = []
    for touched in day["touched"]:
        badges = "".join(
            '<span class="badge{}">{}</span>'.format(
                "" if signal["attributed"] else " weak", _e(signal["label"])
            )
            for signal in touched["signals"]
        )
        extra = " &middot; ".join(
            _e(part) for part in (touched.get("status"), touched.get("location")) if part
        )
        extra_html = f' <span class="sub">{extra}</span>' if extra else ""
        link = _link(touched["name"], touched["url"])
        items.append(f"<li>{link}{extra_html}<div>{badges}</div></li>")
    return f'<ul class="touched">{"".join(items)}</ul>'


def _estimate_html(item: Dict[str, Any]) -> str:
    label = format_estimate_label(item)
    if not label:
        return ""
    return f' <span class="sub">{_e(label)}</span>'


def _scheduled_list(day: Dict[str, Any]) -> str:
    items = []
    for item in day["scheduled"]:
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
        extra = " &middot; ".join(
            _e(part) for part in (item.get("status"), item.get("location")) if part
        )
        extra_html = f' <span class="sub">{extra}</span>' if extra else ""
        link = _link(item["name"], item["url"])
        row_class = ' class="closed"' if item["closed"] else ""
        items.append(
            f"<li{row_class}>{link}{extra_html}{_estimate_html(item)}"
            f"<div>{''.join(badges)}</div></li>"
        )
    return f'<ul class="touched">{"".join(items)}</ul>'


def _open_work_section(report: Dict[str, Any]) -> str:
    items = report.get("open_work") or []
    if not items:
        return ""
    summary = report["summary"]
    rows = []
    for item in items:
        badge = (
            '<span class="badge over">Overdue</span>'
            if item.get("overdue")
            else '<span class="badge start">In progress</span>'
        )
        extra = " &middot; ".join(
            _e(part) for part in (item.get("status"), item.get("location")) if part
        )
        extra_html = f' <span class="sub">{extra}</span>' if extra else ""
        rows.append(
            f"<li>{_link(item['name'], item['url'])}{extra_html}{_estimate_html(item)}"
            f"<div>{badge}</div></li>"
        )
    pill = (
        f"{summary.get('open_work_count', len(items))} &middot; "
        f"total {_e(summary.get('open_work_total_estimate', '0m'))}"
    )
    return (
        '<section class="week"><div class="week-head"><h2>In progress and overdue</h2>'
        f'<span class="pill">{pill}</span></div>'
        f'<ul class="touched">{"".join(rows)}</ul></section>'
    )


def _day_details(week: Dict[str, Any]) -> str:
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
            body.append("<h3>Time entries</h3>" + _entries_table(day))
        if day["touched"]:
            body.append("<h3>Tasks touched</h3>" + _touched_list(day))
        if day["scheduled"]:
            body.append("<h3>Due or starting</h3>" + _scheduled_list(day))
        blocks.append(
            f'<details><summary><span class="lbl">{_e(day["label"])}</span>'
            f'<span class="pill">{_e(day["total"])}</span><span class="sub">{sub}</span></summary>'
            f'<div class="detail">{"".join(body)}</div></details>'
        )
    if not blocks:
        return ""
    return "<h3>Daily detail</h3>" + "".join(blocks)


def _all_tasks(report: Dict[str, Any]) -> str:
    if len(report["weeks"]) < 2 or not report["tasks"]:
        return ""
    rows = "".join(
        f"<tr><td>{_link(task['name'], task['url'])}</td><td>{_e(task['location']) or '-'}</td>"
        f"<td>{_e(task['status']) or '-'}</td><td class=\"n\">{task['entry_count']}</td>"
        f"<td class=\"n\"><strong>{_e(task['total'])}</strong></td></tr>"
        for task in report["tasks"]
    )
    return (
        '<section class="week"><div class="week-head"><h2>All tasks in range</h2>'
        f'<span class="pill">{_e(report["summary"]["total"])}</span></div>'
        '<div class="scroll"><table><thead><tr><th>Task</th><th>Location</th><th>Status</th>'
        f'<th class="n">Entries</th><th class="n">Total</th></tr></thead><tbody>{rows}</tbody>'
        "</table></div></section>"
    )


def render_html(report: Dict[str, Any]) -> str:
    """
    Purpose:    Render the report as a single self-contained HTML page.
    Usage:      html_text = render_html(build_time_report(...))
    Version:    0.3.0
    Changes:    [v0.1.0] Initial: tiles, per-week day strip, task x day matrix, day detail
                with time entries and touched tasks (actor-unknown signals styled apart).
                [v0.2.0] Due / starting list.
                [v0.3.0] In progress and overdue section, with time estimate and total.
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
            f"{_day_strip(week, max_day_ms)}<h3>Tasks tracked</h3>{_task_matrix(week)}"
            f"{_day_details(week)}</section>"
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
        "Total adds subtasks included in the assigned-task cache.</p>"
        "</main></body></html>\n"
    )
