"""Folder management commands for ClickUp Framework CLI."""

from clickup_framework.commands.base_command import BaseCommand
from clickup_framework.resources.workspaces import WorkspacesAPI
from clickup_framework.utils.colors import colorize, TextColor, TextStyle
from clickup_framework.utils.animations import ANSIAnimations
from clickup_framework.exceptions import ClickUpAPIError
from clickup_framework.commands.utils import add_common_args


class FolderCreateCommand(BaseCommand):
    """Create a new folder in a space."""

    def execute(self):
        """Execute the folder create command."""
        workspaces_api = WorkspacesAPI(self.client)

        # Resolve space ID
        space_id = self.resolve_id('space', self.args.space_id)

        # Create the folder
        try:
            new_folder = workspaces_api.create_folder(space_id, self.args.name)

            success_msg = ANSIAnimations.success_message(f"Folder created: {self.args.name}")
            console_out = f"\n{success_msg}\nFolder ID: {colorize(new_folder['id'], TextColor.BRIGHT_GREEN)}"

            if self.args.verbose:
                console_out += f"\nSpace ID: {space_id}"
            
            self.handle_output(data=new_folder, console_output=console_out)

        except ClickUpAPIError as e:
            self.error(f"Error creating folder: {e}")


class FolderCreateFromTemplateCommand(BaseCommand):
    """Create a folder from a ClickUp folder template."""

    def execute(self):
        """Execute the folder create-from-template command."""
        team_id = self.resolve_id('workspace', self.args.team_id)

        try:
            new_folder = self.client.create_folder_from_template(
                team_id,
                self.args.template_id,
                name=self.args.name,
            )

            success_msg = ANSIAnimations.success_message(f"Folder created from template: {self.args.name}")
            console_out = f"\n{success_msg}\nFolder ID: {colorize(new_folder['id'], TextColor.BRIGHT_GREEN)}"

            if self.args.verbose:
                console_out += f"\nWorkspace ID: {team_id}"
                console_out += f"\nTemplate ID: {self.args.template_id}"
            
            self.handle_output(data=new_folder, console_output=console_out)

        except ClickUpAPIError as e:
            self.error(f"Error creating folder from template: {e}")


class FolderUpdateCommand(BaseCommand):
    """Update a folder."""

    def execute(self):
        """Execute the folder update command."""
        workspaces_api = WorkspacesAPI(self.client)

        # Resolve folder ID
        folder_id = self.resolve_id('folder', self.args.folder_id)

        # Build updates
        updates = {}
        if self.args.name:
            updates['name'] = self.args.name

        if not updates:
            self.error("No updates specified. Use --name")

        # Update the folder
        try:
            workspaces_api.update_folder(folder_id, **updates)
            success_msg = ANSIAnimations.success_message("Folder updated successfully")
            
            console_out = f"\n{success_msg}"
            if self.args.verbose:
                console_out += f"\nFolder ID: {folder_id}\nUpdates applied:"
                for key, value in updates.items():
                    console_out += f"\n  {key}: {value}"
            
            self.handle_output(data={"id": folder_id, "updates": updates}, console_output=console_out)

        except ClickUpAPIError as e:
            self.error(f"Error updating folder: {e}")


class FolderDeleteCommand(BaseCommand):
    """Delete a folder."""

    def execute(self):
        """Execute the folder delete command."""
        # Resolve folder ID
        folder_id = self.resolve_id('folder', self.args.folder_id)

        # Show warning
        self.print(f"\n{colorize('Warning:', TextColor.BRIGHT_YELLOW, TextStyle.BOLD)} This will permanently delete the folder and all its lists and tasks.")

        if not self.args.force:
            response = input("Are you sure? [y/N]: ")
            if response.lower() not in ['y', 'yes']:
                self.print("Cancelled.")
                return

        # Delete the folder
        try:
            self.client.delete_folder(folder_id)
            success_msg = ANSIAnimations.success_message("Folder deleted successfully")
            self.handle_output(data={"id": folder_id, "status": "deleted"}, console_output=f"\n{success_msg}")

        except ClickUpAPIError as e:
            self.error(f"Error deleting folder: {e}")


