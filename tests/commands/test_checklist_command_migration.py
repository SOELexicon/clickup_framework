"""Regression tests for BaseCommand migration inside checklist_commands.py."""

import unittest
from argparse import Namespace
from unittest.mock import Mock, patch

from clickup_framework.commands.base_command import BaseCommand
from clickup_framework.commands.checklist_commands import (
    ChecklistCloneCommand,
    ChecklistCommandBase,
    ChecklistCreateCommand,
    ChecklistDeleteCommand,
    ChecklistItemAddCommand,
    ChecklistItemDeleteCommand,
    ChecklistItemUpdateCommand,
    ChecklistListCommand,
    ChecklistTemplateApplyCommand,
    ChecklistTemplateListCommand,
    ChecklistTemplateShowCommand,
    ChecklistUpdateCommand,
    checklist_clone_command,
    checklist_create_command,
    checklist_delete_command,
    checklist_item_add_command,
    checklist_item_delete_command,
    checklist_item_update_command,
    checklist_list_command,
    checklist_template_apply_command,
    checklist_template_list_command,
    checklist_template_show_command,
    checklist_update_command,
)


class TestChecklistCommandMigration(unittest.TestCase):
    """Verify checklist wrappers now execute through BaseCommand subclasses."""

    def _mock_context(self):
        context = Mock()
        context.get_ansi_output.return_value = False
        return context

    def test_checklist_command_classes_inherit_base_command(self):
        self.assertTrue(issubclass(ChecklistCommandBase, BaseCommand))
        self.assertTrue(issubclass(ChecklistCreateCommand, ChecklistCommandBase))
        self.assertTrue(issubclass(ChecklistDeleteCommand, ChecklistCommandBase))
        self.assertTrue(issubclass(ChecklistUpdateCommand, ChecklistCommandBase))
        self.assertTrue(issubclass(ChecklistItemAddCommand, ChecklistCommandBase))
        self.assertTrue(issubclass(ChecklistItemUpdateCommand, ChecklistCommandBase))
        self.assertTrue(issubclass(ChecklistItemDeleteCommand, ChecklistCommandBase))
        self.assertTrue(issubclass(ChecklistListCommand, ChecklistCommandBase))
        self.assertTrue(issubclass(ChecklistTemplateListCommand, ChecklistCommandBase))
        self.assertTrue(issubclass(ChecklistTemplateShowCommand, ChecklistCommandBase))
        self.assertTrue(issubclass(ChecklistTemplateApplyCommand, ChecklistCommandBase))
        self.assertTrue(issubclass(ChecklistCloneCommand, ChecklistCommandBase))

    @patch("clickup_framework.commands.checklist_commands.ClickUpClient")
    @patch("clickup_framework.commands.checklist_commands.get_context_manager")
    def test_checklist_create_wrapper_uses_command_class(self, mock_get_context_manager, mock_client_cls):
        mock_get_context_manager.return_value = self._mock_context()
        mock_client_cls.return_value = Mock()
        args = Namespace(task_id="task-1", name="Checklist", verbose=False, colorize=None)

        with patch.object(ChecklistCreateCommand, "execute", return_value=None) as mock_execute:
            checklist_create_command(args)

        mock_execute.assert_called_once()

    @patch("clickup_framework.commands.checklist_commands.ClickUpClient")
    @patch("clickup_framework.commands.checklist_commands.get_context_manager")
    def test_checklist_delete_wrapper_uses_command_class(self, mock_get_context_manager, mock_client_cls):
        mock_get_context_manager.return_value = self._mock_context()
        mock_client_cls.return_value = Mock()
        args = Namespace(checklist_id="1", task="task-1", force=True, colorize=None)

        with patch.object(ChecklistDeleteCommand, "execute", return_value=None) as mock_execute:
            checklist_delete_command(args)

        mock_execute.assert_called_once()

    @patch("clickup_framework.commands.checklist_commands.ClickUpClient")
    @patch("clickup_framework.commands.checklist_commands.get_context_manager")
    def test_checklist_update_wrapper_uses_command_class(self, mock_get_context_manager, mock_client_cls):
        mock_get_context_manager.return_value = self._mock_context()
        mock_client_cls.return_value = Mock()
        args = Namespace(checklist_id="1", task="task-1", name="Renamed", position=None, verbose=False, colorize=None)

        with patch.object(ChecklistUpdateCommand, "execute", return_value=None) as mock_execute:
            checklist_update_command(args)

        mock_execute.assert_called_once()

    @patch("clickup_framework.commands.checklist_commands.ClickUpClient")
    @patch("clickup_framework.commands.checklist_commands.get_context_manager")
    def test_checklist_item_add_wrapper_uses_command_class(self, mock_get_context_manager, mock_client_cls):
        mock_get_context_manager.return_value = self._mock_context()
        mock_client_cls.return_value = Mock()
        args = Namespace(checklist_id="1", task="task-1", name="Item", assignee=None, verbose=False, colorize=None)

        with patch.object(ChecklistItemAddCommand, "execute", return_value=None) as mock_execute:
            checklist_item_add_command(args)

        mock_execute.assert_called_once()

    @patch("clickup_framework.commands.checklist_commands.ClickUpClient")
    @patch("clickup_framework.commands.checklist_commands.get_context_manager")
    def test_checklist_item_update_wrapper_uses_command_class(self, mock_get_context_manager, mock_client_cls):
        mock_get_context_manager.return_value = self._mock_context()
        mock_client_cls.return_value = Mock()
        args = Namespace(
            checklist_id="1",
            item_id="1",
            task="task-1",
            name="Item",
            assignee=None,
            resolved=None,
            parent=None,
            verbose=False,
            colorize=None,
        )

        with patch.object(ChecklistItemUpdateCommand, "execute", return_value=None) as mock_execute:
            checklist_item_update_command(args)

        mock_execute.assert_called_once()

    @patch("clickup_framework.commands.checklist_commands.ClickUpClient")
    @patch("clickup_framework.commands.checklist_commands.get_context_manager")
    def test_checklist_item_delete_wrapper_uses_command_class(self, mock_get_context_manager, mock_client_cls):
        mock_get_context_manager.return_value = self._mock_context()
        mock_client_cls.return_value = Mock()
        args = Namespace(checklist_id="1", item_id="1", task="task-1", force=True, colorize=None)

        with patch.object(ChecklistItemDeleteCommand, "execute", return_value=None) as mock_execute:
            checklist_item_delete_command(args)

        mock_execute.assert_called_once()

    @patch("clickup_framework.commands.checklist_commands.ClickUpClient")
    @patch("clickup_framework.commands.checklist_commands.get_context_manager")
    def test_checklist_list_wrapper_uses_command_class(self, mock_get_context_manager, mock_client_cls):
        mock_get_context_manager.return_value = self._mock_context()
        mock_client_cls.return_value = Mock()
        args = Namespace(task_id="task-1", show_ids=False, no_items=False, colorize=None)

        with patch.object(ChecklistListCommand, "execute", return_value=None) as mock_execute:
            checklist_list_command(args)

        mock_execute.assert_called_once()

    @patch("clickup_framework.commands.checklist_commands.ClickUpClient")
    @patch("clickup_framework.commands.checklist_commands.get_context_manager")
    def test_checklist_template_list_wrapper_uses_command_class(self, mock_get_context_manager, mock_client_cls):
        mock_get_context_manager.return_value = self._mock_context()
        mock_client_cls.return_value = Mock()
        args = Namespace(colorize=None)

        with patch.object(ChecklistTemplateListCommand, "execute", return_value=None) as mock_execute:
            checklist_template_list_command(args)

        mock_execute.assert_called_once()

    @patch("clickup_framework.commands.checklist_commands.ClickUpClient")
    @patch("clickup_framework.commands.checklist_commands.get_context_manager")
    def test_checklist_template_show_wrapper_uses_command_class(self, mock_get_context_manager, mock_client_cls):
        mock_get_context_manager.return_value = self._mock_context()
        mock_client_cls.return_value = Mock()
        args = Namespace(template_name="default", json=False, colorize=None)

        with patch.object(ChecklistTemplateShowCommand, "execute", return_value=None) as mock_execute:
            checklist_template_show_command(args)

        mock_execute.assert_called_once()

    @patch("clickup_framework.commands.checklist_commands.ClickUpClient")
    @patch("clickup_framework.commands.checklist_commands.get_context_manager")
    def test_checklist_template_apply_wrapper_uses_command_class(self, mock_get_context_manager, mock_client_cls):
        mock_get_context_manager.return_value = self._mock_context()
        mock_client_cls.return_value = Mock()
        args = Namespace(task_id="task-1", template_name="default", verbose=False, colorize=None)

        with patch.object(ChecklistTemplateApplyCommand, "execute", return_value=None) as mock_execute:
            checklist_template_apply_command(args)

        mock_execute.assert_called_once()

    @patch("clickup_framework.commands.checklist_commands.ClickUpClient")
    @patch("clickup_framework.commands.checklist_commands.get_context_manager")
    def test_checklist_clone_wrapper_uses_command_class(self, mock_get_context_manager, mock_client_cls):
        mock_get_context_manager.return_value = self._mock_context()
        mock_client_cls.return_value = Mock()
        args = Namespace(source_task_id="task-1", target_task_id="task-2", verbose=False, colorize=None)

        with patch.object(ChecklistCloneCommand, "execute", return_value=None) as mock_execute:
            checklist_clone_command(args)

        mock_execute.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)
