"""User group (ClickApp Groups) commands for ClickUp Framework CLI."""

from clickup_framework.commands.base_command import BaseCommand
from clickup_framework.commands.utils import add_common_args
from clickup_framework.exceptions import ClickUpAPIError
from clickup_framework.utils.animations import ANSIAnimations
from clickup_framework.utils.colors import TextColor, TextStyle, colorize

COMMAND_METADATA = {
    "category": "👥 User Groups",
    "commands": [
        {
            "name": "group list [grp l]",
            "args": "[team_id]",
            "description": "List user groups in a workspace",
        },
        {
            "name": "group create [grp c]",
            "args": "<team_id> <name>",
            "description": "Create a user group",
        },
        {
            "name": "group update [grp u]",
            "args": "<group_id>",
            "description": "Rename a group or add/remove members",
        },
        {
            "name": "group delete [grp rm]",
            "args": "<group_id>",
            "description": "Delete a user group",
        },
    ],
}


def _parse_ids(ids_str):
    if not ids_str:
        return []
    return [int(i.strip()) for i in ids_str.split(",") if i.strip()]


class GroupListCommand(BaseCommand):
    """List user groups for a workspace."""

    def execute(self):
        team_id = self.resolve_id("workspace", self.args.team_id or "current")
        try:
            response = self.client.get_user_groups(team_id=team_id)
            groups = response.get("groups", [])

            header = colorize(f"User Groups ({len(groups)})", TextColor.BRIGHT_CYAN, TextStyle.BOLD)
            lines = [f"\n{header}"]
            for group in groups:
                name = colorize(
                    group.get("name", "Unnamed"), TextColor.BRIGHT_WHITE, TextStyle.BOLD
                )
                member_count = len(group.get("members", []))
                group_id = colorize(group["id"], TextColor.BRIGHT_GREEN)
                lines.append(f"  {name} [{group_id}] ({member_count} member(s))")

            self.handle_output(data=groups, console_output="\n".join(lines))
        except ClickUpAPIError as e:
            self.error(f"Error listing user groups: {e}")


class GroupCreateCommand(BaseCommand):
    """Create a user group."""

    def execute(self):
        team_id = self.resolve_id("workspace", self.args.team_id)
        member_ids = _parse_ids(self.args.members) or None

        try:
            response = self.client.create_user_group(team_id, self.args.name, member_ids)
            group = response.get("group", response)

            success_msg = ANSIAnimations.success_message(f"Group created: {self.args.name}")
            console_out = (
                f"\n{success_msg}\nGroup ID: {colorize(group['id'], TextColor.BRIGHT_GREEN)}"
            )

            self.handle_output(data=group, console_output=console_out)
        except ClickUpAPIError as e:
            self.error(f"Error creating group: {e}")


class GroupUpdateCommand(BaseCommand):
    """Rename a group or add/remove members."""

    def execute(self):
        updates = {}
        if self.args.name:
            updates["name"] = self.args.name
        if self.args.handle:
            updates["handle"] = self.args.handle

        # ClickUp's Update User Group request nests member changes under a
        # `members` key -- {"members": {"add": [...], "rem": [...]}} -- not
        # top-level `add`/`rem` fields. Confirmed against the vendored API
        # reference schema (UpdateTeamrequest) and its example payload; see
        # PR #185 review thread for the full comparison.
        add_ids = _parse_ids(self.args.add_members)
        remove_ids = _parse_ids(self.args.remove_members)
        if add_ids or remove_ids:
            updates["members"] = {"add": add_ids, "rem": remove_ids}

        if not updates:
            self.error(
                "No updates specified. Use --name, --handle, --add-members, or --remove-members"
            )

        try:
            response = self.client.update_user_group(self.args.group_id, **updates)
            success_msg = ANSIAnimations.success_message("Group updated successfully")
            self.handle_output(data=response, console_output=f"\n{success_msg}")
        except ClickUpAPIError as e:
            self.error(f"Error updating group: {e}")


class GroupDeleteCommand(BaseCommand):
    """Delete a user group."""

    def execute(self):
        group_id = self.args.group_id

        if not self.args.force:
            response = input(f"Delete group {group_id}? [y/N]: ")
            if response.lower() not in ["y", "yes"]:
                self.print("Cancelled.")
                return

        try:
            self.client.delete_user_group(group_id)
            success_msg = ANSIAnimations.success_message("Group deleted successfully")
            self.handle_output(
                data={"id": group_id, "status": "deleted"}, console_output=f"\n{success_msg}"
            )
        except ClickUpAPIError as e:
            self.error(f"Error deleting group: {e}")


def group_list_command(args):
    GroupListCommand(args, command_name="group").execute()


def group_create_command(args):
    GroupCreateCommand(args, command_name="group").execute()


def group_update_command(args):
    GroupUpdateCommand(args, command_name="group").execute()


def group_delete_command(args):
    GroupDeleteCommand(args, command_name="group").execute()


def register_command(subparsers):
    """Register user group commands."""
    group_parser = subparsers.add_parser(
        "group",
        aliases=["grp", "groups"],
        help="Manage ClickApp user groups",
        description="Manage user groups (teams of members you can @mention or assign as a unit)",
        epilog="""Tips:
  • List groups: cum group list
  • Create: cum group create current "Engineering" --members 123,456
  • Add/remove members: cum group update <group_id> --add-members 789 --remove-members 123""",
    )
    add_common_args(group_parser)
    group_subparsers = group_parser.add_subparsers(dest="group_command", help="Group command")

    # group list
    list_parser = group_subparsers.add_parser("list", aliases=["l", "ls"], help="List user groups")
    list_parser.add_argument(
        "team_id",
        nargs="?",
        help='Workspace ID (or "current"); falls back to the configured default',
    )
    list_parser.set_defaults(func=group_list_command)

    # group create
    create_parser = group_subparsers.add_parser("create", aliases=["c"], help="Create a user group")
    create_parser.add_argument("team_id", help='Workspace ID (or "current")')
    create_parser.add_argument("name", help="Group name")
    create_parser.add_argument("--members", help="Comma-separated user IDs to add at creation")
    create_parser.set_defaults(func=group_create_command)

    # group update
    update_parser = group_subparsers.add_parser("update", aliases=["u"], help="Update a user group")
    update_parser.add_argument("group_id", help="Group ID")
    update_parser.add_argument("--name", help="New group name")
    update_parser.add_argument("--handle", help="New @mention handle")
    update_parser.add_argument("--add-members", help="Comma-separated user IDs to add")
    update_parser.add_argument("--remove-members", help="Comma-separated user IDs to remove")
    update_parser.set_defaults(func=group_update_command)

    # group delete
    delete_parser = group_subparsers.add_parser(
        "delete", aliases=["rm"], help="Delete a user group"
    )
    delete_parser.add_argument("group_id", help="Group ID")
    delete_parser.add_argument("--force", "-f", action="store_true", help="Skip confirmation")
    delete_parser.set_defaults(func=group_delete_command)
