"""Goal management commands for ClickUp Framework CLI."""

from clickup_framework.commands.base_command import BaseCommand
from clickup_framework.commands.utils import add_common_args
from clickup_framework.exceptions import ClickUpAPIError
from clickup_framework.utils.animations import ANSIAnimations
from clickup_framework.utils.colors import TextColor, TextStyle, colorize

COMMAND_METADATA = {
    "category": "🎯 Goals",
    "commands": [
        {
            "name": "goal list [g l]",
            "args": "[team_id] [--include-completed]",
            "description": "List goals in a workspace",
        },
        {
            "name": "goal get [g g]",
            "args": "<goal_id>",
            "description": "Get goal details, including key results",
        },
        {"name": "goal create [g c]", "args": "<team_id> <name>", "description": "Create a goal"},
        {"name": "goal update [g u]", "args": "<goal_id>", "description": "Update a goal"},
        {"name": "goal delete [g rm]", "args": "<goal_id>", "description": "Delete a goal"},
        {
            "name": "goal kr create",
            "args": "<goal_id> <name> --type <type>",
            "description": "Add a key result (target) to a goal",
        },
        {
            "name": "goal kr update",
            "args": "<key_result_id>",
            "description": "Update a key result (progress, note, etc.)",
        },
        {"name": "goal kr delete", "args": "<key_result_id>", "description": "Remove a key result"},
    ],
}


def _parse_owners(owners_str):
    if not owners_str:
        return None
    return [int(o.strip()) for o in owners_str.split(",") if o.strip()]


def _parse_ids(ids_str):
    if not ids_str:
        return None
    return [i.strip() for i in ids_str.split(",") if i.strip()]


class GoalListCommand(BaseCommand):
    """List goals in a workspace."""

    def execute(self):
        team_id = self.resolve_id("workspace", self.args.team_id or "current")
        try:
            response = self.client.get_goals(team_id, include_completed=self.args.include_completed)
            goals = response.get("goals", [])

            lines = [
                f"\n{colorize(f'Goals ({len(goals)})', TextColor.BRIGHT_CYAN, TextStyle.BOLD)}"
            ]
            for goal in goals:
                pct = goal.get("percent_completed", 0)
                name = colorize(goal.get("name", "Unnamed"), TextColor.BRIGHT_WHITE, TextStyle.BOLD)
                lines.append(
                    f"  {name} [{colorize(goal['id'], TextColor.BRIGHT_GREEN)}] ({pct}% complete)"
                )

            self.handle_output(data=goals, console_output="\n".join(lines))
        except ClickUpAPIError as e:
            self.error(f"Error listing goals: {e}")


class GoalGetCommand(BaseCommand):
    """Get goal details."""

    def execute(self):
        goal_id = self.args.goal_id
        try:
            response = self.client.get_goal(goal_id)
            goal = response.get("goal", response)

            title = colorize(
                goal.get("name", "Unnamed Goal"), TextColor.BRIGHT_CYAN, TextStyle.BOLD
            )
            lines = [
                f"\n{title}",
                f"ID: {colorize(goal['id'], TextColor.BRIGHT_GREEN)}",
                f"Progress: {goal.get('percent_completed', 0)}%",
            ]
            if goal.get("description"):
                lines.append(f"Description: {goal['description']}")
            if goal.get("due_date"):
                lines.append(f"Due: {goal['due_date']}")

            key_results = goal.get("key_results", [])
            if key_results:
                lines.append(
                    f"\n{colorize('Key Results:', TextColor.BRIGHT_WHITE, TextStyle.BOLD)}"
                )
                for kr in key_results:
                    kr_id = colorize(kr["id"], TextColor.BRIGHT_GREEN)
                    lines.append(
                        f"  {kr.get('name', 'Unnamed')} [{kr_id}] "
                        f"({kr.get('percent_completed', 0)}%)"
                    )

            if self.args.verbose:
                import json

                lines.append(
                    f"\n{colorize('Full Response:', TextColor.BRIGHT_WHITE, TextStyle.BOLD)}"
                )
                lines.append(json.dumps(goal, indent=2))

            self.handle_output(data=goal, console_output="\n".join(lines))
        except ClickUpAPIError as e:
            self.error(f"Error getting goal: {e}")


