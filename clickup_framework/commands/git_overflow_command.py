"""Git Overflow command - Automated Git + ClickUp workflow integration."""

import sys
from clickup_framework.context import get_context_manager
from clickup_framework.client import ClickUpClient
from clickup_framework.git import (
    execute_overflow_workflow,
    WorkflowType,
    OverflowContext,
    load_config,
)
from clickup_framework.exceptions import ClickUpAuthError


def overflow_command(args):
    """
    Execute Git Overflow workflow: Stage → Commit → Push → ClickUp.

    This command automates the entire Git workflow and synchronizes with ClickUp:
    1. Stages all changes
    2. Creates a commit with your message
    3. Pushes to remote (unless --no-push)
    4. Posts commit info to ClickUp task
    5. Updates task status (configurable)
    6. Links commit to task

    Usage:
        cum overflow "Commit message"                    # Use current task
        cum overflow "Commit message" --task TASK_ID     # Specify task
        cum overflow "Commit message" --dry-run          # Test without changes
        cum overflow "Commit message" --no-push          # Don't push to remote
    """
    # Load configuration
    try:
        config = load_config(search=True)
    except Exception as e:
        print(f"Warning: Could not load overflow config: {e}", file=sys.stderr)
        print("Using default configuration", file=sys.stderr)
        config = None

    # Determine task ID
    task_id = args.task
    if not task_id:
        # Try to get from context
        context_mgr = get_context_manager()
        task_id = context_mgr.get_current_task()

    if not task_id:
        print("Error: No task specified and no current task set", file=sys.stderr)
        print("", file=sys.stderr)
        print("Please either:", file=sys.stderr)
        print("  1. Set current task: cum set <task_id>", file=sys.stderr)
        print("  2. Specify task:     cum overflow 'message' --task <task_id>", file=sys.stderr)
        sys.exit(1)

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

    workflow_type = workflow_type_map.get(args.type.lower(), WorkflowType.DIRECT_COMMIT)

    # Check if workflow type is implemented
    if workflow_type != WorkflowType.DIRECT_COMMIT:
        print(f"Error: Workflow type '{args.type}' (Workflow {workflow_type.value}) not yet implemented", file=sys.stderr)
        print("Currently only Workflow 0 (direct commit) is available", file=sys.stderr)
        sys.exit(1)

    # Create workflow context
    context = OverflowContext(
        task_id=task_id,
        task_url=task_url,
        commit_message=args.message,
        workflow_type=workflow_type,
        auto_push=not args.no_push,
        update_clickup=not args.no_clickup,
        status=args.status if args.status else None,
        priority=args.priority if args.priority else None,
        tags=args.tags if args.tags else None,
        dry_run=args.dry_run
    )

    # Create ClickUp client if needed
    client = None
    if context.update_clickup and not args.dry_run:
        try:
            client = ClickUpClient()
        except ClickUpAuthError as e:
            print(f"Warning: Could not create ClickUp client: {e}", file=sys.stderr)
            print("Proceeding with Git operations only (no ClickUp updates)", file=sys.stderr)
            context.update_clickup = False
        except Exception as e:
            print(f"Warning: Unexpected error creating ClickUp client: {e}", file=sys.stderr)
            print("Proceeding with Git operations only (no ClickUp updates)", file=sys.stderr)
            context.update_clickup = False

    # Display what we're about to do
    if args.dry_run:
        print("🧪 DRY RUN MODE - No actual changes will be made")
        print("")

    print(f"📋 Task: {task_id}")
    print(f"💬 Message: {args.message}")
    print(f"🔀 Workflow: {workflow_type.name} (Type {workflow_type.value})")
    print(f"📤 Push: {'Yes' if context.auto_push else 'No'}")
    print(f"🔗 Update ClickUp: {'Yes' if context.update_clickup else 'No'}")

    if args.status:
        print(f"📊 Status: {args.status}")
    if args.priority:
        print(f"⚡ Priority: {args.priority}")
    if args.tags:
        print(f"🏷️  Tags: {', '.join(args.tags)}")

    print("")
    print("⏳ Executing workflow...")
    print("")

    # Execute workflow
    try:
        result = execute_overflow_workflow(context, config=config, client=client)

        # Display results
        if result.success:
            print("✅ Workflow completed successfully!")
            print("")

            if result.commit_result:
                commit = result.commit_result
                print(f"📝 Commit: {commit.commit_sha_short}")

                if commit.author_name:
                    print(f"👤 Author: {commit.author_name} <{commit.author_email}>")

                print(f"📁 Files changed: {commit.files_changed_count}")
                print(f"   +{commit.additions} -{commit.deletions}")

                if commit.pushed:
                    print(f"📤 Pushed to {commit.branch}")
                elif commit.push_error:
                    print(f"⚠️  Push failed: {commit.push_error}", file=sys.stderr)

                if commit.commit_url:
                    print(f"🔗 {commit.commit_url}")

                print("")

            if result.clickup_update:
                clickup = result.clickup_update
                if clickup.applied:
                    print("🔗 ClickUp updated:")
                    if clickup.comment:
                        print("   ✓ Comment posted")
                    if clickup.status:
                        print(f"   ✓ Status set to '{clickup.status}'")
                    print("")
                elif clickup.error:
                    print(f"⚠️  ClickUp update failed: {clickup.error}", file=sys.stderr)
                    print("")

            # Show warnings
            if result.warnings:
                print("⚠️  Warnings:")
                for warning in result.warnings:
                    print(f"   • {warning}")
                print("")

            print(f"⏱️  Duration: {result.duration_seconds:.2f}s")

        else:
            # Workflow failed
            print("❌ Workflow failed!", file=sys.stderr)
            print("", file=sys.stderr)
            print(f"Error: {result.error}", file=sys.stderr)

            if result.warnings:
                print("", file=sys.stderr)
                print("Warnings:", file=sys.stderr)
                for warning in result.warnings:
                    print(f"   • {warning}", file=sys.stderr)

            sys.exit(1)

    except KeyboardInterrupt:
        print("", file=sys.stderr)
        print("⚠️  Interrupted by user", file=sys.stderr)
        sys.exit(130)

    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            print("", file=sys.stderr)
            print("Traceback:", file=sys.stderr)
            traceback.print_exc()
        sys.exit(1)


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
        epilog='For more info: https://github.com/SOELexicon/clickup_framework'
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

    parser.set_defaults(func=overflow_command)
