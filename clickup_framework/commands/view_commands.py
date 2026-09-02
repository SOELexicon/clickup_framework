"""View management commands for ClickUp Framework CLI."""

import json

from clickup_framework.commands.base_command import BaseCommand
from clickup_framework.commands.utils import add_common_args
from clickup_framework.exceptions import ClickUpAPIError
from clickup_framework.utils.animations import ANSIAnimations
from clickup_framework.utils.colors import TextColor, TextStyle, colorize

COMMAND_METADATA = {
    "category": "📊 View Commands",
    "commands": [
        {
            "name": "view list [v l]",
            "args": "[container_id] [--workspace <id>]",
            "description": "List views for a space, folder, list, or workspace",
        },
        {"name": "view get [v g]", "args": "<view_id>", "description": "Get view details"},
        {
            "name": "view create [v c]",
            "args": "[container_id] <name> --type <type>",
            "description": "Create a view on a space/folder/list/workspace",
        },
        {"name": "view update [v u]", "args": "<view_id>", "description": "Update a view"},
        {"name": "view delete [v rm]", "args": "<view_id>", "description": "Delete a view"},
        {
            "name": "view tasks [v t]",
            "args": "<view_id>",
            "description": "List tasks visible in a view",
        },
    ],
}


def _parse_settings(settings_str):
    if not settings_str:
        return {}
    try:
        settings = json.loads(settings_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"--settings must be valid JSON: {e}") from e
    if not isinstance(settings, dict):
        raise ValueError("--settings must be a JSON object")
    return settings


class ViewListCommand(BaseCommand):
    """List views for a container (space/folder/list) or a workspace."""

    def execute(self):
        try:
            if self.args.workspace_id:
                team_id = self.resolve_id("workspace", self.args.workspace_id)
                response = self.client.get_workspace_views(team_id)
                scope_label = f"workspace {team_id}"
            else:
                container = self.resolve_container(self.args.container_id or "current")
                container_type = container["type"]
                container_id = container["id"]
                if container_type == "space":
                    response = self.client.get_space_views(container_id)
                elif container_type == "folder":
                    response = self.client.get_folder_views(container_id)
                elif container_type == "task":
                    response = self.client.get_list_views(container["list_id"])
                else:
                    response = self.client.get_list_views(container_id)
                scope_label = f"{container_type} {container_id}"

            views = response.get("views", [])
            header = colorize(
                f"Views on {scope_label} ({len(views)})", TextColor.BRIGHT_CYAN, TextStyle.BOLD
            )
            lines = [f"\n{header}"]
            for view in views:
                name = colorize(view.get("name", "Unnamed"), TextColor.BRIGHT_WHITE, TextStyle.BOLD)
                view_type = view.get("type", "?")
                lines.append(
                    f"  {name} [{colorize(view['id'], TextColor.BRIGHT_GREEN)}] ({view_type})"
                )

            self.handle_output(data=views, console_output="\n".join(lines))
        except (ClickUpAPIError, ValueError) as e:
            self.error(f"Error listing views: {e}")


class ViewGetCommand(BaseCommand):
    """Get view details."""

    def execute(self):
        try:
            response = self.client.get_view(self.args.view_id)
            view = response.get("view", response)

            title = colorize(
                view.get("name", "Unnamed View"), TextColor.BRIGHT_CYAN, TextStyle.BOLD
            )
            lines = [
                f"\n{title}",
                f"ID: {colorize(view['id'], TextColor.BRIGHT_GREEN)}",
                f"Type: {view.get('type', 'N/A')}",
            ]
            if view.get("parent"):
                parent = view["parent"]
                lines.append(f"Parent: {parent.get('type', 'N/A')} {parent.get('id', 'N/A')}")

            if self.args.verbose:
                lines.append(
                    f"\n{colorize('Full Response:', TextColor.BRIGHT_WHITE, TextStyle.BOLD)}"
                )
                lines.append(json.dumps(view, indent=2))

            self.handle_output(data=view, console_output="\n".join(lines))
        except ClickUpAPIError as e:
            self.error(f"Error getting view: {e}")


