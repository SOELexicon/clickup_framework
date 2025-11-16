"""Task management commands for ClickUp Framework CLI."""

import os
import sys
from collections import defaultdict
from clickup_framework import ClickUpClient, get_context_manager
from clickup_framework.utils.colors import colorize, TextColor, TextStyle
from clickup_framework.utils.animations import ANSIAnimations
from clickup_framework.utils.diff import diff_strings
from clickup_framework.exceptions import ClickUpAPIError
from clickup_framework.commands.utils import read_text_from_file
from clickup_framework.cli_error_handler import handle_cli_error
from clickup_framework.utils.status_mapper import (
    map_status,
    get_available_statuses,
    format_available_statuses,
    suggest_status,
)
from clickup_framework.automation.config import load_automation_config
from clickup_framework.automation.parent_updater import ParentTaskAutomationEngine
from clickup_framework.automation.models import ParentUpdateResult
from clickup_framework.resources.checklist_template_manager import ChecklistTemplateManager
from clickup_framework.parsers import ContentProcessor, ParserContext


def display_automation_result(result: ParentUpdateResult):
    """
    Display automation result to the user.

    Args:
        result: ParentUpdateResult from automation engine
    """
    if result.skip_reason == "parent_already_active":
        print(f"\nℹ️  Parent task already active (status: {result.old_status})")
        print(f"  No update needed for: {result.parent_task_name} [{result.parent_task_id}]")
    elif result.skip_reason == "no_list_id":
        print(f"\n⚠️  Warning: Automatic parent update skipped")
        print(f"  Parent task: {result.parent_task_name} [{result.parent_task_id}]")
        print(f"  Reason: Could not determine parent task's list")
        print(f"  {colorize('→ You may need to manually update the parent task', TextColor.BRIGHT_YELLOW)}")
    elif result.skip_reason == "status_not_available":
        print(f"\n⚠️  Warning: Automatic parent update skipped")
        print(f"  Parent task: {result.parent_task_name} [{result.parent_task_id}]")
        if result.error_message:
            print(f"  {colorize(result.error_message, TextColor.BRIGHT_YELLOW)}")
        print(f"  {colorize('→ You may need to manually update the parent task', TextColor.BRIGHT_YELLOW)}")
    elif result.update_successful:
        print(f"\n🔄 Auto-Update: Parent task updated")
        print(f"  Task: {result.parent_task_name} [{result.parent_task_id}]")
        print(f"  Status: {result.old_status} → {result.new_status}")
        if result.comment_posted:
            print(f"  Comment: Posted automation notice")
        print(f"  Latency: {result.latency_ms}ms")
    else:
        # Failed automation
        print(f"\n⚠️  Warning: Automatic parent update failed")
        print(f"  Parent task: {result.parent_task_name} [{result.parent_task_id}]")
        if result.error_message:
            print(f"  {colorize(result.error_message, TextColor.BRIGHT_YELLOW)}")
        print(f"  {colorize('→ You may need to manually update the parent task', TextColor.BRIGHT_YELLOW)}")


