"""
Comprehensive tests for hierarchy command with pagination and filtering.

Tests cover:
- Basic hierarchy display functionality
- Pagination support for large task sets
- Include/exclude completed tasks
- Space, folder, and list container types
- --all flag for workspace-wide views
- Error handling and edge cases
"""

import pytest
from unittest.mock import Mock, patch
import argparse
import sys
from io import StringIO

from clickup_framework.commands.hierarchy import (
    hierarchy_command,
    _fetch_all_pages,
    _get_tasks_from_lists,
    _get_tasks_from_space,
    _get_tasks_from_folder
)


class TestFetchAllPages:
    """Test pagination helper function."""

    def test_single_page(self):
        """Test fetching when all results fit in one page."""
        mock_func = Mock(return_value={
            'tasks': [{'id': '1'}, {'id': '2'}],
            'last_page': True
        })

        result = _fetch_all_pages(mock_func, include_closed=False)

        assert len(result) == 2
        assert result[0]['id'] == '1'
        mock_func.assert_called_once_with(page=0, include_closed=False)

    def test_multiple_pages(self):
        """Test fetching across multiple pages."""
        # Simulate 3 pages of results
        mock_func = Mock(side_effect=[
            {'tasks': [{'id': '1'}, {'id': '2'}], 'last_page': False},
            {'tasks': [{'id': '3'}, {'id': '4'}], 'last_page': False},
            {'tasks': [{'id': '5'}], 'last_page': True}
        ])

        result = _fetch_all_pages(mock_func, subtasks=True)

        assert len(result) == 5
        assert result[0]['id'] == '1'
        assert result[4]['id'] == '5'
        assert mock_func.call_count == 3

    def test_empty_response(self):
        """Test fetching when no results returned."""
        mock_func = Mock(return_value={'tasks': [], 'last_page': True})

        result = _fetch_all_pages(mock_func)

        assert len(result) == 0

    def test_handles_exception(self):
        """Test graceful handling of pagination errors."""
        mock_func = Mock(side_effect=[
            {'tasks': [{'id': '1'}], 'last_page': False},
            Exception("API Error")
        ])

        result = _fetch_all_pages(mock_func)

        # Should return tasks from first page before error
        assert len(result) == 1
        assert result[0]['id'] == '1'

    def test_passes_parameters(self):
        """Test that parameters are correctly passed through."""
        mock_func = Mock(return_value={'tasks': [], 'last_page': True})

        _fetch_all_pages(mock_func, subtasks=True, include_closed=True, custom_param="value")

        mock_func.assert_called_once_with(
            page=0,
            subtasks=True,
            include_closed=True,
            custom_param="value"
        )


class TestGetTasksFromLists:
    """Test fetching tasks from multiple lists."""

    @patch('clickup_framework.commands.hierarchy._fetch_all_pages')
    def test_fetch_from_multiple_lists(self, mock_fetch):
        """Test fetching tasks from multiple lists."""
        mock_client = Mock()
        lists = [
            {'id': 'list_1', 'name': 'List 1'},
            {'id': 'list_2', 'name': 'List 2'}
        ]

        mock_fetch.side_effect = [
            [{'id': 'task_1'}, {'id': 'task_2'}],
            [{'id': 'task_3'}]
        ]

        result = _get_tasks_from_lists(mock_client, lists, include_closed=False)

        assert len(result) == 3
        assert mock_fetch.call_count == 2

    @patch('clickup_framework.commands.hierarchy._fetch_all_pages')
    def test_handles_auth_error(self, mock_fetch):
        """Test handling of authentication errors."""
        from clickup_framework.exceptions import ClickUpAuthError

        mock_client = Mock()
        lists = [
            {'id': 'list_1'},
            {'id': 'list_2'}
        ]

        mock_fetch.side_effect = [
            ClickUpAuthError("Unauthorized"),
            [{'id': 'task_1'}]
        ]

        result = _get_tasks_from_lists(mock_client, lists)

        # Should continue despite error on first list
        assert len(result) == 1

    @patch('clickup_framework.commands.hierarchy._fetch_all_pages')
    def test_passes_include_closed(self, mock_fetch):
        """Test that include_closed parameter is passed correctly."""
        mock_client = Mock()
        lists = [{'id': 'list_1'}]
        mock_fetch.return_value = []

        _get_tasks_from_lists(mock_client, lists, include_closed=True)

        # Verify include_closed was passed
        call_args = mock_fetch.call_args
        assert call_args[1]['include_closed'] is True


