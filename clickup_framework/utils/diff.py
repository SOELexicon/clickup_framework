"""
Diff Utilities Module

Provides functions for comparing files and strings using Python's difflib module,
with colored output support for terminal display.
"""

import sys
from pathlib import Path
from typing import List, Optional
import difflib

from clickup_framework.utils.colors import colorize, TextColor


def diff_files(
    file1_path: str,
    file2_path: str,
    context_lines: int = 3,
    use_color: bool = True
) -> str:
    """
    Compare two files and return a unified diff.

    Args:
        file1_path: Path to the first file
        file2_path: Path to the second file
        context_lines: Number of context lines to show (default: 3)
        use_color: Whether to colorize the output (default: True)

    Returns:
        Formatted unified diff string

    Raises:
        SystemExit: If files cannot be read
    """
    try:
        # Read first file
        path1 = Path(file1_path)
        if not path1.exists():
            print(f"Error: File not found: {file1_path}", file=sys.stderr)
            sys.exit(1)

        if not path1.is_file():
            print(f"Error: Not a file: {file1_path}", file=sys.stderr)
            sys.exit(1)

        with open(path1, "r", encoding="utf-8") as f:
            file1_lines = f.readlines()

        # Read second file
        path2 = Path(file2_path)
        if not path2.exists():
            print(f"Error: File not found: {file2_path}", file=sys.stderr)
            sys.exit(1)

        if not path2.is_file():
            print(f"Error: Not a file: {file2_path}", file=sys.stderr)
            sys.exit(1)

        with open(path2, "r", encoding="utf-8") as f:
            file2_lines = f.readlines()

        # Generate diff
        return format_unified_diff(
            file1_lines,
            file2_lines,
            file1_path,
            file2_path,
            context_lines=context_lines,
            use_color=use_color
        )

    except UnicodeDecodeError as e:
        print(f"Error: File is not a valid text file: {e}", file=sys.stderr)
        sys.exit(1)
    except PermissionError as e:
        print(f"Error: Permission denied reading file: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading files: {e}", file=sys.stderr)
        sys.exit(1)


def diff_strings(
    old_text: str,
    new_text: str,
    old_label: str = "old",
    new_label: str = "new",
    context_lines: int = 3,
    use_color: bool = True
) -> str:
    """
    Compare two strings and return a unified diff.

    Args:
        old_text: The original text
        new_text: The modified text
        old_label: Label for the old text (default: "old")
        new_label: Label for the new text (default: "new")
        context_lines: Number of context lines to show (default: 3)
        use_color: Whether to colorize the output (default: True)

    Returns:
        Formatted unified diff string
    """
    # Split strings into lines (preserve line endings for proper diff)
    old_lines = old_text.splitlines(keepends=True)
    new_lines = new_text.splitlines(keepends=True)

    # Ensure lines end with newline for proper diff formatting
    if old_lines and not old_lines[-1].endswith('\n'):
        old_lines[-1] += '\n'
    if new_lines and not new_lines[-1].endswith('\n'):
        new_lines[-1] += '\n'

    return format_unified_diff(
        old_lines,
        new_lines,
        old_label,
        new_label,
        context_lines=context_lines,
        use_color=use_color
    )


def format_unified_diff(
    old_lines: List[str],
    new_lines: List[str],
    old_label: str,
    new_label: str,
    context_lines: int = 3,
    use_color: bool = True
) -> str:
    """
    Format a unified diff with optional color support.

    Args:
        old_lines: Lines from the old version
        new_lines: Lines from the new version
        old_label: Label for the old version
        new_label: Label for the new version
        context_lines: Number of context lines to show (default: 3)
        use_color: Whether to colorize the output (default: True)

    Returns:
        Formatted unified diff string
    """
    # Handle empty inputs
    if not old_lines and not new_lines:
        return "No differences found (both inputs are empty)\n"

    # Generate unified diff
    diff_lines = list(difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=old_label,
        tofile=new_label,
        lineterm='',
        n=context_lines
    ))

    # If no differences, return early
    if not diff_lines:
        return "No differences found\n"

    # Format and colorize output
    result = []
    for line in diff_lines:
        if use_color:
            if line.startswith('---') or line.startswith('+++'):
                # File headers in bold
                result.append(colorize(line, style=None))
            elif line.startswith('@@'):
                # Hunk headers in cyan
                result.append(colorize(line, color=TextColor.CYAN))
            elif line.startswith('+'):
                # Additions in green
                result.append(colorize(line, color=TextColor.GREEN))
            elif line.startswith('-'):
                # Deletions in red
                result.append(colorize(line, color=TextColor.RED))
            else:
                # Context lines (no color)
                result.append(line)
        else:
            result.append(line)

    # Join with newlines and ensure final newline
    output = '\n'.join(result)
    if output and not output.endswith('\n'):
        output += '\n'

    return output


def get_diff_summary(old_text: str, new_text: str) -> dict:
    """
    Get a summary of changes between two texts.

    Args:
        old_text: The original text
        new_text: The modified text

    Returns:
        Dictionary with 'added', 'removed', and 'changed' line counts
    """
    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()

    diff = list(difflib.unified_diff(old_lines, new_lines, lineterm=''))

    added = sum(1 for line in diff if line.startswith('+') and not line.startswith('+++'))
    removed = sum(1 for line in diff if line.startswith('-') and not line.startswith('---'))

    return {
        'added': added,
        'removed': removed,
        'changed': added + removed
    }
