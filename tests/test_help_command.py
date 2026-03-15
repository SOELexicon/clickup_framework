"""
Test Help Command Output

This test suite ensures that the help command output includes all available commands
and doesn't miss any commands. It runs on every commit via pre-commit hooks and
GitHub Actions to catch missing commands early.
"""

import argparse
import unittest
import sys
import io
from unittest.mock import patch

from clickup_framework.cli import show_command_tree, main
from clickup_framework.commands import register_all_commands


class TestHelpCommandCompleteness(unittest.TestCase):
    """Test that help command includes all available commands."""

    def setUp(self):
        """Set up test fixtures."""
        parser = argparse.ArgumentParser(prog='cum', add_help=False)
        subparsers = parser.add_subparsers(dest='command')
        register_all_commands(subparsers)

        self.command_names = []
        for action in parser._actions:
            if isinstance(action, argparse._SubParsersAction):
                for choice in action._choices_actions:
                    # Alias-only entries are folded into grouped help labels.
                    if choice.dest not in {'h', 'ls', 'l'}:
                        self.command_names.append(choice.dest)

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
        Test that all registered commands appear in help output.

        This uses the actual argparse registrations as the source of truth so the
        test tracks the real CLI surface rather than guessing from module names.
        """
        output = self._get_help_output()

        # Check each command appears in help output
        missing_commands = []
        for cmd in self.command_names:
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