class TestGetTasksFromSpace:
    """Test fetching tasks from a space."""

    @patch('clickup_framework.commands.hierarchy._get_tasks_from_lists')
    def test_fetch_from_space_with_folders(self, mock_get_lists):
        """Test fetching tasks from a space containing folders."""
        mock_client = Mock()
        space_data = {
            'id': 'space_1',
            'name': 'Test Space',
            'folders': [
                {
                    'id': 'folder_1',
                    'lists': [
                        {'id': 'list_1'},
                        {'id': 'list_2'}
                    ]
                }
            ],
            'lists': [{'id': 'list_3'}]  # Folderless list
        }

        mock_get_lists.side_effect = [
            [{'id': 'task_1'}, {'id': 'task_2'}],  # From folder lists
            [{'id': 'task_3'}]  # From folderless lists
        ]

        result = _get_tasks_from_space(mock_client, space_data, include_closed=False)

        assert len(result) == 3
        assert mock_get_lists.call_count == 2

    @patch('clickup_framework.commands.hierarchy._get_tasks_from_lists')
    def test_fetch_from_space_no_folders(self, mock_get_lists):
        """Test fetching from space with only folderless lists."""
        mock_client = Mock()
        space_data = {
            'folders': [],
            'lists': [{'id': 'list_1'}]
        }

        mock_get_lists.return_value = [{'id': 'task_1'}]

        result = _get_tasks_from_space(mock_client, space_data)

        assert len(result) == 1
        mock_get_lists.assert_called_once()


class TestGetTasksFromFolder:
    """Test fetching tasks from a folder."""

    @patch('clickup_framework.commands.hierarchy._get_tasks_from_lists')
    def test_fetch_from_folder(self, mock_get_lists):
        """Test fetching tasks from a folder."""
        mock_client = Mock()
        folder_data = {
            'id': 'folder_1',
            'lists': [
                {'id': 'list_1'},
                {'id': 'list_2'}
            ]
        }

        mock_get_lists.return_value = [{'id': 'task_1'}, {'id': 'task_2'}]

        result = _get_tasks_from_folder(mock_client, folder_data, include_closed=True)

        assert len(result) == 2
        mock_get_lists.assert_called_once_with(mock_client, folder_data['lists'], True)


