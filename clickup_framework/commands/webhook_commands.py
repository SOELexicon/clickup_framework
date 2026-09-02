"""Webhook management commands for ClickUp Framework CLI."""

from clickup_framework.commands.base_command import BaseCommand
from clickup_framework.commands.utils import add_common_args
from clickup_framework.exceptions import ClickUpAPIError
from clickup_framework.utils.animations import ANSIAnimations
from clickup_framework.utils.colors import TextColor, TextStyle, colorize

COMMAND_METADATA = {
    "category": "🔗 Webhooks",
    "commands": [
        {
            "name": "webhook list [wh l]",
            "args": "[team_id]",
            "description": "List webhooks for a workspace",
        },
        {
            "name": "webhook create [wh c]",
            "args": "<team_id> <endpoint> --events <e1,e2,...>",
            "description": "Create a webhook",
        },
        {
            "name": "webhook update [wh u]",
            "args": "<webhook_id> [--team <id>]",
            "description": "Update a webhook's endpoint/events/status",
        },
        {
            "name": "webhook delete [wh rm]",
            "args": "<webhook_id>",
            "description": "Delete a webhook",
        },
    ],
}


def _parse_events(events_str):
    if not events_str or events_str.strip() == "*":
        return ["*"]
    return [e.strip() for e in events_str.split(",") if e.strip()]


class WebhookListCommand(BaseCommand):
    """List webhooks for a workspace."""

    def execute(self):
        team_id = self.resolve_id("workspace", self.args.team_id or "current")
        try:
            response = self.client.get_webhooks(team_id)
            webhooks = response.get("webhooks", [])

            header = colorize(f"Webhooks ({len(webhooks)})", TextColor.BRIGHT_CYAN, TextStyle.BOLD)
            lines = [f"\n{header}"]
            for wh in webhooks:
                health = wh.get("health", {}).get("status", "unknown")
                health_color = (
                    TextColor.BRIGHT_GREEN if health == "active" else TextColor.BRIGHT_YELLOW
                )
                wh_id = colorize(wh["id"], TextColor.BRIGHT_GREEN)
                lines.append(
                    f"  {wh_id} -> {wh.get('endpoint', 'N/A')} [{colorize(health, health_color)}]"
                )
                events = wh.get("events", [])
                events_display = ", ".join(events[:5]) + (
                    f" (+{len(events) - 5} more)" if len(events) > 5 else ""
                )
                lines.append(f"    events: {events_display}")

            self.handle_output(data=webhooks, console_output="\n".join(lines))
        except ClickUpAPIError as e:
            self.error(f"Error listing webhooks: {e}")


class WebhookCreateCommand(BaseCommand):
    """Create a webhook."""

    def execute(self):
        team_id = self.resolve_id("workspace", self.args.team_id)
        events = _parse_events(self.args.events)

        extra = {}
        if self.args.space_id:
            extra["space_id"] = int(self.resolve_id("space", self.args.space_id))
        elif self.args.folder_id:
            extra["folder_id"] = int(self.resolve_id("folder", self.args.folder_id))
        elif self.args.list_id:
            extra["list_id"] = int(self.resolve_id("list", self.args.list_id))
        elif self.args.task_id:
            extra["task_id"] = self.resolve_id("task", self.args.task_id)

        try:
            response = self.client.create_webhook(team_id, self.args.endpoint, events, **extra)
            webhook = response.get("webhook", response)

            success_msg = ANSIAnimations.success_message(f"Webhook created: {self.args.endpoint}")
            console_out = (
                f"\n{success_msg}\nWebhook ID: {colorize(webhook['id'], TextColor.BRIGHT_GREEN)}"
            )
            if webhook.get("secret"):
                console_out += (
                    f"\nSecret: {webhook['secret']} (save this -- verifies payload signatures)"
                )

            self.handle_output(data=webhook, console_output=console_out)
        except ClickUpAPIError as e:
            self.error(f"Error creating webhook: {e}")


class WebhookUpdateCommand(BaseCommand):
    """Update a webhook.

    ClickUp's PUT webhook/{id} expects endpoint, events, and status
    together. Fetch the workspace's webhook list first (there is no
    single-webhook GET), find the matching one, and merge requested
    changes into its current values before sending.
    """

    def execute(self):
        team_id = self.resolve_id("workspace", self.args.team_id or "current")

        try:
            response = self.client.get_webhooks(team_id)
            webhooks = response.get("webhooks", [])
            current = next((wh for wh in webhooks if wh["id"] == self.args.webhook_id), None)
            if current is None:
                self.error(
                    f"Webhook {self.args.webhook_id} not found in workspace {team_id}. "
                    "Pass --team if it lives in a different workspace."
                )
                return

            payload = {
                "endpoint": self.args.endpoint or current.get("endpoint"),
                "events": (
                    _parse_events(self.args.events)
                    if self.args.events
                    else current.get("events", ["*"])
                ),
                "status": self.args.status or current.get("health", {}).get("status", "active"),
            }

            self.client.update_webhook(self.args.webhook_id, **payload)
            success_msg = ANSIAnimations.success_message("Webhook updated successfully")
            self.handle_output(data=payload, console_output=f"\n{success_msg}")
        except ClickUpAPIError as e:
            self.error(f"Error updating webhook: {e}")


