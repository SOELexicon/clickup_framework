"""Tests for overflow workflow data models."""

import unittest
from datetime import datetime
from clickup_framework.git.overflow import (
    WorkflowType,
    OverflowContext,
    CommitResult,
    ClickUpUpdate,
    WorkflowResult,
    execute_overflow_workflow,
)


class TestWorkflowType(unittest.TestCase):
    """Tests for WorkflowType enum."""

    def test_workflow_types_exist(self):
        """Test that all workflow types are defined."""
        self.assertEqual(WorkflowType.DIRECT_COMMIT.value, 0)
        self.assertEqual(WorkflowType.PULL_REQUEST.value, 1)
        self.assertEqual(WorkflowType.WIP_BRANCH.value, 2)
        self.assertEqual(WorkflowType.HOTFIX.value, 3)
        self.assertEqual(WorkflowType.MERGE_COMPLETE.value, 4)


class TestOverflowContext(unittest.TestCase):
    """Tests for OverflowContext dataclass."""

    def test_minimal_context(self):
        """Test creating context with minimal required fields."""
        context = OverflowContext(
            task_id="86c6fnr3q",
            task_url="https://app.clickup.com/t/86c6fnr3q"
        )

        self.assertEqual(context.task_id, "86c6fnr3q")
        self.assertEqual(context.task_url, "https://app.clickup.com/t/86c6fnr3q")
        self.assertEqual(context.repo_path, ".")
        self.assertEqual(context.remote, "origin")
        self.assertTrue(context.auto_push)
        self.assertTrue(context.update_clickup)
        self.assertEqual(context.workflow_type, WorkflowType.DIRECT_COMMIT)
        self.assertFalse(context.dry_run)

    def test_full_context(self):
        """Test creating context with all fields."""
        context = OverflowContext(
            task_id="86c6fnr3q",
            task_url="https://app.clickup.com/t/86c6fnr3q",
            task_name="Test Task",
            repo_path="/path/to/repo",
            branch="feature/test",
            commit_message="Test commit",
            remote="upstream",
            remote_url="https://github.com/owner/repo.git",
            workflow_type=WorkflowType.PULL_REQUEST,
            auto_push=False,
            update_clickup=False,
            assignees=["user1", "user2"],
            tags=["bug", "urgent"],
            priority="high",
            status="in progress",
            dry_run=True
        )

        self.assertEqual(context.task_id, "86c6fnr3q")
        self.assertEqual(context.task_name, "Test Task")
        self.assertEqual(context.repo_path, "/path/to/repo")
        self.assertEqual(context.branch, "feature/test")
        self.assertEqual(context.workflow_type, WorkflowType.PULL_REQUEST)
        self.assertFalse(context.auto_push)
        self.assertTrue(context.dry_run)
        self.assertEqual(len(context.assignees), 2)
        self.assertEqual(len(context.tags), 2)

    def test_timestamp_auto_generated(self):
        """Test that timestamp is automatically generated."""
        before = datetime.now()
        context = OverflowContext(
            task_id="test",
            task_url="https://test.com"
        )
        after = datetime.now()

        self.assertGreaterEqual(context.timestamp, before)
        self.assertLessEqual(context.timestamp, after)


class TestCommitResult(unittest.TestCase):
    """Tests for CommitResult dataclass."""

    def test_minimal_commit_result(self):
        """Test creating commit result with minimal fields."""
        result = CommitResult(
            commit_sha="abc123def456789",
            commit_sha_short="abc123",
            commit_message="Test commit"
        )

        self.assertEqual(result.commit_sha, "abc123def456789")
        self.assertEqual(result.commit_sha_short, "abc123")
        self.assertEqual(result.commit_message, "Test commit")
        self.assertEqual(len(result.files_changed), 0)
        self.assertEqual(result.files_changed_count, 0)
        self.assertEqual(result.additions, 0)
        self.assertEqual(result.deletions, 0)
        self.assertFalse(result.pushed)
        self.assertIsNone(result.push_error)

    def test_full_commit_result(self):
        """Test creating commit result with all fields."""
        result = CommitResult(
            commit_sha="abc123def456789",
            commit_sha_short="abc123",
            commit_message="Test commit",
            commit_url="https://github.com/owner/repo/commit/abc123",
            author_name="John Doe",
            author_email="john@example.com",
            files_changed=["file1.py", "file2.py"],
            files_changed_count=2,
            additions=50,
            deletions=20,
            branch="main",
            remote_url="https://github.com/owner/repo.git",
            pushed=True
        )

        self.assertEqual(result.commit_url, "https://github.com/owner/repo/commit/abc123")
        self.assertEqual(result.author_name, "John Doe")
        self.assertEqual(result.files_changed_count, 2)
        self.assertEqual(result.additions, 50)
        self.assertEqual(result.deletions, 20)
        self.assertTrue(result.pushed)


