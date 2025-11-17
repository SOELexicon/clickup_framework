"""Container view command."""

from clickup_framework.components import DisplayManager
from clickup_framework.commands.base_command import BaseCommand
from clickup_framework.commands.utils import get_list_statuses, add_common_args


class ContainerCommand(BaseCommand):
    """
    Container view command using BaseCommand.

    Displays tasks organized by container hierarchy (Space → Folder → List).
    """

    def execute(self):
        """Execute the container view command."""
        display = DisplayManager(self.client)

        # Resolve list ID from either list ID, task ID, or "current" keyword
        list_id = self.resolve_list(self.args.list_id)

        # Get the include_completed and show_closed_only flags
        include_completed = getattr(self.args, 'include_completed', False)
        show_closed_only = getattr(self.args, 'show_closed_only', False)

        # Determine if we need to fetch closed tasks from the API
        # We need closed tasks if either include_completed or show_closed_only is True
        include_closed = include_completed or show_closed_only

        # Fetch tasks including subtasks to show proper hierarchy
        result = self.client.get_list_tasks(list_id, include_closed=include_closed, subtasks='true')
        tasks = result.get('tasks', [])

        # Show available statuses
        status_line = get_list_statuses(self.client, list_id, use_color=self.use_color)
        if status_line:
            self.print(status_line)
            self.print()  # Empty line for spacing

        output = display.container_view(tasks, self.format_options)

        self.print(output)


def container_command(args):
    """
    Command function wrapper for backward compatibility.

    This function maintains the existing function-based API while
    using the BaseCommand class internally.
    """
    command = ContainerCommand(args, command_name='container')
    command.execute()


def register_command(subparsers):
    """Register the container command with argparse."""
    parser = subparsers.add_parser(
        'clist',
        aliases=['c', 'container'],
        help='Display tasks by container hierarchy',
        description='Display tasks organized by container hierarchy',
        epilog='''Tips:
  • View by containers: cum c <list_id>
  • Shows: Space → Folder → List structure
  • Organizes by workspace hierarchy
  • Different from task parent-child (use hierarchy for that)
  • Use presets: cum c <list_id> --preset summary'''
    )
    parser.add_argument('list_id', help='ClickUp list ID or task ID')
    add_common_args(parser)
    parser.set_defaults(func=container_command)
