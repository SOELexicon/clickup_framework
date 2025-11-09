"""Stats command."""

import sys
from clickup_framework import ClickUpClient, get_context_manager
from clickup_framework.components import DisplayManager
from clickup_framework.commands.utils import get_list_statuses


def get_task_type_emoji(task_type):
    """Get emoji for task type."""
    emojis = {
        'Bug': '🐛',
        'Feature': '🚀',
        'Test': '🧪',
        'Test Result': '📊',
        'Action Run': '⚙️',
        'Documentation': '📚',
        'Refactor': '♻️',
        'Enhancement': '✨',
        'Chore': '🧹',
        'Security': '🛡️',
        'Merge': '🔀',
        'Task': '📝',
        'Commit': '💾'
    }
    return emojis.get(task_type, '📝')


def get_task_type_stats(tasks):
    """Generate statistics grouped by task type."""
    type_stats = {}

    for task in tasks:
        task_type = task.get('custom_type') or 'Task'
        status = task.get('status', {}).get('status', 'unknown').lower()

        if task_type not in type_stats:
            type_stats[task_type] = {
                'total': 0,
                'open': 0,
                'in_progress': 0,
                'complete': 0,
                'failed': 0,
                'other': 0
            }

        type_stats[task_type]['total'] += 1

        # Categorize by status
        if status in ['open', 'to do', 'todo', 'backlog']:
            type_stats[task_type]['open'] += 1
        elif status in ['in progress', 'in review', 'testing']:
            type_stats[task_type]['in_progress'] += 1
        elif status in ['complete', 'closed', 'done', 'passed']:
            type_stats[task_type]['complete'] += 1
        elif status in ['failed', 'blocked']:
            type_stats[task_type]['failed'] += 1
        else:
            type_stats[task_type]['other'] += 1

    return type_stats


def format_type_stats(type_stats):
    """Format task type statistics for display."""
    if not type_stats:
        return "No tasks found."

    # Sort by total count descending
    sorted_types = sorted(type_stats.items(), key=lambda x: x[1]['total'], reverse=True)

    output = "Task Statistics by Type:\n"
    output += "=" * 80 + "\n\n"

    # Header
    output += f"{'Type':<25} {'Total':<8} {'Open':<8} {'Active':<8} {'Done':<8} {'Failed':<8}\n"
    output += "-" * 80 + "\n"

    # Rows for each type
    total_all = 0
    total_open = 0
    total_in_progress = 0
    total_complete = 0
    total_failed = 0

    for task_type, stats in sorted_types:
        emoji = get_task_type_emoji(task_type)
        type_label = f"{emoji} {task_type}"

        output += f"{type_label:<25} "
        output += f"{stats['total']:<8} "
        output += f"{stats['open']:<8} "
        output += f"{stats['in_progress']:<8} "
        output += f"{stats['complete']:<8} "
        output += f"{stats['failed']:<8}\n"

        total_all += stats['total']
        total_open += stats['open']
        total_in_progress += stats['in_progress']
        total_complete += stats['complete']
        total_failed += stats['failed']

    # Summary row
    output += "-" * 80 + "\n"
    output += f"{'TOTAL':<25} "
    output += f"{total_all:<8} "
    output += f"{total_open:<8} "
    output += f"{total_in_progress:<8} "
    output += f"{total_complete:<8} "
    output += f"{total_failed:<8}\n"

    output += "\n"

    # Completion rate
    if total_all > 0:
        completion_rate = (total_complete / total_all) * 100
        output += f"Completion Rate: {completion_rate:.1f}%\n"
        if total_failed > 0:
            failure_rate = (total_failed / total_all) * 100
            output += f"Failure Rate: {failure_rate:.1f}%\n"

    return output


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

    result = client.get_list_tasks(list_id, include_closed=args.include_closed)
    tasks = result.get('tasks', [])

    # Filter by type if specified
    if args.type:
        tasks = [t for t in tasks if (t.get('custom_type') or 'Task') == args.type]
        if not tasks:
            print(f"No tasks found with type: {args.type}", file=sys.stderr)
            sys.exit(0)

    # Show available statuses
    # Note: stats command doesn't have colorize arg, so default to True
    status_line = get_list_statuses(client, list_id, use_color=True)
    if status_line:
        print(status_line)
        print()  # Empty line for spacing

    if args.by_type:
        # Show breakdown by type
        type_stats = get_task_type_stats(tasks)
        output = format_type_stats(type_stats)
    else:
        # Show regular summary
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
    parser.add_argument('--by-type', action='store_true',
                        help='Show statistics grouped by task type')
    parser.add_argument('--type', type=str,
                        help='Filter tasks by specific type (e.g., Bug, Feature, Test)')
    parser.add_argument('--include-closed', action='store_true',
                        help='Include closed/archived tasks in statistics')
    parser.set_defaults(func=stats_command)
