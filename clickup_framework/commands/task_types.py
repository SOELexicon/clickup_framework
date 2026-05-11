"""Task types listing command for ClickUp Framework CLI."""

import sys
from clickup_framework import ClickUpClient, get_context_manager
from clickup_framework.resources import WorkspacesAPI
from clickup_framework.utils.colors import colorize, TextColor, TextStyle
from clickup_framework.utils.animations import ANSIAnimations


def task_types_command(args):
    """List all custom task types for a workspace."""
    context = get_context_manager()
    client = ClickUpClient()
    workspaces_api = WorkspacesAPI(client)

    # Resolve workspace ID
    try:
        workspace_id = context.resolve_id('workspace', args.workspace_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Get task types
    try:
        result = workspaces_api.get_custom_task_types(workspace_id)
        task_types = result.get('custom_items', [])

        if not task_types:
            print("No custom task types found in this workspace")
            return

        # Display header
        use_color = context.get_ansi_output()
        try:
            if use_color:
                header = ANSIAnimations.gradient_text(
                    f"Task Types in Workspace {workspace_id}",
                    ANSIAnimations.GRADIENT_RAINBOW
                )
            else:
                header = f"Task Types in Workspace {workspace_id}"
        except (UnicodeEncodeError, ValueError):
            # Fallback for Windows console encoding issues
            header = colorize(
                f"Task Types in Workspace {workspace_id}",
                TextColor.BRIGHT_CYAN,
                TextStyle.BOLD
            ) if use_color else f"Task Types in Workspace {workspace_id}"
        print(f"\n{header}")
        separator = "-" * 80  # Use ASCII dash for Windows compatibility
        print(colorize(separator, TextColor.BRIGHT_BLACK) if use_color else separator)
        print()

        # Display task types in a table format
        # Header
        if use_color:
            header_row = (
                colorize("ID", TextColor.BRIGHT_CYAN, TextStyle.BOLD) +
                "  " +
                colorize("Name", TextColor.BRIGHT_CYAN, TextStyle.BOLD) +
                "  " +
                colorize("Description", TextColor.BRIGHT_CYAN, TextStyle.BOLD)
            )
        else:
            header_row = "ID  Name  Description"
        print(header_row)
        separator = "-" * 80  # Use ASCII dash for Windows compatibility
        print(colorize(separator, TextColor.BRIGHT_BLACK) if use_color else separator)

        # Display each task type
        for task_type in task_types:
            task_type_id = str(task_type.get('id', 'Unknown'))
            task_type_name = task_type.get('name', 'Unnamed')
            task_type_desc = task_type.get('description') or task_type.get('desc') or 'No description'
            
            # Format the row
            if use_color:
                id_col = colorize(task_type_id, TextColor.BRIGHT_YELLOW)
                name_col = colorize(task_type_name, TextColor.BRIGHT_GREEN, TextStyle.BOLD)
                if task_type_desc == 'No description':
                    desc_col = colorize(task_type_desc, TextColor.BRIGHT_BLACK)
                else:
                    desc_col = colorize(task_type_desc, TextColor.BRIGHT_WHITE)
                row = f"{id_col:20}  {name_col:30}  {desc_col}"
            else:
                row = f"{task_type_id:20}  {task_type_name:30}  {task_type_desc}"
            
            print(row)

        print()
        print(colorize(f"Total: {len(task_types)} task type(s)", TextColor.BRIGHT_BLACK) if use_color else f"Total: {len(task_types)} task type(s)")

    except Exception as e:
        print(f"Error fetching task types: {e}", file=sys.stderr)
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}", file=sys.stderr)
        sys.exit(1)


