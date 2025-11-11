"""Hierarchy view command - displays tasks in parent-child hierarchy."""

import sys
import logging
from clickup_framework import ClickUpClient, get_context_manager
from clickup_framework.components import DisplayManager
from clickup_framework.commands.utils import create_format_options, get_list_statuses, add_common_args, resolve_container_id

logger = logging.getLogger(__name__)


def hierarchy_command(args):
    """Display tasks in hierarchical parent-child view."""
    context = get_context_manager()
    client = ClickUpClient()
    display = DisplayManager(client)

    # Check if --all flag is set
    show_all = getattr(args, 'show_all', False)

    # Get the include_completed and show_closed_only flags
    include_completed = getattr(args, 'include_completed', False)
    show_closed_only = getattr(args, 'show_closed_only', False)

    # Determine if we need to fetch closed tasks from the API
    # We need closed tasks if either include_completed or show_closed_only is True
    include_closed = include_completed or show_closed_only

    # Validate that either list_id or --all is provided
    if not show_all and not args.list_id:
        print("Error: Either provide a container ID or use --all to show all workspace tasks", file=sys.stderr)
        sys.exit(1)

    if show_all and args.list_id:
        print("Error: Cannot use both container ID and --all flag together", file=sys.stderr)
        sys.exit(1)

    if show_all:
        # Get workspace/team ID and fetch all tasks
        try:
            team_id = context.resolve_id('workspace', 'current')
        except ValueError:
            print("Error: No workspace ID set. Use 'cum set workspace <team_id>' first.", file=sys.stderr)
            sys.exit(1)

        # Fetch all pages of tasks from the workspace
        tasks = _fetch_all_pages(
            lambda **p: client.get_team_tasks(team_id, **p),
            subtasks=True,
            include_closed=include_closed
        )
        list_id = None
        container_name = None
    else:
        # Resolve container ID (space, folder, list, or task)
        try:
            container = resolve_container_id(client, args.list_id, context)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

        container_type = container['type']
        container_id = container['id']

        if container_type == 'space':
            # Fetch all tasks from all lists in the space
            space_data = container['data']
            container_name = space_data.get('name', 'Space')
            tasks = _get_tasks_from_space(client, space_data, include_closed)
            list_id = None
        elif container_type == 'folder':
            # Fetch all tasks from all lists in the folder
            folder_data = container['data']
            container_name = folder_data.get('name', 'Folder')
            tasks = _get_tasks_from_folder(client, folder_data, include_closed)
            list_id = None
        else:  # container_type == 'list'
            # Fetch all pages of tasks from the single list
            list_id = container_id
            tasks = _fetch_all_pages(
                lambda **p: client.get_list_tasks(list_id, **p),
                include_closed=include_closed
            )
            container_name = None

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
    elif container_name and not header:
        header = container_name

    output = display.hierarchy_view(tasks, options, header)

    print(output)


def _fetch_all_pages(fetch_func, **params):
    """
    Fetch all pages of results from a paginated API endpoint.

    Args:
        fetch_func: Function to call for fetching (e.g., client.get_list_tasks)
        **params: Parameters to pass to the fetch function

    Returns:
        List of all tasks from all pages
    """
    all_tasks = []
    page = 0
    last_page = False

    while not last_page:
        try:
            result = fetch_func(page=page, **params)
            tasks = result.get('tasks', [])
            all_tasks.extend(tasks)
            last_page = result.get('last_page', True)
            page += 1
        except Exception as e:
            # If pagination fails, log and break
            logger.warning(f"Pagination stopped at page {page}: {e}")
            break

    return all_tasks


def _get_tasks_from_lists(client, lists, include_closed=False):
    """
    Fetch tasks from a list of list objects.

    Args:
        client: ClickUpClient instance
        lists: List of list objects with 'id' field
        include_closed: Whether to include closed/completed tasks

    Returns:
        List of tasks from all lists
    """
    from clickup_framework.exceptions import ClickUpNotFoundError, ClickUpAuthError

    tasks = []
    for list_item in lists:
        list_id = list_item.get('id')
        if list_id:
            try:
                # Fetch all pages for this list
                list_tasks = _fetch_all_pages(
                    lambda **p: client.get_list_tasks(list_id, **p),
                    include_closed=include_closed
                )
                tasks.extend(list_tasks)
            except (ClickUpNotFoundError, ClickUpAuthError) as e:
                # Log known errors but continue with other lists
                logger.debug(f"Failed to fetch tasks from list {list_id}: {e}")
            except Exception as e:
                # Log unexpected errors but continue with other lists
                logger.warning(f"Unexpected error fetching tasks from list {list_id}: {e}")
    return tasks


