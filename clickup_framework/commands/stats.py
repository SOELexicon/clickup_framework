"""Stats command."""

import sys
from clickup_framework import ClickUpClient, get_context_manager
from clickup_framework.components import DisplayManager
from clickup_framework.commands.utils import get_list_statuses


def stats_command(args):
    """Display task statistics."""
    context = get_context_manager()
    client = ClickUpClient()
    display = DisplayManager(client)

    # Resolve "current" to actual list ID
    try:
        list_id = context.resolve_id('list', args.list_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    result = client.get_list_tasks(list_id)
    tasks = result.get('tasks', [])

    # Show available statuses
    # Note: stats command doesn't have colorize arg, so default to True
    status_line = get_list_statuses(client, list_id, use_color=True)
    if status_line:
        print(status_line)
        print()  # Empty line for spacing

    output = display.summary_stats(tasks)

    print(output)


def register_command(subparsers, add_common_args=None):
    """Register the stats command with argparse."""
    parser = subparsers.add_parser(
        'stats',
        aliases=['st'],
        help='Display task statistics',
        description='Display statistical summary of tasks in a list'
    )
    parser.add_argument('list_id', help='ClickUp list ID')
    parser.set_defaults(func=stats_command)
