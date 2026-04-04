"""Regression tests for the internal search command execution path."""

import io
import unittest
from argparse import Namespace
from unittest.mock import patch

from clickup_framework.commands.search_command import SearchCommand


class TestSearchCommand(unittest.TestCase):
    """Verify search no longer depends on external shell tools."""

    @patch("clickup_framework.commands.base_command.ClickUpClient")
    @patch("clickup_framework.commands.base_command.get_context_manager")
    @patch("clickup_framework.commands.search_command.hierarchy_command")
    def test_search_filters_matches_in_process(
        self,
        mock_hierarchy_command,
        mock_get_context_manager,
        _mock_client,
    ):
        mock_get_context_manager.return_value.get_ansi_output.return_value = False

        def fake_hierarchy(_args):
            print("Task stash cleanup [86abc]")
            print("Task release prep [86def]")

        mock_hierarchy_command.side_effect = fake_hierarchy

        args = Namespace(
            pattern="stash",
            container_id="901517404274",
            case_sensitive=False,
            regex=False,
        )

        command = SearchCommand(args, command_name="search")
        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            command.execute()

        output = stdout.getvalue()
        self.assertIn('Found 1 result(s) matching "stash"', output)
        self.assertIn("Task stash cleanup [86abc]", output)
        self.assertNotIn("Task release prep [86def]", output)

    @patch("clickup_framework.commands.base_command.ClickUpClient")
    @patch("clickup_framework.commands.base_command.get_context_manager")
    @patch("clickup_framework.commands.search_command.hierarchy_command")
    def test_search_no_regex_treats_pattern_as_literal(
        self,
        mock_hierarchy_command,
        mock_get_context_manager,
        _mock_client,
    ):
        mock_get_context_manager.return_value.get_ansi_output.return_value = False

        def fake_hierarchy(_args):
            print("Task bug.*fix literal [86ghi]")
            print("Task bug123fix regex-style [86jkl]")

        mock_hierarchy_command.side_effect = fake_hierarchy

        args = Namespace(
            pattern="bug.*fix",
            container_id=None,
            case_sensitive=False,
            regex=False,
        )

        command = SearchCommand(args, command_name="search")
        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            command.execute()

        output = stdout.getvalue()
        self.assertIn("Task bug.*fix literal [86ghi]", output)
        self.assertNotIn("Task bug123fix regex-style [86jkl]", output)


if __name__ == "__main__":
    unittest.main(verbosity=2)
