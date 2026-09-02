"""Guest management commands for ClickUp Framework CLI."""

from clickup_framework.commands.base_command import BaseCommand
from clickup_framework.commands.utils import add_common_args, parse_bool_flag
from clickup_framework.exceptions import ClickUpAPIError
from clickup_framework.utils.animations import ANSIAnimations
from clickup_framework.utils.colors import TextColor, TextStyle, colorize

COMMAND_METADATA = {
    "category": "👤 Guests",
    "commands": [
        {
            "name": "guest invite [gu i]",
            "args": "<team_id> <email>",
            "description": "Invite a guest to a workspace",
        },
        {
            "name": "guest get [gu g]",
            "args": "<team_id> <guest_id>",
            "description": "Get a guest's details and permissions",
        },
        {
            "name": "guest update [gu u]",
            "args": "<team_id> <guest_id>",
            "description": "Update a guest's permissions",
        },
        {
            "name": "guest remove [gu rm]",
            "args": "<team_id> <guest_id>",
            "description": "Remove a guest from a workspace",
        },
        {
            "name": "guest add-to",
            "args": "task|list|folder <container_id> <guest_id>",
            "description": "Give a guest access to a task/list/folder",
        },
        {
            "name": "guest remove-from",
            "args": "task|list|folder <container_id> <guest_id>",
            "description": "Revoke a guest's access to a task/list/folder",
        },
    ],
}


def _permission_kwargs(args):
    kwargs = {}
    for attr, key in (
        ("can_edit_tags", "can_edit_tags"),
        ("can_see_time_spent", "can_see_time_spent"),
        ("can_see_time_estimated", "can_see_time_estimated"),
        ("can_create_views", "can_create_views"),
        ("can_see_points_estimated", "can_see_points_estimated"),
    ):
        value = getattr(args, attr, None)
        if value is not None:
            kwargs[key] = value
    if getattr(args, "custom_role_id", None) is not None:
        kwargs["custom_role_id"] = args.custom_role_id
    return kwargs


def _add_permission_flags(parser):
    parser.add_argument(
        "--can-edit-tags", type=parse_bool_flag, default=None, help="true/false (default: unset)"
    )
    parser.add_argument(
        "--can-see-time-spent", type=parse_bool_flag, default=None, help="true/false"
    )
    parser.add_argument(
        "--can-see-time-estimated", type=parse_bool_flag, default=None, help="true/false"
    )
    parser.add_argument("--can-create-views", type=parse_bool_flag, default=None, help="true/false")
    parser.add_argument(
        "--can-see-points-estimated", type=parse_bool_flag, default=None, help="true/false"
    )
    parser.add_argument("--custom-role-id", type=int, help="Custom role ID to assign")


class GuestInviteCommand(BaseCommand):
    """Invite a guest to a workspace."""

    def execute(self):
        team_id = self.resolve_id("workspace", self.args.team_id)
        kwargs = {"email": self.args.email, **_permission_kwargs(self.args)}

        try:
            response = self.client.invite_guest_to_workspace(team_id, **kwargs)
            guest = response.get("guest", response)
            guest_info = guest.get("user", guest) if isinstance(guest, dict) else guest

            success_msg = ANSIAnimations.success_message(f"Guest invited: {self.args.email}")
            guest_id = guest_info.get("id") if isinstance(guest_info, dict) else None
            console_out = f"\n{success_msg}"
            if guest_id:
                console_out += f"\nGuest ID: {colorize(str(guest_id), TextColor.BRIGHT_GREEN)}"

            self.handle_output(data=guest, console_output=console_out)
        except ClickUpAPIError as e:
            self.error(f"Error inviting guest: {e}")


