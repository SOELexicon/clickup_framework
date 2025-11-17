"""
Rich Task Formatter Module

Provides enhanced formatting for individual tasks with emojis, colors, and detailed information.
"""

from typing import Any, Dict, Optional

from clickup_framework.components.options import FormatOptions
from clickup_framework.utils.colors import (
    USE_COLORS,
    TextColor,
    TextStyle,
    colorize,
    get_progress_state,
    get_status_icon,
    get_task_emoji,
    priority_color,
    status_color,
    status_to_code,
)
from clickup_framework.utils.datetime import format_timestamp
from clickup_framework.utils.text import strip_markdown, truncate


class RichTaskFormatter:
    """
    Enhanced task formatter with emojis, colors, and styling.

    Provides methods to format task information with various levels of detail.
    """

    @staticmethod
    def _count_subtasks(task: Dict[str, Any]) -> tuple[int, int]:
        """
        Recursively count total and completed subtasks.

        Args:
            task: Task dictionary with potential '_children' property

        Returns:
            Tuple of (completed_count, total_count)
        """
        children = task.get("_children", [])
        if not children:
            return (0, 0)

        # Filter out container nodes when counting
        actual_tasks = [c for c in children if not c.get("_is_container")]
        if not actual_tasks:
            # If only containers, recurse into them
            total = 0
            completed = 0
            for child in children:
                if child.get("_is_container"):
                    child_completed, child_total = RichTaskFormatter._count_subtasks(child)
                    completed += child_completed
                    total += child_total
            return (completed, total)

        total = len(actual_tasks)
        completed = 0

        for child in actual_tasks:
            # Check if child is completed
            status = child.get("status", {})
            status_name = status.get("status") if isinstance(status, dict) else status
            status_lower = str(status_name).lower().strip() if status_name else ""

            if status_lower in ("complete", "completed", "done", "closed"):
                completed += 1

            # Recursively count grandchildren
            child_completed, child_total = RichTaskFormatter._count_subtasks(child)
            completed += child_completed
            total += child_total

        return (completed, total)

    @staticmethod
    def format_task(task: Dict[str, Any], options: Optional[FormatOptions] = None) -> str:
        """
        Format a single task with all requested information.

        Args:
            task: Task dictionary from ClickUp API
            options: Format options (uses defaults if not provided)

        Returns:
            Formatted task string
        """
        if options is None:
            options = FormatOptions()

        # Check if this is a container node (workspace/folder/list)
        if task.get("_is_container"):
            # Simple formatting for containers - just return the name
            return task.get("name", "Unknown Container")

        parts = []

        # Check if this is the highlighted task
        is_highlighted = False
        if options.highlight_task_id and task.get("id") == options.highlight_task_id:
            is_highlighted = True
            # Add animated visual indicator for the highlighted task
            if options.colorize_output:
                # Use blinking/bold arrow to draw attention
                indicator = colorize("👉", TextColor.BRIGHT_YELLOW, TextStyle.BOLD)
            else:
                indicator = "👉"
            parts.append(indicator)

        # Add task ID if requested
        if options.show_ids and task.get("id"):
            id_str = f"[{task['id']}]"
            if options.colorize_output:
                if is_highlighted:
                    # Highlight the ID more prominently
                    id_str = colorize(id_str, TextColor.BRIGHT_YELLOW, TextStyle.BOLD)
                else:
                    id_str = colorize(id_str, TextColor.BRIGHT_BLACK)
            parts.append(id_str)

        # Add dependency and blocker indicators
        dependencies = task.get("dependencies", [])
        if dependencies:
            # Count different types of dependencies
            waiting_on = []  # Tasks this task depends on (is waiting for)
            blocking = []  # Tasks this task is blocking

            for dep in dependencies:
                if isinstance(dep, dict):
                    dep_task_id = dep.get("task_id")
                    dep_type = dep.get("type", "waiting_on")  # Default to waiting_on

                    if dep_type == "waiting_on":
                        waiting_on.append(dep_task_id)
                    elif dep_type == "blocking":
                        blocking.append(dep_task_id)
                elif isinstance(dep, str):
                    # If just a string, assume it's waiting_on
                    waiting_on.append(dep)

            # Show dependency indicators
            dep_indicators = []

            if waiting_on:
                count = len(waiting_on)
                if options.colorize_output:
                    # Use emoji or colored text
                    indicator = colorize(f"⏳{count}", TextColor.YELLOW)
                else:
                    indicator = f"D:{count}"
                dep_indicators.append(indicator)

            if blocking:
                count = len(blocking)
                if options.colorize_output:
                    # Use emoji or colored text
                    indicator = colorize(f"🚫{count}", TextColor.RED)
                else:
                    indicator = f"B:{count}"
                dep_indicators.append(indicator)

            if dep_indicators:
                parts.append(" ".join(dep_indicators))

        # Add linked tasks indicator
        linked_tasks = task.get("linked_tasks", [])
        if linked_tasks:
            count = len(linked_tasks)
            if options.colorize_output:
                indicator = colorize(f"🔗{count}", TextColor.CYAN)
            else:
                indicator = f"L:{count}"
            parts.append(indicator)

        # Add assignee indicator
        assignees = task.get("assignees", [])
        if assignees:
            if options.colorize_output:
                # Show initials or count
                if len(assignees) == 1:
                    # Show first assignee's initials
                    assignee = assignees[0]
                    username = assignee.get("username", "")
                    initials = (
                        "".join([c[0].upper() for c in username.split("_")[:2]])
                        if username
                        else "?"
                    )
                    indicator = colorize(f"👤{initials}", TextColor.BLUE)
                else:
                    # Show count if multiple
                    indicator = colorize(f"👥{len(assignees)}", TextColor.BLUE)
            else:
                indicator = f"A:{len(assignees)}"
            parts.append(indicator)

        # Add due date warning (if overdue or due soon)
        due_date = task.get("due_date")
        if due_date:
            from datetime import datetime, timezone

            try:
                # ClickUp returns due_date as milliseconds timestamp
                if isinstance(due_date, str):
                    due_timestamp = int(due_date) / 1000
                else:
                    due_timestamp = due_date / 1000

                due_dt = datetime.fromtimestamp(due_timestamp, tz=timezone.utc)
                now = datetime.now(timezone.utc)
                days_until_due = (due_dt - now).days

                if days_until_due < 0:
                    # Overdue
                    if options.colorize_output:
                        indicator = colorize(
                            f"🔴{abs(days_until_due)}d", TextColor.RED, TextStyle.BOLD
                        )
                    else:
                        indicator = f"OVERDUE:{abs(days_until_due)}d"
                    parts.append(indicator)
                elif days_until_due == 0:
                    # Due today
                    if options.colorize_output:
                        indicator = colorize("📅TODAY", TextColor.YELLOW, TextStyle.BOLD)
                    else:
                        indicator = "DUE:TODAY"
                    parts.append(indicator)
                elif days_until_due <= 3:
                    # Due soon
                    if options.colorize_output:
                        indicator = colorize(f"⚠️{days_until_due}d", TextColor.YELLOW)
                    else:
                        indicator = f"DUE:{days_until_due}d"
                    parts.append(indicator)
            except (ValueError, TypeError):
                pass  # Skip if date parsing fails

        # Add time tracking indicator
        time_estimate = task.get("time_estimate")
        time_spent = task.get("time_spent", 0)
        if time_estimate or time_spent:
            if time_estimate and time_spent:
                # Show both: spent/estimate
                hours_estimate = time_estimate / 3600000  # Convert ms to hours
                hours_spent = time_spent / 3600000
                if options.colorize_output:
                    if hours_spent > hours_estimate:
                        # Over budget
                        indicator = colorize(
                            f"⏱️{hours_spent:.1f}/{hours_estimate:.1f}h", TextColor.RED
                        )
                    else:
                        indicator = colorize(
                            f"⏱️{hours_spent:.1f}/{hours_estimate:.1f}h", TextColor.GREEN
                        )
                else:
                    indicator = f"T:{hours_spent:.1f}/{hours_estimate:.1f}h"
                parts.append(indicator)
            elif time_estimate:
                # Only estimate
                hours_estimate = time_estimate / 3600000
                if options.colorize_output:
                    indicator = colorize(f"⏱️{hours_estimate:.1f}h", TextColor.CYAN)
                else:
                    indicator = f"T:{hours_estimate:.1f}h"
                parts.append(indicator)
            elif time_spent:
                # Only spent time
                hours_spent = time_spent / 3600000
                if options.colorize_output:
                    indicator = colorize(f"⏱️{hours_spent:.1f}h", TextColor.YELLOW)
                else:
                    indicator = f"T:{hours_spent:.1f}h"
                parts.append(indicator)

        # Add task type emoji
        if options.show_type_emoji:
            task_type = task.get("custom_type") or "task"
            task_name = task.get("name", "")
            emoji = get_task_emoji(task_type, task_name)
            parts.append(emoji)

        # Get status for both code and color
        status = task.get("status", {})
        status_name = status.get("status") if isinstance(status, dict) else status

        # Determine status indicator (icon or code)
        if options.show_status_icon:
            # Use icon/emoji for status
            status_indicator = get_status_icon(status_name or "", fallback_to_code=True)
        else:
            # Use 3-letter code
            status_code = status_to_code(status_name or "")
            status_indicator = f"[{status_code}]"

        # Colorize status indicator if enabled
        if options.colorize_output:
            status_indicator = colorize(status_indicator, status_color(status_name))

        # Add task name with status indicator prefix
        name = task.get("name", "Untitled")
        if options.colorize_output:
            color = status_color(status_name)
            full_name = f"{status_indicator} {colorize(name, color)}"
        else:
            full_name = f"{status_indicator} {name}"
        parts.append(full_name)

        # Add priority (if not default)
        priority = task.get("priority")
        if priority and priority.get("priority") != "4":
            priority_val = priority.get("priority", "4")

            # Map string priorities to numbers
            if isinstance(priority_val, str):
                priority_map = {"urgent": "1", "high": "2", "normal": "3", "low": "4"}
                priority_val = priority_map.get(priority_val.lower(), priority_val)

            priority_str = f"(P{priority_val})"
            if options.colorize_output:
                priority_str = colorize(priority_str, priority_color(priority_val))
            parts.append(priority_str)

        # Add progress state indicator (if enabled)
        if options.show_progress_state:
            progress_state = get_progress_state(status_name or "", use_color=options.colorize_output)
            parts.append(progress_state)

        # Add subtask count aggregation (for tasks with children)
        completed_count, total_count = RichTaskFormatter._count_subtasks(task)
        if total_count > 0:
            subtask_str = f"({completed_count}/{total_count} complete)"
            if options.colorize_output:
                # Color based on completion ratio
                if completed_count == total_count:
                    subtask_color = TextColor.BRIGHT_GREEN
                elif completed_count >= total_count / 2:
                    subtask_color = TextColor.YELLOW
                else:
                    subtask_color = TextColor.BRIGHT_RED
                subtask_str = colorize(subtask_str, subtask_color)
            parts.append(subtask_str)

        # Combine the main line
        main_line = " ".join(parts)

        # Add additional sections if requested
        additional_lines = []

        # Tags
        if options.show_tags and task.get("tags"):
            tags = [tag.get("name") for tag in task["tags"] if tag.get("name")]
            if tags:
                tag_str = f"🏷️  Tags: {', '.join(tags)}"
                if options.colorize_output:
                    tag_str = colorize(tag_str, TextColor.BRIGHT_MAGENTA)
                additional_lines.append(tag_str)

        # Description
        if options.show_descriptions and task.get("description"):
            desc = task["description"]

            # Strip markdown formatting when ANSI colors are enabled
            # because terminals don't render markdown, only ANSI codes
            if options.colorize_output or USE_COLORS:
                desc = strip_markdown(desc)

            if len(desc) > options.description_length:
                desc = truncate(desc, options.description_length)
            desc_str = "📝 Description:"
            if options.colorize_output:
                desc_str = colorize(desc_str, TextColor.BRIGHT_WHITE, TextStyle.BOLD)
            additional_lines.append(desc_str)

            # Handle multi-line descriptions with proper indentation
            for desc_line in desc.split("\n"):
                additional_lines.append(f"  {desc_line}")

        # Attachments
        if task.get("attachments"):
            attachments = task["attachments"]
            if attachments:
                attachment_count = len(attachments)
                attachment_str = (
                    f"📎 {attachment_count} attachment{'s' if attachment_count != 1 else ''}"
                )
                if options.colorize_output:
                    attachment_str = colorize(attachment_str, TextColor.BRIGHT_MAGENTA)
                additional_lines.append(attachment_str)

        # Dates
        if options.show_dates:
            date_parts = []
            if task.get("date_created"):
                formatted_created = format_timestamp(task["date_created"], include_time=False)
                date_parts.append(f"Created: {formatted_created}")
            if task.get("date_updated"):
                formatted_updated = format_timestamp(task["date_updated"], include_time=False)
                date_parts.append(f"Updated: {formatted_updated}")
            if task.get("due_date"):
                formatted_due = format_timestamp(task["due_date"], include_time=False)
                date_parts.append(f"Due: {formatted_due}")

            if date_parts:
                date_str = f"📅 {' | '.join(date_parts)}"
                if options.colorize_output:
                    date_str = colorize(date_str, TextColor.CYAN)
                additional_lines.append(date_str)

        # Comments - Show newest first with threaded replies in treeview
        if options.show_comments > 0 and task.get("comments"):
            from clickup_framework.components.tree import TreeFormatter

            all_comments = task["comments"]
            # Sort by date descending (newest first)
            sorted_comments = sorted(
                all_comments,
                key=lambda c: c.get("date", 0) if isinstance(c.get("date"), (int, float)) else 0,
                reverse=True,
            )
            comments = sorted_comments[: options.show_comments]

            if comments:
                comment_str = f"💬 Comments ({len(all_comments)}):"
                if options.colorize_output:
                    comment_str = colorize(comment_str, TextColor.BRIGHT_WHITE, TextStyle.BOLD)
                additional_lines.append(comment_str)

                # Format comments in treeview with threaded replies
                def format_comment_node(comment):
                    """Format a comment for tree display."""
                    user = comment.get("user", {}).get("username", "Unknown")
                    text = comment.get("comment_text", "")
                    reply_count = comment.get('reply_count', 0)

                    # Truncate text for display
                    if len(text) > 50:
                        text = truncate(text, 50)

                    # Format with reply count if present
                    if reply_count and int(reply_count) > 0:
                        if options.colorize_output:
                            return f"{colorize(user, TextColor.BLUE, TextStyle.BOLD)}: {text} {colorize(f'({reply_count} replies)', TextColor.BRIGHT_BLACK)}"
                        else:
                            return f"{user}: {text} ({reply_count} replies)"
                    else:
                        if options.colorize_output:
                            return f"{colorize(user, TextColor.BLUE)}: {text}"
                        else:
                            return f"{user}: {text}"

                def get_comment_children(comment):
                    """Get replies for a comment."""
                    return comment.get('_replies', [])

                # Display each comment with its replies in treeview
                for comment in comments:
                    tree_lines = TreeFormatter.build_tree(
                        [comment],
                        format_comment_node,
                        get_comment_children,
                        prefix="  ",
                        is_last=True
                    )
                    additional_lines.extend(tree_lines)

        # Relationships
        if options.show_relationships:
            relationships = []
            if task.get("dependencies"):
                relationships.append(f"Depends on: {len(task['dependencies'])} task(s)")
            if task.get("linked_tasks"):
                relationships.append(f"Linked: {len(task['linked_tasks'])} task(s)")

            if relationships:
                rel_str = f"🔗 {' | '.join(relationships)}"
                if options.colorize_output:
                    rel_str = colorize(rel_str, TextColor.BRIGHT_CYAN)
                additional_lines.append(rel_str)

        # Custom Fields
        custom_fields = task.get("custom_fields", [])
        if custom_fields and (options.show_custom_fields or options.show_score):
            for cf in custom_fields:
                field_name = cf.get("name", "")
                field_name_lower = field_name.lower()

                # Check if this is a difficulty/score field
                is_difficulty_field = (
                    field_name_lower == "difficulty"
                    or field_name_lower == "score"
                    or field_name_lower.startswith("difficulty ")
                    or field_name_lower.startswith("score ")
                    or field_name_lower.endswith(" difficulty")
                    or field_name_lower.endswith(" score")
                )

                # Show field if:
                # - show_custom_fields is enabled (show all fields), OR
                # - show_score is enabled AND this is a difficulty/score field
                should_show = options.show_custom_fields or (options.show_score and is_difficulty_field)

                if should_show:
                    value = cf.get("value")
                    if value is not None and value != "":
                        # Format the custom field value
                        if isinstance(value, (int, float)):
                            # Numeric value - show with color coding for difficulty/score
                            if is_difficulty_field:
                                # Show as colored score based on difficulty level
                                if value <= 3:
                                    color = TextColor.BRIGHT_GREEN  # Easy
                                elif value <= 6:
                                    color = TextColor.BRIGHT_YELLOW  # Medium
                                else:
                                    color = TextColor.BRIGHT_RED  # Hard
                            else:
                                # Other numeric fields use cyan
                                color = TextColor.BRIGHT_CYAN

                            field_str = f"⚙️  {field_name}: {value}"
                            if options.colorize_output:
                                field_str = (
                                    f"⚙️  {field_name}: {colorize(str(value), color, TextStyle.BOLD)}"
                                )
                            additional_lines.append(field_str)
                        elif isinstance(value, list):
                            # List value (e.g., multi-select dropdown)
                            if value:  # Only show if list is not empty
                                value_str = ", ".join([str(v) for v in value])
                                field_str = f"⚙️  {field_name}: {value_str}"
                                if options.colorize_output:
                                    field_str = colorize(field_str, TextColor.BRIGHT_CYAN)
                                additional_lines.append(field_str)
                        elif isinstance(value, dict):
                            # Complex value (e.g., dropdown with id and name)
                            display_value = value.get("name") or value.get("value") or str(value)
                            field_str = f"⚙️  {field_name}: {display_value}"
                            if options.colorize_output:
                                field_str = colorize(field_str, TextColor.BRIGHT_CYAN)
                            additional_lines.append(field_str)
                        else:
                            # String or other value
                            field_str = f"⚙️  {field_name}: {value}"
                            if options.colorize_output:
                                field_str = colorize(field_str, TextColor.BRIGHT_CYAN)
                            additional_lines.append(field_str)

        # Combine everything
        if additional_lines:
            return main_line + "\n" + "\n".join(additional_lines)
        else:
            return main_line

    @staticmethod
    def format_task_minimal(task: Dict[str, Any]) -> str:
        """
        Format a task with minimal information (ID and name only).

        Args:
            task: Task dictionary

        Returns:
            Minimal formatted task string
        """
        return RichTaskFormatter.format_task(task, FormatOptions.minimal())

    @staticmethod
    def format_task_summary(task: Dict[str, Any]) -> str:
        """
        Format a task with summary information.

        Args:
            task: Task dictionary

        Returns:
            Summary formatted task string
        """
        return RichTaskFormatter.format_task(task, FormatOptions.summary())

    @staticmethod
    def format_task_detailed(task: Dict[str, Any]) -> str:
        """
        Format a task with detailed information.

        Args:
            task: Task dictionary

        Returns:
            Detailed formatted task string
        """
        return RichTaskFormatter.format_task(task, FormatOptions.detailed())
