"""List management commands for ClickUp Framework CLI."""

from clickup_framework.commands.base_command import BaseCommand
from clickup_framework.resources.lists import ListsAPI
from clickup_framework.utils.colors import colorize, TextColor, TextStyle
from clickup_framework.utils.animations import ANSIAnimations
from clickup_framework.exceptions import ClickUpAPIError


class ListCreateCommand(BaseCommand):
    """Create a new list in a folder."""

    def execute(self):
        """Execute the list create command."""
        lists_api = ListsAPI(self.client)

        # Resolve folder ID
        folder_id = self.resolve_id(self.args.folder_id)

        # Build list data
        list_data = {}
        if self.args.content:
            list_data['content'] = self.args.content
        if self.args.due_date:
            list_data['due_date'] = self.args.due_date
        if self.args.priority:
            # Convert priority name to number if needed
            priority_map = {'urgent': 1, 'high': 2, 'normal': 3, 'low': 4}
            if self.args.priority.lower() in priority_map:
                list_data['priority'] = priority_map[self.args.priority.lower()]
            else:
                list_data['priority'] = int(self.args.priority)
        if self.args.status:
            list_data['status'] = self.args.status

        # Create the list
        try:
            new_list = lists_api.create(folder_id, self.args.name, **list_data)

            success_msg = ANSIAnimations.success_message(f"List created: {self.args.name}")
            self.print(f"\n{success_msg}")
            self.print(f"List ID: {colorize(new_list['id'], TextColor.BRIGHT_GREEN)}")

            if self.args.verbose:
                self.print(f"Folder ID: {folder_id}")
                if list_data:
                    self.print("\nProperties set:")
                    for key, value in list_data.items():
                        self.print(f"  {key}: {value}")

        except ClickUpAPIError as e:
            self.error(f"Error creating list: {e}")


class ListUpdateCommand(BaseCommand):
    """Update a list."""

    def execute(self):
        """Execute the list update command."""
        lists_api = ListsAPI(self.client)

        # Resolve list ID
        list_id = self.resolve_id(self.args.list_id)

        # Build updates
        updates = {}
        if self.args.name:
            updates['name'] = self.args.name
        if self.args.content:
            updates['content'] = self.args.content
        if self.args.priority:
            # Convert priority name to number if needed
            priority_map = {'urgent': 1, 'high': 2, 'normal': 3, 'low': 4}
            if self.args.priority.lower() in priority_map:
                updates['priority'] = priority_map[self.args.priority.lower()]
            else:
                updates['priority'] = int(self.args.priority)
        if self.args.status:
            updates['status'] = self.args.status

        if not updates:
            self.error("No updates specified. Use --name, --content, --priority, or --status")

        # Update the list
        try:
            lists_api.update(list_id, **updates)
            success_msg = ANSIAnimations.success_message("List updated successfully")
            self.print(f"\n{success_msg}")

            if self.args.verbose:
                self.print(f"\nList ID: {list_id}")
                self.print("Updates applied:")
                for key, value in updates.items():
                    self.print(f"  {key}: {value}")

        except ClickUpAPIError as e:
            self.error(f"Error updating list: {e}")


class ListDeleteCommand(BaseCommand):
    """Delete a list."""

    def execute(self):
        """Execute the list delete command."""
        # Resolve list ID
        list_id = self.resolve_id(self.args.list_id)

        # Show warning
        self.print(f"\n{colorize('Warning:', TextColor.BRIGHT_YELLOW, TextStyle.BOLD)} This will permanently delete the list and all its tasks.")

        if not self.args.force:
            response = input("Are you sure? [y/N]: ")
            if response.lower() not in ['y', 'yes']:
                self.print("Cancelled.")
                return

        # Delete the list
        try:
            self.client.delete_list(list_id)
            success_msg = ANSIAnimations.success_message("List deleted successfully")
            self.print(f"\n{success_msg}")

        except ClickUpAPIError as e:
            self.error(f"Error deleting list: {e}")


class ListGetCommand(BaseCommand):
    """Get list details."""

    def execute(self):
        """Execute the list get command."""
        lists_api = ListsAPI(self.client)

        # Resolve list ID
        list_id = self.resolve_id(self.args.list_id)

        # Get the list
        try:
            list_data = lists_api.get(list_id)

            # Display list details
            self.print(f"\n{colorize(list_data.get('name', 'Unnamed List'), TextColor.BRIGHT_CYAN, TextStyle.BOLD)}")
            self.print(f"ID: {colorize(list_data['id'], TextColor.BRIGHT_GREEN)}")

            if list_data.get('content'):
                self.print(f"Description: {list_data['content']}")

            if list_data.get('status'):
                self.print(f"Status: {list_data['status'].get('status', 'N/A')}")

            if list_data.get('priority'):
                priority_names = {1: 'Urgent', 2: 'High', 3: 'Normal', 4: 'Low'}
                priority = list_data['priority'].get('priority')
                priority_name = priority_names.get(int(priority), 'Unknown') if priority else 'None'
                self.print(f"Priority: {priority_name}")

            if list_data.get('folder'):
                self.print(f"Folder: {list_data['folder'].get('name', 'N/A')} ({list_data['folder']['id']})")

            if list_data.get('space'):
                self.print(f"Space: {list_data['space'].get('name', 'N/A')} ({list_data['space']['id']})")

            if self.args.verbose:
                self.print(f"\n{colorize('Full Response:', TextColor.BRIGHT_WHITE, TextStyle.BOLD)}")
                import json
                self.print(json.dumps(list_data, indent=2))

        except ClickUpAPIError as e:
            self.error(f"Error getting list: {e}")


# Backward compatibility wrappers
def list_create_command(args):
    """Command wrapper for list create."""
    command = ListCreateCommand(args, command_name='list-mgmt')
    command.execute()


def list_update_command(args):
    """Command wrapper for list update."""
    command = ListUpdateCommand(args, command_name='list-mgmt')
    command.execute()


def list_delete_command(args):
    """Command wrapper for list delete."""
    command = ListDeleteCommand(args, command_name='list-mgmt')
    command.execute()


def list_get_command(args):
    """Command wrapper for list get."""
    command = ListGetCommand(args, command_name='list-mgmt')
    command.execute()


def register_command(subparsers):
    """Register list commands."""
    # Create list subcommand group
    list_parser = subparsers.add_parser(
        'list-mgmt',
        aliases=['lm', 'list_mgmt'],
        help='Manage lists (create, update, delete)',
        description='Manage lists in ClickUp',
        epilog='''Tips:
  • Create list: cum list-mgmt create <folder_id> "My List"
  • Update list: cum list-mgmt update <list_id> --name "New Name"
  • Delete list: cum list-mgmt delete <list_id>
  • Lists contain Tasks and define statuses/workflows
  • Hierarchy: Workspace → Space → Folder → List → Task
  • Use "cum list" or "cum h" to view tasks in a list'''
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
