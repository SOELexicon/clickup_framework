#!/usr/bin/env python3
"""
Update task descriptions with their command specifications.

Reads spec files from command_specs/ directory and appends them to
the corresponding task descriptions in ClickUp.
"""

import os
from pathlib import Path
from clickup_framework import ClickUpClient


def read_spec_file(spec_path: str) -> str:
    """Read specification content from markdown file."""
    with open(spec_path, 'r') as f:
        return f.read()


def append_spec_to_description(current_desc: str, spec_content: str) -> str:
    """
    Append spec to description if not already present.

    Adds a separator and the spec content.
    """
    # Marker to identify spec section
    spec_marker = "---\n\n## Command Specification"

    # Check if spec is already in description
    if spec_marker in current_desc or "## Synopsis" in current_desc:
        print("    Spec already present, skipping...")
        return None

    # Append spec with separator
    separator = "\n\n" + "="*60 + "\n\n## Command Specification\n\n"
    new_description = current_desc + separator + spec_content

    return new_description


def update_task_with_spec(client: ClickUpClient, task_id: str, spec_path: str, dry_run: bool = False):
    """
    Update a single task with its specification.

    Args:
        client: ClickUpClient instance
        task_id: Task ID to update
        spec_path: Path to specification markdown file
        dry_run: If True, print changes without updating
    """
    print(f"\nProcessing task {task_id}...")

    # Read spec file
    if not os.path.exists(spec_path):
        print(f"  ✗ Spec file not found: {spec_path}")
        return False

    spec_content = read_spec_file(spec_path)
    print(f"  ✓ Read spec file ({len(spec_content)} chars)")

    # Get current task
    try:
        task = client.get_task(task_id)
        task_name = task['name']
        current_desc = task.get('description', '')
        print(f"  ✓ Fetched task: {task_name}")
        print(f"    Current description: {len(current_desc)} chars")
    except Exception as e:
        print(f"  ✗ Error fetching task: {e}")
        return False

    # Append spec to description
    new_description = append_spec_to_description(current_desc, spec_content)

    if new_description is None:
        return True  # Already has spec, skip

    print(f"    New description: {len(new_description)} chars")

    # Update task
    if dry_run:
        print(f"  [DRY RUN] Would update task description")
        return True

    try:
        client.update_task(task_id, description=new_description)
        print(f"  ✓ Updated task description")
        return True
    except Exception as e:
        print(f"  ✗ Error updating task: {e}")
        return False


def main(dry_run: bool = False):
    """
    Main function to update all task specifications.

    Args:
        dry_run: If True, show changes without updating
    """
    client = ClickUpClient()

    # Get all spec files
    spec_dir = Path("command_specs")
    if not spec_dir.exists():
        print(f"Error: Spec directory not found: {spec_dir}")
        return

    spec_files = list(spec_dir.glob("*.md"))
    if not spec_files:
        print(f"Error: No spec files found in {spec_dir}")
        return

    print(f"Found {len(spec_files)} spec files in {spec_dir}/")

    if dry_run:
        print("\n" + "="*60)
        print("DRY RUN MODE - No changes will be made")
        print("="*60)

    # Process each spec file
    success_count = 0
    skip_count = 0
    error_count = 0

    for spec_file in sorted(spec_files):
        # Extract task ID from filename (e.g., "86c6e0q0b.md" -> "86c6e0q0b")
        task_id = spec_file.stem

        result = update_task_with_spec(client, task_id, str(spec_file), dry_run)

        if result is True:
            # Check if it was skipped (already has spec)
            task = client.get_task(task_id)
            current_desc = task.get('description', '')
            if "## Command Specification" in current_desc or "## Synopsis" in current_desc:
                skip_count += 1
            else:
                success_count += 1
        else:
            error_count += 1

    # Summary
    print("\n" + "="*60)
    print("Summary:")
    print(f"  Total spec files: {len(spec_files)}")
    print(f"  Successfully updated: {success_count}")
    print(f"  Skipped (already has spec): {skip_count}")
    print(f"  Errors: {error_count}")
    print("="*60)


if __name__ == "__main__":
    import sys

    # Check for dry-run flag
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv

    if dry_run:
        print("Running in DRY RUN mode (no changes will be made)")

    main(dry_run=dry_run)
