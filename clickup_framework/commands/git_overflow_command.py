"""Git Overflow command - Automated Git + ClickUp workflow integration."""

from clickup_framework.commands.base_command import BaseCommand
from clickup_framework.git import (
    execute_overflow_workflow,
    WorkflowType,
    OverflowContext,
    load_config,
)
from clickup_framework.exceptions import ClickUpAuthError
from clickup_framework.commands.utils import add_common_args


class OverflowCommand(BaseCommand):
    """
    Execute Git Overflow workflow: Stage → Commit → Push → ClickUp.

    This command automates the entire Git workflow and synchronizes with ClickUp:
    1. Stages all changes
    2. Creates a commit with your message
    3. Pushes to remote (unless --no-push)
    4. Posts commit info to ClickUp task
    5. Updates task status (configurable)
    6. Links commit to task
    """

    def execute(self):
        """Execute the overflow command."""
        # Load configuration
        try:
            config = load_config(search=True)
        except Exception as e:
            self.print_error(f"Warning: Could not load overflow config: {e}")
            self.print_error("Using default configuration")
            config = None

        # Determine task ID
        task_id = self.args.task
        if not task_id:
            # Try to get from context
            task_id = self.context.get_current_task()

        if not task_id:
            self.error("No task specified and no current task set\n\n" +
                      "Please either:\n" +
                      "  1. Set current task: cum set <task_id>\n" +
                      "  2. Specify task:     cum overflow 'message' --task <task_id>")

        # Generate task URL
        task_url = f"https://app.clickup.com/t/{task_id}"

        # Determine workflow type
        workflow_type_map = {
            '0': WorkflowType.DIRECT_COMMIT,
            'direct': WorkflowType.DIRECT_COMMIT,
            '1': WorkflowType.PULL_REQUEST,
            'pr': WorkflowType.PULL_REQUEST,
            '2': WorkflowType.WIP_BRANCH,
            'wip': WorkflowType.WIP_BRANCH,
            '3': WorkflowType.HOTFIX,
            'hotfix': WorkflowType.HOTFIX,
            '4': WorkflowType.MERGE_COMPLETE,
            'merge': WorkflowType.MERGE_COMPLETE,
        }

        workflow_type = workflow_type_map.get(self.args.type.lower(), WorkflowType.DIRECT_COMMIT)

        # Check if workflow type is implemented
        if workflow_type != WorkflowType.DIRECT_COMMIT:
            self.error(f"Workflow type '{self.args.type}' (Workflow {workflow_type.value}) not yet implemented\n" +
                      "Currently only Workflow 0 (direct commit) is available")

        # Create workflow context
        context = OverflowContext(
            task_id=task_id,
            task_url=task_url,
            commit_message=self.args.message,
            workflow_type=workflow_type,
            auto_push=not self.args.no_push,
            update_clickup=not self.args.no_clickup,
            status=self.args.status if self.args.status else None,
            priority=self.args.priority if self.args.priority else None,
            tags=self.args.tags if self.args.tags else None,
            dry_run=self.args.dry_run
        )

        # Create ClickUp client if needed
        client = None
        if context.update_clickup and not self.args.dry_run:
            try:
                client = self.client
            except ClickUpAuthError as e:
                self.print_error(f"Warning: Could not create ClickUp client: {e}")
                self.print_error("Proceeding with Git operations only (no ClickUp updates)")
                context.update_clickup = False
            except Exception as e:
                self.print_error(f"Warning: Unexpected error creating ClickUp client: {e}")
                self.print_error("Proceeding with Git operations only (no ClickUp updates)")
                context.update_clickup = False

        # Display what we're about to do
        if self.args.dry_run:
            self.print("🧪 DRY RUN MODE - No actual changes will be made")
            self.print("")

        self.print(f"📋 Task: {task_id}")
        self.print(f"💬 Message: {self.args.message}")
        self.print(f"🔀 Workflow: {workflow_type.name} (Type {workflow_type.value})")
        self.print(f"📤 Push: {'Yes' if context.auto_push else 'No'}")
        self.print(f"🔗 Update ClickUp: {'Yes' if context.update_clickup else 'No'}")

        if self.args.status:
            self.print(f"📊 Status: {self.args.status}")
        if self.args.priority:
            self.print(f"⚡ Priority: {self.args.priority}")
        if self.args.tags:
            self.print(f"🏷️  Tags: {', '.join(self.args.tags)}")

        self.print("")
        self.print("⏳ Executing workflow...")
        self.print("")

        # Execute workflow
        try:
            result = execute_overflow_workflow(context, config=config, client=client)

            # Display results
            if result.success:
                # ... results displayed via self.print ...
                self.handle_output(data=result.__dict__)
                return result
                # Workflow failed
                self.print_error("❌ Workflow failed!")
                self.print_error("")
                self.print_error(f"Error: {result.error}")

                if result.warnings:
                    self.print_error("")
                    self.print_error("Warnings:")
                    for warning in result.warnings:
                        self.print_error(f"   • {warning}")

                self.error("")

        except KeyboardInterrupt:
            self.print_error("")
            self.print_error("⚠️  Interrupted by user")
            import sys
            sys.exit(130)

        except Exception as e:
            self.print_error(f"❌ Unexpected error: {e}")
            if self.args.verbose:
                import traceback
                self.print_error("")
                self.print_error("Traceback:")
                traceback.print_exc()
            self.error("")


