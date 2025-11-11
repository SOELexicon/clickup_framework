"""
Hierarchy view command - displays tasks in parent-child hierarchy.

This module provides the `hierarchy` command (and its aliases: h, list, ls, l) which
displays ClickUp tasks in a hierarchical tree structure showing parent-child relationships.

Features:
    - Workspace-wide task listing with --all flag
    - Support for spaces, folders, lists, and individual task containers
    - Pagination support for large task sets (auto-fetches all pages)
    - Filter completed/closed tasks with --include-completed flag
    - Customizable display options (colors, tags, descriptions, etc.)
    - Visual tree structure with Unicode box-drawing characters

Examples:
    # Show all tasks in workspace (with pagination)
    cum h --all

    # Show all tasks including completed ones
    cum h --all --include-completed

    # Show tasks from a specific list
    cum h <list_id>

    # Show tasks from a space or folder
    cum h <space_id>
    cum h <folder_id>

    # Use preset format options
    cum h --all --preset summary

Aliases:
    - hierarchy: Full command name
    - h: Short alias
    - list: Alternative name
    - ls: Unix-style list
    - l: Shortest alias

Author: ClickUp Framework Team
"""

import sys
import logging
from clickup_framework import ClickUpClient, get_context_manager
from clickup_framework.components import DisplayManager
from clickup_framework.commands.utils import create_format_options, get_list_statuses, add_common_args, resolve_container_id

logger = logging.getLogger(__name__)


