"""Regression tests for BaseCommand migration inside custom_field_commands.py."""

import unittest
from argparse import Namespace
from unittest.mock import Mock, patch

from clickup_framework.commands.base_command import BaseCommand
from clickup_framework.commands.custom_field_commands import (
    CustomFieldCommandBase,
    CustomFieldGetCommand,
    CustomFieldListCommand,
    CustomFieldRemoveCommand,
    CustomFieldSetCommand,
    custom_field_get_command,
    custom_field_list_command,
    custom_field_remove_command,
    custom_field_set_command,
)


class TestCustomFieldCommandMigration(unittest.TestCase):
    """Verify migrated custom field wrappers execute through BaseCommand subclasses."""

    def _mock_context(self):
        context = Mock()
        context.get_ansi_output.return_value = False
        return context

    def test_custom_field_command_classes_inherit_base_command(self):
        self.assertTrue(issubclass(CustomFieldCommandBase, BaseCommand))
        self.assertTrue(issubclass(CustomFieldSetCommand, CustomFieldCommandBase))
        self.assertTrue(issubclass(CustomFieldGetCommand, CustomFieldCommandBase))
        self.assertTrue(issubclass(CustomFieldListCommand, CustomFieldCommandBase))
        self.assertTrue(issubclass(CustomFieldRemoveCommand, CustomFieldCommandBase))

    @patch("clickup_framework.commands.custom_field_commands.ClickUpClient")
    @patch("clickup_framework.commands.custom_field_commands.get_context_manager")
    def test_custom_field_set_wrapper_uses_command_class(
        self,
        mock_get_context_manager,
        mock_client_cls,
    ):
        mock_get_context_manager.return_value = self._mock_context()
        mock_client_cls.return_value = Mock()
        args = Namespace(
            task_id="task-1",
            field_name_or_id="Priority",
            value="High",
            colorize=None,
        )

        with patch.object(CustomFieldSetCommand, "execute", return_value=None) as mock_execute:
            custom_field_set_command(args)

        mock_execute.assert_called_once()

    @patch("clickup_framework.commands.custom_field_commands.ClickUpClient")
    @patch("clickup_framework.commands.custom_field_commands.get_context_manager")
    def test_custom_field_get_wrapper_uses_command_class(
        self,
        mock_get_context_manager,
        mock_client_cls,
    ):
        mock_get_context_manager.return_value = self._mock_context()
        mock_client_cls.return_value = Mock()
        args = Namespace(task_id="task-1", field_name_or_id="Priority", colorize=None)

        with patch.object(CustomFieldGetCommand, "execute", return_value=None) as mock_execute:
            custom_field_get_command(args)

        mock_execute.assert_called_once()

    @patch("clickup_framework.commands.custom_field_commands.ClickUpClient")
    @patch("clickup_framework.commands.custom_field_commands.get_context_manager")
    def test_custom_field_list_wrapper_uses_command_class(
        self,
        mock_get_context_manager,
        mock_client_cls,
    ):
        mock_get_context_manager.return_value = self._mock_context()
        mock_client_cls.return_value = Mock()
        args = Namespace(task="task-1", list=None, space=None, workspace=None, colorize=None)

        with patch.object(CustomFieldListCommand, "execute", return_value=None) as mock_execute:
            custom_field_list_command(args)

        mock_execute.assert_called_once()

    @patch("clickup_framework.commands.custom_field_commands.ClickUpClient")
    @patch("clickup_framework.commands.custom_field_commands.get_context_manager")
    def test_custom_field_remove_wrapper_uses_command_class(
        self,
        mock_get_context_manager,
        mock_client_cls,
    ):
        mock_get_context_manager.return_value = self._mock_context()
        mock_client_cls.return_value = Mock()
        args = Namespace(task_id="task-1", field_name_or_id="Priority", colorize=None)

        with patch.object(CustomFieldRemoveCommand, "execute", return_value=None) as mock_execute:
            custom_field_remove_command(args)

        mock_execute.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)
