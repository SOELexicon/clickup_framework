"""Integration tests for git overflow CLI command."""

import unittest
from unittest.mock import Mock, patch, MagicMock
from argparse import Namespace
from clickup_framework.commands.git_overflow_command import overflow_command
from clickup_framework.git import WorkflowType, WorkflowResult


class TestOverflowCommandIntegration(unittest.TestCase):
    """Integration tests for overflow command."""

    @patch('clickup_framework.commands.git_overflow_command.get_context_manager')
    @patch('clickup_framework.commands.git_overflow_command.execute_overflow_workflow')
    @patch('clickup_framework.commands.git_overflow_command.load_config')
    def test_overflow_with_current_task(self, mock_load_config, mock_execute, mock_get_context):
        """Test overflow command using current task from context."""
        # Setup mocks
        mock_context_mgr = Mock()
        mock_context_mgr.get_current_task.return_value = "task123"
        mock_get_context.return_value = mock_context_mgr

        mock_config = Mock()
        mock_load_config.return_value = mock_config

        mock_result = WorkflowResult(
            success=True,
            workflow_type=WorkflowType.DIRECT_COMMIT,
            duration_seconds=1.5
        )
        mock_execute.return_value = mock_result

        # Create args
        args = Namespace(
            message="Test commit",
            task=None,  # Use current task
            type='0',
            no_push=False,
            no_clickup=False,
            dry_run=True,
            status=None,
            priority=None,
            tags=None,
            verbose=False
        )

        # Execute command
        overflow_command(args)

        # Verify execute_overflow_workflow was called
        mock_execute.assert_called_once()
        call_args = mock_execute.call_args

        # Check context passed to workflow
        context = call_args[0][0]
        self.assertEqual(context.task_id, "task123")
        self.assertEqual(context.commit_message, "Test commit")
        self.assertTrue(context.dry_run)

    @patch('clickup_framework.commands.git_overflow_command.get_context_manager')
    @patch('clickup_framework.commands.git_overflow_command.execute_overflow_workflow')
    @patch('clickup_framework.commands.git_overflow_command.load_config')
    def test_overflow_with_explicit_task(self, mock_load_config, mock_execute, mock_get_context):
        """Test overflow command with explicitly specified task."""
        mock_config = Mock()
        mock_load_config.return_value = mock_config

        mock_result = WorkflowResult(
            success=True,
            workflow_type=WorkflowType.DIRECT_COMMIT,
            duration_seconds=1.0
        )
        mock_execute.return_value = mock_result

        args = Namespace(
            message="Explicit task commit",
            task="explicit_task_id",
            type='direct',
            no_push=False,
            no_clickup=False,
            dry_run=True,
            status=None,
            priority=None,
            tags=None,
            verbose=False
        )

        overflow_command(args)

        # Verify execute_overflow_workflow was called with correct task
        call_args = mock_execute.call_args
        context = call_args[0][0]
        self.assertEqual(context.task_id, "explicit_task_id")

    @patch('clickup_framework.commands.git_overflow_command.get_context_manager')
    @patch('clickup_framework.commands.git_overflow_command.load_config')
    def test_overflow_no_task_exits(self, mock_load_config, mock_get_context):
        """Test that command exits when no task is available."""
        # Setup mocks - no current task
        mock_context_mgr = Mock()
        mock_context_mgr.get_current_task.return_value = None
        mock_get_context.return_value = mock_context_mgr

        mock_config = Mock()
        mock_load_config.return_value = mock_config

        args = Namespace(
            message="Test commit",
            task=None,  # No task provided
            type='0',
            no_push=False,
            no_clickup=False,
            dry_run=True,
            status=None,
            priority=None,
            tags=None,
            verbose=False
        )

        # Should exit with error
        with self.assertRaises(SystemExit) as ctx:
            overflow_command(args)

        self.assertEqual(ctx.exception.code, 1)

    @patch('clickup_framework.commands.git_overflow_command.get_context_manager')
    @patch('clickup_framework.commands.git_overflow_command.execute_overflow_workflow')
    @patch('clickup_framework.commands.git_overflow_command.load_config')
    def test_overflow_with_no_push_flag(self, mock_load_config, mock_execute, mock_get_context):
        """Test that --no-push flag disables pushing."""
        mock_context_mgr = Mock()
        mock_context_mgr.get_current_task.return_value = "task123"
        mock_get_context.return_value = mock_context_mgr

        mock_config = Mock()
        mock_load_config.return_value = mock_config

        mock_result = WorkflowResult(
            success=True,
            workflow_type=WorkflowType.DIRECT_COMMIT,
            duration_seconds=1.0
        )
        mock_execute.return_value = mock_result

        args = Namespace(
            message="Test commit",
            task=None,
            type='0',
            no_push=True,  # No push flag
            no_clickup=False,
            dry_run=True,
            status=None,
            priority=None,
            tags=None,
            verbose=False
        )

        overflow_command(args)

        # Check that auto_push is False
        call_args = mock_execute.call_args
        context = call_args[0][0]
        self.assertFalse(context.auto_push)

    @patch('clickup_framework.commands.git_overflow_command.get_context_manager')
    @patch('clickup_framework.commands.git_overflow_command.execute_overflow_workflow')
    @patch('clickup_framework.commands.git_overflow_command.load_config')
    def test_overflow_with_status_and_priority(self, mock_load_config, mock_execute, mock_get_context):
        """Test overflow with status and priority options."""
        mock_context_mgr = Mock()
        mock_context_mgr.get_current_task.return_value = "task123"
        mock_get_context.return_value = mock_context_mgr

        mock_config = Mock()
        mock_load_config.return_value = mock_config

        mock_result = WorkflowResult(
            success=True,
            workflow_type=WorkflowType.DIRECT_COMMIT,
            duration_seconds=1.0
        )
        mock_execute.return_value = mock_result

        args = Namespace(
            message="Test commit",
            task=None,
            type='0',
            no_push=False,
            no_clickup=False,
            dry_run=True,
            status="in progress",
            priority="high",
            tags=["bug", "urgent"],
            verbose=False
        )

        overflow_command(args)

        # Check that status, priority, and tags are passed
        call_args = mock_execute.call_args
        context = call_args[0][0]
        self.assertEqual(context.status, "in progress")
        self.assertEqual(context.priority, "high")
        self.assertEqual(context.tags, ["bug", "urgent"])

    @patch('clickup_framework.commands.git_overflow_command.get_context_manager')
    @patch('clickup_framework.commands.git_overflow_command.execute_overflow_workflow')
    @patch('clickup_framework.commands.git_overflow_command.load_config')
    def test_overflow_unimplemented_workflow_exits(self, mock_load_config, mock_execute, mock_get_context):
        """Test that unimplemented workflow types exit with error."""
        mock_context_mgr = Mock()
        mock_context_mgr.get_current_task.return_value = "task123"
        mock_get_context.return_value = mock_context_mgr

        mock_config = Mock()
        mock_load_config.return_value = mock_config

        args = Namespace(
            message="Test commit",
            task=None,
            type='pr',  # Workflow 1 - not implemented
            no_push=False,
            no_clickup=False,
            dry_run=True,
            status=None,
            priority=None,
            tags=None,
            verbose=False
        )

        # Should exit with error
        with self.assertRaises(SystemExit) as ctx:
            overflow_command(args)

        self.assertEqual(ctx.exception.code, 1)

    @patch('clickup_framework.commands.git_overflow_command.get_context_manager')
    @patch('clickup_framework.commands.git_overflow_command.execute_overflow_workflow')
    @patch('clickup_framework.commands.git_overflow_command.load_config')
    @patch('clickup_framework.commands.git_overflow_command.ClickUpClient')
    def test_overflow_handles_auth_error(self, mock_client_class, mock_load_config, mock_execute, mock_get_context):
        """Test that auth errors are handled gracefully."""
        from clickup_framework.exceptions import ClickUpAuthError

        mock_context_mgr = Mock()
        mock_context_mgr.get_current_task.return_value = "task123"
        mock_get_context.return_value = mock_context_mgr

        mock_config = Mock()
        mock_load_config.return_value = mock_config

        # Client creation fails with auth error
        mock_client_class.side_effect = ClickUpAuthError("Unauthorized")

        mock_result = WorkflowResult(
            success=True,
            workflow_type=WorkflowType.DIRECT_COMMIT,
            duration_seconds=1.0
        )
        mock_execute.return_value = mock_result

        args = Namespace(
            message="Test commit",
            task=None,
            type='0',
            no_push=False,
            no_clickup=False,  # ClickUp requested but will fail
            dry_run=False,  # Not dry run, so client will be created
            status=None,
            priority=None,
            tags=None,
            verbose=False
        )

        # Should continue with Git only (no exception)
        overflow_command(args)

        # Verify that execute was called with update_clickup=False
        call_args = mock_execute.call_args
        context = call_args[0][0]
        self.assertFalse(context.update_clickup)


if __name__ == '__main__':
    unittest.main()