def task_create_command(args):
    """Create a new task."""
    context = get_context_manager()
    client = ClickUpClient()

    # If parent task is provided, get list_id from parent
    if args.parent:
        try:
            parent_task = client.get_task(args.parent)
            list_id = parent_task['list']['id']
            print(f"ℹ️  Using list from parent task: {parent_task['list']['name']} [{list_id}]")
        except Exception as e:
            error_context = {
                'command': 'task_create',
                'parent_task_id': args.parent,
            }
            handle_cli_error(e, error_context)
    elif args.list_id:
        # Resolve "current" to actual list ID
        try:
            list_id = context.resolve_id('list', args.list_id)
        except ValueError as e:
            # Provide helpful error message if "current" is used without setting context
            error_context = {
                'command': 'task_create',
                'provided_list_id': args.list_id,
                'current_workspace': context.get_current_workspace() or 'Not set',
                'current_list': context.get_current_list() or 'Not set',
            }
            handle_cli_error(e, error_context)
    else:
        print("Error: Either list_id or --parent must be provided", file=sys.stderr)
        sys.exit(1)

    # Build task data
    task_data = {'name': args.name}

    # Handle description from argument or file
    description = None
    if args.description_file:
        description = read_text_from_file(args.description_file)
    elif args.description:
        description = args.description

    # Process description through ContentProcessor if provided
    if description:
        process_markdown = getattr(args, 'markdown', True)
        skip_mermaid = getattr(args, 'skip_mermaid', False)

        if process_markdown:
            processor = ContentProcessor(
                context=ParserContext.TASK_DESCRIPTION,
                cache_dir=getattr(args, 'image_cache', None)
            )

            result = processor.process(
                description,
                format_markdown=True,
                process_mermaid=not skip_mermaid,
                convert_mermaid_to_images=not skip_mermaid
            )

            # Use markdown_description if content has markdown
            if result['has_markdown']:
                task_data['markdown_description'] = result['content']
            else:
                task_data['description'] = result['content']

            # Inform about unuploaded images
            if result.get('unuploaded_images'):
                print(f"ℹ️  {len(result['unuploaded_images'])} image(s) in description. Use comment attachment to upload.")
        else:
            task_data['description'] = description

    # Handle status with smart mapping
    if args.status:
        try:
            # Fetch list data to get available statuses
            list_data = client.get_list(list_id)
            available_statuses = get_available_statuses(list_data)

            # Try to map the user's status to an actual status
            mapped_status = map_status(args.status, available_statuses)

            if mapped_status:
                task_data['status'] = mapped_status
                # Show user if we mapped their status
                if mapped_status.lower() != args.status.lower():
                    print(f"ℹ️  Mapped status '{args.status}' → '{mapped_status}'")
            else:
                # No mapping found, try original status (will error if invalid)
                task_data['status'] = args.status
        except Exception:
            # If we can't fetch list data, just use the original status
            task_data['status'] = args.status

    if args.priority is not None:
        # Map priority names to numbers if needed
        priority_map = {
            'urgent': 1,
            'high': 2,
            'normal': 3,
            'low': 4
        }

        priority = args.priority
        if isinstance(priority, str) and priority.lower() in priority_map:
            priority = priority_map[priority.lower()]
        elif isinstance(priority, str):
            try:
                priority = int(priority)
            except ValueError:
                print(f"Error: Invalid priority '{priority}'. Use 1-4 or urgent/high/normal/low", file=sys.stderr)
                sys.exit(1)

        # Validate priority range
        if priority not in [1, 2, 3, 4]:
            print(f"Error: Priority must be 1-4 (1=urgent, 2=high, 3=normal, 4=low). Got: {priority}", file=sys.stderr)
            sys.exit(1)

        task_data['priority'] = priority

    if args.tags:
        task_data['tags'] = args.tags

    if args.assignees:
        task_data['assignees'] = [{'id': aid} for aid in args.assignees]
    else:
        # Use default assignee if none specified
        default_assignee = context.get_default_assignee()
        if default_assignee:
            task_data['assignees'] = [{'id': default_assignee}]

    if args.parent:
        task_data['parent'] = args.parent

    if args.custom_task_ids:
        task_data['custom_task_ids'] = args.custom_task_ids

    if args.check_required_custom_fields is not None:
        task_data['check_required_custom_fields'] = args.check_required_custom_fields

    # Create the task
    try:
        task = client.create_task(list_id, **task_data)

        # Show success message
        success_msg = ANSIAnimations.success_message(f"Task created: {task['name']}")
        print(success_msg)
        print(f"\nTask ID: {colorize(task['id'], TextColor.BRIGHT_GREEN)}")
        print(f"URL: {task['url']}")

        # Apply checklist templates if provided
        if hasattr(args, 'checklist_template') and args.checklist_template:
            print(f"\n{colorize('Applying checklist templates...', TextStyle.BOLD)}")
            template_manager = ChecklistTemplateManager()

            for template_name in args.checklist_template:
                try:
                    result = template_manager.apply_template(client, task['id'], template_name)
                    checklist = result['checklist']
                    items = result['items']
                    print(f"  ✓ Applied template: {colorize(template_name, TextColor.BRIGHT_CYAN)} ({len(items)} items)")
                except ValueError as e:
                    print(f"  ✗ Error applying template '{template_name}': {e}", file=sys.stderr)
                except ClickUpAPIError as e:
                    print(f"  ✗ Error applying template '{template_name}': {e}", file=sys.stderr)

        # Clone checklists from source task if provided
        if hasattr(args, 'clone_checklists_from') and args.clone_checklists_from:
            print(f"\n{colorize('Cloning checklists...', TextStyle.BOLD)}")
            try:
                source_task_id = context.resolve_id('task', args.clone_checklists_from)
                source_task = client.get_task(source_task_id)
                checklists = source_task.get('checklists', [])

                if checklists:
                    for checklist in checklists:
                        checklist_name = checklist.get('name', 'Unnamed')
                        items = checklist.get('items', [])

                        # Create checklist on new task
                        result = client.create_checklist(task['id'], checklist_name)
                        new_checklist_id = result['checklist']['id']

                        # Clone items
                        for item in items:
                            item_name = item.get('name', '')
                            if item_name:
                                client.create_checklist_item(new_checklist_id, item_name)

                        print(f"  ✓ Cloned checklist: {colorize(checklist_name, TextColor.BRIGHT_CYAN)} ({len(items)} items)")
                else:
                    print(f"  No checklists found on source task {source_task_id}")
            except ValueError as e:
                print(f"  ✗ Error cloning checklists: {e}", file=sys.stderr)
            except ClickUpAPIError as e:
                print(f"  ✗ Error cloning checklists: {e}", file=sys.stderr)

        # Show helpful tip
        from clickup_framework.components.tips import show_tip
        show_tips_enabled = getattr(args, 'show_tips', True)
        use_color = context.get_ansi_output()
        show_tip('task_create', use_color=use_color, enabled=show_tips_enabled)

    except Exception as e:
        # If it's a status error, try to get available statuses for the error message
        error_context = {
            'command': 'task_create',
            'list_id': list_id,
            'task_name': args.name,
        }

        # Check if this is a status-related error
        error_str = str(e).lower()
        if 'status' in error_str and args.status:
            error_context['user_provided_status'] = args.status
            try:
                list_data = client.get_list(list_id)
                error_context['available_statuses'] = get_available_statuses(list_data)
            except:
                pass

        handle_cli_error(e, error_context)


