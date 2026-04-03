#!/usr/bin/env python3
"""
Create a 7-level deep task hierarchy for testing tree formatting.

This script creates a comprehensive test hierarchy with:
- 7 levels of nesting
- 3 tasks at root level (level 1)
- 7 tasks at each subsequent level (levels 2-7)
- Proper camel case naming
- Test descriptions
- Different task types for each task
"""

import argparse
import sys
import time
from typing import List, Optional

# Import ClickUp framework
try:
    from clickup_framework import ClickUpClient
    from clickup_framework.exceptions import ClickUpRateLimitError, ClickUpAPIError
except ImportError:
    print("Error: clickup_framework not found. Install it with: pip install -e .", file=sys.stderr)
    sys.exit(1)


def to_camel_case(text: str) -> str:
    """Convert text to title case (capitalize each word)."""
    return ' '.join(word.capitalize() for word in text.split())


def get_task_types(client: ClickUpClient, list_id: str) -> List[str]:
    """
    Get available custom task types for the workspace.
    
    Args:
        client: ClickUpClient instance
        list_id: List ID to get workspace from
        
    Returns:
        List of task type names (or empty list if none found)
    """
    try:
        # Get list to find workspace/team ID
        list_data = client.get_list(list_id)
        
        # Try multiple ways to get team_id
        team_id = list_data.get('team_id')
        
        if not team_id and isinstance(list_data.get('workspace'), dict):
            team_id = list_data['workspace'].get('id')
        
        if not team_id and isinstance(list_data.get('space'), dict):
            team_id = list_data['space'].get('team_id')
        
        if not team_id and isinstance(list_data.get('folder'), dict):
            team_id = list_data['folder'].get('team_id')
        
        # If still not found, try getting a task from the list
        if not team_id:
            try:
                tasks = client.get_list_tasks(list_id, page=0)
                if tasks.get('tasks') and len(tasks['tasks']) > 0:
                    task = tasks['tasks'][0]
                    team_id = task.get('team_id')
            except Exception:
                pass
        
        if not team_id:
            print("  ⚠ Could not determine workspace ID, using default task types", file=sys.stderr)
            return []
        
        # Get custom task types
        types_data = client.get_custom_task_types(team_id)
        custom_items = types_data.get('custom_items', [])
        
        if not custom_items:
            print("  ⚠ No custom task types found, tasks will use default type", file=sys.stderr)
            return []
        
        # Extract type names
        type_names = [item.get('name') for item in custom_items if item.get('name')]
        return type_names
    
    except Exception as e:
        print(f"  ⚠ Error fetching task types: {e}, using default", file=sys.stderr)
        return []


