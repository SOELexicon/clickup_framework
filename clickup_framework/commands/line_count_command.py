"""
Line count command for analyzing source code metrics.

This module provides the main line-count command that analyzes source code
line counts recursively and generates HTML reports with summary statistics.

Variables:    COMMAND_METADATA
Functions:    line_count_command, register_command
"""

import sys
import logging
from pathlib import Path
from typing import Optional
from clickup_framework.commands.base_command import BaseCommand
from clickup_framework.commands.utils import add_common_args
from clickup_framework.commands.line_count_helpers import (
    LineCounter,
    ConsoleFormatter,
    HTMLReportGenerator
)

logger = logging.getLogger(__name__)


COMMAND_METADATA = {
    "category": "🛠️  Utility Commands",
    "commands": [
        {
            "name": "line-count [loc, lines]",
            "args": ("[<path>] [--max-depth N] [--language LANG] [--no-html] [--no-console]"
                     " [--output-file PATH] [--limit N]"),
            "description": ("Analyze source code line counts recursively and generate"
                            " HTML report with summary statistics")
        }
    ]
}


class LineCountCommand(BaseCommand):
    """
    Analyze source code line counts with recursive directory traversal.

    Purpose:    Provide detailed line-of-code analysis with support for
                language filtering, depth limiting, and HTML report generation
    Usage:      cum line-count [path] [--options]
    Version:    0.1.0
    Changes:    [v0.1.0] Initial: Command registration and help integration
    """

    def _make_paths_relative(self, loc_data: dict, root_path: Path) -> dict:
        """
        Convert absolute file paths to relative paths from root.

        Args:
            loc_data: Dictionary with absolute file paths as keys
            root_path: Root path to compute relative paths from

        Returns:
            Dictionary with relative paths as keys
        """
        relative_data = {}
        for file_path, info in loc_data.items():
            try:
                rel_path = Path(file_path).relative_to(root_path)
                relative_data[str(rel_path)] = info
            except ValueError:
                # Path doesn't start with root_path, keep original
                relative_data[file_path] = info
        return relative_data

    def execute(self) -> None:
        """
        Execute the line count command.

        Resolves path, creates LineCounter with specified filters, counts files,
        formats output for console and/or HTML report generation.
        """
        # Resolve path - use provided path or current directory
        path_str: str = getattr(self.args, 'path', '.')
        path: Path = Path(path_str).resolve()

        if not path.exists():
            print(f"Error: Path does not exist: {path}", file=sys.stderr)
            sys.exit(1)

        if not path.is_dir():
            print(f"Error: Path is not a directory: {path}", file=sys.stderr)
            sys.exit(1)

        # Create LineCounter with configuration
        max_depth: Optional[int] = getattr(self.args, 'max_depth', None)
        language_filter: Optional[str] = getattr(self.args, 'language', None)

        counter: LineCounter = LineCounter(
            max_depth=max_depth,
            language_filter=language_filter
        )

        # Count files in the directory
        try:
            results: dict = counter.count_files(str(path))
        except Exception as e:
            print(f"Error counting files: {e}", file=sys.stderr)
            logger.exception("Failed to count files")
            sys.exit(1)

        # Convert to relative paths for display
        relative_results: dict = self._make_paths_relative(results, path)

        # Generate console output unless disabled
        no_console: bool = getattr(self.args, 'no_console', False)
        if not no_console:
            limit: int = getattr(self.args, 'limit', 20)
            no_color: bool = getattr(self.args, 'no_color', False)

            formatter: ConsoleFormatter = ConsoleFormatter()

            # Print summary stats
            summary_output: str = formatter.format_summary_stats(relative_results, use_color=not no_color)
            print(summary_output)
            print()

            # Print top files table
            top_files_output: str = formatter.format_top_files(
                relative_results,
                limit=limit,
                use_color=not no_color
            )
            print(top_files_output)

        # Generate HTML report unless disabled
        no_html: bool = getattr(self.args, 'no_html', False)
        if not no_html:
            try:
                output_file: Optional[str] = getattr(self.args, 'output_file', None)
                output_dir: Optional[Path] = None

                if output_file:
                    output_dir = Path(output_file).parent if Path(output_file).parent != Path(
                        output_file) else Path(output_file)
                else:
                    output_dir = Path.cwd()

                html_generator: HTMLReportGenerator = HTMLReportGenerator()
                report_path: Path = html_generator.generate_report(
                    relative_results,
                    output_path=output_dir,
                    project_name=path.name
                )

                if not no_console:
                    print(f"\nHTML report generated: {report_path}")
                else:
                    # Show report path if console output was suppressed
                    print(f"HTML report generated: {report_path}")
            except Exception as e:
                print(f"Error generating HTML report: {e}", file=sys.stderr)
                logger.exception("Failed to generate HTML report")
                # Don't exit on HTML generation failure


def line_count_command(args) -> None:
    """
    Command function wrapper for backward compatibility.

    Purpose:    Maintain existing function-based API while using BaseCommand
    Usage:      Called by argparse set_defaults(func=...)
    Version:    0.1.0
    Changes:    [v0.1.0] Initial: Wrapper for LineCountCommand
    """
    command: LineCountCommand = LineCountCommand(args, command_name='line-count')
    command.execute()


def register_command(subparsers) -> None:
    """
    Register the line-count command with argparse.

    Purpose:    Set up argparse parser with all arguments and help text
    Usage:      Called by discover_and_register_commands in cli.py
    Version:    0.1.0
    Changes:    [v0.1.0] Initial: Full argument configuration

    Args:
        subparsers: argparse subparsers object for command registration
    """
    parser = subparsers.add_parser(
        'line-count',
        aliases=['loc', 'lines'],
        help='Analyze source code line counts and generate reports',
        description=(
            'Recursively analyze source code line counts with language detection '
            'and comprehensive reporting.\n\n'
            'Supports filtering by language, limiting recursion depth, and generating both '
            'console output and HTML reports with summary statistics.'
        )
    )

    parser.add_argument(
        'path',
        nargs='?',
        default='.',
        help='Directory path to analyze (default: current directory)'
    )

    parser.add_argument(
        '--max-depth',
        type=int,
        default=None,
        help='Maximum recursion depth (default: unlimited)'
    )

    parser.add_argument(
        '--language',
        dest='language',
        type=str,
        default=None,
        help='Filter by language (e.g., "py" for Python, "js" for JavaScript)'
    )

    parser.add_argument(
        '--no-html',
        action='store_true',
        help='Skip HTML report generation'
    )

    parser.add_argument(
        '--no-console',
        action='store_true',
        help='Skip console output (useful with --output-file)'
    )

    parser.add_argument(
        '--output-file',
        type=str,
        default=None,
        help='Custom path for HTML report output'
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=20,
        help='Number of top files to display in console output (default: 20)'
    )

    parser.add_argument(
        '--no-color',
        action='store_true',
        help='Disable colored console output'
    )

    add_common_args(parser)
    parser.set_defaults(func=line_count_command)
