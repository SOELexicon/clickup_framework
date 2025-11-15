"""
Test Help Command Output

This test suite ensures that the help command output includes all available commands
and doesn't miss any commands. It runs on every commit via pre-commit hooks and
GitHub Actions to catch missing commands early.
"""

import unittest
import sys
import io
from unittest.mock import patch
from pathlib import Path

from clickup_framework.cli import show_command_tree, main
from clickup_framework.commands import discover_commands


class TestHelpCommandCompleteness(unittest.TestCase):
    """Test that help command includes all available commands."""

    def setUp(self):
        """Set up test fixtures."""
        # Discover all available commands dynamically
        self.command_modules = discover_commands()

    def _get_help_output(self):
        """Capture and return the help output."""
        captured_output = io.StringIO()
        sys.stdout = captured_output
        show_command_tree()
        sys.stdout = sys.__stdout__
        return captured_output.getvalue()

    def test_help_output_not_empty(self):
        """Test that help output is not empty."""
        output = self._get_help_output()
        self.assertTrue(len(output) > 0, "Help output should not be empty")
        self.assertIn("ClickUp Framework CLI", output)
        self.assertIn("Available Commands", output)

    def test_all_commands_in_help_output(self):
        """
        Test that all discovered commands appear in help output.

        This is a critical test that ensures the help command doesn't miss any
        commands. It dynamically discovers all command modules and verifies that
        each command name appears in the help output.
        """
        output = self._get_help_output()

        # Get all command names from modules
        command_names = set()
        for module in self.command_modules:
            module_name = module.__name__.split('.')[-1]
            # Convert module name to command name(s)
            # e.g., 'task_commands' -> 'task_create', 'task_update', etc.
            # e.g., 'hierarchy' -> 'hierarchy'
            # e.g., 'assigned_command' -> 'assigned'

            # Special handling for different command patterns
            if module_name.endswith('_commands'):
                # Multi-command modules like task_commands, space_commands
                base = module_name.replace('_commands', '')
                # These have subcommands like task_create, task_update, etc.
                # We'll check for the base command in the help
                if base == 'task':
                    command_names.update(['task_create', 'task_update', 'task_delete',
                                        'task_assign', 'task_unassign', 'task_set_status',
                                        'task_set_priority', 'task_set_tags',
                                        'task_add_dependency', 'task_remove_dependency',
                                        'task_add_link', 'task_remove_link'])
                elif base == 'space':
                    command_names.add('space')
                elif base == 'folder':
                    command_names.add('folder')
                elif base == 'list':
                    command_names.add('list-mgmt')
                elif base == 'comment':
                    command_names.update(['comment_add', 'comment_list',
                                        'comment_update', 'comment_delete'])
                elif base == 'checklist':
                    command_names.add('checklist')
                elif base == 'doc':
                    command_names.update(['dlist', 'doc_get', 'doc_create',
                                        'doc_update', 'doc_export', 'doc_import',
                                        'page_list', 'page_create', 'page_update'])
                elif base == 'custom_field':
                    command_names.add('custom-field')
                elif base == 'automation':
                    command_names.add('parent_auto_update')
                elif base == 'attachment':
                    # Attachment commands might be in help
                    pass
            elif module_name.endswith('_command'):
                # Single command modules like assigned_command
                # Special handling for git commands
                if module_name == 'git_overflow_command':
                    command_names.add('overflow')
                elif module_name == 'git_reauthor_command':
                    command_names.add('reauthor')
                elif module_name == 'gitpull_command':
                    command_names.add('pull')
                elif module_name == 'gitsuck_command':
                    command_names.add('suck')
                elif module_name == 'horde_command':
                    command_names.add('horde')
                elif module_name == 'stash_command':
                    command_names.add('stash')
                else:
                    command_names.add(module_name.replace('_command', ''))
            else:
                # Direct command modules like hierarchy, container, flat, etc.
                command_names.add(module_name)

        # Remove utility/special modules
        command_names.discard('utils')
        command_names.discard('__init__')

        # Check each command appears in help output
        missing_commands = []
        for cmd in command_names:
            # Check if command name appears in output (case-insensitive)
            # Account for variations like 'hierarchy [h]' or 'list [ls, l]'
            if cmd.lower() not in output.lower():
                missing_commands.append(cmd)

        if missing_commands:
            self.fail(
                f"The following commands are missing from help output:\n"
                f"{', '.join(sorted(missing_commands))}\n\n"
                f"Please update the show_command_tree() function in cli.py "
                f"to include these commands."
            )

    def test_help_categories_present(self):
        """Test that all expected help categories are present."""
        output = self._get_help_output()

        expected_categories = [
            "View Commands",
            "Context Management",
            "Task Management",
            "Comment Management",
            "Checklist Management",
            "Custom Fields",
            "Docs Management",
            "Workspace Hierarchy",
            "Git Workflow",
            "Configuration"
        ]

        for category in expected_categories:
            self.assertIn(category, output,
                         f"Expected category '{category}' not found in help output")

    def test_help_includes_examples(self):
        """Test that help output includes usage examples."""
        output = self._get_help_output()

        self.assertIn("Quick Examples", output)
        self.assertIn("For detailed help", output)

        # Check for some example commands
        self.assertIn("cum", output)

    def test_help_command_aliases_shown(self):
        """Test that command aliases are shown in help output."""
        output = self._get_help_output()

        # Check that some known aliases are shown
        known_aliases = [
            "[h]",  # hierarchy
            "[ls, l]",  # list
            "[c]",  # clist
            "[f]",  # flat
            "[tc]",  # task_create
            "[tu]",  # task_update
            "[a]",  # assigned
        ]

        for alias in known_aliases:
            self.assertIn(alias, output,
                         f"Expected alias '{alias}' not found in help output")

    @patch('sys.argv', ['cum'])
    def test_no_command_shows_help(self):
        """Test that running 'cum' with no command shows help."""
        captured_output = io.StringIO()
        sys.stdout = captured_output

        with self.assertRaises(SystemExit) as cm:
            main()

        sys.stdout = sys.__stdout__

        # Should exit with code 0 (success) when showing help
        self.assertEqual(cm.exception.code, 0)

        # Should contain help output
        output = captured_output.getvalue()
        self.assertIn("ClickUp Framework CLI", output)
        self.assertIn("Available Commands", output)

    @patch('sys.argv', ['cum', '-h'])
    def test_help_flag_short(self):
        """Test that 'cum -h' shows help."""
        with self.assertRaises(SystemExit) as cm:
            main()

        # argparse exits with 0 when showing help
        self.assertEqual(cm.exception.code, 0)

    @patch('sys.argv', ['cum', '--help'])
    def test_help_flag_long(self):
        """Test that 'cum --help' shows help."""
        with self.assertRaises(SystemExit) as cm:
            main()

        # argparse exits with 0 when showing help
        self.assertEqual(cm.exception.code, 0)

    def test_version_flag(self):
        """Test that version flag works."""
        with patch('sys.argv', ['cum', '--version']):
            with self.assertRaises(SystemExit) as cm:
                main()

            # argparse exits with 0 when showing version
            self.assertEqual(cm.exception.code, 0)

        with patch('sys.argv', ['cum', '-v']):
            with self.assertRaises(SystemExit) as cm:
                main()

            # argparse exits with 0 when showing version
            self.assertEqual(cm.exception.code, 0)


