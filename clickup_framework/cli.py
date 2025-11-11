#!/usr/bin/env python3
"""
ClickUp Framework CLI

Command-line interface for ClickUp Framework display components.
Uses a modular plugin-based command system where commands are automatically
discovered from the commands/ directory.

Usage:
    cum <command> [arguments]
    python -m clickup_framework.cli <command> [arguments]

Examples:
    cum list <list_id>
    cum hierarchy --all
    cum detail <task_id> <list_id>
    cum assigned
"""

import argparse
import sys
import os
import re
from clickup_framework import get_context_manager, __version__
from clickup_framework.utils.colors import colorize, TextColor, TextStyle
from clickup_framework.utils.animations import ANSIAnimations
from clickup_framework.cli_error_handler import handle_cli_error

# Import argcomplete for tab completion
try:
    import argcomplete
    ARGCOMPLETE_AVAILABLE = True
except ImportError:
    ARGCOMPLETE_AVAILABLE = False


class ImprovedArgumentParser(argparse.ArgumentParser):
    """Custom ArgumentParser with better error messages for common mistakes."""

    def error(self, message):
        """Override error method to provide more helpful messages."""
        # Get the original command line args for analysis
        argv = sys.argv[1:]

        # Detect task_create specific errors
        if len(argv) >= 2 and argv[0] in ['task_create', 'tc']:
            # Check if "unrecognized arguments" error occurred
            if 'unrecognized arguments' in message:
                # Extract the problematic arguments
                match = re.search(r'unrecognized arguments?: (.+)', message)
                if match:
                    unrecognized_args = match.group(1)

                    # Check if first argument (after command) looks like an ID (all numeric)
                    if len(argv) >= 2 and argv[1].isdigit():
                        task_or_list_id = argv[1]

                        # Build helpful error message
                        context = get_context_manager()
                        use_color = context.get_ansi_output()

                        if use_color:
                            error_header = colorize("Error: Invalid task_create syntax", TextColor.BRIGHT_RED, TextStyle.BOLD)
                            print(f"\n{error_header}", file=sys.stderr)
                            print(colorize("─" * 60, TextColor.BRIGHT_BLACK), file=sys.stderr)
                        else:
                            print("\nError: Invalid task_create syntax", file=sys.stderr)
                            print("─" * 60, file=sys.stderr)

                        print(f"\nYou provided: cum tc {task_or_list_id} {unrecognized_args}...", file=sys.stderr)
                        print("\nThe task NAME must come first, not the task/list ID.", file=sys.stderr)

                        if use_color:
                            print(f"\n{colorize('Correct usage:', TextColor.BRIGHT_GREEN, TextStyle.BOLD)}", file=sys.stderr)
                        else:
                            print("\nCorrect usage:", file=sys.stderr)

                        # Show examples based on what they might be trying to do
                        examples = []

                        # If ID looks like it might be a parent task ID
                        if len(task_or_list_id) > 10:  # Typical task IDs are longer
                            if use_color:
                                comment = colorize('# Create a subtask under parent:', TextColor.BRIGHT_BLACK)
                                task_name = colorize('"Task Name"', TextColor.BRIGHT_YELLOW)
                                parent_flag = colorize('--parent', TextColor.BRIGHT_CYAN)
                                desc_flag = colorize('--description', TextColor.BRIGHT_CYAN)
                                desc_value = colorize('"Description"', TextColor.BRIGHT_YELLOW)
                                examples.append(
                                    f"  {comment}\n"
                                    f"  cum tc {task_name} {parent_flag} {task_or_list_id} {desc_flag} {desc_value}"
                                )
                            else:
                                examples.append(
                                    f"  # Create a subtask under parent:\n"
                                    f'  cum tc "Task Name" --parent {task_or_list_id} --description "Description"'
                                )

                        # Show list-based creation example
                        if use_color:
                            comment1 = colorize('# Create task in a list:', TextColor.BRIGHT_BLACK)
                            task_name1 = colorize('"Task Name"', TextColor.BRIGHT_YELLOW)
                            list_flag = colorize('--list', TextColor.BRIGHT_CYAN)
                            desc_flag1 = colorize('--description', TextColor.BRIGHT_CYAN)
                            desc_value1 = colorize('"Description"', TextColor.BRIGHT_YELLOW)
                            examples.append(
                                f"  {comment1}\n"
                                f"  cum tc {task_name1} {list_flag} {task_or_list_id} {desc_flag1} {desc_value1}"
                            )

                            comment2 = colorize('# Create task in current list:', TextColor.BRIGHT_BLACK)
                            task_name2 = colorize('"Task Name"', TextColor.BRIGHT_YELLOW)
                            list_current = colorize('--list current', TextColor.BRIGHT_CYAN)
                            desc_flag2 = colorize('--description', TextColor.BRIGHT_CYAN)
                            desc_value2 = colorize('"Description"', TextColor.BRIGHT_YELLOW)
                            examples.append(
                                f"  {comment2}\n"
                                f"  cum tc {task_name2} {list_current} {desc_flag2} {desc_value2}"
                            )
                        else:
                            examples.append(
                                f"  # Create task in a list:\n"
                                f'  cum tc "Task Name" --list {task_or_list_id} --description "Description"'
                            )
                            examples.append(
                                f"  # Create task in current list:\n"
                                f'  cum tc "Task Name" --list current --description "Description"'
                            )

                        for example in examples:
                            print(example, file=sys.stderr)

                        if use_color:
                            key_header = colorize('Key points:', TextColor.BRIGHT_WHITE, TextStyle.BOLD)
                            pos_arg = colorize('positional argument', TextColor.BRIGHT_YELLOW)
                            parent_example = colorize('--parent <task_id>', TextColor.BRIGHT_CYAN)
                            list_example = colorize('--list <list_id>', TextColor.BRIGHT_CYAN)
                            quote_example = colorize('"Like this"', TextColor.BRIGHT_YELLOW)
                            print(f"\n{key_header}", file=sys.stderr)
                            print(f"  • Task name is a {pos_arg} (comes first)", file=sys.stderr)
                            print(f"  • Use {parent_example} to create a subtask", file=sys.stderr)
                            print(f"  • Use {list_example} to specify the list", file=sys.stderr)
                            print(f"  • Always quote task names with spaces: {quote_example}", file=sys.stderr)
                        else:
                            print("\nKey points:", file=sys.stderr)
                            print("  • Task name is a positional argument (comes first)", file=sys.stderr)
                            print("  • Use --parent <task_id> to create a subtask", file=sys.stderr)
                            print("  • Use --list <list_id> to specify the list", file=sys.stderr)
                            print('  • Always quote task names with spaces: "Like this"', file=sys.stderr)

                        if use_color:
                            print(f"\n{colorize('For more help:', TextColor.BRIGHT_WHITE)}", file=sys.stderr)
                            print(f"  {colorize('cum tc --help', TextColor.BRIGHT_GREEN)}", file=sys.stderr)
                        else:
                            print("\nFor more help:", file=sys.stderr)
                            print("  cum tc --help", file=sys.stderr)

                        print("", file=sys.stderr)
                        sys.exit(2)

        # Fall back to default error handling
        super().error(message)


