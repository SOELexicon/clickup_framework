#!/usr/bin/env python3
"""
Command sync - Auto-update CLI command tasks with command information.

This command discovers all cum commands, creates/updates ClickUp tasks for each command
in the CLI Commands list, and populates custom fields with command information.
"""

import argparse
import re
import sys
import subprocess
from typing import Dict, List, Tuple, Optional
from clickup_framework import ClickUpClient, get_context_manager
from clickup_framework.clickup_constants import (
    CLICKUP_FRAMEWORK_LIST_IDS,
    CLI_COMMAND_CATEGORIES,
    CLI_COMMAND_TASK_IDS,
)
from clickup_framework.exceptions import ClickUpAPIError
from clickup_framework.utils.colors import colorize, TextColor, TextStyle
from clickup_framework.utils.animations import ANSIAnimations

# Default values
DEFAULT_CLI_COMMANDS_LIST_ID = CLICKUP_FRAMEWORK_LIST_IDS["cli-commands"]
DEFAULT_TEST_TASK_ID = "86c6hvba1"

# Custom field IDs
CUSTOM_FIELDS = {
    "command_purpose": "f5f43ae3-bacc-4fc9-970b-139701800b7e",
    "command_syntax": "552f93c3-549b-4848-9773-7825906041cb",
    "required_parameters": "075b7846-9e9c-4b3d-9a83-e1882e0f270c",
    "success_criteria": "84a51a9d-3250-42f7-8ed1-c4a5d998fbba",
    "command_output": "e32fdcce-a5f8-4a1e-9d5d-199fca1ee6df"
}

COMMAND_CATEGORIES = CLI_COMMAND_CATEGORIES
COMMAND_TASK_IDS = CLI_COMMAND_TASK_IDS


def _build_registered_command_parser() -> argparse.ArgumentParser:
    """Build the current CLI parser so help output matches the real entrypoint."""
    from clickup_framework.cli import build_parser

    return build_parser()


def _get_registered_command_parsers() -> Dict[str, argparse.ArgumentParser]:
    """Return the top-level command parsers keyed by their registered names."""
    parser = _build_registered_command_parser()

    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return {
                choice.dest: action._name_parser_map[choice.dest]
                for choice in action._choices_actions
            }

    return {}


def _resolve_registered_command_name(
    command: str,
    command_parsers: Dict[str, argparse.ArgumentParser],
) -> Optional[str]:
    """Match a command key against the registered parser names."""
    candidates = (
        command,
        command.replace("_", "-"),
        command.replace("-", "_"),
    )

    for candidate in candidates:
        if candidate in command_parsers:
            return candidate

    return None


def _resolve_registry_key(command: str, registry: Dict[str, str]) -> Optional[str]:
    """Resolve a command against a dict keyed by command name."""
    for candidate in (
        command,
        command.replace("_", "-"),
        command.replace("-", "_"),
    ):
        if candidate in registry:
            return candidate
    return None


def _cli_module_invocation(*command_parts: str) -> List[str]:
    """Run CLI subprocesses through the current Python interpreter."""
    return [sys.executable, "-m", "clickup_framework", *command_parts]


def _get_all_list_tasks(client: ClickUpClient, list_id: str) -> List[Dict]:
    """Fetch every task from a list, following ClickUp pagination."""
    tasks = []
    page = 0

    while True:
        result = client.get_list_tasks(list_id, include_closed=True, page=page)
        tasks.extend(result.get("tasks", []))
        if result.get("last_page", True):
            break
        page += 1

    return tasks


def get_command_help(
    command: str,
    command_parsers: Optional[Dict[str, argparse.ArgumentParser]] = None,
) -> Tuple[str, str]:
    """
    Get help output for a command.

    Args:
        command: Command name to get help for

    Returns:
        Tuple of (help_output, error_output)
    """
    command_parsers = command_parsers or _get_registered_command_parsers()
    registered_name = _resolve_registered_command_name(command, command_parsers)

    if not registered_name:
        return "", f"Command '{command}' is not currently registered with the CLI parser"

    try:
        return command_parsers[registered_name].format_help(), ""
    except Exception as e:
        return "", f"Error building help output: {str(e)}"


