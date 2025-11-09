"""Hierarchy view command."""

import sys
from clickup_framework import ClickUpClient, get_context_manager
from clickup_framework.components import DisplayManager
from clickup_framework.commands.utils import create_format_options, get_list_statuses


def hierarchy_command(args):
    """Display tasks in hierarchical parent-child view."""
    context = get_context_manager()
    client = ClickUpClient()
    display = DisplayManager(client)

    # Check if --all flag is set
    show_all = getattr(args, 'show_all', False)

    # Validate that either list_id or --all is provided
    if not show_all and not args.list_id:
        print("Error: Either provide a list_id or use --all to show all workspace tasks", file=sys.stderr)
        sys.exit(1)

    if show_all and args.list_id:
        print("Error: Cannot use both list_id and --all flag together", file=sys.stderr)
        sys.exit(1)

    if show_all:
        # Get workspace/team ID and fetch all tasks
        try:
            team_id = context.resolve_id('workspace', 'current')
        except ValueError:
            print("Error: No workspace ID set. Use 'set_current workspace <team_id>' first.", file=sys.stderr)
            sys.exit(1)

        result = client.get_team_tasks(team_id, subtasks=True, include_closed=False)
        tasks = result.get('tasks', [])
        list_id = None
    else:
        # Resolve "current" to actual list ID
        try:
            list_id = context.resolve_id('list', args.list_id)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

        result = client.get_list_tasks(list_id)
        tasks = result.get('tasks', [])

    options = create_format_options(args)

    # Show available statuses (only for single list view)
    if list_id:
        colorize_val = getattr(args, 'colorize', None)
        colorize = colorize_val if colorize_val is not None else context.get_ansi_output()
        status_line = get_list_statuses(client, list_id, use_color=colorize)
        if status_line:
            print(status_line)
            print()  # Empty line for spacing

    header = args.header if hasattr(args, 'header') and args.header else None
    if show_all and not header:
        header = "All Workspace Tasks"

    output = display.hierarchy_view(tasks, options, header)

    print(output)


def register_command(subparsers, add_common_args):
    """
    Register the hierarchy command with argparse.

    Args:
        subparsers: The argparse subparsers object
        add_common_args: Function to add common formatting arguments
    """
    # Hierarchy command
    parser = subparsers.add_parser(
        'hierarchy',
        aliases=['h'],
        help='Display tasks in hierarchical view',
        description='Display tasks in hierarchical parent-child view'
    )
    parser.add_argument('list_id', nargs='?', help='ClickUp list ID (optional if --all is used)')
    parser.add_argument('--header', help='Custom header text')
    parser.add_argument('--all', dest='show_all', action='store_true',
                        help='Show all tasks from the entire workspace')
    add_common_args(parser)
    parser.set_defaults(func=hierarchy_command, preset='full')

    # List command (alias for hierarchy)
    list_parser = subparsers.add_parser(
        'list',
        aliases=['ls', 'l'],
        help='Display tasks in hierarchical view (alias for hierarchy)',
        description='Display tasks in hierarchical parent-child view'
    )
    list_parser.add_argument('list_id', nargs='?', help='ClickUp list ID (optional if --all is used)')
    list_parser.add_argument('--header', help='Custom header text')
    list_parser.add_argument('--all', dest='show_all', action='store_true',
                             help='Show all tasks from the entire workspace')
    add_common_args(list_parser)
    list_parser.set_defaults(func=hierarchy_command, preset='full')