class TestHierarchyCommand:
    """Test the main hierarchy command function."""

    @patch('clickup_framework.commands.hierarchy.get_list_statuses')
    @patch('clickup_framework.commands.hierarchy.DisplayManager')
    @patch('clickup_framework.commands.hierarchy.ClickUpClient')
    @patch('clickup_framework.commands.hierarchy.get_context_manager')
    @patch('clickup_framework.commands.hierarchy._fetch_all_pages')
    def test_workspace_all_with_pagination(
        self, mock_fetch_pages, mock_context, mock_client, mock_display, mock_statuses
    ):
        """Test --all flag fetches all pages from workspace."""
        # Setup mocks
        mock_context_inst = Mock()
        mock_context_inst.resolve_id.return_value = 'team_123'
        mock_context_inst.get_ansi_output.return_value = True
        mock_context.return_value = mock_context_inst

        mock_client_inst = Mock()
        mock_client.return_value = mock_client_inst

        mock_display_inst = Mock()
        mock_display_inst.hierarchy_view.return_value = "Task output"
        mock_display.return_value = mock_display_inst

        mock_statuses.return_value = ""

        # Simulate pagination returning 150 tasks total
        mock_fetch_pages.return_value = [{'id': f'task_{i}'} for i in range(150)]

        # Create args
        args = argparse.Namespace(
            list_id=None,
            show_all=True,
            include_completed=False,
            header=None,
            colorize=None,
            show_ids=False,
            show_tags=True,
            show_descriptions=False,
            show_dates=False,
            show_comments=0,
            show_emoji=True,
            full_descriptions=False,
            preset='full'
        )

        # Capture output
        captured_output = StringIO()
        sys.stdout = captured_output

        hierarchy_command(args)

        sys.stdout = sys.__stdout__

        # Verify fetch_all_pages was called
        mock_fetch_pages.assert_called_once()
        call_kwargs = mock_fetch_pages.call_args[1]
        assert call_kwargs['subtasks'] is True
        assert call_kwargs['include_closed'] is False

        # Verify display was called with all tasks
        display_call = mock_display_inst.hierarchy_view.call_args
        tasks_arg = display_call[0][0]
        assert len(tasks_arg) == 150

    @patch('clickup_framework.commands.hierarchy.get_list_statuses')
    @patch('clickup_framework.commands.hierarchy.DisplayManager')
    @patch('clickup_framework.commands.hierarchy.ClickUpClient')
    @patch('clickup_framework.commands.hierarchy.get_context_manager')
    @patch('clickup_framework.commands.hierarchy._fetch_all_pages')
    def test_workspace_all_with_include_completed(
        self, mock_fetch_pages, mock_context, mock_client, mock_display, mock_statuses
    ):
        """Test --all flag respects --include-completed."""
        # Setup mocks
        mock_context_inst = Mock()
        mock_context_inst.resolve_id.return_value = 'team_123'
        mock_context_inst.get_ansi_output.return_value = True
        mock_context.return_value = mock_context_inst

        mock_client_inst = Mock()
        mock_client.return_value = mock_client_inst

        mock_display_inst = Mock()
        mock_display_inst.hierarchy_view.return_value = "Task output"
        mock_display.return_value = mock_display_inst

        mock_statuses.return_value = ""
        mock_fetch_pages.return_value = []

        # Create args with include_completed=True
        args = argparse.Namespace(
            list_id=None,
            show_all=True,
            include_completed=True,  # Key flag
            header=None,
            colorize=None,
            show_ids=False,
            show_tags=True,
            show_descriptions=False,
            show_dates=False,
            show_comments=0,
            show_emoji=True,
            full_descriptions=False,
            preset='full'
        )

        captured_output = StringIO()
        sys.stdout = captured_output

        hierarchy_command(args)

        sys.stdout = sys.__stdout__

        # Verify include_closed=True was passed
        call_kwargs = mock_fetch_pages.call_args[1]
        assert call_kwargs['include_closed'] is True

    @patch('clickup_framework.commands.hierarchy.get_list_statuses')
    @patch('clickup_framework.commands.hierarchy.DisplayManager')
    @patch('clickup_framework.commands.hierarchy.ClickUpClient')
    @patch('clickup_framework.commands.hierarchy.get_context_manager')
    @patch('clickup_framework.commands.hierarchy.resolve_container_id')
    @patch('clickup_framework.commands.hierarchy._fetch_all_pages')
    def test_single_list_with_pagination(
        self, mock_fetch_pages, mock_resolve, mock_context,
        mock_client, mock_display, mock_statuses
    ):
        """Test fetching from a single list with pagination."""
        # Setup mocks
        mock_context_inst = Mock()
        mock_context_inst.get_ansi_output.return_value = True
        mock_context.return_value = mock_context_inst

        mock_client_inst = Mock()
        mock_client_inst.get_list.return_value = {'id': 'list_123', 'statuses': []}
        mock_client.return_value = mock_client_inst

        mock_resolve.return_value = {'type': 'list', 'id': 'list_123'}

        mock_display_inst = Mock()
        mock_display_inst.hierarchy_view.return_value = "Task output"
        mock_display.return_value = mock_display_inst

        mock_statuses.return_value = ""
        mock_fetch_pages.return_value = [{'id': f'task_{i}'} for i in range(200)]

        # Create args
        args = argparse.Namespace(
            list_id='list_123',
            show_all=False,
            include_completed=False,
            header=None,
            colorize=None,
            show_ids=False,
            show_tags=True,
            show_descriptions=False,
            show_dates=False,
            show_comments=0,
            show_emoji=True,
            full_descriptions=False,
            preset='full'
        )

        captured_output = StringIO()
        sys.stdout = captured_output

        hierarchy_command(args)

        sys.stdout = sys.__stdout__

        # Verify pagination was used
        assert mock_fetch_pages.called
        display_call = mock_display_inst.hierarchy_view.call_args
        tasks_arg = display_call[0][0]
        assert len(tasks_arg) == 200

    @patch('clickup_framework.commands.hierarchy.get_list_statuses')
    @patch('clickup_framework.commands.hierarchy.DisplayManager')
    @patch('clickup_framework.commands.hierarchy.ClickUpClient')
    @patch('clickup_framework.commands.hierarchy.get_context_manager')
    @patch('clickup_framework.commands.hierarchy.resolve_container_id')
    @patch('clickup_framework.commands.hierarchy._get_tasks_from_space')
    def test_space_container(
        self, mock_get_space_tasks, mock_resolve, mock_context,
        mock_client, mock_display, mock_statuses
    ):
        """Test fetching from a space container."""
        # Setup mocks
        mock_context_inst = Mock()
        mock_context_inst.get_ansi_output.return_value = True
        mock_context.return_value = mock_context_inst

        mock_client_inst = Mock()
        mock_client.return_value = mock_client_inst

        space_data = {
            'id': 'space_123',
            'name': 'Test Space',
            'folders': [],
            'lists': []
        }
        mock_resolve.return_value = {'type': 'space', 'id': 'space_123', 'data': space_data}

        mock_display_inst = Mock()
        mock_display_inst.hierarchy_view.return_value = "Task output"
        mock_display.return_value = mock_display_inst

        mock_statuses.return_value = ""
        mock_get_space_tasks.return_value = [{'id': 'task_1'}]

        # Create args
        args = argparse.Namespace(
            list_id='space_123',
            show_all=False,
            include_completed=True,
            header=None,
            colorize=None,
            show_ids=False,
            show_tags=True,
            show_descriptions=False,
            show_dates=False,
            show_comments=0,
            show_emoji=True,
            full_descriptions=False,
            preset='full'
        )

        captured_output = StringIO()
        sys.stdout = captured_output

        hierarchy_command(args)

        sys.stdout = sys.__stdout__

        # Verify space tasks were fetched with include_closed
        mock_get_space_tasks.assert_called_once_with(mock_client_inst, space_data, True)

    @patch('clickup_framework.commands.hierarchy.get_context_manager')
    def test_error_no_list_id_no_all(self, mock_context):
        """Test error when neither list_id nor --all provided."""
        args = argparse.Namespace(list_id=None, show_all=False)

        with pytest.raises(SystemExit) as exc_info:
            hierarchy_command(args)

        assert exc_info.value.code == 1

    @patch('clickup_framework.commands.hierarchy.get_context_manager')
    def test_error_both_list_id_and_all(self, mock_context):
        """Test error when both list_id and --all provided."""
        args = argparse.Namespace(list_id='list_123', show_all=True)

        with pytest.raises(SystemExit) as exc_info:
            hierarchy_command(args)

        assert exc_info.value.code == 1

    @patch('clickup_framework.commands.hierarchy.get_context_manager')
    def test_error_no_workspace_set(self, mock_context):
        """Test error when using --all without workspace set."""
        mock_context_inst = Mock()
        mock_context_inst.resolve_id.side_effect = ValueError("No workspace")
        mock_context.return_value = mock_context_inst

        args = argparse.Namespace(
            list_id=None,
            show_all=True,
            include_completed=False
        )

        with pytest.raises(SystemExit) as exc_info:
            hierarchy_command(args)

        assert exc_info.value.code == 1