def task_update_command(args):
    """Update a task with specified fields."""
    context = get_context_manager()
    client = ClickUpClient()

    # Resolve "current" to actual task ID
    try:
        task_id = context.resolve_id('task', args.task_id)
    except ValueError as e:
        handle_cli_error(e, {'command': args.func.__name__.replace('_command', ''), 'provided_task_id': args.task_id})

    # Build update dictionary from provided arguments
    updates = {}

    if args.name:
        updates['name'] = args.name

    # Handle description from argument or file
    if args.description_file:
        updates['description'] = read_text_from_file(args.description_file)
    elif args.description:
        updates['description'] = args.description

    # Check if diff preview is enabled for description updates
    diff_enabled = os.getenv('CUM_DIFF_ON_UPDATE') or os.getenv('CUM_ENABLE_DIFF_PREVIEW')
    if diff_enabled and 'description' in updates:
        # Fetch current task to get current description
        try:
            current_task = client.get_task(task_id)
            current_description = current_task.get('description', '') or ''
            new_description = updates['description']

            # Only show diff if descriptions are different
            if current_description != new_description:
                # Generate and display diff
                print(f"\n{colorize('Description Changes:', TextColor.BRIGHT_CYAN, TextStyle.BOLD)}")
                print("─" * 60)

                diff_output = diff_strings(
                    current_description,
                    new_description,
                    old_label='current',
                    new_label='new',
                    use_color=context.get_ansi_output()
                )
                print(diff_output)
                print("─" * 60)

                # Prompt for confirmation
                response = input("\nApply this update? (y/N): ")
                if response.lower() not in ['y', 'yes']:
                    print("Update cancelled.")
                    sys.exit(0)
        except Exception as e:
            # If we can't fetch the current task, just continue with the update
            # This prevents diff preview from blocking legitimate updates
            print(f"Warning: Could not fetch current task for diff preview: {e}", file=sys.stderr)

    if args.status:
        updates['status'] = args.status

    if args.priority is not None:
        updates['priority'] = args.priority

    if args.parent:
        updates['parent'] = args.parent

    if args.add_tags:
        # Get current task to append tags
        task = client.get_task(task_id)
        existing_tags = [tag['name'] for tag in task.get('tags', [])]
        all_tags = list(set(existing_tags + args.add_tags))
        updates['tags'] = all_tags

    if args.remove_tags:
        # Get current task to remove tags
        task = client.get_task(task_id)
        existing_tags = [tag['name'] for tag in task.get('tags', [])]
        remaining_tags = [tag for tag in existing_tags if tag not in args.remove_tags]
        updates['tags'] = remaining_tags

    if not updates:
        print("Error: No updates specified. Use --name, --description, --status, --priority, or tag options.", file=sys.stderr)
        sys.exit(1)

    # Perform the update
    try:
        updated_task = client.update_task(task_id, **updates)

        # Show success message with gradient
        success_msg = ANSIAnimations.success_message(f"Task updated: {updated_task.get('name', task_id)}")
        print(success_msg)

        # Show what was updated
        print("\nUpdated fields:")
        for key, value in updates.items():
            if key == 'tags' and isinstance(value, list):
                value_str = ', '.join(value)
            else:
                value_str = str(value)
            print(f"  {colorize(key, TextColor.BRIGHT_CYAN)}: {value_str}")

    except Exception as e:
        handle_cli_error(e, {'command': 'task_update', 'task_id': task_id, 'updates': updates})


def task_delete_command(args):
    """Delete a task."""
    context = get_context_manager()
    client = ClickUpClient()

    # Resolve "current" to actual task ID
    try:
        task_id = context.resolve_id('task', args.task_id)
    except ValueError as e:
        handle_cli_error(e, {'command': args.func.__name__.replace('_command', ''), 'provided_task_id': args.task_id})

    # Get task name for confirmation
    try:
        task = client.get_task(task_id)
        task_name = task['name']
    except Exception as e:
        handle_cli_error(e, {'command': 'task_delete', 'task_id': task_id})

    # Confirmation prompt unless force flag is set
    if not args.force:
        response = input(f"Delete task '{task_name}' [{task_id}]? (y/N): ")
        if response.lower() not in ['y', 'yes']:
            print("Cancelled.")
            return

    # Delete the task
    try:
        client.delete_task(task_id)
        success_msg = ANSIAnimations.success_message(f"Task deleted: {task_name}")
        print(success_msg)

    except Exception as e:
        handle_cli_error(e, {'command': 'task_delete', 'task_id': task_id, 'task_name': task_name})


def task_assign_command(args):
    """Assign users to a task."""
    context = get_context_manager()
    client = ClickUpClient()

    # Resolve "current" to actual task ID
    try:
        task_id = context.resolve_id('task', args.task_id)
    except ValueError as e:
        handle_cli_error(e, {'command': args.func.__name__.replace('_command', ''), 'provided_task_id': args.task_id})

    # Get current task to append assignees
    try:
        task = client.get_task(task_id)
        current_assignees = [a['id'] for a in task.get('assignees', [])]

        # Add new assignees
        all_assignees = list(set(current_assignees + args.assignee_ids))

        # Update task with new assignees
        updated_task = client.update_task(task_id, assignees={'add': args.assignee_ids})

        success_msg = ANSIAnimations.success_message(f"Assigned {len(args.assignee_ids)} user(s) to task")
        print(success_msg)
        print(f"\nTask: {updated_task['name']}")
        print(f"Assignees: {', '.join(args.assignee_ids)}")

    except Exception as e:
        handle_cli_error(e, {'command': 'task_assign', 'task_id': task_id, 'assignee_ids': args.assignee_ids})


