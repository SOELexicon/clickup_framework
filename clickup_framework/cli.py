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
from clickup_framework import get_context_manager
from clickup_framework.utils.colors import colorize, TextColor, TextStyle
from clickup_framework.utils.animations import ANSIAnimations
from clickup_framework.cli_error_handler import handle_cli_error

# Import argcomplete for tab completion
try:
    import argcomplete
    ARGCOMPLETE_AVAILABLE = True
except ImportError:
    ARGCOMPLETE_AVAILABLE = False


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

    parser = argparse.ArgumentParser(
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
