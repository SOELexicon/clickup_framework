"""Zero-hours worklog shorthand for ClickUp Framework CLI.

Variables: COMMAND_METADATA
Functions: zero_hours_command, register_command
Classes: ZeroHoursCommand
"""

from __future__ import annotations

from clickup_framework.commands.base_command import BaseCommand
from clickup_framework.commands.utils import add_common_args
from clickup_framework.utils.argparse_helpers import raw_text_formatter


COMMAND_METADATA = {
    "category": "⏱️  Time Tracking",
    "commands": [
        {
            "name": "0h",
            "args": "[task_id] [--description TEXT]",
            "description": "Log a zero-hour worklog comment on a task (acknowledged, no time tracked)",
        }
    ],
}


class ZeroHoursCommand(BaseCommand):
    """
    Purpose:    Add a zero-hour worklog comment to a ClickUp task.
                Useful for acknowledging you worked on or reviewed a task
                without recording a billable or tracked duration.
    Usage:      cum 0h [task_id] [--description TEXT]
                task_id defaults to "current" context.
    Version:    0.1.0
    Changes:    [v0.1.0] Initial: shorthand for zero-duration acknowledgement comments.
    """

    def execute(self) -> None:
        task_value = getattr(self.args, "task_id", None) or "current"
        task_id = self.resolve_id("task", task_value)

        description = (getattr(self.args, "description", None) or "").strip()
        comment_text = f"⏱ 0h — {description}" if description else "⏱ 0h — acknowledged, no time tracked"

        task = self.client.get_task(task_id)
        task_name = task.get("name", task_id)

        self.client.create_task_comment(task_id, comment_text)

        self.print_success(f"Logged 0h on: {task_name}")
        self.print(f"Comment: {comment_text}")


def zero_hours_command(args) -> None:
    ZeroHoursCommand(args, command_name="0h").execute()


def register_command(subparsers) -> None:
    """Register the 0h zero-hours worklog command."""
    parser = subparsers.add_parser(
        "0h",
        help='Log a zero-hour acknowledgement comment on a task (default: current task)',
        formatter_class=raw_text_formatter(),
        description=(
            "Add a zero-hour worklog comment to a ClickUp task. "
            "Use when you worked on or reviewed a task but have no trackable duration to log. "
            "Defaults to the current task context."
        ),
        epilog=(
            "Examples:\n"
            "  cum 0h                               # Comment on current task\n"
            "  cum 0h current --description 'reviewed PR'\n"
            "  cum 0h 86abc123 --description 'quick config check'\n"
        ),
    )
    parser.add_argument(
        "task_id",
        nargs="?",
        default="current",
        help='Task ID or "current" (default: current context)',
    )
    parser.add_argument(
        "--description", "-m",
        default="",
        help="Optional note to include with the zero-hour comment",
    )
    add_common_args(parser)
    parser.set_defaults(func=zero_hours_command)
