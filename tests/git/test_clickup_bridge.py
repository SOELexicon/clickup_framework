"""Tests for ClickUp bridge module."""

import unittest
from unittest.mock import Mock, patch, MagicMock
from clickup_framework.git.clickup_bridge import (
    format_commit_comment,
    post_commit_comment,
    link_commit_to_task,
    update_task_status,
    update_task_fields,
    apply_clickup_update,
    ClickUpBridgeError,
)
from clickup_framework.exceptions import ClickUpAPIError, ClickUpRateLimitError


class TestFormatCommitComment(unittest.TestCase):
    """Tests for format_commit_comment function."""

    def test_format_basic_comment(self):
        """Test formatting basic commit comment."""
        comment = format_commit_comment(
            commit_sha_short="abc123",
            commit_message="Add new feature",
            commit_url="https://github.com/owner/repo/commit/abc123"
        )

        self.assertIn("abc123", comment)
        self.assertIn("Add new feature", comment)
        self.assertIn("https://github.com/owner/repo/commit/abc123", comment)
        self.assertIn("✅", comment)  # Check for emoji
        self.assertIn("🔗", comment)  # Check for link emoji

    def test_format_comment_with_stats(self):
        """Test formatting comment with file change statistics."""
        comment = format_commit_comment(
            commit_sha_short="abc123",
            commit_message="Update files",
            commit_url="https://github.com/owner/repo/commit/abc123",
            files_changed=["file1.py", "file2.py"],
            additions=50,
            deletions=20
        )

        self.assertIn("2 files changed", comment)
        self.assertIn("+50", comment)
        self.assertIn("-20", comment)

    def test_format_comment_with_custom_template(self):
        """Test formatting comment with custom template."""
        template = "Commit: {commit_sha_short} - {commit_message}"
        comment = format_commit_comment(
            commit_sha_short="abc123",
            commit_message="Test commit",
            commit_url="https://example.com",
            template=template
        )

        self.assertEqual(comment, "Commit: abc123 - Test commit")

    def test_format_comment_single_file(self):
        """Test that 'file' is singular when only one file changed."""
        comment = format_commit_comment(
            commit_sha_short="abc123",
            commit_message="Update single file",
            commit_url="https://github.com/owner/repo/commit/abc123",
            files_changed=["file1.py"],
            additions=10,
            deletions=5
        )

        self.assertIn("1 file changed", comment)
        self.assertNotIn("files changed", comment)


class TestPostCommitComment(unittest.TestCase):
    """Tests for post_commit_comment function."""

    def test_successful_comment_post(self):
        """Test successful comment posting."""
        mock_client = Mock()
        mock_client.create_task_comment.return_value = {"id": "comment_123"}

        result = post_commit_comment(
            client=mock_client,
            task_id="task_123",
            comment_text="Test comment"
        )

        mock_client.create_task_comment.assert_called_once_with("task_123", "Test comment")
        self.assertEqual(result["id"], "comment_123")

    def test_retry_on_rate_limit(self):
        """Test that function retries on rate limit error."""
        mock_client = Mock()
        # First call raises rate limit, second succeeds
        mock_client.create_task_comment.side_effect = [
            ClickUpRateLimitError("Rate limited"),
            {"id": "comment_123"}
        ]

        with patch('time.sleep'):  # Mock sleep to speed up test
            result = post_commit_comment(
                client=mock_client,
                task_id="task_123",
                comment_text="Test comment",
                retry_count=2
            )

        self.assertEqual(mock_client.create_task_comment.call_count, 2)
        self.assertEqual(result["id"], "comment_123")

    def test_fail_after_retries(self):
        """Test that function raises error after all retries exhausted."""
        mock_client = Mock()
        mock_client.create_task_comment.side_effect = ClickUpAPIError(400, "API Error")

        with patch('time.sleep'):
            with self.assertRaises(ClickUpBridgeError) as ctx:
                post_commit_comment(
                    client=mock_client,
                    task_id="task_123",
                    comment_text="Test comment",
                    retry_count=2
                )

        self.assertIn("Failed to post comment", str(ctx.exception))


class TestLinkCommitToTask(unittest.TestCase):
    """Tests for link_commit_to_task function."""

    def test_successful_link_creation(self):
        """Test successful link creation."""
        mock_client = Mock()
        mock_client.add_task_link.return_value = {"id": "link_123"}

        result = link_commit_to_task(
            client=mock_client,
            task_id="task_123",
            commit_url="https://github.com/owner/repo/commit/abc123",
            commit_sha_short="abc123"
        )

        mock_client.add_task_link.assert_called_once()
        args = mock_client.add_task_link.call_args[0]
        self.assertEqual(args[0], "task_123")
        self.assertEqual(args[1], "https://github.com/owner/repo/commit/abc123")
        self.assertIn("abc123", args[2])  # Link title should contain SHA

    def test_link_without_sha(self):
        """Test link creation without explicit SHA."""
        mock_client = Mock()
        mock_client.add_task_link.return_value = {"id": "link_123"}

        result = link_commit_to_task(
            client=mock_client,
            task_id="task_123",
            commit_url="https://github.com/owner/repo/commit/abc123def"
        )

        args = mock_client.add_task_link.call_args[0]
        # Should extract SHA from URL
        self.assertIn("abc123d", args[2])  # First 7 chars of SHA