class GuestGetCommand(BaseCommand):
    """Get a guest's details."""

    def execute(self):
        team_id = self.resolve_id("workspace", self.args.team_id)
        try:
            response = self.client.get_guest(team_id, self.args.guest_id)
            guest = response.get("guest", response)

            if self.args.verbose:
                import json

                console_out = json.dumps(guest, indent=2)
            else:
                user = guest.get("user", {}) if isinstance(guest, dict) else {}
                display_name = user.get("username", user.get("email", "Guest"))
                title = colorize(display_name, TextColor.BRIGHT_CYAN, TextStyle.BOLD)
                guest_id_str = str(user.get("id", self.args.guest_id))
                lines = [
                    f"\n{title}",
                    f"ID: {colorize(guest_id_str, TextColor.BRIGHT_GREEN)}",
                    f"Email: {user.get('email', 'N/A')}",
                ]
                console_out = "\n".join(lines)

            self.handle_output(data=guest, console_output=console_out)
        except ClickUpAPIError as e:
            self.error(f"Error getting guest: {e}")


class GuestUpdateCommand(BaseCommand):
    """Update a guest's permissions."""

    def execute(self):
        team_id = self.resolve_id("workspace", self.args.team_id)
        updates = _permission_kwargs(self.args)

        if not updates:
            self.error(
                "No updates specified. Use --can-edit-tags, --can-see-time-spent, "
                "--can-see-time-estimated, --can-create-views, --can-see-points-estimated, "
                "or --custom-role-id"
            )

        try:
            response = self.client.update_guest(team_id, self.args.guest_id, **updates)
            success_msg = ANSIAnimations.success_message("Guest updated successfully")
            self.handle_output(data=response, console_output=f"\n{success_msg}")
        except ClickUpAPIError as e:
            self.error(f"Error updating guest: {e}")


class GuestRemoveCommand(BaseCommand):
    """Remove a guest from a workspace."""

    def execute(self):
        team_id = self.resolve_id("workspace", self.args.team_id)

        if not self.args.force:
            response = input(f"Remove guest {self.args.guest_id} from workspace {team_id}? [y/N]: ")
            if response.lower() not in ["y", "yes"]:
                self.print("Cancelled.")
                return

        try:
            self.client.remove_guest_from_workspace(team_id, self.args.guest_id)
            success_msg = ANSIAnimations.success_message("Guest removed successfully")
            self.handle_output(
                data={"guest_id": self.args.guest_id, "status": "removed"},
                console_output=f"\n{success_msg}",
            )
        except ClickUpAPIError as e:
            self.error(f"Error removing guest: {e}")


class GuestAddToCommand(BaseCommand):
    """Give a guest access to a task/list/folder."""

    def execute(self):
        container_type = self.args.container_type
        container_id = self.resolve_id(container_type, self.args.container_id)
        guest_id = self.args.guest_id

        try:
            if container_type == "task":
                params = {}
                if self.args.permission_level:
                    params["include_shared"] = True
                    params["permission_level"] = self.args.permission_level
                self.client.add_guest_to_task(container_id, guest_id, **params)
            elif container_type == "list":
                self.client.add_guest_to_list(container_id, guest_id)
            else:
                self.client.add_guest_to_folder(container_id, guest_id)

            success_msg = ANSIAnimations.success_message(
                f"Guest {guest_id} added to {container_type} {container_id}"
            )
            self.handle_output(
                data={
                    "guest_id": guest_id,
                    "container_type": container_type,
                    "container_id": container_id,
                },
                console_output=f"\n{success_msg}",
            )
        except ClickUpAPIError as e:
            self.error(f"Error adding guest to {container_type}: {e}")


class GuestRemoveFromCommand(BaseCommand):
    """Revoke a guest's access to a task/list/folder."""

    def execute(self):
        container_type = self.args.container_type
        container_id = self.resolve_id(container_type, self.args.container_id)
        guest_id = self.args.guest_id

        try:
            if container_type == "task":
                self.client.remove_guest_from_task(container_id, guest_id)
            elif container_type == "list":
                self.client.remove_guest_from_list(container_id, guest_id)
            else:
                self.client.remove_guest_from_folder(container_id, guest_id)

            success_msg = ANSIAnimations.success_message(
                f"Guest {guest_id} removed from {container_type} {container_id}"
            )
            self.handle_output(
                data={
                    "guest_id": guest_id,
                    "container_type": container_type,
                    "container_id": container_id,
                },
                console_output=f"\n{success_msg}",
            )
        except ClickUpAPIError as e:
            self.error(f"Error removing guest from {container_type}: {e}")


