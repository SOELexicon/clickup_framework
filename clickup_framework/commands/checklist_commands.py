"""Checklist management commands for ClickUp Framework CLI."""

import sys
import json
from clickup_framework import ClickUpClient, get_context_manager
from clickup_framework.resources.tasks import TasksAPI
from clickup_framework.resources.checklist_template_manager import ChecklistTemplateManager
from clickup_framework.utils.colors import colorize, TextColor, TextStyle
from clickup_framework.utils.animations import ANSIAnimations
from clickup_framework.utils.checklist_mapping import get_mapping_manager
from clickup_framework.exceptions import ClickUpAPIError


def _is_uuid(value: str) -> bool:
    """Check if a string is a UUID format."""
    # UUIDs are 36 characters with hyphens (e.g., "550e8400-e29b-41d4-a716-446655440000")
    if len(value) == 36 and value.count('-') == 4:
        return True
    # Also accept IDs without hyphens (32 characters)
    if len(value) == 32:
        return True
    return False


def _resolve_checklist_id(task_id: str, checklist_id_or_index: str) -> str:
    """
    Resolve checklist ID or index to UUID.

    Args:
        task_id: Task ID
        checklist_id_or_index: Either a checklist UUID or numeric index (1, 2, 3...)

    Returns:
        Checklist UUID

    Raises:
        ValueError: If index is invalid or not found
    """
    # If it looks like a UUID, return as-is (backward compatibility)
    if _is_uuid(checklist_id_or_index):
        return checklist_id_or_index

    # Try to parse as index
    try:
        index = int(checklist_id_or_index)
    except ValueError:
        # Not a number and not a UUID, return as-is and let API handle it
        return checklist_id_or_index

    # Look up UUID by index
    mapping_manager = get_mapping_manager()
    uuid = mapping_manager.get_checklist_uuid(task_id, index)

    if uuid is None:
        raise ValueError(
            f"Checklist index [{index}] not found for task {task_id}. "
            f"Use 'cum chk list {task_id}' to see available checklists with indices."
        )

    return uuid


def _resolve_item_id(task_id: str, checklist_id: str, item_id_or_index: str) -> str:
    """
    Resolve item ID or index to UUID.

    Args:
        task_id: Task ID
        checklist_id: Checklist UUID
        item_id_or_index: Either an item UUID or numeric index (1, 2, 3...)

    Returns:
        Item UUID

    Raises:
        ValueError: If index is invalid or not found
    """
    # If it looks like a UUID, return as-is (backward compatibility)
    if _is_uuid(item_id_or_index):
        return item_id_or_index

    # Try to parse as index
    try:
        index = int(item_id_or_index)
    except ValueError:
        # Not a number and not a UUID, return as-is and let API handle it
        return item_id_or_index

    # Look up UUID by index
    mapping_manager = get_mapping_manager()
    uuid = mapping_manager.get_item_uuid(task_id, checklist_id, index)

    if uuid is None:
        raise ValueError(
            f"Item index [{index}] not found in checklist {checklist_id} for task {task_id}. "
            f"Use 'cum chk list {task_id}' to see available items with indices."
        )

    return uuid


