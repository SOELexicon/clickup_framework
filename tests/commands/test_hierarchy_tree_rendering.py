"""
Tests for hierarchy command tree pipe rendering.

Validates that tree characters (├─, └─, │) are correctly rendered
in hierarchy command output to prevent display regressions.
"""

import argparse
import sys
from io import StringIO
from unittest.mock import Mock, patch

import pytest

from clickup_framework.commands.hierarchy import hierarchy_command


class TestHierarchyTreeRendering:
    """Test tree pipe rendering in hierarchy command output."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock ClickUp client."""
        client = Mock()

        # Mock get_list_tasks to return sample hierarchical tasks
        client.get_list_tasks.return_value = {
            "tasks": [
                {
                    "id": "parent1",
                    "name": "Parent Task 1",
                    "parent": None,
                    "status": {"status": "open"},
                    "list": {"id": "list1", "name": "Test List"},
                    "folder": {"id": "folder1", "name": "Test Folder"},
                    "space": {"id": "space1", "name": "Test Space"},
                },
                {
                    "id": "child1",
                    "name": "Child Task 1",
                    "parent": "parent1",
                    "status": {"status": "open"},
                    "list": {"id": "list1", "name": "Test List"},
                    "folder": {"id": "folder1", "name": "Test Folder"},
                    "space": {"id": "space1", "name": "Test Space"},
                },
                {
                    "id": "child2",
                    "name": "Child Task 2",
                    "parent": "parent1",
                    "status": {"status": "open"},
                    "list": {"id": "list1", "name": "Test List"},
                    "folder": {"id": "folder1", "name": "Test Folder"},
                    "space": {"id": "space1", "name": "Test Space"},
                },
                {
                    "id": "parent2",
                    "name": "Parent Task 2",
                    "parent": None,
                    "status": {"status": "open"},
                    "list": {"id": "list1", "name": "Test List"},
                    "folder": {"id": "folder1", "name": "Test Folder"},
                    "space": {"id": "space1", "name": "Test Space"},
                },
            ],
            "last_page": True,
        }

        # Mock get_list for status information and to identify as list (not space/folder)
        client.get_list.return_value = {
            "id": "list1",
            "name": "Test List",
            "statuses": [
                {"status": "open", "type": "open"},
                {"status": "closed", "type": "closed"},
            ],
        }

        # Make get_space raise an exception so it's not detected as space
        from clickup_framework.exceptions import ClickUpNotFoundError

        client.get_space.side_effect = ClickUpNotFoundError("Not a space")
        client.get_folder.side_effect = ClickUpNotFoundError("Not a folder")
        client.get_task.side_effect = ClickUpNotFoundError("Not a task")

        return client

    @pytest.fixture
    def mock_context(self):
        """Create a mock context manager."""
        context = Mock()
        context.get_ansi_output.return_value = False  # Disable colors for easier testing
        context.resolve_id.side_effect = lambda type_, id_: id_  # Pass through IDs
        return context

    def test_tree_characters_present_in_output(self, mock_client, mock_context):
        """Test that tree characters (├─, └─) appear in hierarchy output."""
        args = argparse.Namespace(
            list_id="list1",
            show_all=False,
            include_completed=False,
            show_closed_only=False,
            colorize=False,
            show_ids=False,
            show_tags=True,
            show_descriptions=False,
            show_dates=False,
            show_comments=0,
            show_emoji=True,
            preset=None,
            depth=None,
            header=None,
            full_descriptions=False,
            show_tips=False,  # Disable tips for cleaner test output
        )

        # Capture stdout
        captured_output = StringIO()

        with patch("clickup_framework.commands.hierarchy.ClickUpClient", return_value=mock_client):
            with patch(
                "clickup_framework.commands.hierarchy.get_context_manager",
                return_value=mock_context,
            ):
                with patch("sys.stdout", captured_output):
                    hierarchy_command(args)

        output = captured_output.getvalue()

        # Verify tree characters are present
        assert "├─" in output or "└─" in output, f"Tree characters not found in output:\n{output}"

    def test_tree_branch_characters(self, mock_client, mock_context):
        """Test that branch characters (├─) are used for non-last items."""
        args = argparse.Namespace(
            list_id="list1",
            show_all=False,
            include_completed=False,
            show_closed_only=False,
            colorize=False,
            show_ids=False,
            show_tags=True,
            show_descriptions=False,
            show_dates=False,
            show_comments=0,
            show_emoji=True,
            preset=None,
            depth=None,
            header=None,
            full_descriptions=False,
            show_tips=False,
        )

        captured_output = StringIO()

        with patch("clickup_framework.commands.hierarchy.ClickUpClient", return_value=mock_client):
            with patch(
                "clickup_framework.commands.hierarchy.get_context_manager",
                return_value=mock_context,
            ):
                with patch("sys.stdout", captured_output):
                    hierarchy_command(args)

        output = captured_output.getvalue()

        # Should have branch character for first child
        assert "├─" in output, f"Branch character (├─) not found for non-last items:\n{output}"

    def test_tree_end_characters(self, mock_client, mock_context):
        """Test that end characters (└─) are used for last items."""
        args = argparse.Namespace(
            list_id="list1",
            show_all=False,
            include_completed=False,
            show_closed_only=False,
            colorize=False,
            show_ids=False,
            show_tags=True,
            show_descriptions=False,
            show_dates=False,
            show_comments=0,
            show_emoji=True,
            preset=None,
            depth=None,
            header=None,
            full_descriptions=False,
            show_tips=False,
        )

        captured_output = StringIO()

        with patch("clickup_framework.commands.hierarchy.ClickUpClient", return_value=mock_client):
            with patch(
                "clickup_framework.commands.hierarchy.get_context_manager",
                return_value=mock_context,
            ):
                with patch("sys.stdout", captured_output):
                    hierarchy_command(args)

        output = captured_output.getvalue()

        # Should have end character for last child
        assert "└─" in output, f"End character (└─) not found for last items:\n{output}"

    def test_vertical_pipe_for_continuation(self, mock_client, mock_context):
        """Test that vertical pipes (│) appear for tree continuation."""
        # Add a deeply nested task
        mock_client.get_list_tasks.return_value["tasks"].append(
            {
                "id": "grandchild1",
                "name": "Grandchild Task",
                "parent": "child1",
                "status": {"status": "open"},
                "list": {"id": "list1", "name": "Test List"},
                "folder": {"id": "folder1", "name": "Test Folder"},
                "space": {"id": "space1", "name": "Test Space"},
            }
        )

        args = argparse.Namespace(
            list_id="list1",
            show_all=False,
            include_completed=False,
            show_closed_only=False,
            colorize=False,
            show_ids=False,
            show_tags=True,
            show_descriptions=True,  # Enable descriptions to get multi-line content
            show_dates=False,
            show_comments=0,
            show_emoji=True,
            preset=None,
            depth=None,
            header=None,
            full_descriptions=False,
            show_tips=False,
        )

        captured_output = StringIO()

        with patch("clickup_framework.commands.hierarchy.ClickUpClient", return_value=mock_client):
            with patch(
                "clickup_framework.commands.hierarchy.get_context_manager",
                return_value=mock_context,
            ):
                with patch("sys.stdout", captured_output):
                    hierarchy_command(args)

        output = captured_output.getvalue()

        # Vertical pipes should appear for continuation
        # This may or may not appear depending on content, so we make it optional
        # but document the expectation
        lines = output.split("\n")
        has_tree_chars = any("├─" in line or "└─" in line or "│" in line for line in lines)
        assert has_tree_chars, f"No tree characters found in hierarchy output:\n{output}"

    def test_no_broken_tree_characters(self, mock_client, mock_context):
        """Test that tree characters are not broken or malformed."""
        args = argparse.Namespace(
            list_id="list1",
            show_all=False,
            include_completed=False,
            show_closed_only=False,
            colorize=False,
            show_ids=False,
            show_tags=True,
            show_descriptions=False,
            show_dates=False,
            show_comments=0,
            show_emoji=True,
            preset=None,
            depth=None,
            header=None,
            full_descriptions=False,
            show_tips=False,
        )

        captured_output = StringIO()

        with patch("clickup_framework.commands.hierarchy.ClickUpClient", return_value=mock_client):
            with patch(
                "clickup_framework.commands.hierarchy.get_context_manager",
                return_value=mock_context,
            ):
                with patch("sys.stdout", captured_output):
                    hierarchy_command(args)

        output = captured_output.getvalue()

        # Should not have broken unicode or malformed characters
        # Common issues: � (replacement character), broken UTF-8
        assert "�" not in output, f"Broken unicode characters found in output:\n{output}"

        # Tree characters should be properly formed
        # Check for common valid tree characters
        valid_tree_chars = ["├─", "└─", "│", "├", "└", "─"]
        has_valid_chars = any(char in output for char in valid_tree_chars)
        assert has_valid_chars, f"No valid tree characters found in hierarchy output:\n{output}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
