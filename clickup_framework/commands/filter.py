"""Filter view command."""

from clickup_framework.commands.base_command import BaseCommand
from clickup_framework.components import DisplayManager
from clickup_framework.commands.utils import create_format_options, get_list_statuses, add_common_args


class FilterCommand(BaseCommand):
    """
    Filter Command using BaseCommand.
    """

    def execute(self):
        """Execute the filter command."""
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

        output = display.filtered_view(
            tasks,
            status=self.args.status if hasattr(self.args, 'status') else None,
            priority=self.args.priority if hasattr(self.args, 'priority') else None,
            tags=self.args.tags if hasattr(self.args, 'tags') else None,
            assignee_id=self.args.assignee if hasattr(self.args, 'assignee') else None,
            include_completed=self.args.include_completed if hasattr(self.args, 'include_completed') else False,
            options=options,
            view_mode=self.args.view_mode if hasattr(self.args, 'view_mode') else 'hierarchy'
        )

        self.print(output)


def filter_command(args):
    """
    Command function wrapper for backward compatibility.

    This function maintains the existing function-based API while
    using the BaseCommand class internally.
    """
    command = FilterCommand(args, command_name='filter')
    command.execute()


def register_command(subparsers):
    """Register the filter command with argparse."""
    parser = subparsers.add_parser(
        'filter',
        help='Display filtered tasks',
        description='Display tasks filtered by status, priority, tags, or assignee',
        aliases=['fil'],
        epilog='''Tips:
  • Filter by status: cum filter <list_id> --status "in progress"
  • Filter by priority: cum filter <list_id> --priority 1
  • Filter by tags: cum filter <list_id> --tags bug urgent
  • Filter by assignee: cum filter <list_id> --assignee 12345678
  • Combine filters: cum filter <list_id> --status open --priority 1
  • Change view mode: cum filter <list_id> --status open --view-mode flat'''
    )
    parser.add_argument('list_id', help='ClickUp list ID or task ID')
    parser.add_argument('--status', help='Filter by status')
    parser.add_argument('--priority', type=int, help='Filter by priority')
    parser.add_argument('--tags', nargs='+', help='Filter by tags')
    parser.add_argument('--assignee', help='Filter by assignee ID')
    parser.add_argument('--view-mode', choices=['hierarchy', 'container', 'flat'],
                        default='hierarchy', help='Display mode (default: hierarchy)')
    add_common_args(parser)
    parser.set_defaults(func=filter_command)