def show_command_tree():
    """Display available commands in a tree view."""
    import time
    context = get_context_manager()
    use_color = context.get_ansi_output()

    # Print header with animation
    if use_color:
        # Animated rainbow gradient header
        header = ANSIAnimations.gradient_text("ClickUp Framework CLI - Available Commands", ANSIAnimations.GRADIENT_RAINBOW)
        print(header)
        print()

        # Animated separator
        separator = ANSIAnimations.gradient_text("─" * 60, ANSIAnimations.GRADIENT_RAINBOW)
        print(separator)
        print()
        time.sleep(0.05)
    else:
        print("ClickUp Framework CLI - Available Commands")
        print("─" * 60)
        print()

    commands = {
        "📊 View Commands": [
            ("hierarchy [h]", "<list_id|--all> [options]", "Display tasks in hierarchical parent-child view (default: full preset)"),
            ("list [ls, l]", "<list_id|--all> [options]", "Display tasks in hierarchical view (alias for hierarchy)"),
            ("clist [c]", "<list_id> [options]", "Display tasks by container hierarchy (Space → Folder → List)"),
            ("flat [f]", "<list_id> [options]", "Display all tasks in flat list format"),
            ("filter [fil]", "<list_id> [filter_options]", "Display filtered tasks by status/priority/tags/assignee"),
            ("detail [d]", "<task_id> [list_id]", "Show comprehensive details for a single task"),
            ("stats [st]", "<list_id>", "Display aggregate statistics for tasks in a list"),
            ("demo", "[--mode MODE] [options]", "View demo output with sample data (no API required)"),
            ("assigned [a]", "[--user-id ID] [--team-id ID]", "Show tasks assigned to user, sorted by difficulty"),
        ],
        "🎯 Context Management": [
            ("set_current [set]", "<type> <id>", "Set current task/list/workspace/assignee"),
            ("show_current [show]", "", "Display current context with animated box"),
            ("clear_current [clear]", "[type]", "Clear one or all context resources"),
        ],
        "✅ Task Management": [
            ("task_create [tc]", "<list_id> <name> [OPTIONS]", "Create new task (priority: 1-4 or urgent/high/normal/low)"),
            ("task_update [tu]", "<task_id> [OPTIONS]", "Update task name/description/status/priority/tags"),
            ("task_delete [td]", "<task_id> [--force]", "Delete task with confirmation prompt"),
            ("task_assign [ta]", "<task_id> <user_id> [...]", "Assign one or more users to task"),
            ("task_unassign [tua]", "<task_id> <user_id> [...]", "Remove assignees from task"),
            ("task_set_status [tss]", "<task_id> [...] <status>", "Set task status with subtask validation"),
            ("task_set_priority [tsp]", "<task_id> <priority>", "Set task priority (1-4 or urgent/high/normal/low)"),
            ("task_set_tags [tst]", "<task_id> [--add|--remove|--set]", "Manage task tags"),
            ("task_add_dependency [tad]", "<task_id> [--waiting-on|--blocking] <task_id>", "Add task dependency relationship"),
            ("task_remove_dependency [trd]", "<task_id> [--waiting-on|--blocking] <task_id>", "Remove task dependency relationship"),
            ("task_add_link [tal]", "<task_id> <linked_task_id>", "Link two tasks together"),
            ("task_remove_link [trl]", "<task_id> <linked_task_id>", "Remove link between two tasks"),
        ],
        "💬 Comment Management": [
            ("comment_add [ca]", "<task_id> <text>", "Add a comment to a task"),
            ("comment_list [cl]", "<task_id> [--limit N]", "List comments on a task"),
            ("comment_update [cu]", "<comment_id> <text>", "Update an existing comment"),
            ("comment_delete [cd]", "<comment_id> [--force]", "Delete a comment"),
        ],
        "📄 Docs Management": [
            ("dlist [dl]", "<workspace_id>", "List all docs in a workspace"),
            ("doc_get [dg]", "<workspace_id> <doc_id> [--preview]", "Get doc and display pages"),
            ("doc_create [dc]", "<workspace_id> <name> [--pages ...]", "Create new doc with optional pages"),
            ("doc_update [du]", "<workspace_id> <doc_id> <page_id> [OPTIONS]", "Update a page in a doc"),
            ("doc_export [de]", "<workspace_id> [--doc-id ID] [--output-dir DIR] [--nested]", "Export docs to markdown files"),
            ("doc_import [di]", "<workspace_id> <input_dir> [--doc-name NAME] [--nested]", "Import markdown files to create docs"),
            ("page_list [pl]", "<workspace_id> <doc_id>", "List all pages in a doc"),
            ("page_create [pc]", "<workspace_id> <doc_id> --name NAME [--content TEXT]", "Create a new page in a doc"),
            ("page_update [pu]", "<workspace_id> <doc_id> <page_id> [--name NAME] [--content TEXT]", "Update a page in a doc"),
        ],
        "🎨 Configuration": [
            ("ansi", "<enable|disable|status>", "Enable/disable ANSI color output"),
            ("update cum", "", "Update cum tool from git and reinstall"),
        ],
    }

    for category, cmds in commands.items():
        # Print category
        if use_color:
            print(colorize(category, TextColor.BRIGHT_CYAN, TextStyle.BOLD))
        else:
            print(category)

        # Print commands in this category
        for i, (cmd, args, desc) in enumerate(cmds):
            is_last = i == len(cmds) - 1
            prefix = "└─ " if is_last else "├─ "

            if use_color:
                cmd_colored = colorize(cmd, TextColor.BRIGHT_GREEN, TextStyle.BOLD)
                args_colored = colorize(args, TextColor.BRIGHT_YELLOW) if args else ""
                desc_colored = colorize(desc, TextColor.BRIGHT_BLACK)
            else:
                cmd_colored = cmd
                args_colored = args
                desc_colored = desc

            cmd_line = f"{prefix}{cmd_colored}"
            if args_colored:
                cmd_line += f" {args_colored}"
            print(cmd_line)

            # Print description indented
            indent = "   " if is_last else "│  "
            print(f"{indent}{desc_colored}")

        print()  # Blank line between categories

    # Print footer with examples
    if use_color:
        print(colorize("Quick Examples:", TextColor.BRIGHT_WHITE, TextStyle.BOLD))
    else:
        print("Quick Examples:")

    examples = [
        ("cum ls 901517404278", "Show tasks in hierarchy view"),
        ("cum a", "Show your assigned tasks"),
        ("cum tc current \"New Task\"", "Create a task in current list"),
        ("cum set assignee 68483025", "Set default assignee"),
        ("cum demo --mode hierarchy", "Try demo mode (no API needed)"),
    ]

    for cmd, desc in examples:
        if use_color:
            cmd_colored = colorize(cmd, TextColor.BRIGHT_GREEN)
            desc_colored = colorize(f"  # {desc}", TextColor.BRIGHT_BLACK)
        else:
            cmd_colored = cmd
            desc_colored = f"  # {desc}"
        print(f"  {cmd_colored}{desc_colored}")

    print()
    if use_color:
        help_text = colorize("For detailed help on any command:", TextColor.BRIGHT_WHITE)
        example = colorize("cum <command> --help", TextColor.BRIGHT_GREEN)
    else:
        help_text = "For detailed help on any command:"
        example = "cum <command> --help"
    print(f"{help_text} {example}")