class TestUpdateTaskStatus(unittest.TestCase):
    """Tests for update_task_status function."""

    def test_successful_status_update(self):
        """Test successful status update."""
        mock_client = Mock()
        mock_client.update_task.return_value = {"id": "task_123"}

        result = update_task_status(
            client=mock_client,
            task_id="task_123",
            status="in progress"
        )

        mock_client.update_task.assert_called_once_with("task_123", status="in progress")
        self.assertEqual(result["id"], "task_123")


class TestUpdateTaskFields(unittest.TestCase):
    """Tests for update_task_fields function."""

    def test_update_priority(self):
        """Test updating priority only."""
        mock_client = Mock()
        mock_client.update_task.return_value = {"id": "task_123"}

        result = update_task_fields(
            client=mock_client,
            task_id="task_123",
            priority="urgent"
        )

        mock_client.update_task.assert_called_once()
        call_kwargs = mock_client.update_task.call_args[1]
        self.assertEqual(call_kwargs['priority'], "urgent")

    def test_update_multiple_fields(self):
        """Test updating multiple fields at once."""
        mock_client = Mock()
        mock_client.update_task.return_value = {"id": "task_123"}

        result = update_task_fields(
            client=mock_client,
            task_id="task_123",
            priority="high",
            tags=["bug", "urgent"],
            assignees_add=["user1"]
        )

        mock_client.update_task.assert_called_once()
        call_kwargs = mock_client.update_task.call_args[1]
        self.assertEqual(call_kwargs['priority'], "high")
        self.assertEqual(call_kwargs['tags'], ["bug", "urgent"])
        self.assertEqual(call_kwargs['assignees']['add'], ["user1"])

    def test_no_updates(self):
        """Test that no API call is made when no fields to update."""
        mock_client = Mock()

        result = update_task_fields(
            client=mock_client,
            task_id="task_123"
        )

        mock_client.update_task.assert_not_called()
        self.assertEqual(result, {})


class TestApplyClickUpUpdate(unittest.TestCase):
    """Tests for apply_clickup_update function."""

    def test_apply_comment_only(self):
        """Test applying only a comment."""
        mock_client = Mock()
        mock_client.create_task_comment.return_value = {"id": "comment_123"}

        result = apply_clickup_update(
            client=mock_client,
            task_id="task_123",
            comment="Test comment"
        )

        self.assertIn("Posted comment", result['success'])
        self.assertEqual(len(result['errors']), 0)

    def test_apply_multiple_updates(self):
        """Test applying multiple updates."""
        mock_client = Mock()
        mock_client.create_task_comment.return_value = {"id": "comment_123"}
        mock_client.update_task.return_value = {"id": "task_123"}
        mock_client.add_task_link.return_value = {"id": "link_123"}

        result = apply_clickup_update(
            client=mock_client,
            task_id="task_123",
            comment="Test comment",
            status="in progress",
            commit_url="https://github.com/owner/repo/commit/abc123",
            commit_sha_short="abc123"
        )

        self.assertEqual(len(result['success']), 3)
        self.assertIn("Posted comment", result['success'])
        # Check for status update message (contains status name)
        self.assertTrue(any("status" in msg.lower() for msg in result['success']))
        self.assertIn("Added commit link", result['success'])

    @patch('clickup_framework.git.clickup_bridge.post_commit_comment')
    @patch('clickup_framework.git.clickup_bridge.update_task_status')
    def test_partial_failure(self, mock_update_status, mock_post_comment):
        """Test that partial failures are tracked."""
        mock_client = Mock()

        # Comment succeeds, status fails
        mock_post_comment.return_value = {"id": "comment_123"}
        mock_update_status.side_effect = ClickUpBridgeError("Status update failed")

        result = apply_clickup_update(
            client=mock_client,
            task_id="task_123",
            comment="Test comment",
            status="in progress"
        )

        self.assertEqual(len(result['success']), 1)
        self.assertEqual(len(result['errors']), 1)
        self.assertIn("Posted comment", result['success'])
        self.assertIn("Status update failed", result['errors'][0])

    @patch('clickup_framework.git.clickup_bridge.post_commit_comment')
    def test_all_failures_raise_error(self, mock_post_comment):
        """Test that all failures raise ClickUpBridgeError."""
        mock_client = Mock()
        mock_post_comment.side_effect = ClickUpBridgeError("Failed")

        with self.assertRaises(ClickUpBridgeError) as ctx:
            apply_clickup_update(
                client=mock_client,
                task_id="task_123",
                comment="Test comment"
            )

        self.assertIn("All ClickUp updates failed", str(ctx.exception))


if __name__ == '__main__':
    unittest.main()
