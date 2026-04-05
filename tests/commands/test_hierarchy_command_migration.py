"""Regression tests for BaseCommand migration inside hierarchy.py."""

import unittest
from argparse import Namespace
from unittest.mock import Mock, patch

from clickup_framework.commands.base_command import BaseCommand
from clickup_framework.commands.hierarchy import HierarchyCommand, hierarchy_command


class TestHierarchyCommandMigration(unittest.TestCase):
    """Verify the hierarchy wrapper now executes through a BaseCommand subclass."""

    def _mock_context(self):
        context = Mock()
        context.get_ansi_output.return_value = False
        return context

    def test_hierarchy_command_class_inherits_base_command(self):
        self.assertTrue(issubclass(HierarchyCommand, BaseCommand))

    @patch("clickup_framework.commands.hierarchy.ClickUpClient")
    @patch("clickup_framework.commands.hierarchy.get_context_manager")
    def test_hierarchy_wrapper_uses_command_class(
        self,
        mock_get_context_manager,
        mock_client_cls,
    ):
        mock_get_context_manager.return_value = self._mock_context()
        mock_client_cls.return_value = Mock()
        args = Namespace(
            list_id="list-1",
            show_all=False,
            space_id=None,
            include_completed=False,
            show_closed_only=False,
            colorize=None,
        )

        with patch.object(HierarchyCommand, "execute", return_value=None) as mock_execute:
            hierarchy_command(args)

        mock_execute.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)
