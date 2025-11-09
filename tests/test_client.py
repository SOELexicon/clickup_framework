"""
Client API Tests

Tests for core ClickUp client API operations.
"""

import unittest
import time
from tests.base_test import ClickUpTestCase


class TestTaskOperations(ClickUpTestCase):
    """Test task CRUD operations."""

    def test_01_create_task(self):
        """Test task creation."""
        task = self.create_test_task("Basic Task", description="Test description")

        self.assertIn("id", task)
        self.assertIn("name", task)
        self.assertIn("[TEST]", task["name"])
        print(f"  ✓ Task created: {task['id']}")

    def test_02_get_task(self):
        """Test getting a task by ID."""
        task = self.create_test_task("Get Task Test")

        retrieved = self.client.get_task(task["id"])

        self.assertEqual(retrieved["id"], task["id"])
        self.assertIn("name", retrieved)
        print(f"  ✓ Task retrieved: {retrieved['id']}")

    def test_03_update_task(self):
        """Test updating a task."""
        task = self.create_test_task("Update Task Test")

        updated = self.client.update_task(
            task["id"],
            name="[TEST] Updated Task Name",
            description="Updated description"
        )

        self.assertEqual(updated["name"], "[TEST] Updated Task Name")
        print(f"  ✓ Task updated: {task['id']}")

    def test_04_get_list_tasks(self):
        """Test getting all tasks in a list."""
        # Create a few test tasks
        self.create_test_task("List Task 1")
        self.create_test_task("List Task 2")
        self.create_test_task("List Task 3")

        result = self.client.get_list_tasks(self.test_list_id)

        self.assertIn("tasks", result)
        self.assertIsInstance(result["tasks"], list)
        self.assertGreater(len(result["tasks"]), 0)
        print(f"  ✓ Retrieved {len(result['tasks'])} tasks from list")

    def test_05_delete_task(self):
        """Test deleting a task."""
        task = self.create_test_task("Delete Task Test")

        result = self.client.delete_task(task["id"])

        # Remove from tracking since we deleted it
        self.created_resource_ids["tasks"].remove(task["id"])

        self.assertIsInstance(result, dict)
        print(f"  ✓ Task deleted: {task['id']}")


class TestTaskComments(ClickUpTestCase):
    """Test task comment operations."""

    def test_01_add_comment(self):
        """Test adding a comment to a task."""
        task = self.create_test_task("Comment Task")

        comment = self.client.create_task_comment(
            task["id"],
            "This is a test comment"
        )

        self.assertIn("id", comment)
        self.assertIn("comment_text", comment)
        print(f"  ✓ Comment added to task")

    def test_02_get_comments(self):
        """Test getting comments from a task."""
        task = self.create_test_task("Get Comments Task")

        # Add a comment first
        self.client.create_task_comment(task["id"], "Test comment 1")
        self.client.create_task_comment(task["id"], "Test comment 2")

        result = self.client.get_task_comments(task["id"])

        self.assertIn("comments", result)
        self.assertIsInstance(result["comments"], list)
        self.assertGreaterEqual(len(result["comments"]), 2)
        print(f"  ✓ Retrieved {len(result['comments'])} comments")


class TestChecklistOperations(ClickUpTestCase):
    """Test checklist operations."""

    def test_01_create_checklist(self):
        """Test creating a checklist."""
        task = self.create_test_task("Checklist Task")

        checklist = self.client.create_checklist(task["id"], "Test Checklist")

        self.assertIn("id", checklist)
        self.assertIn("name", checklist)
        print(f"  ✓ Checklist created: {checklist['id']}")

        return checklist

    def test_02_add_checklist_item(self):
        """Test adding items to a checklist."""
        task = self.create_test_task("Checklist Item Task")
        checklist = self.client.create_checklist(task["id"], "Test Checklist")

        item = self.client.create_checklist_item(
            checklist["id"],
            "Test checklist item"
        )

        self.assertIn("id", item)
        self.assertIn("name", item)
        print(f"  ✓ Checklist item added")

    def test_03_update_checklist_item(self):
        """Test updating a checklist item."""
        task = self.create_test_task("Update Checklist Item Task")
        checklist = self.client.create_checklist(task["id"], "Test Checklist")
        item = self.client.create_checklist_item(checklist["id"], "Original item")

        updated = self.client.update_checklist_item(
            checklist["id"],
            item["id"],
            name="Updated item",
            resolved=True
        )

        self.assertIn("name", updated)
        print(f"  ✓ Checklist item updated")


