"""
Tests for circular reference detection in task hierarchies.

This module tests the circular reference detection feature that prevents
infinite loops when tasks have circular parent-child relationships.

Acceptance Criteria:
- All circular references are detected
- Error is logged with full cycle path (task names and IDs)
- Cycle is broken at the most recent link
- Hierarchy continues to render in corrected state
- User is notified of the data integrity issue
- Tool never crashes or hangs
- Performance impact is minimal
"""

import pytest
import logging
from clickup_framework.components.hierarchy import TaskHierarchyFormatter
from clickup_framework.components.options import FormatOptions


@pytest.fixture
def circular_three_task_cycle():
    """Simple 3-task circular reference: A → B → C → A"""
    return [
        {
            'id': 'task_a',
            'name': 'Task A',
            'parent': 'task_c',  # Points to C, creating cycle
            'status': {'status': 'to do'}
        },
        {
            'id': 'task_b',
            'name': 'Task B',
            'parent': 'task_a',  # Points to A
            'status': {'status': 'to do'}
        },
        {
            'id': 'task_c',
            'name': 'Task C',
            'parent': 'task_b',  # Points to B
            'status': {'status': 'to do'}
        }
    ]


@pytest.fixture
def circular_two_task_cycle():
    """Simple 2-task circular reference: A → B → A"""
    return [
        {
            'id': 'task_a',
            'name': 'Task A',
            'parent': 'task_b',  # Points to B
            'status': {'status': 'to do'}
        },
        {
            'id': 'task_b',
            'name': 'Task B',
            'parent': 'task_a',  # Points to A, creating cycle
            'status': {'status': 'to do'}
        }
    ]


@pytest.fixture
def circular_self_reference():
    """Task that references itself"""
    return [
        {
            'id': 'task_a',
            'name': 'Task A',
            'parent': 'task_a',  # Points to itself
            'status': {'status': 'to do'}
        }
    ]


@pytest.fixture
def circular_with_non_circular():
    """Mix of circular and non-circular tasks"""
    return [
        # Non-circular branch
        {
            'id': 'root_1',
            'name': 'Root 1',
            'parent': None,
            'status': {'status': 'to do'}
        },
        {
            'id': 'child_1',
            'name': 'Child 1',
            'parent': 'root_1',
            'status': {'status': 'to do'}
        },
        # Circular branch: A → B → C → A
        {
            'id': 'task_a',
            'name': 'Task A',
            'parent': 'task_c',
            'status': {'status': 'to do'}
        },
        {
            'id': 'task_b',
            'name': 'Task B',
            'parent': 'task_a',
            'status': {'status': 'to do'}
        },
        {
            'id': 'task_c',
            'name': 'Task C',
            'parent': 'task_b',
            'status': {'status': 'to do'}
        }
    ]


@pytest.fixture
def circular_complex_cycle():
    """Complex circular reference with 5 tasks"""
    return [
        {
            'id': 'task_1',
            'name': 'Task 1',
            'parent': 'task_5',  # Points to 5, creating cycle
            'status': {'status': 'to do'}
        },
        {
            'id': 'task_2',
            'name': 'Task 2',
            'parent': 'task_1',
            'status': {'status': 'to do'}
        },
        {
            'id': 'task_3',
            'name': 'Task 3',
            'parent': 'task_2',
            'status': {'status': 'to do'}
        },
        {
            'id': 'task_4',
            'name': 'Task 4',
            'parent': 'task_3',
            'status': {'status': 'to do'}
        },
        {
            'id': 'task_5',
            'name': 'Task 5',
            'parent': 'task_4',
            'status': {'status': 'to do'}
        }
    ]


