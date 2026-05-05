"""Regression tests for incremental BaseCommand migration inside task_commands.py."""

import unittest
from argparse import Namespace
from unittest.mock import Mock, patch

from clickup_framework.commands.base_command import BaseCommand
from clickup_framework.commands.task_commands import (
    TaskAddDependencyCommand,
    TaskAddLinkCommand,
    TaskAssignCommand,
    TaskCommandBase,
    TaskCreateCommand,
    TaskDeleteCommand,
    TaskMoveCommand,
    TaskRemoveDependencyCommand,
    TaskRemoveLinkCommand,
    TaskSetStatusCommand,
    TaskSetPriorityCommand,
    TaskSetTagsCommand,
    TaskUnassignCommand,
    TaskUpdateCommand,
    resolve_task_type,
    _task_create_impl,
    _task_update_impl,
    task_add_dependency_command,
    task_add_link_command,
    task_assign_command,
    task_create_command,
    task_delete_command,
    task_move_command,
    task_remove_dependency_command,
    task_remove_link_command,
    task_set_status_command,
    task_set_priority_command,
    task_set_tags_command,
    task_unassign_command,
    task_update_command,
)


class TestTaskCommandMigration(unittest.TestCase):
    """Verify migrated task command wrappers now execute through BaseCommand subclasses."""

    def _mock_context(self):
        context = Mock()
        context.get_ansi_output.return_value = False
        context.get_current_workspace.return_value = "team-1"
        context.get_default_assignee.return_value = None
        context.resolve_id.side_effect = lambda type, id: id
        return context

    def test_task_command_classes_inherit_base_command(self):
        self.assertTrue(issubclass(TaskCommandBase, BaseCommand))
        self.assertTrue(issubclass(TaskCreateCommand, TaskCommandBase))
        self.assertTrue(issubclass(TaskUpdateCommand, TaskCommandBase))
        self.assertTrue(issubclass(TaskDeleteCommand, TaskCommandBase))
        self.assertTrue(issubclass(TaskAddDependencyCommand, TaskCommandBase))
        self.assertTrue(issubclass(TaskRemoveDependencyCommand, TaskCommandBase))
        self.assertTrue(issubclass(TaskAddLinkCommand, TaskCommandBase))
        self.assertTrue(issubclass(TaskRemoveLinkCommand, TaskCommandBase))
        self.assertTrue(issubclass(TaskAssignCommand, TaskCommandBase))
        self.assertTrue(issubclass(TaskUnassignCommand, TaskCommandBase))
        self.assertTrue(issubclass(TaskSetStatusCommand, TaskCommandBase))
        self.assertTrue(issubclass(TaskSetPriorityCommand, TaskCommandBase))
        self.assertTrue(issubclass(TaskSetTagsCommand, TaskCommandBase))
        self.assertTrue(issubclass(TaskMoveCommand, TaskCommandBase))

    @patch("clickup_framework.commands.task_commands.ClickUpClient")
    def test_resolve_task_type_success(self, mock_client_cls):
        mock_client = mock_client_cls.return_value
        mock_client.get_custom_task_types.return_value = {
            "custom_items": [
                {"id": 100, "name": "Feature"},
                {"id": 101, "name": "Bug"}
            ]
        }
        
        type_id = resolve_task_type(mock_client, "team-1", "Feature")
        self.assertEqual(type_id, 100)
        
        type_id = resolve_task_type(mock_client, "team-1", "feature") # Case-insensitive
        self.assertEqual(type_id, 100)

    @patch("clickup_framework.commands.task_commands.ClickUpClient")
    def test_resolve_task_type_standard_task(self, mock_client_cls):
        mock_client = mock_client_cls.return_value
        type_id = resolve_task_type(mock_client, "team-1", "Task")
        self.assertEqual(type_id, 1)

    @patch("clickup_framework.commands.task_commands.resolve_task_type")
    @patch("clickup_framework.commands.task_commands.ANSIAnimations")
    @patch("clickup_framework.commands.task_commands.ClickUpClient")
    @patch("clickup_framework.commands.task_commands.get_context_manager")
    def test_task_create_with_type(self, mock_get_context_manager, mock_client_cls, mock_ansi, mock_resolve):
        mock_get_context_manager.return_value = self._mock_context()
        mock_client = mock_client_cls.return_value
        mock_resolve.return_value = 100
        mock_ansi.success_message.return_value = "Success"
        
        args = Namespace(
            name="New Task",
            list_id="list-1",
            parent=None,
            description=None,
            description_file=None,
            status=None,
            priority=None,
            tags=None,
            assignees=None,
            custom_task_ids=False,
            check_required_custom_fields=None,
            task_type="Feature",
            markdown=True,
            skip_mermaid=False,
            image_cache=None,
            show_tips=False
        )
        
        mock_client.create_task.return_value = {
            "id": "task-1", "name": "New Task", "url": "http://task"
        }
        
        _task_create_impl(args, mock_get_context_manager.return_value, mock_client, False)
        
        mock_client.create_task.assert_called_once()
        kwargs = mock_client.create_task.call_args[1]
        self.assertEqual(kwargs['custom_item_id'], 100)

    @patch("clickup_framework.commands.task_commands.resolve_task_type")
    @patch("clickup_framework.commands.task_commands.ANSIAnimations")
    @patch("clickup_framework.commands.task_commands.ClickUpClient")
    @patch("clickup_framework.commands.task_commands.get_context_manager")
    def test_task_update_with_type(self, mock_get_context_manager, mock_client_cls, mock_ansi, mock_resolve):
        mock_get_context_manager.return_value = self._mock_context()
        mock_client = mock_client_cls.return_value
        mock_resolve.return_value = 100
        mock_ansi.success_message.return_value = "Success"
        
        args = Namespace(
            task_id="task-1",
            name=None,
            description=None,
            description_file=None,
            status=None,
            priority=None,
            parent=None,
            add_tags=None,
            remove_tags=None,
            task_type="Feature",
            markdown=True,
            skip_mermaid=False,
            image_cache=None,
            func=Mock(__name__="task_update")
        )
        
        mock_client.get_task.return_value = {"id": "task-1", "team_id": "team-1"}
        mock_client.update_task.return_value = {"id": "task-1", "name": "Task"}
        
        _task_update_impl(args, mock_get_context_manager.return_value, mock_client, False)
        
        mock_client.update_task.assert_called_once()
        kwargs = mock_client.update_task.call_args[1]
        self.assertEqual(kwargs['custom_item_id'], 100)

    @patch("clickup_framework.commands.task_commands.ClickUpClient")
    @patch("clickup_framework.commands.task_commands.get_context_manager")
    def test_task_create_wrapper_uses_command_class(
        self,
        mock_get_context_manager,
        mock_client_cls,
    ):
        mock_get_context_manager.return_value = self._mock_context()
        mock_client_cls.return_value = Mock()
        args = Namespace(
            name="Task name",
            list_id="list-1",
            parent=None,
            colorize=None,
        )

        with patch.object(TaskCreateCommand, "execute", return_value=None) as mock_execute:
            task_create_command(args)

        mock_execute.assert_called_once()

    @patch("clickup_framework.commands.task_commands.ClickUpClient")
    @patch("clickup_framework.commands.task_commands.get_context_manager")
    def test_task_assign_wrapper_uses_command_class(
        self,
        mock_get_context_manager,
        mock_client_cls,
    ):
        mock_get_context_manager.return_value = self._mock_context()
        mock_client_cls.return_value = Mock()
        args = Namespace(task_id="task-1", assignee_ids=["user-1"], colorize=None)

        with patch.object(TaskAssignCommand, "execute", return_value=None) as mock_execute:
            task_assign_command(args)

        mock_execute.assert_called_once()

    @patch("clickup_framework.commands.task_commands.ClickUpClient")
    @patch("clickup_framework.commands.task_commands.get_context_manager")
    def test_task_unassign_wrapper_uses_command_class(
        self,
        mock_get_context_manager,
        mock_client_cls,
    ):
        mock_get_context_manager.return_value = self._mock_context()
        mock_client_cls.return_value = Mock()
        args = Namespace(task_id="task-1", assignee_ids=["user-1"], colorize=None)

        with patch.object(TaskUnassignCommand, "execute", return_value=None) as mock_execute:
            task_unassign_command(args)

        mock_execute.assert_called_once()

    @patch("clickup_framework.commands.task_commands.ClickUpClient")
    @patch("clickup_framework.commands.task_commands.get_context_manager")
    def test_task_set_status_wrapper_uses_command_class(
        self,
        mock_get_context_manager,
        mock_client_cls,
    ):
        mock_get_context_manager.return_value = self._mock_context()
        mock_client_cls.return_value = Mock()
        args = Namespace(
            task_ids=["task-1"],
            status="open",
            no_parent_update=False,
            update_parent=False,
            force=False,
            verify_checklist=False,
            colorize=None,
        )

        with patch.object(TaskSetStatusCommand, "execute", return_value=None) as mock_execute:
            task_set_status_command(args)

        mock_execute.assert_called_once()

    @patch("clickup_framework.commands.task_commands.ClickUpClient")
    @patch("clickup_framework.commands.task_commands.get_context_manager")
    def test_task_update_wrapper_uses_command_class(
        self,
        mock_get_context_manager,
        mock_client_cls,
    ):
        mock_get_context_manager.return_value = self._mock_context()
        mock_client_cls.return_value = Mock()
        args = Namespace(task_id="task-1", name="Renamed", colorize=None)

        with patch.object(TaskUpdateCommand, "execute", return_value=None) as mock_execute:
            task_update_command(args)

        mock_execute.assert_called_once()

    @patch("clickup_framework.commands.task_commands.ClickUpClient")
    @patch("clickup_framework.commands.task_commands.get_context_manager")
    def test_task_add_dependency_wrapper_uses_command_class(
        self,
        mock_get_context_manager,
        mock_client_cls,
    ):
        mock_get_context_manager.return_value = self._mock_context()
        mock_client_cls.return_value = Mock()
        args = Namespace(task_id="task-1", waiting_on="task-2", blocking=None, colorize=None)

        with patch.object(TaskAddDependencyCommand, "execute", return_value=None) as mock_execute:
            task_add_dependency_command(args)

        mock_execute.assert_called_once()

    @patch("clickup_framework.commands.task_commands.ClickUpClient")
    @patch("clickup_framework.commands.task_commands.get_context_manager")
    def test_task_remove_dependency_wrapper_uses_command_class(
        self,
        mock_get_context_manager,
        mock_client_cls,
    ):
        mock_get_context_manager.return_value = self._mock_context()
        mock_client_cls.return_value = Mock()
        args = Namespace(task_id="task-1", waiting_on="task-2", blocking=None, colorize=None)

        with patch.object(TaskRemoveDependencyCommand, "execute", return_value=None) as mock_execute:
            task_remove_dependency_command(args)

        mock_execute.assert_called_once()

    @patch("clickup_framework.commands.task_commands.ClickUpClient")
    @patch("clickup_framework.commands.task_commands.get_context_manager")
    def test_task_add_link_wrapper_uses_command_class(
        self,
        mock_get_context_manager,
        mock_client_cls,
    ):
        mock_get_context_manager.return_value = self._mock_context()
        mock_client_cls.return_value = Mock()
        args = Namespace(task_id="task-1", linked_task_id="task-2", verbose=False, colorize=None)

        with patch.object(TaskAddLinkCommand, "execute", return_value=None) as mock_execute:
            task_add_link_command(args)

        mock_execute.assert_called_once()

    @patch("clickup_framework.commands.task_commands.ClickUpClient")
    @patch("clickup_framework.commands.task_commands.get_context_manager")
    def test_task_remove_link_wrapper_uses_command_class(
        self,
        mock_get_context_manager,
        mock_client_cls,
    ):
        mock_get_context_manager.return_value = self._mock_context()
        mock_client_cls.return_value = Mock()
        args = Namespace(task_id="task-1", linked_task_id="task-2", colorize=None)

        with patch.object(TaskRemoveLinkCommand, "execute", return_value=None) as mock_execute:
            task_remove_link_command(args)

        mock_execute.assert_called_once()

    @patch("clickup_framework.commands.task_commands.ClickUpClient")
    @patch("clickup_framework.commands.task_commands.get_context_manager")
    def test_task_delete_wrapper_uses_command_class(
        self,
        mock_get_context_manager,
        mock_client_cls,
    ):
        mock_get_context_manager.return_value = self._mock_context()
        mock_client_cls.return_value = Mock()
        args = Namespace(task_ids=["task-1"], force=True, colorize=None)

        with patch.object(TaskDeleteCommand, "execute", return_value=None) as mock_execute:
            task_delete_command(args)

        mock_execute.assert_called_once()

    @patch("clickup_framework.commands.task_commands.ClickUpClient")
    @patch("clickup_framework.commands.task_commands.get_context_manager")
    def test_task_set_priority_wrapper_uses_command_class(
        self,
        mock_get_context_manager,
        mock_client_cls,
    ):
        mock_get_context_manager.return_value = self._mock_context()
        mock_client_cls.return_value = Mock()
        args = Namespace(task_id="task-1", priority="high", colorize=None)

        with patch.object(TaskSetPriorityCommand, "execute", return_value=None) as mock_execute:
            task_set_priority_command(args)

        mock_execute.assert_called_once()

    @patch("clickup_framework.commands.task_commands.ClickUpClient")
    @patch("clickup_framework.commands.task_commands.get_context_manager")
    def test_task_set_tags_wrapper_uses_command_class(
        self,
        mock_get_context_manager,
        mock_client_cls,
    ):
        mock_get_context_manager.return_value = self._mock_context()
        mock_client_cls.return_value = Mock()
        args = Namespace(
            task_id=["task-1"],
            add=["bug"],
            remove=None,
            set=None,
            colorize=None,
        )

        with patch.object(TaskSetTagsCommand, "execute", return_value=None) as mock_execute:
            task_set_tags_command(args)

        mock_execute.assert_called_once()

    @patch("clickup_framework.commands.task_commands.ClickUpClient")
    @patch("clickup_framework.commands.task_commands.get_context_manager")
    def test_task_move_wrapper_uses_command_class(
        self,
        mock_get_context_manager,
        mock_client_cls,
    ):
        mock_get_context_manager.return_value = self._mock_context()
        mock_client_cls.return_value = Mock()
        args = Namespace(
            task_ids=["task-1"],
            list_id="list-1",
            parent=None,
            force=True,
            colorize=None,
        )

        with patch.object(TaskMoveCommand, "execute", return_value=None) as mock_execute:
            task_move_command(args)

        mock_execute.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)