class TestCustomFields(ClickUpTestCase):
    """Test custom field operations."""

    def test_01_get_custom_fields(self):
        """Test getting accessible custom fields."""
        result = self.client.get_accessible_custom_fields(self.test_list_id)

        self.assertIn("fields", result)
        self.assertIsInstance(result["fields"], list)
        print(f"  ✓ Retrieved {len(result['fields'])} custom fields")

    def test_02_set_custom_field_value(self):
        """Test setting a custom field value."""
        # Note: This test requires a custom field to exist
        # We'll skip if no custom fields are available
        fields = self.client.get_accessible_custom_fields(self.test_list_id)

        if not fields.get("fields"):
            self.skipTest("No custom fields available in test list")

        task = self.create_test_task("Custom Field Task")
        field = fields["fields"][0]

        # Try to set a value (this may fail if field type is incompatible)
        try:
            result = self.client.set_custom_field_value(
                task["id"],
                field["id"],
                "Test value"
            )
            print(f"  ✓ Custom field value set")
        except Exception as e:
            self.skipTest(f"Could not set custom field value: {e}")


class TestListOperations(ClickUpTestCase):
    """Test list operations."""

    def test_01_get_list(self):
        """Test getting a list by ID."""
        list_data = self.client.get_list(self.test_list_id)

        self.assertIn("id", list_data)
        self.assertIn("name", list_data)
        self.assertEqual(list_data["id"], self.test_list_id)
        print(f"  ✓ List retrieved: {list_data['id']}")

    def test_02_update_list(self):
        """Test updating a list."""
        result = self.client.update_list(
            self.test_list_id,
            name="[TEST] Updated List Name"
        )

        self.assertIn("id", result)
        print(f"  ✓ List updated")

        # Restore original name
        self.client.update_list(
            self.test_list_id,
            name="[TEST] Test Tasks"
        )


class TestFolderOperations(ClickUpTestCase):
    """Test folder operations."""

    def test_01_get_folder(self):
        """Test getting a folder by ID."""
        folder = self.client.get_folder(self.test_folder_id)

        self.assertIn("id", folder)
        self.assertIn("name", folder)
        self.assertEqual(folder["id"], self.test_folder_id)
        print(f"  ✓ Folder retrieved: {folder['id']}")

    def test_02_update_folder(self):
        """Test updating a folder."""
        result = self.client.update_folder(
            self.test_folder_id,
            name="[TEST] Updated Folder Name"
        )

        self.assertIn("id", result)
        print(f"  ✓ Folder updated")

        # Restore original name
        self.client.update_folder(
            self.test_folder_id,
            name="[TEST] Framework Tests"
        )


class TestSpaceOperations(ClickUpTestCase):
    """Test space operations."""

    def test_01_get_space(self):
        """Test getting a space by ID."""
        from tests.test_config import TEST_SPACE_ID

        space = self.client.get_space(TEST_SPACE_ID)

        self.assertIn("id", space)
        self.assertIn("name", space)
        print(f"  ✓ Space retrieved: {space['id']}")

    def test_02_get_space_tags(self):
        """Test getting tags from a space."""
        from tests.test_config import TEST_SPACE_ID

        result = self.client.get_space_tags(TEST_SPACE_ID)

        self.assertIn("tags", result)
        self.assertIsInstance(result["tags"], list)
        print(f"  ✓ Retrieved {len(result['tags'])} tags from space")


class TestSearchOperations(ClickUpTestCase):
    """Test search operations."""

    def test_01_search_workspace(self):
        """Test searching the workspace."""
        from tests.test_config import TEST_TEAM_ID

        # Create a task with unique content to search for
        unique_name = f"[TEST] Searchable Task {int(time.time())}"
        task = self.create_test_task(unique_name)

        # Wait a bit for indexing
        time.sleep(2)

        # Search for the task
        result = self.client.search(TEST_TEAM_ID, query="Searchable")

        self.assertIn("tasks", result)
        self.assertIsInstance(result["tasks"], list)
        print(f"  ✓ Search completed, found {len(result['tasks'])} tasks")


if __name__ == "__main__":
    unittest.main(verbosity=2)
