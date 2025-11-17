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
import logging
from typing import List, NoReturn
from clickup_framework import get_context_manager, __version__
from clickup_framework.utils.colors import colorize, TextColor, TextStyle
from clickup_framework.utils.animations import ANSIAnimations
from clickup_framework.cli_error_handler import handle_cli_error
from clickup_framework.commands.utils import create_format_options

# Import command functions for backward compatibility with tests
from clickup_framework.commands.hierarchy import hierarchy_command
from clickup_framework.commands.container import container_command
from clickup_framework.commands.flat import flat_command
from clickup_framework.commands.filter import filter_command
from clickup_framework.commands.detail import detail_command
from clickup_framework.commands.stats import stats_command
from clickup_framework.commands.demo import demo_command
from clickup_framework.commands.set_current import set_current_command
from clickup_framework.commands.clear_current import clear_current_command
from clickup_framework.commands.show_current import show_current_command
from clickup_framework.commands.assigned_command import assigned_tasks_command

# Configure logger
logger = logging.getLogger(__name__)

# Import argcomplete for tab completion
try:
    import argcomplete
    ARGCOMPLETE_AVAILABLE = True
except ImportError:
    ARGCOMPLETE_AVAILABLE = False

# Constants for error detection
# Task IDs are typically 12+ characters (alphanumeric), while list IDs are often shorter numeric strings
TYPICAL_TASK_ID_MIN_LENGTH = 10


def _format_task_create_examples(task_or_list_id: str, use_color: bool) -> List[str]:
    """
    Format usage examples for task_create command based on the provided ID.

    This helper function generates contextual examples showing the correct syntax
    for creating tasks, customized based on whether the ID appears to be a task ID
    or list ID based on its length.

    Args:
        task_or_list_id: The ID that was incorrectly provided as first argument
        use_color: Whether to use ANSI color codes in the output

    Returns:
        List of formatted example strings with correct task_create usage

    Examples:
        >>> examples = _format_task_create_examples("901517349362", use_color=False)
        >>> len(examples)
        3
        >>> "cum tc" in examples[0]
        True

    Notes:
        - IDs longer than TYPICAL_TASK_ID_MIN_LENGTH are treated as task IDs
        - Shorter IDs are treated as list IDs
        - Examples include parent task creation and list-based creation
    """
    examples = []

    # If ID looks like it might be a parent task ID (longer IDs)
    if len(task_or_list_id) > TYPICAL_TASK_ID_MIN_LENGTH:
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

    # Show list-based creation examples
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

    return examples


def _print_task_create_error_header(task_or_list_id: str, unrecognized_args: str, use_color: bool) -> None:
    """
    Print the error header for task_create syntax errors.

    Args:
        task_or_list_id: The ID that was incorrectly provided as first argument
        unrecognized_args: The arguments that couldn't be parsed
        use_color: Whether to use ANSI color codes in the output

    Notes:
        - Outputs to stderr
        - Includes a separator line for visual clarity
    """
    if use_color:
        error_header = colorize("Error: Invalid task_create syntax", TextColor.BRIGHT_RED, TextStyle.BOLD)
        print(f"\n{error_header}", file=sys.stderr)
        print(colorize("─" * 60, TextColor.BRIGHT_BLACK), file=sys.stderr)
    else:
        print("\nError: Invalid task_create syntax", file=sys.stderr)
        print("─" * 60, file=sys.stderr)

    print(f"\nYou provided: cum tc {task_or_list_id} {unrecognized_args}...", file=sys.stderr)
    print("\nThe task NAME must come first, not the task/list ID.", file=sys.stderr)


def _print_task_create_key_points(use_color: bool) -> None:
    """
    Print key points about task_create command usage.

    Args:
        use_color: Whether to use ANSI color codes in the output

    Notes:
        - Outputs to stderr
        - Highlights important syntax rules
        - Provides quick reference for correct usage
    """
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


def _print_task_create_help_footer(use_color: bool) -> None:
    """
    Print footer with help command suggestion.

    Args:
        use_color: Whether to use ANSI color codes in the output

    Notes:
        - Outputs to stderr
        - Directs users to --help for full documentation
    """
    if use_color:
        help_text = colorize('For more help:', TextColor.BRIGHT_WHITE)
        help_cmd = colorize('cum tc --help', TextColor.BRIGHT_GREEN)
        print(f"\n{help_text}", file=sys.stderr)
        print(f"  {help_cmd}", file=sys.stderr)
    else:
        print("\nFor more help:", file=sys.stderr)
        print("  cum tc --help", file=sys.stderr)