class WebhookDeleteCommand(BaseCommand):
    """Delete a webhook."""

    def execute(self):
        webhook_id = self.args.webhook_id

        if not self.args.force:
            response = input(f"Delete webhook {webhook_id}? [y/N]: ")
            if response.lower() not in ["y", "yes"]:
                self.print("Cancelled.")
                return

        try:
            self.client.delete_webhook(webhook_id)
            success_msg = ANSIAnimations.success_message("Webhook deleted successfully")
            self.handle_output(
                data={"id": webhook_id, "status": "deleted"}, console_output=f"\n{success_msg}"
            )
        except ClickUpAPIError as e:
            self.error(f"Error deleting webhook: {e}")


def webhook_list_command(args):
    WebhookListCommand(args, command_name="webhook").execute()


def webhook_create_command(args):
    WebhookCreateCommand(args, command_name="webhook").execute()


def webhook_update_command(args):
    WebhookUpdateCommand(args, command_name="webhook").execute()


def webhook_delete_command(args):
    WebhookDeleteCommand(args, command_name="webhook").execute()


def register_command(subparsers):
    """Register webhook commands."""
    webhook_parser = subparsers.add_parser(
        "webhook",
        aliases=["wh", "webhooks"],
        help="Manage ClickUp webhooks",
        description=(
            "Manage webhooks for a workspace, optionally scoped to a space/folder/list/task"
        ),
        epilog="""Tips:
  • List webhooks: cum webhook list
  • Create: cum webhook create current https://example.com/hook --events taskCreated,taskUpdated
  • Subscribe to everything: cum webhook create current https://example.com/hook --events '*'
  • Update: cum webhook update <webhook_id> --status disabled""",
    )
    add_common_args(webhook_parser)
    webhook_subparsers = webhook_parser.add_subparsers(
        dest="webhook_command", help="Webhook command"
    )

    # webhook list
    list_parser = webhook_subparsers.add_parser("list", aliases=["l", "ls"], help="List webhooks")
    list_parser.add_argument(
        "team_id",
        nargs="?",
        help='Workspace ID (or "current"); falls back to the configured default',
    )
    list_parser.set_defaults(func=webhook_list_command)

    # webhook create
    create_parser = webhook_subparsers.add_parser("create", aliases=["c"], help="Create a webhook")
    create_parser.add_argument("team_id", help='Workspace ID (or "current")')
    create_parser.add_argument("endpoint", help="Webhook URL endpoint")
    create_parser.add_argument(
        "--events", required=True, help='Comma-separated event names, or "*" for all events'
    )
    scope_group = create_parser.add_mutually_exclusive_group()
    scope_group.add_argument("--space", dest="space_id", help='Scope to a space (ID or "current")')
    scope_group.add_argument(
        "--folder", dest="folder_id", help='Scope to a folder (ID or "current")'
    )
    scope_group.add_argument("--list", dest="list_id", help='Scope to a list (ID or "current")')
    scope_group.add_argument("--task", dest="task_id", help='Scope to a task (ID or "current")')
    create_parser.set_defaults(func=webhook_create_command)

    # webhook update
    update_parser = webhook_subparsers.add_parser("update", aliases=["u"], help="Update a webhook")
    update_parser.add_argument("webhook_id", help="Webhook ID")
    update_parser.add_argument(
        "--team", dest="team_id", help='Workspace the webhook belongs to (ID or "current")'
    )
    update_parser.add_argument("--endpoint", help="New webhook URL endpoint")
    update_parser.add_argument(
        "--events", help='Comma-separated event names, or "*" for all events'
    )
    update_parser.add_argument(
        "--status",
        help="Webhook status (ClickUp manages this from delivery health; 'active' is the "
        "only confirmed writable value -- omit to keep the current status)",
    )
    update_parser.set_defaults(func=webhook_update_command)

    # webhook delete
    delete_parser = webhook_subparsers.add_parser("delete", aliases=["rm"], help="Delete a webhook")
    delete_parser.add_argument("webhook_id", help="Webhook ID")
    delete_parser.add_argument("--force", "-f", action="store_true", help="Skip confirmation")
    delete_parser.set_defaults(func=webhook_delete_command)
