"""Checklist management commands for ClickUp Framework CLI."""

import sys
from clickup_framework import ClickUpClient, get_context_manager
from clickup_framework.resources.tasks import TasksAPI
from clickup_framework.utils.colors import colorize, TextColor, TextStyle
from clickup_framework.utils.animations import ANSIAnimations
from clickup_framework.exceptions import ClickUpAPIError


def checklist_create_command(args):
    """Create a new checklist on a task."""
    context = get_context_manager()
    client = ClickUpClient()
    tasks_api = TasksAPI(client)

    # Resolve task ID
    try:
        task_id = context.resolve_id('task', args.task_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Create the checklist
    try:
        checklist = tasks_api.add_checklist(task_id, args.name)

        success_msg = ANSIAnimations.success_message(f"Checklist created: {args.name}")
        print(f"\n{success_msg}")
        print(f"Checklist ID: {colorize(checklist['checklist']['id'], TextColor.BRIGHT_GREEN)}")

        if args.verbose:
            print(f"\nTask ID: {task_id}")

    except ClickUpAPIError as e:
        print(f"Error creating checklist: {e}", file=sys.stderr)
        sys.exit(1)


def checklist_delete_command(args):
    """Delete a checklist."""
    client = ClickUpClient()

    # Show warning
    print(f"\n{colorize('Warning:', TextColor.BRIGHT_YELLOW, TextStyle.BOLD)} This will permanently delete the checklist and all its items.")

    if not args.force:
        response = input("Are you sure? [y/N]: ")
        if response.lower() not in ['y', 'yes']:
            print("Cancelled.")
            return

    # Delete the checklist
    try:
        client.delete_checklist(args.checklist_id)
        success_msg = ANSIAnimations.success_message("Checklist deleted successfully")
        print(f"\n{success_msg}")

    except ClickUpAPIError as e:
        print(f"Error deleting checklist: {e}", file=sys.stderr)
        sys.exit(1)


def checklist_update_command(args):
    """Update a checklist."""
    client = ClickUpClient()

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
        client.update_checklist(args.checklist_id, **updates)
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
        result = tasks_api.add_checklist_item(args.checklist_id, args.name, assignee=assignee)

        success_msg = ANSIAnimations.success_message(f"Checklist item added: {args.name}")
        print(f"\n{success_msg}")

        # The API returns: {"checklist": {"items": [...]}}
        # The new item is the last one in the items array
        if isinstance(result, dict) and 'checklist' in result:
            items = result.get('checklist', {}).get('items', [])
            if items:
                item_id = items[-1].get('id', 'Unknown')
                print(f"Item ID: {colorize(str(item_id), TextColor.BRIGHT_GREEN)}")

        if assignee:
            print(f"Assigned to: {assignee}")

        if args.verbose:
            print(f"\nChecklist ID: {args.checklist_id}")

    except ClickUpAPIError as e:
        print(f"Error adding checklist item: {e}", file=sys.stderr)
        sys.exit(1)


def checklist_item_update_command(args):
    """Update a checklist item."""
    client = ClickUpClient()

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
        client.update_checklist_item(args.checklist_id, args.item_id, **updates)
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
    client = ClickUpClient()

    if not args.force:
        response = input(f"Delete checklist item {args.item_id}? [y/N]: ")
        if response.lower() not in ['y', 'yes']:
            print("Cancelled.")
            return

    # Delete the checklist item
    try:
        client.delete_checklist_item(args.checklist_id, args.item_id)
        success_msg = ANSIAnimations.success_message("Checklist item deleted successfully")
        print(f"\n{success_msg}")

    except ClickUpAPIError as e:
        print(f"Error deleting checklist item: {e}", file=sys.stderr)
        sys.exit(1)


def checklist_list_command(args):
    """List checklists on a task."""
    context = get_context_manager()
    client = ClickUpClient()

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

        # Display checklists
        print(f"\n{colorize('Checklists', TextStyle.BOLD)} for task {task['name']}")
        print(f"Task ID: {task_id}\n")

        for checklist in checklists:
            checklist_id = checklist.get('id', 'Unknown')
            checklist_name = checklist.get('name', 'Unnamed')
            items = checklist.get('items', [])
            resolved_count = sum(1 for item in items if item.get('resolved', False))
            total_count = len(items)

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

            print(f"☑️  {colorize(checklist_name, TextStyle.BOLD)} {progress_str}")

            if args.show_ids:
                print(f"    ID: {colorize(checklist_id, TextColor.BRIGHT_BLACK)}")

            # List items
            if items and not args.no_items:
                for item in items:
                    item_name = item.get('name', 'Unnamed')
                    resolved = item.get('resolved', False)
                    assignee = item.get('assignee')

                    # Checkbox indicator
                    checkbox = "✓" if resolved else "☐"
                    if args.colorize:
                        checkbox_color = TextColor.BRIGHT_GREEN if resolved else TextColor.BRIGHT_BLACK
                        checkbox = colorize(checkbox, checkbox_color)

                    item_str = f"    {checkbox} {item_name}"

                    if assignee:
                        assignee_name = assignee.get('username', 'Unknown')
                        item_str += f" [@{assignee_name}]"

                    if args.show_ids:
                        item_id = item.get('id', 'Unknown')
                        item_str += f" {colorize(f'({item_id})', TextColor.BRIGHT_BLACK)}"

                    print(item_str)

            print()  # Blank line between checklists

    except ClickUpAPIError as e:
        print(f"Error listing checklists: {e}", file=sys.stderr)
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
    delete_parser.add_argument('checklist_id', help='Checklist ID')
    delete_parser.add_argument('--force', '-f', action='store_true', help='Skip confirmation')
    delete_parser.set_defaults(func=checklist_delete_command)

    # checklist update
    update_parser = checklist_subparsers.add_parser(
        'update',
        help='Update a checklist',
        description='Update checklist properties'
    )
    update_parser.add_argument('checklist_id', help='Checklist ID')
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
    item_add_parser.add_argument('checklist_id', help='Checklist ID')
    item_add_parser.add_argument('name', help='Item name')
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
    item_update_parser.add_argument('checklist_id', help='Checklist ID')
    item_update_parser.add_argument('item_id', help='Item ID')
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
    item_delete_parser.add_argument('checklist_id', help='Checklist ID')
    item_delete_parser.add_argument('item_id', help='Item ID')
    item_delete_parser.add_argument('--force', '-f', action='store_true', help='Skip confirmation')
    item_delete_parser.set_defaults(func=checklist_item_delete_command)
