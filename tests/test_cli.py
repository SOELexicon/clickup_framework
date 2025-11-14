"""
CLI Tests

Tests for the ClickUp Framework CLI module.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import io
import argparse

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
    main
)
from clickup_framework.components import FormatOptions


class TestCreateFormatOptions(unittest.TestCase):
    """Test create_format_options function."""

    def test_minimal_preset(self):
        """Test minimal preset."""
        args = argparse.Namespace(preset='minimal')
        options = create_format_options(args)

        self.assertTrue(options.show_ids)  # Minimal shows IDs
        self.assertFalse(options.show_tags)
        self.assertFalse(options.show_descriptions)

    def test_summary_preset(self):
        """Test summary preset."""
        args = argparse.Namespace(preset='summary')
        options = create_format_options(args)

        self.assertTrue(options.show_tags)
        self.assertIsInstance(options, FormatOptions)

    def test_detailed_preset(self):
        """Test detailed preset."""
        args = argparse.Namespace(preset='detailed')
        options = create_format_options(args)

        self.assertTrue(options.show_descriptions)
        self.assertIsInstance(options, FormatOptions)

    def test_full_preset(self):
        """Test full preset."""
        args = argparse.Namespace(preset='full')
        options = create_format_options(args)

        self.assertTrue(options.show_ids)
        self.assertTrue(options.show_tags)
        self.assertTrue(options.show_descriptions)

    def test_custom_options(self):
        """Test custom options from flags."""
        args = argparse.Namespace(
            preset=None,
            colorize=True,
            show_ids=True,
            show_tags=False,
            show_descriptions=True,
            show_dates=True,
            show_comments=2,
            include_completed=True,
            show_emoji=False
        )
        options = create_format_options(args)

        self.assertTrue(options.colorize_output)
        self.assertTrue(options.show_ids)
        self.assertFalse(options.show_tags)
        self.assertTrue(options.show_descriptions)
        self.assertTrue(options.show_dates)
        self.assertEqual(options.show_comments, 2)
        self.assertTrue(options.include_completed)
        self.assertFalse(options.show_type_emoji)


class TestHierarchyCommand(unittest.TestCase):
    """Test hierarchy_command function."""

    @patch('clickup_framework.commands.hierarchy.get_list_statuses', return_value="")
    @patch('clickup_framework.commands.hierarchy.resolve_container_id')
    @patch('clickup_framework.commands.hierarchy.ClickUpClient')
    @patch('clickup_framework.commands.hierarchy.get_context_manager')
    @patch('clickup_framework.commands.hierarchy.DisplayManager')
    def test_hierarchy_command_success(self, mock_display_mgr, mock_context, mock_client, mock_resolve_container, mock_statuses):
        """Test hierarchy command with valid input."""
        # Setup mocks
        mock_context_inst = Mock()
        mock_context_inst.get_ansi_output.return_value = True
        mock_context.return_value = mock_context_inst

        mock_client_inst = Mock()
        mock_client_inst.get_list_tasks.return_value = {'tasks': []}
        mock_client.return_value = mock_client_inst

        # Mock resolve_container_id to return a list type
        mock_resolve_container.return_value = {'type': 'list', 'id': 'list_123'}

        mock_display_inst = Mock()
        mock_display_inst.hierarchy_view.return_value = "Task Hierarchy"
        mock_display_mgr.return_value = mock_display_inst

        args = argparse.Namespace(
            list_id='list_123',
            show_all=False,
            header=None,
            preset=None,
            colorize=True,
            show_ids=False,
            show_tags=True,
            show_descriptions=False,
            show_dates=False,
            show_comments=0,
            include_completed=False,
            show_closed_only=False,
            show_emoji=True
        )

        # Capture stdout
        captured_output = io.StringIO()
        sys.stdout = captured_output

        hierarchy_command(args)

        sys.stdout = sys.__stdout__

        # Verify
        mock_resolve_container.assert_called_once()
        mock_display_inst.hierarchy_view.assert_called_once()
        self.assertIn("Task Hierarchy", captured_output.getvalue())

    @patch('clickup_framework.cli.get_context_manager')
    def test_hierarchy_command_invalid_list(self, mock_context):
        """Test hierarchy command with invalid list ID."""
        mock_context_inst = Mock()
        mock_context_inst.resolve_id.side_effect = ValueError("Invalid list ID")
        mock_context.return_value = mock_context_inst

        args = argparse.Namespace(list_id='invalid')

        with self.assertRaises(SystemExit) as cm:
            hierarchy_command(args)

        self.assertEqual(cm.exception.code, 1)

    @patch('clickup_framework.commands.hierarchy.get_list_statuses', return_value="")
    @patch('clickup_framework.commands.hierarchy.ClickUpClient')
    @patch('clickup_framework.commands.hierarchy.get_context_manager')
    @patch('clickup_framework.commands.hierarchy.DisplayManager')
    def test_hierarchy_command_with_all_flag(self, mock_display_mgr, mock_context, mock_client, mock_statuses):
        """Test hierarchy command with --all flag."""
        # Setup mocks
        mock_context_inst = Mock()
        mock_context_inst.resolve_id.return_value = 'team_123'
        mock_context_inst.get_ansi_output.return_value = True
        mock_context.return_value = mock_context_inst

        mock_client_inst = Mock()
        mock_client_inst.get_team_tasks.return_value = {'tasks': []}
        mock_client.return_value = mock_client_inst

        mock_display_inst = Mock()
        mock_display_inst.hierarchy_view.return_value = "All Workspace Tasks"
        mock_display_mgr.return_value = mock_display_inst

        args = argparse.Namespace(
            list_id=None,
            show_all=True,
            header=None,
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

        hierarchy_command(args)

        sys.stdout = sys.__stdout__

        # Verify
        mock_context_inst.resolve_id.assert_called_once_with('workspace', 'current')
        mock_client_inst.get_team_tasks.assert_called_once()
        mock_display_inst.hierarchy_view.assert_called_once()
        self.assertIn("All Workspace Tasks", captured_output.getvalue())

    @patch('clickup_framework.cli.get_context_manager')
    def test_hierarchy_command_no_list_id_no_all(self, mock_context):
        """Test hierarchy command with no list_id and no --all flag."""
        args = argparse.Namespace(list_id=None, show_all=False)

        with self.assertRaises(SystemExit) as cm:
            hierarchy_command(args)

        self.assertEqual(cm.exception.code, 1)

    @patch('clickup_framework.cli.get_context_manager')
    def test_hierarchy_command_both_list_id_and_all(self, mock_context):
        """Test hierarchy command with both list_id and --all flag."""
        args = argparse.Namespace(list_id='list_123', show_all=True)

        with self.assertRaises(SystemExit) as cm:
            hierarchy_command(args)

        self.assertEqual(cm.exception.code, 1)


class TestDemoCommand(unittest.TestCase):
    """Test demo_command function."""

    def test_demo_hierarchy_mode(self):
        """Test demo command in hierarchy mode."""
        args = argparse.Namespace(
            mode='hierarchy',
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

        # Just verify output contains expected text
        output = captured_output.getvalue()
        self.assertTrue(len(output) > 0)
        self.assertIn("Feature Development", output)

    def test_demo_stats_mode(self):
        """Test demo command in stats mode."""
        args = argparse.Namespace(
            mode='stats',
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

        # Just verify output contains expected text
        output = captured_output.getvalue()
        self.assertTrue(len(output) > 0)


class TestContextCommands(unittest.TestCase):
    """Test context management commands."""

    @patch('clickup_framework.cli.ClickUpClient')
    @patch('clickup_framework.cli.get_context_manager')
    def test_set_current_task(self, mock_context, mock_client_class):
        """Test set_current command for task with auto-hierarchy detection."""
        mock_context_inst = Mock()
        mock_context.return_value = mock_context_inst

        # Mock the task data returned by the API
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.get_task.return_value = {
            'id': 'task_123',
            'name': 'Test Task',
            'list': {'id': 'list_456', 'name': 'Test List'},
            'folder': {'id': 'folder_789', 'name': 'Test Folder'},
            'space': {'id': 'space_012', 'name': 'Test Space'},
            'status': {'status': 'in progress'}
        }

        args = argparse.Namespace(
            resource_type='task',
            resource_id='task_123'
        )

        captured_output = io.StringIO()
        sys.stdout = captured_output

        set_current_command(args)

        sys.stdout = sys.__stdout__

        # Verify all context setters were called
        mock_context_inst.set_current_task.assert_called_once_with('task_123')
        mock_context_inst.set_current_list.assert_called_once_with('list_456')
        mock_context_inst.set_current_folder.assert_called_once_with('folder_789')
        mock_context_inst.set_current_space.assert_called_once_with('space_012')

        # Verify output includes all resources
        output = captured_output.getvalue()
        self.assertIn("Set current task", output)
        self.assertIn("Set current list", output)
        self.assertIn("Set current folder", output)
        self.assertIn("Set current space", output)
        self.assertIn("Context updated successfully", output)

    @patch('clickup_framework.cli.get_context_manager')
    def test_set_current_list(self, mock_context):
        """Test set_current command for list."""
        mock_context_inst = Mock()
        mock_context.return_value = mock_context_inst

        args = argparse.Namespace(
            resource_type='list',
            resource_id='list_456'
        )

        captured_output = io.StringIO()
        sys.stdout = captured_output

        set_current_command(args)

        sys.stdout = sys.__stdout__

        mock_context_inst.set_current_list.assert_called_once_with('list_456')
        self.assertIn("Set current list", captured_output.getvalue())

    @patch('clickup_framework.cli.get_context_manager')
    def test_set_current_invalid_type(self, mock_context):
        """Test set_current command with invalid resource type."""
        mock_context.return_value = Mock()

        args = argparse.Namespace(
            resource_type='invalid_type',
            resource_id='123'
        )

        with self.assertRaises(SystemExit) as cm:
            set_current_command(args)

        self.assertEqual(cm.exception.code, 1)

    @patch('clickup_framework.cli.get_context_manager')
    def test_clear_current_specific(self, mock_context):
        """Test clear_current command for specific resource."""
        mock_context_inst = Mock()
        mock_context.return_value = mock_context_inst

        args = argparse.Namespace(resource_type='task')

        captured_output = io.StringIO()
        sys.stdout = captured_output

        clear_current_command(args)

        sys.stdout = sys.__stdout__

        mock_context_inst.clear_current_task.assert_called_once()
        self.assertIn("Cleared current task", captured_output.getvalue())

    @patch('clickup_framework.cli.get_context_manager')
    def test_clear_current_all(self, mock_context):
        """Test clear_current command for all resources."""
        mock_context_inst = Mock()
        mock_context.return_value = mock_context_inst

        args = argparse.Namespace(resource_type=None)

        captured_output = io.StringIO()
        sys.stdout = captured_output

        clear_current_command(args)

        sys.stdout = sys.__stdout__

        mock_context_inst.clear_all.assert_called_once()
        self.assertIn("Cleared all context", captured_output.getvalue())

    @patch('clickup_framework.cli.get_context_manager')
    def test_show_current_with_context(self, mock_context):
        """Test show_current command with existing context."""
        mock_context_inst = Mock()
        mock_context_inst.get_all.return_value = {
            'task': 'task_123',
            'list': 'list_456',
            'last_updated': '2024-01-01'
        }
        mock_context_inst.get_current_task.return_value = 'task_123'
        mock_context_inst.get_current_list.return_value = 'list_456'
        mock_context_inst.get_current_space.return_value = None
        mock_context_inst.get_current_folder.return_value = None
        mock_context_inst.get_current_workspace.return_value = None
        mock_context.return_value = mock_context_inst

        args = argparse.Namespace()

        captured_output = io.StringIO()
        sys.stdout = captured_output

        show_current_command(args)

        sys.stdout = sys.__stdout__

        output = captured_output.getvalue()
        # Check that output contains context (may have ANSI codes)
        self.assertTrue(len(output) > 0)
        self.assertIn("task_123", output)
        self.assertIn("list_456", output)

    @patch('clickup_framework.cli.get_context_manager')
    def test_show_current_empty(self, mock_context):
        """Test show_current command with no context."""
        mock_context_inst = Mock()
        mock_context_inst.get_all.return_value = {}
        mock_context.return_value = mock_context_inst

        args = argparse.Namespace()

        captured_output = io.StringIO()
        sys.stdout = captured_output

        show_current_command(args)

        sys.stdout = sys.__stdout__

        self.assertIn("No context set", captured_output.getvalue())


class TestFilterCommand(unittest.TestCase):
    """Test filter_command function."""

    @patch('clickup_framework.commands.filter.ClickUpClient')
    @patch('clickup_framework.commands.filter.get_context_manager')
    @patch('clickup_framework.commands.filter.DisplayManager')
    def test_filter_by_status(self, mock_display_mgr, mock_context, mock_client):
        """Test filter command with status filter."""
        # Setup mocks
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
            status='in progress',
            priority=None,
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

        # Verify filtered_view was called with correct parameters
        call_args = mock_display_inst.filtered_view.call_args
        self.assertEqual(call_args[1]['status'], 'in progress')
        self.assertIn("Filtered Tasks", captured_output.getvalue())


class TestStatsCommand(unittest.TestCase):
    """Test stats_command function."""

    @patch('clickup_framework.commands.stats.ClickUpClient')
    @patch('clickup_framework.commands.stats.get_context_manager')
    @patch('clickup_framework.commands.stats.DisplayManager')
    def test_stats_command(self, mock_display_mgr, mock_context, mock_client):
        """Test stats command."""
        # Setup mocks
        mock_context_inst = Mock()
        mock_context_inst.resolve_id.return_value = 'list_123'
        mock_context.return_value = mock_context_inst

        mock_client_inst = Mock()
        mock_client_inst.get_list_tasks.return_value = {'tasks': []}
        mock_client.return_value = mock_client_inst

        mock_display_inst = Mock()
        mock_display_inst.summary_stats.return_value = "Task Statistics"
        mock_display_mgr.return_value = mock_display_inst

        args = argparse.Namespace(list_id='list_123')

        captured_output = io.StringIO()
        sys.stdout = captured_output

        stats_command(args)

        sys.stdout = sys.__stdout__

        mock_display_inst.summary_stats.assert_called_once()
        self.assertIn("Task Statistics", captured_output.getvalue())


class TestMainCLI(unittest.TestCase):
    """Test main CLI entry point."""

    @patch('sys.argv', ['cli.py', 'demo', '--mode', 'hierarchy'])
    @patch('clickup_framework.commands.demo.DisplayManager')
    def test_main_demo_command(self, mock_display_mgr):
        """Test main CLI with demo command."""
        mock_display_inst = Mock()
        mock_display_inst.hierarchy_view.return_value = "Demo"
        mock_display_mgr.return_value = mock_display_inst

        captured_output = io.StringIO()
        sys.stdout = captured_output

        main()

        sys.stdout = sys.__stdout__

        self.assertIn("Demo", captured_output.getvalue())

    @patch('sys.argv', ['cli.py'])
    def test_main_no_command(self):
        """Test main CLI with no command shows help."""
        with self.assertRaises(SystemExit) as cm:
            main()

        self.assertEqual(cm.exception.code, 1)

    @patch('sys.argv', ['cli.py', 'demo'])
    @patch('clickup_framework.cli.demo_command')
    def test_main_keyboard_interrupt(self, mock_demo):
        """Test main CLI handles keyboard interrupt."""
        mock_demo.side_effect = KeyboardInterrupt()

        with self.assertRaises(SystemExit) as cm:
            main()

        self.assertEqual(cm.exception.code, 130)


if __name__ == "__main__":
    unittest.main(verbosity=2)