def execute_command_on_test_task(command: str, test_task_id: str) -> Tuple[str, str]:
    """
    Execute a command on the test task to capture output.

    Args:
        command: Command to execute
        test_task_id: Task ID to use for testing

    Returns:
        Tuple of (stdout, stderr)
    """
    # Commands that work with task IDs
    task_commands = [
        "detail", "comment_add", "comment_list", "task_update", "task_delete",
        "task_assign", "task_unassign", "task_set_status", "task_set_priority",
        "task_set_tags", "task_add_dependency", "task_remove_dependency",
        "task_add_link", "task_remove_link"
    ]

    # Commands that don't need parameters or can't be tested
    no_param_commands = ["assigned", "assigned_tasks", "show_current"]

    # Commands that need list IDs
    list_commands = [
        "hierarchy", "flat", "filter", "stats", "clist", "container", "list"
    ]

    # Commands that can't be safely tested
    unsafe_commands = [
        "suck", "pull", "reauthor", "stash", "horde", "overflow",
        "task_create", "task_delete", "update"
    ]

    try:
        if command in unsafe_commands:
            return "N/A - Command cannot be safely executed in test mode", ""
        elif command in no_param_commands:
            result = subprocess.run(
                _cli_module_invocation(command),
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=30
            )
            return result.stdout, result.stderr
        elif command in task_commands:
            # For commands that work with task IDs
            if command == "detail":
                cmd = _cli_module_invocation(command, test_task_id)
            else:
                # Most other task commands would modify the task, so skip execution
                return "N/A - Command would modify task (execution skipped)", ""

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=30
            )
            return result.stdout, result.stderr
        else:
            return "N/A - Command execution not implemented for this command type", ""
    except subprocess.TimeoutExpired:
        return "", "Command execution timed out"
    except Exception as e:
        return "", f"Error executing command: {str(e)}"


def parse_help_output(help_output: str) -> Dict[str, str]:
    """
    Parse help output to extract command information.

    Args:
        help_output: Raw help output from command

    Returns:
        Dictionary with parsed fields:
        - purpose: What the command does
        - syntax: Command syntax
        - required_params: Required parameters
        - success_criteria: What indicates success
    """
    lines = help_output.split('\n')

    # Extract description (usually after "usage:" or at the beginning)
    purpose = ""
    syntax = ""
    required_params = []

    # Find usage line
    for i, line in enumerate(lines):
        if 'usage:' in line.lower():
            syntax = lines[i].replace('usage:', '').strip()
            # Check next few lines for description
            for j in range(i + 1, min(i + 10, len(lines))):
                if lines[j].strip() and not lines[j].startswith(' ' * 10):
                    purpose = lines[j].strip()
                    break
            break

    # If no usage found, try to find description from argparse output
    if not purpose:
        for line in lines:
            if line.strip() and not line.startswith('-'):
                purpose = line.strip()
                break

    # Extract positional arguments (required parameters)
    in_positional = False
    for line in lines:
        if 'positional arguments:' in line.lower():
            in_positional = True
            continue
        if in_positional:
            if line.startswith('optional arguments:') or line.startswith('options:'):
                break
            if line.strip() and not line.startswith(' ' * 20):
                # Extract parameter name
                match = re.match(r'\s+(\w+)', line)
                if match:
                    required_params.append(match.group(1))

    # Generate success criteria based on command type
    success_criteria = "Command executes without errors and produces expected output"

    return {
        "purpose": purpose or "Command documentation not available",
        "syntax": syntax or "See help output for syntax",
        "required_params": ", ".join(required_params) if required_params else "None",
        "success_criteria": success_criteria
    }


def get_command_category(command: str) -> str:
    """
    Get category for a command.

    Args:
        command: Command name

    Returns:
        Category string
    """
    # Check direct mapping first
    if command in COMMAND_CATEGORIES:
        return COMMAND_CATEGORIES[command]

    # Check for aliases
    base_command = command.replace('_', '-')
    if base_command in COMMAND_CATEGORIES:
        return COMMAND_CATEGORIES[base_command]

    # Default category
    return "Utility"


