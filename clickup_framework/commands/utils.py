"""Utility functions for CLI commands."""

import sys
import logging
from pathlib import Path
from clickup_framework import ClickUpClient, get_context_manager
from clickup_framework.components import FormatOptions
from clickup_framework.utils.colors import colorize, TextColor, TextStyle

logger = logging.getLogger(__name__)


def get_list_statuses(client: ClickUpClient, list_id: str, use_color: bool = True) -> str:
    """
    Get and format available statuses for a list with caching.

    Args:
        client: ClickUpClient instance
        list_id: List ID
        use_color: Whether to colorize output

    Returns:
        Formatted string showing available statuses
    """
    from clickup_framework.utils.colors import status_color as get_status_color
    import sys

    try:
        context = get_context_manager()

        # Use context setting if not explicitly specified
        if use_color is None:
            use_color = context.get_ansi_output()

        # Try to get from cache first
        cached_metadata = context.get_cached_list_metadata(list_id)

        if cached_metadata:
            list_data = cached_metadata
        else:
            # Fetch from API and cache
            list_data = client.get_list(list_id)
            context.cache_list_metadata(list_id, list_data)

        statuses = list_data.get('statuses', [])

        if not statuses:
            return ""

        # Format status display
        status_parts = []
        for status in statuses:
            status_name = status.get('status', 'Unknown')

            if use_color:
                # Use our status color mapping
                color = get_status_color(status_name)
                status_parts.append(colorize(status_name, color, TextStyle.BOLD))
            else:
                status_parts.append(status_name)

        status_line = " → ".join(status_parts)

        if use_color:
            header = colorize("Available Statuses:", TextColor.BRIGHT_BLUE, TextStyle.BOLD) + f" {status_line}"
        else:
            header = f"Available Statuses: {status_line}"

        return header
    except Exception:
        # If anything fails (e.g., in tests or network issues), silently return empty string
        return ""


def create_format_options(args) -> FormatOptions:
    """Create FormatOptions from command-line arguments."""
    # Check context for ANSI output setting
    context = get_context_manager()
    default_colorize = context.get_ansi_output()

    # Use preset if specified
    if hasattr(args, 'preset') and args.preset:
        if args.preset == 'minimal':
            options = FormatOptions.minimal()
        elif args.preset == 'summary':
            options = FormatOptions.summary()
        elif args.preset == 'detailed':
            options = FormatOptions.detailed()
        elif args.preset == 'full':
            options = FormatOptions.full()
        else:
            options = FormatOptions()

        # Override colorize based on context setting
        options.colorize_output = default_colorize
        return options

    # Otherwise build from individual flags
    colorize_val = getattr(args, 'colorize', None)
    if colorize_val is None:
        colorize_val = default_colorize

    # Handle full descriptions flag
    full_descriptions = getattr(args, 'full_descriptions', False)
    show_descriptions = getattr(args, 'show_descriptions', False) or full_descriptions
    description_length = 10000 if full_descriptions else 500

    return FormatOptions(
        colorize_output=colorize_val,
        show_ids=getattr(args, 'show_ids', False),
        show_tags=getattr(args, 'show_tags', True),
        show_descriptions=show_descriptions,
        show_dates=getattr(args, 'show_dates', False),
        show_comments=getattr(args, 'show_comments', 0),
        include_completed=getattr(args, 'include_completed', False),
        show_type_emoji=getattr(args, 'show_emoji', True),
        description_length=description_length
    )


def add_common_args(subparser):
    """Add common formatting arguments to a command parser."""
    subparser.add_argument('--preset', choices=['minimal', 'summary', 'detailed', 'full'],
                         help='Use a preset format configuration')
    subparser.add_argument('--no-colorize', dest='colorize', action='store_const', const=False, default=None,
                         help='Disable color output (default: use config setting)')
    subparser.add_argument('--colorize', dest='colorize', action='store_const', const=True,
                         help='Enable color output')
    subparser.add_argument('--show-ids', action='store_true',
                         help='Show task IDs')
    subparser.add_argument('--show-tags', action='store_true', default=True,
                         help='Show task tags (default: true)')
    subparser.add_argument('--show-descriptions', action='store_true',
                         help='Show task descriptions')
    subparser.add_argument('-d', '--full-descriptions', dest='full_descriptions', action='store_true',
                         help='Show full descriptions without truncation (implies --show-descriptions)')
    subparser.add_argument('--show-dates', action='store_true',
                         help='Show task dates')
    subparser.add_argument('--show-comments', type=int, default=0, metavar='N',
                         help='Show N comments per task')
    subparser.add_argument('--include-completed', action='store_true',
                         help='Include completed tasks')
    subparser.add_argument('--no-emoji', dest='show_emoji', action='store_false',
                         help='Hide task type emojis')