def task_unassign_command(args):
    """Remove assignees from a task."""
    context = get_context_manager()
    client = ClickUpClient()

    # Resolve "current" to actual task ID
    try:
        task_id = context.resolve_id('task', args.task_id)
    except ValueError as e:
        handle_cli_error(e, {'command': args.func.__name__.replace('_command', ''), 'provided_task_id': args.task_id})

    # Remove assignees
    try:
        updated_task = client.update_task(task_id, assignees={'rem': args.assignee_ids})

        success_msg = ANSIAnimations.success_message(f"Removed {len(args.assignee_ids)} user(s) from task")
        print(success_msg)
        print(f"\nTask: {updated_task['name']}")

    except Exception as e:
        handle_cli_error(e, {'command': 'task_unassign', 'task_id': task_id, 'assignee_ids': args.assignee_ids})


def task_set_status_command(args):
    """Set task status with subtask validation - supports multiple tasks."""
    context = get_context_manager()
    client = ClickUpClient()

    # Load automation configuration
    automation_config = load_automation_config()
    automation_engine = ParentTaskAutomationEngine(automation_config, client)

    # Check for automation flags
    skip_automation = getattr(args, 'no_parent_update', False)
    force_automation = getattr(args, 'update_parent', False)

    # Resolve all task IDs
    task_ids = []
    for tid in args.task_ids:
        try:
            resolved_id = context.resolve_id('task', tid)
            task_ids.append(resolved_id)
        except ValueError as e:
            print(f"Error resolving '{tid}': {e}", file=sys.stderr)
            sys.exit(1)

    # Process each task
    success_count = 0
    failed_count = 0
    errors_by_type = defaultdict(list)  # {(error_message, status_code): [task_ids]}
    parent_updates = {}  # Track which parents have been updated

    for task_id in task_ids:
        # Get task details to check for subtasks
        try:
            task = client.get_task(task_id)
            list_id = task['list']['id']

            # Get list data for status mapping
            list_data = client.get_list(list_id)
            available_statuses = get_available_statuses(list_data)

            # Map user's status to actual status
            target_status = map_status(args.status, available_statuses)

            # If mapping failed, try original status (will error if invalid)
            if not target_status:
                target_status = args.status
            else:
                # Show user if we mapped their status
                if target_status.lower() != args.status.lower():
                    print(f"ℹ️  Mapped status '{args.status}' → '{target_status}'")

            # Get all tasks in the list to find subtasks
            result = client.get_list_tasks(list_id, subtasks='true')
            all_tasks = result.get('tasks', [])

            # Find subtasks of this task
            subtasks = [t for t in all_tasks if t.get('parent') == task_id]

            # Check if any subtasks have different status
            mismatched_subtasks = []
            for subtask in subtasks:
                subtask_status = subtask.get('status', {})
                if isinstance(subtask_status, dict):
                    subtask_status = subtask_status.get('status', '')
                if subtask_status.lower() != target_status.lower():
                    mismatched_subtasks.append(subtask)

            # If there are mismatched subtasks, show them and skip this task
            if mismatched_subtasks:
                print(ANSIAnimations.warning_message(
                    f"Cannot set status to '{target_status}' for task '{task['name']}' - {len(mismatched_subtasks)} subtask(s) have different status"
                ))
                print(f"\nTask: {colorize(task['name'], TextColor.BRIGHT_CYAN)} [{task_id}]")
                print(f"Target status: {colorize(target_status, TextColor.BRIGHT_YELLOW)}\n")

                # Display subtasks in formatted tree view
                print(colorize("Subtasks requiring status update:", TextColor.BRIGHT_WHITE, TextStyle.BOLD))
                print()

                for i, subtask in enumerate(mismatched_subtasks, 1):
                    subtask_status = subtask.get('status', {})
                    if isinstance(subtask_status, dict):
                        current_status = subtask_status.get('status', 'Unknown')
                        status_color = subtask_status.get('color', '#87909e')
                    else:
                        current_status = subtask_status
                        status_color = '#87909e'

                    # Format status with color
                    from clickup_framework.utils.colors import status_color as get_status_color
                    status_colored = colorize(current_status, get_status_color(current_status), TextStyle.BOLD)

                    # Show task info
                    task_name = colorize(subtask['name'], TextColor.BRIGHT_WHITE)
                    task_id_colored = colorize(f"[{subtask['id']}]", TextColor.BRIGHT_BLACK)

                    print(f"  {i}. {task_id_colored} {task_name}")
                    print(f"     Current status: {status_colored}")
                    print()

                print(colorize("Update these subtasks first, then retry.", TextColor.BRIGHT_BLUE))
                print()
                failed_count += 1
                continue

            # No mismatched subtasks, proceed with update
            # Get old status for automation tracking
            old_status = task.get('status', {})
            if isinstance(old_status, dict):
                old_status = old_status.get('status', '')

            updated_task = client.update_task(task_id, status=target_status)

            success_msg = ANSIAnimations.success_message(f"Status updated")
            print(success_msg)
            print(f"\nTask: {updated_task['name']} [{task_id}]")
            print(f"New status: {colorize(target_status, TextColor.BRIGHT_YELLOW)}")

            if subtasks:
                print(f"Subtasks: {len(subtasks)} subtask(s) also have status '{target_status}'")

            # Handle parent automation
            parent_id = task.get('parent')
            if parent_id:
                # Check if we've already updated this parent (for batching multiple subtasks)
                if parent_id not in parent_updates:
                    event = automation_engine.handle_status_update(
                        task_id=task_id,
                        old_status=old_status,
                        new_status=target_status,
                        force_update=force_automation,
                        skip_automation=skip_automation
                    )

                    # Display automation result
                    if event.automation_triggered and event.automation_result:
                        display_automation_result(event.automation_result)
                        parent_updates[parent_id] = True
                else:
                    # Parent already updated by another subtask
                    print(f"\nℹ️  Parent already updated (skipped for this subtask)")

            if len(task_ids) > 1:
                print()  # Extra spacing between tasks

            success_count += 1

        except ClickUpAPIError as e:
            # Collect API errors by type and status code
            error_key = (e.message, e.status_code)
            errors_by_type[error_key].append(task_id)
            failed_count += 1
            continue
        except Exception as e:
            # Collect other errors
            error_key = (str(e), None)
            errors_by_type[error_key].append(task_id)
            failed_count += 1
            continue

    # Summary for multiple tasks
    if len(task_ids) > 1:
        print(f"\n{colorize('Summary:', TextColor.BRIGHT_WHITE, TextStyle.BOLD)}")
        print(f"  Updated: {success_count}/{len(task_ids)} tasks")
        if failed_count > 0:
            print(f"  Failed: {failed_count}/{len(task_ids)} tasks")

    # Display grouped errors if any
    if errors_by_type:
        print(f"\n{colorize('Errors:', TextColor.BRIGHT_RED, TextStyle.BOLD)}")
        for (error_msg, status_code), task_list in sorted(errors_by_type.items()):
            if status_code:
                print(f"{error_msg}: {colorize(str(status_code), TextColor.BRIGHT_YELLOW)}")
            else:
                print(f"{error_msg}")
            # Format task IDs in a comma-separated list
            task_ids_str = ', '.join(task_list)
            print(f"   - ({colorize(task_ids_str, TextColor.BRIGHT_BLACK)})")
            print()

    if failed_count > 0:
        sys.exit(1)


