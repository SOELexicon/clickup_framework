#!/usr/bin/env python3
"""
Test Structure Setup Script

This script creates a comprehensive test structure in ClickUp for testing the framework.
It builds a 7-level task hierarchy with various task types, statuses, tags, and comments.

Usage:
    python tests/setup_test_structure.py [--clean] [--verify-only]

Options:
    --clean: Remove existing test structure before creating new one
    --verify-only: Only verify the structure exists, don't create
"""

import json
import os
import sys
import time
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from clickup_framework import ClickUpClient


class TestStructureManager:
    """Manages the test structure in ClickUp."""

    def __init__(self, config_file: str = "tests/test_structure.json"):
        """Initialize the manager with configuration."""
        self.client = ClickUpClient()
        self.config_file = config_file
        self.config = self._load_config()
        self.ids_file = "tests/test_structure_ids.json"
        self.ids = self._load_ids()

    def _load_config(self) -> Dict:
        """Load the test structure configuration."""
        with open(self.config_file, 'r') as f:
            return json.load(f)

    def _load_ids(self) -> Dict:
        """Load existing test structure IDs if available."""
        if os.path.exists(self.ids_file):
            try:
                with open(self.ids_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load existing IDs: {e}")
                return {}
        return {}

    def _save_ids(self):
        """Save test structure IDs to file."""
        with open(self.ids_file, 'w') as f:
            json.dump(self.ids, f, indent=2)
        print(f"✓ Saved structure IDs to {self.ids_file}")

    def verify_structure(self) -> bool:
        """Verify that the test structure exists in ClickUp."""
        print("\n" + "="*70)
        print("VERIFYING TEST STRUCTURE")
        print("="*70)

        if not self.ids:
            print("✗ No structure IDs found")
            return False

        # Verify folder
        if 'folder_id' in self.ids:
            try:
                folder = self.client.get_folder(self.ids['folder_id'])
                print(f"✓ Folder exists: {folder['name']} ({self.ids['folder_id']})")
            except Exception as e:
                print(f"✗ Folder not found: {e}")
                return False
        else:
            print("✗ No folder ID stored")
            return False

        # Verify list
        if 'list_id' in self.ids:
            try:
                list_data = self.client.get_list(self.ids['list_id'])
                print(f"✓ List exists: {list_data['name']} ({self.ids['list_id']})")
            except Exception as e:
                print(f"✗ List not found: {e}")
                return False
        else:
            print("✗ No list ID stored")
            return False

        # Verify tasks
        task_count = len(self.ids.get('task_ids', {}))
        print(f"✓ Found {task_count} task IDs in structure")

        print("="*70)
        print(f"✓ Structure verification PASSED")
        print("="*70 + "\n")
        return True

    def clean_structure(self):
        """Remove existing test structure."""
        print("\n" + "="*70)
        print("CLEANING EXISTING TEST STRUCTURE")
        print("="*70)

        if not self.ids:
            print("No structure IDs found, nothing to clean")
            return

        # Delete all tasks
        task_ids = self.ids.get('task_ids', {})
        deleted_count = 0
        failed_count = 0

        print(f"\nDeleting {len(task_ids)} tasks...")
        for task_name, task_id in task_ids.items():
            try:
                self.client.delete_task(task_id)
                deleted_count += 1
                print(f"  ✓ Deleted: {task_name}")
                time.sleep(0.2)  # Rate limiting
            except Exception as e:
                failed_count += 1
                print(f"  ⚠ Could not delete {task_name}: {e}")

        print(f"\n✓ Deleted {deleted_count} tasks")
        if failed_count > 0:
            print(f"⚠ Failed to delete {failed_count} tasks")

        # Delete list
        if 'list_id' in self.ids:
            try:
                # Note: List deletion is done via folder deletion in ClickUp
                print(f"✓ List will be deleted with folder: {self.ids['list_id']}")
            except Exception as e:
                print(f"⚠ Could not delete list: {e}")

        # Delete folder (this will delete lists inside)
        if 'folder_id' in self.ids:
            try:
                # ClickUp doesn't have direct folder deletion API
                # Folders need to be manually deleted from UI or archived
                print(f"⚠ Folder should be manually deleted from UI: {self.ids['folder_id']}")
            except Exception as e:
                print(f"⚠ Could not delete folder: {e}")

        # Clear IDs file
        self.ids = {}
        self._save_ids()

        print("="*70)
        print("✓ Cleanup complete")
        print("="*70 + "\n")

    def create_structure(self):
        """Create the complete test structure in ClickUp."""
        print("\n" + "="*70)
        print("CREATING TEST STRUCTURE")
        print("="*70)

        structure = self.config['structure']
        space_id = self.config['space_id']

        # Create folder
        folder_config = structure['folder']
        print(f"\nCreating folder: {folder_config['name']}")

        try:
            folder = self.client.create_folder(
                space_id,
                folder_config['name']
            )
            folder_id = folder['id']
            self.ids['folder_id'] = folder_id
            print(f"✓ Folder created: {folder_id}")
            time.sleep(0.5)
        except Exception as e:
            if "Folder name taken" in str(e):
                print(f"⚠ Folder already exists, attempting to find it...")
                # Try to find existing folder
                folders = self.client.get_space_folders(space_id)
                for folder in folders['folders']:
                    if folder['name'] == folder_config['name']:
                        folder_id = folder['id']
                        self.ids['folder_id'] = folder_id
                        print(f"✓ Found existing folder: {folder_id}")
                        break
                else:
                    print(f"✗ Could not find existing folder")
                    raise
            else:
                raise

        # Create list
        list_config = structure['list']
        print(f"\nCreating list: {list_config['name']}")

        try:
            list_data = self.client.create_list(
                folder_id,
                list_config['name']
            )
            list_id = list_data['id']
            self.ids['list_id'] = list_id
            print(f"✓ List created: {list_id}")
            time.sleep(0.5)
        except Exception as e:
            if "List name already used in Folder" in str(e) or "already exists" in str(e).lower():
                print(f"⚠ List already exists, attempting to find it...")
                # Try to find existing list
                lists = self.client.get_folder_lists(folder_id)
                for lst in lists['lists']:
                    if lst['name'] == list_config['name']:
                        list_id = lst['id']
                        self.ids['list_id'] = list_id
                        print(f"✓ Found existing list: {list_id}")
                        break
                else:
                    print(f"✗ Could not find existing list")
                    raise
            else:
                raise

        # Create tasks hierarchy
        self.ids['task_ids'] = {}
        print(f"\nCreating task hierarchy...")

        for task_config in structure['tasks']:
            self._create_task_hierarchy(list_id, task_config, level=1, parent_id=None)

        # Save all IDs
        self._save_ids()

        # Print summary
        print("\n" + "="*70)
        print("TEST STRUCTURE CREATED SUCCESSFULLY")
        print("="*70)
        print(f"Folder ID: {self.ids['folder_id']}")
        print(f"List ID: {self.ids['list_id']}")
        print(f"Total tasks created: {len(self.ids['task_ids'])}")
        print(f"\nStructure IDs saved to: {self.ids_file}")
        print("="*70 + "\n")

    def _create_task_hierarchy(
        self,
        list_id: str,
        task_config: Dict,
        level: int,
        parent_id: Optional[str]
    ):
        """Recursively create task hierarchy."""
        indent = "  " * level
        print(f"{indent}[Level {level}] Creating: {task_config['name']}")

        # Prepare task data
        task_data = {
            'name': task_config['name'],
            'description': task_config.get('description', ''),
            'status': task_config.get('status', 'to do'),
            'priority': task_config.get('priority', 3),
        }

        if parent_id:
            task_data['parent'] = parent_id

        # Create task
        try:
            task = self.client.create_task(list_id, **task_data)
            task_id = task['id']

            # Store task ID
            self.ids['task_ids'][task_config['name']] = task_id

            print(f"{indent}  ✓ Task created: {task_id}")
            time.sleep(0.3)  # Rate limiting

            # Add tags
            if 'tags' in task_config and task_config['tags']:
                for tag in task_config['tags']:
                    try:
                        self.client.add_tag_to_task(task_id, tag)
                        print(f"{indent}    ✓ Added tag: {tag}")
                    except Exception as e:
                        print(f"{indent}    ⚠ Could not add tag {tag}: {e}")
                    time.sleep(0.2)

            # Add comments
            if 'comments' in task_config:
                for comment_data in task_config['comments']:
                    try:
                        self.client.create_task_comment(task_id, comment_data['text'])
                        print(f"{indent}    ✓ Added comment")
                    except Exception as e:
                        print(f"{indent}    ⚠ Could not add comment: {e}")
                    time.sleep(0.2)

            # Create subtasks recursively
            if 'subtasks' in task_config:
                print(f"{indent}  Creating {len(task_config['subtasks'])} subtasks...")
                for subtask_config in task_config['subtasks']:
                    self._create_task_hierarchy(
                        list_id,
                        subtask_config,
                        level + 1,
                        task_id
                    )

        except Exception as e:
            print(f"{indent}  ✗ Failed to create task: {e}")
            raise

    def get_test_ids(self) -> Dict:
        """Get the test structure IDs for use in tests."""
        return self.ids


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Setup test structure in ClickUp"
    )
    parser.add_argument(
        '--clean',
        action='store_true',
        help='Clean existing test structure before creating new one'
    )
    parser.add_argument(
        '--verify-only',
        action='store_true',
        help='Only verify structure exists, do not create'
    )
    parser.add_argument(
        '--clean-only',
        action='store_true',
        help='Only clean the structure, do not create'
    )

    args = parser.parse_args()

    # Initialize manager
    manager = TestStructureManager()

    try:
        # Clean if requested
        if args.clean or args.clean_only:
            manager.clean_structure()
            if args.clean_only:
                return

        # Verify only if requested
        if args.verify_only:
            exists = manager.verify_structure()
            sys.exit(0 if exists else 1)

        # Create structure
        manager.create_structure()

        # Verify it was created correctly
        if manager.verify_structure():
            print("✓ Test structure ready for testing!")
            sys.exit(0)
        else:
            print("✗ Structure verification failed")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
