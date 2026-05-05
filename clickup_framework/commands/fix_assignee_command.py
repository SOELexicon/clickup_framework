"""
Fix-assignee command: bulk-assign unassigned tasks to the default (or specified) user.

Variables:  FixAssigneeCommand, fix_assignee_command, register_command, COMMAND_METADATA
"""

from clickup_framework.commands.base_command import BaseCommand
from clickup_framework.commands.utils import add_common_args
from clickup_framework.utils.colors import colorize, TextColor, TextStyle


COMMAND_METADATA = {
    "category": "✅ Task Management",
    "commands": [
        {
            "name": "fix-ass",
            "args": "[--list LIST_ID] [--user-id USER_ID] [--force]",
            "description": "Assign all unassigned tasks in current list to default assignee",
        }
    ],
}


class FixAssigneeCommand(BaseCommand):
    """
    Fix-Assignee Command using BaseCommand.

    Fetches all tasks in the current (or specified) list and assigns any
    that have no assignee to the configured default assignee.  --force
    reassigns tasks that already have a different assignee.
    """

    def execute(self):
        """
        Purpose:    Bulk-assign unassigned (or all, with --force) tasks in a list
                    to the target user ID.
        Usage:      cum fix-ass [--list LIST_ID] [--user-id USER_ID] [--force]
        Version:    0.1.0
        Changes:    [v0.1.0] Initial: unassigned task bulk-assignment
        """
        # Resolve target user
        user_id = getattr(self.args, 'user_id', None)
        if not user_id:
            user_id = self.context.get_default_assignee()
        if not user_id:
            self.error(
                "No assignee specified. Use --user-id <id> or set one with: cum set assignee <id>"
            )
        user_id = int(user_id)

        # Resolve list
        list_id = getattr(self.args, 'list_id', None)
        if not list_id:
            try:
                list_id = self.context.resolve_id('list', 'current')
            except (ValueError, KeyError):
                self.error("No list specified. Use --list <list_id> or set one with: cum set list <id>")

        force = getattr(self.args, 'force', False)

        # Fetch all tasks in the list (open only by default)
        try:
            result = self.client.get_list_tasks(list_id, subtasks=True, include_closed=False)
            tasks = result.get('tasks', [])
        except Exception as e:
            self.error(f"Error fetching tasks from list {list_id}: {e}")

        if not tasks:
            self.print(f"No tasks found in list {list_id}.")
            return

        use_color = self.context.get_ansi_output()

        candidates = []
        skipped = []
        for task in tasks:
            assignees = task.get('assignees', [])
            already_has = any(int(a.get('id', 0)) == user_id for a in assignees)

            if not assignees or (force and not already_has):
                candidates.append(task)
            elif not already_has and not force:
                # Has a different assignee - skip unless --force
                skipped.append(task)

        if not candidates:
            msg = f"All {len(tasks)} tasks already assigned."
            if skipped:
                msg += f" ({len(skipped)} have a different assignee; use --force to reassign)"
            self.print(msg)
            return

        label = colorize(f"Assigning {len(candidates)} task(s) to user {user_id}", TextColor.BRIGHT_CYAN, TextStyle.BOLD) if use_color else f"Assigning {len(candidates)} task(s) to user {user_id}"
        self.print(label)
        if skipped:
            self.print(f"  ({len(skipped)} task(s) with existing assignees skipped; use --force to include)")
        self.print()

        ok = []
        failed = []
        for task in candidates:
            tid = task['id']
            name = task.get('name', tid)
            try:
                self.client.update_task(tid, assignees={'add': [user_id]})
                ok.append(name)
                tick = colorize("  ✓", TextColor.BRIGHT_GREEN) if use_color else "  ✓"
                self.print(f"{tick} {name}")
            except Exception as e:
                failed.append((name, str(e)))
                cross = colorize("  ✗", TextColor.BRIGHT_RED) if use_color else "  ✗"
                self.print(f"{cross} {name}: {e}")

        self.print()
        summary = f"Done: {len(ok)} assigned"
        if failed:
            summary += f", {len(failed)} failed"
        self.print(colorize(summary, TextColor.BRIGHT_WHITE, TextStyle.BOLD) if use_color else summary)


def fix_assignee_command(args):
    """
    Purpose:    Command function wrapper for backward compatibility.
    Usage:      Called by argparse via set_defaults(func=...)
    Version:    0.1.0
    Changes:    [v0.1.0] Initial
    """
    command = FixAssigneeCommand(args, command_name='fix-ass')
    command.execute()


def register_command(subparsers, add_common_args_func=None):
    """Register the fix-ass command with argparse."""
    parser = subparsers.add_parser(
        'fix-ass',
        aliases=['fix_ass'],
        help='Bulk-assign unassigned tasks in a list to the default assignee',
        description='Assign every unassigned task in the current (or specified) list to the default assignee.',
        epilog='''Tips:
  • Assign unassigned tasks in current list: cum fix-ass
  • Target a specific list:                 cum fix-ass --list 901517404274
  • Override target user:                   cum fix-ass --user-id 50460297
  • Reassign even tasks with an assignee:   cum fix-ass --force'''
    )
    parser.add_argument('--list', dest='list_id', metavar='LIST_ID',
                        help='List ID to operate on (defaults to current list)')
    parser.add_argument('--user-id', dest='user_id', metavar='USER_ID',
                        help='User ID to assign tasks to (defaults to configured default assignee)')
    parser.add_argument('--force', action='store_true',
                        help='Reassign tasks that already have a different assignee')
    common_args = add_common_args_func or add_common_args
    common_args(parser)
    parser.set_defaults(func=fix_assignee_command)