def task_set_priority_command(args):
    """Set task priority."""
    context = get_context_manager()
    client = ClickUpClient()

    # Resolve "current" to actual task ID
    try:
        task_id = context.resolve_id('task', args.task_id)
    except ValueError as e:
        handle_cli_error(e, {'command': args.func.__name__.replace('_command', ''), 'provided_task_id': args.task_id})

    # Map priority names to numbers if needed
    priority_map = {
        'urgent': 1,
        'high': 2,
        'normal': 3,
        'low': 4
    }

    priority = args.priority
    if isinstance(priority, str) and priority.lower() in priority_map:
        priority = priority_map[priority.lower()]
    elif isinstance(priority, str):
        try:
            priority = int(priority)
        except ValueError:
            print(f"Error: Invalid priority '{priority}'. Use 1-4 or urgent/high/normal/low", file=sys.stderr)
            sys.exit(1)

    # Update priority
    try:
        updated_task = client.update_task(task_id, priority=priority)

        success_msg = ANSIAnimations.success_message(f"Priority updated")
        print(success_msg)
        print(f"\nTask: {updated_task['name']}")
        print(f"New priority: {colorize(str(priority), TextColor.BRIGHT_RED)}")

    except Exception as e:
        print(f"Error setting priority: {e}", file=sys.stderr)
        sys.exit(1)


def task_set_tags_command(args):
    """Set/manage task tags."""
    context = get_context_manager()
    client = ClickUpClient()

    # Resolve "current" to actual task ID
    try:
        task_id = context.resolve_id('task', args.task_id)
    except ValueError as e:
        handle_cli_error(e, {'command': args.func.__name__.replace('_command', ''), 'provided_task_id': args.task_id})

    # Get current task
    try:
        task = client.get_task(task_id)
        existing_tags = [tag['name'] for tag in task.get('tags', [])]

        new_tags = existing_tags.copy()

        # Handle different tag operations
        if args.add:
            new_tags.extend(args.add)
            new_tags = list(set(new_tags))  # Remove duplicates
            action = f"Added {len(args.add)} tag(s)"
        elif args.remove:
            new_tags = [t for t in new_tags if t not in args.remove]
            action = f"Removed {len(args.remove)} tag(s)"
        elif args.set:
            new_tags = args.set
            action = "Set tags"
        else:
            print("Error: Use --add, --remove, or --set to modify tags", file=sys.stderr)
            sys.exit(1)

        # Update task with new tags
        updated_task = client.update_task(task_id, tags=new_tags)

        success_msg = ANSIAnimations.success_message(action)
        print(success_msg)
        print(f"\nTask: {updated_task['name']}")
        print(f"Tags: {colorize(', '.join(new_tags) if new_tags else '(none)', TextColor.BRIGHT_MAGENTA)}")

    except Exception as e:
        print(f"Error setting tags: {e}", file=sys.stderr)
        sys.exit(1)


