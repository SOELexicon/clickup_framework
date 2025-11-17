"""
Search command - find tasks and lists by keyword search.

This module provides the `search` command which allows users to search for
tasks and lists across the workspace using keyword matching. It wraps the
hierarchy command with grep-style pattern matching.

Features:
    - Workspace-wide search with intuitive syntax
    - Case-insensitive search by default
    - Regex pattern support
    - Simple and familiar interface

Examples:
    # Search for tasks containing "bug"
    cum search "bug"

    # Search with regex pattern
    cum search "bug.*fix"

    # Search in specific container
    cum search "feature" --container <list_id>

Aliases:
    - search: Full command name
    - s: Short alias

Author: ClickUp Framework Team
"""

import sys
import re
import subprocess
from typing import Optional
from clickup_framework import ClickUpClient, get_context_manager
from clickup_framework.components import DisplayManager
from clickup_framework.commands.utils import resolve_container_id


# Command metadata for help generation
COMMAND_METADATA = {
    "category": "📊 View Commands",
    "commands": [
        {
            "name": "search [s]",
            "args": "<pattern> [--container ID] [--case-sensitive]",
            "description": "Search for tasks and lists by keyword (wraps hierarchy + grep)"
        }
    ]
}


def search_command(args):
    """
    Search for tasks and lists matching a pattern.

    This command provides an intuitive search interface by executing
    `cum hierarchy` and filtering output with grep.

    Args:
        args: argparse.Namespace containing:
            - pattern (str): Search pattern (can be regex)
            - container_id (str, optional): Limit search to specific container
            - case_sensitive (bool): If True, search is case-sensitive

    Returns:
        None: Outputs search results to stdout

    Examples:
        >>> # Search all tasks for "bug"
        >>> args = argparse.Namespace(pattern="bug", container_id=None,
        ...                           case_sensitive=False)
        >>> search_command(args)

    Notes:
        - Executes hierarchy command and filters output
        - Uses grep for simple and reliable filtering
        - Case-insensitive by default for better user experience
    """
    import os

    # Build the hierarchy command
    hierarchy_cmd = ["cum", "h"]

    if args.container_id:
        hierarchy_cmd.append(args.container_id)
    else:
        hierarchy_cmd.append("--all")

    # Add some useful display options
    hierarchy_cmd.extend(["--show-ids", "--show-tags"])

    # Build grep command
    grep_flags = ["-i"] if not args.case_sensitive else []
    grep_cmd = ["grep"] + grep_flags + [args.pattern]

    # Execute command pipeline
    try:
        # Run hierarchy | grep
        hierarchy_proc = subprocess.Popen(
            hierarchy_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        grep_proc = subprocess.Popen(
            grep_cmd,
            stdin=hierarchy_proc.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Allow hierarchy_proc to receive SIGPIPE if grep_proc exits
        hierarchy_proc.stdout.close()

        # Get output
        output, grep_err = grep_proc.communicate()
        hierarchy_err = hierarchy_proc.stderr.read() if hierarchy_proc.stderr else ""

        # Check for errors
        if hierarchy_proc.returncode not in [0, None] and hierarchy_err:
            print(hierarchy_err, file=sys.stderr)
            sys.exit(hierarchy_proc.returncode)

        # Check if grep found anything
        if grep_proc.returncode == 1:
            # grep returns 1 when no matches found
            context = get_context_manager()
            use_color = context.get_ansi_output()

            if use_color:
                from clickup_framework.utils.colors import colorize, TextColor
                pattern_colored = colorize(f'"{args.pattern}"', TextColor.BRIGHT_YELLOW)
                print(f"\n🔍 No tasks found matching {pattern_colored}\n", file=sys.stderr)
            else:
                print(f'\n🔍 No tasks found matching "{args.pattern}"\n', file=sys.stderr)
            return
        elif grep_proc.returncode not in [0, None]:
            # grep error (not just no matches)
            if grep_err:
                print(grep_err, file=sys.stderr)
            sys.exit(grep_proc.returncode)

        # Print results with header
        context = get_context_manager()
        use_color = context.get_ansi_output()

        if use_color:
            from clickup_framework.utils.colors import colorize, TextColor, TextStyle
            pattern_colored = colorize(f'"{args.pattern}"', TextColor.BRIGHT_YELLOW, TextStyle.BOLD)
            result_count = len([line for line in output.split('\n') if line.strip() and not line.startswith('Available')])
            count_colored = colorize(str(result_count), TextColor.BRIGHT_GREEN, TextStyle.BOLD)
            print(f"\n🔍 Found {count_colored} result(s) matching {pattern_colored}\n")
        else:
            result_count = len([line for line in output.split('\n') if line.strip() and not line.startswith('Available')])
            print(f'\n🔍 Found {result_count} result(s) matching "{args.pattern}"\n')

        # Print the filtered output
        print(output)

    except FileNotFoundError as e:
        print(f"❌ Error: Required command not found: {e.filename}", file=sys.stderr)
        print("Make sure 'cum' and 'grep' are in your PATH", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error executing search: {e}", file=sys.stderr)
        sys.exit(1)


def register_command(subparsers):
    """
    Register the search command with the CLI argument parser.

    Args:
        subparsers: The subparsers object from argparse

    Returns:
        The configured parser for this command
    """
    parser = subparsers.add_parser(
        'search',
        aliases=['s'],
        help='Search for tasks and lists by keyword or regex pattern',
        description="""
Search for tasks and lists across the workspace using keyword or regex matching.

This command provides a simple, intuitive way to find tasks without remembering
the exact hierarchy or container IDs. It searches task names, descriptions, tags,
and IDs.

Examples:
  # Search for tasks about bugs
  cum search "bug"
  cum s "bug"  # Short alias

  # Search with regex
  cum search "bug.*fix"

  # Case-sensitive search
  cum search "BUG" --case-sensitive

  # Search in specific list
  cum search "feature" --container <list_id>

Tips:
  - Searches are case-insensitive by default
  - Pattern matching uses regex (escape special chars if needed)
  - Use quotes around patterns with spaces
  - Results show full task hierarchy for context
        """,
        formatter_class=lambda prog: __import__('argparse').RawDescriptionHelpFormatter(
            prog, max_help_position=40, width=80
        )
    )

    parser.add_argument(
        'pattern',
        help='Search pattern (regex supported)'
    )

    parser.add_argument(
        '--container',
        dest='container_id',
        metavar='ID',
        help='Limit search to specific container (list, folder, space)'
    )

    parser.add_argument(
        '--case-sensitive',
        action='store_true',
        help='Make search case-sensitive (default: case-insensitive)'
    )

    parser.add_argument(
        '--regex',
        action='store_true',
        default=True,
        help='Treat pattern as regex (default: True)'
    )

    parser.add_argument(
        '--no-regex',
        dest='regex',
        action='store_false',
        help='Treat pattern as literal string (escape regex)'
    )

    parser.set_defaults(func=search_command)

    return parser
