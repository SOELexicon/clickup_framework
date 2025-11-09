"""
Task Formatter

Transform verbose task JSON into concise, human-readable text.
Achieves 90-95% token reduction through intelligent formatting.
"""

from typing import Dict, Any, Optional
from .base import BaseFormatter, DetailLevel
from ..utils import (
    format_timestamp,
    format_duration,
    format_user_list,
    truncate,
    clean_html,
)


class TaskFormatter(BaseFormatter):
    """
    Format ClickUp task objects.

    Detail Levels:
        - minimal: ID and name only (~50 tokens)
        - summary: + status, assignees, dates (~200 tokens)
        - detailed: + priority, tags, custom fields (~500 tokens)
        - full: Everything including watchers, checklists (~1500 tokens)
    """

    def format(self, task: Dict[str, Any], detail_level: DetailLevel = "summary") -> str:
        """
        Format task based on detail level.

        Args:
            task: Task dictionary from API
            detail_level: One of "minimal", "summary", "detailed", "full"

        Returns:
            Formatted task string
        """
        if detail_level == "minimal":
            return self._format_minimal(task)
        elif detail_level == "summary":
            return self._format_summary(task)
        elif detail_level == "detailed":
            return self._format_detailed(task)
        elif detail_level == "full":
            return self._format_full(task)
        else:
            raise ValueError(f"Invalid detail level: {detail_level}")

    def _format_minimal(self, task: Dict[str, Any]) -> str:
        """
        Minimal format: ID and name only.

        Example: "Task: abc123 - 'Implement feature'"

        Token count: ~50 (95% reduction from raw JSON)
        """
        task_id = task.get("id", "unknown")
        name = task.get("name", "Unnamed")
        return f"Task: {task_id} - \"{name}\""

    def _format_summary(self, task: Dict[str, Any]) -> str:
        """
        Summary format: Key details only.

        Example:
            Task: abc123 - "Implement feature"
            Status: in progress
            Assigned: John Doe, Jane Smith
            Due: 2024-01-15

        Token count: ~200 (92% reduction from raw JSON)
        """
        lines = []

        # ID and name
        task_id = task.get("id", "unknown")
        name = task.get("name", "Unnamed")
        lines.append(f"Task: {task_id} - \"{name}\"")

        # Status
        status = self._get_field(task, "status.status", "Unknown")
        lines.append(f"Status: {status}")

        # Assignees
        assignees = task.get("assignees", [])
        if assignees:
            assignee_names = format_user_list(assignees, max_users=3)
            lines.append(f"Assigned: {assignee_names}")

        # Due date
        due_date = task.get("due_date")
        if due_date:
            formatted_date = format_timestamp(due_date)
            lines.append(f"Due: {formatted_date}")

        return "\n".join(lines)

    def _format_detailed(self, task: Dict[str, Any]) -> str:
        """
        Detailed format: Extended information.

        Example:
            Task: abc123 - "Implement feature"
            Status: in progress | Priority: High
            Created: 2024-01-01 by John Doe
            Assigned: John Doe, Jane Smith
            Due: 2024-01-15
            Tags: backend, api
            Time: 2h tracked / 8h estimated
            List: Development
            Description: Implement the new API endpoint...

        Token count: ~500 (80% reduction from raw JSON)
        """
        lines = []

        # ID and name
        task_id = task.get("id", "unknown")
        name = task.get("name", "Unnamed")
        lines.append(f"Task: {task_id} - \"{name}\"")

        # Status and priority on same line
        status = self._get_field(task, "status.status", "Unknown")
        priority = self._get_priority_text(task)
        if priority:
            lines.append(f"Status: {status} | Priority: {priority}")
        else:
            lines.append(f"Status: {status}")

        # Creator and creation date
        creator = self._get_field(task, "creator.username", "Unknown")
        created = format_timestamp(task.get("date_created"), include_time=False)
        lines.append(f"Created: {created} by {creator}")

        # Assignees
        assignees = task.get("assignees", [])
        if assignees:
            assignee_names = format_user_list(assignees, max_users=5)
            lines.append(f"Assigned: {assignee_names}")

        # Dates
        due_date = task.get("due_date")
        start_date = task.get("start_date")
        if due_date:
            formatted_date = format_timestamp(due_date)
            lines.append(f"Due: {formatted_date}")
        if start_date:
            formatted_date = format_timestamp(start_date)
            lines.append(f"Start: {formatted_date}")

        # Tags
        tags = task.get("tags", [])
        if tags:
            tag_names = [tag.get("name", tag) if isinstance(tag, dict) else tag for tag in tags]
            lines.append(f"Tags: {', '.join(tag_names)}")

        # Time tracking
        time_spent = task.get("time_spent", 0)
        time_estimate = task.get("time_estimate", 0)
        if time_spent or time_estimate:
            spent_str = format_duration(time_spent) if time_spent else "0m"
            estimate_str = format_duration(time_estimate) if time_estimate else "none"
            lines.append(f"Time: {spent_str} tracked / {estimate_str} estimated")

        # List/Location
        list_name = self._get_field(task, "list.name")
        if list_name:
            lines.append(f"List: {list_name}")

        # Dependencies
        dependencies = task.get("dependencies", [])
        if dependencies:
            dep_info = self._format_dependencies(dependencies)
            if dep_info:
                lines.append(f"Dependencies: {dep_info}")

        # Linked Tasks
        linked_tasks = task.get("linked_tasks", [])
        if linked_tasks:
            lines.append(f"Linked: {len(linked_tasks)} task(s)")

        # Description (truncated)
        description = task.get("text_content") or task.get("description", "")
        if description:
            # Clean HTML and truncate
            clean_desc = clean_html(description)
            truncated = truncate(clean_desc, max_length=150)
            if truncated:
                lines.append(f"Description: {truncated}")

        return "\n".join(lines)

    def _format_full(self, task: Dict[str, Any]) -> str:
        """
        Full format: Complete task information.

        Includes everything from detailed plus:
        - Watchers
        - Parent task
        - Subtask count
        - Custom fields
        - Dependencies
        - URL

        Token count: ~1500 (50% reduction from raw JSON)
        """
        lines = []

        # Start with detailed format
        lines.append(self._format_detailed(task))
        lines.append("")  # Blank line separator

        # Watchers
        watchers = task.get("watchers", [])
        if watchers:
            watcher_names = format_user_list(watchers, max_users=10)
            lines.append(f"Watchers: {watcher_names}")

        # Parent task
        parent = task.get("parent")
        if parent:
            lines.append(f"Parent: {parent}")

        # Subtasks
        subtasks = task.get("subtasks", [])
        if subtasks:
            lines.append(f"Subtasks: {len(subtasks)} subtasks")

        # Custom fields
        custom_fields = task.get("custom_fields", [])
        if custom_fields:
            lines.append("Custom Fields:")
            for field in custom_fields[:5]:  # Limit to 5 fields
                field_name = field.get("name", "Unknown")
                field_type = field.get("type", "")
                value = self._format_custom_field_value(field)
                # Highlight relationship fields
                if field_type == "relationship":
                    lines.append(f"  - {field_name} (Relationship): {value}")
                else:
                    lines.append(f"  - {field_name}: {value}")

        # Dependencies (detailed)
        dependencies = task.get("dependencies", [])
        if dependencies:
            waiting_on = [d for d in dependencies if d.get("type") == 0]
            blocking = [d for d in dependencies if d.get("type") == 1]

            if waiting_on:
                lines.append(f"⏳ Waiting On: {len(waiting_on)} task(s)")
                for dep in waiting_on[:3]:  # Show first 3
                    task_id = dep.get("task_id", "unknown")
                    lines.append(f"    - {task_id}")

            if blocking:
                lines.append(f"🚫 Blocking: {len(blocking)} task(s)")
                for dep in blocking[:3]:  # Show first 3
                    task_id = dep.get("depends_on", "unknown")
                    lines.append(f"    - {task_id}")

        # Linked Tasks (detailed)
        linked_tasks = task.get("linked_tasks", [])
        if linked_tasks:
            lines.append(f"🔗 Linked Tasks: {len(linked_tasks)} task(s)")
            for link in linked_tasks[:5]:  # Show first 5
                linked_task_id = link.get("task_id") or link.get("link_id", "unknown")
                lines.append(f"    - {linked_task_id}")

        # URL
        url = task.get("url")
        if url:
            lines.append(f"URL: {url}")

        return "\n".join(lines)

    def _get_priority_text(self, task: Dict[str, Any]) -> Optional[str]:
        """Get human-readable priority text."""
        priority = task.get("priority")
        if not priority:
            return None

        priority_map = {
            "1": "Urgent",
            "2": "High",
            "3": "Normal",
            "4": "Low",
        }

        priority_id = priority.get("id") if isinstance(priority, dict) else str(priority)
        return priority_map.get(str(priority_id), "Unknown")

    def _format_custom_field_value(self, field: Dict[str, Any]) -> str:
        """Format custom field value based on type."""
        value = field.get("value")
        if not value:
            return "None"

        field_type = field.get("type", "")

        # Handle different field types
        if field_type == "drop_down":
            return value.get("name", "Unknown") if isinstance(value, dict) else str(value)
        elif field_type == "date":
            return format_timestamp(value)
        elif field_type == "currency":
            return f"${value / 100:.2f}" if isinstance(value, (int, float)) else str(value)
        elif field_type == "relationship":
            # Handle relationship custom fields (array of task IDs)
            if isinstance(value, list) and len(value) > 0:
                return f"{len(value)} task(s)"
            elif isinstance(value, list):
                return "None"
            return str(value)
        elif isinstance(value, dict):
            # Generic dict handling
            return value.get("name", str(value))
        else:
            return str(value)

    def _format_dependencies(self, dependencies: list) -> str:
        """
        Format dependency list into concise summary.

        Returns string like "2 waiting on, 1 blocking" or empty string if no dependencies.
        """
        if not dependencies:
            return ""

        # Type 0 = waiting on, Type 1 = blocking
        waiting_on = sum(1 for d in dependencies if d.get("type") == 0)
        blocking = sum(1 for d in dependencies if d.get("type") == 1)

        parts = []
        if waiting_on:
            parts.append(f"{waiting_on} waiting on")
        if blocking:
            parts.append(f"{blocking} blocking")

        return ", ".join(parts) if parts else f"{len(dependencies)} dependency(ies)"


# Convenience function
def format_task(task: Dict[str, Any], detail_level: DetailLevel = "summary") -> str:
    """
    Format a task (convenience function).

    Args:
        task: Task dictionary from API
        detail_level: Detail level (minimal, summary, detailed, full)

    Returns:
        Formatted task string
    """
    formatter = TaskFormatter()
    return formatter.format(task, detail_level)


def format_task_list(
    tasks: list[Dict[str, Any]], detail_level: DetailLevel = "summary"
) -> str:
    """
    Format list of tasks (convenience function).

    Args:
        tasks: List of task dictionaries
        detail_level: Detail level for each task

    Returns:
        Formatted tasks string
    """
    return TaskFormatter.format_list(tasks, detail_level)