def resolve_container_id(client: ClickUpClient, id_or_current: str, context=None) -> dict:
    """
    Resolve a container ID from space, folder, list, task ID, or "current" keyword.

    This function is flexible and accepts:
    - Space IDs: returns {'type': 'space', 'id': space_id, 'data': space_data}
    - Folder IDs: returns {'type': 'folder', 'id': folder_id, 'data': folder_data}
    - List IDs: returns {'type': 'list', 'id': list_id}
    - Task IDs: fetches the task and returns {'type': 'list', 'id': list_id}
    - "current": resolves from context

    Args:
        client: ClickUpClient instance
        id_or_current: Either a space, folder, list, task ID, or "current"
        context: Context manager (optional, will be fetched if not provided)

    Returns:
        Dictionary with 'type' and 'id' keys, and optionally 'data' key

    Raises:
        ValueError: If ID cannot be resolved or is invalid
    """
    from clickup_framework.exceptions import ClickUpNotFoundError, ClickUpAuthError

    if context is None:
        context = get_context_manager()

    # Handle "current" keyword
    if id_or_current.lower() == "current":
        try:
            list_id = context.resolve_id('list', 'current')
            return {'type': 'list', 'id': list_id}
        except ValueError as e:
            raise ValueError(f"No current list set. Use 'cum set list <list_id>' first or provide a space/folder/list/task ID.") from e

    # Try each container type in order: space, folder, list, task
    last_error = None
    got_auth_error = False

    # Try as space ID
    try:
        space_data = client.get_space(id_or_current)
        return {'type': 'space', 'id': id_or_current, 'data': space_data}
    except ClickUpAuthError as e:
        last_error = e
        got_auth_error = True
    except ClickUpNotFoundError as e:
        last_error = e
    except Exception as e:
        logger.debug(f"Failed to resolve '{id_or_current}' as space ID: {e}")
        if last_error is None:
            last_error = e

    # Try as folder ID
    try:
        folder_data = client.get_folder(id_or_current)
        return {'type': 'folder', 'id': id_or_current, 'data': folder_data}
    except ClickUpAuthError as e:
        last_error = e
        got_auth_error = True
    except ClickUpNotFoundError as e:
        last_error = e
    except Exception as e:
        logger.debug(f"Failed to resolve '{id_or_current}' as folder ID: {e}")
        if last_error is None:
            last_error = e

    # Try as list ID
    try:
        client.get_list(id_or_current)
        return {'type': 'list', 'id': id_or_current}
    except ClickUpAuthError as e:
        last_error = e
        got_auth_error = True
    except ClickUpNotFoundError as e:
        last_error = e
    except Exception as e:
        logger.debug(f"Failed to resolve '{id_or_current}' as list ID: {e}")
        if last_error is None:
            last_error = e

    # Try as task ID
    try:
        task = client.get_task(id_or_current)
        list_id = task.get('list', {}).get('id')
        if list_id:
            return {'type': 'list', 'id': list_id}
        else:
            raise ValueError(f"Task {id_or_current} does not have a valid list ID")
    except ClickUpAuthError as e:
        last_error = e
        got_auth_error = True
    except ClickUpNotFoundError as e:
        last_error = e
    except Exception as e:
        logger.debug(f"Failed to resolve '{id_or_current}' as task ID: {e}")
        if last_error is None:
            last_error = e

    # If we got an auth error, provide more diagnostic information
    if got_auth_error:
        error_msg = f"Cannot access ID '{id_or_current}'. "

        # Check if workspace is set
        workspace_id = None
        try:
            workspace_id = context.resolve_id('workspace', 'current')
        except ValueError:
            pass

        if not workspace_id:
            error_msg += (
                "No workspace is set in context. "
                "This could mean:\n"
                "  1. You need to set a workspace: cum set workspace <team_id>\n"
                "  2. The ID doesn't exist or is invalid\n"
                "  3. Your API token is invalid or lacks permissions\n\n"
                "To verify your API token is valid, try: cum show"
            )
        else:
            # Validate API token by checking if we can access the workspace
            token_valid = False
            try:
                client.get_workspace_hierarchy(workspace_id)
                token_valid = True
            except ClickUpAuthError:
                error_msg += (
                    "Your API token appears to be invalid or expired. "
                    "Please check your token and set it again: cum set token <your_token>"
                )
            except Exception:
                token_valid = True  # Assume valid if error is not auth-related

            if token_valid:
                error_msg += (
                    f"API token is valid, but ID '{id_or_current}' is not accessible. "
                    f"This could mean:\n"
                    f"  1. The ID doesn't exist in your workspace (team_id: {workspace_id})\n"
                    f"  2. The ID belongs to a different workspace\n"
                    f"  3. Your API token lacks permission to access this resource\n\n"
                    f"Try these commands to explore your workspace:\n"
                    f"  - cum container {workspace_id}  (view workspace structure)\n"
                    f"  - cum show                      (view current context)\n"
                    f"  - cum h <valid_id> --preset summary  (test with a known ID)"
                )

        raise ValueError(error_msg)

    # If all fail, provide a helpful error message
    error_msg = f"Invalid ID '{id_or_current}'. "
    if last_error:
        error_msg += f"Error: {str(last_error)}. "
    error_msg += (
        "Please provide a valid space, folder, list, or task ID.\n\n"
        "To set up context: cum set list <list_id>\n"
        "To view workspace: cum container <workspace_id>"
    )

    raise ValueError(error_msg)


