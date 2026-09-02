"""Space management commands for ClickUp Framework CLI."""

from clickup_framework.commands.base_command import BaseCommand
from clickup_framework.resources.workspaces import WorkspacesAPI
from clickup_framework.utils.colors import colorize, TextColor, TextStyle
from clickup_framework.utils.animations import ANSIAnimations
from clickup_framework.exceptions import ClickUpAPIError
from clickup_framework.commands.utils import add_common_args, parse_bool_flag
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


class SpaceTagListCommand(BaseCommand):
    """List tags defined on a space."""

    def execute(self):
        space_id = self.resolve_id('space', self.args.space_id)
        try:
            response = self.client.get_space_tags(space_id)
            tags = response.get('tags', [])

            header = colorize(f"Space Tags ({len(tags)})", TextColor.BRIGHT_CYAN, TextStyle.BOLD)
            lines = [f"\n{header}"]
            for tag in tags:
                name = colorize(tag.get('name', 'unnamed'), TextColor.BRIGHT_WHITE, TextStyle.BOLD)
                fg = tag.get('tag_fg', 'N/A')
                bg = tag.get('tag_bg', 'N/A')
                lines.append(f"  {name} (fg: {fg}, bg: {bg})")

            self.handle_output(data=tags, console_output="\n".join(lines))
        except ClickUpAPIError as e:
            self.error(f"Error listing space tags: {e}")


class SpaceTagCreateCommand(BaseCommand):
    """Create a tag on a space."""

    def execute(self):
        space_id = self.resolve_id('space', self.args.space_id)
        try:
            self.client.create_space_tag(
                space_id,
                self.args.name,
                tag_fg=self.args.fg or "#000000",
                tag_bg=self.args.bg or "#FFFFFF",
            )
            success_msg = ANSIAnimations.success_message(f"Tag created: {self.args.name}")
            self.handle_output(data={"name": self.args.name}, console_output=f"\n{success_msg}")
        except ClickUpAPIError as e:
            self.error(f"Error creating space tag: {e}")


class SpaceTagUpdateCommand(BaseCommand):
    """Rename or recolor a space tag.

    ClickUp's PUT space/{id}/tag/{name} requires the tag's full
    name+fg_color+bg_color together (and confusingly uses fg_color/
    bg_color here vs tag_fg/tag_bg on create and in the GET response).
    Fetch the current tag first and merge requested changes in.

    Observed live: the rename (name) reliably takes effect, but
    bg_color changes were silently ignored by ClickUp's API in
    testing (200 response, unchanged color on re-fetch) even with a
    correctly-shaped payload verified via a raw client call bypassing
    this command entirely. This looks like a ClickUp-side limitation,
    not something --fg/--bg here can work around.
    """

    def execute(self):
        space_id = self.resolve_id('space', self.args.space_id)

        if not self.args.name and not self.args.fg and not self.args.bg:
            self.error("No updates specified. Use --name, --fg, or --bg")

        try:
            response = self.client.get_space_tags(space_id)
            tags = response.get('tags', [])
            current = next((t for t in tags if t.get('name') == self.args.tag_name), None)
            if current is None:
                self.error(f"Tag '{self.args.tag_name}' not found on space {space_id}")
                return

            tag_payload = {
                'name': self.args.name or current.get('name'),
                'fg_color': self.args.fg or current.get('tag_fg'),
                'bg_color': self.args.bg or current.get('tag_bg'),
            }

            self.client.update_space_tag(space_id, self.args.tag_name, tag=tag_payload)
            success_msg = ANSIAnimations.success_message("Tag updated successfully")
            self.handle_output(data=tag_payload, console_output=f"\n{success_msg}")
        except ClickUpAPIError as e:
            self.error(f"Error updating space tag: {e}")


