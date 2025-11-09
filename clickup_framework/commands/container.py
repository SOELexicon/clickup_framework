"""Container view command."""

import sys
from clickup_framework import ClickUpClient, get_context_manager
from clickup_framework.components import DisplayManager
from clickup_framework.commands.utils import create_format_options, get_list_statuses, add_common_args, resolve_list_id


def container_command(args):
    """Display tasks organized by container hierarchy."""
    context = get_context_manager()
    client = ClickUpClient()
    display = DisplayManager(client)

    # Resolve list ID from either list ID, task ID, or "current" keyword
    try:
        list_id = resolve_list_id(client, args.list_id, context)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    result = client.get_list_tasks(list_id)
    tasks = result.get('tasks', [])
    options = create_format_options(args)

    # Show available statuses
    colorize_val = getattr(args, 'colorize', None)
    colorize = colorize_val if colorize_val is not None else context.get_ansi_output()
    status_line = get_list_statuses(client, list_id, use_color=colorize)
    if status_line:
        print(status_line)
        print()  # Empty line for spacing

    output = display.container_view(tasks, options)

    print(output)


def register_command(subparsers):
    """Register the container command with argparse."""
    parser = subparsers.add_parser(
        'clist',
        aliases=['c', 'container'],
        help='Display tasks by container hierarchy',
        description='Display tasks organized by container hierarchy'
    )
    parser.add_argument('list_id', help='ClickUp list ID or task ID')
    add_common_args(parser)
    parser.set_defaults(func=container_command)