def resolve_list_id(client: ClickUpClient, id_or_current: str, context=None) -> str:
    """
    Resolve a list ID from either a list ID, task ID, or "current" keyword.

    Note: This function is deprecated in favor of resolve_container_id() which
    also handles space and folder IDs. This is kept for backwards compatibility.

    This function is flexible and accepts:
    - List IDs: returns the list ID as-is
    - Task IDs: fetches the task and returns its list ID
    - "current": resolves from context

    Args:
        client: ClickUpClient instance
        id_or_current: Either a list ID, task ID, or "current"
        context: Context manager (optional, will be fetched if not provided)

    Returns:
        Resolved list ID

    Raises:
        ValueError: If ID cannot be resolved or is invalid
    """
    if context is None:
        context = get_context_manager()

    # Handle "current" keyword
    if id_or_current.lower() == "current":
        try:
            return context.resolve_id('list', 'current')
        except ValueError as e:
            raise ValueError(f"No current list set. Use 'cum set list <list_id>' first or provide a list/task ID.") from e

    # First, try to use it as a list ID
    try:
        # Try to fetch the list to validate it's a list ID
        client.get_list(id_or_current)
        return id_or_current
    except Exception:
        # If that fails, try to get it as a task ID
        pass

    # Try to get it as a task ID
    try:
        task = client.get_task(id_or_current)
        list_id = task.get('list', {}).get('id')
        if list_id:
            return list_id
        else:
            raise ValueError(f"Task {id_or_current} does not have a valid list ID")
    except Exception:
        # If both fail, raise an error
        raise ValueError(
            f"Invalid ID '{id_or_current}'. "
            f"Please provide a valid list ID, task ID, or use 'current' if you have a list set.\n"
            f"To set current list: cum set list <list_id>"
        )


def read_text_from_file(file_path: str) -> str:
    """
    Read text content from a file.

    Args:
        file_path: Path to the file to read

    Returns:
        File content as string

    Raises:
        SystemExit: If file cannot be read
    """
    try:
        path = Path(file_path)
        if not path.exists():
            print(f"Error: File not found: {file_path}", file=sys.stderr)
            sys.exit(1)

        if not path.is_file():
            print(f"Error: Not a file: {file_path}", file=sys.stderr)
            sys.exit(1)

        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        if not content.strip():
            print(f"Error: File is empty: {file_path}", file=sys.stderr)
            sys.exit(1)
        return content
    except UnicodeDecodeError:
        print(f"Error: File is not a valid text file: {file_path}", file=sys.stderr)
        sys.exit(1)
    except PermissionError:
        print(f"Error: Permission denied reading file: {file_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file {file_path}: {e}", file=sys.stderr)
        sys.exit(1)
