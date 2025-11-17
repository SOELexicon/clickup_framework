"""Detail view command."""

import sys
import logging
from clickup_framework import ClickUpClient, get_context_manager
from clickup_framework.components import DisplayManager
from clickup_framework.commands.utils import create_format_options, add_common_args

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

    # Get the specific task with all related data
    # The get_task endpoint includes: status, priority, tags, assignees, dates,
    # checklists, attachments, custom fields, dependencies, linked tasks, and more
    task = client.get_task(task_id, include_subtasks=True)

    # Get all tasks from the list for comprehensive relationship context
    # This provides full details for subtasks, siblings, and related tasks
    # If list_id not provided, extract it from the task
    if args.list_id:
        try:
            list_id = context.resolve_id('list', args.list_id)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Extract list ID from the task object
        list_data = task.get('list')
        if list_data:
            list_id = list_data.get('id') if isinstance(list_data, dict) else list_data
        else:
            list_id = None

    # Fetch all tasks from the list if we have a list ID
    # This ensures we have full subtask details for hierarchical display
    # ClickUp API quirk: Need to fetch root tasks and subtasks separately, then merge
    if list_id:
        try:
            # Fetch root tasks (without subtasks parameter)
            root_tasks = _fetch_all_pages(
                lambda **p: client.get_list_tasks(list_id, **p),
                include_closed=True
            )

            # Fetch subtasks (with subtasks='true' parameter)
            subtask_list = _fetch_all_pages(
                lambda **p: client.get_list_tasks(list_id, **p),
                subtasks='true',
                include_closed=True
            )

            # Merge both lists and deduplicate by task ID
            task_map = {}
            for t in root_tasks + subtask_list:
                task_map[t['id']] = t
            all_tasks = list(task_map.values())

        except Exception as e:
            # If we can't fetch list tasks, just show task without relationships
            print(f"Warning: Could not fetch list tasks: {e}", file=sys.stderr)
            all_tasks = None
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
        help='Show comprehensive task details with hierarchical view',
        description='''Display comprehensive details of a single task with enhanced hierarchical view.

Shows the main task (first 2 lines of description) with a detailed tree view of all
subtasks (first 9 lines each), including smart indicators for dependencies, blockers,
linked tasks, assignees, due dates, and time tracking.''',
        epilog='''Usage:
  • View task details: cum d <task_id>
  • With full context: cum d <task_id> <list_id> (shows relationship tree)
  • Use alias: cum d current (view current task)

What's Displayed:
  • Task info: status, priority, type, tags, assignees, dates
  • Main task description (first 2 lines with "..." if truncated)
  • Hierarchical subtask tree with:
    - First 9 lines of each subtask description
    - Task types (emoji indicators)
    - Smart indicators (⏳ dependencies, 🚫 blockers, 🔗 links, 👤 assignees, 📅 due dates, ⏱️ time)
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
  • The detail view automatically limits the main task description to 2 lines
  • Each subtask shows up to 9 lines of description
  • Use -p/--preset for different detail levels (minimal, summary, full)
  • Incomplete subtasks show latest 2 comments; completed show count only'''
    )
    parser.add_argument('task_id', help='ClickUp task ID or "current"')
    parser.add_argument('list_id', nargs='?', help='List ID for relationship context (optional, auto-detected if not provided)')
    add_common_args(parser)
    parser.set_defaults(func=detail_command, preset='full')
