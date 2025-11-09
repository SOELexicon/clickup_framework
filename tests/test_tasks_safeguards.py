"""
Tests for TasksAPI safeguards (view-before-modify and duplicate detection)
"""

import pytest
from unittest.mock import Mock, MagicMock
from clickup_framework.resources import TasksAPI


class TestViewBeforeModify:
    """Test view-before-modify requirement for update and delete operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.tasks_api = TasksAPI(self.mock_client)

    def test_update_with_task_object_succeeds(self):
        """Test that update works with a valid task object."""
        task = {"id": "task_123", "name": "Test Task"}
        self.mock_client.update_task.return_value = {"id": "task_123", "name": "Updated"}

        result = self.tasks_api.update(task, name="Updated")

        assert result["name"] == "Updated"
        self.mock_client.update_task.assert_called_once_with("task_123", name="Updated")

    def test_update_with_task_id_raises_error(self):
        """Test that update raises ValueError when given task ID instead of object."""
        with pytest.raises(ValueError) as exc_info:
            self.tasks_api.update("task_123", name="Updated")

        assert "must be viewed/fetched before updating" in str(exc_info.value)

    def test_update_with_invalid_object_raises_error(self):
        """Test that update raises ValueError with invalid object."""
        with pytest.raises(ValueError) as exc_info:
            self.tasks_api.update({"name": "No ID"}, status="done")

        assert "must be viewed/fetched before updating" in str(exc_info.value)

    def test_delete_with_task_object_succeeds(self):
        """Test that delete works with a valid task object."""
        task = {"id": "task_123", "name": "Test Task"}
        self.mock_client.delete_task.return_value = {}

        result = self.tasks_api.delete(task)

        assert result == {}
        self.mock_client.delete_task.assert_called_once_with("task_123")

    def test_delete_with_task_id_raises_error(self):
        """Test that delete raises ValueError when given task ID instead of object."""
        with pytest.raises(ValueError) as exc_info:
            self.tasks_api.delete("task_123")

        assert "must be viewed/fetched before deleting" in str(exc_info.value)

    def test_update_status_with_task_object_succeeds(self):
        """Test that update_status works with a valid task object."""
        task = {"id": "task_123", "name": "Test Task"}
        self.mock_client.update_task.return_value = {"id": "task_123", "status": "done"}

        result = self.tasks_api.update_status(task, "done")

        assert result["status"] == "done"
        self.mock_client.update_task.assert_called_once_with("task_123", status="done")

    def test_update_priority_with_task_object_succeeds(self):
        """Test that update_priority works with a valid task object."""
        task = {"id": "task_123", "name": "Test Task"}
        self.mock_client.update_task.return_value = {"id": "task_123", "priority": 1}

        result = self.tasks_api.update_priority(task, 1)

        assert result["priority"] == 1
        self.mock_client.update_task.assert_called_once_with("task_123", priority=1)

    def test_assign_with_task_object_succeeds(self):
        """Test that assign works with a valid task object."""
        task = {"id": "task_123", "name": "Test Task"}
        self.mock_client.update_task.return_value = {"id": "task_123"}

        result = self.tasks_api.assign(task, [123, 456])

        self.mock_client.update_task.assert_called_once_with(
            "task_123",
            assignees={"add": [123, 456]}
        )

    def test_unassign_with_task_object_succeeds(self):
        """Test that unassign works with a valid task object."""
        task = {"id": "task_123", "name": "Test Task"}
        self.mock_client.update_task.return_value = {"id": "task_123"}

        result = self.tasks_api.unassign(task, [123])

        self.mock_client.update_task.assert_called_once_with(
            "task_123",
            assignees={"rem": [123]}
        )


class TestDuplicateDetection:
    """Test duplicate detection for create operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.tasks_api = TasksAPI(self.mock_client, duplicate_threshold=0.95)

    def test_create_with_no_duplicates_succeeds(self):
        """Test that create works when no duplicates exist."""
        # Mock get_list_tasks to return no similar tasks
        self.mock_client.get_list_tasks.return_value = {
            "tasks": [
                {"id": "task_1", "name": "Different Task", "description": "Different"}
            ]
        }
        self.mock_client.create_task.return_value = {
            "id": "task_new",
            "name": "New Task"
        }

        result = self.tasks_api.create(
            list_id="list_123",
            name="New Task",
            description="New description"
        )

        assert result["id"] == "task_new"
        self.mock_client.create_task.assert_called_once()

    def test_create_with_duplicate_name_raises_error(self):
        """Test that create raises ValueError when duplicate found."""
        # Mock get_list_tasks to return a similar task
        self.mock_client.get_list_tasks.return_value = {
            "tasks": [
                {
                    "id": "task_existing",
                    "name": "Test Task",
                    "description": "Test description"
                }
            ]
        }

        with pytest.raises(ValueError) as exc_info:
            self.tasks_api.create(
                list_id="list_123",
                name="Test Task",
                description="Test description"
            )

        assert "Task already exists" in str(exc_info.value)
        assert "task_existing" in str(exc_info.value)
        self.mock_client.create_task.assert_not_called()

    def test_create_with_skip_duplicate_check(self):
        """Test that create works when skip_duplicate_check is True."""
        # Mock get_list_tasks to return a similar task (should be ignored)
        self.mock_client.get_list_tasks.return_value = {
            "tasks": [
                {
                    "id": "task_existing",
                    "name": "Test Task",
                    "description": "Test description"
                }
            ]
        }
        self.mock_client.create_task.return_value = {
            "id": "task_new",
            "name": "Test Task"
        }

        result = self.tasks_api.create(
            list_id="list_123",
            name="Test Task",
            description="Test description",
            skip_duplicate_check=True
        )

        assert result["id"] == "task_new"
        self.mock_client.create_task.assert_called_once()
        # Should not check for duplicates
        self.mock_client.get_list_tasks.assert_not_called()

    def test_similarity_calculation(self):
        """Test similarity calculation for strings."""
        # Test exact match
        assert self.tasks_api._calculate_similarity("Test", "Test") == 1.0

        # Test similar strings
        similarity = self.tasks_api._calculate_similarity(
            "Implement feature X",
            "Implement feature x"
        )
        assert similarity > 0.95

        # Test different strings
        similarity = self.tasks_api._calculate_similarity(
            "Implement feature X",
            "Fix bug Y"
        )
        assert similarity < 0.5

    def test_duplicate_check_with_parent(self):
        """Test that duplicate detection considers parent task."""
        # Mock get_list_tasks to return tasks with different parents
        self.mock_client.get_list_tasks.return_value = {
            "tasks": [
                {
                    "id": "task_1",
                    "name": "Subtask",
                    "description": "Description",
                    "parent": "parent_1"
                },
                {
                    "id": "task_2",
                    "name": "Subtask",
                    "description": "Description",
                    "parent": "parent_2"
                }
            ]
        }
        self.mock_client.create_task.return_value = {
            "id": "task_new",
            "name": "Subtask"
        }

        # Should not raise error since parent is different
        result = self.tasks_api.create(
            list_id="list_123",
            name="Subtask",
            description="Description",
            parent="parent_3"
        )

        assert result["id"] == "task_new"
        self.mock_client.create_task.assert_called_once()

    def test_duplicate_check_same_parent_raises_error(self):
        """Test that duplicate detection catches duplicates with same parent."""
        # Mock get_list_tasks to return task with same parent
        self.mock_client.get_list_tasks.return_value = {
            "tasks": [
                {
                    "id": "task_existing",
                    "name": "Subtask",
                    "description": "Description",
                    "parent": "parent_1"
                }
            ]
        }

        with pytest.raises(ValueError) as exc_info:
            self.tasks_api.create(
                list_id="list_123",
                name="Subtask",
                description="Description",
                parent="parent_1"
            )

        assert "Task already exists" in str(exc_info.value)
        self.mock_client.create_task.assert_not_called()
