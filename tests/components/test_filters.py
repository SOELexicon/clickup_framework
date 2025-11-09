"""
Tests for TaskFilter.
"""

import pytest
from clickup_framework.components.filters import TaskFilter


class TestTaskFilter:
    """Tests for TaskFilter class."""

    def test_filter_by_status(self, sample_tasks_mixed_status):
        """Test filtering by status."""
        filtered = TaskFilter.filter_by_status(sample_tasks_mixed_status, "to do")

        assert len(filtered) == 2
        assert all(task['status']['status'] == 'to do' for task in filtered)

    def test_filter_by_status_in_progress(self, sample_tasks_mixed_status):
        """Test filtering by in progress status."""
        filtered = TaskFilter.filter_by_status(sample_tasks_mixed_status, "in progress")

        assert len(filtered) == 1
        assert filtered[0]['name'] == 'In Progress Task'

    def test_filter_by_status_case_insensitive(self, sample_tasks_mixed_status):
        """Test status filtering is case insensitive."""
        filtered = TaskFilter.filter_by_status(sample_tasks_mixed_status, "TO DO")

        assert len(filtered) == 2

    def test_filter_by_priority(self, sample_tasks_mixed_status):
        """Test filtering by priority."""
        filtered = TaskFilter.filter_by_priority(sample_tasks_mixed_status, 1)

        assert len(filtered) == 2
        assert all(int(task['priority']['priority']) == 1 for task in filtered)

    def test_filter_by_priority_string(self, sample_tasks_mixed_status):
        """Test filtering by priority with string input."""
        filtered = TaskFilter.filter_by_priority(sample_tasks_mixed_status, 2)

        assert len(filtered) == 1
        assert filtered[0]['name'] == 'In Progress Task'

    def test_filter_by_tags(self, sample_task):
        """Test filtering by tags."""
        tasks = [sample_task]
        filtered = TaskFilter.filter_by_tags(tasks, ["feature"])

        assert len(filtered) == 1
        assert filtered[0]['id'] == 'task_123'

    def test_filter_by_tags_multiple(self, sample_task):
        """Test filtering by multiple tags (OR operation)."""
        tasks = [sample_task]
        filtered = TaskFilter.filter_by_tags(tasks, ["feature", "nonexistent"])

        assert len(filtered) == 1  # Matches "feature"

    def test_filter_by_tags_no_match(self, sample_task):
        """Test filtering by tags with no matches."""
        tasks = [sample_task]
        filtered = TaskFilter.filter_by_tags(tasks, ["nonexistent"])

        assert len(filtered) == 0

    def test_filter_by_assignee(self, sample_task):
        """Test filtering by assignee."""
        tasks = [sample_task]
        filtered = TaskFilter.filter_by_assignee(tasks, "user_1")

        assert len(filtered) == 1

    def test_filter_by_assignee_no_match(self, sample_task):
        """Test filtering by assignee with no match."""
        tasks = [sample_task]
        filtered = TaskFilter.filter_by_assignee(tasks, "user_999")

        assert len(filtered) == 0

    def test_filter_completed_include(self, sample_tasks_mixed_status):
        """Test filtering completed tasks (including them)."""
        filtered = TaskFilter.filter_completed(sample_tasks_mixed_status, include_completed=True)

        assert len(filtered) == 5  # All tasks included

    def test_filter_completed_exclude(self, sample_tasks_mixed_status):
        """Test filtering completed tasks (excluding them)."""
        filtered = TaskFilter.filter_completed(sample_tasks_mixed_status, include_completed=False)

        assert len(filtered) == 4  # Only non-completed

    def test_filter_by_parent_root_tasks(self, sample_hierarchical_tasks):
        """Test filtering by parent to get root tasks."""
        filtered = TaskFilter.filter_by_parent(sample_hierarchical_tasks, parent_id=None)

        assert len(filtered) == 2  # parent_1 and orphan_1
        assert all(not task.get('parent') for task in filtered)

    def test_filter_by_parent_specific_parent(self, sample_hierarchical_tasks):
        """Test filtering by specific parent ID."""
        filtered = TaskFilter.filter_by_parent(sample_hierarchical_tasks, parent_id='parent_1')

        assert len(filtered) == 2  # child_1 and child_2
        assert all(task.get('parent') == 'parent_1' for task in filtered)

    def test_filter_by_date_range_with_start(self):
        """Test filtering by date range with start date."""
        tasks = [
            {'id': '1', 'due_date': '2024-01-05'},
            {'id': '2', 'due_date': '2024-01-15'},
            {'id': '3', 'due_date': '2024-01-25'},
        ]

        filtered = TaskFilter.filter_by_date_range(tasks, start_date='2024-01-10')

        assert len(filtered) == 2
        assert filtered[0]['id'] == '2'
        assert filtered[1]['id'] == '3'

    def test_filter_by_date_range_with_end(self):
        """Test filtering by date range with end date."""
        tasks = [
            {'id': '1', 'due_date': '2024-01-05'},
            {'id': '2', 'due_date': '2024-01-15'},
            {'id': '3', 'due_date': '2024-01-25'},
        ]

        filtered = TaskFilter.filter_by_date_range(tasks, end_date='2024-01-20')

        assert len(filtered) == 2
        assert filtered[0]['id'] == '1'
        assert filtered[1]['id'] == '2'

    def test_filter_by_date_range_with_both(self):
        """Test filtering by date range with both start and end."""
        tasks = [
            {'id': '1', 'due_date': '2024-01-05'},
            {'id': '2', 'due_date': '2024-01-15'},
            {'id': '3', 'due_date': '2024-01-25'},
        ]

        filtered = TaskFilter.filter_by_date_range(
            tasks,
            start_date='2024-01-10',
            end_date='2024-01-20'
        )

        assert len(filtered) == 1
        assert filtered[0]['id'] == '2'

    def test_filter_by_custom_function(self, sample_tasks_mixed_status):
        """Test filtering with custom function."""
        # Filter tasks with priority 1 or 2
        custom_filter = lambda task: int(task['priority']['priority']) <= 2
        filtered = TaskFilter.filter_by_custom_function(sample_tasks_mixed_status, custom_filter)

        assert len(filtered) == 3

    def test_combine_filters(self, sample_tasks_mixed_status):
        """Test combining multiple filters."""
        # Create filter functions
        filters = [
            lambda tasks: TaskFilter.filter_by_status(tasks, "to do"),
            lambda tasks: TaskFilter.filter_by_priority(tasks, 1),
        ]

        filtered = TaskFilter.combine_filters(sample_tasks_mixed_status, filters)

        # Should get only "to do" tasks with priority 1
        assert len(filtered) == 1
        assert filtered[0]['name'] == 'To Do Task'

    def test_combine_filters_empty_result(self, sample_tasks_mixed_status):
        """Test combining filters with no matches."""
        filters = [
            lambda tasks: TaskFilter.filter_by_status(tasks, "complete"),
            lambda tasks: TaskFilter.filter_by_priority(tasks, 1),  # No complete tasks with priority 1
        ]

        filtered = TaskFilter.combine_filters(sample_tasks_mixed_status, filters)

        assert len(filtered) == 0