def hierarchy_command(args):
    """
    Display tasks in hierarchical parent-child view with full pagination support.

    This command displays ClickUp tasks in a tree structure showing parent-child
    relationships. It automatically handles pagination to fetch all tasks, regardless
    of workspace size.

    Args:
        args: argparse.Namespace containing:
            - list_id (str, optional): ClickUp space, folder, list, or task ID.
              If provided, shows tasks from that container.
            - show_all (bool): If True, shows all tasks from entire workspace.
            - include_completed (bool): If True, includes closed/completed tasks.
            - header (str, optional): Custom header text for the display.
            - colorize (bool, optional): Enable/disable color output.
            - show_ids (bool): Show task IDs.
            - show_tags (bool): Show task tags.
            - show_descriptions (bool): Show task descriptions.
            - show_dates (bool): Show task dates.
            - show_comments (int): Number of comments to show per task.
            - show_emoji (bool): Show task type emojis.
            - preset (str, optional): Preset format (minimal|summary|detailed|full).

    Behavior:
        - Fetches all pages of tasks using pagination (handles 100+ task workspaces)
        - Respects include_completed flag throughout entire call chain
        - Validates that either list_id or --all is provided (not both)
        - Displays status information for single list views
        - Uses custom header or auto-generates based on container

    Exits:
        1: If neither list_id nor --all is provided
        1: If both list_id and --all are provided
        1: If workspace is not set when using --all
        1: If container ID is invalid

    Examples:
        Show all workspace tasks (with pagination):
            >>> args = Namespace(list_id=None, show_all=True, include_completed=False)
            >>> hierarchy_command(args)

        Show tasks from a specific list:
            >>> args = Namespace(list_id='123456', show_all=False)
            >>> hierarchy_command(args)

        Show all tasks including completed:
            >>> args = Namespace(show_all=True, include_completed=True)
            >>> hierarchy_command(args)

    Notes:
        - Automatically detects container type (space/folder/list)
        - Handles API pagination transparently (fetches all pages)
        - Passes include_closed parameter through entire call chain
        - Uses DisplayManager for consistent formatting
    """
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

    ClickUp API endpoints return a maximum of 100 tasks per page. This function
    automatically iterates through all pages until last_page is True, collecting
    all tasks into a single list.

    Args:
        fetch_func (callable): Function to call for fetching data. Should accept
            a 'page' parameter and return a dict with 'tasks' and 'last_page' keys.
            Example: lambda **p: client.get_team_tasks(team_id, **p)
        **params: Additional parameters to pass to fetch_func on each call.
            Common parameters:
            - subtasks (bool): Include subtasks in results
            - include_closed (bool): Include completed/closed tasks
            - archived (bool): Include archived tasks

    Returns:
        list: All tasks from all pages combined. Returns empty list if no tasks found.

    Raises:
        Exception: Logs warning and stops pagination if any page fetch fails.
            Returns tasks fetched up to that point.

    Examples:
        Fetch all team tasks:
            >>> tasks = _fetch_all_pages(
            ...     lambda **p: client.get_team_tasks('123', **p),
            ...     subtasks=True,
            ...     include_closed=False
            ... )

        Fetch all list tasks:
            >>> tasks = _fetch_all_pages(
            ...     lambda **p: client.get_list_tasks('456', **p),
            ...     include_closed=True
            ... )

    Notes:
        - Starts with page=0 and increments until last_page=True
        - Each page typically contains up to 100 tasks
        - Gracefully handles errors by returning partial results
        - Logs warnings for pagination failures
        - Uses 'last_page' field from API response to determine completion
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
    Fetch tasks from multiple ClickUp lists with pagination support.

    Iterates through a list of ClickUp list objects and fetches all tasks from each,
    using pagination to handle large lists. Continues fetching from other lists even
    if one fails due to permissions or API errors.

    Args:
        client (ClickUpClient): Authenticated ClickUp API client instance
        lists (list): List of dictionaries containing list metadata. Each dict
            should have an 'id' key with the list ID.
            Example: [{'id': '123', 'name': 'List 1'}, {'id': '456', 'name': 'List 2'}]
        include_closed (bool, optional): If True, includes completed/closed tasks
            in results. Defaults to False (open tasks only).

    Returns:
        list: Combined list of all tasks from all lists. Tasks are returned in
            the order they were fetched (list by list). Returns empty list if
            no tasks found or all fetches fail.

    Error Handling:
        - ClickUpNotFoundError: Logged at debug level, continues with next list
        - ClickUpAuthError: Logged at debug level, continues with next list
        - Other exceptions: Logged as warnings, continues with next list

    Examples:
        Fetch from multiple lists (open tasks only):
            >>> lists = [{'id': '123'}, {'id': '456'}]
            >>> tasks = _get_tasks_from_lists(client, lists, include_closed=False)

        Fetch including completed tasks:
            >>> tasks = _get_tasks_from_lists(client, lists, include_closed=True)

    Notes:
        - Each list is fetched with full pagination support
        - Errors on individual lists don't stop processing of other lists
        - Useful for fetching tasks from spaces and folders
        - Debug/warning logs help diagnose permission issues
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
    """
    Fetch all tasks from all lists within a ClickUp space (including folders).

    A ClickUp space can contain both folders (which contain lists) and folderless
    lists directly under the space. This function fetches tasks from both locations,
    using pagination for each list.

    Args:
        client (ClickUpClient): Authenticated ClickUp API client instance
        space_data (dict): Space metadata dictionary containing:
            - id (str): Space ID
            - name (str): Space name
            - folders (list): List of folder objects, each with a 'lists' key
            - lists (list): List of folderless list objects
        include_closed (bool, optional): If True, includes completed/closed tasks.
            Defaults to False.

    Returns:
        list: All tasks from the space, including tasks from:
            - Lists within folders
            - Folderless lists directly under the space
        Returns empty list if no tasks found.

    Examples:
        >>> space_data = {
        ...     'id': 'space_123',
        ...     'folders': [{'lists': [{'id': 'list_1'}]}],
        ...     'lists': [{'id': 'list_2'}]
        ... }
        >>> tasks = _get_tasks_from_space(client, space_data, include_closed=False)

    Notes:
        - Processes folders first, then folderless lists
        - Uses _get_tasks_from_lists() internally for pagination
        - Combines results from all sources into single list
    """
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
    """
    Fetch all tasks from all lists within a ClickUp folder.

    A ClickUp folder contains multiple lists. This function fetches all tasks from
    all lists in the folder using pagination.

    Args:
        client (ClickUpClient): Authenticated ClickUp API client instance
        folder_data (dict): Folder metadata dictionary containing:
            - id (str): Folder ID
            - name (str): Folder name
            - lists (list): List of list objects with 'id' field
        include_closed (bool, optional): If True, includes completed/closed tasks.
            Defaults to False.

    Returns:
        list: All tasks from all lists in the folder. Returns empty list if
            no tasks found.

    Examples:
        >>> folder_data = {
        ...     'id': 'folder_123',
        ...     'lists': [{'id': 'list_1'}, {'id': 'list_2'}]
        ... }
        >>> tasks = _get_tasks_from_folder(client, folder_data, include_closed=True)

    Notes:
        - Simple wrapper around _get_tasks_from_lists()
        - Provides consistent interface for folder-level fetching
        - Uses full pagination support via _get_tasks_from_lists()
    """
    lists = folder_data.get('lists', [])
    return _get_tasks_from_lists(client, lists, include_closed)


def register_command(subparsers):
    """
    Register the hierarchy command and its aliases with the CLI argument parser.

    Registers five command aliases that all execute the same hierarchy_command function:
    - hierarchy: Full command name
    - h: Short alias
    - list: Alternative name
    - ls: Unix-style list
    - l: Shortest alias

    Each command accepts the same arguments for consistency.

    Args:
        subparsers: argparse subparsers object to register commands with

    Command Arguments:
        list_id (positional, optional): ClickUp space, folder, list, or task ID
        --header: Custom header text for output
        --all: Show all tasks from entire workspace
        --preset: Use preset format (minimal|summary|detailed|full)
        --colorize/--no-colorize: Enable/disable color output
        --show-ids: Show task IDs
        --show-tags: Show task tags (default: true)
        --show-descriptions: Show task descriptions
        -d, --full-descriptions: Show full descriptions without truncation
        --show-dates: Show task dates
        --show-comments N: Show N comments per task
        --include-completed: Include completed/closed tasks
        --no-emoji: Hide task type emojis

    Examples of registered commands:
        cum hierarchy --all
        cum h --all
        cum list <list_id>
        cum ls <space_id> --include-completed
        cum l --all --preset summary

    Notes:
        - All aliases use the same hierarchy_command function
        - Preset defaults to 'full' for rich output
        - Common args are added via add_common_args() utility
    """
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
