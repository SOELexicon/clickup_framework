"""Stats command."""

from clickup_framework.commands.base_command import BaseCommand
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


class StatsCommand(BaseCommand):
    """
    Stats Command using BaseCommand.
    """

    def execute(self):
        """Execute the stats command."""
        display = DisplayManager(self.client)

        # Resolve list ID from either list ID, task ID, or "current" keyword
        list_id = self.resolve_list(self.args.list_id)

        result = self.client.get_list_tasks(list_id, include_closed=self.args.include_closed)
        tasks = result.get('tasks', [])

        # Filter by type if specified
        if self.args.type:
            tasks = [t for t in tasks if (t.get('custom_type') or 'Task') == self.args.type]
            if not tasks:
                self.print_error(f"No tasks found with type: {self.args.type}")
                return

        # Show available statuses
        # Note: stats command doesn't have colorize arg, so default to True
        status_line = get_list_statuses(self.client, list_id, use_color=True)
        if status_line:
            self.print(status_line)
            self.print()  # Empty line for spacing

        if getattr(self.args, 'by_type', False):
            # Show breakdown by type
            type_stats = get_task_type_stats(tasks)
            output = format_type_stats(type_stats)
        else:
            # Show regular summary
            output = display.summary_stats(tasks)

        self.print(output)


def stats_command(args):
    """
    Command function wrapper for backward compatibility.

    This function maintains the existing function-based API while
    using the BaseCommand class internally.
    """
    command = StatsCommand(args, command_name='stats')
    command.execute()


def register_command(subparsers, add_common_args=None):
    """Register the stats command with argparse."""
    parser = subparsers.add_parser(
        'stats',
        aliases=['st'],
        help='Display task statistics',
        description='Display statistical summary of tasks in a list',
        epilog='''Tips:
  • View statistics: cum stats <list_id>
  • Group by type: cum stats <list_id> --by-type
  • Filter by type: cum stats <list_id> --type Bug
  • Include closed: cum stats <list_id> --include-closed
  • Shows: task counts, status distribution, priority breakdown'''
    )
    parser.add_argument('list_id', help='ClickUp list ID or task ID')
    parser.add_argument('--by-type', action='store_true',
                        help='Show statistics grouped by task type')
    parser.add_argument('--type', type=str,
                        help='Filter tasks by specific type (e.g., Bug, Feature, Test)')
    parser.add_argument('--include-closed', action='store_true',
                        help='Include closed/archived tasks in statistics')
    parser.set_defaults(func=stats_command)
