"""Diff command for comparing files and strings."""

from clickup_framework.commands.base_command import BaseCommand
from clickup_framework.utils.diff import diff_files, diff_strings


class DiffCommand(BaseCommand):
    """
    Diff Command using BaseCommand.
    """

    def execute(self):
        """
        Compare two files or strings and display the differences.
        """
        # Determine if we should use color
        use_color = True

        # Check for explicit color flags
        if hasattr(self.args, 'no_color') and self.args.no_color:
            use_color = False
        elif hasattr(self.args, 'color') and self.args.color:
            use_color = True
        else:
            # Default: respect ANSI settings from context manager
            use_color = self.context.get_ansi_output()

        # Get context lines (default: 3)
        context_lines = getattr(self.args, 'context', 3)

        # Validate context lines
        if context_lines < 0:
            self.error("Context lines must be non-negative")

        # Determine operation mode: file comparison or string comparison
        file_mode = self.args.file1 is not None and self.args.file2 is not None
        string_mode = self.args.old is not None and self.args.new is not None

        # Validate that exactly one mode is specified
        if file_mode and string_mode:
            self.error("Cannot specify both file paths and --old/--new strings\n" +
                      "Use either: cum diff file1 file2\n" +
                      "        or: cum diff --old 'text1' --new 'text2'")

        if not file_mode and not string_mode:
            self.error("Must specify either file paths or --old/--new strings\n" +
                      "Use either: cum diff file1 file2\n" +
                      "        or: cum diff --old 'text1' --new 'text2'")

        # Execute appropriate diff operation
        try:
            if file_mode:
                # File comparison
                result = diff_files(
                    self.args.file1,
                    self.args.file2,
                    context_lines=context_lines,
                    use_color=use_color
                )
                self.print(result, end='')
            else:
                # String comparison
                result = diff_strings(
                    self.args.old,
                    self.args.new,
                    old_label=getattr(self.args, 'old_label', 'old'),
                    new_label=getattr(self.args, 'new_label', 'new'),
                    context_lines=context_lines,
                    use_color=use_color
                )
                self.print(result, end='')
        except SystemExit:
            # Re-raise SystemExit from diff utilities (already handled)
            raise
        except Exception as e:
            self.error(str(e))


def diff_command(args):
    """
    Command function wrapper for backward compatibility.

    This function maintains the existing function-based API while
    using the BaseCommand class internally.
    """
    command = DiffCommand(args, command_name='diff')
    command.execute()


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