class TestHelpCommandFormatting(unittest.TestCase):
    """Test help command formatting and readability."""

    def test_help_output_has_proper_structure(self):
        """Test that help output has proper tree structure."""
        captured_output = io.StringIO()
        sys.stdout = captured_output
        show_command_tree()
        sys.stdout = sys.__stdout__

        output = captured_output.getvalue()

        # Check for tree formatting characters
        self.assertIn("├─", output, "Help should use tree formatting")
        self.assertIn("└─", output, "Help should use tree formatting")

    def test_help_color_handling(self):
        """Test that help handles color output properly."""
        # Test with ANSI enabled
        with patch('clickup_framework.cli.get_context_manager') as mock_context:
            mock_context_inst = mock_context.return_value
            mock_context_inst.get_ansi_output.return_value = True

            captured_output = io.StringIO()
            sys.stdout = captured_output
            show_command_tree()
            sys.stdout = sys.__stdout__

            output = captured_output.getvalue()
            self.assertTrue(len(output) > 0)

        # Test with ANSI disabled
        with patch('clickup_framework.cli.get_context_manager') as mock_context:
            mock_context_inst = mock_context.return_value
            mock_context_inst.get_ansi_output.return_value = False

            captured_output = io.StringIO()
            sys.stdout = captured_output
            show_command_tree()
            sys.stdout = sys.__stdout__

            output = captured_output.getvalue()
            self.assertTrue(len(output) > 0)
            # Should not contain ANSI codes when disabled
            self.assertNotIn('\x1b[', output)


class TestIndividualCommandHelp(unittest.TestCase):
    """Test that individual commands have help text."""

    def test_hierarchy_command_help(self):
        """Test that hierarchy command has help."""
        with patch('sys.argv', ['cum', 'hierarchy', '--help']):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 0)

    def test_demo_command_help(self):
        """Test that demo command has help."""
        with patch('sys.argv', ['cum', 'demo', '--help']):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 0)

    def test_assigned_command_help(self):
        """Test that assigned command has help."""
        with patch('sys.argv', ['cum', 'assigned', '--help']):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