def checklist_create_command(args):
    """Create a new checklist on a task."""
    context = get_context_manager()
    client = ClickUpClient()
    tasks_api = TasksAPI(client)
    mapping_manager = get_mapping_manager()

    # Resolve task ID
    try:
        task_id = context.resolve_id('task', args.task_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Create the checklist
    try:
        checklist = tasks_api.add_checklist(task_id, args.name)
        # API response is unwrapped by client, no need for nested ['checklist'] access
        checklist_id = checklist['id']

        # Auto-map the new checklist
        next_index = mapping_manager.get_next_checklist_index(task_id)
        mapping_manager.set_checklist_mapping(task_id, next_index, checklist_id)

        success_msg = ANSIAnimations.success_message(f"Checklist created: {args.name}")
        print(f"\n{success_msg}")
        print(f"Checklist ID: {colorize(checklist_id, TextColor.BRIGHT_GREEN)}")
        print(f"Checklist Index: {colorize(f'[{next_index}]', TextColor.BRIGHT_CYAN)}")

        if args.verbose:
            print(f"\nTask ID: {task_id}")

    except ClickUpAPIError as e:
        print(f"Error creating checklist: {e}", file=sys.stderr)
        sys.exit(1)


def checklist_delete_command(args):
    """Delete a checklist."""
    context = get_context_manager()
    client = ClickUpClient()
    mapping_manager = get_mapping_manager()

    # Resolve checklist ID (with optional task ID for index resolution)
    checklist_id = args.checklist_id
    task_id = None

    if hasattr(args, 'task') and args.task:
        # Task ID provided, resolve index if needed
        try:
            task_id = context.resolve_id('task', args.task)
            checklist_id = _resolve_checklist_id(task_id, args.checklist_id)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    elif not _is_uuid(args.checklist_id):
        # Looks like an index but no task provided
        print(f"Error: Checklist index provided but no task specified. Use --task <task_id>", file=sys.stderr)
        sys.exit(1)

    # Show warning
    print(f"\n{colorize('Warning:', TextColor.BRIGHT_YELLOW, TextStyle.BOLD)} This will permanently delete the checklist and all its items.")

    if not args.force:
        response = input("Are you sure? [y/N]: ")
        if response.lower() not in ['y', 'yes']:
            print("Cancelled.")
            return

    # Delete the checklist
    try:
        client.delete_checklist(checklist_id)

        # Remove from mapping if task_id is known
        if task_id:
            mapping_manager.remove_checklist_mapping(task_id, checklist_id)

        success_msg = ANSIAnimations.success_message("Checklist deleted successfully")
        print(f"\n{success_msg}")

    except ClickUpAPIError as e:
        print(f"Error deleting checklist: {e}", file=sys.stderr)
        sys.exit(1)


def checklist_update_command(args):
    """Update a checklist."""
    context = get_context_manager()
    client = ClickUpClient()

    # Resolve checklist ID (with optional task ID for index resolution)
    checklist_id = args.checklist_id
    if hasattr(args, 'task') and args.task:
        # Task ID provided, resolve index if needed
        try:
            task_id = context.resolve_id('task', args.task)
            checklist_id = _resolve_checklist_id(task_id, args.checklist_id)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    elif not _is_uuid(args.checklist_id):
        # Looks like an index but no task provided
        print(f"Error: Checklist index provided but no task specified. Use --task <task_id>", file=sys.stderr)
        sys.exit(1)

    # Build updates
    updates = {}
    if args.name:
        updates['name'] = args.name
    if args.position is not None:
        updates['position'] = args.position

    if not updates:
        print("Error: No updates specified. Use --name or --position", file=sys.stderr)
        sys.exit(1)

    # Update the checklist
    try:
        client.update_checklist(checklist_id, **updates)
        success_msg = ANSIAnimations.success_message("Checklist updated successfully")
        print(f"\n{success_msg}")

        if args.verbose:
            print(f"\nUpdates applied:")
            for key, value in updates.items():
                print(f"  {key}: {value}")

    except ClickUpAPIError as e:
        print(f"Error updating checklist: {e}", file=sys.stderr)
        sys.exit(1)


def checklist_item_add_command(args):
    """Add an item to a checklist."""
    context = get_context_manager()
    client = ClickUpClient()
    tasks_api = TasksAPI(client)
    mapping_manager = get_mapping_manager()

    # Resolve checklist ID (with optional task ID for index resolution)
    checklist_id = args.checklist_id
    task_id = None

    if hasattr(args, 'task') and args.task:
        # Task ID provided, resolve index if needed
        try:
            task_id = context.resolve_id('task', args.task)
            checklist_id = _resolve_checklist_id(task_id, args.checklist_id)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    elif not _is_uuid(args.checklist_id):
        # Looks like an index but no task provided
        print(f"Error: Checklist index provided but no task specified. Use --task <task_id>", file=sys.stderr)
        sys.exit(1)

    # Resolve assignee if provided
    assignee = None
    if args.assignee:
        try:
            assignee = int(context.resolve_id('assignee', args.assignee))
        except ValueError as e:
            print(f"Error: Invalid assignee ID: {e}", file=sys.stderr)
            sys.exit(1)

    # Add the checklist item
    try:
        result = tasks_api.add_checklist_item(checklist_id, args.name, assignee=assignee)

        success_msg = ANSIAnimations.success_message(f"Checklist item added: {args.name}")
        print(f"\n{success_msg}")

        # API now returns the item directly (unwrapped by client)
        item_id = result.get('id', 'Unknown') if isinstance(result, dict) else 'Unknown'
        print(f"Item ID: {colorize(str(item_id), TextColor.BRIGHT_GREEN)}")

        # Auto-map the new item if task_id is known
        if task_id and item_id and item_id != 'Unknown':
            next_index = mapping_manager.get_next_item_index(task_id, checklist_id)
            mapping_manager.set_item_mapping(task_id, checklist_id, next_index, item_id)
            print(f"Item Index: {colorize(f'[{next_index}]', TextColor.BRIGHT_CYAN)}")

        if assignee:
            print(f"Assigned to: {assignee}")

        if args.verbose:
            print(f"\nChecklist ID: {checklist_id}")
            if task_id:
                print(f"Task ID: {task_id}")

    except ClickUpAPIError as e:
        print(f"Error adding checklist item: {e}", file=sys.stderr)
        sys.exit(1)


def checklist_item_update_command(args):
    """Update a checklist item."""
    context = get_context_manager()
    client = ClickUpClient()

    # Resolve checklist ID and item ID (with optional task ID for index resolution)
    checklist_id = args.checklist_id
    item_id = args.item_id

    if hasattr(args, 'task') and args.task:
        # Task ID provided, resolve indices if needed
        try:
            task_id = context.resolve_id('task', args.task)
            checklist_id = _resolve_checklist_id(task_id, args.checklist_id)
            item_id = _resolve_item_id(task_id, checklist_id, args.item_id)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # No task provided, check if indices were used
        if not _is_uuid(args.checklist_id):
            print(f"Error: Checklist index provided but no task specified. Use --task <task_id>", file=sys.stderr)
            sys.exit(1)
        if not _is_uuid(args.item_id):
            print(f"Error: Item index provided but no task specified. Use --task <task_id>", file=sys.stderr)
            sys.exit(1)

    # Build updates
    updates = {}
    if args.name:
        updates['name'] = args.name
    if args.assignee is not None:
        updates['assignee'] = int(args.assignee) if args.assignee else None
    if args.resolved is not None:
        updates['resolved'] = args.resolved
    if args.parent is not None:
        updates['parent'] = args.parent

    if not updates:
        print("Error: No updates specified. Use --name, --assignee, --resolved, or --parent", file=sys.stderr)
        sys.exit(1)

    # Update the checklist item
    try:
        client.update_checklist_item(checklist_id, item_id, **updates)
        success_msg = ANSIAnimations.success_message("Checklist item updated successfully")
        print(f"\n{success_msg}")

        if args.verbose:
            print(f"\nUpdates applied:")
            for key, value in updates.items():
                print(f"  {key}: {value}")

    except ClickUpAPIError as e:
        print(f"Error updating checklist item: {e}", file=sys.stderr)
        sys.exit(1)


def checklist_item_delete_command(args):
    """Delete a checklist item."""
    context = get_context_manager()
    client = ClickUpClient()
    mapping_manager = get_mapping_manager()

    # Resolve checklist ID and item ID (with optional task ID for index resolution)
    checklist_id = args.checklist_id
    item_id = args.item_id
    task_id = None

    if hasattr(args, 'task') and args.task:
        # Task ID provided, resolve indices if needed
        try:
            task_id = context.resolve_id('task', args.task)
            checklist_id = _resolve_checklist_id(task_id, args.checklist_id)
            item_id = _resolve_item_id(task_id, checklist_id, args.item_id)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # No task provided, check if indices were used
        if not _is_uuid(args.checklist_id):
            print(f"Error: Checklist index provided but no task specified. Use --task <task_id>", file=sys.stderr)
            sys.exit(1)
        if not _is_uuid(args.item_id):
            print(f"Error: Item index provided but no task specified. Use --task <task_id>", file=sys.stderr)
            sys.exit(1)

    if not args.force:
        response = input(f"Delete checklist item {item_id}? [y/N]: ")
        if response.lower() not in ['y', 'yes']:
            print("Cancelled.")
            return

    # Delete the checklist item
    try:
        client.delete_checklist_item(checklist_id, item_id)

        # Remove from mapping if task_id is known
        if task_id:
            mapping_manager.remove_item_mapping(task_id, checklist_id, item_id)

        success_msg = ANSIAnimations.success_message("Checklist item deleted successfully")
        print(f"\n{success_msg}")

    except ClickUpAPIError as e:
        print(f"Error deleting checklist item: {e}", file=sys.stderr)
        sys.exit(1)


def checklist_list_command(args):
    """List checklists on a task."""
    context = get_context_manager()
    client = ClickUpClient()
    mapping_manager = get_mapping_manager()

    # Resolve task ID
    try:
        task_id = context.resolve_id('task', args.task_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Get task to access checklists
    try:
        task = client.get_task(task_id)
        checklists = task.get('checklists', [])

        if not checklists:
            print(f"\nNo checklists found on task {task_id}")
            return

        # Update mappings from task data
        mapping_manager.update_mappings_from_task(task_id, task)

        # Display checklists
        print(f"\n{colorize('Checklists', TextStyle.BOLD)} for task {task['name']}")
        print(f"Task ID: {task_id}\n")

        for checklist in checklists:
            checklist_id = checklist.get('id', 'Unknown')
            checklist_name = checklist.get('name', 'Unnamed')
            items = checklist.get('items', [])
            resolved_count = sum(1 for item in items if item.get('resolved', False))
            total_count = len(items)

            # Get checklist index
            checklist_index = mapping_manager.get_checklist_index(task_id, checklist_id)
            checklist_index_str = f"[{checklist_index}] " if checklist_index else ""

            # Progress indicator
            if total_count > 0:
                progress_pct = int((resolved_count / total_count) * 100)
                if progress_pct == 100:
                    progress_color = TextColor.BRIGHT_GREEN
                elif progress_pct > 0:
                    progress_color = TextColor.BRIGHT_YELLOW
                else:
                    progress_color = TextColor.BRIGHT_BLACK

                progress_str = f"({resolved_count}/{total_count})"
                if args.colorize:
                    progress_str = colorize(progress_str, progress_color)
            else:
                progress_str = "(0/0)"

            print(f"☑️  {checklist_index_str}{colorize(checklist_name, TextStyle.BOLD)} {progress_str}")

            if args.show_ids:
                print(f"    ID: {colorize(checklist_id, TextColor.BRIGHT_BLACK)}")

            # List items
            if items and not args.no_items:
                for item in items:
                    item_name = item.get('name', 'Unnamed')
                    item_id = item.get('id', 'Unknown')
                    resolved = item.get('resolved', False)
                    assignee = item.get('assignee')

                    # Get item index
                    item_index = mapping_manager.get_item_index(task_id, checklist_id, item_id)
                    item_index_str = f"[{item_index}] " if item_index else ""

                    # Checkbox indicator
                    checkbox = "✓" if resolved else "☐"
                    if args.colorize:
                        checkbox_color = TextColor.BRIGHT_GREEN if resolved else TextColor.BRIGHT_BLACK
                        checkbox = colorize(checkbox, checkbox_color)

                    item_str = f"    {checkbox} {item_index_str}{item_name}"

                    if assignee:
                        assignee_name = assignee.get('username', 'Unknown')
                        item_str += f" [@{assignee_name}]"

                    if args.show_ids:
                        item_str += f" {colorize(f'({item_id})', TextColor.BRIGHT_BLACK)}"

                    print(item_str)

            print()  # Blank line between checklists

    except ClickUpAPIError as e:
        print(f"Error listing checklists: {e}", file=sys.stderr)
        sys.exit(1)


def checklist_template_list_command(args):
    """List available checklist templates."""
    template_manager = ChecklistTemplateManager()

    try:
        templates = template_manager.list_templates()

        if not templates:
            print("\nNo checklist templates found.")
            print("\nTemplates are loaded from:")
            print(f"  1. {ChecklistTemplateManager.DEFAULT_TEMPLATES_FILE}")
            print(f"  2. {ChecklistTemplateManager.USER_TEMPLATES_FILE}")
            return

        print(f"\n{colorize('Available Checklist Templates', TextStyle.BOLD)}\n")

        for template_name in templates:
            template = template_manager.get_template(template_name)
            item_count = len(template.get('items', []))
            description = template.get('description', 'No description')

            print(f"  {colorize(template_name, TextColor.BRIGHT_CYAN, TextStyle.BOLD)}")
            print(f"    {description}")
            print(f"    Items: {item_count}\n")

        print(f"Use {colorize('cum checklist template show <name>', TextColor.BRIGHT_BLACK)} to view template details")
        print(f"Use {colorize('cum checklist template apply <task_id> <name>', TextColor.BRIGHT_BLACK)} to apply template to a task")

    except Exception as e:
        print(f"Error listing templates: {e}", file=sys.stderr)
        sys.exit(1)


def checklist_template_show_command(args):
    """Show details of a checklist template."""
    template_manager = ChecklistTemplateManager()

    try:
        template = template_manager.get_template(args.template_name)

        if not template:
            print(f"Error: Template '{args.template_name}' not found", file=sys.stderr)
            print(f"\nUse {colorize('cum checklist template list', TextColor.BRIGHT_BLACK)} to see available templates")
            sys.exit(1)

        # Display template details
        print(f"\n{colorize('Template:', TextStyle.BOLD)} {colorize(args.template_name, TextColor.BRIGHT_CYAN)}")
        print(f"{colorize('Name:', TextStyle.BOLD)} {template.get('name', args.template_name)}")

        if 'description' in template:
            print(f"{colorize('Description:', TextStyle.BOLD)} {template['description']}")

        items = template.get('items', [])
        print(f"\n{colorize('Items:', TextStyle.BOLD)} ({len(items)})\n")

        for i, item in enumerate(items, 1):
            item_name = item.get('name', 'Unnamed')
            print(f"  {i}. {item_name}")

            if 'assignee' in item and item['assignee']:
                print(f"     Assignee: {item['assignee']}")

        if args.json:
            print(f"\n{colorize('JSON:', TextStyle.BOLD)}")
            print(json.dumps(template, indent=2))

    except Exception as e:
        print(f"Error showing template: {e}", file=sys.stderr)
        sys.exit(1)


def checklist_template_apply_command(args):
    """Apply a checklist template to a task."""
    context = get_context_manager()
    client = ClickUpClient()
    template_manager = ChecklistTemplateManager()

    # Resolve task ID
    try:
        task_id = context.resolve_id('task', args.task_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Apply template
    try:
        result = template_manager.apply_template(client, task_id, args.template_name)

        checklist = result['checklist']
        items = result['items']
        template_name = result['template_name']

        success_msg = ANSIAnimations.success_message(f"Template '{template_name}' applied successfully")
        print(f"\n{success_msg}")
        print(f"\nChecklist: {colorize(checklist['name'], TextColor.BRIGHT_CYAN)}")
        print(f"Checklist ID: {colorize(checklist['id'], TextColor.BRIGHT_GREEN)}")
        print(f"Items created: {len(items)}")

        if args.verbose:
            print(f"\nTask ID: {task_id}")
            print(f"\nCreated items:")
            for item_data in items:
                if 'checklist' in item_data and 'items' in item_data['checklist']:
                    for item in item_data['checklist']['items']:
                        print(f"  - {item.get('name', 'Unnamed')}")

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ClickUpAPIError as e:
        print(f"Error applying template: {e}", file=sys.stderr)
        sys.exit(1)


def checklist_clone_command(args):
    """Clone checklists from one task to another."""
    context = get_context_manager()
    client = ClickUpClient()

    # Resolve task IDs
    try:
        source_task_id = context.resolve_id('task', args.source_task_id)
        target_task_id = context.resolve_id('task', args.target_task_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if source_task_id == target_task_id:
        print("Error: Source and target tasks must be different", file=sys.stderr)
        sys.exit(1)

    # Get source task checklists
    try:
        source_task = client.get_task(source_task_id)
        checklists = source_task.get('checklists', [])

        if not checklists:
            print(f"No checklists found on source task {source_task_id}")
            return

        print(f"\nCloning {len(checklists)} checklist(s) from task {source_task_id} to {target_task_id}...")

        cloned_count = 0
        for checklist in checklists:
            checklist_name = checklist.get('name', 'Unnamed')
            items = checklist.get('items', [])

            # Create checklist on target task
            result = client.create_checklist(target_task_id, checklist_name)
            # API response is unwrapped by client, no need for nested ['checklist'] access
            new_checklist_id = result['id']

            # Clone items
            for item in items:
                item_name = item.get('name', '')
                if not item_name:
                    continue

                item_data = {}
                # Note: Not cloning assignees or resolved status by default
                # Items start fresh on the new task

                client.create_checklist_item(new_checklist_id, item_name, **item_data)

            cloned_count += 1
            print(f"  ✓ Cloned: {colorize(checklist_name, TextColor.BRIGHT_CYAN)} ({len(items)} items)")

        success_msg = ANSIAnimations.success_message(f"Successfully cloned {cloned_count} checklist(s)")
        print(f"\n{success_msg}")

        if args.verbose:
            print(f"\nSource Task: {source_task_id}")
            print(f"Target Task: {target_task_id}")

    except ClickUpAPIError as e:
        print(f"Error cloning checklists: {e}", file=sys.stderr)
        sys.exit(1)


def register_command(subparsers):
    """Register checklist commands."""
    # Create checklist subcommand group
    checklist_parser = subparsers.add_parser(
        'checklist',
        aliases=['chk'],
        help='Manage checklists on tasks',
        description='Manage checklists and checklist items on tasks'
    )

    checklist_subparsers = checklist_parser.add_subparsers(dest='checklist_command', help='Checklist command')

    # checklist create
    create_parser = checklist_subparsers.add_parser(
        'create',
        help='Create a new checklist on a task',
        description='Create a new checklist on a task'
    )
    create_parser.add_argument('task_id', help='Task ID (or "current")')
    create_parser.add_argument('name', help='Checklist name')
    create_parser.add_argument('--verbose', '-v', action='store_true', help='Show additional information')
    create_parser.set_defaults(func=checklist_create_command)

    # checklist delete
    delete_parser = checklist_subparsers.add_parser(
        'delete',
        aliases=['rm'],
        help='Delete a checklist',
        description='Delete a checklist and all its items'
    )
    delete_parser.add_argument('checklist_id', help='Checklist ID or index (e.g., 1, 2, 3)')
    delete_parser.add_argument('--task', help='Task ID (required when using checklist index)')
    delete_parser.add_argument('--force', '-f', action='store_true', help='Skip confirmation')
    delete_parser.set_defaults(func=checklist_delete_command)

    # checklist update
    update_parser = checklist_subparsers.add_parser(
        'update',
        help='Update a checklist',
        description='Update checklist properties'
    )
    update_parser.add_argument('checklist_id', help='Checklist ID or index (e.g., 1, 2, 3)')
    update_parser.add_argument('--task', help='Task ID (required when using checklist index)')
    update_parser.add_argument('--name', help='New checklist name')
    update_parser.add_argument('--position', type=int, help='New position (order)')
    update_parser.add_argument('--verbose', '-v', action='store_true', help='Show update details')
    update_parser.set_defaults(func=checklist_update_command)

    # checklist list
    list_parser = checklist_subparsers.add_parser(
        'list',
        aliases=['ls'],
        help='List checklists on a task',
        description='List all checklists and items on a task'
    )
    list_parser.add_argument('task_id', help='Task ID (or "current")')
    list_parser.add_argument('--show-ids', action='store_true', help='Show checklist and item IDs')
    list_parser.add_argument('--no-items', action='store_true', help='Hide checklist items, show only checklist names')
    list_parser.add_argument('--colorize', action='store_true', default=True, help='Use colors in output')
    list_parser.set_defaults(func=checklist_list_command)

    # checklist-item add
    item_add_parser = checklist_subparsers.add_parser(
        'item-add',
        aliases=['add'],
        help='Add an item to a checklist',
        description='Add a new item to an existing checklist'
    )
    item_add_parser.add_argument('checklist_id', help='Checklist ID or index (e.g., 1, 2, 3)')
    item_add_parser.add_argument('name', help='Item name')
    item_add_parser.add_argument('--task', help='Task ID (required when using checklist index)')
    item_add_parser.add_argument('--assignee', help='User ID to assign (or "current")')
    item_add_parser.add_argument('--verbose', '-v', action='store_true', help='Show additional information')
    item_add_parser.set_defaults(func=checklist_item_add_command)

    # checklist-item update
    item_update_parser = checklist_subparsers.add_parser(
        'item-update',
        aliases=['update-item'],
        help='Update a checklist item',
        description='Update properties of a checklist item'
    )
    item_update_parser.add_argument('checklist_id', help='Checklist ID or index (e.g., 1, 2, 3)')
    item_update_parser.add_argument('item_id', help='Item ID or index (e.g., 1, 2, 3)')
    item_update_parser.add_argument('--task', help='Task ID (required when using indices)')
    item_update_parser.add_argument('--name', help='New item name')
    item_update_parser.add_argument('--assignee', help='User ID to assign (or empty to unassign)')
    item_update_parser.add_argument('--resolved', type=bool, help='Mark as resolved (true/false)')
    item_update_parser.add_argument('--parent', help='Parent checklist item ID')
    item_update_parser.add_argument('--verbose', '-v', action='store_true', help='Show update details')
    item_update_parser.set_defaults(func=checklist_item_update_command)

    # checklist-item delete
    item_delete_parser = checklist_subparsers.add_parser(
        'item-delete',
        aliases=['delete-item', 'rm-item'],
        help='Delete a checklist item',
        description='Delete a checklist item'
    )
    item_delete_parser.add_argument('checklist_id', help='Checklist ID or index (e.g., 1, 2, 3)')
    item_delete_parser.add_argument('item_id', help='Item ID or index (e.g., 1, 2, 3)')
    item_delete_parser.add_argument('--task', help='Task ID (required when using indices)')
    item_delete_parser.add_argument('--force', '-f', action='store_true', help='Skip confirmation')
    item_delete_parser.set_defaults(func=checklist_item_delete_command)

    # checklist template list
    template_list_parser = checklist_subparsers.add_parser(
        'template',
        help='Manage checklist templates',
        description='List, show, and apply checklist templates'
    )
    template_subparsers = template_list_parser.add_subparsers(dest='template_command', help='Template command')

    # template list
    tpl_list_parser = template_subparsers.add_parser(
        'list',
        aliases=['ls'],
        help='List available checklist templates',
        description='List all available checklist templates'
    )
    tpl_list_parser.set_defaults(func=checklist_template_list_command)

    # template show
    tpl_show_parser = template_subparsers.add_parser(
        'show',
        help='Show template details',
        description='Show details of a specific checklist template'
    )
    tpl_show_parser.add_argument('template_name', help='Template name')
    tpl_show_parser.add_argument('--json', action='store_true', help='Output template as JSON')
    tpl_show_parser.set_defaults(func=checklist_template_show_command)

    # template apply
    tpl_apply_parser = template_subparsers.add_parser(
        'apply',
        help='Apply template to task',
        description='Apply a checklist template to a task'
    )
    tpl_apply_parser.add_argument('task_id', help='Task ID (or "current")')
    tpl_apply_parser.add_argument('template_name', help='Template name')
    tpl_apply_parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed output')
    tpl_apply_parser.set_defaults(func=checklist_template_apply_command)

    # checklist clone
    clone_parser = checklist_subparsers.add_parser(
        'clone',
        help='Clone checklists from one task to another',
        description='Clone all checklists from source task to target task'
    )
    clone_parser.add_argument('source_task_id', help='Source task ID (or "current")')
    clone_parser.add_argument('target_task_id', help='Target task ID')
    clone_parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed output')
    clone_parser.set_defaults(func=checklist_clone_command)
