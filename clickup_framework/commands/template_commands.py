"""Task template listing commands for ClickUp Framework CLI.

Task/list/folder creation already consume template IDs (--checklist-
template, `list-mgmt create-from-template`, folder template apply)
but there was no way to discover what templates exist without already
knowing the ID. Custom task types have their own `cum task_types`
command already -- this module only covers task templates, the other
half of that gap.
"""

from clickup_framework.commands.base_command import BaseCommand
from clickup_framework.commands.utils import add_common_args
from clickup_framework.exceptions import ClickUpAPIError
from clickup_framework.utils.colors import TextColor, TextStyle, colorize

COMMAND_METADATA = {
    "category": "📋 Templates",
    "commands": [
        {
            "name": "templates [tpl]",
            "args": "[team_id]",
            "description": "List task templates available in a workspace",
        },
    ],
}


class TemplatesListCommand(BaseCommand):
    """List task templates for a workspace."""

    def execute(self):
        team_id = self.resolve_id("workspace", self.args.team_id or "current")
        try:
            response = self.client.get_task_templates(team_id)
            templates = response.get("templates", [])

            header = colorize(
                f"Task Templates ({len(templates)})", TextColor.BRIGHT_CYAN, TextStyle.BOLD
            )
            lines = [f"\n{header}"]
            for template in templates:
                if isinstance(template, dict):
                    name = colorize(template.get("name", "Unnamed"), TextColor.BRIGHT_WHITE)
                    template_id = colorize(str(template.get("id", "N/A")), TextColor.BRIGHT_GREEN)
                    lines.append(f"  {name} [{template_id}]")
                else:
                    lines.append(f"  {template}")

            if not templates:
                lines.append("  No task templates found on this workspace.")

            self.handle_output(data=templates, console_output="\n".join(lines))
        except ClickUpAPIError as e:
            self.error(f"Error listing task templates: {e}")


def templates_list_command(args):
    TemplatesListCommand(args, command_name="templates").execute()


def register_command(subparsers):
    """Register the templates command."""
    templates_parser = subparsers.add_parser(
        "templates",
        aliases=["tpl"],
        help="List task templates on a workspace",
        description="List task templates so their IDs can be used with --checklist-template, "
        "list-mgmt create-from-template, or folder template creation",
    )
    templates_parser.add_argument(
        "team_id",
        nargs="?",
        help='Workspace ID (or "current"); falls back to the configured default',
    )
    add_common_args(templates_parser)
    templates_parser.set_defaults(func=templates_list_command)
