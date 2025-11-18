"""Flat list view command."""

from clickup_framework.commands.base_command import BaseCommand
from clickup_framework.components import DisplayManager
from clickup_framework.commands.utils import create_format_options, get_list_statuses, add_common_args


class FlatCommand(BaseCommand):
    """
    Flat Command using BaseCommand.
    """

    def execute(self):
        """Execute the flat command."""
        display = DisplayManager(self.client)

        # Resolve list ID from either list ID, task ID, or "current" keyword
        list_id = self.resolve_list(self.args.list_id)

        # Get the include_completed and show_closed_only flags
        include_completed = getattr(self.args, 'include_completed', False)
        show_closed_only = getattr(self.args, 'show_closed_only', False)

        # Determine if we need to fetch closed tasks from the API
        # We need closed tasks if either include_completed or show_closed_only is True
        include_closed = include_completed or show_closed_only

        result = self.client.get_list_tasks(list_id, include_closed=include_closed)
        tasks = result.get('tasks', [])
        options = create_format_options(self.args)

        # Show available statuses
        colorize_val = getattr(self.args, 'colorize', None)
        colorize = colorize_val if colorize_val is not None else self.context.get_ansi_output()
        status_line = get_list_statuses(self.client, list_id, use_color=colorize)
        if status_line:
            self.print(status_line)
            self.print()  # Empty line for spacing

        header = self.args.header if hasattr(self.args, 'header') and self.args.header else None
        output = display.flat_view(tasks, options, header)

        self.print(output)


def flat_command(args):
    """
    Command function wrapper for backward compatibility.

    This function maintains the existing function-based API while
    using the BaseCommand class internally.
    """
    command = FlatCommand(args, command_name='flat')
    command.execute()


def register_command(subparsers):
    """Register the flat command with argparse."""
    parser = subparsers.add_parser(
        'flat',
        help='Display tasks in flat list',
        description='Display tasks in a flat list view',
        aliases=['f'],
        epilog='''Tips:
  • View tasks in flat list: cum flat <list_id>
  • Alias: cum f <list_id>
  • No parent-child hierarchy shown
  • Faster rendering than hierarchy view
  • Use presets: cum flat <list_id> --preset summary'''
    )
    parser.add_argument('list_id', help='ClickUp list ID or task ID')
    parser.add_argument('--header', help='Custom header text')
    add_common_args(parser)
    parser.set_defaults(func=flat_command)