def _get_tasks_from_space(client, space_data, include_closed=False):
    """Fetch all tasks from all lists within a space."""
    tasks = []

    # Get lists from folders
    folders = space_data.get('folders', [])
    for folder in folders:
        lists = folder.get('lists', [])
        tasks.extend(_get_tasks_from_lists(client, lists, include_closed))

    # Get folderless lists (lists directly under space)
    lists = space_data.get('lists', [])
    tasks.extend(_get_tasks_from_lists(client, lists, include_closed))

    return tasks


def _get_tasks_from_folder(client, folder_data, include_closed=False):
    """Fetch all tasks from all lists within a folder."""
    lists = folder_data.get('lists', [])
    return _get_tasks_from_lists(client, lists, include_closed)


def register_command(subparsers):
    """Register the hierarchy command and its aliases 'list', 'h', 'ls', 'l'."""
    # Hierarchy command
    hierarchy_parser = subparsers.add_parser('hierarchy', help='Display tasks in hierarchical view')
    hierarchy_parser.add_argument('list_id', nargs='?', help='ClickUp space, folder, list, or task ID (optional if --all is used)')
    hierarchy_parser.add_argument('--header', help='Custom header text')
    hierarchy_parser.add_argument('--all', dest='show_all', action='store_true',
                                 help='Show all tasks from the entire workspace')
    add_common_args(hierarchy_parser)
    hierarchy_parser.set_defaults(func=hierarchy_command, preset='full')

    # Short alias: h
    h_parser = subparsers.add_parser('h', help='Display tasks in hierarchical view (alias for hierarchy)')
    h_parser.add_argument('list_id', nargs='?', help='ClickUp space, folder, list, or task ID (optional if --all is used)')
    h_parser.add_argument('--header', help='Custom header text')
    h_parser.add_argument('--all', dest='show_all', action='store_true',
                         help='Show all tasks from the entire workspace')
    add_common_args(h_parser)
    h_parser.set_defaults(func=hierarchy_command, preset='full')

    # List command (alias for hierarchy)
    list_parser = subparsers.add_parser('list', help='Display tasks in hierarchical view (alias for hierarchy)')
    list_parser.add_argument('list_id', nargs='?', help='ClickUp space, folder, list, or task ID (optional if --all is used)')
    list_parser.add_argument('--header', help='Custom header text')
    list_parser.add_argument('--all', dest='show_all', action='store_true',
                            help='Show all tasks from the entire workspace')
    add_common_args(list_parser)
    list_parser.set_defaults(func=hierarchy_command, preset='full')

    # Short alias: ls
    ls_parser = subparsers.add_parser('ls', help='Display tasks in hierarchical view (alias for hierarchy)')
    ls_parser.add_argument('list_id', nargs='?', help='ClickUp space, folder, list, or task ID (optional if --all is used)')
    ls_parser.add_argument('--header', help='Custom header text')
    ls_parser.add_argument('--all', dest='show_all', action='store_true',
                          help='Show all tasks from the entire workspace')
    add_common_args(ls_parser)
    ls_parser.set_defaults(func=hierarchy_command, preset='full')

    # Short alias: l
    l_parser = subparsers.add_parser('l', help='Display tasks in hierarchical view (alias for hierarchy)')
    l_parser.add_argument('list_id', nargs='?', help='ClickUp space, folder, list, or task ID (optional if --all is used)')
    l_parser.add_argument('--header', help='Custom header text')
    l_parser.add_argument('--all', dest='show_all', action='store_true',
                         help='Show all tasks from the entire workspace')
    add_common_args(l_parser)
    l_parser.set_defaults(func=hierarchy_command, preset='full')
