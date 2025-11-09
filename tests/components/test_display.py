"""
Tests for DisplayManager.
"""

import pytest
from unittest.mock import Mock, MagicMock
from clickup_framework.components.display import DisplayManager
from clickup_framework.components.options import FormatOptions


class TestDisplayManager:
    """Tests for DisplayManager class."""

    def test_init_without_client(self):
        """Test initializing DisplayManager without client."""
        display = DisplayManager()

        assert display.client is None
        assert display.task_formatter is not None
        assert display.hierarchy_formatter is not None
        assert display.container_formatter is not None
        assert display.filter is not None

    def test_init_with_client(self):
        """Test initializing DisplayManager with client."""
        mock_client = Mock()
        display = DisplayManager(mock_client)

        assert display.client is mock_client

    def test_hierarchy_view(self, sample_hierarchical_tasks):
        """Test hierarchy view."""
        display = DisplayManager()
        result = display.hierarchy_view(sample_hierarchical_tasks)

        assert isinstance(result, str)
        assert "Parent Task" in result
        assert len(result) > 0

    def test_hierarchy_view_with_options(self, sample_hierarchical_tasks):
        """Test hierarchy view with custom options."""
        display = DisplayManager()
        options = FormatOptions(show_ids=True)
        result = display.hierarchy_view(sample_hierarchical_tasks, options)

        assert isinstance(result, str)
        assert "parent_1" in result

    def test_hierarchy_view_with_header(self, sample_hierarchical_tasks):
        """Test hierarchy view with header."""
        display = DisplayManager()
        result = display.hierarchy_view(sample_hierarchical_tasks, header="My Tasks")

        assert "My Tasks" in result

    def test_container_view(self, sample_container_tasks):
        """Test container view."""
        display = DisplayManager()
        result = display.container_view(sample_container_tasks)

        assert isinstance(result, str)
        assert "Engineering" in result
        assert len(result) > 0

    def test_container_view_with_options(self, sample_container_tasks):
        """Test container view with custom options."""
        display = DisplayManager()
        options = FormatOptions(include_completed=False)
        result = display.container_view(sample_container_tasks, options)

        # Completed task should be excluded
        assert "Task in Different Folder" not in result

    def test_flat_view(self, sample_hierarchical_tasks):
        """Test flat view."""
        display = DisplayManager()
        result = display.flat_view(sample_hierarchical_tasks)

        assert isinstance(result, str)
        # Should show all tasks
        assert "Parent Task" in result
        assert "Child Task 1" in result

    def test_flat_view_with_header(self, sample_hierarchical_tasks):
        """Test flat view with header."""
        display = DisplayManager()
        result = display.flat_view(sample_hierarchical_tasks, header="All Tasks")

        assert "All Tasks" in result

    def test_filtered_view_by_status(self, sample_tasks_mixed_status):
        """Test filtered view by status."""
        display = DisplayManager()
        result = display.filtered_view(
            sample_tasks_mixed_status,
            status="to do",
            view_mode='flat'
        )

        assert "To Do Task" in result
        assert "Another To Do" in result
        assert "In Progress Task" not in result

    def test_filtered_view_by_priority(self, sample_tasks_mixed_status):
        """Test filtered view by priority."""
        display = DisplayManager()
        result = display.filtered_view(
            sample_tasks_mixed_status,
            priority=1,
            view_mode='flat'
        )

        assert "To Do Task" in result
        assert "Blocked Task" in result

    def test_filtered_view_by_tags(self, sample_task):
        """Test filtered view by tags."""
        display = DisplayManager()
        result = display.filtered_view(
            [sample_task],
            tags=["feature"],
            view_mode='flat'
        )

        assert "Implement new feature" in result

    def test_filtered_view_exclude_completed(self, sample_tasks_mixed_status):
        """Test filtered view excluding completed tasks."""
        display = DisplayManager()
        result = display.filtered_view(
            sample_tasks_mixed_status,
            include_completed=False,
            view_mode='flat'
        )

        assert "Complete Task" not in result
        assert "To Do Task" in result

    def test_filtered_view_hierarchy_mode(self, sample_hierarchical_tasks):
        """Test filtered view in hierarchy mode."""
        display = DisplayManager()
        result = display.filtered_view(
            sample_hierarchical_tasks,
            view_mode='hierarchy'
        )

        assert "Parent Task" in result
        assert "├─" in result or "└─" in result

    def test_filtered_view_container_mode(self, sample_container_tasks):
        """Test filtered view in container mode."""
        display = DisplayManager()
        result = display.filtered_view(
            sample_container_tasks,
            view_mode='container'
        )

        assert "Engineering" in result
        assert "├─" in result or "└─" in result

    def test_get_list_tasks_display_requires_client(self):
        """Test get_list_tasks_display raises error without client."""
        display = DisplayManager()  # No client

        with pytest.raises(ValueError, match="ClickUpClient must be configured"):
            display.get_list_tasks_display("list_id")

    def test_get_list_tasks_display_with_client(self, sample_hierarchical_tasks):
        """Test get_list_tasks_display with client."""
        mock_client = Mock()
        mock_client.get_list_tasks = Mock(return_value=sample_hierarchical_tasks)

        display = DisplayManager(mock_client)
        result = display.get_list_tasks_display("list_id")

        mock_client.get_list_tasks.assert_called_once_with("list_id")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_list_tasks_display_view_modes(self, sample_hierarchical_tasks):
        """Test different view modes for get_list_tasks_display."""
        mock_client = Mock()
        mock_client.get_list_tasks = Mock(return_value=sample_hierarchical_tasks)

        display = DisplayManager(mock_client)

        # Test hierarchy mode
        result_hierarchy = display.get_list_tasks_display("list_id", view_mode='hierarchy')
        assert "Parent Task" in result_hierarchy

        # Test flat mode
        result_flat = display.get_list_tasks_display("list_id", view_mode='flat')
        assert "Parent Task" in result_flat

    def test_get_team_tasks_display_requires_client(self):
        """Test get_team_tasks_display raises error without client."""
        display = DisplayManager()  # No client

        with pytest.raises(ValueError, match="ClickUpClient must be configured"):
            display.get_team_tasks_display("team_id")

    def test_get_team_tasks_display_with_client(self, sample_container_tasks):
        """Test get_team_tasks_display with client."""
        mock_client = Mock()
        mock_client.get_team_tasks = Mock(return_value=sample_container_tasks)

        display = DisplayManager(mock_client)
        result = display.get_team_tasks_display("team_id")

        mock_client.get_team_tasks.assert_called_once_with("team_id")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_summary_stats(self, sample_tasks_mixed_status):
        """Test getting summary statistics."""
        display = DisplayManager()
        result = display.summary_stats(sample_tasks_mixed_status)

        assert "Task Summary:" in result
        assert "Total: 5" in result
        assert "Completed: 1" in result
        assert "In Progress: 1" in result
        assert "Blocked: 1" in result
        assert "To Do: 2" in result

    def test_summary_stats_empty_list(self):
        """Test summary stats with empty task list."""
        display = DisplayManager()
        result = display.summary_stats([])

        assert "Total: 0" in result
