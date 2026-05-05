"""
Search command - find tasks and lists by keyword search.

This module provides the `search` command which allows users to search for
tasks and lists across the workspace using keyword matching. It renders the
hierarchy view internally and filters the output in Python, avoiding external
shell tool dependencies.

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

from argparse import Namespace
from contextlib import redirect_stdout
import io
import re

from clickup_framework.commands.base_command import BaseCommand
from clickup_framework.commands.hierarchy import hierarchy_command
from clickup_framework.utils.argparse_helpers import raw_description_formatter
from clickup_framework.commands.utils import add_common_args


# Command metadata for help generation
COMMAND_METADATA = {
    "category": "📊 View Commands",
    "commands": [
        {
            "name": "search [s]",
            "args": "<pattern> [--container ID] [--case-sensitive]",
            "description": "Search for tasks and lists by keyword with internal hierarchy filtering"
        }
    ]
}


class SearchCommand(BaseCommand):
    """
    Search Command using BaseCommand.
    """

    def _build_hierarchy_args(self) -> Namespace:
        """Build the internal hierarchy invocation args used for search."""
        return Namespace(
            list_id=self.args.container_id,
            show_all=not bool(self.args.container_id),
            header=None,
            colorize=getattr(self.args, "colorize", None),
            show_ids=True,
            show_tags=True,
            show_descriptions=False,
            full_descriptions=False,
            show_dates=False,
            show_comments=0,
            include_completed=False,
            show_closed_only=False,
            show_emoji=True,
            show_custom_fields=False,
            show_tips=False,
            preset="full",
            depth=None,
            space_id=None,
        )

    def _compile_pattern(self):
        """Compile the search pattern according to the selected flags."""
        pattern = self.args.pattern if self.args.regex else re.escape(self.args.pattern)
        flags = 0 if self.args.case_sensitive else re.IGNORECASE
        return re.compile(pattern, flags)

    def _render_hierarchy_output(self) -> str:
        """Render hierarchy output to a string for in-process filtering."""
        hierarchy_args = self._build_hierarchy_args()
        capture = io.StringIO()
        with redirect_stdout(capture):
            hierarchy_command(hierarchy_args)
        return capture.getvalue()

    def _filter_matches(self, hierarchy_output: str):
        """Filter hierarchy output down to matching lines."""
        matcher = self._compile_pattern()
        return [line for line in hierarchy_output.splitlines() if matcher.search(line)]

    def execute(self):
        """
        Search for tasks and lists matching a pattern.

        This command provides an intuitive search interface by executing
        the hierarchy command internally and filtering the rendered output.
        """
        try:
            output = self._render_hierarchy_output()
            matches = self._filter_matches(output)

            if not matches:
                use_color = self.context.get_ansi_output()

                if use_color:
                    from clickup_framework.utils.colors import colorize, TextColor
                    pattern_colored = colorize(f'"{self.args.pattern}"', TextColor.BRIGHT_YELLOW)
                    self.print(f"\n🔍 No tasks found matching {pattern_colored}\n")
                else:
                    self.print(f'\n🔍 No tasks found matching "{self.args.pattern}"\n')
                return

            # Print results with header
            use_color = self.context.get_ansi_output()
            result_count = len(matches)

            if use_color:
                from clickup_framework.utils.colors import colorize, TextColor, TextStyle
                pattern_colored = colorize(f'"{self.args.pattern}"', TextColor.BRIGHT_YELLOW, TextStyle.BOLD)
                count_colored = colorize(str(result_count), TextColor.BRIGHT_GREEN, TextStyle.BOLD)
                header = f"\n🔍 Found {count_colored} result(s) matching {pattern_colored}\n"
            else:
                header = f'\n🔍 Found {result_count} result(s) matching "{self.args.pattern}"\n'

            # Print the filtered output
            full_output = header + "\n" + "\n".join(matches)
            self.handle_output(
                data={'matches': matches, 'count': result_count, 'pattern': self.args.pattern},
                console_output=full_output
            )
        except Exception as e:
            self.error(f"Error executing search: {e}")


def search_command(args):
    """
    Command function wrapper for backward compatibility.

    This function maintains the existing function-based API while
    using the BaseCommand class internally.
    """
    command = SearchCommand(args, command_name='search')
    command.execute()


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
  - Normal usage does not require external `cum` or `grep` binaries on PATH
        """,
        formatter_class=raw_description_formatter(),
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

    add_common_args(parser)
    parser.set_defaults(func=search_command)

    return parser
