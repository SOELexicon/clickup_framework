"""Diff command for comparing files and strings."""

import sys
import os
from clickup_framework.utils.diff import diff_files, diff_strings
from clickup_framework import get_context_manager


def diff_command(args):
    """
    Compare two files or strings and display the differences.

    Args:
        args: Parsed command line arguments
    """
    # Determine if we should use color
    use_color = True

    # Check for explicit color flags
    if hasattr(args, 'no_color') and args.no_color:
        use_color = False
    elif hasattr(args, 'color') and args.color:
        use_color = True
    else:
        # Default: respect ANSI settings from context manager
        context = get_context_manager()
        use_color = context.get_ansi_output()

    # Get context lines (default: 3)
    context_lines = getattr(args, 'context', 3)

    # Validate context lines
    if context_lines < 0:
        print("Error: Context lines must be non-negative", file=sys.stderr)
        sys.exit(1)

    # Determine operation mode: file comparison or string comparison
    file_mode = args.file1 is not None and args.file2 is not None
    string_mode = args.old is not None and args.new is not None

    # Validate that exactly one mode is specified
    if file_mode and string_mode:
        print("Error: Cannot specify both file paths and --old/--new strings", file=sys.stderr)
        print("Use either: cum diff file1 file2", file=sys.stderr)
        print("        or: cum diff --old 'text1' --new 'text2'", file=sys.stderr)
        sys.exit(1)

    if not file_mode and not string_mode:
        print("Error: Must specify either file paths or --old/--new strings", file=sys.stderr)
        print("Use either: cum diff file1 file2", file=sys.stderr)
        print("        or: cum diff --old 'text1' --new 'text2'", file=sys.stderr)
        sys.exit(1)

    # Execute appropriate diff operation
    try:
        if file_mode:
            # File comparison
            result = diff_files(
                args.file1,
                args.file2,
                context_lines=context_lines,
                use_color=use_color
            )
            print(result, end='')
        else:
            # String comparison
            result = diff_strings(
                args.old,
                args.new,
                old_label=getattr(args, 'old_label', 'old'),
                new_label=getattr(args, 'new_label', 'new'),
                context_lines=context_lines,
                use_color=use_color
            )
            print(result, end='')
    except SystemExit:
        # Re-raise SystemExit from diff utilities (already handled)
        raise
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def register_command(subparsers, add_common_args=None):
    """
    Register the diff command with argparse.

    Args:
        subparsers: The subparsers object from argparse
        add_common_args: Optional function to add common arguments
    """
    parser = subparsers.add_parser(
        'diff',
        help='Compare files or strings and show differences',
        description='Display differences between two files or two strings using unified diff format'
    )

    # File comparison arguments (positional, optional)
    parser.add_argument(
        'file1',
        nargs='?',
        help='First file to compare'
    )
    parser.add_argument(
        'file2',
        nargs='?',
        help='Second file to compare'
    )

    # String comparison arguments
    parser.add_argument(
        '--old',
        help='Old text string to compare'
    )
    parser.add_argument(
        '--new',
        help='New text string to compare'
    )

    # Optional labels for string comparison
    parser.add_argument(
        '--old-label',
        default='old',
        help='Label for old text (default: "old")'
    )
    parser.add_argument(
        '--new-label',
        default='new',
        help='Label for new text (default: "new")'
    )

    # Context lines
    parser.add_argument(
        '--context',
        '-c',
        type=int,
        default=3,
        help='Number of context lines to show (default: 3)'
    )

    # Color control
    color_group = parser.add_mutually_exclusive_group()
    color_group.add_argument(
        '--color',
        action='store_true',
        help='Force colored output'
    )
    color_group.add_argument(
        '--no-color',
        action='store_true',
        help='Disable colored output'
    )

    # Set the command function
    parser.set_defaults(func=diff_command)
