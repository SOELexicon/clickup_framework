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
    import sys

    try:
        context = get_context_manager()

        # Use context setting if not explicitly specified
        if use_color is None:
            use_color = context.get_ansi_output()

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
    colorize_val = getattr(args, 'colorize', None)
    if colorize_val is None:
        colorize_val = default_colorize

    # Handle full descriptions flag
    full_descriptions = getattr(args, 'full_descriptions', False)
    show_descriptions = getattr(args, 'show_descriptions', False) or full_descriptions
    description_length = 10000 if full_descriptions else 500

    return FormatOptions(
        colorize_output=colorize_val,
        show_ids=getattr(args, 'show_ids', False),
        show_tags=getattr(args, 'show_tags', True),
        show_descriptions=show_descriptions,
        show_dates=getattr(args, 'show_dates', False),
        show_comments=getattr(args, 'show_comments', 0),
        include_completed=getattr(args, 'include_completed', False),
        show_type_emoji=getattr(args, 'show_emoji', True),
        description_length=description_length
    )


def hierarchy_command(args):
    """Display tasks in hierarchical parent-child view."""
    context = get_context_manager()
    client = ClickUpClient()
    display = DisplayManager(client)

    # Check if --all flag is set
    show_all = getattr(args, 'show_all', False)

    # Validate that either list_id or --all is provided
    if not show_all and not args.list_id:
        print("Error: Either provide a list_id or use --all to show all workspace tasks", file=sys.stderr)
        sys.exit(1)

    if show_all and args.list_id:
        print("Error: Cannot use both list_id and --all flag together", file=sys.stderr)
        sys.exit(1)

    if show_all:
        # Get workspace/team ID and fetch all tasks
        try:
            team_id = context.resolve_id('workspace', 'current')
        except ValueError:
            print("Error: No workspace ID set. Use 'set_current workspace <team_id>' first.", file=sys.stderr)
            sys.exit(1)

        result = client.get_team_tasks(team_id, subtasks=True, include_closed=False)
        tasks = result.get('tasks', [])
        list_id = None
    else:
        # Resolve "current" to actual list ID
        try:
            list_id = context.resolve_id('list', args.list_id)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

        result = client.get_list_tasks(list_id)
        tasks = result.get('tasks', [])

    options = create_format_options(args)

    # Show available statuses (only for single list view)
    if list_id:
        colorize_val = getattr(args, 'colorize', None)
        colorize = colorize_val if colorize_val is not None else context.get_ansi_output()
        status_line = get_list_statuses(client, list_id, use_color=colorize)
        if status_line:
            print(status_line)
            print()  # Empty line for spacing

    header = args.header if hasattr(args, 'header') and args.header else None
    if show_all and not header:
        header = "All Workspace Tasks"

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
    colorize_val = getattr(args, 'colorize', None)
    colorize = colorize_val if colorize_val is not None else context.get_ansi_output()
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
    colorize_val = getattr(args, 'colorize', None)
    colorize = colorize_val if colorize_val is not None else context.get_ansi_output()
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
    colorize_val = getattr(args, 'colorize', None)
    colorize = colorize_val if colorize_val is not None else context.get_ansi_output()
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
        'token': context.set_api_token,
    }

    setter = setters.get(resource_type)
    if not setter:
        print(f"Error: Unknown resource type '{resource_type}'", file=sys.stderr)
        print(f"Valid types: {', '.join(setters.keys())}", file=sys.stderr)
        sys.exit(1)

    try:
        setter(resource_id)
        # Mask token in output for security
        if resource_type == 'token':
            masked_token = f"{resource_id[:15]}...{resource_id[-4:]}" if len(resource_id) > 20 else "********"
            print(f"✓ API token validated and saved successfully: {masked_token}")
        else:
            print(f"✓ Set current {resource_type} to: {resource_id}")
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


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
            'token': context.clear_api_token,
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
        context.get_current_workspace(),
        context.get_api_token(),
        context.get_default_assignee()
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

    # Show API token status (without revealing the token)
    api_token = context.get_api_token()
    if api_token:
        # Mask token but show first 15 and last 4 chars for verification
        masked = f"{api_token[:15]}...{api_token[-4:]}" if len(api_token) > 20 else "********"
        content_lines.append(
            colorize("API Token: ", TextColor.BRIGHT_WHITE) +
            colorize(masked, TextColor.BRIGHT_GREEN) +
            colorize(" (set)", TextColor.BRIGHT_BLACK)
        )

        # Warn if environment variable might override
        env_token = os.environ.get('CLICKUP_API_TOKEN')
        if env_token and env_token != api_token:
            content_lines.append(
                colorize("⚠ Warning: CLICKUP_API_TOKEN env var is set and differs from stored token!",
                        TextColor.BRIGHT_RED, TextStyle.BOLD)
            )
            env_masked = f"{env_token[:15]}...{env_token[-4:]}" if len(env_token) > 20 else "********"
            content_lines.append(
                colorize(f"  Env token: {env_masked} (this will be used instead)",
                        TextColor.BRIGHT_YELLOW)
            )

    # Show default assignee
    default_assignee = context.get_default_assignee()
    if default_assignee:
        content_lines.append(ANSIAnimations.highlight_id("Default Assignee", str(default_assignee), id_color=TextColor.BRIGHT_CYAN))

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