class ViewCreateCommand(BaseCommand):
    """Create a new view on a space/folder/list/workspace."""

    def execute(self):
        try:
            extra = _parse_settings(self.args.settings)

            if self.args.workspace_id:
                team_id = self.resolve_id("workspace", self.args.workspace_id)
                response = self.client.create_workspace_view(
                    team_id, self.args.name, self.args.type, **extra
                )
                scope_label = f"workspace {team_id}"
            else:
                container = self.resolve_container(self.args.container_id or "current")
                container_type = container["type"]
                container_id = container["id"]
                if container_type == "space":
                    response = self.client.create_space_view(
                        container_id, self.args.name, self.args.type, **extra
                    )
                elif container_type == "folder":
                    response = self.client.create_folder_view(
                        container_id, self.args.name, self.args.type, **extra
                    )
                else:
                    list_id = container.get("list_id", container_id)
                    response = self.client.create_list_view(
                        list_id, self.args.name, self.args.type, **extra
                    )
                scope_label = f"{container_type} {container_id}"

            view = response.get("view", response)
            success_msg = ANSIAnimations.success_message(
                f"View created on {scope_label}: {self.args.name}"
            )
            console_out = (
                f"\n{success_msg}\nView ID: {colorize(view['id'], TextColor.BRIGHT_GREEN)}"
            )

            self.handle_output(data=view, console_output=console_out)
        except (ClickUpAPIError, ValueError) as e:
            self.error(f"Error creating view: {e}")


class ViewUpdateCommand(BaseCommand):
    """Update a view.

    ClickUp's PUT view/{id} requires the view's full schema (name, type,
    parent, grouping, divide, sorting, filters, columns, team_sidebar,
    settings) on every request -- a partial payload is rejected with
    "View schema not found". Fetch the current view first and merge the
    requested changes into it rather than sending a bare patch.
    """

    _SCHEMA_FIELDS = (
        "name",
        "type",
        "parent",
        "grouping",
        "divide",
        "sorting",
        "filters",
        "columns",
        "team_sidebar",
        "settings",
    )

    def execute(self):
        try:
            extra = _parse_settings(self.args.settings)
        except ValueError as e:
            self.error(str(e))
            return

        if not self.args.name and not extra:
            self.error("No updates specified. Use --name or --settings '<json>'")

        try:
            current = self.client.get_view(self.args.view_id)
            view = current.get("view", current)

            payload = {field: view[field] for field in self._SCHEMA_FIELDS if field in view}
            payload.update(extra)
            if self.args.name:
                payload["name"] = self.args.name

            response = self.client.update_view(self.args.view_id, **payload)
            success_msg = ANSIAnimations.success_message("View updated successfully")
            self.handle_output(data=response, console_output=f"\n{success_msg}")
        except ClickUpAPIError as e:
            self.error(f"Error updating view: {e}")


class ViewDeleteCommand(BaseCommand):
    """Delete a view."""

    def execute(self):
        view_id = self.args.view_id

        if not self.args.force:
            response = input(f"Delete view {view_id}? [y/N]: ")
            if response.lower() not in ["y", "yes"]:
                self.print("Cancelled.")
                return

        try:
            self.client.delete_view(view_id)
            success_msg = ANSIAnimations.success_message("View deleted successfully")
            self.handle_output(
                data={"id": view_id, "status": "deleted"}, console_output=f"\n{success_msg}"
            )
        except ClickUpAPIError as e:
            self.error(f"Error deleting view: {e}")


class ViewTasksCommand(BaseCommand):
    """List tasks visible in a view."""

    def execute(self):
        try:
            response = self.client.get_view_tasks(self.args.view_id, page=self.args.page)
            tasks = response.get("tasks", [])

            header = colorize(
                f"Tasks in view ({len(tasks)})", TextColor.BRIGHT_CYAN, TextStyle.BOLD
            )
            lines = [f"\n{header}"]
            for task in tasks:
                name = colorize(task.get("name", "Unnamed"), TextColor.BRIGHT_WHITE)
                lines.append(f"  {name} [{colorize(task['id'], TextColor.BRIGHT_GREEN)}]")

            self.handle_output(data=tasks, console_output="\n".join(lines))
        except ClickUpAPIError as e:
            self.error(f"Error getting view tasks: {e}")