class ImprovedArgumentParser(argparse.ArgumentParser):
    """
    Custom ArgumentParser with enhanced error messages for common CLI mistakes.

    This parser extends argparse.ArgumentParser to provide contextual, user-friendly
    error messages when users make common mistakes, particularly when arguments are
    provided in the wrong order. Currently specialized for task_create command errors.

    The parser detects when users incorrectly place IDs before required positional
    arguments and provides:
    - Clear explanation of what went wrong
    - Multiple correct usage examples
    - Highlighted key points about command structure
    - Reference to help documentation

    Examples:
        >>> parser = ImprovedArgumentParser(description="My CLI")
        >>> # When user runs: cum tc 901517349362 "Task Name"
        >>> # Parser will detect ID-first error and show helpful message

    Notes:
        - Currently handles task_create (tc) command errors
        - Respects user's ANSI color preferences from context
        - Logs error detection for debugging
        - Exits with code 2 on detected syntax errors
        - Falls back to standard argparse error handling for other errors

    See Also:
        - argparse.ArgumentParser: Base class documentation
        - _format_task_create_examples: Helper for generating examples
    """

    def error(self, message: str) -> NoReturn:
        """
        Override error method to provide contextual, helpful error messages.

        This method intercepts argparse errors and checks if they match known
        error patterns (e.g., incorrect argument order in task_create). When
        a known pattern is detected, it provides a detailed, helpful error
        message with examples and then exits. Otherwise, it falls back to
        the standard argparse error handling.

        Args:
            message: The error message from argparse

        Exits:
            - Code 2: When a recognized error pattern is detected and handled
            - Other: Via super().error() for unrecognized errors

        Examples:
            >>> # Internally called by argparse when parsing fails
            >>> # User command: cum tc 901517349362 "Task Name"
            >>> # Triggers: parser.error("unrecognized arguments: Task Name")
            >>> # Result: Displays helpful error with correct syntax

        Notes:
            - Logs at debug level when custom error handling is triggered
            - Analyzes sys.argv to understand user's original command
            - Only handles errors for commands: ['task_create', 'tc']
            - Checks for numeric or alphanumeric first argument to detect ID-before-name error
        """
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

                    # Check if first argument (after command) looks like an ID
                    # IDs can be numeric (list IDs) or alphanumeric (task IDs like "86c6hv10c")
                    first_arg = argv[1]
                    is_likely_id = (
                        first_arg.isdigit()  # Numeric list ID
                        or (first_arg.isalnum() and len(first_arg) >= 8)  # Alphanumeric task ID
                        or first_arg.startswith('"') is False  # Not quoted (task names should be quoted)
                    )

                    if is_likely_id and len(argv) >= 2:
                        task_or_list_id = first_arg

                        logger.debug(
                            f"Detected task_create syntax error: ID '{task_or_list_id}' provided before task name"
                        )

                        # Get color preference from context
                        context = get_context_manager()
                        use_color = context.get_ansi_output()

                        # Build and display helpful error message
                        _print_task_create_error_header(task_or_list_id, unrecognized_args, use_color)

                        # Show usage header
                        if use_color:
                            usage_header = colorize('Correct usage:', TextColor.BRIGHT_GREEN, TextStyle.BOLD)
                            print(f"\n{usage_header}", file=sys.stderr)
                        else:
                            print("\nCorrect usage:", file=sys.stderr)

                        # Format and display examples
                        examples = _format_task_create_examples(task_or_list_id, use_color)
                        for example in examples:
                            print(example, file=sys.stderr)

                        # Display key points
                        _print_task_create_key_points(use_color)

                        # Display help footer
                        _print_task_create_help_footer(use_color)

                        print("", file=sys.stderr)

                        logger.debug("Exiting with code 2 after displaying custom error message")
                        sys.exit(2)

        # Fall back to improved error handling for other errors
        logger.debug(f"Using improved error handling for: {message}")
        self._print_improved_error(message)

    def _print_improved_error(self, message: str) -> NoReturn:
        """
        Print an improved error message instead of the massive argparse usage dump.

        Args:
            message: The error message from argparse

        Exits:
            Code 2: Always exits after displaying error
        """
        # Get the command that was run
        argv = sys.argv[1:]
        command = argv[0] if argv else None

        # Get color preference from context
        try:
            context = get_context_manager()
            use_color = context.get_ansi_output()
        except:
            use_color = True

        # Print error header
        if use_color:
            error_header = colorize("Error", TextColor.BRIGHT_RED, TextStyle.BOLD)
            print(f"\n{error_header}: {message}", file=sys.stderr)
            print(colorize("─" * 60, TextColor.BRIGHT_BLACK), file=sys.stderr)
        else:
            print(f"\nError: {message}", file=sys.stderr)
            print("─" * 60, file=sys.stderr)

        # Show what the user typed
        if use_color:
            you_ran = colorize("You ran:", TextColor.BRIGHT_WHITE)
            cmd_display = colorize(' '.join(sys.argv), TextColor.BRIGHT_YELLOW)
        else:
            you_ran = "You ran:"
            cmd_display = ' '.join(sys.argv)
        print(f"\n{you_ran} {cmd_display}", file=sys.stderr)

        # Print helpful tips
        tips = []
        if command:
            if use_color:
                help_cmd = colorize(f'cum {command} --help', TextColor.BRIGHT_GREEN)
                tips.append(f"See command help: {help_cmd}")
            else:
                tips.append(f"See command help: cum {command} --help")

        # Add general tips
        if use_color:
            all_cmds = colorize('cum', TextColor.BRIGHT_GREEN)
            general_help = colorize('cum -h', TextColor.BRIGHT_GREEN)
            tips.append(f"List all commands: {all_cmds}")
            tips.append(f"General help: {general_help}")
        else:
            tips.append("List all commands: cum")
            tips.append("General help: cum -h")

        # Print tips section
        if tips:
            if use_color:
                tips_header = colorize("\n💡 Tips:", TextColor.BRIGHT_CYAN, TextStyle.BOLD)
                print(tips_header, file=sys.stderr)
            else:
                print("\nTips:", file=sys.stderr)

            for tip in tips:
                if use_color:
                    bullet = colorize("  •", TextColor.BRIGHT_CYAN)
                    print(f"{bullet} {tip}", file=sys.stderr)
                else:
                    print(f"  • {tip}", file=sys.stderr)

        print("", file=sys.stderr)
        sys.exit(2)


