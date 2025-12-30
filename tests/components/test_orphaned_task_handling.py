"""Tests for orphaned task handling in task hierarchies.

This module tests the orphaned task detection and resolution functionality,
including API fetching of missing parents.
"""

import pytest
import logging
from unittest.mock import Mock, MagicMock
from clickup_framework.components.hierarchy import TaskHierarchyFormatter


@pytest.fixture
def orphaned_tasks_no_client():
    """Tasks with orphaned task (missing parent), no client available."""
    return [
        {'id': 'root_1', 'name': 'Root Task', 'parent': None, 'status': {'status': 'to do'}},
        {'id': 'orphan_1', 'name': 'Orphaned Task', 'parent': 'missing_parent', 'status': {'status': 'to do'}},
        {'id': 'child_1', 'name': 'Child Task', 'parent': 'root_1', 'status': {'status': 'to do'}}
    ]


@pytest.fixture
def orphaned_tasks_with_parent_data():
    """Tasks with orphaned task and the parent data that should be fetched."""
    tasks = [
        {'id': 'root_1', 'name': 'Root Task', 'parent': None, 'status': {'status': 'to do'}},
        {'id': 'orphan_1', 'name': 'Orphaned Task', 'parent': 'missing_parent', 'status': {'status': 'to do'}},
        {'id': 'child_1', 'name': 'Child Task', 'parent': 'root_1', 'status': {'status': 'to do'}}
    ]

    parent_data = {
        'id': 'missing_parent',
        'name': 'Fetched Parent Task',
        'parent': None,
        'status': {'status': 'to do'}
    }

    return tasks, parent_data


@pytest.fixture
def multiple_orphaned_tasks():
    """Multiple orphaned tasks with different missing parents."""
    return [
        {'id': 'root_1', 'name': 'Root Task', 'parent': None, 'status': {'status': 'to do'}},
        {'id': 'orphan_1', 'name': 'Orphaned Task 1', 'parent': 'missing_parent_1', 'status': {'status': 'to do'}},
        {'id': 'orphan_2', 'name': 'Orphaned Task 2', 'parent': 'missing_parent_2', 'status': {'status': 'to do'}},
        {'id': 'orphan_3', 'name': 'Orphaned Task 3', 'parent': 'missing_parent_1', 'status': {'status': 'to do'}}
    ]


class TestOrphanedTaskDetection:
    """Test orphaned task detection without API client."""

    def test_detects_orphaned_task_without_client(self, orphaned_tasks_no_client):
        """Test orphaned tasks are promoted to root when no client is available."""
        formatter = TaskHierarchyFormatter()

        root_tasks = formatter.organize_by_parent_child(orphaned_tasks_no_client)

        # Should have 3 root tasks: root_1, orphan_1 (promoted), and their actual children
        root_ids = {task['id'] for task in root_tasks}
        assert 'root_1' in root_ids
        assert 'orphan_1' in root_ids  # Orphaned task promoted to root

    def test_orphaned_task_has_no_children(self, orphaned_tasks_no_client):
        """Test orphaned tasks don't incorrectly get children."""
        formatter = TaskHierarchyFormatter()

        root_tasks = formatter.organize_by_parent_child(orphaned_tasks_no_client)

        orphan = [t for t in root_tasks if t['id'] == 'orphan_1'][0]
        assert len(orphan.get('_children', [])) == 0

    def test_non_orphaned_hierarchy_preserved(self, orphaned_tasks_no_client):
        """Test non-orphaned parent-child relationships are preserved."""
        formatter = TaskHierarchyFormatter()

        root_tasks = formatter.organize_by_parent_child(orphaned_tasks_no_client)

        root = [t for t in root_tasks if t['id'] == 'root_1'][0]
        assert len(root.get('_children', [])) == 1
        assert root['_children'][0]['id'] == 'child_1'