def create_task(
    client: ClickUpClient,
    name: str,
    parent_id: Optional[str] = None,
    description: Optional[str] = None,
    list_id: Optional[str] = None,
    task_type: Optional[str] = None,
    max_retries: int = 5
) -> str:
    """
    Create a task using the ClickUp API with rate limit retry logic.

    Args:
        client: ClickUpClient instance
        name: Task name (will be converted to camel case)
        parent_id: Parent task ID
        description: Task description
        list_id: List ID (required if no parent)
        task_type: Custom task type name (optional)
        max_retries: Maximum number of retry attempts for rate limits

    Returns:
        Task ID of created task
    """
    # Convert to camel case
    name = to_camel_case(name)

    # Get list_id from parent if needed
    if parent_id and not list_id:
        try:
            parent_task = client.get_task(parent_id)
            list_id = parent_task['list']['id']
        except Exception as e:
            print(f"Error getting parent task: {e}", file=sys.stderr)
            sys.exit(1)
    
    if not list_id:
        raise ValueError("Either parent_id or list_id must be provided")

    # Build task data
    task_data = {'name': name}
    
    if description:
        task_data['description'] = description
    
    if parent_id:
        task_data['parent'] = parent_id
    
    if task_type:
        task_data['custom_type'] = task_type

    # Execute with retry logic for rate limits
    type_info = f" [{task_type}]" if task_type else ""
    print(f"Creating: {name}{type_info} (parent: {parent_id or 'root'})")
    
    for attempt in range(max_retries):
        try:
            task = client.create_task(list_id, **task_data)
            return task['id']
        
        except ClickUpRateLimitError as e:
            if attempt < max_retries - 1:
                wait_time = e.retry_after if hasattr(e, 'retry_after') and e.retry_after else 60
                print(f"  ⚠ Rate limit hit, waiting {wait_time}s before retry {attempt + 1}/{max_retries}...")
                time.sleep(wait_time)
                continue
            else:
                print(f"  ✗ Rate limit retries exhausted after {max_retries} attempts", file=sys.stderr)
                raise
        
        except ClickUpAPIError as e:
            print(f"Error creating task: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Should never reach here, but just in case
    print(f"Failed to create task after {max_retries} attempts", file=sys.stderr)
    sys.exit(1)


def create_hierarchy(
    client: ClickUpClient,
    task_types: List[str],
    parent_id: Optional[str],
    current_level: int,
    max_level: int,
    task_num: int = 1,
    list_id: Optional[str] = None,
    delay: float = 0.6,
    task_counter: int = 0
):
    """
    Recursively create hierarchy of tasks with different task types.

    Args:
        client: ClickUpClient instance
        task_types: List of available task type names
        parent_id: Parent task ID
        current_level: Current depth level
        max_level: Maximum depth to create
        task_num: Task number for naming
        list_id: List ID (only used for root level)
        delay: Delay between task creations in seconds
        task_counter: Counter for cycling through task types
    """
    if current_level > max_level:
        return task_counter

    # Determine number of tasks to create: 3 at root (level 1), 7 at all other levels
    num_tasks = 3 if current_level == 1 else 7

    # Create tasks at this level
    for i in range(1, num_tasks + 1):
        task_name = f"Test {i} Level {current_level}"
        description = f"This is test task {i} at level {current_level} of the hierarchy. Used for testing tree formatting and display."

        # Cycle through task types
        task_type = None
        if task_types:
            task_type = task_types[task_counter % len(task_types)]
            task_counter += 1

        # Create the task
        task_id = create_task(
            client,
            task_name,
            parent_id=parent_id,
            description=description,
            list_id=list_id if current_level == 1 and not parent_id else None,
            task_type=task_type
        )

        type_display = f" [{task_type}]" if task_type else ""
        print(f"  ✓ Created: {task_id} - {to_camel_case(task_name)}{type_display}")

        # Delay to avoid rate limiting
        time.sleep(delay)

        # Recursively create children for this task (only for task 1 at each level except last)
        # This creates a deep hierarchy on the first branch
        if i == 1 and current_level < max_level:
            task_counter = create_hierarchy(
                client, task_types, task_id, current_level + 1, max_level, i,
                list_id=list_id, delay=delay, task_counter=task_counter
            )
    
    return task_counter


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Create a 7-level deep task hierarchy for testing"
    )
    parser.add_argument(
        'parent_id',
        nargs='?',
        help='Parent task ID (optional - will create root tasks if not provided)'
    )
    parser.add_argument(
        '--list',
        dest='list_id',
        help='List ID (required if parent_id not provided)'
    )
    parser.add_argument(
        '--levels',
        type=int,
        default=7,
        help='Number of levels to create (default: 7)'
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=0.6,
        help='Delay between task creations in seconds (default: 0.6, ~100 req/min)'
    )

    args = parser.parse_args()

    # Validate inputs
    if not args.parent_id and not args.list_id:
        print("Error: Either parent_id or --list must be provided", file=sys.stderr)
        sys.exit(1)

    # Initialize ClickUp client
    try:
        client = ClickUpClient()
    except Exception as e:
        print(f"Error initializing ClickUp client: {e}", file=sys.stderr)
        sys.exit(1)

    # Get list_id (from parent if needed)
    list_id = args.list_id
    if args.parent_id and not list_id:
        try:
            parent_task = client.get_task(args.parent_id)
            list_id = parent_task['list']['id']
            print(f"ℹ️  Using list from parent task: {parent_task['list']['name']} [{list_id}]")
        except Exception as e:
            print(f"Error getting parent task: {e}", file=sys.stderr)
            sys.exit(1)

    if not list_id:
        print("Error: Could not determine list ID", file=sys.stderr)
        sys.exit(1)

    # Get available task types
    print("Fetching available task types...")
    task_types = get_task_types(client, list_id)
    if task_types:
        print(f"  ✓ Found {len(task_types)} task types: {', '.join(task_types)}")
    else:
        print("  ℹ️  No custom task types found, tasks will use default type")
    print()

    print(f"Creating {args.levels}-level hierarchy...")
    print(f"Parent: {args.parent_id or 'root'}")
    print(f"List: {list_id}")
    print()

    # Create the hierarchy
    create_hierarchy(
        client,
        task_types,
        parent_id=args.parent_id,
        current_level=1,
        max_level=args.levels,
        list_id=list_id,
        delay=args.delay
    )

    print()
    print("✓ Hierarchy created successfully!")
    print()
    print("Test the hierarchy with:")
    if args.parent_id:
        print(f"  cum h {args.parent_id}")
    else:
        print(f"  cum h --all")


if __name__ == '__main__':
    main()