def get_task_name(command: str, category: str) -> str:
    """
    Generate task name from command and category.

    Args:
        command: Command name
        category: Command category

    Returns:
        Task name in format: (Category) CUM command_name
    """
    return f"({category}) CUM {command}"


def find_existing_task(client: ClickUpClient, list_id: str, task_name: str) -> Optional[str]:
    """
    Find existing task by name in a list.

    Args:
        client: ClickUp client instance
        list_id: List ID to search in
        task_name: Task name to find

    Returns:
        Task ID if found, None otherwise
    """
    try:
        result = client.get_list_tasks(list_id, include_closed=False)
        tasks = result.get('tasks', [])

        for task in tasks:
            if task.get('name') == task_name:
                return task.get('id')

        return None
    except Exception as e:
        print(f"  [WARNING] Error searching for task: {e}", file=sys.stderr)
        return None


def create_or_update_task(
    client: ClickUpClient,
    list_id: str,
    command: str,
    category: str,
    help_output: str,
    command_output: str,
    dry_run: bool = False,
    force: bool = False,
    use_color: bool = True
) -> Tuple[Optional[str], str]:
    """
    Create or update a task for a command.

    Args:
        client: ClickUp client instance
        list_id: List ID to create task in
        command: Command name
        category: Command category
        help_output: Help output from command
        command_output: Output from executing command
        dry_run: If True, don't make changes
        force: If True, update even if task exists
        use_color: If True, use ANSI colors and emojis

    Returns:
        Tuple of (task_id, status) where status is 'created', 'updated', 'skipped', or 'failed'
    """
    task_name = get_task_name(command, category)

    # Parse help output
    parsed = parse_help_output(help_output)

    # Check if task exists
    existing_task_id = find_existing_task(client, list_id, task_name)

    if existing_task_id and not force:
        if use_color:
            skip_msg = colorize("🎯 Task already synced, nothing to do here!", TextColor.BRIGHT_CYAN)
            print(f"    {skip_msg} ({existing_task_id})")
        else:
            print(f"  [SKIP] Task already exists: {task_name} ({existing_task_id})")
        return existing_task_id, 'skipped'

    # Prepare custom fields
    custom_fields = [
        {"id": CUSTOM_FIELDS["command_purpose"], "value": parsed["purpose"]},
        {"id": CUSTOM_FIELDS["command_syntax"], "value": parsed["syntax"]},
        {"id": CUSTOM_FIELDS["required_parameters"], "value": parsed["required_params"]},
        {"id": CUSTOM_FIELDS["success_criteria"], "value": parsed["success_criteria"]},
        {"id": CUSTOM_FIELDS["command_output"], "value": command_output}
    ]

    # Prepare task description
    description = f"""# CUM {command}

## Command Information

**Category:** {category}
**Command:** `cum {command}`

## Help Output

```
{help_output}
```

## Command Output

```
{command_output}
```

## Notes

- This task documents the `cum {command}` command
- Information is automatically generated by command-sync
- For the most up-to-date information, run `cum {command} --help`
"""

    if dry_run:
        if use_color:
            dry_msg = colorize("[DRY-RUN]", TextColor.BRIGHT_BLUE, TextStyle.BOLD)
            print(f"    {dry_msg} Would create/update: {task_name}")
            print(f"      Purpose: {parsed['purpose'][:60]}...")
            print(f"      Syntax: {parsed['syntax'][:60]}...")
        else:
            print(f"  [DRY-RUN] Would create/update: {task_name}")
            print(f"    Purpose: {parsed['purpose'][:60]}...")
            print(f"    Syntax: {parsed['syntax'][:60]}...")
        if existing_task_id:
            return existing_task_id, 'would-update'
        else:
            return None, 'would-create'

    try:
        if existing_task_id:
            # Update existing task
            client.update_task(
                task_id=existing_task_id,
                name=task_name,
                markdown_description=description
            )

            # Update custom fields (one at a time)
            for field in custom_fields:
                try:
                    client.set_custom_field(existing_task_id, field["id"], field["value"])
                except Exception as e:
                    print(f"  [WARNING] Failed to set custom field: {e}", file=sys.stderr)

            if use_color:
                update_msg = colorize("📝 Task refreshed with latest info!", TextColor.BRIGHT_YELLOW)
                print(f"    {update_msg} ({existing_task_id})")
            else:
                print(f"  [UPDATED] {task_name} ({existing_task_id})")
            return existing_task_id, 'updated'
        else:
            # Create new task
            task = client.create_task(
                list_id=list_id,
                name=task_name,
                markdown_description=description,
                tags=[category.lower().replace(" ", "-"), "cli-command", "auto-generated"]
            )
            task_id = task.get('id')

            # Set custom fields (one at a time)
            for field in custom_fields:
                try:
                    client.set_custom_field(task_id, field["id"], field["value"])
                except Exception as e:
                    print(f"  [WARNING] Failed to set custom field: {e}", file=sys.stderr)

            if use_color:
                create_msg = colorize("✨ Fresh task created, welcome to the party!", TextColor.BRIGHT_GREEN)
                print(f"    {create_msg} ({task_id})")
            else:
                print(f"  [CREATED] {task_name} ({task_id})")
            return task_id, 'created'
    except ClickUpAPIError as e:
        if use_color:
            error_msg = ANSIAnimations.error_message(f"Failed to create/update task: {e}")
            print(f"    {error_msg}", file=sys.stderr)
        else:
            print(f"  [ERROR] Failed to create/update task: {e}", file=sys.stderr)
        return None, 'failed'
    except Exception as e:
        if use_color:
            error_msg = ANSIAnimations.error_message(f"Unexpected error: {e}")
            print(f"    {error_msg}", file=sys.stderr)
        else:
            print(f"  [ERROR] Unexpected error: {e}", file=sys.stderr)
        return None, 'failed'