class GoalCreateCommand(BaseCommand):
    """Create a new goal."""

    def execute(self):
        team_id = self.resolve_id("workspace", self.args.team_id)

        goal_data = {
            "name": self.args.name,
            "due_date": self.args.due_date,
            "description": self.args.description or "",
            "multiple_owners": self.args.multiple_owners,
            "owners": _parse_owners(self.args.owners) or [],
            "color": self.args.color or "#32a852",
        }

        try:
            response = self.client.create_goal(team_id, **goal_data)
            goal = response.get("goal", response)

            success_msg = ANSIAnimations.success_message(f"Goal created: {self.args.name}")
            console_out = (
                f"\n{success_msg}\nGoal ID: {colorize(goal['id'], TextColor.BRIGHT_GREEN)}"
            )

            self.handle_output(data=goal, console_output=console_out)
        except ClickUpAPIError as e:
            self.error(f"Error creating goal: {e}")


class GoalUpdateCommand(BaseCommand):
    """Update a goal."""

    def execute(self):
        goal_id = self.args.goal_id

        updates = {}
        if self.args.name:
            updates["name"] = self.args.name
        if self.args.description is not None:
            updates["description"] = self.args.description
        if self.args.due_date:
            updates["due_date"] = self.args.due_date
        if self.args.color:
            updates["color"] = self.args.color
        if self.args.owners:
            updates["owners"] = _parse_owners(self.args.owners)

        if not updates:
            self.error(
                "No updates specified. Use --name, --description, --due-date, --color, or --owners"
            )

        try:
            response = self.client.update_goal(goal_id, **updates)
            success_msg = ANSIAnimations.success_message("Goal updated successfully")
            self.handle_output(data=response, console_output=f"\n{success_msg}")
        except ClickUpAPIError as e:
            self.error(f"Error updating goal: {e}")


class GoalDeleteCommand(BaseCommand):
    """Delete a goal."""

    def execute(self):
        goal_id = self.args.goal_id

        warning = colorize("Warning:", TextColor.BRIGHT_YELLOW, TextStyle.BOLD)
        self.print(f"\n{warning} This will permanently delete the goal and its key results.")

        if not self.args.force:
            response = input("Are you sure? [y/N]: ")
            if response.lower() not in ["y", "yes"]:
                self.print("Cancelled.")
                return

        try:
            self.client.delete_goal(goal_id)
            success_msg = ANSIAnimations.success_message("Goal deleted successfully")
            self.handle_output(
                data={"id": goal_id, "status": "deleted"}, console_output=f"\n{success_msg}"
            )
        except ClickUpAPIError as e:
            self.error(f"Error deleting goal: {e}")


class KeyResultCreateCommand(BaseCommand):
    """Create a key result (target) on a goal."""

    def execute(self):
        kr_data = {
            "name": self.args.name,
            "owners": _parse_owners(self.args.owners) or [],
            "type": self.args.type,
            "steps_start": self.args.steps_start,
            "steps_end": self.args.steps_end,
            "unit": self.args.unit or "",
            "task_ids": _parse_ids(self.args.task_ids) or [],
            "list_ids": _parse_ids(self.args.list_ids) or [],
        }

        try:
            response = self.client.create_key_result(self.args.goal_id, **kr_data)
            key_result = response.get("key_result", response)

            success_msg = ANSIAnimations.success_message(f"Key result created: {self.args.name}")
            kr_id = colorize(key_result["id"], TextColor.BRIGHT_GREEN)
            console_out = f"\n{success_msg}\nKey Result ID: {kr_id}"

            self.handle_output(data=key_result, console_output=console_out)
        except ClickUpAPIError as e:
            self.error(f"Error creating key result: {e}")


