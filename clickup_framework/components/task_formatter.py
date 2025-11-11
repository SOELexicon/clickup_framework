"""
Rich Task Formatter Module

Provides enhanced formatting for individual tasks with emojis, colors, and detailed information.
"""

from typing import Dict, Any, Optional
from clickup_framework.components.options import FormatOptions
from clickup_framework.utils.colors import (
    colorize, status_color, status_to_code, priority_color, get_task_emoji,
    get_status_icon, TextColor, TextStyle, USE_COLORS
)
from clickup_framework.utils.text import truncate, strip_markdown
from clickup_framework.utils.datetime import format_timestamp


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
        children = task.get('_children', [])
        if not children:
            return (0, 0)

        total = len(children)
        completed = 0

        for child in children:
            # Check if child is completed
            status = child.get('status', {})
            status_name = status.get('status') if isinstance(status, dict) else status
            status_lower = str(status_name).lower().strip() if status_name else ''

            if status_lower in ('complete', 'completed', 'done', 'closed'):
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

        parts = []

        # Add task ID if requested
        if options.show_ids and task.get('id'):
            id_str = f"[{task['id']}]"
            if options.colorize_output:
                id_str = colorize(id_str, TextColor.BRIGHT_BLACK)
            parts.append(id_str)

        # Add task type emoji
        if options.show_type_emoji:
            task_type = task.get('custom_type') or 'task'
            emoji = get_task_emoji(task_type)
            parts.append(emoji)

        # Get status for both code and color
        status = task.get('status', {})
        status_name = status.get('status') if isinstance(status, dict) else status

        # Determine status indicator (icon or code)
        if options.show_status_icon:
            # Use icon/emoji for status
            status_indicator = get_status_icon(status_name or '', fallback_to_code=True)
        else:
            # Use 3-letter code
            status_code = status_to_code(status_name or '')
            status_indicator = f"[{status_code}]"

        # Colorize status indicator if enabled
        if options.colorize_output:
            status_indicator = colorize(status_indicator, status_color(status_name))

        # Add task name with status indicator prefix
        name = task.get('name', 'Untitled')
        if options.colorize_output:
            color = status_color(status_name)
            full_name = f"{status_indicator} {colorize(name, color)}"
        else:
            full_name = f"{status_indicator} {name}"
        parts.append(full_name)

        # Add priority (if not default)
        priority = task.get('priority')
        if priority and priority.get('priority') != '4':
            priority_val = priority.get('priority', '4')

            # Map string priorities to numbers
            if isinstance(priority_val, str):
                priority_map = {
                    'urgent': '1',
                    'high': '2',
                    'normal': '3',
                    'low': '4'
                }
                priority_val = priority_map.get(priority_val.lower(), priority_val)

            priority_str = f"(P{priority_val})"
            if options.colorize_output:
                priority_str = colorize(priority_str, priority_color(priority_val))
            parts.append(priority_str)

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
        main_line = ' '.join(parts)

        # Add additional sections if requested
        additional_lines = []

        # Tags
        if options.show_tags and task.get('tags'):
            tags = [tag.get('name') for tag in task['tags'] if tag.get('name')]
            if tags:
                tag_str = f"🏷️  Tags: {', '.join(tags)}"
                if options.colorize_output:
                    tag_str = colorize(tag_str, TextColor.BRIGHT_MAGENTA)
                additional_lines.append(f"  {tag_str}")

        # Description
        if options.show_descriptions and task.get('description'):
            desc = task['description']

            # Strip markdown formatting when ANSI colors are enabled
            # because terminals don't render markdown, only ANSI codes
            if options.colorize_output or USE_COLORS:
                desc = strip_markdown(desc)

            if len(desc) > options.description_length:
                desc = truncate(desc, options.description_length)
            desc_str = f"📝 Description:"
            if options.colorize_output:
                desc_str = colorize(desc_str, TextColor.BRIGHT_WHITE, TextStyle.BOLD)
            additional_lines.append(f"  {desc_str}")

            # Handle multi-line descriptions with proper indentation
            for desc_line in desc.split('\n'):
                additional_lines.append(f"    {desc_line}")

        # Dates
        if options.show_dates:
            date_parts = []
            if task.get('date_created'):
                formatted_created = format_timestamp(task['date_created'], include_time=False)
                date_parts.append(f"Created: {formatted_created}")
            if task.get('date_updated'):
                formatted_updated = format_timestamp(task['date_updated'], include_time=False)
                date_parts.append(f"Updated: {formatted_updated}")
            if task.get('due_date'):
                formatted_due = format_timestamp(task['due_date'], include_time=False)
                date_parts.append(f"Due: {formatted_due}")

            if date_parts:
                date_str = f"📅 {' | '.join(date_parts)}"
                if options.colorize_output:
                    date_str = colorize(date_str, TextColor.CYAN)
                additional_lines.append(f"  {date_str}")

        # Comments
        if options.show_comments > 0 and task.get('comments'):
            comments = task['comments'][:options.show_comments]
            if comments:
                comment_str = f"💬 Comments ({len(comments)}):"
                if options.colorize_output:
                    comment_str = colorize(comment_str, TextColor.BRIGHT_WHITE, TextStyle.BOLD)
                additional_lines.append(f"  {comment_str}")

                for comment in comments:
                    user = comment.get('user', {}).get('username', 'Unknown')
                    text = comment.get('comment_text', '')
                    if len(text) > 50:
                        text = truncate(text, 50)
                    additional_lines.append(f"    {user}: {text}")

        # Relationships
        if options.show_relationships:
            relationships = []
            if task.get('dependencies'):
                relationships.append(f"Depends on: {len(task['dependencies'])} task(s)")
            if task.get('linked_tasks'):
                relationships.append(f"Linked: {len(task['linked_tasks'])} task(s)")

            if relationships:
                rel_str = f"🔗 {' | '.join(relationships)}"
                if options.colorize_output:
                    rel_str = colorize(rel_str, TextColor.BRIGHT_CYAN)
                additional_lines.append(f"  {rel_str}")

        # Custom Fields - Show Difficulty Score if set
        custom_fields = task.get('custom_fields', [])
        for cf in custom_fields:
            # Check for Difficulty Score field (exact match or prefix/suffix)
            field_name = cf.get('name', '')
            field_name_lower = field_name.lower()
            # Match only if field name starts/ends with difficulty/score or is exactly "difficulty" or "score"
            is_difficulty_field = (
                field_name_lower == 'difficulty' or 
                field_name_lower == 'score' or
                field_name_lower.startswith('difficulty ') or
                field_name_lower.startswith('score ') or
                field_name_lower.endswith(' difficulty') or
                field_name_lower.endswith(' score')
            )
            if is_difficulty_field:
                value = cf.get('value')
                if value is not None and value != '':
                    # Format the difficulty score
                    if isinstance(value, (int, float)):
                        # Show as colored score based on difficulty level
                        if value <= 3:
                            color = TextColor.BRIGHT_GREEN  # Easy
                        elif value <= 6:
                            color = TextColor.BRIGHT_YELLOW  # Medium
                        else:
                            color = TextColor.BRIGHT_RED  # Hard

                        score_str = f"⚙️  {field_name}: {value}"
                        if options.colorize_output:
                            score_str = f"⚙️  {field_name}: {colorize(str(value), color, TextStyle.BOLD)}"
                        additional_lines.append(f"  {score_str}")
                    else:
                        # Non-numeric custom field value
                        score_str = f"⚙️  {field_name}: {value}"
                        if options.colorize_output:
                            score_str = colorize(score_str, TextColor.BRIGHT_CYAN)
                        additional_lines.append(f"  {score_str}")

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
