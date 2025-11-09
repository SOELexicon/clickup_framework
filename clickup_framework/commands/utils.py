"""Utility functions for CLI commands."""

import sys
from pathlib import Path
from clickup_framework import ClickUpClient, get_context_manager
from clickup_framework.components import FormatOptions
from clickup_framework.utils.colors import colorize, TextColor, TextStyle


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
