#!/usr/bin/env python3
"""
ClickUp Framework CLI

Command-line interface for ClickUp Framework display components.
Provides easy access to all view modes and formatting options.

Usage:
    python -m clickup_framework.cli hierarchy <list_id>
    python -m clickup_framework.cli container <list_id>
    python -m clickup_framework.cli detail <task_id> <list_id>
    python -m clickup_framework.cli filter <list_id> --status "in progress"
    python -m clickup_framework.cli assigned [--user-id <user_id>] [--team-id <team_id>]
"""

import argparse
import sys
import os
from typing import Optional

from clickup_framework import ClickUpClient, ContextManager, get_context_manager
from clickup_framework.components import (
    DisplayManager,
    FormatOptions,
    TaskDetailFormatter
)
from clickup_framework.utils.colors import colorize, TextColor, TextStyle
from clickup_framework.utils.animations import ANSIAnimations


def get_list_statuses(client: ClickUpClient, list_id: str, use_color: bool = True) -> str:
    """
    Get and format available statuses for a list with caching.

    Args:
        client: ClickUpClient instance
        list_id: List ID
        use_color: Whether to colorize output

    Returns:
        Formatted string showing available statuses
    """
    from clickup_framework.utils.colors import status_color as get_status_color

    try:
        context = get_context_manager()

        # Try to get from cache first
        cached_metadata = context.get_cached_list_metadata(list_id)

        if cached_metadata:
            list_data = cached_metadata
        else:
            # Fetch from API and cache
            list_data = client.get_list(list_id)
            context.cache_list_metadata(list_id, list_data)

        statuses = list_data.get('statuses', [])

        if not statuses:
            return ""

        # Format status display
        status_parts = []
        for status in statuses:
            status_name = status.get('status', 'Unknown')

            if use_color:
                # Use our status color mapping
                color = get_status_color(status_name)
                status_parts.append(colorize(status_name, color, TextStyle.BOLD))
            else:
                status_parts.append(status_name)

        status_line = " → ".join(status_parts)

        if use_color:
            header = colorize("Available Statuses:", TextColor.BRIGHT_BLUE, TextStyle.BOLD) + f" {status_line}"
        else:
            header = f"Available Statuses: {status_line}"

        return header
    except Exception:
        # If anything fails (e.g., in tests or network issues), silently return empty string
        return ""


def create_format_options(args) -> FormatOptions:
    """Create FormatOptions from command-line arguments."""
    # Check context for ANSI output setting
    context = get_context_manager()
    default_colorize = context.get_ansi_output()

    # Use preset if specified
    if hasattr(args, 'preset') and args.preset:
        if args.preset == 'minimal':
            options = FormatOptions.minimal()
        elif args.preset == 'summary':
            options = FormatOptions.summary()
        elif args.preset == 'detailed':
            options = FormatOptions.detailed()
        elif args.preset == 'full':
            options = FormatOptions.full()
        else:
            options = FormatOptions()

        # Override colorize based on context setting
        options.colorize_output = default_colorize
        return options

    # Otherwise build from individual flags
    return FormatOptions(
        colorize_output=getattr(args, 'colorize', default_colorize),
        show_ids=getattr(args, 'show_ids', False),
        show_tags=getattr(args, 'show_tags', True),
        show_descriptions=getattr(args, 'show_descriptions', False),
        show_dates=getattr(args, 'show_dates', False),
        show_comments=getattr(args, 'show_comments', 0),
        include_completed=getattr(args, 'include_completed', False),
        show_type_emoji=getattr(args, 'show_emoji', True)
    )


