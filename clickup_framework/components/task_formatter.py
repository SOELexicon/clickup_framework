"""
Rich Task Formatter Module

Provides enhanced formatting for individual tasks with emojis, colors, and detailed information.
"""

from typing import Dict, Any, Optional
from clickup_framework.components.options import FormatOptions
from clickup_framework.utils.colors import (
    colorize, status_color, status_to_code, priority_color, get_task_emoji,
    TextColor, TextStyle
)
from clickup_framework.utils.text import truncate


class RichTaskFormatter:
    """
    Enhanced task formatter with emojis, colors, and styling.

    Provides methods to format task information with various levels of detail.
    """

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

        # Add status code at the beginning of task name
        status_code = status_to_code(status_name or '')
        status_code_str = f"[{status_code}]"
        if options.colorize_output:
            status_code_str = colorize(status_code_str, status_color(status_name))

        # Add task name with status code prefix
        name = task.get('name', 'Untitled')
        full_name = f"{status_code_str} {name}"
        if options.colorize_output:
            color = status_color(status_name)
            full_name = f"{status_code_str} {colorize(name, color)}"
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
                additional_lines.append(f"│  {tag_str}")

        # Description
        if options.show_descriptions and task.get('description'):
            desc = task['description']
            if len(desc) > options.description_length:
                desc = truncate(desc, options.description_length)
            desc_str = f"📝 Description:"
            if options.colorize_output:
                desc_str = colorize(desc_str, TextColor.BRIGHT_WHITE, TextStyle.BOLD)
            additional_lines.append(f"│  {desc_str}")

            # Handle multi-line descriptions - add tree character to each line
            for desc_line in desc.split('\n'):
                additional_lines.append(f"│    {desc_line}")

        # Dates
        if options.show_dates:
            date_parts = []
            if task.get('date_created'):
                date_parts.append(f"Created: {task['date_created']}")
            if task.get('date_updated'):
                date_parts.append(f"Updated: {task['date_updated']}")
            if task.get('due_date'):
                date_parts.append(f"Due: {task['due_date']}")

            if date_parts:
                date_str = f"📅 {' | '.join(date_parts)}"
                if options.colorize_output:
                    date_str = colorize(date_str, TextColor.CYAN)
                additional_lines.append(f"│  {date_str}")

        # Comments
        if options.show_comments > 0 and task.get('comments'):
            comments = task['comments'][:options.show_comments]
            if comments:
                comment_str = f"💬 Comments ({len(comments)}):"
                if options.colorize_output:
                    comment_str = colorize(comment_str, TextColor.BRIGHT_WHITE, TextStyle.BOLD)
                additional_lines.append(f"│  {comment_str}")

                for comment in comments:
                    user = comment.get('user', {}).get('username', 'Unknown')
                    text = comment.get('comment_text', '')
                    if len(text) > 50:
                        text = truncate(text, 50)
                    additional_lines.append(f"│    {user}: {text}")

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
                additional_lines.append(f"│  {rel_str}")

        # Combine everything
        if additional_lines:
            # Add final line marker
            additional_lines.append("└─")
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