def task_add_dependency_command(args):
    """Add a dependency relationship between tasks."""
    context = get_context_manager()
    client = ClickUpClient()

    # Resolve "current" to actual task ID
    try:
        task_id = context.resolve_id('task', args.task_id)
    except ValueError as e:
        handle_cli_error(e, {'command': args.func.__name__.replace('_command', ''), 'provided_task_id': args.task_id})

    # Validate that exactly one relationship type is provided
    if not args.waiting_on and not args.blocking:
        print("Error: Must provide either --waiting-on or --blocking", file=sys.stderr)
        sys.exit(1)

    if args.waiting_on and args.blocking:
        print("Error: Cannot provide both --waiting-on and --blocking", file=sys.stderr)
        sys.exit(1)

    # Resolve dependency task IDs
    try:
        if args.waiting_on:
            depends_on_id = context.resolve_id('task', args.waiting_on)
            result = client.add_task_dependency(task_id, depends_on=depends_on_id)
            relationship_type = "waiting on"
            other_task = depends_on_id
        else:
            dependency_of_id = context.resolve_id('task', args.blocking)
            result = client.add_task_dependency(task_id, dependency_of=dependency_of_id)
            relationship_type = "blocking"
            other_task = dependency_of_id
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error adding dependency: {e}", file=sys.stderr)
        sys.exit(1)

    # Show success message
    success_msg = ANSIAnimations.success_message(
        f"Task {task_id} now {relationship_type} {other_task}"
    )
    print(success_msg)


def task_remove_dependency_command(args):
    """Remove a dependency relationship between tasks."""
    context = get_context_manager()
    client = ClickUpClient()

    # Resolve "current" to actual task ID
    try:
        task_id = context.resolve_id('task', args.task_id)
    except ValueError as e:
        handle_cli_error(e, {'command': args.func.__name__.replace('_command', ''), 'provided_task_id': args.task_id})

    # Validate that exactly one relationship type is provided
    if not args.waiting_on and not args.blocking:
        print("Error: Must provide either --waiting-on or --blocking", file=sys.stderr)
        sys.exit(1)

    if args.waiting_on and args.blocking:
        print("Error: Cannot provide both --waiting-on and --blocking", file=sys.stderr)
        sys.exit(1)

    # Resolve dependency task IDs
    try:
        if args.waiting_on:
            depends_on_id = context.resolve_id('task', args.waiting_on)
            result = client.delete_task_dependency(task_id, depends_on=depends_on_id)
            relationship_type = "waiting on"
            other_task = depends_on_id
        else:
            dependency_of_id = context.resolve_id('task', args.blocking)
            result = client.delete_task_dependency(task_id, dependency_of=dependency_of_id)
            relationship_type = "blocking"
            other_task = dependency_of_id
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error removing dependency: {e}", file=sys.stderr)
        sys.exit(1)

    # Show success message
    success_msg = ANSIAnimations.success_message(
        f"Dependency removed: {task_id} no longer {relationship_type} {other_task}"
    )
    print(success_msg)


