"""List management commands for ClickUp Framework CLI."""

import sys
from clickup_framework import ClickUpClient, get_context_manager
from clickup_framework.resources.lists import ListsAPI
from clickup_framework.utils.colors import colorize, TextColor, TextStyle
from clickup_framework.utils.animations import ANSIAnimations
from clickup_framework.exceptions import ClickUpAPIError


def list_create_command(args):
    """Create a new list in a folder."""
    context = get_context_manager()
    client = ClickUpClient()
    lists_api = ListsAPI(client)

    # Resolve folder ID
    try:
        folder_id = context.resolve_id('folder', args.folder_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Build list data
    list_data = {}
    if args.content:
        list_data['content'] = args.content
    if args.due_date:
        list_data['due_date'] = args.due_date
    if args.priority:
        # Convert priority name to number if needed
        priority_map = {'urgent': 1, 'high': 2, 'normal': 3, 'low': 4}
        if args.priority.lower() in priority_map:
            list_data['priority'] = priority_map[args.priority.lower()]
        else:
            list_data['priority'] = int(args.priority)
    if args.status:
        list_data['status'] = args.status

    # Create the list
    try:
        new_list = lists_api.create(folder_id, args.name, **list_data)

        success_msg = ANSIAnimations.success_message(f"List created: {args.name}")
        print(f"\n{success_msg}")
        print(f"List ID: {colorize(new_list['id'], TextColor.BRIGHT_GREEN)}")

        if args.verbose:
            print(f"Folder ID: {folder_id}")
            if list_data:
                print("\nProperties set:")
                for key, value in list_data.items():
                    print(f"  {key}: {value}")

    except ClickUpAPIError as e:
        print(f"Error creating list: {e}", file=sys.stderr)
        sys.exit(1)


def list_update_command(args):
    """Update a list."""
    context = get_context_manager()
    client = ClickUpClient()
    lists_api = ListsAPI(client)

    # Resolve list ID
    try:
        list_id = context.resolve_id('list', args.list_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Build updates
    updates = {}
    if args.name:
        updates['name'] = args.name
    if args.content:
        updates['content'] = args.content
    if args.priority:
        # Convert priority name to number if needed
        priority_map = {'urgent': 1, 'high': 2, 'normal': 3, 'low': 4}
        if args.priority.lower() in priority_map:
            updates['priority'] = priority_map[args.priority.lower()]
        else:
            updates['priority'] = int(args.priority)
    if args.status:
        updates['status'] = args.status

    if not updates:
        print("Error: No updates specified. Use --name, --content, --priority, or --status", file=sys.stderr)
        sys.exit(1)

    # Update the list
    try:
        lists_api.update(list_id, **updates)
        success_msg = ANSIAnimations.success_message("List updated successfully")
        print(f"\n{success_msg}")

        if args.verbose:
            print(f"\nList ID: {list_id}")
            print("Updates applied:")
            for key, value in updates.items():
                print(f"  {key}: {value}")

    except ClickUpAPIError as e:
        print(f"Error updating list: {e}", file=sys.stderr)
        sys.exit(1)


def list_delete_command(args):
    """Delete a list."""
    context = get_context_manager()
    client = ClickUpClient()

    # Resolve list ID
    try:
        list_id = context.resolve_id('list', args.list_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Show warning
    print(f"\n{colorize('Warning:', TextColor.BRIGHT_YELLOW, TextStyle.BOLD)} This will permanently delete the list and all its tasks.")

    if not args.force:
        response = input("Are you sure? [y/N]: ")
        if response.lower() not in ['y', 'yes']:
            print("Cancelled.")
            return

    # Delete the list
    try:
        client.delete_list(list_id)
        success_msg = ANSIAnimations.success_message("List deleted successfully")
        print(f"\n{success_msg}")

    except ClickUpAPIError as e:
        print(f"Error deleting list: {e}", file=sys.stderr)
        sys.exit(1)


def list_get_command(args):
    """Get list details."""
    context = get_context_manager()
    client = ClickUpClient()
    lists_api = ListsAPI(client)

    # Resolve list ID
    try:
        list_id = context.resolve_id('list', args.list_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Get the list
    try:
        list_data = lists_api.get(list_id)

        # Display list details
        print(f"\n{colorize(list_data.get('name', 'Unnamed List'), TextColor.BRIGHT_CYAN, TextStyle.BOLD)}")
        print(f"ID: {colorize(list_data['id'], TextColor.BRIGHT_GREEN)}")

        if list_data.get('content'):
            print(f"Description: {list_data['content']}")

        if list_data.get('status'):
            print(f"Status: {list_data['status'].get('status', 'N/A')}")

        if list_data.get('priority'):
            priority_names = {1: 'Urgent', 2: 'High', 3: 'Normal', 4: 'Low'}
            priority = list_data['priority'].get('priority')
            priority_name = priority_names.get(int(priority), 'Unknown') if priority else 'None'
            print(f"Priority: {priority_name}")

        if list_data.get('folder'):
            print(f"Folder: {list_data['folder'].get('name', 'N/A')} ({list_data['folder']['id']})")

        if list_data.get('space'):
            print(f"Space: {list_data['space'].get('name', 'N/A')} ({list_data['space']['id']})")

        if args.verbose:
            print(f"\n{colorize('Full Response:', TextColor.BRIGHT_WHITE, TextStyle.BOLD)}")
            import json
            print(json.dumps(list_data, indent=2))

    except ClickUpAPIError as e:
        print(f"Error getting list: {e}", file=sys.stderr)
        sys.exit(1)


def register_command(subparsers):
    """Register list commands."""
    # Create list subcommand group
    list_parser = subparsers.add_parser(
        'list-mgmt',
        aliases=['lm', 'list_mgmt'],
        help='Manage lists (create, update, delete)',
        description='Manage lists in ClickUp'
    )

    list_subparsers = list_parser.add_subparsers(dest='list_command', help='List command')

    # list create
    create_parser = list_subparsers.add_parser(
        'create',
        help='Create a new list in a folder',
        description='Create a new list in a folder'
    )
    create_parser.add_argument('folder_id', help='Folder ID (or "current")')
    create_parser.add_argument('name', help='List name')
    create_parser.add_argument('--content', help='List description')
    create_parser.add_argument('--due-date', type=int, help='Due date (Unix timestamp in milliseconds)')
    create_parser.add_argument('--priority', help='Priority (1-4 or urgent/high/normal/low)')
    create_parser.add_argument('--status', help='Initial status')
    create_parser.add_argument('--verbose', '-v', action='store_true', help='Show additional information')
    create_parser.set_defaults(func=list_create_command)

    # list update
    update_parser = list_subparsers.add_parser(
        'update',
        help='Update a list',
        description='Update list properties'
    )
    update_parser.add_argument('list_id', help='List ID (or "current")')
    update_parser.add_argument('--name', help='New list name')
    update_parser.add_argument('--content', help='New list description')
    update_parser.add_argument('--priority', help='Priority (1-4 or urgent/high/normal/low)')
    update_parser.add_argument('--status', help='Status')
    update_parser.add_argument('--verbose', '-v', action='store_true', help='Show update details')
    update_parser.set_defaults(func=list_update_command)

    # list delete
    delete_parser = list_subparsers.add_parser(
        'delete',
        aliases=['rm'],
        help='Delete a list',
        description='Delete a list and all its tasks'
    )
    delete_parser.add_argument('list_id', help='List ID (or "current")')
    delete_parser.add_argument('--force', '-f', action='store_true', help='Skip confirmation')
    delete_parser.set_defaults(func=list_delete_command)

    # list get
    get_parser = list_subparsers.add_parser(
        'get',
        help='Get list details',
        description='Get detailed information about a list'
    )
    get_parser.add_argument('list_id', help='List ID (or "current")')
    get_parser.add_argument('--verbose', '-v', action='store_true', help='Show full JSON response')
    get_parser.set_defaults(func=list_get_command)