class TestOrphanedTaskAPIFetch:
    """Test orphaned task handling with API client."""

    def test_fetches_missing_parent_successfully(self, orphaned_tasks_with_parent_data, caplog):
        """Test successful fetch of missing parent task."""
        tasks, parent_data = orphaned_tasks_with_parent_data

        # Create mock client
        mock_client = Mock()
        mock_client.get_task.return_value = parent_data

        formatter = TaskHierarchyFormatter(client=mock_client)

        with caplog.at_level(logging.INFO):
            root_tasks = formatter.organize_by_parent_child(tasks)

        # Verify API was called
        mock_client.get_task.assert_called_once_with('missing_parent')

        # Verify logging
        assert any("Fetching missing parent task: missing_parent" in record.message for record in caplog.records)
        assert any("Successfully fetched parent: Fetched Parent Task" in record.message for record in caplog.records)

        # Verify orphaned task is now a child of fetched parent
        root_ids = {task['id'] for task in root_tasks}
        assert 'missing_parent' in root_ids  # Fetched parent is now a root

        fetched_parent = [t for t in root_tasks if t['id'] == 'missing_parent'][0]
        assert len(fetched_parent.get('_children', [])) == 1
        assert fetched_parent['_children'][0]['id'] == 'orphan_1'

    def test_tracks_successfully_fetched_parent(self, orphaned_tasks_with_parent_data):
        """Test that successfully fetched parents are tracked."""
        tasks, parent_data = orphaned_tasks_with_parent_data

        mock_client = Mock()
        mock_client.get_task.return_value = parent_data

        formatter = TaskHierarchyFormatter(client=mock_client)
        formatter.organize_by_parent_child(tasks)

        # Verify tracking
        assert len(formatter.orphaned_tasks_handled) == 1
        assert formatter.orphaned_tasks_handled[0]['parent_id'] == 'missing_parent'
        assert formatter.orphaned_tasks_handled[0]['parent_name'] == 'Fetched Parent Task'
        assert formatter.orphaned_tasks_handled[0]['status'] == 'fetched'

    def test_handles_failed_fetch_gracefully(self, orphaned_tasks_no_client, caplog):
        """Test graceful handling when fetch fails."""
        mock_client = Mock()
        mock_client.get_task.side_effect = Exception("API error")

        formatter = TaskHierarchyFormatter(client=mock_client)

        with caplog.at_level(logging.WARNING):
            root_tasks = formatter.organize_by_parent_child(orphaned_tasks_no_client)

        # Should not crash, orphaned task promoted to root
        root_ids = {task['id'] for task in root_tasks}
        assert 'orphan_1' in root_ids

        # Verify warning logged
        assert any("Failed to fetch parent task" in record.message for record in caplog.records)

    def test_tracks_failed_fetch(self, orphaned_tasks_no_client):
        """Test that failed fetches are tracked."""
        mock_client = Mock()
        mock_client.get_task.side_effect = Exception("API error")

        formatter = TaskHierarchyFormatter(client=mock_client)
        formatter.organize_by_parent_child(orphaned_tasks_no_client)

        # Verify tracking
        assert len(formatter.orphaned_tasks_handled) == 1
        assert formatter.orphaned_tasks_handled[0]['parent_id'] == 'missing_parent'
        assert formatter.orphaned_tasks_handled[0]['status'] == 'fetch_failed'
        assert 'error' in formatter.orphaned_tasks_handled[0]

    def test_handles_empty_fetch_result(self, orphaned_tasks_no_client, caplog):
        """Test handling when fetch returns None or empty dict."""
        mock_client = Mock()
        mock_client.get_task.return_value = None

        formatter = TaskHierarchyFormatter(client=mock_client)

        with caplog.at_level(logging.WARNING):
            root_tasks = formatter.organize_by_parent_child(orphaned_tasks_no_client)

        # Should handle gracefully
        root_ids = {task['id'] for task in root_tasks}
        assert 'orphan_1' in root_ids

        # Verify warning logged
        assert any("fetch returned empty result" in record.message for record in caplog.records)

    def test_fetches_multiple_missing_parents(self, multiple_orphaned_tasks):
        """Test fetching multiple different missing parents."""
        mock_client = Mock()

        # Set up different return values for different parent IDs
        def get_task_side_effect(task_id):
            if task_id == 'missing_parent_1':
                return {'id': 'missing_parent_1', 'name': 'Parent 1', 'parent': None, 'status': {'status': 'to do'}}
            elif task_id == 'missing_parent_2':
                return {'id': 'missing_parent_2', 'name': 'Parent 2', 'parent': None, 'status': {'status': 'to do'}}
            return None

        mock_client.get_task.side_effect = get_task_side_effect

        formatter = TaskHierarchyFormatter(client=mock_client)
        root_tasks = formatter.organize_by_parent_child(multiple_orphaned_tasks)

        # Should fetch both missing parents (called once per unique parent)
        assert mock_client.get_task.call_count == 2

        # Both fetched parents should be in root
        root_ids = {task['id'] for task in root_tasks}
        assert 'missing_parent_1' in root_ids
        assert 'missing_parent_2' in root_ids

        # Verify children are properly assigned
        parent1 = [t for t in root_tasks if t['id'] == 'missing_parent_1'][0]
        assert len(parent1.get('_children', [])) == 2  # orphan_1 and orphan_3

        parent2 = [t for t in root_tasks if t['id'] == 'missing_parent_2'][0]
        assert len(parent2.get('_children', [])) == 1  # orphan_2


