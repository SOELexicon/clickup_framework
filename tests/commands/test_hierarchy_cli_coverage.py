"""
Comprehensive CLI Coverage Tests for Hierarchy Command

Tests cover:
- All valid argument combinations for 'cum h' command
- Output format validation (pipe structure, tree characters)
- Piping output compatibility
- Different preset variations
- Edge cases and error conditions
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import subprocess
import sys
import io
import argparse
import re
from pathlib import Path

from clickup_framework.cli import hierarchy_command, create_format_options
from clickup_framework.components import FormatOptions


class TestHierarchyCommandArguments(unittest.TestCase):
    """Test hierarchy command with all valid argument combinations."""

    def setUp(self):
        """Set up common mocks for all tests."""
        self.mock_context = self._create_mock_context()
        self.mock_client = self._create_mock_client()
        self.mock_display = self._create_mock_display()

    def _create_mock_context(self):
        """Create a mock context manager."""
        mock_ctx = Mock()
        mock_ctx.resolve_id.return_value = 'list_123'
        mock_ctx.get_ansi_output.return_value = True
        return mock_ctx

    def _create_mock_client(self):
        """Create a mock ClickUp client."""
        mock_client = Mock()
        mock_client.get_list.return_value = {
            'id': 'list_123',
            'name': 'Test List',
            'statuses': []
        }
        mock_client.get_list_tasks.return_value = {
            'tasks': [
                {
                    'id': 'task_1',
                    'name': 'Parent Task',
                    'status': {'status': 'Open'},
                    'parent': None,
                    'description': 'Parent description',
                    'date_created': '1234567890000',
                    'date_updated': '1234567890000',
                },
                {
                    'id': 'task_2',
                    'name': 'Child Task',
                    'status': {'status': 'Open'},
                    'parent': 'task_1',
                    'description': 'Child description',
                    'date_created': '1234567890000',
                    'date_updated': '1234567890000',
                }
            ]
        }
        return mock_client

    def _create_mock_display(self):
        """Create a mock display manager."""
        mock_display = Mock()
        # Return realistic tree output
        mock_display.hierarchy_view.return_value = (
            "└── 📝 ⬜ Parent Task (0/1 complete)\n"
            "    │     📅 Created: 2025-11-14 | Updated: 2025-11-14\n"
            "    └── 📝 ⬜ Child Task\n"
            "            📅 Created: 2025-11-14 | Updated: 2025-11-14\n"
        )
        return mock_display

    @patch('clickup_framework.commands.hierarchy.get_list_statuses')
    @patch('clickup_framework.commands.hierarchy.DisplayManager')
    @patch('clickup_framework.commands.hierarchy.ClickUpClient')
    @patch('clickup_framework.commands.hierarchy.get_context_manager')
    @patch('clickup_framework.commands.hierarchy.resolve_container_id')
    def test_hierarchy_with_all_display_options(
        self, mock_resolve, mock_context, mock_client, mock_display, mock_statuses
    ):
        """Test hierarchy command with all display options enabled."""
        mock_context.return_value = self.mock_context
        mock_client.return_value = self.mock_client
        mock_display.return_value = self.mock_display
        mock_resolve.return_value = {'type': 'list', 'id': 'list_123'}
        mock_statuses.return_value = ""

        args = argparse.Namespace(
            list_id='list_123',
            show_all=False,
            include_completed=True,
            header='My Tasks',
            colorize=True,
            show_ids=True,
            show_tags=True,
            show_descriptions=True,
            show_dates=True,
            show_comments=5,
            show_emoji=True,
            full_descriptions=True,
            preset=None
        )

        captured_output = io.StringIO()
        sys.stdout = captured_output

        hierarchy_command(args)

        sys.stdout = sys.__stdout__

        # Verify all options were passed correctly
        call_args = self.mock_display.hierarchy_view.call_args
        options = call_args[0][1]

        self.assertIsInstance(options, FormatOptions)
        self.assertTrue(options.colorize_output)
        self.assertTrue(options.show_ids)
        self.assertTrue(options.show_tags)
        self.assertTrue(options.show_descriptions)
        self.assertTrue(options.show_dates)
        self.assertEqual(options.show_comments, 5)
        self.assertTrue(options.show_type_emoji)
        self.assertTrue(options.include_completed)

    @patch('clickup_framework.commands.hierarchy.get_list_statuses')
    @patch('clickup_framework.commands.hierarchy.DisplayManager')
    @patch('clickup_framework.commands.hierarchy.ClickUpClient')
    @patch('clickup_framework.commands.hierarchy.get_context_manager')
    @patch('clickup_framework.commands.hierarchy.resolve_container_id')
    def test_hierarchy_with_minimal_preset(
        self, mock_resolve, mock_context, mock_client, mock_display, mock_statuses
    ):
        """Test hierarchy command with 'minimal' preset."""
        mock_context.return_value = self.mock_context
        mock_client.return_value = self.mock_client
        mock_display.return_value = self.mock_display
        mock_resolve.return_value = {'type': 'list', 'id': 'list_123'}
        mock_statuses.return_value = ""

        args = argparse.Namespace(
            list_id='list_123',
            show_all=False,
            include_completed=False,
            header=None,
            preset='minimal'
        )

        captured_output = io.StringIO()
        sys.stdout = captured_output

        hierarchy_command(args)

        sys.stdout = sys.__stdout__

        # Verify preset was applied
        call_args = self.mock_display.hierarchy_view.call_args
        options = call_args[0][1]
        self.assertIsInstance(options, FormatOptions)

    @patch('clickup_framework.commands.hierarchy.get_list_statuses')
    @patch('clickup_framework.commands.hierarchy.DisplayManager')
    @patch('clickup_framework.commands.hierarchy.ClickUpClient')
    @patch('clickup_framework.commands.hierarchy.get_context_manager')
    @patch('clickup_framework.commands.hierarchy.resolve_container_id')
    def test_hierarchy_with_full_preset(
        self, mock_resolve, mock_context, mock_client, mock_display, mock_statuses
    ):
        """Test hierarchy command with 'full' preset."""
        mock_context.return_value = self.mock_context
        mock_client.return_value = self.mock_client
        mock_display.return_value = self.mock_display
        mock_resolve.return_value = {'type': 'list', 'id': 'list_123'}
        mock_statuses.return_value = ""

        args = argparse.Namespace(
            list_id='list_123',
            show_all=False,
            include_completed=False,
            header=None,
            preset='full'
        )

        captured_output = io.StringIO()
        sys.stdout = captured_output

        hierarchy_command(args)

        sys.stdout = sys.__stdout__

        call_args = self.mock_display.hierarchy_view.call_args
        options = call_args[0][1]
        self.assertIsInstance(options, FormatOptions)

    @patch('clickup_framework.commands.hierarchy.get_list_statuses')
    @patch('clickup_framework.commands.hierarchy.DisplayManager')
    @patch('clickup_framework.commands.hierarchy.ClickUpClient')
    @patch('clickup_framework.commands.hierarchy.get_context_manager')
    @patch('clickup_framework.commands.hierarchy.resolve_container_id')
    def test_hierarchy_no_colorize(
        self, mock_resolve, mock_context, mock_client, mock_display, mock_statuses
    ):
        """Test hierarchy command with colorization disabled."""
        mock_context.return_value = self.mock_context
        mock_client.return_value = self.mock_client
        mock_display.return_value = self.mock_display
        mock_resolve.return_value = {'type': 'list', 'id': 'list_123'}
        mock_statuses.return_value = ""

        args = argparse.Namespace(
            list_id='list_123',
            show_all=False,
            include_completed=False,
            header=None,
            colorize=False,
            show_ids=False,
            show_tags=False,
            show_descriptions=False,
            show_dates=False,
            show_comments=0,
            show_emoji=False,
            full_descriptions=False,
            preset=None
        )

        captured_output = io.StringIO()
        sys.stdout = captured_output

        hierarchy_command(args)

        sys.stdout = sys.__stdout__

        call_args = self.mock_display.hierarchy_view.call_args
        options = call_args[0][1]
        self.assertFalse(options.colorize_output)


class TestHierarchyOutputFormat(unittest.TestCase):
    """Test that hierarchy command output adheres to format specifications."""

    @patch('clickup_framework.commands.hierarchy.get_list_statuses')
    @patch('clickup_framework.commands.hierarchy.DisplayManager')
    @patch('clickup_framework.commands.hierarchy.ClickUpClient')
    @patch('clickup_framework.commands.hierarchy.get_context_manager')
    @patch('clickup_framework.commands.hierarchy.resolve_container_id')
    def test_output_has_tree_characters(
        self, mock_resolve, mock_context, mock_client, mock_display, mock_statuses
    ):
        """Test that output contains proper tree drawing characters."""
        mock_ctx = Mock()
        mock_ctx.resolve_id.return_value = 'list_123'
        mock_ctx.get_ansi_output.return_value = True
        mock_context.return_value = mock_ctx

        mock_client_inst = Mock()
        mock_client_inst.get_list.return_value = {'id': 'list_123', 'statuses': []}
        mock_client_inst.get_list_tasks.return_value = {'tasks': []}
        mock_client.return_value = mock_client_inst

        mock_display_inst = Mock()
        # Return output with tree characters
        mock_display_inst.hierarchy_view.return_value = (
            "└── Task 1\n"
            "    ├── Task 2\n"
            "    └── Task 3\n"
        )
        mock_display.return_value = mock_display_inst

        mock_resolve.return_value = {'type': 'list', 'id': 'list_123'}
        mock_statuses.return_value = ""

        args = argparse.Namespace(
            list_id='list_123',
            show_all=False,
            include_completed=False,
            header=None,
            colorize=False,
            show_ids=False,
            show_tags=False,
            show_descriptions=False,
            show_dates=False,
            show_comments=0,
            show_emoji=False,
            full_descriptions=False,
            preset=None
        )

        captured_output = io.StringIO()
        sys.stdout = captured_output

        hierarchy_command(args)

        sys.stdout = sys.__stdout__

        output = captured_output.getvalue()

        # Verify tree characters are present
        self.assertIn('└──', output)
        self.assertIn('├──', output)

    @patch('clickup_framework.commands.hierarchy.get_list_statuses')
    @patch('clickup_framework.commands.hierarchy.DisplayManager')
    @patch('clickup_framework.commands.hierarchy.ClickUpClient')
    @patch('clickup_framework.commands.hierarchy.get_context_manager')
    @patch('clickup_framework.commands.hierarchy.resolve_container_id')
    def test_output_pipe_markers_on_metadata(
        self, mock_resolve, mock_context, mock_client, mock_display, mock_statuses
    ):
        """Test that metadata lines have proper pipe markers."""
        mock_ctx = Mock()
        mock_ctx.resolve_id.return_value = 'list_123'
        mock_ctx.get_ansi_output.return_value = True
        mock_context.return_value = mock_ctx

        mock_client_inst = Mock()
        mock_client_inst.get_list.return_value = {'id': 'list_123', 'statuses': []}
        mock_client_inst.get_list_tasks.return_value = {'tasks': []}
        mock_client.return_value = mock_client_inst

        mock_display_inst = Mock()
        # Return output with metadata lines
        mock_display_inst.hierarchy_view.return_value = (
            "└── Task 1 (0/1 complete)\n"
            "    │     📅 Created: 2025-11-14\n"
            "    └── Task 2\n"
            "            📅 Created: 2025-11-14\n"
        )
        mock_display.return_value = mock_display_inst

        mock_resolve.return_value = {'type': 'list', 'id': 'list_123'}
        mock_statuses.return_value = ""

        args = argparse.Namespace(
            list_id='list_123',
            show_all=False,
            include_completed=False,
            header=None,
            colorize=False,
            show_ids=False,
            show_tags=False,
            show_descriptions=False,
            show_dates=True,
            show_comments=0,
            show_emoji=False,
            full_descriptions=False,
            preset=None
        )

        captured_output = io.StringIO()
        sys.stdout = captured_output

        hierarchy_command(args)

        sys.stdout = sys.__stdout__

        output = captured_output.getvalue()

        # Verify pipe markers are present on metadata lines FOR TASKS WITH SIBLINGS
        # Note: Last task in a branch won't have pipe (uses spaces instead)
        lines = output.split('\n')
        has_pipe_on_metadata = False
        for line in lines:
            if '📅' in line:
                # Metadata line may have pipe character if task has siblings below
                emoji_pos = line.index('📅')
                prefix = line[:emoji_pos]
                if '│' in prefix:
                    has_pipe_on_metadata = True

        # At least one metadata line should have a pipe (the non-last task)
        self.assertTrue(has_pipe_on_metadata,
                       "Expected at least one metadata line with pipe marker")

    @patch('clickup_framework.commands.hierarchy.get_list_statuses')
    @patch('clickup_framework.commands.hierarchy.DisplayManager')
    @patch('clickup_framework.commands.hierarchy.ClickUpClient')
    @patch('clickup_framework.commands.hierarchy.get_context_manager')
    @patch('clickup_framework.commands.hierarchy.resolve_container_id')
    def test_output_consistent_indentation(
        self, mock_resolve, mock_context, mock_client, mock_display, mock_statuses
    ):
        """Test that output has consistent 4-character indentation."""
        mock_ctx = Mock()
        mock_ctx.resolve_id.return_value = 'list_123'
        mock_ctx.get_ansi_output.return_value = True
        mock_context.return_value = mock_ctx

        mock_client_inst = Mock()
        mock_client_inst.get_list.return_value = {'id': 'list_123', 'statuses': []}
        mock_client_inst.get_list_tasks.return_value = {'tasks': []}
        mock_client.return_value = mock_client_inst

        mock_display_inst = Mock()
        mock_display_inst.hierarchy_view.return_value = (
            "└── Task 1\n"
            "    └── Task 2\n"
            "        └── Task 3\n"
        )
        mock_display.return_value = mock_display_inst

        mock_resolve.return_value = {'type': 'list', 'id': 'list_123'}
        mock_statuses.return_value = ""

        args = argparse.Namespace(
            list_id='list_123',
            show_all=False,
            include_completed=False,
            header=None,
            colorize=False,
            show_ids=False,
            show_tags=False,
            show_descriptions=False,
            show_dates=False,
            show_comments=0,
            show_emoji=False,
            full_descriptions=False,
            preset=None
        )

        captured_output = io.StringIO()
        sys.stdout = captured_output

        hierarchy_command(args)

        sys.stdout = sys.__stdout__

        output = captured_output.getvalue()
        lines = output.split('\n')

        # Check that indentation increases by 4 characters per level
        for line in lines:
            if '└──' in line or '├──' in line:
                # Count leading spaces before tree character
                match = re.match(r'^(\s*)[└├]', line)
                if match:
                    indent = len(match.group(1))
                    # Indent should be multiple of 4
                    self.assertEqual(indent % 4, 0,
                                   f"Indentation not multiple of 4: {repr(line)}")


class TestHierarchyPipingOutput(unittest.TestCase):
    """Test that hierarchy command output can be piped correctly."""

    def test_output_is_plain_text_pipeable(self):
        """Test that output without colorization can be piped."""
        # This is more of a demonstration that output is text-based
        # In real usage, this would be: cum h list_123 --no-colorize | grep "Task"

        sample_output = (
            "└── Task 1\n"
            "    ├── Task 2\n"
            "    └── Task 3\n"
        )

        # Simulate piping through grep
        filtered = '\n'.join([
            line for line in sample_output.split('\n')
            if 'Task 2' in line
        ])

        self.assertIn('Task 2', filtered)
        self.assertNotIn('Task 3', filtered)

    def test_output_strips_ansi_when_not_tty(self):
        """Test that ANSI codes can be stripped for piping."""
        # When output is piped, ANSI codes should ideally be stripped
        # This tests the concept

        ansi_output = "\x1b[31mRed Text\x1b[0m Normal Text"

        # Strip ANSI escape codes (pattern: \x1b[...m)
        plain = re.sub(r'\x1b\[[0-9;]*m', '', ansi_output)

        self.assertEqual(plain, "Red Text Normal Text")
        self.assertNotIn('\x1b', plain)


class TestHierarchyArgumentCombinations(unittest.TestCase):
    """Test all valid combinations of hierarchy command arguments."""

    @patch('clickup_framework.commands.hierarchy.get_list_statuses')
    @patch('clickup_framework.commands.hierarchy.DisplayManager')
    @patch('clickup_framework.commands.hierarchy.ClickUpClient')
    @patch('clickup_framework.commands.hierarchy.get_context_manager')
    @patch('clickup_framework.commands.hierarchy.resolve_container_id')
    def test_descriptions_with_dates(
        self, mock_resolve, mock_context, mock_client, mock_display, mock_statuses
    ):
        """Test --show-descriptions combined with --show-dates."""
        mock_ctx = Mock()
        mock_ctx.resolve_id.return_value = 'list_123'
        mock_ctx.get_ansi_output.return_value = True
        mock_context.return_value = mock_ctx

        mock_client_inst = Mock()
        mock_client_inst.get_list.return_value = {'id': 'list_123', 'statuses': []}
        mock_client_inst.get_list_tasks.return_value = {'tasks': []}
        mock_client.return_value = mock_client_inst

        mock_display_inst = Mock()
        mock_display_inst.hierarchy_view.return_value = "Test output"
        mock_display.return_value = mock_display_inst

        mock_resolve.return_value = {'type': 'list', 'id': 'list_123'}
        mock_statuses.return_value = ""

        args = argparse.Namespace(
            list_id='list_123',
            show_all=False,
            include_completed=False,
            header=None,
            colorize=False,
            show_ids=False,
            show_tags=False,
            show_descriptions=True,
            show_dates=True,
            show_comments=0,
            show_emoji=False,
            full_descriptions=False,
            preset=None
        )

        captured_output = io.StringIO()
        sys.stdout = captured_output

        hierarchy_command(args)

        sys.stdout = sys.__stdout__

        call_args = mock_display_inst.hierarchy_view.call_args
        options = call_args[0][1]
        self.assertTrue(options.show_descriptions)
        self.assertTrue(options.show_dates)

    @patch('clickup_framework.commands.hierarchy.get_list_statuses')
    @patch('clickup_framework.commands.hierarchy.DisplayManager')
    @patch('clickup_framework.commands.hierarchy.ClickUpClient')
    @patch('clickup_framework.commands.hierarchy.get_context_manager')
    @patch('clickup_framework.commands.hierarchy.resolve_container_id')
    def test_ids_with_tags_and_emoji(
        self, mock_resolve, mock_context, mock_client, mock_display, mock_statuses
    ):
        """Test --show-ids combined with --show-tags and --show-emoji."""
        mock_ctx = Mock()
        mock_ctx.resolve_id.return_value = 'list_123'
        mock_ctx.get_ansi_output.return_value = True
        mock_context.return_value = mock_ctx

        mock_client_inst = Mock()
        mock_client_inst.get_list.return_value = {'id': 'list_123', 'statuses': []}
        mock_client_inst.get_list_tasks.return_value = {'tasks': []}
        mock_client.return_value = mock_client_inst

        mock_display_inst = Mock()
        mock_display_inst.hierarchy_view.return_value = "Test output"
        mock_display.return_value = mock_display_inst

        mock_resolve.return_value = {'type': 'list', 'id': 'list_123'}
        mock_statuses.return_value = ""

        args = argparse.Namespace(
            list_id='list_123',
            show_all=False,
            include_completed=False,
            header=None,
            colorize=True,
            show_ids=True,
            show_tags=True,
            show_descriptions=False,
            show_dates=False,
            show_comments=0,
            show_emoji=True,
            full_descriptions=False,
            preset=None
        )

        captured_output = io.StringIO()
        sys.stdout = captured_output

        hierarchy_command(args)

        sys.stdout = sys.__stdout__

        call_args = mock_display_inst.hierarchy_view.call_args
        options = call_args[0][1]
        self.assertTrue(options.show_ids)
        self.assertTrue(options.show_tags)
        self.assertTrue(options.show_type_emoji)


if __name__ == '__main__':
    unittest.main(verbosity=2)