def hierarchy_command(args):
    """Display tasks in hierarchical parent-child view."""
    context = get_context_manager()
    client = ClickUpClient()
    display = DisplayManager(client)

    # Resolve "current" to actual list ID
    try:
        list_id = context.resolve_id('list', args.list_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    result = client.get_list_tasks(list_id)
    tasks = result.get('tasks', [])
    options = create_format_options(args)

    # Show available statuses
    colorize = getattr(args, 'colorize', True)
    status_line = get_list_statuses(client, list_id, use_color=colorize)
    if status_line:
        print(status_line)
        print()  # Empty line for spacing

    header = args.header if hasattr(args, 'header') and args.header else None
    output = display.hierarchy_view(tasks, options, header)

    print(output)


def container_command(args):
    """Display tasks organized by container hierarchy."""
    context = get_context_manager()
    client = ClickUpClient()
    display = DisplayManager(client)

    # Resolve "current" to actual list ID
    try:
        list_id = context.resolve_id('list', args.list_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    result = client.get_list_tasks(list_id)
    tasks = result.get('tasks', [])
    options = create_format_options(args)

    # Show available statuses
    colorize = getattr(args, 'colorize', True)
    status_line = get_list_statuses(client, list_id, use_color=colorize)
    if status_line:
        print(status_line)
        print()  # Empty line for spacing

    output = display.container_view(tasks, options)

    print(output)


def flat_command(args):
    """Display tasks in a flat list."""
    context = get_context_manager()
    client = ClickUpClient()
    display = DisplayManager(client)

    # Resolve "current" to actual list ID
    try:
        list_id = context.resolve_id('list', args.list_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    result = client.get_list_tasks(list_id)
    tasks = result.get('tasks', [])
    options = create_format_options(args)

    # Show available statuses
    colorize = getattr(args, 'colorize', True)
    status_line = get_list_statuses(client, list_id, use_color=colorize)
    if status_line:
        print(status_line)
        print()  # Empty line for spacing

    header = args.header if hasattr(args, 'header') and args.header else None
    output = display.flat_view(tasks, options, header)

    print(output)


def filter_command(args):
    """Display filtered tasks."""
    context = get_context_manager()
    client = ClickUpClient()
    display = DisplayManager(client)

    # Resolve "current" to actual list ID
    try:
        list_id = context.resolve_id('list', args.list_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    result = client.get_list_tasks(list_id)
    tasks = result.get('tasks', [])
    options = create_format_options(args)

    # Show available statuses
    colorize = getattr(args, 'colorize', True)
    status_line = get_list_statuses(client, list_id, use_color=colorize)
    if status_line:
        print(status_line)
        print()  # Empty line for spacing

    output = display.filtered_view(
        tasks,
        status=args.status if hasattr(args, 'status') else None,
        priority=args.priority if hasattr(args, 'priority') else None,
        tags=args.tags if hasattr(args, 'tags') else None,
        assignee_id=args.assignee if hasattr(args, 'assignee') else None,
        include_completed=args.include_completed if hasattr(args, 'include_completed') else False,
        options=options,
        view_mode=args.view_mode if hasattr(args, 'view_mode') else 'hierarchy'
    )

    print(output)


def detail_command(args):
    """Display comprehensive details of a single task with relationships."""
    context = get_context_manager()
    client = ClickUpClient()
    display = DisplayManager(client)

    # Resolve "current" to actual task ID
    try:
        task_id = context.resolve_id('task', args.task_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Get the specific task
    task = client.get_task(task_id)

    # Get all tasks from the list for relationship context
    if args.list_id:
        try:
            list_id = context.resolve_id('list', args.list_id)
            result = client.get_list_tasks(list_id)
            all_tasks = result.get('tasks', [])
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        all_tasks = None

    options = create_format_options(args)

    output = display.detail_view(task, all_tasks, options)

    print(output)


def stats_command(args):
    """Display task statistics."""
    context = get_context_manager()
    client = ClickUpClient()
    display = DisplayManager(client)

    # Resolve "current" to actual list ID
    try:
        list_id = context.resolve_id('list', args.list_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    result = client.get_list_tasks(list_id)
    tasks = result.get('tasks', [])

    # Show available statuses
    # Note: stats command doesn't have colorize arg, so default to True
    status_line = get_list_statuses(client, list_id, use_color=True)
    if status_line:
        print(status_line)
        print()  # Empty line for spacing

    output = display.summary_stats(tasks)

    print(output)


def demo_command(args):
    """Show demo output with sample data (no API required)."""
    from clickup_framework.components import DisplayManager, FormatOptions

    # Sample data
    sample_tasks = [
        {
            'id': 'parent_1',
            'name': 'Feature Development',
            'status': {'status': 'in progress'},
            'priority': {'priority': '1'},
            'parent': None,
            'custom_type': 'project',
            'tags': [{'name': 'backend'}, {'name': 'api'}],
            'description': 'Develop new API endpoints for user management',
            'date_created': '2024-01-01T10:00:00Z',
            'assignees': [{'username': 'alice'}]
        },
        {
            'id': 'child_1',
            'name': 'Add Authentication Endpoint',
            'status': {'status': 'in progress'},
            'priority': {'priority': '1'},
            'parent': 'parent_1',
            'custom_type': 'feature',
            'tags': [{'name': 'auth'}, {'name': 'security'}],
            'assignees': [{'username': 'alice'}, {'username': 'bob'}]
        },
        {
            'id': 'child_2',
            'name': 'Add Profile Endpoint',
            'status': {'status': 'to do'},
            'priority': {'priority': '2'},
            'parent': 'parent_1',
            'custom_type': 'feature'
        },
        {
            'id': 'bug_1',
            'name': 'Fix Login Error',
            'status': {'status': 'blocked'},
            'priority': {'priority': '1'},
            'parent': None,
            'custom_type': 'bug',
            'tags': [{'name': 'critical'}]
        }
    ]

    display = DisplayManager()
    options = create_format_options(args)

    mode = args.mode if hasattr(args, 'mode') else 'hierarchy'

    if mode == 'hierarchy':
        output = display.hierarchy_view(sample_tasks, options, "Demo: Hierarchy View")
    elif mode == 'container':
        output = display.container_view(sample_tasks, options)
    elif mode == 'flat':
        output = display.flat_view(sample_tasks, options, "Demo: Flat View")
    elif mode == 'stats':
        output = display.summary_stats(sample_tasks)
    elif mode == 'detail':
        output = display.detail_view(sample_tasks[1], sample_tasks, options)
    else:
        output = display.hierarchy_view(sample_tasks, options, "Demo: Hierarchy View")

    print(output)


def set_current_command(args):
    """Set current resource context."""
    context = get_context_manager()

    resource_type = args.resource_type.lower()
    resource_id = args.resource_id

    # Map resource types to setter methods
    setters = {
        'task': context.set_current_task,
        'list': context.set_current_list,
        'space': context.set_current_space,
        'folder': context.set_current_folder,
        'workspace': context.set_current_workspace,
        'team': context.set_current_workspace,  # Alias
        'assignee': lambda aid: context.set_default_assignee(int(aid)),
    }

    setter = setters.get(resource_type)
    if not setter:
        print(f"Error: Unknown resource type '{resource_type}'", file=sys.stderr)
        print(f"Valid types: {', '.join(setters.keys())}", file=sys.stderr)
        sys.exit(1)

    setter(resource_id)
    print(f"✓ Set current {resource_type} to: {resource_id}")


def clear_current_command(args):
    """Clear current resource context."""
    context = get_context_manager()

    if args.resource_type:
        resource_type = args.resource_type.lower()

        # Map resource types to clear methods
        clearers = {
            'task': context.clear_current_task,
            'list': context.clear_current_list,
            'space': context.clear_current_space,
            'folder': context.clear_current_folder,
            'workspace': context.clear_current_workspace,
            'team': context.clear_current_workspace,  # Alias
        }

        clearer = clearers.get(resource_type)
        if not clearer:
            print(f"Error: Unknown resource type '{resource_type}'", file=sys.stderr)
            print(f"Valid types: {', '.join(clearers.keys())}", file=sys.stderr)
            sys.exit(1)

        clearer()
        print(f"✓ Cleared current {resource_type}")
    else:
        # Clear all context
        context.clear_all()
        print("✓ Cleared all context")


def show_current_command(args):
    """Show current resource context with animated display."""
    context = get_context_manager()
    all_context = context.get_all()

    if not all_context or all(v is None for v in [
        context.get_current_task(),
        context.get_current_list(),
        context.get_current_space(),
        context.get_current_folder(),
        context.get_current_workspace()
    ]):
        print(ANSIAnimations.warning_message("No context set"))
        return

    # Build content lines for the box
    content_lines = []

    # Show current values with highlighted IDs
    items = [
        ('Workspace', context.get_current_workspace(), TextColor.BRIGHT_MAGENTA),
        ('Space', context.get_current_space(), TextColor.BRIGHT_BLUE),
        ('Folder', context.get_current_folder(), TextColor.BRIGHT_CYAN),
        ('List', context.get_current_list(), TextColor.BRIGHT_YELLOW),
        ('Task', context.get_current_task(), TextColor.BRIGHT_GREEN),
    ]

    for label, value, color in items:
        if value:
            content_lines.append(ANSIAnimations.highlight_id(label, value, id_color=color))

    # Show last updated with gradient
    if 'last_updated' in all_context:
        last_updated = all_context['last_updated']
        content_lines.append("")  # Empty line for spacing
        content_lines.append(
            colorize("Last Updated: ", TextColor.BRIGHT_BLACK) +
            colorize(last_updated, TextColor.BRIGHT_WHITE)
        )

    # Create animated box
    box = ANSIAnimations.animated_box(
        ANSIAnimations.gradient_text("Current Context", ANSIAnimations.GRADIENT_RAINBOW),
        content_lines,
        color=TextColor.BRIGHT_CYAN
    )

    print("\n" + box + "\n")


def ansi_command(args):
    """Enable or disable ANSI color output."""
    context = get_context_manager()

    if args.action == 'enable':
        context.set_ansi_output(True)
        print("✓ ANSI color output enabled")
    elif args.action == 'disable':
        context.set_ansi_output(False)
        print("✓ ANSI color output disabled")
    elif args.action == 'status':
        enabled = context.get_ansi_output()
        status = "enabled" if enabled else "disabled"
        print(f"ANSI color output is currently: {status}")


def task_update_command(args):
    """Update a task with specified fields."""
    context = get_context_manager()
    client = ClickUpClient()

    # Resolve "current" to actual task ID
    try:
        task_id = context.resolve_id('task', args.task_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Build update dictionary from provided arguments
    updates = {}

    if args.name:
        updates['name'] = args.name

    if args.description:
        updates['description'] = args.description

    if args.status:
        updates['status'] = args.status

    if args.priority is not None:
        updates['priority'] = args.priority

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
        print(f"Error updating task: {e}", file=sys.stderr)
        sys.exit(1)


def task_create_command(args):
    """Create a new task."""
    context = get_context_manager()
    client = ClickUpClient()

    # Resolve "current" to actual list ID
    try:
        list_id = context.resolve_id('list', args.list_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Build task data
    task_data = {'name': args.name}

    if args.description:
        task_data['description'] = args.description

    if args.status:
        task_data['status'] = args.status

    if args.priority is not None:
        task_data['priority'] = args.priority

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

    # Create the task
    try:
        task = client.create_task(list_id, **task_data)

        # Show success message
        success_msg = ANSIAnimations.success_message(f"Task created: {task['name']}")
        print(success_msg)
        print(f"\nTask ID: {colorize(task['id'], TextColor.BRIGHT_GREEN)}")
        print(f"URL: {task['url']}")

    except Exception as e:
        print(f"Error creating task: {e}", file=sys.stderr)
        sys.exit(1)


def task_delete_command(args):
    """Delete a task."""
    context = get_context_manager()
    client = ClickUpClient()

    # Resolve "current" to actual task ID
    try:
        task_id = context.resolve_id('task', args.task_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Get task name for confirmation
    try:
        task = client.get_task(task_id)
        task_name = task['name']
    except Exception as e:
        print(f"Error fetching task: {e}", file=sys.stderr)
        sys.exit(1)

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
        print(f"Error deleting task: {e}", file=sys.stderr)
        sys.exit(1)


def task_assign_command(args):
    """Assign users to a task."""
    context = get_context_manager()
    client = ClickUpClient()

    # Resolve "current" to actual task ID
    try:
        task_id = context.resolve_id('task', args.task_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

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
        print(f"Error assigning task: {e}", file=sys.stderr)
        sys.exit(1)


def task_unassign_command(args):
    """Remove assignees from a task."""
    context = get_context_manager()
    client = ClickUpClient()

    # Resolve "current" to actual task ID
    try:
        task_id = context.resolve_id('task', args.task_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Remove assignees
    try:
        updated_task = client.update_task(task_id, assignees={'rem': args.assignee_ids})

        success_msg = ANSIAnimations.success_message(f"Removed {len(args.assignee_ids)} user(s) from task")
        print(success_msg)
        print(f"\nTask: {updated_task['name']}")

    except Exception as e:
        print(f"Error unassigning task: {e}", file=sys.stderr)
        sys.exit(1)


def task_set_status_command(args):
    """Set task status with subtask validation - supports multiple tasks."""
    context = get_context_manager()
    client = ClickUpClient()

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

    for task_id in task_ids:
        # Get task details to check for subtasks
        try:
            task = client.get_task(task_id)
            list_id = task['list']['id']

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
                if subtask_status.lower() != args.status.lower():
                    mismatched_subtasks.append(subtask)

            # If there are mismatched subtasks, show them and skip this task
            if mismatched_subtasks:
                print(ANSIAnimations.warning_message(
                    f"Cannot set status to '{args.status}' for task '{task['name']}' - {len(mismatched_subtasks)} subtask(s) have different status"
                ))
                print(f"\nTask: {colorize(task['name'], TextColor.BRIGHT_CYAN)} [{task_id}]")
                print(f"Target status: {colorize(args.status, TextColor.BRIGHT_YELLOW)}\n")

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
            updated_task = client.update_task(task_id, status=args.status)

            success_msg = ANSIAnimations.success_message(f"Status updated")
            print(success_msg)
            print(f"\nTask: {updated_task['name']} [{task_id}]")
            print(f"New status: {colorize(args.status, TextColor.BRIGHT_YELLOW)}")

            if subtasks:
                print(f"Subtasks: {len(subtasks)} subtask(s) also have status '{args.status}'")

            if len(task_ids) > 1:
                print()  # Extra spacing between tasks

            success_count += 1

        except Exception as e:
            print(f"Error setting status for {task_id}: {e}", file=sys.stderr)
            failed_count += 1
            continue

    # Summary for multiple tasks
    if len(task_ids) > 1:
        print(f"\n{colorize('Summary:', TextColor.BRIGHT_WHITE, TextStyle.BOLD)}")
        print(f"  Updated: {success_count}/{len(task_ids)} tasks")
        if failed_count > 0:
            print(f"  Failed: {failed_count}/{len(task_ids)} tasks")

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
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

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
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

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


def assigned_tasks_command(args):
    """Display tasks assigned to a user, sorted by dependency difficulty."""
    from collections import defaultdict, deque

    context = get_context_manager()
    client = ClickUpClient()

    # Get user ID from args or use default assignee
    if args.user_id:
        user_id = args.user_id
    else:
        user_id = context.get_default_assignee()
        if not user_id:
            print("Error: No user ID specified and no default assignee configured.", file=sys.stderr)
            print("Use --user-id <user_id> or set default: set_current assignee <user_id>", file=sys.stderr)
            sys.exit(1)

    # Get workspace/team ID
    try:
        team_id = context.resolve_id('workspace', args.team_id if hasattr(args, 'team_id') and args.team_id else 'current')
    except ValueError:
        print("Error: No team/workspace ID specified. Use --team-id or set_current workspace <team_id>", file=sys.stderr)
        sys.exit(1)

    # Fetch tasks assigned to user
    try:
        result = client.get_team_tasks(
            team_id,
            assignees=[user_id],
            subtasks=True,
            include_closed=False
        )
        tasks = result.get('tasks', [])
    except Exception as e:
        print(f"Error fetching tasks: {e}", file=sys.stderr)
        sys.exit(1)

    if not tasks:
        print(f"No tasks found assigned to user {user_id}")
        return

    # Build dependency graph
    task_map = {task['id']: task for task in tasks}
    task_info = {}

    for task in tasks:
        task_id = task['id']
        dependencies = task.get('dependencies', [])

        # Count blockers (tasks this task is waiting on)
        blockers = []
        open_blockers = []

        for dep in dependencies:
            # Type 0 means this task waits for another task
            if dep.get('type') == 0:
                blocker_id = dep.get('depends_on')
                if blocker_id:
                    blockers.append(blocker_id)
                    # Check if blocker is completed
                    if blocker_id in task_map:
                        blocker_status = task_map[blocker_id].get('status', {})
                        if isinstance(blocker_status, dict):
                            blocker_status = blocker_status.get('status', '').lower()
                        else:
                            blocker_status = str(blocker_status).lower()

                        if blocker_status not in ['closed', 'complete', 'completed']:
                            open_blockers.append(blocker_id)

        # Count dependents (tasks waiting on this task)
        dependents = []
        for dep in dependencies:
            # Type 1 means this task blocks another task
            if dep.get('type') == 1:
                dependent_id = dep.get('task_id')
                if dependent_id:
                    dependents.append(dependent_id)

        task_info[task_id] = {
            'task': task,
            'blockers': blockers,
            'open_blockers': open_blockers,
            'dependents': dependents,
            'difficulty': len(open_blockers),  # Difficulty score = number of open blockers
        }

    # Calculate dependency depth using topological sort
    def calculate_depth():
        depths = {}
        in_degree = defaultdict(int)

        # Initialize
        for task_id in task_info:
            in_degree[task_id] = 0

        # Build in-degree count
        for task_id, info in task_info.items():
            for blocker in info['blockers']:
                if blocker in task_info:
                    in_degree[task_id] += 1

        # BFS to calculate depth
        queue = deque()
        for task_id in task_info:
            if in_degree[task_id] == 0:
                queue.append((task_id, 0))
                depths[task_id] = 0

        while queue:
            task_id, depth = queue.popleft()

            # Find tasks that depend on this one
            for tid, info in task_info.items():
                if task_id in info['blockers']:
                    in_degree[tid] -= 1
                    new_depth = depth + 1
                    if tid not in depths or new_depth > depths[tid]:
                        depths[tid] = new_depth
                    if in_degree[tid] == 0:
                        queue.append((tid, depths[tid]))

        return depths

    depths = calculate_depth()
    for task_id in task_info:
        task_info[task_id]['depth'] = depths.get(task_id, 0)

    # Sort tasks by difficulty (ascending) then by depth (ascending)
    sorted_task_ids = sorted(
        task_info.keys(),
        key=lambda tid: (task_info[tid]['difficulty'], task_info[tid]['depth'])
    )

    # Display header
    print(ANSIAnimations.gradient_text(f"Tasks Assigned to User {user_id}", ANSIAnimations.GRADIENT_RAINBOW))
    print(f"Total: {len(tasks)} tasks\n")

    # Get colorize setting
    use_color = context.get_ansi_output()

    # Display tasks
    from clickup_framework.utils.colors import status_color as get_status_color

    for i, task_id in enumerate(sorted_task_ids, 1):
        info = task_info[task_id]
        task = info['task']

        # Task name and ID
        task_name = task.get('name', 'Unnamed')
        status = task.get('status', {})
        if isinstance(status, dict):
            status_name = status.get('status', 'Unknown')
        else:
            status_name = str(status)

        # Format status with color
        if use_color:
            status_colored = colorize(status_name, get_status_color(status_name), TextStyle.BOLD)
            task_name_colored = colorize(task_name, TextColor.BRIGHT_WHITE)
        else:
            status_colored = status_name
            task_name_colored = task_name

        # Difficulty indicator
        difficulty = info['difficulty']
        if difficulty == 0:
            difficulty_indicator = colorize("✓ Ready", TextColor.BRIGHT_GREEN) if use_color else "✓ Ready"
        elif difficulty <= 2:
            difficulty_indicator = colorize(f"⚠ {difficulty} blocker(s)", TextColor.BRIGHT_YELLOW) if use_color else f"⚠ {difficulty} blocker(s)"
        else:
            difficulty_indicator = colorize(f"🚫 {difficulty} blocker(s)", TextColor.BRIGHT_RED) if use_color else f"🚫 {difficulty} blocker(s)"

        print(f"{i}. {task_name_colored}")
        print(f"   Status: {status_colored}")
        print(f"   Difficulty: {difficulty_indicator}")
        print(f"   Depth: {info['depth']} | Relationships: {len(info['blockers'])} blockers, {len(info['dependents'])} dependents")
        print(f"   ID: {colorize(task_id, TextColor.BRIGHT_BLACK) if use_color else task_id}")

        # Show blocker details if any
        if info['open_blockers']:
            print(f"   Blocked by:")
            for blocker_id in info['open_blockers'][:3]:  # Show first 3
                if blocker_id in task_map:
                    blocker_task = task_map[blocker_id]
                    blocker_name = blocker_task.get('name', 'Unknown')
                    print(f"     - {blocker_name} [{blocker_id}]")

        print()  # Blank line between tasks

    # Summary stats
    ready_tasks = sum(1 for info in task_info.values() if info['difficulty'] == 0)
    blocked_tasks = sum(1 for info in task_info.values() if info['difficulty'] > 0)

    print(f"{colorize('Summary:', TextColor.BRIGHT_WHITE, TextStyle.BOLD) if use_color else 'Summary:'}")
    print(f"  Ready to start: {ready_tasks} task(s)")
    print(f"  Blocked: {blocked_tasks} task(s)")


def show_command_tree():
    """Display available commands in a tree view."""
    context = get_context_manager()
    use_color = context.get_ansi_output()

    # Print header
    header = ANSIAnimations.gradient_text("ClickUp Framework CLI - Available Commands", ANSIAnimations.GRADIENT_RAINBOW)
    print(header)
    print()

    commands = {
        "📊 View Commands": [
            ("hierarchy", "<list_id> [options]", "Display tasks in hierarchical parent-child view (default: full preset)"),
            ("container", "<list_id> [options]", "Display tasks by container hierarchy (Space → Folder → List)"),
            ("flat", "<list_id> [options]", "Display all tasks in flat list format"),
            ("filter", "<list_id> [filter_options]", "Display filtered tasks by status/priority/tags/assignee"),
            ("detail", "<task_id> [list_id]", "Show comprehensive details for a single task"),
            ("stats", "<list_id>", "Display aggregate statistics for tasks in a list"),
            ("demo", "[--mode MODE] [options]", "View demo output with sample data (no API required)"),
            ("assigned", "[--user-id ID] [--team-id ID]", "Show tasks assigned to user, sorted by difficulty"),
        ],
        "🎯 Context Management": [
            ("set_current", "<type> <id>", "Set current task/list/workspace/assignee"),
            ("show_current", "", "Display current context with animated box"),
            ("clear_current", "[type]", "Clear one or all context resources"),
        ],
        "✅ Task Management": [
            ("task_create", "<list_id> <name> [OPTIONS]", "Create new task with optional description/tags/assignees"),
            ("task_update", "<task_id> [OPTIONS]", "Update task name/description/status/priority/tags"),
            ("task_delete", "<task_id> [--force]", "Delete task with confirmation prompt"),
            ("task_assign", "<task_id> <user_id> [...]", "Assign one or more users to task"),
            ("task_unassign", "<task_id> <user_id> [...]", "Remove assignees from task"),
            ("task_set_status", "<task_id> [...] <status>", "Set task status with subtask validation"),
            ("task_set_priority", "<task_id> <priority>", "Set task priority (1-4 or urgent/high/normal/low)"),
            ("task_set_tags", "<task_id> [--add|--remove|--set]", "Manage task tags"),
        ],
        "🎨 Configuration": [
            ("ansi", "<enable|disable|status>", "Enable/disable ANSI color output"),
        ],
    }

    for category, cmds in commands.items():
        # Print category
        if use_color:
            print(colorize(category, TextColor.BRIGHT_CYAN, TextStyle.BOLD))
        else:
            print(category)

        # Print commands in this category
        for i, (cmd, args, desc) in enumerate(cmds):
            is_last = i == len(cmds) - 1
            prefix = "└─ " if is_last else "├─ "

            if use_color:
                cmd_colored = colorize(cmd, TextColor.BRIGHT_GREEN, TextStyle.BOLD)
                args_colored = colorize(args, TextColor.BRIGHT_YELLOW) if args else ""
                desc_colored = colorize(desc, TextColor.BRIGHT_BLACK)
            else:
                cmd_colored = cmd
                args_colored = args
                desc_colored = desc

            cmd_line = f"{prefix}{cmd_colored}"
            if args_colored:
                cmd_line += f" {args_colored}"
            print(cmd_line)

            # Print description indented
            indent = "   " if is_last else "│  "
            print(f"{indent}{desc_colored}")

        print()  # Blank line between categories

    # Print footer with examples
    if use_color:
        print(colorize("Quick Examples:", TextColor.BRIGHT_WHITE, TextStyle.BOLD))
    else:
        print("Quick Examples:")

    examples = [
        ("cum hierarchy 901517404278", "Show tasks in hierarchy view"),
        ("cum assigned", "Show your assigned tasks"),
        ("cum task_create current \"New Task\"", "Create a task in current list"),
        ("cum set_current assignee 68483025", "Set default assignee"),
        ("cum demo --mode hierarchy", "Try demo mode (no API needed)"),
    ]

    for cmd, desc in examples:
        if use_color:
            cmd_colored = colorize(cmd, TextColor.BRIGHT_GREEN)
            desc_colored = colorize(f"  # {desc}", TextColor.BRIGHT_BLACK)
        else:
            cmd_colored = cmd
            desc_colored = f"  # {desc}"
        print(f"  {cmd_colored}{desc_colored}")

    print()
    if use_color:
        help_text = colorize("For detailed help on any command:", TextColor.BRIGHT_WHITE)
        example = colorize("cum <command> --help", TextColor.BRIGHT_GREEN)
    else:
        help_text = "For detailed help on any command:"
        example = "cum <command> --help"
    print(f"{help_text} {example}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='ClickUp Framework CLI - Beautiful hierarchical task displays',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,  # Disable default help to use custom tree view
        epilog="""
Examples:
  # Show hierarchy view
  cum hierarchy <list_id>

  # Show container view
  cum container <list_id>

  # Show task details
  cum detail <task_id> <list_id>

  # Filter tasks
  cum filter <list_id> --status "in progress"

  # Show with custom options
  cum hierarchy <list_id> --show-ids --show-descriptions

  # Use preset formats
  cum hierarchy <list_id> --preset detailed

  # Demo mode (no API required)
  cum demo --mode hierarchy
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Common arguments for all commands
    def add_common_args(subparser):
        """Add common formatting arguments."""
        subparser.add_argument('--preset', choices=['minimal', 'summary', 'detailed', 'full'],
                             help='Use a preset format configuration')
        subparser.add_argument('--no-colorize', dest='colorize', action='store_false',
                             help='Disable color output')
        subparser.add_argument('--show-ids', action='store_true',
                             help='Show task IDs')
        subparser.add_argument('--show-tags', action='store_true', default=True,
                             help='Show task tags (default: true)')
        subparser.add_argument('--show-descriptions', action='store_true',
                             help='Show task descriptions')
        subparser.add_argument('--show-dates', action='store_true',
                             help='Show task dates')
        subparser.add_argument('--show-comments', type=int, default=0, metavar='N',
                             help='Show N comments per task')
        subparser.add_argument('--include-completed', action='store_true',
                             help='Include completed tasks')
        subparser.add_argument('--no-emoji', dest='show_emoji', action='store_false',
                             help='Hide task type emojis')

    # Hierarchy command
    hierarchy_parser = subparsers.add_parser('hierarchy', help='Display tasks in hierarchical view')
    hierarchy_parser.add_argument('list_id', help='ClickUp list ID')
    hierarchy_parser.add_argument('--header', help='Custom header text')
    add_common_args(hierarchy_parser)
    hierarchy_parser.set_defaults(func=hierarchy_command, preset='full')

    # Container command
    container_parser = subparsers.add_parser('container', help='Display tasks by container hierarchy')
    container_parser.add_argument('list_id', help='ClickUp list ID')
    add_common_args(container_parser)
    container_parser.set_defaults(func=container_command)

    # Flat command
    flat_parser = subparsers.add_parser('flat', help='Display tasks in flat list')
    flat_parser.add_argument('list_id', help='ClickUp list ID')
    flat_parser.add_argument('--header', help='Custom header text')
    add_common_args(flat_parser)
    flat_parser.set_defaults(func=flat_command)

    # Filter command
    filter_parser = subparsers.add_parser('filter', help='Display filtered tasks')
    filter_parser.add_argument('list_id', help='ClickUp list ID')
    filter_parser.add_argument('--status', help='Filter by status')
    filter_parser.add_argument('--priority', type=int, help='Filter by priority')
    filter_parser.add_argument('--tags', nargs='+', help='Filter by tags')
    filter_parser.add_argument('--assignee', help='Filter by assignee ID')
    filter_parser.add_argument('--view-mode', choices=['hierarchy', 'container', 'flat'],
                             default='hierarchy', help='Display mode (default: hierarchy)')
    add_common_args(filter_parser)
    filter_parser.set_defaults(func=filter_command)

    # Detail command
    detail_parser = subparsers.add_parser('detail', help='Show comprehensive task details')
    detail_parser.add_argument('task_id', help='ClickUp task ID')
    detail_parser.add_argument('list_id', nargs='?', help='List ID for relationship context (optional)')
    add_common_args(detail_parser)
    detail_parser.set_defaults(func=detail_command)

    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Display task statistics')
    stats_parser.add_argument('list_id', help='ClickUp list ID')
    stats_parser.set_defaults(func=stats_command)

    # Demo command
    demo_parser = subparsers.add_parser('demo', help='Show demo with sample data (no API required)')
    demo_parser.add_argument('--mode', choices=['hierarchy', 'container', 'flat', 'stats', 'detail'],
                           default='hierarchy', help='View mode to demonstrate')
    add_common_args(demo_parser)
    demo_parser.set_defaults(func=demo_command)

    # Context management commands
    set_current_parser = subparsers.add_parser('set_current',
                                                help='Set current resource context')
    set_current_parser.add_argument('resource_type',
                                     choices=['task', 'list', 'space', 'folder', 'workspace', 'team'],
                                     help='Type of resource to set as current')
    set_current_parser.add_argument('resource_id', help='ID of the resource')
    set_current_parser.set_defaults(func=set_current_command)

    clear_current_parser = subparsers.add_parser('clear_current',
                                                  help='Clear current resource context')
    clear_current_parser.add_argument('resource_type', nargs='?',
                                       choices=['task', 'list', 'space', 'folder', 'workspace', 'team'],
                                       help='Type of resource to clear (omit to clear all)')
    clear_current_parser.set_defaults(func=clear_current_command)

    show_current_parser = subparsers.add_parser('show_current',
                                                 help='Show current resource context')
    show_current_parser.set_defaults(func=show_current_command)

    # Task management commands
    task_create_parser = subparsers.add_parser('task_create',
                                                help='Create a new task')
    task_create_parser.add_argument('list_id', help='List ID to create task in (or "current")')
    task_create_parser.add_argument('name', help='Task name')
    task_create_parser.add_argument('--description', help='Task description')
    task_create_parser.add_argument('--status', help='Task status')
    task_create_parser.add_argument('--priority', type=int, help='Task priority (1-4)')
    task_create_parser.add_argument('--tags', nargs='+', help='Tags to add')
    task_create_parser.add_argument('--assignees', nargs='+', help='Assignee IDs')
    task_create_parser.add_argument('--parent', help='Parent task ID')
    task_create_parser.set_defaults(func=task_create_command)

    task_update_parser = subparsers.add_parser('task_update',
                                                help='Update a task')
    task_update_parser.add_argument('task_id', help='Task ID to update (or "current")')
    task_update_parser.add_argument('--name', help='New task name')
    task_update_parser.add_argument('--description', help='New task description')
    task_update_parser.add_argument('--status', help='New task status')
    task_update_parser.add_argument('--priority', type=int, help='New task priority (1-4)')
    task_update_parser.add_argument('--add-tags', nargs='+', help='Tags to add')
    task_update_parser.add_argument('--remove-tags', nargs='+', help='Tags to remove')
    task_update_parser.set_defaults(func=task_update_command)

    task_delete_parser = subparsers.add_parser('task_delete',
                                                help='Delete a task')
    task_delete_parser.add_argument('task_id', help='Task ID to delete (or "current")')
    task_delete_parser.add_argument('--force', '-f', action='store_true',
                                    help='Skip confirmation prompt')
    task_delete_parser.set_defaults(func=task_delete_command)

    task_assign_parser = subparsers.add_parser('task_assign',
                                                help='Assign users to a task')
    task_assign_parser.add_argument('task_id', help='Task ID (or "current")')
    task_assign_parser.add_argument('assignee_ids', nargs='+', help='User IDs to assign')
    task_assign_parser.set_defaults(func=task_assign_command)

    task_unassign_parser = subparsers.add_parser('task_unassign',
                                                  help='Remove assignees from a task')
    task_unassign_parser.add_argument('task_id', help='Task ID (or "current")')
    task_unassign_parser.add_argument('assignee_ids', nargs='+', help='User IDs to remove')
    task_unassign_parser.set_defaults(func=task_unassign_command)

    task_set_status_parser = subparsers.add_parser('task_set_status',
                                                    help='Set task status')
    task_set_status_parser.add_argument('task_ids', nargs='+', help='Task ID(s) (or "current")')
    task_set_status_parser.add_argument('status', help='New status')
    task_set_status_parser.set_defaults(func=task_set_status_command)

    task_set_priority_parser = subparsers.add_parser('task_set_priority',
                                                      help='Set task priority')
    task_set_priority_parser.add_argument('task_id', help='Task ID (or "current")')
    task_set_priority_parser.add_argument('priority', help='Priority (1-4 or urgent/high/normal/low)')
    task_set_priority_parser.set_defaults(func=task_set_priority_command)

    task_set_tags_parser = subparsers.add_parser('task_set_tags',
                                                  help='Manage task tags')
    task_set_tags_parser.add_argument('task_id', help='Task ID (or "current")')
    task_set_tags_group = task_set_tags_parser.add_mutually_exclusive_group(required=True)
    task_set_tags_group.add_argument('--add', nargs='+', help='Tags to add')
    task_set_tags_group.add_argument('--remove', nargs='+', help='Tags to remove')
    task_set_tags_group.add_argument('--set', nargs='+', help='Set tags (replace all)')
    task_set_tags_parser.set_defaults(func=task_set_tags_command)

    # ANSI output configuration
    ansi_parser = subparsers.add_parser('ansi',
                                        help='Enable or disable ANSI color output')
    ansi_parser.add_argument('action',
                            choices=['enable', 'disable', 'status'],
                            help='Action to perform (enable/disable/status)')
    ansi_parser.set_defaults(func=ansi_command)

    # Assigned tasks command
    assigned_parser = subparsers.add_parser('assigned',
                                            help='Show tasks assigned to user, sorted by dependency difficulty')
    assigned_parser.add_argument('--user-id', dest='user_id',
                                help='User ID to filter tasks (defaults to configured default assignee)')
    assigned_parser.add_argument('--team-id', dest='team_id',
                                help='Team/workspace ID (defaults to current workspace)')
    assigned_parser.set_defaults(func=assigned_tasks_command)

    # Parse arguments
    args = parser.parse_args()

    # Show help if no command specified
    if not args.command:
        show_command_tree()
        sys.exit(0)

    # Execute command
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if os.getenv('DEBUG'):
            raise
        sys.exit(1)


if __name__ == '__main__':
    main()