def task_type_update_command(args):
    """Update a custom task type's description and/or icon."""
    context = get_context_manager()
    client = ClickUpClient()
    workspaces_api = WorkspacesAPI(client)

    # Resolve workspace ID
    try:
        workspace_id = context.resolve_id('workspace', args.workspace_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Validate that at least one update field is provided
    if not args.description and not args.icon and not args.name and not getattr(args, 'name_plural', None):
        print("Error: At least one of --description, --icon, --name, or --name-plural must be provided", file=sys.stderr)
        sys.exit(1)

    # Get color setting
    use_color = context.get_ansi_output()

    # Update task type
    try:
        result = workspaces_api.update_custom_task_type(
            team_id=workspace_id,
            custom_item_id=args.task_type_id,
            name=args.name,
            name_plural=getattr(args, 'name_plural', None),
            description=args.description,
            icon=args.icon
        )
        
        # Display success message
        if use_color:
            success_msg = colorize("✓ Task type updated successfully", TextColor.BRIGHT_GREEN, TextStyle.BOLD)
        else:
            success_msg = "✓ Task type updated successfully"
        print(f"\n{success_msg}")

        # Show what was updated
        updated = result.get('custom_item', result)
        task_type_name = updated.get('name', args.task_type_id)
        separator = "-" * 60
        
        print(f"\nTask Type: {colorize(task_type_name, TextColor.BRIGHT_CYAN, TextStyle.BOLD) if use_color else task_type_name}")
        print(separator)
        
        if args.name:
            print(f"Name: {updated.get('name', 'N/A')}")
        if getattr(args, 'name_plural', None):
            print(f"Plural Name: {updated.get('name_plural', 'N/A')}")
        if args.description:
            print(f"Description: {updated.get('description', 'N/A')}")
        if args.icon:
            # Show avatar info if available
            avatar_source = updated.get('avatar_source', 'N/A')
            avatar_value = updated.get('avatar_value', updated.get('icon', 'N/A'))
            print(f"Icon: {avatar_value} (source: {avatar_source})")

    except Exception as e:
        error_msg = str(e)
        if use_color:
            error_msg = colorize(f"Error updating task type: {error_msg}", TextColor.BRIGHT_RED)
        else:
            error_msg = f"Error updating task type: {error_msg}"
        print(error_msg, file=sys.stderr)
        
        # The client already provides detailed error messages for API limitations
        # Check if it's the specific "Invalid custom item type" error
        if "does not currently support updating custom task types" in error_msg or "Invalid custom item type" in error_msg:
            # Error message already includes instructions, no need to duplicate
            pass
        elif "400" in error_msg and "Invalid custom item type" in error_msg:
            print("\nNote: The ClickUp public API (v2) does not currently support updating custom task types.", file=sys.stderr)
            print("This operation must be performed through the ClickUp web interface:", file=sys.stderr)
            print("  Settings > Task Types > Edit", file=sys.stderr)
        elif "404" in error_msg or "not found" in error_msg.lower():
            print("\nNote: The ClickUp API may not support updating custom task types via API.", file=sys.stderr)
            print("You may need to update task types through the ClickUp web interface:", file=sys.stderr)
            print("  Settings > Task Types > Edit", file=sys.stderr)
        elif "405" in error_msg or "method not allowed" in error_msg.lower():
            print("\nNote: The ClickUp API does not support updating custom task types via API.", file=sys.stderr)
            print("Please update task types through the ClickUp web interface:", file=sys.stderr)
            print("  Settings > Task Types > Edit", file=sys.stderr)
        
        sys.exit(1)


def register_command(subparsers, add_common_args=None):
    """Register the task_types commands with argparse."""
    # List command
    list_parser = subparsers.add_parser(
        'task_types',
        aliases=['tt', 'types'],
        help='List all custom task types for a workspace',
        description='Display all custom task types configured in a ClickUp workspace with their IDs and descriptions'
    )
    list_parser.add_argument(
        'workspace_id',
        nargs='?',
        default='current',
        help='Workspace/team ID (default: use current workspace from context)'
    )
    list_parser.set_defaults(func=task_types_command)

    # Update command
    update_parser = subparsers.add_parser(
        'task_type_update',
        aliases=['ttu', 'type_update'],
        help='Update a custom task type description and/or icon',
        description='Update the description, icon, or name of a custom task type'
    )
    update_parser.add_argument(
        'task_type_id',
        help='Custom task type ID to update'
    )
    update_parser.add_argument(
        '--workspace-id',
        dest='workspace_id',
        default='current',
        help='Workspace/team ID (default: use current workspace from context)'
    )
    update_parser.add_argument(
        '--name',
        help='New name for the task type'
    )
    update_parser.add_argument(
        '--description',
        help='New description for the task type'
    )
    update_parser.add_argument(
        '--icon',
        help='New icon for the task type (Font Awesome icon name, e.g., bug, rocket, youtube, code)'
    )
    update_parser.add_argument(
        '--name-plural',
        dest='name_plural',
        help='New plural name for the task type (defaults to name + "s" if not provided)'
    )
    update_parser.set_defaults(func=task_type_update_command)

