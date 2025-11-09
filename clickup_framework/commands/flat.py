"""Flat list view command."""

import sys
from clickup_framework import ClickUpClient, get_context_manager
from clickup_framework.components import DisplayManager
from clickup_framework.commands.utils import create_format_options, get_list_statuses


def flat_command(args):
    """Display tasks in a flat list."""
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
    options = create_format_options(args)

    # Show available statuses
    colorize_val = getattr(args, 'colorize', None)
    colorize = colorize_val if colorize_val is not None else context.get_ansi_output()
    status_line = get_list_statuses(client, list_id, use_color=colorize)
    if status_line:
        print(status_line)
        print()  # Empty line for spacing

    header = args.header if hasattr(args, 'header') and args.header else None
    output = display.flat_view(tasks, options, header)

    print(output)


def register_command(subparsers, add_common_args):
    """Register the flat command with argparse."""
    parser = subparsers.add_parser(
        'flat',
        help='Display tasks in flat list',
        description='Display tasks in a flat list view',
        aliases=['f']
    )
    parser.add_argument('list_id', help='ClickUp list ID')
    parser.add_argument('--header', help='Custom header text')
    add_common_args(parser)
    parser.set_defaults(func=flat_command)