class FolderGetCommand(BaseCommand):
    """Get folder details."""

    def execute(self):
        """Execute the folder get command."""
        # Resolve folder ID
        folder_id = self.resolve_id('folder', self.args.folder_id)

        # Get the folder
        try:
            folder_data = self.client.get_folder(folder_id)

            # Display folder details
            lines = [
                f"\n{colorize(folder_data.get('name', 'Unnamed Folder'), TextColor.BRIGHT_CYAN, TextStyle.BOLD)}",
                f"ID: {colorize(folder_data['id'], TextColor.BRIGHT_GREEN)}"
            ]

            if folder_data.get('space'):
                lines.append(f"Space: {folder_data['space'].get('name', 'N/A')} ({folder_data['space']['id']})")

            # Show lists in folder
            if folder_data.get('lists'):
                list_count = len(folder_data['lists'])
                lines.append(f"\n{colorize(f'Lists ({list_count}):', TextColor.BRIGHT_WHITE, TextStyle.BOLD)}")
                for lst in folder_data['lists']:
                    lines.append(f"  • {lst.get('name', 'Unnamed')} ({lst['id']})")

            if self.args.verbose:
                lines.append(f"\n{colorize('Full Response:', TextColor.BRIGHT_WHITE, TextStyle.BOLD)}")
                import json
                lines.append(json.dumps(folder_data, indent=2))
            
            self.handle_output(data=folder_data, console_output="\n".join(lines))

        except ClickUpAPIError as e:
            self.error(f"Error getting folder: {e}")


# Backward compatibility wrappers
def folder_create_command(args):
    """Command wrapper for folder create."""
    command = FolderCreateCommand(args, command_name='folder')
    command.execute()


def folder_update_command(args):
    """Command wrapper for folder update."""
    command = FolderUpdateCommand(args, command_name='folder')
    command.execute()


def folder_create_from_template_command(args):
    """Command wrapper for folder create-from-template."""
    command = FolderCreateFromTemplateCommand(args, command_name='folder')
    command.execute()


def folder_delete_command(args):
    """Command wrapper for folder delete."""
    command = FolderDeleteCommand(args, command_name='folder')
    command.execute()


def folder_get_command(args):
    """Command wrapper for folder get."""
    command = FolderGetCommand(args, command_name='folder')
    command.execute()


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
    add_common_args(create_parser)
    create_parser.set_defaults(func=folder_create_command)

    # folder create-from-template
    template_parser = folder_subparsers.add_parser(
        'create-from-template',
        help='Create a folder from a folder template',
        description='Create a new folder in a workspace from a ClickUp folder template'
    )
    template_parser.add_argument(
        '--team-id',
        required=True,
        help='Workspace/team ID (or "current") where the folder should be created'
    )
    template_parser.add_argument(
        '--template-id',
        required=True,
        help='Folder template ID to use'
    )
    template_parser.add_argument(
        '--name',
        required=True,
        help='Name for the new folder'
    )
    template_parser.add_argument('--verbose', '-v', action='store_true', help='Show additional information')
    add_common_args(template_parser)
    template_parser.set_defaults(func=folder_create_from_template_command)

    # folder update
    update_parser = folder_subparsers.add_parser(
        'update',
        help='Update a folder',
        description='Update folder properties'
    )
    update_parser.add_argument('folder_id', help='Folder ID (or "current")')
    update_parser.add_argument('--name', help='New folder name')
    update_parser.add_argument('--verbose', '-v', action='store_true', help='Show update details')
    add_common_args(update_parser)
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
    add_common_args(delete_parser)
    delete_parser.set_defaults(func=folder_delete_command)

    # folder get
    get_parser = folder_subparsers.add_parser(
        'get',
        help='Get folder details',
        description='Get detailed information about a folder'
    )
    get_parser.add_argument('folder_id', help='Folder ID (or "current")')
    get_parser.add_argument('--verbose', '-v', action='store_true', help='Show full JSON response')
    add_common_args(get_parser)
    get_parser.set_defaults(func=folder_get_command)