def main():
    """Main CLI entry point."""
    # Configure stdout and stderr to use UTF-8 encoding on Windows
    # This prevents UnicodeEncodeError when using Unicode characters (✓, ├─, └─, │, etc.)
    import io

    if hasattr(sys.stdout, 'reconfigure'):
        # Python 3.7+: Use reconfigure method
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    else:
        # Fallback for older Python versions
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    parser = ImprovedArgumentParser(
        description='ClickUp Framework CLI - Beautiful hierarchical task displays',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,  # Disable default help to use custom tree view
        epilog="""
Examples:
  # Show hierarchy view
  cum list <list_id>
  cum hierarchy <list_id>

  # Show all workspace tasks
  cum list --all
  cum hierarchy --all

  # Show container view
  cum clist <list_id>

  # Show task details
  cum detail <task_id> <list_id>

  # Filter tasks
  cum filter <list_id> --status "in progress"

  # Show with custom options
  cum list <list_id> --show-ids --show-descriptions

  # Use preset formats
  cum list <list_id> --preset detailed

  # Demo mode (no API required)
  cum demo --mode hierarchy
        """
    )

    # Add version flag
    parser.add_argument(
        '--version', '-v',
        action='version',
        version=f'ClickUp Framework CLI (cum) version {__version__}'
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Automatically discover and register all commands from the commands/ directory
    from clickup_framework.commands import register_all_commands
    register_all_commands(subparsers)

    # Enable tab completion if argcomplete is available
    if ARGCOMPLETE_AVAILABLE:
        argcomplete.autocomplete(parser)

    # Parse arguments
    args = parser.parse_args()

    # Show help if no command specified
    if not args.command:
        show_command_tree()
        sys.exit(0)

    # Execute command
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        # Use centralized error handler for beautiful error messages
        if os.getenv('DEBUG'):
            raise
        handle_cli_error(e)


if __name__ == '__main__':
    main()