def guest_invite_command(args):
    GuestInviteCommand(args, command_name="guest").execute()


def guest_get_command(args):
    GuestGetCommand(args, command_name="guest").execute()


def guest_update_command(args):
    GuestUpdateCommand(args, command_name="guest").execute()


def guest_remove_command(args):
    GuestRemoveCommand(args, command_name="guest").execute()


def guest_add_to_command(args):
    GuestAddToCommand(args, command_name="guest").execute()


def guest_remove_from_command(args):
    GuestRemoveFromCommand(args, command_name="guest").execute()


def register_command(subparsers):
    """Register guest commands."""
    guest_parser = subparsers.add_parser(
        "guest",
        aliases=["gu", "guests"],
        help="Manage ClickUp guests",
        description="Invite, update, and scope access for guests (requires a plan with Guests)",
        epilog="""Tips:
  • Invite: cum guest invite current guest@example.com --can-edit-tags true
  • Grant list access: cum guest add-to list <list_id> <guest_id>
  • Revoke: cum guest remove-from list <list_id> <guest_id>
  • Remove entirely: cum guest remove current <guest_id>""",
    )
    add_common_args(guest_parser)
    guest_subparsers = guest_parser.add_subparsers(dest="guest_command", help="Guest command")

    # guest invite
    invite_parser = guest_subparsers.add_parser("invite", aliases=["i"], help="Invite a guest")
    invite_parser.add_argument("team_id", help='Workspace ID (or "current")')
    invite_parser.add_argument("email", help="Guest's email address")
    _add_permission_flags(invite_parser)
    invite_parser.set_defaults(func=guest_invite_command)

    # guest get
    get_parser = guest_subparsers.add_parser("get", aliases=["g", "show"], help="Get guest details")
    get_parser.add_argument("team_id", help='Workspace ID (or "current")')
    get_parser.add_argument("guest_id", help="Guest ID")
    get_parser.add_argument("--verbose", "-v", action="store_true", help="Show full JSON response")
    get_parser.set_defaults(func=guest_get_command)

    # guest update
    update_parser = guest_subparsers.add_parser("update", aliases=["u"], help="Update a guest")
    update_parser.add_argument("team_id", help='Workspace ID (or "current")')
    update_parser.add_argument("guest_id", help="Guest ID")
    _add_permission_flags(update_parser)
    update_parser.set_defaults(func=guest_update_command)

    # guest remove
    remove_parser = guest_subparsers.add_parser(
        "remove", aliases=["rm"], help="Remove a guest from a workspace"
    )
    remove_parser.add_argument("team_id", help='Workspace ID (or "current")')
    remove_parser.add_argument("guest_id", help="Guest ID")
    remove_parser.add_argument("--force", "-f", action="store_true", help="Skip confirmation")
    remove_parser.set_defaults(func=guest_remove_command)

    # guest add-to
    add_to_parser = guest_subparsers.add_parser(
        "add-to", help="Give a guest access to a task/list/folder"
    )
    add_to_parser.add_argument("container_type", choices=["task", "list", "folder"])
    add_to_parser.add_argument("container_id", help="Task, list, or folder ID")
    add_to_parser.add_argument("guest_id", help="Guest ID")
    add_to_parser.add_argument(
        "--permission-level", choices=["read", "comment", "edit", "create"], help="Task-only"
    )
    add_to_parser.set_defaults(func=guest_add_to_command)

    # guest remove-from
    remove_from_parser = guest_subparsers.add_parser(
        "remove-from", help="Revoke a guest's access to a task/list/folder"
    )
    remove_from_parser.add_argument("container_type", choices=["task", "list", "folder"])
    remove_from_parser.add_argument("container_id", help="Task, list, or folder ID")
    remove_from_parser.add_argument("guest_id", help="Guest ID")
    remove_from_parser.set_defaults(func=guest_remove_from_command)
