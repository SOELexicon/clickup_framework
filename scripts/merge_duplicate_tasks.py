#!/usr/bin/env python3
"""
Merge Duplicate Tasks Script

Finds and merges tasks with the same name in a ClickUp list.
For each set of duplicates, keeps one task and merges content from others.

Usage:
    python scripts/merge_duplicate_tasks.py <list_id> [--dry-run]
    python scripts/merge_duplicate_tasks.py 901517412318 --dry-run

Features:
    - Groups tasks by exact name match
    - Keeps the oldest task (by creation date)
    - Moves subtasks from duplicates to the kept task
    - Moves comments from duplicates to the kept task
    - Consolidates checklist items
    - Deletes duplicate tasks after merging
"""

import argparse
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from clickup_framework import ClickUpClient


def parse_date(date_str):
    """Parse ClickUp date string to datetime object."""
    if not date_str:
        return datetime.min
    try:
        # ClickUp uses milliseconds timestamp
        timestamp_ms = int(date_str)
        return datetime.fromtimestamp(timestamp_ms / 1000)
    except (ValueError, TypeError):
        return datetime.min


def get_tasks_from_list(client, list_id, include_closed=False):
    """Fetch all tasks from a list."""
    print(f"Fetching tasks from list {list_id}...")
    result = client.get_list_tasks(
        list_id,
        include_closed=include_closed,
        subtasks=True
    )
    tasks = result.get('tasks', [])
    print(f"Found {len(tasks)} tasks")
    return tasks


def group_tasks_by_name(tasks):
    """Group tasks by their name, excluding subtasks."""
    groups = defaultdict(list)

    for task in tasks:
        # Skip subtasks - they have a parent field
        if task.get('parent'):
            continue

        name = task.get('name', '').strip()
        if name:
            groups[name].append(task)

    # Filter to only groups with duplicates
    duplicates = {name: task_list for name, task_list in groups.items() if len(task_list) > 1}

    return duplicates


def get_task_details(client, task_id):
    """Get full task details including comments and subtasks."""
    return client.get_task(task_id, include_subtasks=True)