class TestIntegration:
    """Integration tests for full command flow."""

    @patch('clickup_framework.commands.hierarchy.get_list_statuses')
    @patch('clickup_framework.commands.hierarchy.DisplayManager')
    @patch('clickup_framework.commands.hierarchy.ClickUpClient')
    @patch('clickup_framework.commands.hierarchy.get_context_manager')
    def test_full_workspace_pagination_flow(
        self, mock_context, mock_client, mock_display, mock_statuses
    ):
        """Test complete flow with realistic pagination scenario."""
        # Setup mocks
        mock_context_inst = Mock()
        mock_context_inst.resolve_id.return_value = 'team_123'
        mock_context_inst.get_ansi_output.return_value = True
        mock_context.return_value = mock_context_inst

        # Mock client to return paginated results
        mock_client_inst = Mock()

        # Simulate 3 pages: 100 + 100 + 50 = 250 tasks
        # Note: The lambda in hierarchy_command passes page and other kwargs, but not self
        page_results = [
            {
                'tasks': [{'id': f'task_{i}', 'name': f'Task {i}'} for i in range(100)],
                'last_page': False
            },
            {
                'tasks': [{'id': f'task_{i}', 'name': f'Task {i}'} for i in range(100, 200)],
                'last_page': False
            },
            {
                'tasks': [{'id': f'task_{i}', 'name': f'Task {i}'} for i in range(200, 250)],
                'last_page': True
            }
        ]


        def mock_get_team_tasks(*args, **kwargs):
            page = kwargs.get('page', 0)
            if page < len(page_results):
                return page_results[page]
            return {'tasks': [], 'last_page': True}

        mock_client_inst.get_team_tasks = Mock(side_effect=mock_get_team_tasks)
        mock_client.return_value = mock_client_inst

        mock_display_inst = Mock()
        mock_display_inst.hierarchy_view.return_value = "Task output"
        mock_display.return_value = mock_display_inst

        mock_statuses.return_value = ""

        # Create args
        args = argparse.Namespace(
            list_id=None,
            show_all=True,
            include_completed=False,
            header=None,
            colorize=None,
            show_ids=False,
            show_tags=True,
            show_descriptions=False,
            show_dates=False,
            show_comments=0,
            show_emoji=True,
            full_descriptions=False,
            preset='full'
        )

        captured_output = StringIO()
        sys.stdout = captured_output

        hierarchy_command(args)

        sys.stdout = sys.__stdout__

        # Verify all pages were fetched
        assert mock_client_inst.get_team_tasks.call_count == 3

        # Verify all 250 tasks were passed to display
        display_call = mock_display_inst.hierarchy_view.call_args
        tasks_arg = display_call[0][0]
        assert len(tasks_arg) == 250
        assert tasks_arg[0]['id'] == 'task_0'
        assert tasks_arg[249]['id'] == 'task_249'