class TestCircularReferenceDetection:
    """Test circular reference detection."""

    def test_detects_simple_three_task_cycle(self, circular_three_task_cycle, caplog):
        """Test detection of A → B → C → A cycle."""
        formatter = TaskHierarchyFormatter()

        with caplog.at_level(logging.ERROR):
            root_tasks = formatter.organize_by_parent_child(circular_three_task_cycle)

        # Verify cycle was detected and logged
        assert any("Circular reference detected" in record.message for record in caplog.records)
        # The cycle path order depends on where detection starts - just verify all tasks are mentioned
        error_messages = [record.message for record in caplog.records if record.levelname == 'ERROR']
        assert any("Task A" in msg and "Task B" in msg and "Task C" in msg for msg in error_messages)

        # Verify all tasks in cycle were promoted to root level
        root_ids = {task['id'] for task in root_tasks}
        assert 'task_a' in root_ids
        assert 'task_b' in root_ids
        assert 'task_c' in root_ids

        # Verify no circular children relationships
        for task in root_tasks:
            assert len(task.get('_children', [])) == 0

    def test_detects_two_task_cycle(self, circular_two_task_cycle, caplog):
        """Test detection of A → B → A cycle."""
        formatter = TaskHierarchyFormatter()

        with caplog.at_level(logging.ERROR):
            root_tasks = formatter.organize_by_parent_child(circular_two_task_cycle)

        # Verify cycle was detected
        assert any("Circular reference detected" in record.message for record in caplog.records)

        # Verify both tasks promoted to root
        root_ids = {task['id'] for task in root_tasks}
        assert 'task_a' in root_ids
        assert 'task_b' in root_ids

    def test_detects_self_reference(self, circular_self_reference, caplog):
        """Test detection of task pointing to itself."""
        formatter = TaskHierarchyFormatter()

        with caplog.at_level(logging.ERROR):
            root_tasks = formatter.organize_by_parent_child(circular_self_reference)

        # Verify cycle was detected
        assert any("Circular reference detected" in record.message for record in caplog.records)

        # Verify task is promoted to root
        assert len(root_tasks) == 1
        assert root_tasks[0]['id'] == 'task_a'

    def test_handles_mixed_circular_and_non_circular(self, circular_with_non_circular, caplog):
        """Test handling of mix of circular and non-circular tasks."""
        formatter = TaskHierarchyFormatter()

        with caplog.at_level(logging.ERROR):
            root_tasks = formatter.organize_by_parent_child(circular_with_non_circular)

        # Verify cycle was detected
        assert any("Circular reference detected" in record.message for record in caplog.records)

        # Verify all tasks in cycle promoted to root
        root_ids = {task['id'] for task in root_tasks}
        assert 'task_a' in root_ids
        assert 'task_b' in root_ids
        assert 'task_c' in root_ids

        # Verify non-circular branch is preserved correctly
        assert 'root_1' in root_ids
        root_1 = [t for t in root_tasks if t['id'] == 'root_1'][0]
        assert len(root_1['_children']) == 1
        assert root_1['_children'][0]['id'] == 'child_1'

    def test_detects_complex_five_task_cycle(self, circular_complex_cycle, caplog):
        """Test detection of complex 5-task cycle."""
        formatter = TaskHierarchyFormatter()

        with caplog.at_level(logging.ERROR):
            root_tasks = formatter.organize_by_parent_child(circular_complex_cycle)

        # Verify cycle was detected
        assert any("Circular reference detected" in record.message for record in caplog.records)

        # Verify all 5 tasks promoted to root
        root_ids = {task['id'] for task in root_tasks}
        for i in range(1, 6):
            assert f'task_{i}' in root_ids

    def test_error_log_includes_task_names(self, circular_three_task_cycle, caplog):
        """Test that error log includes task names in cycle path."""
        formatter = TaskHierarchyFormatter()

        with caplog.at_level(logging.ERROR):
            formatter.organize_by_parent_child(circular_three_task_cycle)

        # Verify task names are in the error message
        error_messages = [record.message for record in caplog.records if record.levelname == 'ERROR']
        assert any("Task A" in msg and "Task B" in msg and "Task C" in msg for msg in error_messages)

    def test_error_log_includes_task_ids(self, circular_three_task_cycle, caplog):
        """Test that error log includes task IDs in cycle path."""
        formatter = TaskHierarchyFormatter()

        with caplog.at_level(logging.ERROR):
            formatter.organize_by_parent_child(circular_three_task_cycle)

        # Verify task IDs are in the error message
        error_messages = [record.message for record in caplog.records if record.levelname == 'ERROR']
        assert any("task_a" in msg and "task_b" in msg and "task_c" in msg for msg in error_messages)