def discover_cli_commands(
    command_parsers: Optional[Dict[str, argparse.ArgumentParser]] = None,
) -> List[str]:
    """
    Discover syncable CLI commands from the registered parser tree.

    Returns:
        List of command names (canonical names, not aliases)
    """
    command_parsers = command_parsers or _get_registered_command_parsers()
    known_commands = sorted(COMMAND_CATEGORIES.keys())
    available_commands = []
    missing_from_parser = []

    for command in known_commands:
        if _resolve_registered_command_name(command, command_parsers):
            available_commands.append(command)
        else:
            missing_from_parser.append(command)

    if missing_from_parser:
        print(
            f"  [WARNING] {len(missing_from_parser)} commands in COMMAND_CATEGORIES "
            "are not currently registered in the CLI parser:",
            file=sys.stderr,
        )
        for command in missing_from_parser:
            print(f"    - {command}", file=sys.stderr)

    return available_commands


def list_missing_commands(list_id: str = DEFAULT_CLI_COMMANDS_LIST_ID):
    """Report parser, mapping, and catalog gaps for command-sync maintenance."""
    command_parsers = _get_registered_command_parsers()
    registered_commands = set(command_parsers.keys())
    known_commands = set(COMMAND_CATEGORIES.keys())
    syncable_commands = discover_cli_commands(command_parsers)

    missing_from_categories = sorted(
        command
        for command in registered_commands
        if _resolve_registry_key(command, COMMAND_CATEGORIES) is None
    )
    missing_from_parser = sorted(
        command
        for command in known_commands
        if _resolve_registered_command_name(command, command_parsers) is None
    )
    missing_task_mappings = sorted(
        command
        for command in syncable_commands
        if _resolve_registry_key(command, COMMAND_TASK_IDS) is None
    )

    print("=" * 80)
    print("Command Discovery Status")
    print("=" * 80)
    print(f"Total registered root commands: {len(registered_commands)}")
    print(f"Total in COMMAND_CATEGORIES: {len(known_commands)}")
    print(f"Total in CLI_COMMAND_TASK_IDS: {len(COMMAND_TASK_IDS)}")
    print(f"Total syncable commands: {len(syncable_commands)}")
    print("=" * 80)
    print()

    if missing_from_categories:
        print(
            "Registered commands missing from COMMAND_CATEGORIES "
            f"({len(missing_from_categories)}):"
        )
        for command in missing_from_categories:
            print(f"  - {command}")
        print()
    else:
        print("✓ All registered commands have COMMAND_CATEGORIES coverage")
        print()

    if missing_from_parser:
        print(
            "Commands in COMMAND_CATEGORIES but not currently registered "
            f"({len(missing_from_parser)}):"
        )
        for command in missing_from_parser:
            print(f"  - {command}")
        print()
    else:
        print("✓ All COMMAND_CATEGORIES entries are currently registered")
        print()

    if missing_task_mappings:
        print(
            "Syncable commands missing from CLI_COMMAND_TASK_IDS "
            f"({len(missing_task_mappings)}):"
        )
        for command in missing_task_mappings:
            print(f"  - {command}")
        print()
    else:
        print("✓ All syncable commands have CLI_COMMAND_TASK_IDS coverage")
        print()

    try:
        client = ClickUpClient()
        list_tasks = _get_all_list_tasks(client, list_id)
        task_ids_in_list = {task.get("id") for task in list_tasks}
        task_names_in_list = {task.get("name") for task in list_tasks}

        mapped_ids_missing_in_list = []
        expected_tasks_missing_in_list = []

        for command in syncable_commands:
            category = get_command_category(command)
            expected_task_name = get_task_name(command, category)
            if expected_task_name not in task_names_in_list:
                expected_tasks_missing_in_list.append((command, expected_task_name))

            mapping_key = _resolve_registry_key(command, COMMAND_TASK_IDS)
            if not mapping_key:
                continue

            mapped_task_id = COMMAND_TASK_IDS[mapping_key]
            if mapped_task_id not in task_ids_in_list:
                mapped_ids_missing_in_list.append((command, mapped_task_id))

        print(
            f"CLI Commands list audit: {len(list_tasks)} task(s) fetched from {list_id}"
        )
        print()

        if expected_tasks_missing_in_list:
            print(
                "Syncable commands with no matching CLI Commands task by name "
                f"({len(expected_tasks_missing_in_list)}):"
            )
            for command, task_name in expected_tasks_missing_in_list:
                print(f"  - {command} -> {task_name}")
            print()
        else:
            print("✓ Every syncable command has a matching CLI Commands task by name")
            print()

        if mapped_ids_missing_in_list:
            print(
                "CLI_COMMAND_TASK_IDS entries not found in the CLI Commands list "
                f"({len(mapped_ids_missing_in_list)}):"
            )
            for command, task_id in mapped_ids_missing_in_list:
                print(f"  - {command} -> {task_id}")
            print()
        else:
            print("✓ Every mapped CLI command task ID exists in the CLI Commands list")
            print()

    except Exception as e:
        print(
            f"[WARNING] Could not audit the CLI Commands list itself: {e}",
            file=sys.stderr,
        )

    print("=" * 80)


