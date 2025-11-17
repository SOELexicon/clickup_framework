"""
Comprehensive CLI Coverage Tests

Tests for all CLI commands using fixtures from conftest.py.
Ensures complete coverage of the CLI module including all commands,
options, presets, and error handling.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import io
import argparse
from pathlib import Path

from clickup_framework.cli import (
    create_format_options,
    hierarchy_command,
    container_command,
    flat_command,
    filter_command,
    detail_command,
    stats_command,
    demo_command,
    set_current_command,
    clear_current_command,
    show_current_command,
    assigned_tasks_command,
    main
)
from clickup_framework.components import FormatOptions


# Helper function to mock get_list_statuses
def mock_get_list_statuses_empty(*args, **kwargs):
    """Mock get_list_statuses to return empty string."""
    return ""


class TestContainerCommand(unittest.TestCase):
    """Test container_command function with comprehensive coverage."""

    @patch('clickup_framework.commands.container.get_list_statuses', side_effect=mock_get_list_statuses_empty)
    @patch('clickup_framework.commands.container.ClickUpClient')
    @patch('clickup_framework.commands.container.get_context_manager')
    @patch('clickup_framework.commands.container.DisplayManager')
    def test_container_command_success(self, mock_display_mgr, mock_context, mock_client, mock_statuses):
        """Test container command with valid input."""
        # Setup mocks
        mock_context_inst = Mock()
        mock_context_inst.resolve_id.return_value = 'list_123'
        mock_context.return_value = mock_context_inst

        mock_client_inst = Mock()
        mock_client_inst.get_list.return_value = {'id': 'list_123', 'name': 'Test List'}
        mock_client_inst.get_list_tasks.return_value = {'tasks': []}
        mock_client.return_value = mock_client_inst

        mock_display_inst = Mock()
        mock_display_inst.container_view.return_value = "Container View"
        mock_display_mgr.return_value = mock_display_inst

        args = argparse.Namespace(
            list_id='list_123',
            preset=None,
            colorize=True,
            show_ids=False,
            show_tags=True,
            show_descriptions=False,
            show_dates=False,
            show_comments=0,
            include_completed=False,
            show_emoji=True
        )

        # Capture stdout
        captured_output = io.StringIO()
        sys.stdout = captured_output

        container_command(args)

        sys.stdout = sys.__stdout__

        # Verify
        mock_client_inst.get_list_tasks.assert_called_once()
        mock_display_inst.container_view.assert_called_once()
        self.assertIn("Container View", captured_output.getvalue())

    @patch('clickup_framework.commands.container.get_context_manager')
    def test_container_command_invalid_list(self, mock_context):
        """Test container command with invalid list ID."""
        mock_context_inst = Mock()
        mock_context_inst.resolve_id.side_effect = ValueError("Invalid list ID")
        mock_context.return_value = mock_context_inst

        args = argparse.Namespace(list_id='invalid')

        with self.assertRaises(SystemExit) as cm:
            container_command(args)

        self.assertEqual(cm.exception.code, 1)

    @patch('clickup_framework.commands.container.ClickUpClient')
    @patch('clickup_framework.commands.container.get_context_manager')
    @patch('clickup_framework.commands.container.DisplayManager')
    def test_container_command_with_preset(self, mock_display_mgr, mock_context, mock_client):
        """Test container command with preset option."""
        mock_context_inst = Mock()
        mock_context_inst.resolve_id.return_value = 'list_123'
        mock_context.return_value = mock_context_inst

        mock_client_inst = Mock()
        mock_client_inst.get_list_tasks.return_value = {'tasks': []}
        mock_client.return_value = mock_client_inst

        mock_display_inst = Mock()
        mock_display_inst.container_view.return_value = "Container View"
        mock_display_mgr.return_value = mock_display_inst

        args = argparse.Namespace(
            list_id='list_123',
            preset='detailed'
        )

        captured_output = io.StringIO()
        sys.stdout = captured_output

        container_command(args)

        sys.stdout = sys.__stdout__

        # Verify preset was used
        mock_display_inst.container_view.assert_called_once()
        call_args = mock_display_inst.container_view.call_args
        options = call_args[0][1]
        self.assertIsInstance(options, FormatOptions)


class TestFlatCommand(unittest.TestCase):
    """Test flat_command function with comprehensive coverage."""

    @patch('clickup_framework.commands.flat.ClickUpClient')
    @patch('clickup_framework.commands.flat.get_context_manager')
    @patch('clickup_framework.commands.flat.DisplayManager')
    def test_flat_command_success(self, mock_display_mgr, mock_context, mock_client):
        """Test flat command with valid input."""
        mock_context_inst = Mock()
        mock_context_inst.resolve_id.return_value = 'list_123'
        mock_context.return_value = mock_context_inst

        mock_client_inst = Mock()
        mock_client_inst.get_list_tasks.return_value = {'tasks': []}
        mock_client.return_value = mock_client_inst

        mock_display_inst = Mock()
        mock_display_inst.flat_view.return_value = "Flat View"
        mock_display_mgr.return_value = mock_display_inst

        args = argparse.Namespace(
            list_id='list_123',
            header='My Tasks',
            preset=None,
            colorize=True,
            show_ids=False,
            show_tags=True,
            show_descriptions=False,
            show_dates=False,
            show_comments=0,
            include_completed=False,
            show_emoji=True
        )

        captured_output = io.StringIO()
        sys.stdout = captured_output

        flat_command(args)

        sys.stdout = sys.__stdout__

        mock_display_inst.flat_view.assert_called_once()
        self.assertIn("Flat View", captured_output.getvalue())

    @patch('clickup_framework.commands.flat.ClickUpClient')
    @patch('clickup_framework.commands.flat.get_context_manager')
    @patch('clickup_framework.commands.flat.DisplayManager')
    def test_flat_command_no_header(self, mock_display_mgr, mock_context, mock_client):
        """Test flat command without header."""
        mock_context_inst = Mock()
        mock_context_inst.resolve_id.return_value = 'list_123'
        mock_context.return_value = mock_context_inst

        mock_client_inst = Mock()
        mock_client_inst.get_list_tasks.return_value = {'tasks': []}
        mock_client.return_value = mock_client_inst

        mock_display_inst = Mock()
        mock_display_inst.flat_view.return_value = "Flat View"
        mock_display_mgr.return_value = mock_display_inst

        args = argparse.Namespace(
            list_id='list_123',
            preset=None,
            colorize=True,
            show_ids=False,
            show_tags=True,
            show_descriptions=False,
            show_dates=False,
            show_comments=0,
            include_completed=False,
            show_emoji=True
        )

        captured_output = io.StringIO()
        sys.stdout = captured_output

        flat_command(args)

        sys.stdout = sys.__stdout__

        # Verify flat_view was called with None as header
        call_args = mock_display_inst.flat_view.call_args
        self.assertIsNone(call_args[0][2])


class TestDetailCommand(unittest.TestCase):
    """Test detail_command function with comprehensive coverage."""

    @patch('clickup_framework.commands.detail.ClickUpClient')
    @patch('clickup_framework.commands.detail.get_context_manager')
    @patch('clickup_framework.commands.detail.DisplayManager')
    def test_detail_command_with_list(self, mock_display_mgr, mock_context, mock_client):
        """Test detail command with list ID provided."""
        mock_context_inst = Mock()
        mock_context_inst.resolve_id.side_effect = lambda res_type, res_id: res_id
        mock_context.return_value = mock_context_inst

        mock_client_inst = Mock()
        mock_client_inst.get_task.return_value = {'id': 'task_123', 'name': 'Test Task'}
        mock_client_inst.get_list_tasks.return_value = {'tasks': []}
        mock_client.return_value = mock_client_inst

        mock_display_inst = Mock()
        mock_display_inst.detail_view.return_value = "Detail View"
        mock_display_mgr.return_value = mock_display_inst

        args = argparse.Namespace(
            task_id='task_123',
            list_id='list_123',
            preset=None,
            colorize=True,
            show_ids=False,
            show_tags=True,
            show_descriptions=False,
            show_dates=False,
            show_comments=0,
            include_completed=False,
            show_emoji=True
        )

        captured_output = io.StringIO()
        sys.stdout = captured_output

        detail_command(args)

        sys.stdout = sys.__stdout__

        mock_client_inst.get_task.assert_called_once_with('task_123', include_subtasks=True)
        # get_list_tasks is called twice: once for root tasks, once for subtasks
        self.assertEqual(mock_client_inst.get_list_tasks.call_count, 2)
        self.assertIn("Detail View", captured_output.getvalue())

    @patch('clickup_framework.commands.detail.ClickUpClient')
    @patch('clickup_framework.commands.detail.get_context_manager')
    @patch('clickup_framework.commands.detail.DisplayManager')
    def test_detail_command_without_list(self, mock_display_mgr, mock_context, mock_client):
        """Test detail command without list ID."""
        mock_context_inst = Mock()
        mock_context_inst.resolve_id.return_value = 'task_123'
        mock_context.return_value = mock_context_inst

        mock_client_inst = Mock()
        mock_client_inst.get_task.return_value = {'id': 'task_123', 'name': 'Test Task'}
        mock_client.return_value = mock_client_inst

        mock_display_inst = Mock()
        mock_display_inst.detail_view.return_value = "Detail View"
        mock_display_mgr.return_value = mock_display_inst

        args = argparse.Namespace(
            task_id='task_123',
            list_id=None,
            preset=None,
            colorize=True,
            show_ids=False,
            show_tags=True,
            show_descriptions=False,
            show_dates=False,
            show_comments=0,
            include_completed=False,
            show_emoji=True
        )

        captured_output = io.StringIO()
        sys.stdout = captured_output

        detail_command(args)

        sys.stdout = sys.__stdout__

        mock_client_inst.get_task.assert_called_once()
        # Verify detail_view was called with None for all_tasks
        call_args = mock_display_inst.detail_view.call_args
        self.assertIsNone(call_args[0][1])

    @patch('clickup_framework.commands.detail.get_context_manager')
    def test_detail_command_invalid_task(self, mock_context):
        """Test detail command with invalid task ID."""
        mock_context_inst = Mock()
        mock_context_inst.resolve_id.side_effect = ValueError("Invalid task ID")
        mock_context.return_value = mock_context_inst

        args = argparse.Namespace(task_id='invalid', list_id=None)

        with self.assertRaises(SystemExit) as cm:
            detail_command(args)

        self.assertEqual(cm.exception.code, 1)


class TestFilterCommandExtended(unittest.TestCase):
    """Extended tests for filter_command function."""

    @patch('clickup_framework.commands.filter.ClickUpClient')
    @patch('clickup_framework.commands.filter.get_context_manager')
    @patch('clickup_framework.commands.filter.DisplayManager')
    def test_filter_by_priority(self, mock_display_mgr, mock_context, mock_client):
        """Test filter command with priority filter."""
        mock_context_inst = Mock()
        mock_context_inst.resolve_id.return_value = 'list_123'
        mock_context.return_value = mock_context_inst

        mock_client_inst = Mock()
        mock_client_inst.get_list_tasks.return_value = {'tasks': []}
        mock_client.return_value = mock_client_inst

        mock_display_inst = Mock()
        mock_display_inst.filtered_view.return_value = "Filtered Tasks"
        mock_display_mgr.return_value = mock_display_inst

        args = argparse.Namespace(
            list_id='list_123',
            status=None,
            priority=1,
            tags=None,
            assignee=None,
            include_completed=False,
            view_mode='hierarchy',
            preset=None,
            colorize=True,
            show_ids=False,
            show_tags=True,
            show_descriptions=False,
            show_dates=False,
            show_comments=0,
            show_emoji=True
        )

        captured_output = io.StringIO()
        sys.stdout = captured_output

        filter_command(args)

        sys.stdout = sys.__stdout__

        call_args = mock_display_inst.filtered_view.call_args
        self.assertEqual(call_args[1]['priority'], 1)

    @patch('clickup_framework.commands.filter.ClickUpClient')
    @patch('clickup_framework.commands.filter.get_context_manager')
    @patch('clickup_framework.commands.filter.DisplayManager')
    def test_filter_by_tags(self, mock_display_mgr, mock_context, mock_client):
        """Test filter command with tags filter."""
        mock_context_inst = Mock()
        mock_context_inst.resolve_id.return_value = 'list_123'
        mock_context.return_value = mock_context_inst

        mock_client_inst = Mock()
        mock_client_inst.get_list_tasks.return_value = {'tasks': []}
        mock_client.return_value = mock_client_inst

        mock_display_inst = Mock()
        mock_display_inst.filtered_view.return_value = "Filtered Tasks"
        mock_display_mgr.return_value = mock_display_inst

        args = argparse.Namespace(
            list_id='list_123',
            status=None,
            priority=None,
            tags=['bug', 'critical'],
            assignee=None,
            include_completed=False,
            view_mode='flat',
            preset=None,
            colorize=True,
            show_ids=False,
            show_tags=True,
            show_descriptions=False,
            show_dates=False,
            show_comments=0,
            show_emoji=True
        )

        captured_output = io.StringIO()
        sys.stdout = captured_output

        filter_command(args)

        sys.stdout = sys.__stdout__

        call_args = mock_display_inst.filtered_view.call_args
        self.assertEqual(call_args[1]['tags'], ['bug', 'critical'])
        self.assertEqual(call_args[1]['view_mode'], 'flat')

    @patch('clickup_framework.commands.filter.ClickUpClient')
    @patch('clickup_framework.commands.filter.get_context_manager')
    @patch('clickup_framework.commands.filter.DisplayManager')
    def test_filter_by_assignee(self, mock_display_mgr, mock_context, mock_client):
        """Test filter command with assignee filter."""
        mock_context_inst = Mock()
        mock_context_inst.resolve_id.return_value = 'list_123'
        mock_context.return_value = mock_context_inst

        mock_client_inst = Mock()
        mock_client_inst.get_list_tasks.return_value = {'tasks': []}
        mock_client.return_value = mock_client_inst

        mock_display_inst = Mock()
        mock_display_inst.filtered_view.return_value = "Filtered Tasks"
        mock_display_mgr.return_value = mock_display_inst

        args = argparse.Namespace(
            list_id='list_123',
            status=None,
            priority=None,
            tags=None,
            assignee='user_123',
            include_completed=True,
            view_mode='container',
            preset=None,
            colorize=True,
            show_ids=False,
            show_tags=True,
            show_descriptions=False,
            show_dates=False,
            show_comments=0,
            show_emoji=True
        )

        captured_output = io.StringIO()
        sys.stdout = captured_output

        filter_command(args)

        sys.stdout = sys.__stdout__

        call_args = mock_display_inst.filtered_view.call_args
        self.assertEqual(call_args[1]['assignee_id'], 'user_123')
        self.assertTrue(call_args[1]['include_completed'])
        self.assertEqual(call_args[1]['view_mode'], 'container')


class TestDemoCommandExtended(unittest.TestCase):
    """Extended tests for demo_command function."""

    def test_demo_container_mode(self):
        """Test demo command in container mode."""
        args = argparse.Namespace(
            mode='container',
            preset=None,
            colorize=True,
            show_ids=False,
            show_tags=True,
            show_descriptions=False,
            show_dates=False,
            show_comments=0,
            include_completed=False,
            show_emoji=True
        )

        captured_output = io.StringIO()
        sys.stdout = captured_output

        demo_command(args)

        sys.stdout = sys.__stdout__

        output = captured_output.getvalue()
        self.assertTrue(len(output) > 0)

    def test_demo_flat_mode(self):
        """Test demo command in flat mode."""
        args = argparse.Namespace(
            mode='flat',
            preset=None,
            colorize=True,
            show_ids=False,
            show_tags=True,
            show_descriptions=False,
            show_dates=False,
            show_comments=0,
            include_completed=False,
            show_emoji=True
        )

        captured_output = io.StringIO()
        sys.stdout = captured_output

        demo_command(args)

        sys.stdout = sys.__stdout__

        output = captured_output.getvalue()
        self.assertTrue(len(output) > 0)

    def test_demo_detail_mode(self):
        """Test demo command in detail mode."""
        args = argparse.Namespace(
            mode='detail',
            preset=None,
            colorize=True,
            show_ids=False,
            show_tags=True,
            show_descriptions=False,
            show_dates=False,
            show_comments=0,
            include_completed=False,
            show_emoji=True
        )

        captured_output = io.StringIO()
        sys.stdout = captured_output

        demo_command(args)

        sys.stdout = sys.__stdout__

        output = captured_output.getvalue()
        self.assertTrue(len(output) > 0)

    def test_demo_with_minimal_preset(self):
        """Test demo command with minimal preset."""
        args = argparse.Namespace(
            mode='hierarchy',
            preset='minimal'
        )

        captured_output = io.StringIO()
        sys.stdout = captured_output

        demo_command(args)

        sys.stdout = sys.__stdout__

        output = captured_output.getvalue()
        self.assertTrue(len(output) > 0)

    def test_demo_with_full_preset(self):
        """Test demo command with full preset."""
        args = argparse.Namespace(
            mode='hierarchy',
            preset='full'
        )

        captured_output = io.StringIO()
        sys.stdout = captured_output

        demo_command(args)

        sys.stdout = sys.__stdout__

        output = captured_output.getvalue()
        self.assertTrue(len(output) > 0)


class TestContextCommandsExtended(unittest.TestCase):
    """Extended tests for context management commands."""

    @patch('clickup_framework.commands.set_current.get_context_manager')
    def test_set_current_space(self, mock_context):
        """Test set_current command for space."""
        mock_context_inst = Mock()
        mock_context_inst._save = Mock()  # Mock _save to prevent JSON serialization
        mock_context.return_value = mock_context_inst

        args = argparse.Namespace(
            resource_type='space',
            resource_id='space_789'
        )

        captured_output = io.StringIO()
        sys.stdout = captured_output

        set_current_command(args)

        sys.stdout = sys.__stdout__

        mock_context_inst.set_current_space.assert_called_once_with('space_789')
        self.assertIn("Set current space", captured_output.getvalue())

    @patch('clickup_framework.commands.set_current.get_context_manager')
    def test_set_current_folder(self, mock_context):
        """Test set_current command for folder."""
        mock_context_inst = Mock()
        mock_context_inst._save = Mock()  # Mock _save to prevent JSON serialization
        mock_context.return_value = mock_context_inst

        args = argparse.Namespace(
            resource_type='folder',
            resource_id='folder_999'
        )

        captured_output = io.StringIO()
        sys.stdout = captured_output

        set_current_command(args)

        sys.stdout = sys.__stdout__

        mock_context_inst.set_current_folder.assert_called_once_with('folder_999')
        self.assertIn("Set current folder", captured_output.getvalue())

    @patch('clickup_framework.commands.set_current.get_context_manager')
    def test_set_current_workspace(self, mock_context):
        """Test set_current command for workspace."""
        mock_context_inst = Mock()
        mock_context_inst._save = Mock()  # Mock _save to prevent JSON serialization
        mock_context.return_value = mock_context_inst

        args = argparse.Namespace(
            resource_type='workspace',
            resource_id='workspace_111'
        )

        captured_output = io.StringIO()
        sys.stdout = captured_output

        set_current_command(args)

        sys.stdout = sys.__stdout__

        mock_context_inst.set_current_workspace.assert_called_once_with('workspace_111')
        self.assertIn("Set current workspace", captured_output.getvalue())

    @patch('clickup_framework.commands.set_current.get_context_manager')
    def test_set_current_team_alias(self, mock_context):
        """Test set_current command with 'team' alias for workspace."""
        mock_context_inst = Mock()
        mock_context_inst._save = Mock()  # Mock _save to prevent JSON serialization
        mock_context.return_value = mock_context_inst

        args = argparse.Namespace(
            resource_type='team',
            resource_id='team_222'
        )

        captured_output = io.StringIO()
        sys.stdout = captured_output

        set_current_command(args)

        sys.stdout = sys.__stdout__

        mock_context_inst.set_current_workspace.assert_called_once_with('team_222')

    @patch('clickup_framework.commands.clear_current.get_context_manager')
    def test_clear_current_list(self, mock_context):
        """Test clear_current command for list."""
        mock_context_inst = Mock()
        mock_context_inst._save = Mock()  # Mock _save to prevent JSON serialization
        mock_context.return_value = mock_context_inst

        args = argparse.Namespace(resource_type='list')

        captured_output = io.StringIO()
        sys.stdout = captured_output

        clear_current_command(args)

        sys.stdout = sys.__stdout__

        mock_context_inst.clear_current_list.assert_called_once()
        self.assertIn("Cleared current list", captured_output.getvalue())

    @patch('clickup_framework.commands.clear_current.get_context_manager')
    def test_clear_current_invalid_type(self, mock_context):
        """Test clear_current command with invalid resource type."""
        mock_context.return_value = Mock()

        args = argparse.Namespace(resource_type='invalid_type')

        with self.assertRaises(SystemExit) as cm:
            clear_current_command(args)

        self.assertEqual(cm.exception.code, 1)


class TestFormatOptionsExtended(unittest.TestCase):
    """Extended tests for create_format_options function."""

    def test_all_options_enabled(self):
        """Test format options with all flags enabled."""
        args = argparse.Namespace(
            preset=None,
            colorize=True,
            show_ids=True,
            show_tags=True,
            show_descriptions=True,
            show_dates=True,
            show_comments=5,
            include_completed=True,
            show_emoji=True
        )
        options = create_format_options(args)

        self.assertTrue(options.colorize_output)
        self.assertTrue(options.show_ids)
        self.assertTrue(options.show_tags)
        self.assertTrue(options.show_descriptions)
        self.assertTrue(options.show_dates)
        self.assertEqual(options.show_comments, 5)
        self.assertTrue(options.include_completed)
        self.assertTrue(options.show_type_emoji)

    def test_all_options_disabled(self):
        """Test format options with all flags disabled."""
        args = argparse.Namespace(
            preset=None,
            colorize=False,
            show_ids=False,
            show_tags=False,
            show_descriptions=False,
            show_dates=False,
            show_comments=0,
            include_completed=False,
            show_emoji=False
        )
        options = create_format_options(args)

        self.assertFalse(options.colorize_output)
        self.assertFalse(options.show_ids)
        self.assertFalse(options.show_tags)
        self.assertFalse(options.show_descriptions)
        self.assertFalse(options.show_dates)
        self.assertEqual(options.show_comments, 0)
        self.assertFalse(options.include_completed)
        self.assertFalse(options.show_type_emoji)

    def test_preset_takes_precedence(self):
        """Test that preset takes precedence over individual flags."""
        args = argparse.Namespace(
            preset='minimal',
            colorize=True,
            show_ids=False,
            show_tags=True,
            show_descriptions=True,
            show_dates=True,
            show_comments=5,
            include_completed=True,
            show_emoji=True
        )
        options = create_format_options(args)

        # Minimal preset should override the individual flags
        self.assertTrue(options.show_ids)  # Minimal shows IDs
        self.assertFalse(options.show_tags)  # Minimal hides tags


class TestMainCLIExtended(unittest.TestCase):
    """Extended tests for main CLI entry point."""

    @patch('sys.argv', ['cli.py', 'demo', '--mode', 'container'])
    @patch('clickup_framework.commands.demo.DisplayManager')
    def test_main_demo_container(self, mock_display_mgr):
        """Test main CLI with demo container command."""
        mock_display_inst = Mock()
        mock_display_inst.container_view.return_value = "Container Demo"
        mock_display_mgr.return_value = mock_display_inst

        captured_output = io.StringIO()
        sys.stdout = captured_output

        main()

        sys.stdout = sys.__stdout__

        output = captured_output.getvalue()
        self.assertTrue(len(output) > 0)

    @patch('sys.argv', ['cli.py', 'demo', '--mode', 'stats'])
    @patch('clickup_framework.commands.demo.DisplayManager')
    def test_main_demo_stats(self, mock_display_mgr):
        """Test main CLI with demo stats command."""
        mock_display_inst = Mock()
        mock_display_inst.summary_stats.return_value = "Stats Demo"
        mock_display_mgr.return_value = mock_display_inst

        captured_output = io.StringIO()
        sys.stdout = captured_output

        main()

        sys.stdout = sys.__stdout__

        output = captured_output.getvalue()
        self.assertTrue(len(output) > 0)

    @patch('sys.argv', ['cli.py', 'set_current', 'list', 'list_123'])
    @patch('clickup_framework.commands.set_current.get_context_manager')
    def test_main_set_current(self, mock_context):
        """Test main CLI with set_current command."""
        mock_context_inst = Mock()
        mock_context_inst._save = Mock()  # Mock _save to prevent JSON serialization
        mock_context.return_value = mock_context_inst

        captured_output = io.StringIO()
        sys.stdout = captured_output

        main()

        sys.stdout = sys.__stdout__

        mock_context_inst.set_current_list.assert_called_once()

    @patch('sys.argv', ['cli.py', 'clear_current'])
    @patch('clickup_framework.commands.clear_current.get_context_manager')
    def test_main_clear_current_all(self, mock_context):
        """Test main CLI with clear_current command (all)."""
        mock_context_inst = Mock()
        mock_context_inst._save = Mock()  # Mock _save to prevent JSON serialization
        mock_context_inst.get_all.return_value = {}
        mock_context.return_value = mock_context_inst

        captured_output = io.StringIO()
        sys.stdout = captured_output

        main()

        sys.stdout = sys.__stdout__

        mock_context_inst.clear_all.assert_called_once()

    @patch('sys.argv', ['cli.py', 'show_current'])
    @patch('clickup_framework.commands.show_current.get_context_manager')
    def test_main_show_current(self, mock_context):
        """Test main CLI with show_current command."""
        mock_context_inst = Mock()
        mock_context_inst.get_all.return_value = {'task': 'task_123'}
        mock_context_inst.get_current_task.return_value = 'task_123'
        mock_context_inst.get_current_list.return_value = None
        mock_context_inst.get_current_space.return_value = None
        mock_context_inst.get_current_folder.return_value = None
        mock_context_inst.get_current_workspace.return_value = None
        mock_context_inst.get_api_token.return_value = None
        mock_context_inst.get_default_assignee.return_value = None
        mock_context.return_value = mock_context_inst

        captured_output = io.StringIO()
        sys.stdout = captured_output

        main()

        sys.stdout = sys.__stdout__

        output = captured_output.getvalue()
        # Check that output contains context (may have ANSI codes)
        self.assertTrue(len(output) > 0)
        self.assertIn("task_123", output)

    @patch('sys.argv', ['cli.py', 'demo', '--preset', 'minimal'])
    @patch('clickup_framework.commands.demo.DisplayManager')
    def test_main_with_preset(self, mock_display_mgr):
        """Test main CLI with preset argument."""
        mock_display_inst = Mock()
        mock_display_inst.hierarchy_view.return_value = "Demo"
        mock_display_mgr.return_value = mock_display_inst

        captured_output = io.StringIO()
        sys.stdout = captured_output

        main()

        sys.stdout = sys.__stdout__

        self.assertTrue(len(captured_output.getvalue()) > 0)


class TestAssignedTasksCommand(unittest.TestCase):
    """Test assigned_tasks_command function."""

    @patch('clickup_framework.commands.assigned_command.ClickUpClient')
    @patch('clickup_framework.commands.assigned_command.get_context_manager')
    def test_assigned_tasks_with_user_and_team(self, mock_context, mock_client):
        """Test assigned command with user-id and team-id provided."""
        mock_context_inst = Mock()
        mock_context_inst.resolve_id.return_value = 'team_123'
        mock_context_inst.get_ansi_output.return_value = True
        mock_context.return_value = mock_context_inst

        mock_client_inst = Mock()
        # Return tasks with dependencies
        mock_client_inst.get_team_tasks.return_value = {
            'tasks': [
                {
                    'id': 'task_1',
                    'name': 'Task 1',
                    'status': {'status': 'in progress'},
                    'dependencies': [],
                    'assignees': [{'id': '12345'}]
                },
                {
                    'id': 'task_2',
                    'name': 'Task 2',
                    'status': {'status': 'to do'},
                    'dependencies': [
                        {'type': 0, 'depends_on': 'task_1'}  # Task 2 waits on Task 1
                    ],
                    'assignees': [{'id': '12345'}]
                }
            ]
        }
        mock_client.return_value = mock_client_inst

        args = argparse.Namespace(
            user_id='12345',
            team_id='team_123'
        )

        captured_output = io.StringIO()
        sys.stdout = captured_output

        assigned_tasks_command(args)

        sys.stdout = sys.__stdout__

        # Verify API calls
        mock_client_inst.get_team_tasks.assert_called_once_with(
            'team_123',
            assignees=['12345'],
            subtasks=True,
            include_closed=False
        )

        output = captured_output.getvalue()
        self.assertIn('Task 1', output)
        self.assertIn('Task 2', output)

    @patch('clickup_framework.commands.assigned_command.get_context_manager')
    def test_assigned_tasks_no_user_id_or_default(self, mock_context):
        """Test assigned command without user-id and no default assignee."""
        mock_context_inst = Mock()
        mock_context_inst.get_default_assignee.return_value = None
        mock_context.return_value = mock_context_inst

        args = argparse.Namespace(
            user_id=None,
            team_id='team_123'
        )

        with self.assertRaises(SystemExit) as cm:
            assigned_tasks_command(args)

        self.assertEqual(cm.exception.code, 1)

    @patch('clickup_framework.commands.assigned_command.ClickUpClient')
    @patch('clickup_framework.commands.assigned_command.get_context_manager')
    def test_assigned_tasks_use_default_assignee(self, mock_context, mock_client):
        """Test assigned command using default assignee from context."""
        mock_context_inst = Mock()
        mock_context_inst.get_default_assignee.return_value = '68483025'
        mock_context_inst.resolve_id.return_value = 'team_123'
        mock_context_inst.get_ansi_output.return_value = True
        mock_context.return_value = mock_context_inst

        mock_client_inst = Mock()
        mock_client_inst.get_team_tasks.return_value = {'tasks': []}
        mock_client.return_value = mock_client_inst

        args = argparse.Namespace(
            user_id=None,
            team_id='team_123'
        )

        captured_output = io.StringIO()
        sys.stdout = captured_output

        assigned_tasks_command(args)

        sys.stdout = sys.__stdout__

        # Verify default assignee was used
        mock_client_inst.get_team_tasks.assert_called_once_with(
            'team_123',
            assignees=['68483025'],
            subtasks=True,
            include_closed=False
        )

    @patch('clickup_framework.commands.assigned_command.ClickUpClient')
    @patch('clickup_framework.commands.assigned_command.get_context_manager')
    def test_assigned_tasks_no_workspace_no_teams(self, mock_context, mock_client):
        """Test assigned command without workspace ID and no teams available."""
        mock_context_inst = Mock()
        mock_context_inst.get_default_assignee.return_value = '12345'
        mock_context_inst.resolve_id.side_effect = ValueError("No workspace set")
        mock_context.return_value = mock_context_inst

        mock_client_inst = Mock()
        mock_client_inst.get_authorized_workspaces.return_value = {'teams': []}
        mock_client.return_value = mock_client_inst

        args = argparse.Namespace(
            user_id='12345',
            team_id=None
        )

        with self.assertRaises(SystemExit) as cm:
            assigned_tasks_command(args)

        self.assertEqual(cm.exception.code, 1)

    @patch('builtins.input', return_value='1')
    @patch('clickup_framework.commands.assigned_command.ClickUpClient')
    @patch('clickup_framework.commands.assigned_command.get_context_manager')
    def test_assigned_tasks_interactive_workspace_selection(self, mock_context, mock_client, mock_input):
        """Test assigned command with interactive workspace selection."""
        mock_context_inst = Mock()
        mock_context_inst.get_default_assignee.return_value = '12345'
        mock_context_inst.resolve_id.side_effect = ValueError("No workspace set")
        mock_context_inst.get_ansi_output.return_value = True
        mock_context.return_value = mock_context_inst

        mock_client_inst = Mock()
        mock_client_inst.get_authorized_workspaces.return_value = {
            'teams': [
                {'id': 'team_123', 'name': 'My Workspace'},
                {'id': 'team_456', 'name': 'Other Workspace'}
            ]
        }
        mock_client_inst.get_team_tasks.return_value = {'tasks': []}
        mock_client.return_value = mock_client_inst

        args = argparse.Namespace(
            user_id='12345',
            team_id=None
        )

        captured_output = io.StringIO()
        sys.stdout = captured_output

        assigned_tasks_command(args)

        sys.stdout = sys.__stdout__

        # Verify workspace list was fetched
        mock_client_inst.get_authorized_workspaces.assert_called_once()
        # Verify the selected workspace was used
        mock_client_inst.get_team_tasks.assert_called_once_with(
            'team_123',
            assignees=['12345'],
            subtasks=True,
            include_closed=False
        )

    @patch('builtins.input', return_value='q')
    @patch('clickup_framework.commands.assigned_command.ClickUpClient')
    @patch('clickup_framework.commands.assigned_command.get_context_manager')
    def test_assigned_tasks_cancel_workspace_selection(self, mock_context, mock_client, mock_input):
        """Test assigned command cancelling workspace selection."""
        mock_context_inst = Mock()
        mock_context_inst.get_default_assignee.return_value = '12345'
        mock_context_inst.resolve_id.side_effect = ValueError("No workspace set")
        mock_context_inst.get_ansi_output.return_value = True
        mock_context.return_value = mock_context_inst

        mock_client_inst = Mock()
        mock_client_inst.get_authorized_workspaces.return_value = {
            'teams': [
                {'id': 'team_123', 'name': 'My Workspace'}
            ]
        }
        mock_client.return_value = mock_client_inst

        args = argparse.Namespace(
            user_id='12345',
            team_id=None
        )

        with self.assertRaises(SystemExit) as cm:
            assigned_tasks_command(args)

        self.assertEqual(cm.exception.code, 0)  # Cancelled, not an error

    @patch('clickup_framework.commands.assigned_command.ClickUpClient')
    @patch('clickup_framework.commands.assigned_command.get_context_manager')
    def test_assigned_tasks_no_tasks_found(self, mock_context, mock_client):
        """Test assigned command when no tasks are found."""
        mock_context_inst = Mock()
        mock_context_inst.resolve_id.return_value = 'team_123'
        mock_context_inst.get_ansi_output.return_value = True
        mock_context.return_value = mock_context_inst

        mock_client_inst = Mock()
        mock_client_inst.get_team_tasks.return_value = {'tasks': []}
        mock_client.return_value = mock_client_inst

        args = argparse.Namespace(
            user_id='12345',
            team_id='team_123'
        )

        captured_output = io.StringIO()
        sys.stdout = captured_output

        assigned_tasks_command(args)

        sys.stdout = sys.__stdout__

        output = captured_output.getvalue()
        self.assertIn('No tasks found', output)


class TestPullCommand(unittest.TestCase):
    """Test pull_command function with comprehensive coverage."""

    @patch('clickup_framework.commands.gitpull_command.Path')
    @patch('clickup_framework.commands.gitpull_command.subprocess.run')
    def test_pull_command_success(self, mock_run, mock_path):
        """Test pull command in a Git repository."""
        # Mock .git directory exists
        mock_git_dir = Mock()
        mock_git_dir.exists.return_value = True
        mock_path.return_value = mock_git_dir

        # Mock successful git pull
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        args = argparse.Namespace()

        with self.assertRaises(SystemExit) as cm:
            from clickup_framework.commands.gitpull_command import pull_command
            pull_command(args)

        self.assertEqual(cm.exception.code, 0)
        mock_run.assert_called_once_with(
            ['git', 'pull', '--rebase'],
            capture_output=False,
            text=True
        )

    @patch('clickup_framework.commands.gitpull_command.Path')
    def test_pull_command_not_in_git_repo(self, mock_path):
        """Test pull command when not in a Git repository."""
        # Mock .git directory does not exist
        mock_git_dir = Mock()
        mock_git_dir.exists.return_value = False
        mock_path.return_value = mock_git_dir

        args = argparse.Namespace()

        captured_output = io.StringIO()
        sys.stderr = captured_output

        with self.assertRaises(SystemExit) as cm:
            from clickup_framework.commands.gitpull_command import pull_command
            pull_command(args)

        sys.stderr = sys.__stderr__

        self.assertEqual(cm.exception.code, 1)
        self.assertIn("Not in a Git repository", captured_output.getvalue())

    @patch('clickup_framework.commands.gitpull_command.Path')
    @patch('clickup_framework.commands.gitpull_command.subprocess.run')
    def test_pull_command_git_failure(self, mock_run, mock_path):
        """Test pull command when git pull fails."""
        # Mock .git directory exists
        mock_git_dir = Mock()
        mock_git_dir.exists.return_value = True
        mock_path.return_value = mock_git_dir

        # Mock failed git pull
        mock_result = Mock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        args = argparse.Namespace()

        with self.assertRaises(SystemExit) as cm:
            from clickup_framework.commands.gitpull_command import pull_command
            pull_command(args)

        self.assertEqual(cm.exception.code, 1)


class TestSuckCommand(unittest.TestCase):
    """Test suck_command function with comprehensive coverage."""

    @patch('clickup_framework.commands.gitsuck_command.find_git_repositories')
    @patch('clickup_framework.commands.gitsuck_command.subprocess.run')
    def test_suck_command_success(self, mock_run, mock_find_repos):
        """Test suck command with multiple repositories."""
        # Mock finding repositories
        mock_find_repos.return_value = [
            Path('/path/to/repo1'),
            Path('/path/to/repo2')
        ]

        # Mock successful git pulls
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Already up to date."
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        args = argparse.Namespace()

        captured_output = io.StringIO()
        sys.stdout = captured_output

        with self.assertRaises(SystemExit) as cm:
            from clickup_framework.commands.gitsuck_command import suck_command
            suck_command(args)

        sys.stdout = sys.__stdout__

        self.assertEqual(cm.exception.code, 0)
        output = captured_output.getvalue()
        self.assertIn("Found 2 repositories", output)
        self.assertIn("2 successful, 0 failed", output)
        self.assertEqual(mock_run.call_count, 2)

    @patch('clickup_framework.commands.gitsuck_command.find_git_repositories')
    def test_suck_command_no_repos_found(self, mock_find_repos):
        """Test suck command when no repositories are found."""
        # Mock finding no repositories
        mock_find_repos.return_value = []

        args = argparse.Namespace()

        captured_output = io.StringIO()
        sys.stdout = captured_output

        from clickup_framework.commands.gitsuck_command import suck_command
        suck_command(args)

        sys.stdout = sys.__stdout__

        output = captured_output.getvalue()
        self.assertIn("No Git repositories found", output)

    @patch('clickup_framework.commands.gitsuck_command.find_git_repositories')
    @patch('clickup_framework.commands.gitsuck_command.subprocess.run')
    def test_suck_command_partial_failure(self, mock_run, mock_find_repos):
        """Test suck command with some repositories failing."""
        # Mock finding repositories
        mock_find_repos.return_value = [
            Path('/path/to/repo1'),
            Path('/path/to/repo2'),
            Path('/path/to/repo3')
        ]

        # Mock mixed results
        def run_side_effect(*args, **kwargs):
            repo_path = kwargs.get('cwd', '')
            if 'repo2' in str(repo_path):
                result = Mock()
                result.returncode = 1
                result.stdout = ""
                result.stderr = "fatal: unable to access repository"
                return result
            else:
                result = Mock()
                result.returncode = 0
                result.stdout = "Already up to date."
                result.stderr = ""
                return result

        mock_run.side_effect = run_side_effect

        args = argparse.Namespace()

        captured_output = io.StringIO()
        sys.stdout = captured_output

        with self.assertRaises(SystemExit) as cm:
            from clickup_framework.commands.gitsuck_command import suck_command
            suck_command(args)

        sys.stdout = sys.__stdout__

        self.assertEqual(cm.exception.code, 1)
        output = captured_output.getvalue()
        self.assertIn("2 successful, 1 failed", output)
        self.assertIn("Pull failed", output)

    def test_find_git_repositories_function(self):
        """Test find_git_repositories function."""
        from clickup_framework.commands.gitsuck_command import find_git_repositories

        # This will test the actual directory structure
        # In a real git repo, it should find at least the current repo
        repos = find_git_repositories('.')

        # Verify it returns a list
        self.assertIsInstance(repos, list)

        # Each item should be a Path object
        for repo in repos:
            self.assertIsInstance(repo, Path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