class SpaceTagDeleteCommand(BaseCommand):
    """Delete a tag from a space."""

    def execute(self):
        space_id = self.resolve_id('space', self.args.space_id)

        if not self.args.force:
            prompt = f"Delete tag '{self.args.tag_name}' from space {space_id}? [y/N]: "
            response = input(prompt)
            if response.lower() not in ['y', 'yes']:
                self.print("Cancelled.")
                return

        try:
            self.client.delete_space_tag(space_id, self.args.tag_name)
            success_msg = ANSIAnimations.success_message("Tag deleted successfully")
            self.handle_output(
                data={"name": self.args.tag_name, "status": "deleted"},
                console_output=f"\n{success_msg}",
            )
        except ClickUpAPIError as e:
            self.error(f"Error deleting space tag: {e}")


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


def space_tag_list_command(args):
    """Command wrapper for space tag list."""
    SpaceTagListCommand(args, command_name='space').execute()


def space_tag_create_command(args):
    """Command wrapper for space tag create."""
    SpaceTagCreateCommand(args, command_name='space').execute()


def space_tag_update_command(args):
    """Command wrapper for space tag update."""
    SpaceTagUpdateCommand(args, command_name='space').execute()


def space_tag_delete_command(args):
    """Command wrapper for space tag delete."""
    SpaceTagDeleteCommand(args, command_name='space').execute()


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
    create_parser.add_argument(
        '--multiple-assignees', type=parse_bool_flag, help='Enable multiple assignees (true/false)'
    )
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
    update_parser.add_argument('--private', type=parse_bool_flag, help='Set private (true/false)')
    update_parser.add_argument(
        '--admin-can-manage', type=parse_bool_flag, help='Admin can manage (true/false)'
    )
    update_parser.add_argument(
        '--multiple-assignees', type=parse_bool_flag, help='Multiple assignees (true/false)'
    )
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

    # space tag <...>
    tag_parser = space_subparsers.add_parser(
        'tag',
        help='Manage tags defined on a space',
        description='Create, rename/recolor, list, and delete tags defined on a space',
    )
    tag_subparsers = tag_parser.add_subparsers(dest='space_tag_command', help='Tag command')

    tag_list_parser = tag_subparsers.add_parser('list', aliases=['l', 'ls'], help='List space tags')
    tag_list_parser.add_argument('space_id', help='Space ID (or "current")')
    add_common_args(tag_list_parser)
    tag_list_parser.set_defaults(func=space_tag_list_command)

    tag_create_parser = tag_subparsers.add_parser(
        'create', aliases=['c'], help='Create a space tag'
    )
    tag_create_parser.add_argument('space_id', help='Space ID (or "current")')
    tag_create_parser.add_argument('name', help='Tag name')
    tag_create_parser.add_argument('--fg', help='Foreground (text) color, hex (default: #000000)')
    tag_create_parser.add_argument('--bg', help='Background color, hex (default: #FFFFFF)')
    add_common_args(tag_create_parser)
    tag_create_parser.set_defaults(func=space_tag_create_command)

    tag_update_parser = tag_subparsers.add_parser(
        'update', aliases=['u'], help='Rename or recolor a space tag'
    )
    tag_update_parser.add_argument('space_id', help='Space ID (or "current")')
    tag_update_parser.add_argument('tag_name', help='Current tag name')
    tag_update_parser.add_argument('--name', help='New tag name')
    tag_update_parser.add_argument('--fg', help='New foreground (text) color, hex')
    tag_update_parser.add_argument('--bg', help='New background color, hex')
    add_common_args(tag_update_parser)
    tag_update_parser.set_defaults(func=space_tag_update_command)

    tag_delete_parser = tag_subparsers.add_parser(
        'delete', aliases=['rm'], help='Delete a space tag'
    )
    tag_delete_parser.add_argument('space_id', help='Space ID (or "current")')
    tag_delete_parser.add_argument('tag_name', help='Tag name')
    tag_delete_parser.add_argument('--force', '-f', action='store_true', help='Skip confirmation')
    add_common_args(tag_delete_parser)
    tag_delete_parser.set_defaults(func=space_tag_delete_command)
