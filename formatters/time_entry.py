"""
Time Entry Formatter

Transform verbose time entry JSON into concise, human-readable text.
Achieves 90-95% token reduction through intelligent formatting.
"""

from typing import Dict, Any
from .base import BaseFormatter, DetailLevel
from ..utils import (
    format_timestamp,
    format_duration,
    truncate,
)


class TimeEntryFormatter(BaseFormatter):
    """
    Format ClickUp time entry objects.

    Detail Levels:
        - minimal: Duration and task only (~30 tokens)
        - summary: + user, date, task name (~100 tokens)
        - detailed: + description, billable status (~250 tokens)
        - full: Everything including tags, source (~400 tokens)
    """

    def format(self, entry: Dict[str, Any], detail_level: DetailLevel = "summary") -> str:
        """
        Format time entry based on detail level.

        Args:
            entry: Time entry dictionary from API
            detail_level: One of "minimal", "summary", "detailed", "full"

        Returns:
            Formatted time entry string
        """
        if detail_level == "minimal":
            return self._format_minimal(entry)
        elif detail_level == "summary":
            return self._format_summary(entry)
        elif detail_level == "detailed":
            return self._format_detailed(entry)
        elif detail_level == "full":
            return self._format_full(entry)
        else:
            raise ValueError(f"Invalid detail level: {detail_level}")

    def _format_minimal(self, entry: Dict[str, Any]) -> str:
        """
        Minimal format: Duration and task only.

        Example: "2h 30m on Task: Implement feature"

        Token count: ~30 (95% reduction from raw JSON)
        """
        duration = entry.get("duration", 0)
        duration_str = format_duration(abs(int(duration)))

        task = entry.get("task", {})
        task_name = task.get("name", "Unknown task") if task else "Unknown task"

        # Check if timer is running
        if int(duration) < 0:
            return f"⏱️ Running on: {task_name}"
        else:
            return f"{duration_str} on {task_name}"

    def _format_summary(self, entry: Dict[str, Any]) -> str:
        """
        Summary format: Key details with user and date.

        Example:
            Time Entry: 2h 30m by John Doe
            Task: Implement feature
            Date: 2024-01-15 09:00 - 11:30

        Token count: ~100 (90% reduction from raw JSON)
        """
        lines = []

        # Duration and user
        duration = entry.get("duration", 0)
        duration_int = int(duration)
        duration_str = format_duration(abs(duration_int))

        user = self._get_field(entry, "user", {})
        username = user.get("username", "Unknown") if user else "Unknown"

        if duration_int < 0:
            lines.append(f"⏱️ Timer Running by {username}")
        else:
            lines.append(f"Time Entry: {duration_str} by {username}")

        # Task name
        task = entry.get("task", {})
        if task:
            task_name = task.get("name", "Unknown task")
            lines.append(f"Task: {task_name}")

        # Date/time range
        start = entry.get("start")
        end = entry.get("end") or entry.get("at")

        if start:
            start_str = format_timestamp(start, include_time=True)
            if end and duration_int >= 0:
                end_str = format_timestamp(end, include_time=True)
                # Only show time for end if same day
                if start_str.split()[0] == end_str.split()[0]:
                    end_time = end_str.split()[1] if len(end_str.split()) > 1 else ""
                    lines.append(f"Date: {start_str} - {end_time}")
                else:
                    lines.append(f"Date: {start_str} - {end_str}")
            else:
                lines.append(f"Started: {start_str}")

        return "\n".join(lines)

    def _format_detailed(self, entry: Dict[str, Any]) -> str:
        """
        Detailed format: Extended information with description.

        Example:
            Time Entry #123456: 2h 30m by John Doe
            Task: Implement feature (in progress)
            Date: 2024-01-15 09:00 - 11:30
            Billable: Yes
            Description: Working on API endpoint implementation

        Token count: ~250 (85% reduction from raw JSON)
        """
        lines = []

        # ID, duration, and user
        entry_id = entry.get("id", "unknown")
        duration = entry.get("duration", 0)
        duration_int = int(duration)
        duration_str = format_duration(abs(duration_int))

        user = self._get_field(entry, "user", {})
        username = user.get("username", "Unknown") if user else "Unknown"

        if duration_int < 0:
            lines.append(f"⏱️ Time Entry #{entry_id}: Timer Running by {username}")
        else:
            lines.append(f"Time Entry #{entry_id}: {duration_str} by {username}")

        # Task with status
        task = entry.get("task", {})
        if task:
            task_name = task.get("name", "Unknown task")
            task_status = self._get_field(task, "status.status")
            if task_status:
                lines.append(f"Task: {task_name} ({task_status})")
            else:
                lines.append(f"Task: {task_name}")

        # Date/time range
        start = entry.get("start")
        end = entry.get("end") or entry.get("at")

        if start:
            start_str = format_timestamp(start, include_time=True)
            if end and duration_int >= 0:
                end_str = format_timestamp(end, include_time=True)
                if start_str.split()[0] == end_str.split()[0]:
                    end_time = end_str.split()[1] if len(end_str.split()) > 1 else ""
                    lines.append(f"Date: {start_str} - {end_time}")
                else:
                    lines.append(f"Date: {start_str} - {end_str}")
            else:
                lines.append(f"Started: {start_str}")

        # Billable status
        billable = entry.get("billable")
        if billable is not None:
            billable_str = "Yes" if billable else "No"
            lines.append(f"Billable: {billable_str}")

        # Description (truncated)
        description = entry.get("description", "")
        if description:
            truncated = truncate(description, max_length=100)
            lines.append(f"Description: {truncated}")

        return "\n".join(lines)

    def _format_full(self, entry: Dict[str, Any]) -> str:
        """
        Full format: Complete time entry information.

        Includes everything from detailed plus:
        - Tags
        - Source (manual, timer, etc.)
        - Task URL
        - Full description

        Token count: ~400 (80% reduction from raw JSON)
        """
        lines = []

        # Start with detailed format (but we'll rebuild to avoid double truncation)
        entry_id = entry.get("id", "unknown")
        duration = entry.get("duration", 0)
        duration_int = int(duration)
        duration_str = format_duration(abs(duration_int))

        user = self._get_field(entry, "user", {})
        username = user.get("username", "Unknown") if user else "Unknown"

        if duration_int < 0:
            lines.append(f"⏱️ Time Entry #{entry_id}: Timer Running by {username}")
        else:
            lines.append(f"Time Entry #{entry_id}: {duration_str} by {username}")

        # Task with status and ID
        task = entry.get("task", {})
        if task:
            task_id = task.get("id", "")
            task_name = task.get("name", "Unknown task")
            task_status = self._get_field(task, "status.status")
            if task_status:
                lines.append(f"Task: {task_name} ({task_status}) [{task_id}]")
            else:
                lines.append(f"Task: {task_name} [{task_id}]")

        # Date/time range
        start = entry.get("start")
        end = entry.get("end") or entry.get("at")

        if start:
            start_str = format_timestamp(start, include_time=True)
            if end and duration_int >= 0:
                end_str = format_timestamp(end, include_time=True)
                if start_str.split()[0] == end_str.split()[0]:
                    end_time = end_str.split()[1] if len(end_str.split()) > 1 else ""
                    lines.append(f"Date: {start_str} - {end_time}")
                else:
                    lines.append(f"Date: {start_str} - {end_str}")
            else:
                lines.append(f"Started: {start_str}")

        # Billable status
        billable = entry.get("billable")
        if billable is not None:
            billable_str = "Yes" if billable else "No"
            lines.append(f"Billable: {billable_str}")

        # Source
        source = entry.get("source")
        if source:
            lines.append(f"Source: {source}")

        # Tags
        tags = entry.get("tags", [])
        if tags:
            tag_names = [tag.get("name", tag) if isinstance(tag, dict) else str(tag) for tag in tags]
            lines.append(f"Tags: {', '.join(tag_names)}")

        # Full description (no truncation in full mode)
        description = entry.get("description", "")
        if description:
            lines.append(f"Description: {description}")

        # Task URL
        task_url = self._get_field(task, "url") if task else None
        if task_url:
            lines.append(f"Task URL: {task_url}")

        return "\n".join(lines)


# Convenience functions
def format_time_entry(entry: Dict[str, Any], detail_level: DetailLevel = "summary") -> str:
    """
    Format a time entry (convenience function).

    Args:
        entry: Time entry dictionary from API
        detail_level: Detail level (minimal, summary, detailed, full)

    Returns:
        Formatted time entry string
    """
    formatter = TimeEntryFormatter()
    return formatter.format(entry, detail_level)


def format_time_entry_list(
    entries: list[Dict[str, Any]], detail_level: DetailLevel = "summary"
) -> str:
    """
    Format list of time entries (convenience function).

    Args:
        entries: List of time entry dictionaries
        detail_level: Detail level for each entry

    Returns:
        Formatted time entries string
    """
    return TimeEntryFormatter.format_list(entries, detail_level)
