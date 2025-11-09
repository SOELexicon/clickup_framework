#!/usr/bin/env python3
"""
Bulk Task Update Script

Updates multiple ClickUp tasks with status changes and comments based on JSON configuration.
Eliminates need for inline Python - just edit the JSON config file.

Usage:
    python clickup_framework/scripts/update_tasks.py task_updates.json
    python clickup_framework/scripts/update_tasks.py --dry-run task_updates.json

    # Or from anywhere if clickup_framework is installed:
    python -m clickup_framework.scripts.update_tasks task_updates.json
"""

import argparse
import json
import sys
import time
from pathlib import Path

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from clickup_framework import ClickUpClient


def load_config(config_file: str) -> dict:
    """Load task update configuration from JSON file."""
    with open(config_file, 'r') as f:
        return json.load(f)


def update_tasks(config: dict, dry_run: bool = False):
    """
    Update tasks based on configuration.

    Args:
        config: Configuration dict with task updates
        dry_run: If True, only print what would be done without making changes
    """
    client = ClickUpClient()

    print(f"\n{'='*80}")
    print(f"Task Update Script - {'DRY RUN' if dry_run else 'LIVE MODE'}")
    print(f"{'='*80}\n")

    total_tasks = len(config.get('tasks', []))
    successful = 0
    failed = 0

    for i, task_config in enumerate(config.get('tasks', []), 1):
        task_id = task_config.get('id')
        print(f"\n[{i}/{total_tasks}] Processing: {task_id}")
        print(f"  Name: {task_config.get('name', 'Unknown')}")

        try:
            # Update status if specified
            if 'status' in task_config and task_config['status']:
                new_status = task_config['status']
                if dry_run:
                    print(f"  [DRY RUN] Would update status to: '{new_status}'")
                else:
                    client.update_task(task_id, status=new_status)
                    print(f"  ✓ Status updated to: '{new_status}'")

            # Add comment if specified
            if 'comment' in task_config and task_config['comment']:
                comment = task_config['comment']
                if dry_run:
                    print(f"  [DRY RUN] Would add comment ({len(comment)} chars)")
                else:
                    client.create_task_comment(task_id, comment)
                    print(f"  ✓ Comment added ({len(comment)} chars)")

            # Add tags if specified
            if 'add_tags' in task_config:
                for tag in task_config['add_tags']:
                    if dry_run:
                        print(f"  [DRY RUN] Would add tag: '{tag}'")
                    else:
                        client.add_tag_to_task(task_id, tag)
                        print(f"  ✓ Tag added: '{tag}'")

            successful += 1

            # Rate limiting - small delay between requests
            if not dry_run:
                time.sleep(0.3)

        except Exception as e:
            failed += 1
            print(f"  ✗ Error: {str(e)}")
            continue

    # Summary
    print(f"\n{'='*80}")
    print(f"Summary:")
    print(f"  Total tasks: {total_tasks}")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print(f"{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(description='Bulk update ClickUp tasks from JSON config')
    parser.add_argument('config', help='Path to JSON configuration file')
    parser.add_argument('--dry-run', action='store_true',
                       help='Print what would be done without making changes')

    args = parser.parse_args()

    # Load configuration
    try:
        config = load_config(args.config)
    except FileNotFoundError:
        print(f"Error: Config file not found: {args.config}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in config file: {e}")
        sys.exit(1)

    # Validate configuration
    if 'tasks' not in config:
        print("Error: Config must have 'tasks' array")
        sys.exit(1)

    # Run updates
    update_tasks(config, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