class TestOrphanedTaskWarnings:
    """Test user warning generation for orphaned tasks."""

    def test_no_warnings_when_no_orphaned_tasks(self, orphaned_tasks_with_parent_data):
        """Test no warnings when all parents are successfully fetched."""
        tasks, parent_data = orphaned_tasks_with_parent_data

        mock_client = Mock()
        mock_client.get_task.return_value = parent_data

        formatter = TaskHierarchyFormatter(client=mock_client)
        formatter.organize_by_parent_child(tasks)

        info = formatter.get_orphaned_task_info()

        # Should have info about successful fetch, not a warning
        assert info is not None
        assert "Fetched" in info
        assert "missing parent" not in info.lower() or "fetched" in info.lower()

    def test_warning_generated_for_failed_fetch(self, orphaned_tasks_no_client):
        """Test warning is generated when fetch fails."""
        mock_client = Mock()
        mock_client.get_task.side_effect = Exception("API error")

        formatter = TaskHierarchyFormatter(client=mock_client)
        formatter.organize_by_parent_child(orphaned_tasks_no_client)

        info = formatter.get_orphaned_task_info()

        assert info is not None
        assert "⚠️" in info
        assert "orphaned" in info.lower()
        assert "missing_parent" in info

    def test_info_message_for_successful_fetch(self, orphaned_tasks_with_parent_data):
        """Test info message includes fetched parent names."""
        tasks, parent_data = orphaned_tasks_with_parent_data

        mock_client = Mock()
        mock_client.get_task.return_value = parent_data

        formatter = TaskHierarchyFormatter(client=mock_client)
        formatter.organize_by_parent_child(tasks)

        info = formatter.get_orphaned_task_info()

        assert "Fetched Parent Task" in info
        assert "missing_parent" in info

    def test_no_info_when_no_orphaned_tasks(self):
        """Test no info message when there are no orphaned tasks."""
        tasks = [
            {'id': 'root_1', 'name': 'Root Task', 'parent': None, 'status': {'status': 'to do'}},
            {'id': 'child_1', 'name': 'Child Task', 'parent': 'root_1', 'status': {'status': 'to do'}}
        ]

        formatter = TaskHierarchyFormatter()
        formatter.organize_by_parent_child(tasks)

        info = formatter.get_orphaned_task_info()

        assert info is None

    def test_info_displayed_in_formatted_output(self, orphaned_tasks_with_parent_data):
        """Test that orphaned task info is included in formatted output."""
        tasks, parent_data = orphaned_tasks_with_parent_data

        mock_client = Mock()
        mock_client.get_task.return_value = parent_data

        formatter = TaskHierarchyFormatter(client=mock_client)
        output = formatter.format_hierarchy(tasks)

        # Info message should be in output
        assert "Fetched" in output or "ℹ️" in output