def view_list_command(args):
    ViewListCommand(args, command_name="view").execute()


def view_get_command(args):
    ViewGetCommand(args, command_name="view").execute()


def view_create_command(args):
    ViewCreateCommand(args, command_name="view").execute()


def view_update_command(args):
    ViewUpdateCommand(args, command_name="view").execute()


def view_delete_command(args):
    ViewDeleteCommand(args, command_name="view").execute()


def view_tasks_command(args):
    ViewTasksCommand(args, command_name="view").execute()


def register_command(subparsers):
    """Register view commands."""
    view_parser = subparsers.add_parser(
        "view",
        aliases=["v", "views"],
        help="Manage ClickUp views",
        description="Manage views (List, Board, Calendar, etc.) at workspace/space/folder/list",
        epilog="""Tips:
  • List views on a list: cum view list <list_id>
  • List Everything-level views: cum view list --workspace <team_id>
  • Create a view: cum view create <list_id> "Sprint Board" --type board
  • Tasks in a view: cum view tasks <view_id>""",
    )
    add_common_args(view_parser)
    view_subparsers = view_parser.add_subparsers(dest="view_command", help="View command")

    # view list
    list_parser = view_subparsers.add_parser("list", aliases=["l", "ls"], help="List views")
    list_parser.add_argument(
        "container_id", nargs="?", help='Space, folder, or list ID (or "current")'
    )
    list_parser.add_argument(
        "--workspace",
        dest="workspace_id",
        help='Workspace ID for Everything-level views (or "current")',
    )
    list_parser.set_defaults(func=view_list_command)

    # view get
    get_parser = view_subparsers.add_parser("get", aliases=["g", "show"], help="Get view details")
    get_parser.add_argument("view_id", help="View ID")
    get_parser.add_argument("--verbose", "-v", action="store_true", help="Show full JSON response")
    get_parser.set_defaults(func=view_get_command)

    # view create
    create_parser = view_subparsers.add_parser("create", aliases=["c"], help="Create a new view")
    create_parser.add_argument(
        "container_id", nargs="?", help='Space, folder, or list ID (or "current")'
    )
    create_parser.add_argument("name", help="View name")
    create_parser.add_argument(
        "--type", required=True, help="View type (list, board, calendar, table, gantt, etc.)"
    )
    create_parser.add_argument(
        "--workspace",
        dest="workspace_id",
        help="Create an Everything-level view for this workspace ID instead",
    )
    create_parser.add_argument(
        "--settings",
        help='Extra view config as inline JSON, e.g. \'{"grouping": {"field": "status"}}\'',
    )
    create_parser.set_defaults(func=view_create_command)

    # view update
    update_parser = view_subparsers.add_parser("update", aliases=["u"], help="Update a view")
    update_parser.add_argument("view_id", help="View ID")
    update_parser.add_argument("--name", help="New view name")
    update_parser.add_argument("--settings", help="Extra view config as inline JSON to merge in")
    update_parser.set_defaults(func=view_update_command)

    # view delete
    delete_parser = view_subparsers.add_parser("delete", aliases=["rm"], help="Delete a view")
    delete_parser.add_argument("view_id", help="View ID")
    delete_parser.add_argument("--force", "-f", action="store_true", help="Skip confirmation")
    delete_parser.set_defaults(func=view_delete_command)

    # view tasks
    tasks_parser = view_subparsers.add_parser("tasks", aliases=["t"], help="List tasks in a view")
    tasks_parser.add_argument("view_id", help="View ID")
    tasks_parser.add_argument("--page", type=int, default=0, help="Page number (default: 0)")
    tasks_parser.set_defaults(func=view_tasks_command)
