"""Space management commands for ClickUp Framework CLI."""

import sys
from clickup_framework import ClickUpClient, get_context_manager
from clickup_framework.resources.workspaces import WorkspacesAPI
from clickup_framework.utils.colors import colorize, TextColor, TextStyle
from clickup_framework.utils.animations import ANSIAnimations
from clickup_framework.exceptions import ClickUpAPIError


def space_create_command(args):
    """Create a new space in a workspace/team."""
    context = get_context_manager()
    client = ClickUpClient()
    workspaces_api = WorkspacesAPI(client)

    # Resolve team/workspace ID
    try:
        team_id = context.resolve_id('workspace', args.team_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Build space data
    space_data = {}
    if args.multiple_assignees is not None:
        space_data['multiple_assignees'] = args.multiple_assignees
    if args.features:
        space_data['features'] = {}
        if 'due_dates' in args.features:
            space_data['features']['due_dates'] = {'enabled': True}
        if 'time_tracking' in args.features:
            space_data['features']['time_tracking'] = {'enabled': True}
        if 'tags' in args.features:
            space_data['features']['tags'] = {'enabled': True}
        if 'time_estimates' in args.features:
            space_data['features']['time_estimates'] = {'enabled': True}
        if 'checklists' in args.features:
            space_data['features']['checklists'] = {'enabled': True}
        if 'custom_fields' in args.features:
            space_data['features']['custom_fields'] = {'enabled': True}
        if 'remap_dependencies' in args.features:
            space_data['features']['dependency_warning'] = {'enabled': True}
        if 'remap_closed_due_date' in args.features:
            space_data['features']['remap_closed_due_date'] = {'enabled': True}

    # Create the space
    try:
        new_space = workspaces_api.create_space(team_id, args.name, **space_data)

        success_msg = ANSIAnimations.success_message(f"Space created: {args.name}")
        print(f"\n{success_msg}")
        print(f"Space ID: {colorize(new_space['id'], TextColor.BRIGHT_GREEN)}")

        if args.verbose:
            print(f"Team/Workspace ID: {team_id}")
            if space_data:
                print("\nFeatures configured:")
                for key, value in space_data.items():
                    print(f"  {key}: {value}")

    except ClickUpAPIError as e:
        print(f"Error creating space: {e}", file=sys.stderr)
        sys.exit(1)


def space_update_command(args):
    """Update a space."""
    context = get_context_manager()
    client = ClickUpClient()
    workspaces_api = WorkspacesAPI(client)

    # Resolve space ID
    try:
        space_id = context.resolve_id('space', args.space_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Build updates
    updates = {}
    if args.name:
        updates['name'] = args.name
    if args.color:
        updates['color'] = args.color
    if args.private is not None:
        updates['private'] = args.private
    if args.admin_can_manage is not None:
        updates['admin_can_manage'] = args.admin_can_manage
    if args.multiple_assignees is not None:
        updates['multiple_assignees'] = args.multiple_assignees

    if not updates:
        print("Error: No updates specified. Use --name, --color, --private, --admin-can-manage, or --multiple-assignees", file=sys.stderr)
        sys.exit(1)

    # Update the space
    try:
        workspaces_api.update_space(space_id, **updates)
        success_msg = ANSIAnimations.success_message("Space updated successfully")
        print(f"\n{success_msg}")

        if args.verbose:
            print(f"\nSpace ID: {space_id}")
            print("Updates applied:")
            for key, value in updates.items():
                print(f"  {key}: {value}")

    except ClickUpAPIError as e:
        print(f"Error updating space: {e}", file=sys.stderr)
        sys.exit(1)


def space_delete_command(args):
    """Delete a space."""
    context = get_context_manager()
    client = ClickUpClient()

    # Resolve space ID
    try:
        space_id = context.resolve_id('space', args.space_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Show warning
    print(f"\n{colorize('Warning:', TextColor.BRIGHT_YELLOW, TextStyle.BOLD)} This will permanently delete the space and all its folders, lists, and tasks.")

    if not args.force:
        response = input("Are you sure? [y/N]: ")
        if response.lower() not in ['y', 'yes']:
            print("Cancelled.")
            return

    # Delete the space
    try:
        client.delete_space(space_id)
        success_msg = ANSIAnimations.success_message("Space deleted successfully")
        print(f"\n{success_msg}")

    except ClickUpAPIError as e:
        print(f"Error deleting space: {e}", file=sys.stderr)
        sys.exit(1)


def space_get_command(args):
    """Get space details."""
    context = get_context_manager()
    client = ClickUpClient()

    # Resolve space ID
    try:
        space_id = context.resolve_id('space', args.space_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Get the space
    try:
        space_data = client.get_space(space_id)

        # Display space details
        print(f"\n{colorize(space_data.get('name', 'Unnamed Space'), TextColor.BRIGHT_CYAN, TextStyle.BOLD)}")
        print(f"ID: {colorize(space_data['id'], TextColor.BRIGHT_GREEN)}")

        if space_data.get('private'):
            print(f"Privacy: Private")
        else:
            print(f"Privacy: Public")

        if space_data.get('multiple_assignees'):
            print(f"Multiple Assignees: Enabled")

        # Show features
        if space_data.get('features'):
            print(f"\n{colorize('Features:', TextColor.BRIGHT_WHITE, TextStyle.BOLD)}")
            features = space_data['features']
            for feature_name, feature_data in features.items():
                if isinstance(feature_data, dict) and feature_data.get('enabled'):
                    print(f"  ✓ {feature_name.replace('_', ' ').title()}")

        # Show folders
        if space_data.get('folders'):
            folder_count = len(space_data['folders'])
            print(f"\n{colorize(f'Folders ({folder_count}):', TextColor.BRIGHT_WHITE, TextStyle.BOLD)}")
            for folder in space_data['folders']:
                print(f"  • {folder.get('name', 'Unnamed')} ({folder['id']})")

        if args.verbose:
            print(f"\n{colorize('Full Response:', TextColor.BRIGHT_WHITE, TextStyle.BOLD)}")
            import json
            print(json.dumps(space_data, indent=2))

    except ClickUpAPIError as e:
        print(f"Error getting space: {e}", file=sys.stderr)
        sys.exit(1)


def space_list_command(args):
    """List all spaces in a workspace/team."""
    context = get_context_manager()
    client = ClickUpClient()

    # Resolve team/workspace ID
    try:
        team_id = context.resolve_id('workspace', args.team_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Get spaces
    try:
        spaces_data = client.get_team_spaces(team_id, archived=args.archived)
        spaces = spaces_data.get('spaces', [])

        space_count = len(spaces)
        print(f"\n{colorize(f'Spaces in Workspace ({space_count}):', TextColor.BRIGHT_CYAN, TextStyle.BOLD)}")
        print()

        for space in spaces:
            privacy = "🔒 Private" if space.get('private') else "🌐 Public"
            print(f"{colorize(space.get('name', 'Unnamed'), TextColor.BRIGHT_GREEN)} {privacy}")
            print(f"  ID: {colorize(space['id'], TextColor.BRIGHT_BLACK)}")

            if space.get('folders'):
                print(f"  Folders: {len(space['folders'])}")

            if args.show_details:
                if space.get('statuses'):
                    print(f"  Statuses: {', '.join([s['status'] for s in space['statuses']])}")

            print()

    except ClickUpAPIError as e:
        print(f"Error listing spaces: {e}", file=sys.stderr)
        sys.exit(1)


def register_command(subparsers):
    """Register space commands."""
    # Create space subcommand group
    space_parser = subparsers.add_parser(
        'space',
        aliases=['sp', 'spc'],
        help='Manage spaces (create, update, delete, list)',
        description='Manage spaces in ClickUp',
        epilog='''Tips:
  • Create space: cum space create current "My Space"
  • Update space: cum space update <space_id> --name "New Name"
  • Delete space: cum space delete <space_id>
  • List spaces: cum space list current
  • Spaces contain Folders, which contain Lists
  • Use --verbose for detailed output'''
    )

    space_subparsers = space_parser.add_subparsers(dest='space_command', help='Space command')

    # space create
    create_parser = space_subparsers.add_parser(
        'create',
        help='Create a new space in a workspace',
        description='Create a new space in a workspace/team'
    )
    create_parser.add_argument('team_id', help='Team/Workspace ID (or "current")')
    create_parser.add_argument('name', help='Space name')
    create_parser.add_argument('--multiple-assignees', type=bool, help='Enable multiple assignees (true/false)')
    create_parser.add_argument('--features', nargs='+',
                               choices=['due_dates', 'time_tracking', 'tags', 'time_estimates',
                                       'checklists', 'custom_fields', 'remap_dependencies',
                                       'remap_closed_due_date'],
                               help='Features to enable')
    create_parser.add_argument('--verbose', '-v', action='store_true', help='Show additional information')
    create_parser.set_defaults(func=space_create_command)

    # space update
    update_parser = space_subparsers.add_parser(
        'update',
        help='Update a space',
        description='Update space properties'
    )
    update_parser.add_argument('space_id', help='Space ID (or "current")')
    update_parser.add_argument('--name', help='New space name')
    update_parser.add_argument('--color', help='Space color (hex code)')
    update_parser.add_argument('--private', type=bool, help='Set private (true/false)')
    update_parser.add_argument('--admin-can-manage', type=bool, help='Admin can manage (true/false)')
    update_parser.add_argument('--multiple-assignees', type=bool, help='Multiple assignees (true/false)')
    update_parser.add_argument('--verbose', '-v', action='store_true', help='Show update details')
    update_parser.set_defaults(func=space_update_command)

    # space delete
    delete_parser = space_subparsers.add_parser(
        'delete',
        aliases=['rm'],
        help='Delete a space',
        description='Delete a space and all its contents'
    )
    delete_parser.add_argument('space_id', help='Space ID (or "current")')
    delete_parser.add_argument('--force', '-f', action='store_true', help='Skip confirmation')
    delete_parser.set_defaults(func=space_delete_command)

    # space get
    get_parser = space_subparsers.add_parser(
        'get',
        help='Get space details',
        description='Get detailed information about a space'
    )
    get_parser.add_argument('space_id', help='Space ID (or "current")')
    get_parser.add_argument('--verbose', '-v', action='store_true', help='Show full JSON response')
    get_parser.set_defaults(func=space_get_command)

    # space list
    list_parser = space_subparsers.add_parser(
        'list',
        aliases=['ls'],
        help='List all spaces in a workspace',
        description='List all spaces in a workspace/team'
    )
    list_parser.add_argument('team_id', help='Team/Workspace ID (or "current")')
    list_parser.add_argument('--archived', action='store_true', help='Include archived spaces')
    list_parser.add_argument('--show-details', action='store_true', help='Show additional details')
    list_parser.set_defaults(func=space_list_command)
