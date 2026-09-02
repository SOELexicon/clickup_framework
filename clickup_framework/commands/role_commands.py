"""Custom role commands for ClickUp Framework CLI."""

from clickup_framework.commands.base_command import BaseCommand
from clickup_framework.commands.utils import add_common_args
from clickup_framework.exceptions import ClickUpAPIError
from clickup_framework.utils.colors import TextColor, TextStyle, colorize

COMMAND_METADATA = {
    "category": "🎭 Roles",
    "commands": [
        {
            "name": "roles [role]",
            "args": "[team_id]",
            "description": "List custom roles defined on a workspace",
        },
    ],
}

_INHERITED_ROLE_NAMES = {
    1: "Owner",
    2: "Admin",
    3: "Member",
    4: "Guest",
}


class RolesListCommand(BaseCommand):
    """List custom roles for a workspace."""

    def execute(self):
        team_id = self.resolve_id("workspace", self.args.team_id or "current")
        try:
            response = self.client.get_custom_roles(team_id)
            roles = response.get("custom_roles", [])

            header = colorize(f"Custom Roles ({len(roles)})", TextColor.BRIGHT_CYAN, TextStyle.BOLD)
            lines = [f"\n{header}"]
            for role in roles:
                inherited = _INHERITED_ROLE_NAMES.get(role.get("inherited_role"), "Unknown")
                name = colorize(role.get("name", "Unnamed"), TextColor.BRIGHT_WHITE, TextStyle.BOLD)
                member_count = len(role.get("members", []))
                lines.append(
                    f"  {name} [{colorize(str(role['id']), TextColor.BRIGHT_GREEN)}] "
                    f"(inherits: {inherited}, {member_count} member(s))"
                )

            if not roles:
                lines.append("  No custom roles defined on this workspace.")

            self.handle_output(data=roles, console_output="\n".join(lines))
        except ClickUpAPIError as e:
            self.error(f"Error listing custom roles: {e}")


def roles_list_command(args):
    RolesListCommand(args, command_name="roles").execute()


def register_command(subparsers):
    """Register the roles command."""
    roles_parser = subparsers.add_parser(
        "roles",
        aliases=["role"],
        help="List custom roles on a workspace",
        description="List custom roles defined on a workspace (requires a plan with Custom Roles)",
    )
    roles_parser.add_argument(
        "team_id",
        nargs="?",
        help='Workspace ID (or "current"); falls back to the configured default',
    )
    add_common_args(roles_parser)
    roles_parser.set_defaults(func=roles_list_command)