class TestClickUpUpdate(unittest.TestCase):
    """Tests for ClickUpUpdate dataclass."""

    def test_minimal_update(self):
        """Test creating update with minimal fields."""
        update = ClickUpUpdate(task_id="86c6fnr3q")

        self.assertEqual(update.task_id, "86c6fnr3q")
        self.assertIsNone(update.comment)
        self.assertIsNone(update.status)
        self.assertIsNone(update.priority)
        self.assertFalse(update.applied)
        self.assertIsNone(update.error)

    def test_comment_only_update(self):
        """Test creating update with just a comment."""
        update = ClickUpUpdate(
            task_id="86c6fnr3q",
            comment="Test comment"
        )

        self.assertEqual(update.comment, "Test comment")

    def test_full_update(self):
        """Test creating update with all fields."""
        update = ClickUpUpdate(
            task_id="86c6fnr3q",
            comment="Test comment",
            status="in progress",
            priority="high",
            assignees_add=["user1"],
            assignees_remove=["user2"],
            tags_add=["bug"],
            tags_remove=["wontfix"],
            links=[{"url": "https://example.com", "title": "Test"}],
            custom_fields={"field1": "value1"},
            applied=True
        )

        self.assertEqual(update.status, "in progress")
        self.assertEqual(update.priority, "high")
        self.assertEqual(len(update.assignees_add), 1)
        self.assertEqual(len(update.tags_add), 1)
        self.assertEqual(len(update.links), 1)
        self.assertTrue(update.applied)


class TestWorkflowResult(unittest.TestCase):
    """Tests for WorkflowResult dataclass."""

    def test_success_result(self):
        """Test creating successful workflow result."""
        commit_result = CommitResult(
            commit_sha="abc123",
            commit_sha_short="abc123",
            commit_message="Test"
        )

        result = WorkflowResult(
            success=True,
            workflow_type=WorkflowType.DIRECT_COMMIT,
            commit_result=commit_result,
            duration_seconds=2.5
        )

        self.assertTrue(result.success)
        self.assertEqual(result.workflow_type, WorkflowType.DIRECT_COMMIT)
        self.assertIsNotNone(result.commit_result)
        self.assertIsNone(result.error)
        self.assertEqual(result.duration_seconds, 2.5)

    def test_failure_result(self):
        """Test creating failed workflow result."""
        result = WorkflowResult(
            success=False,
            workflow_type=WorkflowType.DIRECT_COMMIT,
            error="Test error message"
        )

        self.assertFalse(result.success)
        self.assertEqual(result.error, "Test error message")
        self.assertIsNone(result.commit_result)

    def test_result_with_warnings(self):
        """Test result with warnings."""
        result = WorkflowResult(
            success=True,
            workflow_type=WorkflowType.DIRECT_COMMIT,
            warnings=["Warning 1", "Warning 2"]
        )

        self.assertTrue(result.success)
        self.assertEqual(len(result.warnings), 2)

    def test_result_with_metadata(self):
        """Test result with metadata."""
        result = WorkflowResult(
            success=True,
            workflow_type=WorkflowType.DIRECT_COMMIT,
            metadata={"key1": "value1", "key2": 123}
        )

        self.assertEqual(result.metadata["key1"], "value1")
        self.assertEqual(result.metadata["key2"], 123)


class TestExecuteOverflowWorkflow(unittest.TestCase):
    """Tests for execute_overflow_workflow function."""

    def test_dry_run_workflow_0(self):
        """Test Workflow 0 in dry run mode."""
        context = OverflowContext(
            task_id="test123",
            task_url="https://app.clickup.com/t/test123",
            commit_message="Test commit",
            dry_run=True
        )

        result = execute_overflow_workflow(context)

        self.assertTrue(result.success)
        self.assertEqual(result.workflow_type, WorkflowType.DIRECT_COMMIT)
        self.assertIn("DRY RUN", result.warnings[0])
        self.assertTrue(result.metadata.get("dry_run"))

    def test_workflow_0_missing_commit_message(self):
        """Test that Workflow 0 fails without commit message."""
        context = OverflowContext(
            task_id="test123",
            task_url="https://app.clickup.com/t/test123",
            commit_message=""  # Empty message
        )

        result = execute_overflow_workflow(context)

        self.assertFalse(result.success)
        self.assertEqual(result.error, "Commit message is required")

    def test_unimplemented_workflow_types(self):
        """Test that non-Workflow-0 types return not implemented."""
        for workflow_type in [WorkflowType.PULL_REQUEST, WorkflowType.WIP_BRANCH,
                              WorkflowType.HOTFIX, WorkflowType.MERGE_COMPLETE]:
            context = OverflowContext(
                task_id="test123",
                task_url="https://app.clickup.com/t/test123",
                commit_message="Test",
                workflow_type=workflow_type
            )

            result = execute_overflow_workflow(context)

            self.assertFalse(result.success)
            self.assertIn("not yet implemented", result.error)


if __name__ == '__main__':
    unittest.main()
