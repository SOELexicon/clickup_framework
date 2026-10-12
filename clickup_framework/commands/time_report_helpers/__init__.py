"""Helpers for the ``cum time report`` timesheet (aggregation and rendering)."""

from .html_renderer import render_html
from .renderers import render_json, render_markdown
from .report_builder import (
    build_time_report,
    derive_comment_activities,
    derive_schedule_items,
    derive_task_activities,
    format_hours,
    range_bounds_ms,
    resolve_report_range,
    resolve_report_timezone,
    task_info_from_task,
    timezone_label,
)

__all__ = [
    "build_time_report",
    "derive_comment_activities",
    "derive_schedule_items",
    "derive_task_activities",
    "format_hours",
    "range_bounds_ms",
    "render_html",
    "render_json",
    "render_markdown",
    "resolve_report_range",
    "resolve_report_timezone",
    "task_info_from_task",
    "timezone_label",
]
