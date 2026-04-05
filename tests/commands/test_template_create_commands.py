"""Regression tests for folder/list create-from-template command support."""

import unittest
from argparse import Namespace
from unittest.mock import Mock, patch

from clickup_framework.apis.folders import FoldersAPI
from clickup_framework.apis.lists import ListsAPI
from clickup_framework.commands.base_command import BaseCommand
from clickup_framework.commands.folder_commands import (
    FolderCreateFromTemplateCommand,
    folder_create_from_template_command,
)
from clickup_framework.commands.list_commands import (
    ListCreateFromTemplateCommand,
    list_create_from_template_command,
)


class TestTemplateCreateCommands(unittest.TestCase):
    """Verify template endpoint wiring and CLI wrappers."""

    def _mock_context(self):
        context = Mock()
        context.get_ansi_output.return_value = False
        return context

    def test_api_template_methods_use_documented_endpoints(self):
        mock_client = Mock()
        lists_api = ListsAPI(mock_client)
        folders_api = FoldersAPI(mock_client)

        lists_api.create_list_from_template_in_folder("folder-1", "tpl-list", name="Sprint")
        mock_client._request.assert_called_with(
            "POST",
            "folder/folder-1/list",
            params={"template_id": "tpl-list"},
            json={"name": "Sprint"},
        )

        lists_api.create_list_from_template_in_space("space-1", "tpl-list", name="Sprint")
        mock_client._request.assert_called_with(
            "POST",
            "space/space-1/list",
            params={"template_id": "tpl-list"},
            json={"name": "Sprint"},
        )

        folders_api.create_folder_from_template("team-1", "tpl-folder", name="Projects")
        mock_client._request.assert_called_with(
            "POST",
            "team/team-1/folder",
            params={"template_id": "tpl-folder"},
            json={"name": "Projects"},
        )

    @patch("clickup_framework.commands.base_command.ClickUpClient")
    @patch("clickup_framework.commands.base_command.get_context_manager")
    def test_list_create_from_template_uses_folder_target(
        self,
        mock_get_context_manager,
        mock_client_cls,
    ):
        mock_get_context_manager.return_value = self._mock_context()
        mock_client = Mock()
        mock_client.create_list_from_template_in_folder.return_value = {"id": "list-123"}
        mock_client_cls.return_value = mock_client
        args = Namespace(
            folder_id="current",
            space_id=None,
            template_id="tpl-list",
            name="Sprint 24",
            content="Backlog",
            due_date=None,
            priority="high",
            assignee=123,
            status="to do",
            verbose=False,
            colorize=None,
        )

        command = ListCreateFromTemplateCommand(args, command_name="list-mgmt")
        with patch.object(command, "resolve_id", return_value="folder-123") as mock_resolve:
            command.execute()

        mock_resolve.assert_called_once_with("folder", "current")
        mock_client.create_list_from_template_in_folder.assert_called_once_with(
            "folder-123",
            "tpl-list",
            name="Sprint 24",
            content="Backlog",
            priority=2,
            assignee=123,
            status="to do",
        )

    @patch("clickup_framework.commands.base_command.ClickUpClient")
    @patch("clickup_framework.commands.base_command.get_context_manager")
    def test_folder_create_from_template_uses_workspace_target(
        self,
        mock_get_context_manager,
        mock_client_cls,
    ):
        mock_get_context_manager.return_value = self._mock_context()
        mock_client = Mock()
        mock_client.create_folder_from_template.return_value = {"id": "folder-123"}
        mock_client_cls.return_value = mock_client
        args = Namespace(
            team_id="current",
            template_id="tpl-folder",
            name="Q1 Projects",
            verbose=False,
            colorize=None,
        )

        command = FolderCreateFromTemplateCommand(args, command_name="folder")
        with patch.object(command, "resolve_id", return_value="team-123") as mock_resolve:
            command.execute()

        mock_resolve.assert_called_once_with("workspace", "current")
        mock_client.create_folder_from_template.assert_called_once_with(
            "team-123",
            "tpl-folder",
            name="Q1 Projects",
        )

    @patch("clickup_framework.commands.base_command.ClickUpClient")
    @patch("clickup_framework.commands.base_command.get_context_manager")
    @patch("clickup_framework.commands.folder_commands.FolderCreateFromTemplateCommand.execute")
    def test_folder_template_wrapper_uses_command_class(
        self,
        mock_execute,
        mock_get_context_manager,
        mock_client_cls,
    ):
        mock_get_context_manager.return_value = self._mock_context()
        mock_client_cls.return_value = Mock()
        args = Namespace(team_id="team-1", template_id="tpl", name="Folder", verbose=False, colorize=None)
        folder_create_from_template_command(args)
        mock_execute.assert_called_once()

    @patch("clickup_framework.commands.base_command.ClickUpClient")
    @patch("clickup_framework.commands.base_command.get_context_manager")
    @patch("clickup_framework.commands.list_commands.ListCreateFromTemplateCommand.execute")
    def test_list_template_wrapper_uses_command_class(
        self,
        mock_execute,
        mock_get_context_manager,
        mock_client_cls,
    ):
        mock_get_context_manager.return_value = self._mock_context()
        mock_client_cls.return_value = Mock()
        args = Namespace(
            folder_id="folder-1",
            space_id=None,
            template_id="tpl",
            name="List",
            content=None,
            due_date=None,
            priority=None,
            assignee=None,
            status=None,
            verbose=False,
            colorize=None,
        )
        list_create_from_template_command(args)
        mock_execute.assert_called_once()

    def test_template_command_classes_inherit_base_command(self):
        self.assertTrue(issubclass(ListCreateFromTemplateCommand, BaseCommand))
        self.assertTrue(issubclass(FolderCreateFromTemplateCommand, BaseCommand))


if __name__ == "__main__":
    unittest.main(verbosity=2)