def task_add_link_command(args):
    """Link two tasks together."""
    context = get_context_manager()
    client = ClickUpClient()

    # Resolve "current" to actual task IDs
    try:
        task_id = context.resolve_id('task', args.task_id)
        links_to_id = context.resolve_id('task', args.linked_task_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Add link
    try:
        result = client.add_task_link(task_id, links_to_id)

        # Show success message
        success_msg = ANSIAnimations.success_message(
            f"Tasks linked: {task_id} ↔ {links_to_id}"
        )
        print(success_msg)

        # Optionally show updated task info
        if hasattr(args, 'verbose') and args.verbose:
            task = client.get_task(task_id)
            linked_count = len(task.get('linked_tasks', []))
            print(f"  Total links for {task_id}: {linked_count}")

    except Exception as e:
        print(f"Error linking tasks: {e}", file=sys.stderr)
        sys.exit(1)


def task_remove_link_command(args):
    """Remove a link between two tasks."""
    context = get_context_manager()
    client = ClickUpClient()

    # Resolve "current" to actual task IDs
    try:
        task_id = context.resolve_id('task', args.task_id)
        links_to_id = context.resolve_id('task', args.linked_task_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Remove link
    try:
        result = client.delete_task_link(task_id, links_to_id)

        # Show success message
        success_msg = ANSIAnimations.success_message(
            f"Link removed: {task_id} ↔ {links_to_id}"
        )
        print(success_msg)

    except Exception as e:
        print(f"Error removing link: {e}", file=sys.stderr)
        sys.exit(1)


def register_command(subparsers):
    """Register task management commands."""
    # Task create
    task_create_parser = subparsers.add_parser(
        'task_create',
        aliases=['tc'],
        help='Create a new task',
        description='Create a new task in a ClickUp list with optional metadata and relationships.',
        epilog='''Tips:
  • Create task in current list: cum tc "My Task" --list current
  • Create subtask under parent: cum tc "Subtask" --parent 86abc123
  • Set priority with name or number: cum tc "Urgent" --priority urgent (or --priority 1)
  • Apply checklist template: cum tc "Task" --list current --checklist-template "dev-workflow"
  • Clone checklists from another task: cum tc "New" --list current --clone-checklists-from current'''
    )
    task_create_parser.add_argument('name', help='Task name')
    task_create_parser.add_argument('--list', dest='list_id', help='List ID to create task in (or "current"). Not required if --parent is provided.')
    description_group = task_create_parser.add_mutually_exclusive_group()
    description_group.add_argument('--description', help='Task description')
    description_group.add_argument('--description-file', help='Read task description from file')
    task_create_parser.add_argument('--status', help='Task status')
    task_create_parser.add_argument('--priority', help='Task priority (1-4 or urgent/high/normal/low)')
    task_create_parser.add_argument('--tags', nargs='+', help='Tags to add')
    task_create_parser.add_argument('--assignees', nargs='+', help='Assignee IDs')
    task_create_parser.add_argument('--parent', help='Parent task ID')
    task_create_parser.add_argument('--custom-task-ids', dest='custom_task_ids', action='store_true',
                                    help='Use custom task IDs (requires workspace setting enabled)')
    task_create_parser.add_argument('--check-required-custom-fields', dest='check_required_custom_fields',
                                    type=lambda x: x.lower() == 'true', metavar='true|false',
                                    help='Check required custom fields (default: true)')
    task_create_parser.add_argument('--checklist-template', action='append', metavar='TEMPLATE',
                                    help='Apply checklist template(s) to the task. Can be used multiple times. Use "cum checklist template list" to see available templates.')
    task_create_parser.add_argument('--clone-checklists-from', metavar='TASK_ID',
                                    help='Clone all checklists from the specified task ID (or "current")')
    task_create_parser.add_argument('--no-markdown', dest='markdown', action='store_false',
                                    help='Disable markdown formatting in description')
    task_create_parser.add_argument('--skip-mermaid', action='store_true',
                                    help='Skip mermaid diagram processing in description')
    task_create_parser.add_argument('--image-cache', help='Directory for image cache')
    task_create_parser.set_defaults(func=task_create_command)

    # Task update
    task_update_parser = subparsers.add_parser(
        'task_update',
        aliases=['tu'],
        help='Update a task',
        description='Update an existing task with new values for name, description, status, priority, tags, or parent.',
        epilog='''Tips:
  • Update task name: cum tu current --name "New Name"
  • Change status: cum tu 86abc123 --status "in progress"
  • Add tags: cum tu current --add-tags bug urgent
  • Update from file: cum tu current --description-file notes.md
  • Move to new parent: cum tu 86abc123 --parent 86def456'''
    )
    task_update_parser.add_argument('task_id', help='Task ID to update (or "current")')
    task_update_parser.add_argument('--name', help='New task name')
    description_update_group = task_update_parser.add_mutually_exclusive_group()
    description_update_group.add_argument('--description', help='New task description')
    description_update_group.add_argument('--description-file', help='Read new task description from file')
    task_update_parser.add_argument('--status', help='New task status')
    task_update_parser.add_argument('--priority', type=int, help='New task priority (1-4)')
    task_update_parser.add_argument('--add-tags', nargs='+', help='Tags to add')
    task_update_parser.add_argument('--remove-tags', nargs='+', help='Tags to remove')
    task_update_parser.add_argument('--parent', help='New parent task ID')
    task_update_parser.set_defaults(func=task_update_command)

    # Task delete
    task_delete_parser = subparsers.add_parser(
        'task_delete',
        aliases=['td'],
        help='Delete a task',
        description='Permanently delete a task from ClickUp with optional confirmation prompt.',
        epilog='''Tips:
  • Delete with confirmation: cum td 86abc123 (prompts for confirmation)
  • Force delete without prompt: cum td 86abc123 --force
  • Delete current task: cum td current
  • Be careful - deletion is permanent!
  • Consider archiving instead of deleting when possible'''
    )
    task_delete_parser.add_argument('task_id', help='Task ID to delete (or "current")')
    task_delete_parser.add_argument('--force', '-f', action='store_true',
                                    help='Skip confirmation prompt')
    task_delete_parser.set_defaults(func=task_delete_command)

    # Task assign
    task_assign_parser = subparsers.add_parser(
        'task_assign',
        aliases=['ta'],
        help='Assign users to a task',
        description='Assign one or more users to a task by their user IDs.',
        epilog='''Tips:
  • Assign single user: cum ta current 12345678
  • Assign multiple users: cum ta 86abc123 12345678 87654321
  • Find user IDs in ClickUp settings or team directory
  • Assignments are additive - existing assignees remain
  • Use task_unassign to remove assignees'''
    )
    task_assign_parser.add_argument('task_id', help='Task ID (or "current")')
    task_assign_parser.add_argument('assignee_ids', nargs='+', help='User IDs to assign')
    task_assign_parser.set_defaults(func=task_assign_command)

    # Task unassign
    task_unassign_parser = subparsers.add_parser(
        'task_unassign',
        aliases=['tua'],
        help='Remove assignees from a task',
        description='Remove one or more users from a task by their user IDs.',
        epilog='''Tips:
  • Remove single user: cum tua current 12345678
  • Remove multiple users: cum tua 86abc123 12345678 87654321
  • Use cum d <task_id> to see current assignees
  • Other assignees remain on the task
  • Use task_assign to add assignees back'''
    )
    task_unassign_parser.add_argument('task_id', help='Task ID (or "current")')
    task_unassign_parser.add_argument('assignee_ids', nargs='+', help='User IDs to remove')
    task_unassign_parser.set_defaults(func=task_unassign_command)

    # Task set status
    task_set_status_parser = subparsers.add_parser(
        'task_set_status',
        aliases=['tss'],
        help='Set task status',
        description='Set the status of one or more tasks with smart status mapping and subtask validation.',
        epilog='''Tips:
  • Set single task: cum tss current "in progress"
  • Set multiple tasks: cum tss 86abc123 86def456 "completed"
  • Status names are case-insensitive and fuzzy-matched
  • Parent tasks require matching subtask statuses
  • Use --no-parent-update to skip parent automation
  • Use --update-parent to force parent status update'''
    )
    task_set_status_parser.add_argument('task_ids', nargs='+', help='Task ID(s) (or "current")')
    task_set_status_parser.add_argument('status', help='New status')
    task_set_status_parser.add_argument('--no-parent-update', action='store_true',
                                        help='Skip automatic parent task update')
    task_set_status_parser.add_argument('--update-parent', action='store_true',
                                        help='Force parent update even if automation disabled')
    task_set_status_parser.set_defaults(func=task_set_status_command)

    # Task set priority
    task_set_priority_parser = subparsers.add_parser(
        'task_set_priority',
        aliases=['tsp'],
        help='Set task priority',
        description='Set the priority level of a task using numbers (1-4) or names (urgent/high/normal/low).',
        epilog='''Tips:
  • Set by number: cum tsp current 1 (1=urgent, 2=high, 3=normal, 4=low)
  • Set by name: cum tsp current urgent
  • Priority names are case-insensitive: "URGENT" or "urgent"
  • View current priority: cum d <task_id>
  • Urgent tasks (P1) appear at the top in most views'''
    )
    task_set_priority_parser.add_argument('task_id', help='Task ID (or "current")')
    task_set_priority_parser.add_argument('priority', help='Priority (1-4 or urgent/high/normal/low)')
    task_set_priority_parser.set_defaults(func=task_set_priority_command)

    # Task set tags
    task_set_tags_parser = subparsers.add_parser(
        'task_set_tags',
        aliases=['tst'],
        help='Manage task tags',
        description='Add, remove, or replace tags on a task for better organization and filtering.',
        epilog='''Tips:
  • Add tags: cum tst current --add bug frontend
  • Remove tags: cum tst current --remove old-tag
  • Replace all tags: cum tst current --set feature v2.0
  • View current tags: cum d <task_id>
  • Use tags for filtering: cum filter <list_id> --tags bug'''
    )
    task_set_tags_parser.add_argument('task_id', help='Task ID (or "current")')
    task_set_tags_group = task_set_tags_parser.add_mutually_exclusive_group(required=True)
    task_set_tags_group.add_argument('--add', nargs='+', help='Tags to add')
    task_set_tags_group.add_argument('--remove', nargs='+', help='Tags to remove')
    task_set_tags_group.add_argument('--set', nargs='+', help='Set tags (replace all)')
    task_set_tags_parser.set_defaults(func=task_set_tags_command)

    # Task add dependency
    task_add_dep_parser = subparsers.add_parser(
        'task_add_dependency',
        aliases=['tad'],
        help='Add dependency relationship between tasks',
        description='Create a dependency relationship where one task must wait for or blocks another task.',
        epilog='''Tips:
  • Make task wait: cum tad current --waiting-on 86abc123
  • Make task block: cum tad current --blocking 86def456
  • "Waiting-on" means current task depends on the other
  • "Blocking" means other task depends on current
  • View dependencies: cum d <task_id>
  • Dependencies affect task ordering in "assigned" view'''
    )
    task_add_dep_parser.add_argument('task_id', help='Task ID (or "current")')
    task_add_dep_parser.add_argument('--waiting-on', dest='waiting_on',
                                      help='Task ID that this task depends on (waiting-on relationship)')
    task_add_dep_parser.add_argument('--blocking',
                                      help='Task ID that depends on this task (blocking relationship)')
    task_add_dep_parser.set_defaults(func=task_add_dependency_command)

    # Task remove dependency
    task_rm_dep_parser = subparsers.add_parser(
        'task_remove_dependency',
        aliases=['trd'],
        help='Remove dependency relationship between tasks',
        description='Remove an existing dependency relationship between two tasks.',
        epilog='''Tips:
  • Remove waiting-on: cum trd current --waiting-on 86abc123
  • Remove blocking: cum trd current --blocking 86def456
  • View current dependencies: cum d <task_id>
  • Must match the original relationship type
  • Task becomes independent after removal'''
    )
    task_rm_dep_parser.add_argument('task_id', help='Task ID (or "current")')
    task_rm_dep_parser.add_argument('--waiting-on', dest='waiting_on',
                                     help='Task ID to remove from "waiting on" list')
    task_rm_dep_parser.add_argument('--blocking',
                                     help='Task ID to remove from "blocking" list')
    task_rm_dep_parser.set_defaults(func=task_remove_dependency_command)

    # Task add link
    task_link_parser = subparsers.add_parser(
        'task_add_link',
        aliases=['tal'],
        help='Link two tasks together',
        description='Create a bidirectional link between two related tasks without dependency constraints.',
        epilog='''Tips:
  • Link tasks: cum tal current 86abc123
  • Links are bidirectional (both tasks show the link)
  • Links are different from dependencies (no blocking)
  • Use for related work, references, or context
  • Use --verbose to see total link count after creation'''
    )
    task_link_parser.add_argument('task_id', help='Task ID to link from (or "current")')
    task_link_parser.add_argument('linked_task_id', help='Task ID to link to')
    task_link_parser.add_argument('--verbose', '-v', action='store_true',
                                   help='Show additional information about the link')
    task_link_parser.set_defaults(func=task_add_link_command)

    # Task remove link
    task_unlink_parser = subparsers.add_parser(
        'task_remove_link',
        aliases=['trl'],
        help='Remove link between two tasks',
        description='Remove an existing bidirectional link between two tasks.',
        epilog='''Tips:
  • Remove link: cum trl current 86abc123
  • Removes link from both tasks (bidirectional)
  • View current links: cum d <task_id>
  • Use task_add_link to recreate if needed
  • Does not affect dependencies or other relationships'''
    )
    task_unlink_parser.add_argument('task_id', help='Task ID to unlink from (or "current")')
    task_unlink_parser.add_argument('linked_task_id', help='Task ID to unlink')
    task_unlink_parser.set_defaults(func=task_remove_link_command)