def overflow_command(args):
    """Command wrapper for backward compatibility."""
    command = OverflowCommand(args, command_name='overflow')
    command.execute()


def register_command(subparsers):
    """Register the overflow command with argparse."""
    parser = subparsers.add_parser(
        'overflow',
        help='Git Overflow: Automated Git + ClickUp workflow',
        description='''
Execute automated Git workflow with ClickUp synchronization.

Workflow 0 (Direct Commit):
  1. Stage all changes
  2. Create commit with message
  3. Push to remote (optional)
  4. Post commit info to ClickUp task
  5. Update task status
  6. Link commit to task

Example:
  cum overflow "Add new feature"                    # Use current task
  cum overflow "Fix bug" --task abc123xyz           # Specify task
  cum overflow "WIP: Testing" --no-push --dry-run   # Test without pushing
        ''',
        epilog='''Tips:
  • Quick commit: cum overflow "message" (auto-detects current task)
  • Test first: cum overflow "message" --dry-run
  • Commit without push: cum overflow "message" --no-push
  • Git only (skip ClickUp): cum overflow "message" --no-clickup
  • Automates: git add, commit, push, ClickUp task update, and linking
  • For more info: https://github.com/SOELexicon/clickup_framework'''
    )

    # Required arguments
    parser.add_argument(
        'message',
        help='Commit message (use quotes for messages with spaces)'
    )

    # Task specification
    parser.add_argument(
        '--task', '-t',
        help='Task ID (default: use current task from context)'
    )

    # Workflow options
    parser.add_argument(
        '--type',
        choices=['0', 'direct', '1', 'pr', '2', 'wip', '3', 'hotfix', '4', 'merge'],
        default='0',
        help='Workflow type: 0/direct (default), 1/pr, 2/wip, 3/hotfix, 4/merge'
    )

    parser.add_argument(
        '--no-push',
        action='store_true',
        help='Create commit but do not push to remote'
    )

    parser.add_argument(
        '--no-clickup',
        action='store_true',
        help='Skip ClickUp updates (Git operations only)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Test mode: show what would happen without making changes'
    )

    # ClickUp updates
    parser.add_argument(
        '--status',
        help='Set task status (e.g., "in progress", "complete")'
    )

    parser.add_argument(
        '--priority',
        choices=['urgent', 'high', 'normal', 'low'],
        help='Set task priority'
    )

    parser.add_argument(
        '--tags',
        nargs='+',
        help='Add tags to task (space-separated)'
    )

    # Debugging
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed error information'
    )

    add_common_args(parser)
    parser.set_defaults(func=overflow_command)