def show_command_tree():
    """Display available commands in a tree view using auto-discovered metadata."""
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

    # Collect metadata from command modules (auto-discovery)
    from clickup_framework.commands import collect_command_metadata
    commands = collect_command_metadata()

    # Fallback to hardcoded commands if no metadata found
    if not commands:
        commands = _get_fallback_commands()

    # Display commands and examples
    _display_commands(commands, use_color)
    _display_examples_and_footer(use_color)


def _get_fallback_commands():
    """Return fallback hardcoded commands if metadata collection fails."""
    return {
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
            ("task_create [tc]", "<name> [--list|--parent] <id> [OPTIONS]", "Create new task (priority: 1-4 or urgent/high/normal/low)"),
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
        "☑️  Checklist Management": [
            ("checklist [chk]", "create <task_id> <name>", "Create a new checklist on a task"),
            ("checklist [chk]", "delete <checklist_id> [--force]", "Delete a checklist and all items"),
            ("checklist [chk]", "update <checklist_id> [--name|--position]", "Update checklist properties"),
            ("checklist [chk]", "list <task_id> [--show-ids]", "List all checklists on a task"),
            ("checklist [chk]", "item-add <checklist_id> <name> [--assignee]", "Add item to checklist"),
            ("checklist [chk]", "item-update <checklist_id> <item_id> [OPTIONS]", "Update checklist item"),
            ("checklist [chk]", "item-delete <checklist_id> <item_id>", "Delete checklist item"),
            ("checklist [chk]", "template list", "List available checklist templates"),
            ("checklist [chk]", "template show <name>", "Show template details"),
            ("checklist [chk]", "template apply <task_id> <name>", "Apply template to task"),
            ("checklist [chk]", "clone <source_task> <target_task>", "Clone checklists between tasks"),
        ],
        "🏷️  Custom Fields": [
            ("custom-field [cf]", "set <task_id> <field> <value>", "Set custom field value on task"),
            ("custom-field [cf]", "get <task_id> <field>", "Get custom field value from task"),
            ("custom-field [cf]", "list --task|--list|--space|--workspace <id>", "List custom fields at hierarchy level"),
            ("custom-field [cf]", "remove <task_id> <field>", "Remove custom field value from task"),
        ],
        "🤖 Parent Task Automation": [
            ("parent_auto_update [pau]", "status", "Show automation configuration"),
            ("parent_auto_update [pau]", "enable", "Enable parent task auto-updates"),
            ("parent_auto_update [pau]", "disable", "Disable parent task auto-updates"),
            ("parent_auto_update [pau]", "config <key> <value>", "Update configuration value"),
            ("parent_auto_update [pau]", "add-trigger <status>", "Add status to trigger list"),
            ("parent_auto_update [pau]", "remove-trigger <status>", "Remove status from trigger list"),
            ("parent_auto_update [pau]", "list-triggers", "List all trigger statuses"),
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
        "📦 Export/Dump": [
            ("dump", "list <list_id> [--format FORMAT] [-o DIR]", "Dump list hierarchy to markdown/json/console"),
            ("dump", "task <task_id> [--format FORMAT] [-o DIR]", "Dump task and subtasks to markdown/json/console"),
            ("dump", "doc <workspace_id> <doc_id> [--format FORMAT] [-o DIR]", "Dump doc to markdown/json/console"),
        ],
        "🏗️  Workspace Hierarchy": [
            ("space [sp, spc]", "create <team_id> <name> [OPTIONS]", "Create new space in workspace"),
            ("space [sp, spc]", "update <space_id> [--name|--color|--private]", "Update space properties"),
            ("space [sp, spc]", "delete <space_id> [--force]", "Delete space and all contents"),
            ("space [sp, spc]", "get <space_id>", "Get space details"),
            ("space [sp, spc]", "list <team_id> [--archived]", "List all spaces in workspace"),
            ("folder [fld, fd]", "create <space_id> <name>", "Create new folder in space"),
            ("folder [fld, fd]", "update <folder_id> [--name]", "Update folder properties"),
            ("folder [fld, fd]", "delete <folder_id> [--force]", "Delete folder and all contents"),
            ("folder [fld, fd]", "get <folder_id>", "Get folder details"),
            ("list-mgmt [lm]", "create <folder_id> <name> [OPTIONS]", "Create new list in folder"),
            ("list-mgmt [lm]", "update <list_id> [--name|--content|--priority]", "Update list properties"),
            ("list-mgmt [lm]", "delete <list_id> [--force]", "Delete list and all tasks"),
            ("list-mgmt [lm]", "get <list_id>", "Get list details"),
        ],
        "🔄 Git Workflow": [
            ("overflow", "<message> [--task ID] [OPTIONS]", "Automated Git + ClickUp workflow (stage, commit, push, sync)"),
            ("pull", "", "Execute git pull --rebase"),
            ("suck", "", "Pull all Git repositories in project folder recursively"),
            ("reauthor", "[--force-push]", "Rewrite git history to change author to current git user"),
            ("stash", "[push|pop|list|apply|drop|clear|...] [args]", "Wrapper for git stash operations"),
            ("horde", "[push|pop|list|apply|drop|clear|...] [args]", "Execute git stash operations on all repositories recursively"),
        ],
        "🛠️  Utility Commands": [
            ("diff", "<file1> <file2> | --old TEXT --new TEXT [OPTIONS]", "Compare two files or strings and show unified diff"),
        ],
        "🎨 Configuration": [
            ("ansi", "<enable|disable|status>", "Enable/disable ANSI color output"),
            ("update cum", "", "Update cum tool from git and reinstall"),
            ("update version", "[VERSION] [--major|--minor|--patch]", "Bump project version and create git tag"),
            ("jizz", "[-dry|--dry-run]", "Humorous auto-deploy workflow (stash → pull → tag → push → update)"),
            ("command_sync", "[--list-id ID] [--dry-run]", "Sync CLI command information to ClickUp tasks"),
        ],
    }


def _display_commands(commands, use_color):
    """Display the commands dictionary in tree format."""
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


def _display_examples_and_footer(use_color):
    """Display examples and help footer."""
    # Print footer with examples
    if use_color:
        print(colorize("Quick Examples:", TextColor.BRIGHT_WHITE, TextStyle.BOLD))
    else:
        print("Quick Examples:")

    examples = [
        ("cum ls 901517404278", "Show tasks in hierarchy view"),
        ("cum a", "Show your assigned tasks"),
        ("cum tc \"New Task\" --list current", "Create a task in current list"),
        ("cum dump list current -o ./backup", "Export list to markdown files"),
        ("cum sp create current \"New Space\"", "Create a space in current workspace"),
        ("cum fld create current \"New Folder\"", "Create a folder in current space"),
        ("cum lm create current \"New List\"", "Create a list in current folder"),
        ("cum chk list current", "List checklists on current task"),
        ("cum cf set current \"Priority\" \"High\"", "Set custom field value"),
        ("cum overflow \"Fix bug\" --status \"in progress\"", "Git commit + update ClickUp task"),
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
        help_text = colorize("For detailed help:", TextColor.BRIGHT_WHITE)
        general_help = colorize("cum -h", TextColor.BRIGHT_GREEN)
        or_text = colorize(" or ", TextColor.BRIGHT_BLACK)
        cmd_help = colorize("cum <command> --help", TextColor.BRIGHT_GREEN)
    else:
        help_text = "For detailed help:"
        general_help = "cum -h"
        or_text = " or "
        cmd_help = "cum <command> --help"
    print(f"{help_text} {general_help}{or_text}{cmd_help}")


def main():
    """Main CLI entry point."""
    # Configure stdout and stderr to use UTF-8 encoding on Windows
    # This prevents UnicodeEncodeError when using Unicode characters (✓, ├─, └─, │, etc.)
    import io

    if hasattr(sys.stdout, 'reconfigure'):
        # Python 3.7+: Use reconfigure method
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    elif hasattr(sys.stdout, 'buffer'):
        # Fallback for older Python versions (only if buffer exists)
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    parser = ImprovedArgumentParser(
        description='ClickUp Framework CLI - Beautiful hierarchical task displays',
        formatter_class=argparse.RawDescriptionHelpFormatter,
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