class TestOrphanedTaskEdgeCases:
    """Test edge cases for orphaned task handling."""

    def test_orphaned_task_with_children(self):
        """Test orphaned task that itself has children."""
        tasks = [
            {'id': 'root_1', 'name': 'Root Task', 'parent': None, 'status': {'status': 'to do'}},
            {'id': 'orphan_1', 'name': 'Orphaned Task', 'parent': 'missing_parent', 'status': {'status': 'to do'}},
            {'id': 'child_1', 'name': 'Child of Orphan', 'parent': 'orphan_1', 'status': {'status': 'to do'}}
        ]

        formatter = TaskHierarchyFormatter()
        root_tasks = formatter.organize_by_parent_child(tasks)

        # Orphaned task promoted to root but keeps its children
        orphan = [t for t in root_tasks if t['id'] == 'orphan_1'][0]
        assert len(orphan.get('_children', [])) == 1
        assert orphan['_children'][0]['id'] == 'child_1'

    def test_deeply_nested_orphaned_chain(self):
        """Test chain of orphaned tasks (A->B->C where A is missing)."""
        tasks = [
            {'id': 'orphan_1', 'name': 'Orphan Level 1', 'parent': 'missing_parent', 'status': {'status': 'to do'}},
            {'id': 'orphan_2', 'name': 'Orphan Level 2', 'parent': 'orphan_1', 'status': {'status': 'to do'}},
            {'id': 'orphan_3', 'name': 'Orphan Level 3', 'parent': 'orphan_2', 'status': {'status': 'to do'}}
        ]

        formatter = TaskHierarchyFormatter()
        root_tasks = formatter.organize_by_parent_child(tasks)

        # Only orphan_1 should be at root
        assert len(root_tasks) == 1
        assert root_tasks[0]['id'] == 'orphan_1'

        # Verify nested structure preserved
        assert root_tasks[0]['_children'][0]['id'] == 'orphan_2'
        assert root_tasks[0]['_children'][0]['_children'][0]['id'] == 'orphan_3'

    def test_fetched_parent_integrated_into_existing_hierarchy(self):
        """Test fetched parent properly integrated when it also has a parent."""
        tasks = [
            {'id': 'root_1', 'name': 'Root Task', 'parent': None, 'status': {'status': 'to do'}},
            {'id': 'orphan_1', 'name': 'Orphaned Task', 'parent': 'missing_parent', 'status': {'status': 'to do'}}
        ]

        # Fetched parent has root_1 as its parent
        parent_data = {
            'id': 'missing_parent',
            'name': 'Fetched Parent',
            'parent': 'root_1',
            'status': {'status': 'to do'}
        }

        mock_client = Mock()
        mock_client.get_task.return_value = parent_data

        formatter = TaskHierarchyFormatter(client=mock_client)
        root_tasks = formatter.organize_by_parent_child(tasks)

        # Should have only one root (root_1)
        assert len(root_tasks) == 1
        assert root_tasks[0]['id'] == 'root_1'

        # Verify hierarchy: root_1 -> missing_parent -> orphan_1
        root = root_tasks[0]
        assert len(root['_children']) == 1
        assert root['_children'][0]['id'] == 'missing_parent'
        assert len(root['_children'][0]['_children']) == 1
        assert root['_children'][0]['_children'][0]['id'] == 'orphan_1'

    def test_state_reset_between_calls(self, orphaned_tasks_no_client):
        """Test that orphaned task tracking is reset between organize calls."""
        mock_client = Mock()
        mock_client.get_task.side_effect = Exception("API error")

        formatter = TaskHierarchyFormatter(client=mock_client)

        # First call
        formatter.organize_by_parent_child(orphaned_tasks_no_client)
        assert len(formatter.orphaned_tasks_handled) == 1

        # Second call should reset
        formatter.organize_by_parent_child(orphaned_tasks_no_client)
        assert len(formatter.orphaned_tasks_handled) == 1  # Not accumulated

    def test_empty_task_list(self):
        """Test handling of empty task list."""
        formatter = TaskHierarchyFormatter()
        root_tasks = formatter.organize_by_parent_child([])

        assert len(root_tasks) == 0
        assert formatter.get_orphaned_task_info() is None

    def test_all_tasks_orphaned(self):
        """Test when all tasks have missing parents."""
        tasks = [
            {'id': 'orphan_1', 'name': 'Orphan 1', 'parent': 'missing_1', 'status': {'status': 'to do'}},
            {'id': 'orphan_2', 'name': 'Orphan 2', 'parent': 'missing_2', 'status': {'status': 'to do'}},
            {'id': 'orphan_3', 'name': 'Orphan 3', 'parent': 'missing_3', 'status': {'status': 'to do'}}
        ]

        formatter = TaskHierarchyFormatter()
        root_tasks = formatter.organize_by_parent_child(tasks)

        # All should be promoted to root
        assert len(root_tasks) == 3
        root_ids = {task['id'] for task in root_tasks}
        assert root_ids == {'orphan_1', 'orphan_2', 'orphan_3'}


class TestOrphanedTaskPerformance:
    """Test performance characteristics of orphaned task handling."""

    def test_large_hierarchy_with_some_orphaned_tasks(self):
        """Test performance with large task list including orphaned tasks."""
        import time

        # Create 100 tasks, 10 orphaned
        tasks = []
        for i in range(100):
            if i % 10 == 0:
                # Orphaned task
                task = {
                    'id': f'task_{i}',
                    'name': f'Task {i}',
                    'parent': f'missing_{i}',
                    'status': {'status': 'to do'}
                }
            else:
                # Normal task
                task = {
                    'id': f'task_{i}',
                    'name': f'Task {i}',
                    'parent': f'task_{i-1}' if i > 0 and i % 10 != 1 else None,
                    'status': {'status': 'to do'}
                }
            tasks.append(task)

        formatter = TaskHierarchyFormatter()

        start_time = time.time()
        result = formatter.organize_by_parent_child(tasks)
        elapsed_time = time.time() - start_time

        # Should complete quickly
        assert elapsed_time < 1.0, f"Performance test failed: took {elapsed_time:.2f}s"
        assert len(result) > 0
