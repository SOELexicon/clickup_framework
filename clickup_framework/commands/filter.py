"""Filter view command."""

import sys
from clickup_framework import ClickUpClient, get_context_manager
from clickup_framework.components import DisplayManager
from clickup_framework.commands.utils import create_format_options, get_list_statuses, add_common_args, resolve_list_id


def filter_command(args):
    """Display filtered tasks."""
    context = get_context_manager()
    client = ClickUpClient()
    display = DisplayManager(client)

    # Resolve list ID from either list ID, task ID, or "current" keyword
    try:
        list_id = resolve_list_id(client, args.list_id, context)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Get the include_completed and show_closed_only flags
    include_completed = getattr(args, 'include_completed', False)
    show_closed_only = getattr(args, 'show_closed_only', False)

    # Determine if we need to fetch closed tasks from the API
    # We need closed tasks if either include_completed or show_closed_only is True
    include_closed = include_completed or show_closed_only

    result = client.get_list_tasks(list_id, include_closed=include_closed)
    tasks = result.get('tasks', [])
    options = create_format_options(args)

    # Show available statuses
    colorize_val = getattr(args, 'colorize', None)
    colorize = colorize_val if colorize_val is not None else context.get_ansi_output()
    status_line = get_list_statuses(client, list_id, use_color=colorize)
    if status_line:
        print(status_line)
        print()  # Empty line for spacing

    output = display.filtered_view(
        tasks,
        status=args.status if hasattr(args, 'status') else None,
        priority=args.priority if hasattr(args, 'priority') else None,
        tags=args.tags if hasattr(args, 'tags') else None,
        assignee_id=args.assignee if hasattr(args, 'assignee') else None,
        include_completed=args.include_completed if hasattr(args, 'include_completed') else False,
        options=options,
        view_mode=args.view_mode if hasattr(args, 'view_mode') else 'hierarchy'
    )

    print(output)


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
