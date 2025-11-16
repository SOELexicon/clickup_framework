"""Folder management commands for ClickUp Framework CLI."""

import sys
from clickup_framework import ClickUpClient, get_context_manager
from clickup_framework.resources.workspaces import WorkspacesAPI
from clickup_framework.utils.colors import colorize, TextColor, TextStyle
from clickup_framework.utils.animations import ANSIAnimations
from clickup_framework.exceptions import ClickUpAPIError


def folder_create_command(args):
    """Create a new folder in a space."""
    context = get_context_manager()
    client = ClickUpClient()
    workspaces_api = WorkspacesAPI(client)

    # Resolve space ID
    try:
        space_id = context.resolve_id('space', args.space_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Create the folder
    try:
        new_folder = workspaces_api.create_folder(space_id, args.name)

        success_msg = ANSIAnimations.success_message(f"Folder created: {args.name}")
        print(f"\n{success_msg}")
        print(f"Folder ID: {colorize(new_folder['id'], TextColor.BRIGHT_GREEN)}")

        if args.verbose:
            print(f"Space ID: {space_id}")

    except ClickUpAPIError as e:
        print(f"Error creating folder: {e}", file=sys.stderr)
        sys.exit(1)


def folder_update_command(args):
    """Update a folder."""
    context = get_context_manager()
    client = ClickUpClient()
    workspaces_api = WorkspacesAPI(client)

    # Resolve folder ID
    try:
        folder_id = context.resolve_id('folder', args.folder_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Build updates
    updates = {}
    if args.name:
        updates['name'] = args.name

    if not updates:
        print("Error: No updates specified. Use --name", file=sys.stderr)
        sys.exit(1)

    # Update the folder
    try:
        workspaces_api.update_folder(folder_id, **updates)
        success_msg = ANSIAnimations.success_message("Folder updated successfully")
        print(f"\n{success_msg}")

        if args.verbose:
            print(f"\nFolder ID: {folder_id}")
            print("Updates applied:")
            for key, value in updates.items():
                print(f"  {key}: {value}")

    except ClickUpAPIError as e:
        print(f"Error updating folder: {e}", file=sys.stderr)
        sys.exit(1)


def folder_delete_command(args):
    """Delete a folder."""
    context = get_context_manager()
    client = ClickUpClient()

    # Resolve folder ID
    try:
        folder_id = context.resolve_id('folder', args.folder_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Show warning
    print(f"\n{colorize('Warning:', TextColor.BRIGHT_YELLOW, TextStyle.BOLD)} This will permanently delete the folder and all its lists and tasks.")

    if not args.force:
        response = input("Are you sure? [y/N]: ")
        if response.lower() not in ['y', 'yes']:
            print("Cancelled.")
            return

    # Delete the folder
    try:
        client.delete_folder(folder_id)
        success_msg = ANSIAnimations.success_message("Folder deleted successfully")
        print(f"\n{success_msg}")

    except ClickUpAPIError as e:
        print(f"Error deleting folder: {e}", file=sys.stderr)
        sys.exit(1)


def folder_get_command(args):
    """Get folder details."""
    context = get_context_manager()
    client = ClickUpClient()

    # Resolve folder ID
    try:
        folder_id = context.resolve_id('folder', args.folder_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Get the folder
    try:
        folder_data = client.get_folder(folder_id)

        # Display folder details
        print(f"\n{colorize(folder_data.get('name', 'Unnamed Folder'), TextColor.BRIGHT_CYAN, TextStyle.BOLD)}")
        print(f"ID: {colorize(folder_data['id'], TextColor.BRIGHT_GREEN)}")

        if folder_data.get('space'):
            print(f"Space: {folder_data['space'].get('name', 'N/A')} ({folder_data['space']['id']})")

        # Show lists in folder
        if folder_data.get('lists'):
            list_count = len(folder_data['lists'])
            print(f"\n{colorize(f'Lists ({list_count}):', TextColor.BRIGHT_WHITE, TextStyle.BOLD)}")
            for lst in folder_data['lists']:
                print(f"  • {lst.get('name', 'Unnamed')} ({lst['id']})")

        if args.verbose:
            print(f"\n{colorize('Full Response:', TextColor.BRIGHT_WHITE, TextStyle.BOLD)}")
            import json
            print(json.dumps(folder_data, indent=2))

    except ClickUpAPIError as e:
        print(f"Error getting folder: {e}", file=sys.stderr)
        sys.exit(1)


def register_command(subparsers):
    """Register folder commands."""
    # Create folder subcommand group
    folder_parser = subparsers.add_parser(
        'folder',
        aliases=['fld', 'fd'],
        help='Manage folders (create, update, delete)',
        description='Manage folders in ClickUp',
        epilog='''Tips:
  • Create folder: cum folder create <space_id> "My Folder"
  • Update folder: cum folder update <folder_id> --name "New Name"
  • Delete folder: cum folder delete <folder_id>
  • Folders organize Lists within a Space
  • Hierarchy: Workspace → Space → Folder → List
  • Use current context: cum folder create current "Folder Name"'''
    )

    folder_subparsers = folder_parser.add_subparsers(dest='folder_command', help='Folder command')

    # folder create
    create_parser = folder_subparsers.add_parser(
        'create',
        help='Create a new folder in a space',
        description='Create a new folder in a space'
    )
    create_parser.add_argument('space_id', help='Space ID (or "current")')
    create_parser.add_argument('name', help='Folder name')
    create_parser.add_argument('--verbose', '-v', action='store_true', help='Show additional information')
    create_parser.set_defaults(func=folder_create_command)

    # folder update
    update_parser = folder_subparsers.add_parser(
        'update',
        help='Update a folder',
        description='Update folder properties'
    )
    update_parser.add_argument('folder_id', help='Folder ID (or "current")')
    update_parser.add_argument('--name', help='New folder name')
    update_parser.add_argument('--verbose', '-v', action='store_true', help='Show update details')
    update_parser.set_defaults(func=folder_update_command)

    # folder delete
    delete_parser = folder_subparsers.add_parser(
        'delete',
        aliases=['rm'],
        help='Delete a folder',
        description='Delete a folder and all its lists and tasks'
    )
    delete_parser.add_argument('folder_id', help='Folder ID (or "current")')
    delete_parser.add_argument('--force', '-f', action='store_true', help='Skip confirmation')
    delete_parser.set_defaults(func=folder_delete_command)

    # folder get
    get_parser = folder_subparsers.add_parser(
        'get',
        help='Get folder details',
        description='Get detailed information about a folder'
    )
    get_parser.add_argument('folder_id', help='Folder ID (or "current")')
    get_parser.add_argument('--verbose', '-v', action='store_true', help='Show full JSON response')
    get_parser.set_defaults(func=folder_get_command)
