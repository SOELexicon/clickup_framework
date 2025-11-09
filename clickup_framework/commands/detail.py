"""Detail view command."""

import sys
from clickup_framework import ClickUpClient, get_context_manager
from clickup_framework.components import DisplayManager
from clickup_framework.commands.utils import create_format_options, add_common_args


def detail_command(args):
    """Display comprehensive details of a single task with relationships."""
    context = get_context_manager()
    client = ClickUpClient()
    display = DisplayManager(client)

    # Resolve "current" to actual task ID
    try:
        task_id = context.resolve_id('task', args.task_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Get the specific task
    task = client.get_task(task_id)

    # Get all tasks from the list for relationship context
    if args.list_id:
        try:
            list_id = context.resolve_id('list', args.list_id)
            result = client.get_list_tasks(list_id)
            all_tasks = result.get('tasks', [])
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        all_tasks = None

    options = create_format_options(args)

    output = display.detail_view(task, all_tasks, options)

    print(output)


def register_command(subparsers):
    """Register the detail command with argparse."""
    parser = subparsers.add_parser(
        'detail',
        aliases=['d'],
        help='Show comprehensive task details',
        description='Display comprehensive details of a single task with relationships'
    )
    parser.add_argument('task_id', help='ClickUp task ID')
    parser.add_argument('list_id', nargs='?', help='List ID for relationship context (optional)')
    add_common_args(parser)
    parser.set_defaults(func=detail_command, preset='full')