def merge_tasks(client, task_name, duplicate_tasks, dry_run=False):
    """
    Merge duplicate tasks into one.

    Args:
        client: ClickUpClient instance
        task_name: Name of the duplicate tasks
        duplicate_tasks: List of task objects with the same name
        dry_run: If True, only print what would be done

    Returns:
        True if successful, False otherwise
    """
    # Sort by creation date (oldest first)
    sorted_tasks = sorted(duplicate_tasks, key=lambda t: parse_date(t.get('date_created')))

    # Keep the oldest task
    kept_task = sorted_tasks[0]
    tasks_to_merge = sorted_tasks[1:]

    kept_task_id = kept_task['id']
    kept_task_url = kept_task.get('url', '')

    print(f"\n{'='*80}")
    print(f"Task: {task_name}")
    print(f"Found {len(duplicate_tasks)} duplicates")
    print(f"Keeping: {kept_task_id} (created {parse_date(kept_task.get('date_created'))})")
    print(f"URL: {kept_task_url}")
    print(f"{'='*80}")

    # Get full details for all tasks
    print(f"\nFetching details for {len(duplicate_tasks)} tasks...")
    all_task_details = []
    for task in duplicate_tasks:
        try:
            details = get_task_details(client, task['id'])
            all_task_details.append(details)
        except Exception as e:
            print(f"  ✗ Error fetching details for {task['id']}: {e}")
            return False

    kept_task_details = all_task_details[0]
    tasks_to_merge_details = all_task_details[1:]

    # Process each duplicate task
    for i, duplicate_task in enumerate(tasks_to_merge_details):
        duplicate_id = duplicate_task['id']
        duplicate_url = duplicate_task.get('url', '')
        print(f"\n  Merging from duplicate: {duplicate_id}")
        print(f"    URL: {duplicate_url}")
        print(f"    Created: {parse_date(duplicate_task.get('date_created'))}")

        # 1. Move subtasks
        subtasks = [t for t in duplicate_task.get('subtasks', []) if isinstance(t, dict)]
        if subtasks:
            print(f"    Found {len(subtasks)} subtasks to move")
            for subtask in subtasks:
                subtask_id = subtask.get('id')
                subtask_name = subtask.get('name', 'Unnamed')
                if dry_run:
                    print(f"      [DRY RUN] Would move subtask '{subtask_name}' ({subtask_id})")
                else:
                    try:
                        client.update_task(subtask_id, parent=kept_task_id)
                        print(f"      ✓ Moved subtask '{subtask_name}'")
                    except Exception as e:
                        print(f"      ✗ Error moving subtask {subtask_id}: {e}")

        # 2. Copy comments
        try:
            comments_result = client.get_task_comments(duplicate_id)
            comments = comments_result.get('comments', [])
            if comments:
                print(f"    Found {len(comments)} comments to copy")
                for comment in comments:
                    comment_text = comment.get('comment_text', '')
                    comment_user = comment.get('user', {}).get('username', 'Unknown')
                    comment_date = parse_date(comment.get('date'))

                    # Create a new comment with original author/date info
                    merged_comment = f"[Merged from duplicate task - Original by {comment_user} on {comment_date}]\n\n{comment_text}"

                    if dry_run:
                        print(f"      [DRY RUN] Would copy comment from {comment_user}")
                    else:
                        try:
                            client.create_task_comment(kept_task_id, merged_comment)
                            print(f"      ✓ Copied comment from {comment_user}")
                        except Exception as e:
                            print(f"      ✗ Error copying comment: {e}")
        except Exception as e:
            print(f"    ✗ Error fetching comments: {e}")

        # 3. Consolidate checklists
        checklists = duplicate_task.get('checklists', [])
        if checklists:
            print(f"    Found {len(checklists)} checklists to merge")
            for checklist in checklists:
                checklist_name = checklist.get('name', 'Unnamed')
                items = checklist.get('items', [])

                if dry_run:
                    print(f"      [DRY RUN] Would merge checklist '{checklist_name}' with {len(items)} items")
                else:
                    try:
                        # Create new checklist on kept task
                        new_checklist = client.create_checklist(kept_task_id, f"{checklist_name} (merged)")
                        new_checklist_id = new_checklist['checklist']['id']
                        print(f"      ✓ Created merged checklist '{checklist_name}'")

                        # Copy all items
                        for item in items:
                            item_name = item.get('name', '')
                            resolved = item.get('resolved', False)
                            try:
                                client.create_checklist_item(
                                    new_checklist_id,
                                    item_name,
                                    resolved=resolved
                                )
                            except Exception as e:
                                print(f"        ✗ Error copying checklist item: {e}")

                        print(f"        ✓ Copied {len(items)} checklist items")
                    except Exception as e:
                        print(f"      ✗ Error creating checklist: {e}")

        # 4. Add a note to the kept task about the merge
        merge_note = (
            f"📋 Merged duplicate task on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Duplicate task ID: {duplicate_id}\n"
            f"Duplicate task URL: {duplicate_url}\n"
            f"Created: {parse_date(duplicate_task.get('date_created'))}"
        )

        if dry_run:
            print(f"    [DRY RUN] Would add merge note to kept task")
        else:
            try:
                client.create_task_comment(kept_task_id, merge_note)
                print(f"    ✓ Added merge note to kept task")
            except Exception as e:
                print(f"    ✗ Error adding merge note: {e}")

        # 5. Delete the duplicate task
        if dry_run:
            print(f"    [DRY RUN] Would delete duplicate task {duplicate_id}")
        else:
            try:
                client.delete_task(duplicate_id)
                print(f"    ✓ Deleted duplicate task {duplicate_id}")
            except Exception as e:
                print(f"    ✗ Error deleting duplicate task: {e}")
                return False

    print(f"\n✓ Successfully merged {len(tasks_to_merge)} duplicate(s) into {kept_task_id}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Merge duplicate tasks in a ClickUp list',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run to see what would be merged
  python scripts/merge_duplicate_tasks.py 901517412318 --dry-run

  # Actually merge the duplicates
  python scripts/merge_duplicate_tasks.py 901517412318

  # Include closed tasks
  python scripts/merge_duplicate_tasks.py 901517412318 --include-closed
        """
    )
    parser.add_argument('list_id', help='ClickUp list ID to process')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview what would be done without making changes')
    parser.add_argument('--include-closed', action='store_true',
                       help='Include closed/archived tasks in the merge')
    parser.add_argument('--yes', '-y', action='store_true',
                       help='Auto-confirm merge without prompting')

    args = parser.parse_args()

    # Initialize client
    try:
        client = ClickUpClient()
    except Exception as e:
        print(f"Error initializing ClickUp client: {e}")
        print("Make sure CLICKUP_API_TOKEN is set or use 'set_current token <token>'")
        sys.exit(1)

    print(f"\n{'='*80}")
    print(f"Merge Duplicate Tasks - {'DRY RUN' if args.dry_run else 'LIVE MODE'}")
    print(f"{'='*80}\n")

    # Fetch tasks
    try:
        tasks = get_tasks_from_list(client, args.list_id, include_closed=args.include_closed)
    except Exception as e:
        print(f"Error fetching tasks: {e}")
        sys.exit(1)

    if not tasks:
        print("No tasks found in list")
        sys.exit(0)

    # Group by name
    duplicate_groups = group_tasks_by_name(tasks)

    if not duplicate_groups:
        print("\n✓ No duplicate tasks found!")
        sys.exit(0)

    print(f"\nFound {len(duplicate_groups)} sets of duplicate tasks:")
    for name, task_list in duplicate_groups.items():
        print(f"  • '{name}' - {len(task_list)} duplicates")

    if args.dry_run:
        print("\n[DRY RUN MODE - No changes will be made]")
    else:
        print("\n⚠️  WARNING: This will permanently delete duplicate tasks!")
        if not args.yes:
            response = input("Continue? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("Cancelled")
                sys.exit(0)
        else:
            print("Auto-confirmed with --yes flag")

    # Merge each group
    successful = 0
    failed = 0

    for task_name, task_list in duplicate_groups.items():
        try:
            if merge_tasks(client, task_name, task_list, dry_run=args.dry_run):
                successful += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n✗ Error merging '{task_name}': {e}")
            failed += 1

    # Summary
    print(f"\n{'='*80}")
    print(f"Summary:")
    print(f"  Total duplicate groups: {len(duplicate_groups)}")
    print(f"  Successfully merged: {successful}")
    print(f"  Failed: {failed}")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    main()
