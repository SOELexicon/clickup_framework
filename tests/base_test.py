"""
Base Test Class

Provides setup/teardown infrastructure for ClickUp Framework tests.
"""

import unittest
import time
from typing import Optional, Dict, List
from clickup_framework import ClickUpClient
from tests.test_config import (
    TEST_SPACE_ID,
    TEST_TEAM_ID,
    TEST_FOLDER_NAME,
    TEST_LIST_NAME,
    TEST_TASK_PREFIX,
    CLEANUP_AFTER_TESTS,
    VERBOSE_OUTPUT,
    TEST_FOLDER_ID,
    TEST_LIST_ID,
    TEST_STRUCTURE,
)


class ClickUpTestCase(unittest.TestCase):
    """
    Base test case for ClickUp Framework tests.

    Handles:
    - Client initialization
    - Test resource creation (folder, list)
    - Test resource tracking
    - Cleanup after tests
    """

    client: ClickUpClient
    test_folder_id: Optional[str] = None
    test_list_id: Optional[str] = None
    created_task_ids: List[str] = []
    created_resource_ids: Dict[str, List[str]] = {
        "tasks": [],
        "lists": [],
        "folders": [],
        "docs": [],
        "time_entries": [],
    }

    @classmethod
    def setUpClass(cls):
        """Set up test resources once for all tests in the class."""
        if VERBOSE_OUTPUT:
            print(f"\n{'='*60}")
            print(f"Setting up test environment for {cls.__name__}")
            print(f"{'='*60}")

        # Initialize client
        cls.client = ClickUpClient()

        # Use existing test structure if available
        if TEST_FOLDER_ID and TEST_LIST_ID:
            if VERBOSE_OUTPUT:
                print(f"Using existing test structure:")
                print(f"  Folder ID: {TEST_FOLDER_ID}")
                print(f"  List ID: {TEST_LIST_ID}")
                print(f"  Tasks: {len(TEST_STRUCTURE.get('task_ids', {}))}")
                print(f"{'='*60}\n")

            cls.test_folder_id = TEST_FOLDER_ID
            cls.test_list_id = TEST_LIST_ID
            return

        # Create test folder (fallback if structure doesn't exist)
        try:
            if VERBOSE_OUTPUT:
                print(f"No existing structure found, creating test folder: {TEST_FOLDER_NAME}")

            folder = cls.client.create_folder(TEST_SPACE_ID, TEST_FOLDER_NAME)
            cls.test_folder_id = folder["id"]
            cls.created_resource_ids["folders"].append(cls.test_folder_id)

            if VERBOSE_OUTPUT:
                print(f"✓ Test folder created: {cls.test_folder_id}")

            # Wait a bit for folder to be ready
            time.sleep(0.5)

            # Create test list
            if VERBOSE_OUTPUT:
                print(f"Creating test list: {TEST_LIST_NAME}")

            list_data = cls.client.create_list(cls.test_folder_id, TEST_LIST_NAME)
            cls.test_list_id = list_data["id"]
            cls.created_resource_ids["lists"].append(cls.test_list_id)

            if VERBOSE_OUTPUT:
                print(f"✓ Test list created: {cls.test_list_id}")
                print(f"⚠ Consider running 'python tests/setup_test_structure.py' for better test structure")
                print(f"{'='*60}\n")

        except Exception as e:
            print(f"ERROR setting up test resources: {e}")
            raise

    @classmethod
    def tearDownClass(cls):
        """Clean up test resources after all tests."""
        # If using the persistent test structure, don't delete it
        if TEST_FOLDER_ID and TEST_LIST_ID and cls.test_folder_id == TEST_FOLDER_ID:
            if VERBOSE_OUTPUT:
                print(f"\n{'='*60}")
                print(f"Using persistent test structure - skipping folder/list cleanup")
                print(f"{'='*60}\n")

            # Only clean up temporary tasks created during tests
            if CLEANUP_AFTER_TESTS:
                for task_id in cls.created_resource_ids.get("tasks", []):
                    try:
                        cls.client.delete_task(task_id)
                        if VERBOSE_OUTPUT:
                            print(f"✓ Deleted temporary task: {task_id}")
                    except Exception as e:
                        if VERBOSE_OUTPUT:
                            print(f"⚠️  Could not delete task {task_id}: {e}")
            return

        # Cleanup for dynamically created test resources
        if not CLEANUP_AFTER_TESTS:
            if VERBOSE_OUTPUT:
                print(f"\n⚠️  Cleanup skipped (CLEANUP_AFTER_TESTS=False)")
                print(f"Test folder ID: {cls.test_folder_id}")
            return

        if VERBOSE_OUTPUT:
            print(f"\n{'='*60}")
            print(f"Cleaning up test resources for {cls.__name__}")
            print(f"{'='*60}")

        try:
            # Clean up tasks
            for task_id in cls.created_resource_ids.get("tasks", []):
                try:
                    cls.client.delete_task(task_id)
                    if VERBOSE_OUTPUT:
                        print(f"✓ Deleted task: {task_id}")
                except Exception as e:
                    if VERBOSE_OUTPUT:
                        print(f"⚠️  Could not delete task {task_id}: {e}")

            # Clean up lists (except main test list which will be deleted with folder)
            for list_id in cls.created_resource_ids.get("lists", []):
                if list_id != cls.test_list_id:
                    try:
                        # Lists are deleted when folder is deleted
                        pass
                    except Exception as e:
                        if VERBOSE_OUTPUT:
                            print(f"⚠️  Could not delete list {list_id}: {e}")

            # Clean up folder (this will delete lists and tasks inside)
            if cls.test_folder_id:
                try:
                    # Note: Folder deletion endpoint might vary; using update to archive
                    # or you may need to manually delete from UI if API doesn't support it
                    if VERBOSE_OUTPUT:
                        print(f"✓ Test folder cleanup complete: {cls.test_folder_id}")
                        print(f"   (Note: May need manual cleanup from ClickUp UI)")
                except Exception as e:
                    if VERBOSE_OUTPUT:
                        print(f"⚠️  Could not delete folder {cls.test_folder_id}: {e}")

            if VERBOSE_OUTPUT:
                print(f"{'='*60}\n")

        except Exception as e:
            print(f"ERROR during cleanup: {e}")

    def track_task(self, task_id: str):
        """Track a created task for cleanup."""
        self.created_resource_ids["tasks"].append(task_id)

    def track_list(self, list_id: str):
        """Track a created list for cleanup."""
        self.created_resource_ids["lists"].append(list_id)

    def track_folder(self, folder_id: str):
        """Track a created folder for cleanup."""
        self.created_resource_ids["folders"].append(folder_id)

    def create_test_task(self, name: str = None, **kwargs) -> Dict:
        """
        Create a test task and track it for cleanup.

        Args:
            name: Task name (will be prefixed with TEST_TASK_PREFIX)
            **kwargs: Additional task data

        Returns:
            Created task data
        """
        if name is None:
            name = f"Test Task {len(self.created_resource_ids['tasks']) + 1}"

        full_name = f"{TEST_TASK_PREFIX} {name}"

        task = self.client.create_task(
            self.test_list_id,
            name=full_name,
            **kwargs
        )

        self.track_task(task["id"])

        if VERBOSE_OUTPUT:
            print(f"  Created test task: {task['id']} - {full_name}")

        return task