class TestCircularReferenceWarnings:
    """Test user warning generation for circular references."""

    def test_warning_generated_for_circular_reference(self, circular_three_task_cycle):
        """Test that user warning is generated when circular reference detected."""
        formatter = TaskHierarchyFormatter()
        formatter.organize_by_parent_child(circular_three_task_cycle)

        warning = formatter.get_circular_reference_warnings()

        assert warning is not None
        assert "Warning: Circular references detected" in warning
        assert "Cycle 1:" in warning

    def test_warning_includes_cycle_path(self, circular_three_task_cycle):
        """Test that warning includes the cycle path with task names."""
        formatter = TaskHierarchyFormatter()
        formatter.organize_by_parent_child(circular_three_task_cycle)

        warning = formatter.get_circular_reference_warnings()

        # Verify cycle path is shown with arrows
        assert "Task A" in warning or "Task B" in warning or "Task C" in warning
        assert "→" in warning

    def test_warning_explains_resolution(self, circular_three_task_cycle):
        """Test that warning explains how the issue was resolved."""
        formatter = TaskHierarchyFormatter()
        formatter.organize_by_parent_child(circular_three_task_cycle)

        warning = formatter.get_circular_reference_warnings()

        # Verify explanation is included
        assert "promoted to root level" in warning
        assert "fix the parent relationships" in warning

    def test_no_warning_for_non_circular_tasks(self, sample_hierarchical_tasks):
        """Test that no warning is generated for non-circular tasks."""
        formatter = TaskHierarchyFormatter()
        formatter.organize_by_parent_child(sample_hierarchical_tasks)

        warning = formatter.get_circular_reference_warnings()

        assert warning is None

    def test_warning_shown_in_format_hierarchy_output(self, circular_three_task_cycle):
        """Test that warning is prepended to hierarchy output."""
        formatter = TaskHierarchyFormatter()
        options = FormatOptions()
        result = formatter.format_hierarchy(circular_three_task_cycle, options)

        # Verify warning appears at the top of output
        assert "⚠️  Warning: Circular references detected" in result
        assert result.index("Warning") < result.index("Task")


class TestCircularReferenceHierarchyRendering:
    """Test that hierarchy renders correctly after breaking circular references."""

    def test_hierarchy_renders_without_crash(self, circular_three_task_cycle):
        """Test that hierarchy rendering doesn't crash with circular references."""
        formatter = TaskHierarchyFormatter()
        options = FormatOptions()

        # Should not raise exception
        result = formatter.format_hierarchy(circular_three_task_cycle, options)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_all_tasks_visible_in_output(self, circular_three_task_cycle):
        """Test that all tasks are visible in rendered output."""
        formatter = TaskHierarchyFormatter()
        options = FormatOptions(show_ids=True)
        result = formatter.format_hierarchy(circular_three_task_cycle, options)

        # All tasks should be visible
        assert "task_a" in result
        assert "task_b" in result
        assert "task_c" in result

    def test_circular_tasks_shown_at_root_level(self, circular_with_non_circular):
        """Test that circular tasks are shown at root level."""
        formatter = TaskHierarchyFormatter()
        options = FormatOptions(show_ids=True)
        result = formatter.format_hierarchy(circular_with_non_circular, options)

        # Circular tasks should not be nested under each other
        lines = result.split('\n')
        circular_task_lines = [line for line in lines if 'task_a' in line or 'task_b' in line or 'task_c' in line]

        # All circular tasks should have minimal indentation (root level)
        for line in circular_task_lines:
            # Root level tasks should not have deep tree characters
            assert line.count('├─') + line.count('└─') <= 1

    def test_non_circular_hierarchy_preserved(self, circular_with_non_circular):
        """Test that non-circular hierarchy is preserved correctly."""
        formatter = TaskHierarchyFormatter()
        root_tasks = formatter.organize_by_parent_child(circular_with_non_circular)

        # Find root_1 and verify its structure is intact
        root_1 = [t for t in root_tasks if t['id'] == 'root_1'][0]
        assert len(root_1['_children']) == 1
        assert root_1['_children'][0]['id'] == 'child_1'