class KeyResultUpdateCommand(BaseCommand):
    """Update a key result's progress or details."""

    def execute(self):
        updates = {}
        if self.args.steps_current is not None:
            updates["steps_current"] = self.args.steps_current
        if self.args.note is not None:
            updates["note"] = self.args.note
        if self.args.name:
            updates["name"] = self.args.name
        if self.args.owners:
            updates["owners"] = _parse_owners(self.args.owners)

        if not updates:
            self.error("No updates specified. Use --steps-current, --note, --name, or --owners")

        try:
            response = self.client.update_key_result(self.args.key_result_id, **updates)
            success_msg = ANSIAnimations.success_message("Key result updated successfully")
            self.handle_output(data=response, console_output=f"\n{success_msg}")
        except ClickUpAPIError as e:
            self.error(f"Error updating key result: {e}")


class KeyResultDeleteCommand(BaseCommand):
    """Delete a key result."""

    def execute(self):
        key_result_id = self.args.key_result_id

        if not self.args.force:
            response = input(f"Delete key result {key_result_id}? [y/N]: ")
            if response.lower() not in ["y", "yes"]:
                self.print("Cancelled.")
                return

        try:
            self.client.delete_key_result(key_result_id)
            success_msg = ANSIAnimations.success_message("Key result deleted successfully")
            self.handle_output(
                data={"id": key_result_id, "status": "deleted"}, console_output=f"\n{success_msg}"
            )
        except ClickUpAPIError as e:
            self.error(f"Error deleting key result: {e}")


def goal_list_command(args):
    GoalListCommand(args, command_name="goal").execute()


def goal_get_command(args):
    GoalGetCommand(args, command_name="goal").execute()


def goal_create_command(args):
    GoalCreateCommand(args, command_name="goal").execute()


def goal_update_command(args):
    GoalUpdateCommand(args, command_name="goal").execute()


def goal_delete_command(args):
    GoalDeleteCommand(args, command_name="goal").execute()


def key_result_create_command(args):
    KeyResultCreateCommand(args, command_name="goal").execute()


def key_result_update_command(args):
    KeyResultUpdateCommand(args, command_name="goal").execute()


def key_result_delete_command(args):
    KeyResultDeleteCommand(args, command_name="goal").execute()


