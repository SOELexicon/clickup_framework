#!/usr/bin/env python3
"""
Create a 7-level deep task hierarchy for testing tree formatting.

This script creates a comprehensive test hierarchy with:
- 7 levels of nesting
- 3 tasks at each level
- Proper camel case naming
- Test descriptions
"""

import argparse
import subprocess
import sys
import time


def to_camel_case(text: str) -> str:
    """Convert text to title case (capitalize each word)."""
    return ' '.join(word.capitalize() for word in text.split())


def create_task(name: str, parent_id: str = None, description: str = None, list_id: str = None) -> str:
    """
    Create a task using the cum CLI.

    Args:
        name: Task name (will be converted to camel case)
        parent_id: Parent task ID
        description: Task description
        list_id: List ID (required if no parent)

    Returns:
        Task ID of created task
    """
    # Convert to camel case
    name = to_camel_case(name)

    # Build command
    cmd = ['cum', 'tc', name]

    if parent_id:
        cmd.extend(['--parent', parent_id])
    elif list_id:
        cmd.extend(['--list', list_id])
    else:
        raise ValueError("Either parent_id or list_id must be provided")

    if description:
        cmd.extend(['--description', description])

    # Execute command
    print(f"Creating: {name} (parent: {parent_id or 'root'})")
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')

    if result.returncode != 0:
        print(f"Error creating task: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    # Extract task ID from output
    output = result.stdout
    for line in output.split('\n'):
        if 'Task ID:' in line:
            task_id = line.split('Task ID:')[1].strip()
            return task_id

    print(f"Failed to extract task ID from output:\n{output}", file=sys.stderr)
    sys.exit(1)


def create_hierarchy(parent_id: str, current_level: int, max_level: int, task_num: int = 1, list_id: str = None):
    """
    Recursively create hierarchy of tasks.

    Args:
        parent_id: Parent task ID
        current_level: Current depth level
        max_level: Maximum depth to create
        task_num: Task number for naming
        list_id: List ID (only used for root level)
    """
    if current_level > max_level:
        return

    # Create 3 tasks at this level
    for i in range(1, 4):
        task_name = f"Test {i} Level {current_level}"
        description = f"This is test task {i} at level {current_level} of the hierarchy. Used for testing tree formatting and display."

        # Create the task
        task_id = create_task(
            task_name,
            parent_id=parent_id,
            description=description,
            list_id=list_id if current_level == 1 and not parent_id else None
        )

        print(f"  ✓ Created: {task_id} - {to_camel_case(task_name)}")

        # Small delay to avoid rate limiting
        time.sleep(0.2)

        # Recursively create children for this task (only for task 1 at each level except last)
        # This creates a deep hierarchy on the first branch
        if i == 1 and current_level < max_level:
            create_hierarchy(task_id, current_level + 1, max_level, i)


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

    args = parser.parse_args()

    # Validate inputs
    if not args.parent_id and not args.list_id:
        print("Error: Either parent_id or --list must be provided", file=sys.stderr)
        sys.exit(1)

    print(f"Creating {args.levels}-level hierarchy...")
    print(f"Parent: {args.parent_id or 'root'}")
    print(f"List: {args.list_id or 'from parent'}")
    print()

    # Create the hierarchy
    create_hierarchy(
        parent_id=args.parent_id,
        current_level=1,
        max_level=args.levels,
        list_id=args.list_id
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
