"""Regression tests for invalid command suggestions in CLI parser errors."""

import io
import unittest
from unittest.mock import Mock, patch

from clickup_framework.cli import main


class TestCommandSuggestions(unittest.TestCase):
    """Verify mistyped commands receive actionable suggestions."""

    def _plain_context(self):
        context = Mock()
        context.get_ansi_output.return_value = False
        return context

    @patch("clickup_framework.cli.ARGCOMPLETE_AVAILABLE", False)
    @patch("clickup_framework.cli.get_context_manager")
    def test_root_command_typo_suggests_search(self, mock_get_context_manager):
        mock_get_context_manager.return_value = self._plain_context()
        stderr = io.StringIO()

        with patch("sys.stderr", stderr):
            with patch("sys.argv", ["cum", "serch"]):
                with self.assertRaises(SystemExit) as cm:
                    main()

        self.assertEqual(cm.exception.code, 2)
        output = stderr.getvalue()
        self.assertIn("Did you mean:", output)
        self.assertIn("cum search", output)
        self.assertIn("See suggested command help: cum search --help", output)

    @patch("clickup_framework.cli.ARGCOMPLETE_AVAILABLE", False)
    @patch("clickup_framework.cli.get_context_manager")
    def test_root_command_abbreviation_suggests_task_create_alias(self, mock_get_context_manager):
        mock_get_context_manager.return_value = self._plain_context()
        stderr = io.StringIO()

        with patch("sys.stderr", stderr):
            with patch("sys.argv", ["cum", "tk"]):
                with self.assertRaises(SystemExit) as cm:
                    main()

        self.assertEqual(cm.exception.code, 2)
        output = stderr.getvalue()
        self.assertIn("Did you mean:", output)
        self.assertIn("cum tc  # task_create", output)
        self.assertIn("See suggested command help: cum tc --help", output)

    @patch("clickup_framework.cli.ARGCOMPLETE_AVAILABLE", False)
    @patch("clickup_framework.cli.get_context_manager")
    def test_nested_subcommand_typo_suggests_dump_task(self, mock_get_context_manager):
        mock_get_context_manager.return_value = self._plain_context()
        stderr = io.StringIO()

        with patch("sys.stderr", stderr):
            with patch("sys.argv", ["cum", "dump", "tsk"]):
                with self.assertRaises(SystemExit) as cm:
                    main()

        self.assertEqual(cm.exception.code, 2)
        output = stderr.getvalue()
        self.assertIn("Did you mean:", output)
        self.assertIn("cum dump task", output)
        self.assertIn("See suggested command help: cum dump task --help", output)


if __name__ == "__main__":
    unittest.main(verbosity=2)