def register_command(subparsers):
    """Register goal commands."""
    goal_parser = subparsers.add_parser(
        "goal",
        aliases=["g", "goals"],
        help="Manage goals and key results",
        description="Manage ClickUp goals (Targets/OKRs) and their key results",
        epilog="""Tips:
  • List goals: cum goal list [team_id]
  • View a goal: cum goal get <goal_id>
  • Create a goal: cum goal create <team_id> "Q3 Revenue" --due-date <ms_timestamp>
  • Add a target: cum goal kr create <goal_id> "Signups" --type number --steps-end 100
  • Update progress: cum goal kr update <key_result_id> --steps-current 42""",
    )
    add_common_args(goal_parser)
    goal_subparsers = goal_parser.add_subparsers(dest="goal_command", help="Goal command")

    # goal list
    list_parser = goal_subparsers.add_parser(
        "list", aliases=["l", "ls"], help="List goals in a workspace"
    )
    list_parser.add_argument(
        "team_id",
        nargs="?",
        help='Workspace ID (or "current"); falls back to the configured default workspace',
    )
    list_parser.add_argument(
        "--include-completed", action="store_true", help="Include completed goals"
    )
    list_parser.set_defaults(func=goal_list_command)

    # goal get
    get_parser = goal_subparsers.add_parser("get", aliases=["g", "show"], help="Get goal details")
    get_parser.add_argument("goal_id", help="Goal ID")
    get_parser.add_argument("--verbose", "-v", action="store_true", help="Show full JSON response")
    get_parser.set_defaults(func=goal_get_command)

    # goal create
    create_parser = goal_subparsers.add_parser("create", aliases=["c"], help="Create a new goal")
    create_parser.add_argument("team_id", help='Workspace ID (or "current")')
    create_parser.add_argument("name", help="Goal name")
    create_parser.add_argument(
        "--due-date",
        type=int,
        required=True,
        help="Due date (Unix timestamp in milliseconds)",
    )
    create_parser.add_argument("--description", help="Goal description")
    create_parser.add_argument("--color", help="Hex color (e.g. #32a852)")
    create_parser.add_argument("--owners", help="Comma-separated user IDs")
    create_parser.add_argument(
        "--multiple-owners",
        action="store_true",
        default=True,
        help="Allow multiple owners (default: true)",
    )
    create_parser.set_defaults(func=goal_create_command)

    # goal update
    update_parser = goal_subparsers.add_parser("update", aliases=["u"], help="Update a goal")
    update_parser.add_argument("goal_id", help="Goal ID")
    update_parser.add_argument("--name", help="New goal name")
    update_parser.add_argument("--description", help="New description")
    update_parser.add_argument(
        "--due-date", type=int, help="Due date (Unix timestamp in milliseconds)"
    )
    update_parser.add_argument("--color", help="Hex color")
    update_parser.add_argument("--owners", help="Comma-separated user IDs")
    update_parser.set_defaults(func=goal_update_command)

    # goal delete
    delete_parser = goal_subparsers.add_parser("delete", aliases=["rm"], help="Delete a goal")
    delete_parser.add_argument("goal_id", help="Goal ID")
    delete_parser.add_argument("--force", "-f", action="store_true", help="Skip confirmation")
    delete_parser.set_defaults(func=goal_delete_command)

    # goal kr <...>
    kr_parser = goal_subparsers.add_parser(
        "kr", aliases=["key-result", "key_result"], help="Manage key results (targets) on a goal"
    )
    kr_subparsers = kr_parser.add_subparsers(dest="kr_command", help="Key result command")

    kr_create_parser = kr_subparsers.add_parser(
        "create", aliases=["c"], help="Add a key result to a goal"
    )
    kr_create_parser.add_argument("goal_id", help="Goal ID")
    kr_create_parser.add_argument("name", help="Key result name")
    kr_create_parser.add_argument(
        "--type",
        required=True,
        choices=["number", "currency", "boolean", "percentage", "automatic"],
        help="Key result type",
    )
    kr_create_parser.add_argument(
        "--steps-start", type=int, default=0, help="Starting value (default: 0)"
    )
    kr_create_parser.add_argument(
        "--steps-end", type=int, default=1, help="Target value (default: 1)"
    )
    kr_create_parser.add_argument("--unit", help="Unit label (e.g. km, $, users)")
    kr_create_parser.add_argument("--owners", help="Comma-separated user IDs")
    kr_create_parser.add_argument("--task-ids", help="Comma-separated task IDs to link")
    kr_create_parser.add_argument("--list-ids", help="Comma-separated list IDs to link")
    kr_create_parser.set_defaults(func=key_result_create_command)

    kr_update_parser = kr_subparsers.add_parser("update", aliases=["u"], help="Update a key result")
    kr_update_parser.add_argument("key_result_id", help="Key result ID")
    kr_update_parser.add_argument("--steps-current", type=int, help="Current progress value")
    kr_update_parser.add_argument("--note", help="Progress note")
    kr_update_parser.add_argument("--name", help="New name")
    kr_update_parser.add_argument("--owners", help="Comma-separated user IDs")
    kr_update_parser.set_defaults(func=key_result_update_command)

    kr_delete_parser = kr_subparsers.add_parser(
        "delete", aliases=["rm"], help="Remove a key result"
    )
    kr_delete_parser.add_argument("key_result_id", help="Key result ID")
    kr_delete_parser.add_argument("--force", "-f", action="store_true", help="Skip confirmation")
    kr_delete_parser.set_defaults(func=key_result_delete_command)
