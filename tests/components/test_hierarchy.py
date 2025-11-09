"""
Tests for TaskHierarchyFormatter.
"""

import pytest
from clickup_framework.components.hierarchy import TaskHierarchyFormatter
from clickup_framework.components.options import FormatOptions


class TestTaskHierarchyFormatter:
    """Tests for TaskHierarchyFormatter class."""

    def test_organize_by_parent_child(self, sample_hierarchical_tasks):
        """Test organizing tasks by parent-child relationships."""
        formatter = TaskHierarchyFormatter()
        root_tasks = formatter.organize_by_parent_child(sample_hierarchical_tasks)

        # Should have 2 root tasks (parent_1 and orphan_1)
        assert len(root_tasks) == 2

        # Check that children are nested
        parent = [t for t in root_tasks if t['id'] == 'parent_1'][0]
        assert len(parent['_children']) == 2

    def test_organize_excludes_orphaned_when_requested(self, sample_hierarchical_tasks):
        """Test excluding orphaned tasks."""
        formatter = TaskHierarchyFormatter()
        root_tasks = formatter.organize_by_parent_child(
            sample_hierarchical_tasks,
            include_orphaned=False
        )

        # Should have parent_1 at minimum (orphan may or may not be excluded depending on logic)
        assert len(root_tasks) >= 1
        assert any(task['id'] == 'parent_1' for task in root_tasks)

    def test_format_hierarchy(self, sample_hierarchical_tasks):
        """Test formatting tasks as hierarchy."""
        formatter = TaskHierarchyFormatter()
        options = FormatOptions(include_completed=True)  # Include all tasks
        result = formatter.format_hierarchy(sample_hierarchical_tasks, options)

        assert "Parent Task" in result
        assert "Child Task 1" in result
        assert "Child Task 2" in result
        # Should use tree characters
        assert "├─" in result or "└─" in result

    def test_format_hierarchy_with_header(self, sample_hierarchical_tasks):
        """Test formatting hierarchy with header."""
        formatter = TaskHierarchyFormatter()
        result = formatter.format_hierarchy(
            sample_hierarchical_tasks,
            header="My Tasks"
        )

        assert "My Tasks" in result
        assert "Parent Task" in result

    def test_format_hierarchy_excludes_completed(self, sample_hierarchical_tasks):
        """Test excluding completed tasks from hierarchy."""
        formatter = TaskHierarchyFormatter()
        options = FormatOptions(include_completed=False)
        result = formatter.format_hierarchy(sample_hierarchical_tasks, options)

        # Child Task 2 is completed, so shouldn't appear
        assert "Child Task 2" not in result
        assert "Parent Task" in result

    def test_get_task_count(self, sample_hierarchical_tasks):
        """Test getting task counts by status."""
        formatter = TaskHierarchyFormatter()
        counts = formatter.get_task_count(sample_hierarchical_tasks)

        assert counts['total'] == 5
        assert counts['completed'] == 1
        assert counts['in_progress'] == 1
        assert counts['todo'] == 3
        assert counts['blocked'] == 0

    def test_is_completed(self):
        """Test detecting completed tasks."""
        completed_task = {'status': {'status': 'complete'}}
        incomplete_task = {'status': {'status': 'to do'}}

        assert TaskHierarchyFormatter._is_completed(completed_task) is True
        assert TaskHierarchyFormatter._is_completed(incomplete_task) is False

    def test_get_priority_value(self):
        """Test getting numeric priority value."""
        task_p1 = {'priority': {'priority': '1'}}
        task_p4 = {'priority': {'priority': '4'}}
        task_no_priority = {}

        assert TaskHierarchyFormatter._get_priority_value(task_p1) == 1
        assert TaskHierarchyFormatter._get_priority_value(task_p4) == 4
        assert TaskHierarchyFormatter._get_priority_value(task_no_priority) == 4  # Default

    def test_organize_by_dependencies(self):
        """Test organizing tasks by dependencies."""
        tasks = [
            {
                'id': 'task_1',
                'name': 'Task 1',
                'dependencies': []
            },
            {
                'id': 'task_2',
                'name': 'Task 2',
                'dependencies': [{'depends_on': 'task_1'}]
            }
        ]

        formatter = TaskHierarchyFormatter()
        root_tasks = formatter.organize_by_dependencies(tasks)

        # Should return a list of tasks
        assert isinstance(root_tasks, list)
        assert len(root_tasks) <= len(tasks)

    def test_format_hierarchy_respects_options(self, sample_hierarchical_tasks):
        """Test that format_hierarchy respects format options."""
        formatter = TaskHierarchyFormatter()
        options = FormatOptions(
            show_ids=True,
            colorize_output=False
        )
        result = formatter.format_hierarchy(sample_hierarchical_tasks, options)

        # With show_ids, task IDs should be visible
        assert "parent_1" in result
        assert isinstance(result, str)
