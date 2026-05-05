"""Space management commands for ClickUp Framework CLI."""

from clickup_framework.commands.base_command import BaseCommand
from clickup_framework.resources.workspaces import WorkspacesAPI
from clickup_framework.utils.colors import colorize, TextColor, TextStyle
from clickup_framework.utils.animations import ANSIAnimations
from clickup_framework.exceptions import ClickUpAPIError
from clickup_framework.commands.utils import add_common_args
from clickup_framework.formatters.workspace import SpaceFormatter


class SpaceCreateCommand(BaseCommand):
    """Create a new space in a workspace/team."""

    def execute(self):
        """Execute the space create command."""
        workspaces_api = WorkspacesAPI(self.client)

        # Resolve team/workspace ID
        team_id = self.resolve_id('workspace', self.args.team_id)

        # Build space data
        space_data = {}
        if self.args.multiple_assignees is not None:
            space_data['multiple_assignees'] = self.args.multiple_assignees
        if self.args.features:
            space_data['features'] = {}
            if 'due_dates' in self.args.features:
                space_data['features']['due_dates'] = {'enabled': True}
            if 'time_tracking' in self.args.features:
                space_data['features']['time_tracking'] = {'enabled': True}
            if 'tags' in self.args.features:
                space_data['features']['tags'] = {'enabled': True}
            if 'time_estimates' in self.args.features:
                space_data['features']['time_estimates'] = {'enabled': True}
            if 'checklists' in self.args.features:
                space_data['features']['checklists'] = {'enabled': True}
            if 'custom_fields' in self.args.features:
                space_data['features']['custom_fields'] = {'enabled': True}
            if 'remap_dependencies' in self.args.features:
                space_data['features']['dependency_warning'] = {'enabled': True}
            if 'remap_closed_due_date' in self.args.features:
                space_data['features']['remap_closed_due_date'] = {'enabled': True}

        # Create the space
        try:
            new_space = workspaces_api.create_space(team_id, self.args.name, **space_data)

            success_msg = ANSIAnimations.success_message(f"Space created: {self.args.name}")
            console_out = f"\n{success_msg}\nSpace ID: {colorize(new_space['id'], TextColor.BRIGHT_GREEN)}"
            
            self.handle_output(data=new_space, formatter=SpaceFormatter(), console_output=console_out)

        except ClickUpAPIError as e:
            self.error(f"Error creating space: {e}")


class SpaceUpdateCommand(BaseCommand):
    """Update a space."""

    def execute(self):
        """Execute the space update command."""
        workspaces_api = WorkspacesAPI(self.client)

        # Resolve space ID
        space_id = self.resolve_id('space', self.args.space_id)

        # Build updates
        updates = {}
        if self.args.name:
            updates['name'] = self.args.name
        if self.args.color:
            updates['color'] = self.args.color
        if self.args.private is not None:
            updates['private'] = self.args.private
        if self.args.admin_can_manage is not None:
            updates['admin_can_manage'] = self.args.admin_can_manage
        if self.args.multiple_assignees is not None:
            updates['multiple_assignees'] = self.args.multiple_assignees

        if not updates:
            self.error("No updates specified. Use --name, --color, --private, --admin-can-manage, or --multiple-assignees")

        # Update the space
        try:
            workspaces_api.update_space(space_id, **updates)
            # Fetch updated space for output
            updated_space = self.client.get_space(space_id)
            
            success_msg = ANSIAnimations.success_message("Space updated successfully")
            self.handle_output(data=updated_space, formatter=SpaceFormatter(), console_output=f"\n{success_msg}")

        except ClickUpAPIError as e:
            self.error(f"Error updating space: {e}")


class SpaceDeleteCommand(BaseCommand):
    """Delete a space."""

    def execute(self):
        """Execute the space delete command."""
        # Resolve space ID
        space_id = self.resolve_id('space', self.args.space_id)

        # Show warning
        self.print(f"\n{colorize('Warning:', TextColor.BRIGHT_YELLOW, TextStyle.BOLD)} This will permanently delete the space and all its folders, lists, and tasks.")

        if not self.args.force:
            response = input("Are you sure? [y/N]: ")
            if response.lower() not in ['y', 'yes']:
                self.print("Cancelled.")
                return

        # Delete the space
        try:
            self.client.delete_space(space_id)
            success_msg = ANSIAnimations.success_message("Space deleted successfully")
            self.handle_output(data={"id": space_id, "status": "deleted"}, console_output=f"\n{success_msg}")

        except ClickUpAPIError as e:
            self.error(f"Error deleting space: {e}")


class SpaceGetCommand(BaseCommand):
    """Get space details."""

    def execute(self):
        """Execute the space get command."""
        # Resolve space ID
        space_id = self.resolve_id('space', self.args.space_id)

        # Get the space
        try:
            space_data = self.client.get_space(space_id)
            self.handle_output(data=space_data, formatter=SpaceFormatter(), detail_level=getattr(self.args, 'preset', 'summary'))

        except ClickUpAPIError as e:
            self.error(f"Error getting space: {e}")


class SpaceListCommand(BaseCommand):
    """List all spaces in a workspace/team."""

    def execute(self):
        """Execute the space list command."""
        # Resolve team/workspace ID
        team_id = self.resolve_id('workspace', self.args.team_id)

        # Get spaces
        try:
            spaces_data = self.client.get_team_spaces(team_id, archived=self.args.archived)
            spaces = spaces_data.get('spaces', [])
            self.handle_output(data=spaces, formatter=SpaceFormatter(), detail_level=getattr(self.args, 'preset', 'summary'))

        except ClickUpAPIError as e:
            self.error(f"Error listing spaces: {e}")


# Backward compatibility wrappers
def space_create_command(args):
    """Command wrapper for space create."""
    command = SpaceCreateCommand(args, command_name='space')
    command.execute()


def space_update_command(args):
    """Command wrapper for space update."""
    command = SpaceUpdateCommand(args, command_name='space')
    command.execute()


def space_delete_command(args):
    """Command wrapper for space delete."""
    command = SpaceDeleteCommand(args, command_name='space')
    command.execute()


def space_get_command(args):
    """Command wrapper for space get."""
    command = SpaceGetCommand(args, command_name='space')
    command.execute()


def space_list_command(args):
    """Command wrapper for space list."""
    command = SpaceListCommand(args, command_name='space')
    command.execute()


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

    add_common_args(space_parser)
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
    add_common_args(create_parser)
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
    add_common_args(update_parser)
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
    add_common_args(delete_parser)
    delete_parser.set_defaults(func=space_delete_command)

    # space get
    get_parser = space_subparsers.add_parser(
        'get',
        help='Get space details',
        description='Get detailed information about a space'
    )
    get_parser.add_argument('space_id', help='Space ID (or "current")')
    get_parser.add_argument('--verbose', '-v', action='store_true', help='Show full JSON response')
    add_common_args(get_parser)
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
    add_common_args(list_parser)
    list_parser.set_defaults(func=space_list_command)