def command_sync_command(args):
    """Execute command-sync command."""
    # Handle --list-missing option
    if args.list_missing:
        list_missing_commands(args.list_id)
        return

    list_id = args.list_id
    test_task_id = args.test_task_id
    dry_run = args.dry_run
    force = args.force

    # Get ANSI output preference
    context = get_context_manager()
    use_color = context.get_ansi_output()

    # Display humorous header
    print()
    if use_color:
        # Animated rainbow header
        ANSIAnimations.display_animated_rainbow("🔄 CUM COMMAND SYNC - SYNCING ALL THE THINGS! 🔄", duration=1.5, speed=3.0)
        print()

        # Dry run warning
        if dry_run:
            dry_run_msg = colorize("🧪 DRY RUN MODE - No actual changes will be made",
                                  TextColor.BRIGHT_YELLOW, TextStyle.BOLD)
            print(dry_run_msg)
            print()

        # Config info box
        config_lines = [
            f"📋 List ID: {colorize(list_id, TextColor.BRIGHT_CYAN)}",
            f"🎯 Test Task: {colorize(test_task_id, TextColor.BRIGHT_CYAN)}",
            f"🔧 Mode: {colorize('DRY RUN' if dry_run else 'LIVE', TextColor.BRIGHT_YELLOW if dry_run else TextColor.BRIGHT_GREEN)}",
            f"⚡ Force: {colorize('YES' if force else 'NO', TextColor.BRIGHT_RED if force else TextColor.BRIGHT_GREEN)}"
        ]

        box = ANSIAnimations.animated_box(
            ANSIAnimations.white_sheen_text("SYNC CONFIGURATION", TextColor.BRIGHT_MAGENTA),
            config_lines,
            TextColor.BRIGHT_MAGENTA
        )
        print(box)
        print()
    else:
        print("=" * 80)
        print("CUM Command Sync - Auto-Update CLI Command Tasks")
        print("=" * 80)
        print(f"List ID: {list_id}")
        print(f"Test Task ID: {test_task_id}")
        print(f"Dry Run: {dry_run}")
        print(f"Force Update: {force}")
        print("=" * 80)
        print()

    # Initialize ClickUp client
    try:
        client = ClickUpClient()
    except Exception as e:
        print(f"Error: Failed to initialize ClickUp client: {e}", file=sys.stderr)
        sys.exit(1)

    # Discover all commands
    if use_color:
        step_msg = ANSIAnimations.white_sheen_text("[1/4]", TextColor.BRIGHT_CYAN)
        step_text = ANSIAnimations.white_sheen_text("✨ Discovering commands... ✨", TextColor.BRIGHT_MAGENTA)
        print(f"{step_msg} {step_text}")
    else:
        print("[1/4] Discovering commands...")

    command_parsers = _get_registered_command_parsers()
    all_commands = discover_cli_commands(command_parsers)

    if use_color:
        found_msg = colorize(f"🎯 Found {len(all_commands)} commands ready to sync!", TextColor.BRIGHT_GREEN, TextStyle.BOLD)
        print(f"  {found_msg}")
    else:
        print(f"  Found {len(all_commands)} commands")
    print()

    # Process each command
    if use_color:
        step_msg = ANSIAnimations.white_sheen_text("[2/4]", TextColor.BRIGHT_CYAN)
        step_text = ANSIAnimations.white_sheen_text("📋 Processing commands... 📋", TextColor.BRIGHT_MAGENTA)
        print(f"{step_msg} {step_text}")
    else:
        print(f"[2/4] Processing commands...")

    created = 0
    updated = 0
    skipped = 0
    failed = 0

    for i, command in enumerate(all_commands, 1):
        if use_color:
            cmd_msg = colorize(f"✨ [{i}/{len(all_commands)}] Processing:", TextColor.BRIGHT_YELLOW)
            cmd_name = colorize(command, TextColor.BRIGHT_CYAN, TextStyle.BOLD)
            print(f"\n  {cmd_msg} {cmd_name}")
        else:
            print(f"\n[{i}/{len(all_commands)}] Processing: {command}")

        # Get category
        category = get_command_category(command)
        if use_color:
            cat_label = colorize("Category:", TextColor.BRIGHT_BLUE)
            cat_name = colorize(category, TextColor.BRIGHT_GREEN)
            print(f"    {cat_label} {cat_name}")
        else:
            print(f"  Category: {category}")

        # Get help output
        help_output, error_output = get_command_help(command, command_parsers)
        if not help_output:
            print(f"  [WARNING] No help output for command '{command}'")
            if error_output:
                print(f"  Error: {error_output[:100]}")

        # Execute command to get output
        if not dry_run and test_task_id:
            print(f"  Executing command on test task...")
            command_output, exec_error = execute_command_on_test_task(command, test_task_id)
        else:
            command_output = "N/A - Dry run mode"

        # Create or update task
        task_id, status = create_or_update_task(
            client=client,
            list_id=list_id,
            command=command,
            category=category,
            help_output=help_output,
            command_output=command_output,
            dry_run=dry_run,
            force=force,
            use_color=use_color
        )

        # Count based on status
        if status == 'created' or status == 'would-create':
            created += 1
        elif status == 'updated' or status == 'would-update':
            updated += 1
        elif status == 'skipped':
            skipped += 1
        elif status == 'failed':
            failed += 1

    # Print summary
    print()
    if use_color:
        # Epic finale
        print()
        ANSIAnimations.display_animated_rainbow(
            "🎉 COMMAND SYNC COMPLETE! ALL COMMANDS ARE NOW IN SYNC! 🎉",
            duration=2.0,
            speed=3.0
        )
        print()

        # Summary stats
        summary_lines = [
            f"📊 {colorize('Total commands:', TextColor.BRIGHT_CYAN)} {colorize(str(len(all_commands)), TextColor.BRIGHT_WHITE, TextStyle.BOLD)}",
            f"✨ {colorize('Created:', TextColor.BRIGHT_GREEN)} {colorize(str(created), TextColor.BRIGHT_WHITE, TextStyle.BOLD)}",
            f"📝 {colorize('Updated:', TextColor.BRIGHT_YELLOW)} {colorize(str(updated), TextColor.BRIGHT_WHITE, TextStyle.BOLD)}",
            f"⏭️  {colorize('Skipped:', TextColor.BRIGHT_BLUE)} {colorize(str(skipped), TextColor.BRIGHT_WHITE, TextStyle.BOLD)}",
            f"❌ {colorize('Failed:', TextColor.BRIGHT_RED)} {colorize(str(failed), TextColor.BRIGHT_WHITE, TextStyle.BOLD)}"
        ]

        box = ANSIAnimations.animated_box(
            ANSIAnimations.white_sheen_text("SYNC RESULTS", TextColor.BRIGHT_GREEN),
            summary_lines,
            TextColor.BRIGHT_GREEN
        )
        print(box)
        print()

        # Fun completion message
        if failed == 0:
            success_msg = colorize("🚀 All systems go! Your CLI commands are locked and loaded!", TextColor.BRIGHT_GREEN, TextStyle.BOLD)
            print(success_msg)
        else:
            warning_msg = colorize(f"⚠️  Sync completed with {failed} failure(s). Check the logs above!", TextColor.BRIGHT_YELLOW, TextStyle.BOLD)
            print(warning_msg)
        print()
    else:
        print("=" * 80)
        print("Summary:")
        print(f"  Total commands: {len(all_commands)}")
        print(f"  Created: {created}")
        print(f"  Updated: {updated}")
        print(f"  Skipped: {skipped}")
        print(f"  Failed: {failed}")
        print("=" * 80)


def register_command(subparsers):
    """Register the command-sync command with argparse."""
    parser = subparsers.add_parser(
        'command-sync',
        aliases=['csync', 'cmd-sync'],
        help='Auto-update CLI command tasks with command information',
        description="""
Automatically discover all cum commands, create/update ClickUp tasks for each command
in the CLI Commands list, and populate custom fields with command information including
help output, syntax, purpose, and execution results.
"""
    )

    parser.add_argument(
        '--list-id',
        default=DEFAULT_CLI_COMMANDS_LIST_ID,
        help=f'ClickUp list ID where command tasks are stored (default: {DEFAULT_CLI_COMMANDS_LIST_ID})'
    )

    parser.add_argument(
        '--test-task-id',
        default=DEFAULT_TEST_TASK_ID,
        help=f'Task ID to use for command execution testing (default: {DEFAULT_TEST_TASK_ID})'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )

    parser.add_argument(
        '--force',
        action='store_true',
        help='Force update even if task already exists and is up-to-date'
    )

    parser.add_argument(
        '--list-missing',
        action='store_true',
        help='Audit registered commands against category/task mappings and the CLI Commands list'
    )

    parser.set_defaults(func=command_sync_command)
