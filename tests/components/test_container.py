"""
Tests for ContainerHierarchyFormatter.
"""

import pytest
from clickup_framework.components.container import ContainerHierarchyFormatter
from clickup_framework.components.options import FormatOptions


class TestContainerHierarchyFormatter:
    """Tests for ContainerHierarchyFormatter class."""

    def test_format_container_hierarchy(self, sample_container_tasks):
        """Test formatting tasks by container hierarchy."""
        formatter = ContainerHierarchyFormatter()
        result = formatter.format_container_hierarchy(sample_container_tasks)

        # Should contain container names
        assert "Engineering" in result
        assert "Backend" in result
        assert "API Development" in result

        # Should use tree characters
        assert "├─" in result or "└─" in result

    def test_format_container_hierarchy_shows_completion_stats(self, sample_container_tasks):
        """Test that container hierarchy shows completion statistics."""
        formatter = ContainerHierarchyFormatter()
        result = formatter.format_container_hierarchy(sample_container_tasks)

        # Should show task counts
        assert "(" in result and "/" in result and ")" in result

    def test_build_container_structure(self, sample_container_tasks):
        """Test building container structure from tasks."""
        formatter = ContainerHierarchyFormatter()
        options = FormatOptions(include_completed=True)  # Include all tasks
        structure = formatter._build_container_structure(sample_container_tasks, options)

        # Should have 2 spaces
        assert len(structure) == 2
        assert 'space_1' in structure
        assert 'space_2' in structure

        # Engineering space should have 2 folders
        eng_space = structure['space_1']
        assert len(eng_space['folders']) == 2

    def test_format_container_hierarchy_excludes_completed(self, sample_container_tasks):
        """Test excluding completed tasks from container hierarchy."""
        formatter = ContainerHierarchyFormatter()
        options = FormatOptions(include_completed=False)
        result = formatter.format_container_hierarchy(sample_container_tasks, options)

        # task_3 is completed, so shouldn't appear
        assert "Task in Different Folder" not in result

    def test_count_tasks(self, sample_container_tasks):
        """Test counting tasks in a space."""
        formatter = ContainerHierarchyFormatter()
        options = FormatOptions(include_completed=True)  # Include all tasks
        structure = formatter._build_container_structure(sample_container_tasks, options)

        space_data = structure['space_1']
        total, completed = formatter._count_tasks(space_data)

        assert total == 3  # 3 tasks in Engineering space
        assert completed == 1  # 1 completed task

    def test_count_tasks_in_folder(self, sample_container_tasks):
        """Test counting tasks in a folder."""
        formatter = ContainerHierarchyFormatter()
        options = FormatOptions()
        structure = formatter._build_container_structure(sample_container_tasks, options)

        space_data = structure['space_1']
        folder_data = space_data['folders']['folder_1']
        total, completed = formatter._count_tasks_in_folder(folder_data)

        assert total == 2  # 2 tasks in Backend folder
        assert completed == 0  # No completed tasks in this folder

    def test_is_completed(self):
        """Test detecting completed tasks."""
        completed = {
            'status': {'status': 'complete'}
        }
        incomplete = {
            'status': {'status': 'to do'}
        }

        formatter = ContainerHierarchyFormatter()
        assert formatter._is_completed(completed) is True
        assert formatter._is_completed(incomplete) is False

    def test_format_container_hierarchy_with_options(self, sample_container_tasks):
        """Test container hierarchy respects format options."""
        formatter = ContainerHierarchyFormatter()
        options = FormatOptions(
            colorize_output=False,
            show_ids=True
        )
        result = formatter.format_container_hierarchy(sample_container_tasks, options)

        # Should include task IDs
        assert "task_1" in result or "task_2" in result

    def test_format_container_hierarchy_header(self, sample_container_tasks):
        """Test that container hierarchy includes header."""
        formatter = ContainerHierarchyFormatter()
        result = formatter.format_container_hierarchy(sample_container_tasks)

        assert "Tasks organized by container" in result or "organized" in result.lower()

    def test_format_container_hierarchy_summary(self, sample_container_tasks):
        """Test that container hierarchy includes summary."""
        formatter = ContainerHierarchyFormatter()
        result = formatter.format_container_hierarchy(sample_container_tasks)

        # Should include summary at the end
        assert "Total:" in result or "total" in result.lower()
