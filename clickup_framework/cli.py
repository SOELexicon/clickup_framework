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
    # Use preset if specified
    if hasattr(args, 'preset') and args.preset:
        if args.preset == 'minimal':
            return FormatOptions.minimal()
        elif args.preset == 'summary':
            return FormatOptions.summary()
        elif args.preset == 'detailed':
            return FormatOptions.detailed()
        elif args.preset == 'full':
            return FormatOptions.full()

    # Otherwise build from individual flags
    return FormatOptions(
        colorize_output=getattr(args, 'colorize', True),
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
    """Set task status."""
    context = get_context_manager()
    client = ClickUpClient()

    # Resolve "current" to actual task ID
    try:
        task_id = context.resolve_id('task', args.task_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Update status
    try:
        updated_task = client.update_task(task_id, status=args.status)

        success_msg = ANSIAnimations.success_message(f"Status updated")
        print(success_msg)
        print(f"\nTask: {updated_task['name']}")
        print(f"New status: {colorize(args.status, TextColor.BRIGHT_YELLOW)}")

    except Exception as e:
        print(f"Error setting status: {e}", file=sys.stderr)
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
    if isinstance(priority, str):
        priority = priority_map.get(priority.lower(), priority)

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


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='ClickUp Framework CLI - Beautiful hierarchical task displays',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show hierarchy view
  python -m clickup_framework.cli hierarchy <list_id>

  # Show container view
  python -m clickup_framework.cli container <list_id>

  # Show task details
  python -m clickup_framework.cli detail <task_id> <list_id>

  # Filter tasks
  python -m clickup_framework.cli filter <list_id> --status "in progress"

  # Show with custom options
  python -m clickup_framework.cli hierarchy <list_id> --show-ids --show-descriptions

  # Use preset formats
  python -m clickup_framework.cli hierarchy <list_id> --preset detailed

  # Demo mode (no API required)
  python -m clickup_framework.cli demo --mode hierarchy
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
    hierarchy_parser.set_defaults(func=hierarchy_command)

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
    task_set_status_parser.add_argument('task_id', help='Task ID (or "current")')
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

    # Parse arguments
    args = parser.parse_args()

    # Show help if no command specified
    if not args.command:
        parser.print_help()
        sys.exit(1)

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
