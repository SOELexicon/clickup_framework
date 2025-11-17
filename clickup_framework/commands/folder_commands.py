"""Folder management commands for ClickUp Framework CLI."""

from clickup_framework.commands.base_command import BaseCommand
from clickup_framework.resources.workspaces import WorkspacesAPI
from clickup_framework.utils.colors import colorize, TextColor, TextStyle
from clickup_framework.utils.animations import ANSIAnimations
from clickup_framework.exceptions import ClickUpAPIError


class FolderCreateCommand(BaseCommand):
    """Create a new folder in a space."""

    def execute(self):
        """Execute the folder create command."""
        workspaces_api = WorkspacesAPI(self.client)

        # Resolve space ID
        space_id = self.resolve_id(self.args.space_id)

        # Create the folder
        try:
            new_folder = workspaces_api.create_folder(space_id, self.args.name)

            success_msg = ANSIAnimations.success_message(f"Folder created: {self.args.name}")
            self.print(f"\n{success_msg}")
            self.print(f"Folder ID: {colorize(new_folder['id'], TextColor.BRIGHT_GREEN)}")

            if self.args.verbose:
                self.print(f"Space ID: {space_id}")

        except ClickUpAPIError as e:
            self.error(f"Error creating folder: {e}")


class FolderUpdateCommand(BaseCommand):
    """Update a folder."""

    def execute(self):
        """Execute the folder update command."""
        workspaces_api = WorkspacesAPI(self.client)

        # Resolve folder ID
        folder_id = self.resolve_id(self.args.folder_id)

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
            self.print(f"\n{success_msg}")

            if self.args.verbose:
                self.print(f"\nFolder ID: {folder_id}")
                self.print("Updates applied:")
                for key, value in updates.items():
                    self.print(f"  {key}: {value}")

        except ClickUpAPIError as e:
            self.error(f"Error updating folder: {e}")


class FolderDeleteCommand(BaseCommand):
    """Delete a folder."""

    def execute(self):
        """Execute the folder delete command."""
        # Resolve folder ID
        folder_id = self.resolve_id(self.args.folder_id)

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
            self.print(f"\n{success_msg}")

        except ClickUpAPIError as e:
            self.error(f"Error deleting folder: {e}")


class FolderGetCommand(BaseCommand):
    """Get folder details."""

    def execute(self):
        """Execute the folder get command."""
        # Resolve folder ID
        folder_id = self.resolve_id(self.args.folder_id)

        # Get the folder
        try:
            folder_data = self.client.get_folder(folder_id)

            # Display folder details
            self.print(f"\n{colorize(folder_data.get('name', 'Unnamed Folder'), TextColor.BRIGHT_CYAN, TextStyle.BOLD)}")
            self.print(f"ID: {colorize(folder_data['id'], TextColor.BRIGHT_GREEN)}")

            if folder_data.get('space'):
                self.print(f"Space: {folder_data['space'].get('name', 'N/A')} ({folder_data['space']['id']})")

            # Show lists in folder
            if folder_data.get('lists'):
                list_count = len(folder_data['lists'])
                self.print(f"\n{colorize(f'Lists ({list_count}):', TextColor.BRIGHT_WHITE, TextStyle.BOLD)}")
                for lst in folder_data['lists']:
                    self.print(f"  • {lst.get('name', 'Unnamed')} ({lst['id']})")

            if self.args.verbose:
                self.print(f"\n{colorize('Full Response:', TextColor.BRIGHT_WHITE, TextStyle.BOLD)}")
                import json
                self.print(json.dumps(folder_data, indent=2))

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