def comment_add_command(args):
    """Add a comment to a task."""
    from clickup_framework.resources import CommentsAPI
    from clickup_framework.formatters import format_comment

    context = get_context_manager()
    client = ClickUpClient()
    comments_api = CommentsAPI(client)

    # Resolve "current" to actual task ID
    try:
        task_id = context.resolve_id('task', args.task_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        # Create the comment
        comment = comments_api.create_task_comment(task_id, args.comment_text)

        # Show success message
        success_msg = ANSIAnimations.success_message("Comment added")
        print(success_msg)

        # Format and display the comment
        formatted = format_comment(comment, detail_level="summary")
        print(f"\n{formatted}")

    except Exception as e:
        print(f"Error adding comment: {e}", file=sys.stderr)
        sys.exit(1)


def comment_list_command(args):
    """List comments on a task."""
    from clickup_framework.resources import CommentsAPI
    from clickup_framework.formatters import format_comment_list

    context = get_context_manager()
    client = ClickUpClient()
    comments_api = CommentsAPI(client)

    # Resolve "current" to actual task ID
    try:
        task_id = context.resolve_id('task', args.task_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        # Get task to display task name
        task = client.get_task(task_id)

        # Get comments
        result = comments_api.get_task_comments(task_id)
        comments = result.get('comments', [])

        # Display header
        use_color = context.get_ansi_output()
        if use_color:
            header = colorize(f"Comments for: {task['name']}", TextColor.BRIGHT_CYAN, TextStyle.BOLD)
        else:
            header = f"Comments for: {task['name']}"
        print(f"\n{header}")
        print(colorize("─" * 60, TextColor.BRIGHT_BLACK) if use_color else "─" * 60)

        if not comments:
            print(colorize("\nNo comments found", TextColor.BRIGHT_BLACK) if use_color else "\nNo comments found")
            return

        # Limit comments if specified
        if hasattr(args, 'limit') and args.limit:
            comments = comments[:args.limit]

        # Format and display comments
        detail_level = getattr(args, 'detail', 'summary')
        formatted = format_comment_list(comments, detail_level=detail_level)
        print(f"\n{formatted}")

        # Show total count
        total = len(result.get('comments', []))
        shown = len(comments)
        if shown < total:
            msg = f"\nShowing {shown} of {total} comments"
            print(colorize(msg, TextColor.BRIGHT_BLACK) if use_color else msg)
        else:
            msg = f"\nTotal: {total} comment(s)"
            print(colorize(msg, TextColor.BRIGHT_BLACK) if use_color else msg)

    except Exception as e:
        print(f"Error listing comments: {e}", file=sys.stderr)
        sys.exit(1)


def comment_update_command(args):
    """Update an existing comment."""
    from clickup_framework.resources import CommentsAPI
    from clickup_framework.formatters import format_comment

    context = get_context_manager()
    client = ClickUpClient()
    comments_api = CommentsAPI(client)

    try:
        # Update the comment
        updated = comments_api.update(args.comment_id, args.comment_text)

        # Show success message
        success_msg = ANSIAnimations.success_message("Comment updated")
        print(success_msg)

        # Format and display the updated comment
        formatted = format_comment(updated, detail_level="summary")
        print(f"\n{formatted}")

    except Exception as e:
        print(f"Error updating comment: {e}", file=sys.stderr)
        sys.exit(1)


def comment_delete_command(args):
    """Delete a comment."""
    from clickup_framework.resources import CommentsAPI

    context = get_context_manager()
    client = ClickUpClient()
    comments_api = CommentsAPI(client)

    # Confirmation prompt unless --force is specified
    if not args.force:
        use_color = context.get_ansi_output()
        if use_color:
            prompt = colorize(f"Delete comment {args.comment_id}? (y/N): ", TextColor.BRIGHT_YELLOW)
        else:
            prompt = f"Delete comment {args.comment_id}? (y/N): "

        response = input(prompt).strip().lower()
        if response != 'y':
            print("Cancelled")
            return

    try:
        # Delete the comment
        comments_api.delete(args.comment_id)

        # Show success message
        success_msg = ANSIAnimations.success_message("Comment deleted")
        print(success_msg)

    except Exception as e:
        print(f"Error deleting comment: {e}", file=sys.stderr)
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
        # No workspace configured - show list and let user select
        try:
            workspaces = client.get_authorized_workspaces()
            teams = workspaces.get('teams', [])

            if not teams:
                print("Error: No workspaces found in your account.", file=sys.stderr)
                sys.exit(1)

            # Display workspaces
            print(colorize("\nAvailable Workspaces:", TextColor.BRIGHT_CYAN, TextStyle.BOLD))
            for i, team in enumerate(teams, 1):
                team_name = team.get('name', 'Unnamed')
                team_id_val = team.get('id', 'Unknown')
                print(f"  {colorize(str(i), TextColor.BRIGHT_YELLOW)}. {team_name} {colorize(f'[{team_id_val}]', TextColor.BRIGHT_BLACK)}")

            print()
            selection = input(colorize("Select workspace number (or press any letter to cancel): ", TextColor.BRIGHT_WHITE))

            # Check if input is a letter (cancel)
            if selection.isalpha():
                print("Cancelled.")
                sys.exit(0)

            # Try to parse as number
            try:
                workspace_num = int(selection)
                if 1 <= workspace_num <= len(teams):
                    team_id = teams[workspace_num - 1]['id']
                    print(colorize(f"✓ Using workspace: {teams[workspace_num - 1]['name']}", TextColor.BRIGHT_GREEN))
                    print()
                else:
                    print(f"Error: Invalid selection. Please choose 1-{len(teams)}", file=sys.stderr)
                    sys.exit(1)
            except ValueError:
                print("Error: Invalid input. Please enter a number or letter to cancel.", file=sys.stderr)
                sys.exit(1)

        except Exception as e:
            print(f"Error fetching workspaces: {e}", file=sys.stderr)
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


def doc_list_command(args):
    """List all docs in a workspace."""
    from clickup_framework.resources import DocsAPI

    context = get_context_manager()
    client = ClickUpClient()
    docs_api = DocsAPI(client)

    # Resolve workspace ID
    try:
        workspace_id = context.resolve_id('workspace', args.workspace_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        # Get all docs
        result = docs_api.get_workspace_docs(workspace_id)
        docs = result.get('docs', [])

        if not docs:
            print("No docs found in workspace")
            return

        # Display header
        use_color = context.get_ansi_output()
        if use_color:
            header = colorize(f"Docs in Workspace {workspace_id}", TextColor.BRIGHT_CYAN, TextStyle.BOLD)
        else:
            header = f"Docs in Workspace {workspace_id}"

        print(f"\n{header}")
        print(colorize("─" * 80, TextColor.BRIGHT_BLACK) if use_color else "─" * 80)
        print()

        # Display each doc
        for i, doc in enumerate(docs, 1):
            doc_id = doc.get('id', 'Unknown')
            doc_name = doc.get('name', 'Unnamed')
            date_created = doc.get('date_created', '')
            creator = doc.get('creator', {})
            creator_name = creator.get('username', 'Unknown') if isinstance(creator, dict) else 'Unknown'

            if use_color:
                print(f"{i}. {colorize(doc_name, TextColor.BRIGHT_WHITE, TextStyle.BOLD)}")
                print(f"   ID: {colorize(doc_id, TextColor.BRIGHT_BLACK)}")
                print(f"   Created: {colorize(date_created, TextColor.BRIGHT_YELLOW)} by {colorize(creator_name, TextColor.BRIGHT_CYAN)}")
            else:
                print(f"{i}. {doc_name}")
                print(f"   ID: {doc_id}")
                print(f"   Created: {date_created} by {creator_name}")
            print()

        print(f"Total: {len(docs)} doc(s)")

    except Exception as e:
        print(f"Error listing docs: {e}", file=sys.stderr)
        sys.exit(1)


def doc_get_command(args):
    """Get a specific doc and display its content."""
    from clickup_framework.resources import DocsAPI

    context = get_context_manager()
    client = ClickUpClient()
    docs_api = DocsAPI(client)

    # Resolve workspace ID
    try:
        workspace_id = context.resolve_id('workspace', args.workspace_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        # Get doc
        doc = docs_api.get_doc(workspace_id, args.doc_id)

        # Get pages
        pages = docs_api.get_doc_pages(workspace_id, args.doc_id)

        # Display doc info
        use_color = context.get_ansi_output()

        if use_color:
            print(f"\n{colorize('📄 Doc:', TextColor.BRIGHT_CYAN, TextStyle.BOLD)} {colorize(doc.get('name', 'Unnamed'), TextColor.BRIGHT_WHITE, TextStyle.BOLD)}")
        else:
            print(f"\n📄 Doc: {doc.get('name', 'Unnamed')}")

        print(colorize("─" * 80, TextColor.BRIGHT_BLACK) if use_color else "─" * 80)
        print()

        # Show doc metadata
        print(f"ID: {colorize(doc.get('id', 'Unknown'), TextColor.BRIGHT_BLACK) if use_color else doc.get('id', 'Unknown')}")

        creator = doc.get('creator', {})
        creator_name = creator.get('username', 'Unknown') if isinstance(creator, dict) else 'Unknown'
        print(f"Creator: {colorize(creator_name, TextColor.BRIGHT_CYAN) if use_color else creator_name}")

        date_created = doc.get('date_created', 'Unknown')
        print(f"Created: {colorize(date_created, TextColor.BRIGHT_YELLOW) if use_color else date_created}")

        # Show pages
        print()
        if use_color:
            print(colorize(f"📑 Pages ({len(pages)}):", TextColor.BRIGHT_WHITE, TextStyle.BOLD))
        else:
            print(f"📑 Pages ({len(pages)}):")

        print()

        if not pages:
            print(colorize("  No pages found", TextColor.BRIGHT_BLACK) if use_color else "  No pages found")
        else:
            for i, page in enumerate(pages, 1):
                page_name = page.get('name', 'Unnamed')
                page_id = page.get('id', 'Unknown')

                if use_color:
                    print(f"  {i}. {colorize(page_name, TextColor.BRIGHT_WHITE)}")
                    print(f"     ID: {colorize(page_id, TextColor.BRIGHT_BLACK)}")
                else:
                    print(f"  {i}. {page_name}")
                    print(f"     ID: {page_id}")

                # Show content preview if requested
                if args.show_content:
                    content = page.get('content', '')
                    if content:
                        # Show first 200 chars of content
                        preview = content[:200].replace('\n', ' ')
                        if len(content) > 200:
                            preview += '...'
                        print(f"     Preview: {preview}")

                print()

    except Exception as e:
        print(f"Error getting doc: {e}", file=sys.stderr)
        sys.exit(1)


def doc_create_command(args):
    """Create a new doc."""
    from clickup_framework.resources import DocsAPI

    context = get_context_manager()
    client = ClickUpClient()
    docs_api = DocsAPI(client)

    # Resolve workspace ID
    try:
        workspace_id = context.resolve_id('workspace', args.workspace_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        # Create doc
        doc = docs_api.create_doc(
            workspace_id=workspace_id,
            name=args.name,
            parent_id=args.parent if hasattr(args, 'parent') and args.parent else None
        )

        # Show success message
        use_color = context.get_ansi_output()
        success_msg = ANSIAnimations.success_message(f"Doc created: {doc['name']}")
        print(success_msg)
        print(f"\nDoc ID: {colorize(doc['id'], TextColor.BRIGHT_GREEN) if use_color else doc['id']}")

        # Create initial pages if specified
        if hasattr(args, 'pages') and args.pages:
            print(f"\nCreating {len(args.pages)} page(s)...")
            for page_name in args.pages:
                page = docs_api.create_page(
                    workspace_id=workspace_id,
                    doc_id=doc['id'],
                    name=page_name
                )
                print(f"  ✓ Created page: {page_name}")

    except Exception as e:
        print(f"Error creating doc: {e}", file=sys.stderr)
        sys.exit(1)


def doc_update_command(args):
    """Update a page in a doc."""
    from clickup_framework.resources import DocsAPI

    context = get_context_manager()
    client = ClickUpClient()
    docs_api = DocsAPI(client)

    # Resolve workspace ID
    try:
        workspace_id = context.resolve_id('workspace', args.workspace_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        # Update page
        updated = docs_api.update_page(
            workspace_id=workspace_id,
            doc_id=args.doc_id,
            page_id=args.page_id,
            name=args.name if hasattr(args, 'name') and args.name else None,
            content=args.content if hasattr(args, 'content') and args.content else None
        )

        # Show success message
        success_msg = ANSIAnimations.success_message(f"Page updated: {updated.get('name', 'Unknown')}")
        print(success_msg)

    except Exception as e:
        print(f"Error updating page: {e}", file=sys.stderr)
        sys.exit(1)


def doc_export_command(args):
    """Export a doc and its pages to markdown files."""
    import os
    import re
    from clickup_framework.resources import DocsAPI

    context = get_context_manager()
    client = ClickUpClient()
    docs_api = DocsAPI(client)

    # Resolve workspace ID
    try:
        workspace_id = context.resolve_id('workspace', args.workspace_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        # Get doc
        doc = docs_api.get_doc(workspace_id, args.doc_id)
        doc_name = doc.get('name', 'Unnamed')

        # Get pages
        pages = docs_api.get_doc_pages(workspace_id, args.doc_id)

        # Create output directory
        output_dir = args.output_dir if hasattr(args, 'output_dir') and args.output_dir else '.'

        # Sanitize doc name for folder name
        safe_doc_name = re.sub(r'[^\w\-_\. ]', '_', doc_name)
        doc_dir = os.path.join(output_dir, safe_doc_name)

        # Create directory if it doesn't exist
        os.makedirs(doc_dir, exist_ok=True)

        use_color = context.get_ansi_output()

        if use_color:
            print(f"\n{colorize('📤 Exporting doc:', TextColor.BRIGHT_CYAN, TextStyle.BOLD)} {colorize(doc_name, TextColor.BRIGHT_WHITE)}")
        else:
            print(f"\n📤 Exporting doc: {doc_name}")

        print(f"Output directory: {doc_dir}")
        print()

        # Export doc metadata as main README
        readme_path = os.path.join(doc_dir, f"{safe_doc_name}.md")
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(f"# {doc_name}\n\n")
            f.write(f"**Doc ID:** {doc.get('id', 'Unknown')}\n\n")

            creator = doc.get('creator', {})
            creator_name = creator.get('username', 'Unknown') if isinstance(creator, dict) else 'Unknown'
            f.write(f"**Creator:** {creator_name}\n\n")
            f.write(f"**Created:** {doc.get('date_created', 'Unknown')}\n\n")

            if pages:
                f.write("## Pages\n\n")
                for page in pages:
                    safe_page_name = re.sub(r'[^\w\-_\. ]', '_', page.get('name', 'Unnamed'))
                    f.write(f"- [{page.get('name', 'Unnamed')}]({safe_page_name}.md)\n")

        print(f"✓ Created: {readme_path}")

        # Export each page
        for i, page in enumerate(pages, 1):
            page_name = page.get('name', f'page_{i}')
            safe_page_name = re.sub(r'[^\w\-_\. ]', '_', page_name)

            # Get full page content
            full_page = docs_api.get_page(workspace_id, args.doc_id, page['id'])
            content = full_page.get('content', '')

            # Determine output path
            if args.nested and '/' in page_name:
                # Create nested folder structure based on page name
                parts = page_name.split('/')
                folder_parts = parts[:-1]
                file_name = parts[-1]

                page_dir = os.path.join(doc_dir, *[re.sub(r'[^\w\-_\. ]', '_', p) for p in folder_parts])
                os.makedirs(page_dir, exist_ok=True)

                safe_file_name = re.sub(r'[^\w\-_\. ]', '_', file_name)
                page_path = os.path.join(page_dir, f"{safe_file_name}.md")
            else:
                page_path = os.path.join(doc_dir, f"{safe_page_name}.md")

            # Write page content
            with open(page_path, 'w', encoding='utf-8') as f:
                f.write(f"# {page_name}\n\n")
                if content:
                    f.write(content)
                else:
                    f.write("*No content*\n")

            print(f"✓ Exported: {page_path}")

        print()
        if use_color:
            print(colorize(f"✓ Successfully exported {len(pages)} page(s) to {doc_dir}", TextColor.BRIGHT_GREEN))
        else:
            print(f"✓ Successfully exported {len(pages)} page(s) to {doc_dir}")

    except Exception as e:
        print(f"Error exporting doc: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def update_cum_command(args):
    """Update the cum tool from git and reinstall."""
    import subprocess
    from clickup_framework import __version__

    context = get_context_manager()
    use_color = context.get_ansi_output()

    # Show current version
    if use_color:
        print(colorize(f"Current version: {__version__}", TextColor.BRIGHT_CYAN, TextStyle.BOLD))
    else:
        print(f"Current version: {__version__}")
    print()

    # Get the repository root
    try:
        repo_root = subprocess.check_output(
            ['git', 'rev-parse', '--show-toplevel'],
            stderr=subprocess.PIPE,
            text=True
        ).strip()
    except subprocess.CalledProcessError:
        print("Error: Not in a git repository. Cannot update.", file=sys.stderr)
        sys.exit(1)

    # Check current branch
    try:
        current_branch = subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            cwd=repo_root,
            stderr=subprocess.PIPE,
            text=True
        ).strip()

        if use_color:
            print(colorize(f"Current branch: {current_branch}", TextColor.BRIGHT_WHITE))
        else:
            print(f"Current branch: {current_branch}")
    except subprocess.CalledProcessError:
        pass

    # Fetch latest changes
    if use_color:
        print(colorize("Fetching latest changes from git...", TextColor.BRIGHT_YELLOW))
    else:
        print("Fetching latest changes from git...")

    try:
        # Fetch all branches
        subprocess.run(
            ['git', 'fetch', '--all'],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True
        )

        # Determine the main branch name (master or main)
        main_branch = None
        for branch_name in ['main', 'master']:
            result = subprocess.run(
                ['git', 'rev-parse', '--verify', f'origin/{branch_name}'],
                cwd=repo_root,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                main_branch = branch_name
                break

        if main_branch:
            if use_color:
                print(colorize(f"Pulling from origin/{main_branch}...", TextColor.BRIGHT_YELLOW))
            else:
                print(f"Pulling from origin/{main_branch}...")

            # Pull from the main branch
            result = subprocess.run(
                ['git', 'pull', 'origin', main_branch],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=True
            )

            if result.stdout:
                print(result.stdout)

            if "Already up to date" in result.stdout or "Already up-to-date" in result.stdout:
                if use_color:
                    print(colorize("✓ Repository is already up to date", TextColor.BRIGHT_GREEN))
                else:
                    print("✓ Repository is already up to date")
            else:
                if use_color:
                    print(colorize("✓ Successfully pulled latest changes", TextColor.BRIGHT_GREEN))
                else:
                    print("✓ Successfully pulled latest changes")
        else:
            # No main/master branch, just fetch is enough
            if use_color:
                print(colorize("✓ Fetched latest changes", TextColor.BRIGHT_GREEN))
            else:
                print("✓ Fetched latest changes")

    except subprocess.CalledProcessError as e:
        print(f"Warning: Could not update from git: {e.stderr}", file=sys.stderr)
        print("Continuing with reinstall...", file=sys.stderr)

    print()

    # Force reinstall
    if use_color:
        print(colorize("Reinstalling package...", TextColor.BRIGHT_YELLOW))
    else:
        print("Reinstalling package...")

    try:
        result = subprocess.run(
            ['pip', 'install', '-e', repo_root, '--force-reinstall', '--no-deps'],
            capture_output=True,
            text=True,
            check=True
        )

        # Show relevant output
        if result.stdout:
            # Filter to show only important lines
            for line in result.stdout.split('\n'):
                if 'Successfully installed' in line or 'clickup-framework' in line.lower():
                    print(line)

        if use_color:
            print(colorize("✓ Package reinstalled successfully", TextColor.BRIGHT_GREEN))
        else:
            print("✓ Package reinstalled successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error reinstalling package: {e.stderr}", file=sys.stderr)
        sys.exit(1)

    print()

    # Import the updated version
    import importlib
    import clickup_framework
    importlib.reload(clickup_framework)
    from clickup_framework import __version__ as new_version

    if use_color:
        success_msg = ANSIAnimations.success_message(f"Update complete! Version: {new_version}")
        print(success_msg)
    else:
        print(f"Update complete! Version: {new_version}")


def show_command_tree():
    """Display available commands in a tree view."""
    import time
    context = get_context_manager()
    use_color = context.get_ansi_output()

    # Print header with animation
    if use_color:
        # Animated rainbow gradient header
        header = ANSIAnimations.gradient_text("ClickUp Framework CLI - Available Commands", ANSIAnimations.GRADIENT_RAINBOW)
        print(header)
        print()

        # Animated separator
        separator = ANSIAnimations.gradient_text("─" * 60, ANSIAnimations.GRADIENT_RAINBOW)
        print(separator)
        print()
        time.sleep(0.05)
    else:
        print("ClickUp Framework CLI - Available Commands")
        print("─" * 60)
        print()

    commands = {
        "📊 View Commands": [
            ("hierarchy", "<list_id|--all> [options]", "Display tasks in hierarchical parent-child view (default: full preset)"),
            ("list", "<list_id|--all> [options]", "Display tasks in hierarchical view (alias for hierarchy)"),
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
        "📄 Docs Management": [
            ("doc_list", "<workspace_id>", "List all docs in a workspace"),
            ("doc_get", "<workspace_id> <doc_id> [--show-content]", "Get doc and display pages"),
            ("doc_create", "<workspace_id> <name> [OPTIONS]", "Create new doc with optional pages"),
            ("doc_update", "<workspace_id> <doc_id> <page_id> [OPTIONS]", "Update a page in a doc"),
            ("doc_export", "<workspace_id> <doc_id> [--output-dir DIR] [--nested]", "Export doc to markdown files"),
        ],
        "🎨 Configuration": [
            ("ansi", "<enable|disable|status>", "Enable/disable ANSI color output"),
            ("update cum", "", "Update cum tool from git and reinstall"),
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
        ("cum list 901517404278", "Show tasks in hierarchy view"),
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
  cum list <list_id>
  cum hierarchy <list_id>

  # Show all workspace tasks
  cum list --all
  cum hierarchy --all

  # Show container view
  cum container <list_id>

  # Show task details
  cum detail <task_id> <list_id>

  # Filter tasks
  cum filter <list_id> --status "in progress"

  # Show with custom options
  cum list <list_id> --show-ids --show-descriptions

  # Use preset formats
  cum list <list_id> --preset detailed

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
        subparser.add_argument('--no-colorize', dest='colorize', action='store_const', const=False, default=None,
                             help='Disable color output (default: use config setting)')
        subparser.add_argument('--colorize', dest='colorize', action='store_const', const=True,
                             help='Enable color output')
        subparser.add_argument('--show-ids', action='store_true',
                             help='Show task IDs')
        subparser.add_argument('--show-tags', action='store_true', default=True,
                             help='Show task tags (default: true)')
        subparser.add_argument('--show-descriptions', action='store_true',
                             help='Show task descriptions')
        subparser.add_argument('-d', '--full-descriptions', dest='full_descriptions', action='store_true',
                             help='Show full descriptions without truncation (implies --show-descriptions)')
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
    hierarchy_parser.add_argument('list_id', nargs='?', help='ClickUp list ID (optional if --all is used)')
    hierarchy_parser.add_argument('--header', help='Custom header text')
    hierarchy_parser.add_argument('--all', dest='show_all', action='store_true',
                                 help='Show all tasks from the entire workspace')
    add_common_args(hierarchy_parser)
    hierarchy_parser.set_defaults(func=hierarchy_command, preset='full')

    # List command (alias for hierarchy)
    list_parser = subparsers.add_parser('list', help='Display tasks in hierarchical view (alias for hierarchy)')
    list_parser.add_argument('list_id', nargs='?', help='ClickUp list ID (optional if --all is used)')
    list_parser.add_argument('--header', help='Custom header text')
    list_parser.add_argument('--all', dest='show_all', action='store_true',
                            help='Show all tasks from the entire workspace')
    add_common_args(list_parser)
    list_parser.set_defaults(func=hierarchy_command, preset='full')

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
    detail_parser.set_defaults(func=detail_command, preset='full')

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
                                     choices=['task', 'list', 'space', 'folder', 'workspace', 'team', 'assignee', 'token'],
                                     help='Type of resource to set as current')
    set_current_parser.add_argument('resource_id', help='ID/value of the resource (API token for token type)')
    set_current_parser.set_defaults(func=set_current_command)

    clear_current_parser = subparsers.add_parser('clear_current',
                                                  help='Clear current resource context')
    clear_current_parser.add_argument('resource_type', nargs='?',
                                       choices=['task', 'list', 'space', 'folder', 'workspace', 'team', 'assignee', 'token'],
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

    # Comment management commands
    comment_add_parser = subparsers.add_parser('comment_add',
                                                help='Add a comment to a task')
    comment_add_parser.add_argument('task_id', help='Task ID (or "current")')
    comment_add_parser.add_argument('comment_text', help='Comment text')
    comment_add_parser.set_defaults(func=comment_add_command)

    comment_list_parser = subparsers.add_parser('comment_list',
                                                 help='List comments on a task')
    comment_list_parser.add_argument('task_id', help='Task ID (or "current")')
    comment_list_parser.add_argument('--limit', type=int, help='Limit number of comments shown')
    comment_list_parser.add_argument('--detail', choices=['minimal', 'summary', 'detailed', 'full'],
                                     default='summary', help='Detail level for comment display')
    comment_list_parser.set_defaults(func=comment_list_command)

    comment_update_parser = subparsers.add_parser('comment_update',
                                                   help='Update an existing comment')
    comment_update_parser.add_argument('comment_id', help='Comment ID')
    comment_update_parser.add_argument('comment_text', help='New comment text')
    comment_update_parser.set_defaults(func=comment_update_command)

    comment_delete_parser = subparsers.add_parser('comment_delete',
                                                   help='Delete a comment')
    comment_delete_parser.add_argument('comment_id', help='Comment ID')
    comment_delete_parser.add_argument('--force', '-f', action='store_true',
                                       help='Skip confirmation prompt')
    comment_delete_parser.set_defaults(func=comment_delete_command)

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

    # Doc management commands
    doc_list_parser = subparsers.add_parser('doc_list',
                                            help='List all docs in a workspace')
    doc_list_parser.add_argument('workspace_id', help='Workspace/team ID (or "current")')
    doc_list_parser.set_defaults(func=doc_list_command)

    doc_get_parser = subparsers.add_parser('doc_get',
                                           help='Get a specific doc and display its content')
    doc_get_parser.add_argument('workspace_id', help='Workspace/team ID (or "current")')
    doc_get_parser.add_argument('doc_id', help='Doc ID')
    doc_get_parser.add_argument('--show-content', action='store_true',
                                help='Show content preview for each page')
    doc_get_parser.set_defaults(func=doc_get_command)

    doc_create_parser = subparsers.add_parser('doc_create',
                                              help='Create a new doc')
    doc_create_parser.add_argument('workspace_id', help='Workspace/team ID (or "current")')
    doc_create_parser.add_argument('name', help='Doc name')
    doc_create_parser.add_argument('--parent', help='Parent doc ID (for nested docs)')
    doc_create_parser.add_argument('--pages', nargs='+', help='Initial page names to create')
    doc_create_parser.set_defaults(func=doc_create_command)

    doc_update_parser = subparsers.add_parser('doc_update',
                                              help='Update a page in a doc')
    doc_update_parser.add_argument('workspace_id', help='Workspace/team ID (or "current")')
    doc_update_parser.add_argument('doc_id', help='Doc ID')
    doc_update_parser.add_argument('page_id', help='Page ID to update')
    doc_update_parser.add_argument('--name', help='New page name')
    doc_update_parser.add_argument('--content', help='New page content (markdown)')
    doc_update_parser.set_defaults(func=doc_update_command)

    doc_export_parser = subparsers.add_parser('doc_export',
                                              help='Export a doc and its pages to markdown files')
    doc_export_parser.add_argument('workspace_id', help='Workspace/team ID (or "current")')
    doc_export_parser.add_argument('doc_id', help='Doc ID to export')
    doc_export_parser.add_argument('--output-dir', dest='output_dir', default='.',
                                   help='Output directory (default: current directory)')
    doc_export_parser.add_argument('--nested', action='store_true',
                                   help='Create nested folder structure for pages with "/" in name')
    doc_export_parser.set_defaults(func=doc_export_command)

    # Update command
    update_parser = subparsers.add_parser('update',
                                          help='Update components of the cum tool')
    update_subparsers = update_parser.add_subparsers(dest='update_target', help='Component to update')

    # Update cum (self-update)
    update_cum_parser = update_subparsers.add_parser('cum',
                                                     help='Update cum tool from git and reinstall')
    update_cum_parser.set_defaults(func=update_cum_command)

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
