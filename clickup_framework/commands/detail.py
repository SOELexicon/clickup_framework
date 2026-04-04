"""Detail view command."""

import sys
import logging
from clickup_framework import ClickUpClient, get_context_manager
from clickup_framework.components import DisplayManager
from clickup_framework.commands.base_command import BaseCommand
from clickup_framework.commands.utils import create_format_options, add_common_args
from clickup_framework.utils.argparse_helpers import raw_text_formatter

logger = logging.getLogger(__name__)


def _fetch_all_pages(fetch_func, **params):
    """
    Fetch all pages of results from a paginated API endpoint.

    Args:
        fetch_func: Function to call for fetching data
        **params: Additional parameters (subtasks, include_closed, etc.)

    Returns:
        list: All tasks from all pages combined
    """
    all_tasks = []
    page = 0

    while True:
        try:
            result = fetch_func(page=page, **params)
            tasks = result.get('tasks', [])
            all_tasks.extend(tasks)

            if result.get('last_page', True):
                break

            page += 1
        except Exception as e:
            logger.warning(f"Failed to fetch page {page}: {e}")
            break

    return all_tasks


class DetailCommand(BaseCommand):
    """Display comprehensive details of a single task with relationships."""

    def _get_context_manager(self):
        """Use module-local factories so existing tests can patch them."""
        return get_context_manager()

    def _create_client(self):
        """Use module-local factories so existing tests can patch them."""
        return ClickUpClient()

    def execute(self):
        """Execute the detail command."""
        display = DisplayManager(self.client)
        task_id = self.resolve_id('task', self.args.task_id)

        # The get_task endpoint includes the full task payload used by the detail view.
        task = self.client.get_task(task_id, include_subtasks=True)

        # If list_id not provided, extract it from the task object for relationship context.
        if self.args.list_id:
            list_id = self.resolve_id('list', self.args.list_id)
        else:
            list_data = task.get('list')
            if list_data:
                list_id = list_data.get('id') if isinstance(list_data, dict) else list_data
            else:
                list_id = None

        # ClickUp API quirk: fetch root tasks and subtasks separately, then merge.
        if list_id:
            try:
                root_tasks = _fetch_all_pages(
                    lambda **p: self.client.get_list_tasks(list_id, **p),
                    include_closed=True
                )
                subtask_list = _fetch_all_pages(
                    lambda **p: self.client.get_list_tasks(list_id, **p),
                    subtasks='true',
                    include_closed=True
                )

                task_map = {}
                for item in root_tasks + subtask_list:
                    task_map[item['id']] = item
                all_tasks = list(task_map.values())
            except Exception as e:
                print(f"Warning: Could not fetch list tasks: {e}", file=sys.stderr)
                all_tasks = None
        else:
            all_tasks = None

        output = display.detail_view(task, all_tasks, self.format_options or create_format_options(self.args))
        self.print(output)


def detail_command(args):
    """Command function wrapper for backward compatibility."""
    command = DetailCommand(args, command_name='detail')
    command.execute()


def register_command(subparsers):
    """Register the detail command with argparse."""
    parser = subparsers.add_parser(
        'detail',
        aliases=['d', 'task'],
        help='Show comprehensive task details with hierarchical view',
        formatter_class=raw_text_formatter(),
        description='''Display comprehensive details of a single task with enhanced hierarchical view.

Shows the main task with full description and a detailed tree view of all subtasks with
full descriptions, including smart indicators for dependencies, blockers, linked tasks,
assignees, due dates, and time tracking.''',
        epilog='''Usage:
  • View task details: cum detail <task_id>
  • Use shorter alias: cum d <task_id>
  • Use task alias: cum task <task_id>
  • With full context: cum d <task_id> <list_id> (shows relationship tree)
  • View current: cum d current (or cum task current)

What's Displayed:
  • Task info: status, priority, type, tags, assignees, dates
  • Full main task description
  • Hierarchical subtask tree with:
    - Full description for each subtask
    - Task types (emoji indicators)
    - Smart indicators (⏳ dependencies, 🚫 blockers, 🔗 links, 👤 assignees, 📅 due dates, ⏱️ time)
    - Visual tree connections with vertical pipes (│) linking subtasks
    - Comments: latest 2 for incomplete subtasks, count only for completed
  • All attachments with proper formatting
  • All custom fields
  • Linked tasks (type and title, no description)
  • Linked docs with tree view of page structure
  • Dependencies and blockers clearly displayed
  • Checklists, comments, time tracking

Smart Indicators (per DOCS_SMART_INDICATORS.md):
  ⏳ Dependencies (waiting on)  🚫 Blockers (blocking others)
  🔗 Linked tasks              👤 Single assignee (initials)
  👥 Multiple assignees        🔴 Overdue  📅 Due today  ⚠️ Due soon
  ⏱️ Time tracking (spent/estimate)

Tips:
  • The detail view now shows full descriptions by default (no truncation)
  • Tree structure uses vertical pipes (│) to connect subtasks visually
  • Use -p/--preset for different detail levels (minimal, summary, full)
  • Incomplete subtasks show latest 2 comments; completed show count only'''
    )
    parser.add_argument('task_id', help='ClickUp task ID or "current"')
    parser.add_argument('list_id', nargs='?', help='List ID for relationship context (optional, auto-detected if not provided)')
    add_common_args(parser)
    parser.set_defaults(func=detail_command, preset='full')