class TestCircularReferencePerformance:
    """Test performance characteristics of circular reference detection."""

    def test_large_hierarchy_with_no_cycles_fast(self):
        """Test performance with large non-circular hierarchy."""
        import time

        # Create a deep hierarchy with 100 tasks, no cycles
        tasks = []
        for i in range(100):
            task = {
                'id': f'task_{i}',
                'name': f'Task {i}',
                'parent': f'task_{i-1}' if i > 0 else None,
                'status': {'status': 'to do'}
            }
            tasks.append(task)

        formatter = TaskHierarchyFormatter()

        # Should complete quickly (< 1 second)
        start_time = time.time()
        result = formatter.organize_by_parent_child(tasks)
        elapsed_time = time.time() - start_time

        assert len(result) == 1  # One root task
        assert result[0]['id'] == 'task_0'
        assert elapsed_time < 1.0, f"Performance test failed: took {elapsed_time:.2f}s (expected < 1s)"

    def test_multiple_small_cycles_detected(self):
        """Test detection of multiple independent cycles."""
        tasks = [
            # Cycle 1: A → B → A
            {'id': 'a', 'name': 'A', 'parent': 'b', 'status': {'status': 'to do'}},
            {'id': 'b', 'name': 'B', 'parent': 'a', 'status': {'status': 'to do'}},
            # Cycle 2: X → Y → Z → X
            {'id': 'x', 'name': 'X', 'parent': 'z', 'status': {'status': 'to do'}},
            {'id': 'y', 'name': 'Y', 'parent': 'x', 'status': {'status': 'to do'}},
            {'id': 'z', 'name': 'Z', 'parent': 'y', 'status': {'status': 'to do'}},
        ]

        formatter = TaskHierarchyFormatter()
        root_tasks = formatter.organize_by_parent_child(tasks)

        # Verify all tasks promoted to root
        assert len(root_tasks) == 5

        # Verify multiple cycles were detected
        assert len(formatter.circular_refs_detected) >= 2


class TestCircularReferenceEdgeCases:
    """Test edge cases in circular reference detection."""

    def test_cycle_with_missing_task_in_chain(self):
        """Test cycle where one task in the chain is missing from data."""
        tasks = [
            {'id': 'task_a', 'name': 'Task A', 'parent': 'task_b', 'status': {'status': 'to do'}},
            # task_b is missing - referenced but not in list
            {'id': 'task_c', 'name': 'Task C', 'parent': 'task_a', 'status': {'status': 'to do'}},
        ]

        formatter = TaskHierarchyFormatter()

        # Should not crash
        root_tasks = formatter.organize_by_parent_child(tasks)

        # Should handle gracefully
        assert isinstance(root_tasks, list)

    def test_empty_task_list(self):
        """Test with empty task list."""
        formatter = TaskHierarchyFormatter()
        root_tasks = formatter.organize_by_parent_child([])

        assert root_tasks == []
        assert formatter.get_circular_reference_warnings() is None

    def test_single_task_no_cycle(self):
        """Test with single task with no parent."""
        tasks = [{'id': 'task_1', 'name': 'Task 1', 'parent': None, 'status': {'status': 'to do'}}]

        formatter = TaskHierarchyFormatter()
        root_tasks = formatter.organize_by_parent_child(tasks)

        assert len(root_tasks) == 1
        assert formatter.get_circular_reference_warnings() is None

    def test_cycle_detection_resets_between_calls(self, circular_three_task_cycle, sample_hierarchical_tasks):
        """Test that cycle detection state is reset between organize calls."""
        formatter = TaskHierarchyFormatter()

        # First call with circular data
        formatter.organize_by_parent_child(circular_three_task_cycle)
        warning_1 = formatter.get_circular_reference_warnings()
        assert warning_1 is not None

        # Second call with non-circular data
        formatter.organize_by_parent_child(sample_hierarchical_tasks)
        warning_2 = formatter.get_circular_reference_warnings()
        assert warning_2 is None  # State should be reset
