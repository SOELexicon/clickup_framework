"""
Task Relationship Tests

Tests for task dependency, link, and custom relationship functionality.
"""

import unittest
from tests.base_test import ClickUpTestCase


class TestTaskRelationships(ClickUpTestCase):
    """Test task relationship operations (dependencies and links)."""

    def test_01_add_dependency_waiting_on(self):
        """Test adding a 'waiting on' dependency."""
        # Create two tasks
        task_a = self.create_test_task("Task A - Must Complete First")
        task_b = self.create_test_task("Task B - Waits for Task A")

        # Make Task B wait on Task A
        result = self.client.add_task_dependency(
            task_b["id"],
            depends_on=task_a["id"]
        )

        # Verify (result should be empty dict on success)
        self.assertIsInstance(result, dict)
        print(f"  ✓ Task B now waits for Task A")

    def test_02_add_dependency_blocking(self):
        """Test adding a 'blocking' dependency."""
        # Create two tasks
        task_a = self.create_test_task("Task A - Blocks Task B")
        task_b = self.create_test_task("Task B - Blocked by Task A")

        # Make Task A block Task B
        result = self.client.add_task_dependency(
            task_a["id"],
            dependency_of=task_b["id"]
        )

        # Verify
        self.assertIsInstance(result, dict)
        print(f"  ✓ Task A now blocks Task B")

    def test_03_get_task_with_dependencies(self):
        """Test retrieving a task with dependencies."""
        # Create tasks with dependency
        task_a = self.create_test_task("Dependency Task A")
        task_b = self.create_test_task("Dependency Task B")

        self.client.add_task_dependency(task_b["id"], depends_on=task_a["id"])

        # Retrieve Task B and check for dependencies
        task_b_data = self.client.get_task(task_b["id"])

        # Check if dependencies field exists
        self.assertIn("dependencies", task_b_data)
        print(f"  ✓ Task retrieved with dependencies field")

        # Note: Dependencies field structure may vary based on API response

    def test_04_remove_dependency(self):
        """Test removing a dependency."""
        # Create tasks with dependency
        task_a = self.create_test_task("Remove Dep Task A")
        task_b = self.create_test_task("Remove Dep Task B")

        # Add dependency
        self.client.add_task_dependency(task_b["id"], depends_on=task_a["id"])

        # Remove dependency
        result = self.client.delete_task_dependency(
            task_b["id"],
            depends_on=task_a["id"]
        )

        # Verify
        self.assertIsInstance(result, dict)
        print(f"  ✓ Dependency removed successfully")

    def test_05_add_task_link(self):
        """Test adding a simple task link."""
        # Create two tasks
        task_a = self.create_test_task("Linked Task A")
        task_b = self.create_test_task("Linked Task B")

        # Link tasks
        result = self.client.add_task_link(task_a["id"], task_b["id"])

        # Verify (should return updated task with linked_tasks field)
        self.assertIsInstance(result, dict)
        self.assertIn("task", result)
        print(f"  ✓ Tasks linked successfully")

    def test_06_get_task_with_links(self):
        """Test retrieving a task with links."""
        # Create and link tasks
        task_a = self.create_test_task("Link Retrieve A")
        task_b = self.create_test_task("Link Retrieve B")

        self.client.add_task_link(task_a["id"], task_b["id"])

        # Retrieve task
        task_data = self.client.get_task(task_a["id"])

        # Check for linked_tasks field
        self.assertIn("linked_tasks", task_data)
        print(f"  ✓ Task retrieved with linked_tasks field")

    def test_07_remove_task_link(self):
        """Test removing a task link."""
        # Create and link tasks
        task_a = self.create_test_task("Unlink Task A")
        task_b = self.create_test_task("Unlink Task B")

        self.client.add_task_link(task_a["id"], task_b["id"])

        # Remove link
        result = self.client.delete_task_link(task_a["id"], task_b["id"])

        # Verify
        self.assertIsInstance(result, dict)
        self.assertIn("task", result)
        print(f"  ✓ Task link removed successfully")

    def test_08_dependency_error_handling(self):
        """Test error handling for invalid dependency operations."""
        task = self.create_test_task("Error Handling Task")

        # Test: Both depends_on and dependency_of provided (should fail)
        with self.assertRaises(ValueError):
            self.client.add_task_dependency(
                task["id"],
                depends_on="task_a",
                dependency_of="task_b"
            )
        print(f"  ✓ Correctly rejects both depends_on and dependency_of")

        # Test: Neither depends_on nor dependency_of provided (should fail)
        with self.assertRaises(ValueError):
            self.client.add_task_dependency(task["id"])
        print(f"  ✓ Correctly requires one of depends_on or dependency_of")


class TestTasksAPIRelationships(ClickUpTestCase):
    """Test TasksAPI relationship convenience methods."""

    def setUp(self):
        """Set up TasksAPI instance."""
        from clickup_framework.resources import TasksAPI
        self.tasks_api = TasksAPI(self.client)

    def test_01_add_dependency_waiting_on_convenience(self):
        """Test TasksAPI add_dependency_waiting_on convenience method."""
        task_a = self.create_test_task("Convenience Wait A")
        task_b = self.create_test_task("Convenience Wait B")

        result = self.tasks_api.add_dependency_waiting_on(task_b["id"], task_a["id"])

        self.assertIsInstance(result, dict)
        print(f"  ✓ TasksAPI add_dependency_waiting_on works")

    def test_02_add_dependency_blocking_convenience(self):
        """Test TasksAPI add_dependency_blocking convenience method."""
        task_a = self.create_test_task("Convenience Block A")
        task_b = self.create_test_task("Convenience Block B")

        result = self.tasks_api.add_dependency_blocking(task_a["id"], task_b["id"])

        self.assertIsInstance(result, dict)
        print(f"  ✓ TasksAPI add_dependency_blocking works")

    def test_03_add_link_convenience(self):
        """Test TasksAPI add_link convenience method."""
        task_a = self.create_test_task("Convenience Link A")
        task_b = self.create_test_task("Convenience Link B")

        result = self.tasks_api.add_link(task_a["id"], task_b["id"])

        self.assertIsInstance(result, dict)
        print(f"  ✓ TasksAPI add_link works")

    def test_04_remove_link_convenience(self):
        """Test TasksAPI remove_link convenience method."""
        task_a = self.create_test_task("Convenience Unlink A")
        task_b = self.create_test_task("Convenience Unlink B")

        # Add then remove link
        self.tasks_api.add_link(task_a["id"], task_b["id"])
        result = self.tasks_api.remove_link(task_a["id"], task_b["id"])

        self.assertIsInstance(result, dict)
        print(f"  ✓ TasksAPI remove_link works")


if __name__ == "__main__":
    unittest.main(verbosity=2)
