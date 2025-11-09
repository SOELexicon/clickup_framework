"""
Tests for ContextManager
"""

import pytest
import os
import json
import tempfile
from pathlib import Path
from clickup_framework.context import ContextManager


class TestContextManager:
    """Test context management functionality."""

    def setup_method(self):
        """Set up test fixtures with temporary context file."""
        # Create a temporary file for testing
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        self.context_path = self.temp_file.name
        self.context = ContextManager(context_path=self.context_path)

    def teardown_method(self):
        """Clean up temporary files."""
        if os.path.exists(self.context_path):
            os.unlink(self.context_path)

    def test_set_and_get_current_task(self):
        """Test setting and getting current task ID."""
        self.context.set_current_task("task_123")
        assert self.context.get_current_task() == "task_123"

    def test_set_and_get_current_list(self):
        """Test setting and getting current list ID."""
        self.context.set_current_list("list_456")
        assert self.context.get_current_list() == "list_456"

    def test_set_and_get_current_space(self):
        """Test setting and getting current space ID."""
        self.context.set_current_space("space_789")
        assert self.context.get_current_space() == "space_789"

    def test_set_and_get_current_folder(self):
        """Test setting and getting current folder ID."""
        self.context.set_current_folder("folder_abc")
        assert self.context.get_current_folder() == "folder_abc"

    def test_set_and_get_current_workspace(self):
        """Test setting and getting current workspace ID."""
        self.context.set_current_workspace("workspace_def")
        assert self.context.get_current_workspace() == "workspace_def"

    def test_get_nonexistent_returns_none(self):
        """Test that getting nonexistent context returns None."""
        assert self.context.get_current_task() is None
        assert self.context.get_current_list() is None

    def test_persistence(self):
        """Test that context is persisted to disk."""
        self.context.set_current_task("task_123")
        self.context.set_current_list("list_456")

        # Create new instance with same path
        new_context = ContextManager(context_path=self.context_path)

        assert new_context.get_current_task() == "task_123"
        assert new_context.get_current_list() == "list_456"

    def test_clear_current_task(self):
        """Test clearing current task."""
        self.context.set_current_task("task_123")
        assert self.context.get_current_task() == "task_123"

        self.context.clear_current_task()
        assert self.context.get_current_task() is None

    def test_clear_current_list(self):
        """Test clearing current list."""
        self.context.set_current_list("list_456")
        self.context.clear_current_list()
        assert self.context.get_current_list() is None

    def test_clear_all(self):
        """Test clearing all context."""
        self.context.set_current_task("task_123")
        self.context.set_current_list("list_456")
        self.context.set_current_space("space_789")

        self.context.clear_all()

        assert self.context.get_current_task() is None
        assert self.context.get_current_list() is None
        assert self.context.get_current_space() is None

    def test_get_all(self):
        """Test getting all context data."""
        self.context.set_current_task("task_123")
        self.context.set_current_list("list_456")

        all_context = self.context.get_all()

        assert all_context["current_task"] == "task_123"
        assert all_context["current_list"] == "list_456"
        assert "last_updated" in all_context

    def test_resolve_id_with_actual_id(self):
        """Test that resolve_id returns the ID when given an actual ID."""
        result = self.context.resolve_id("task", "task_123")
        assert result == "task_123"

    def test_resolve_id_with_current_keyword(self):
        """Test that resolve_id resolves 'current' keyword."""
        self.context.set_current_task("task_123")
        result = self.context.resolve_id("task", "current")
        assert result == "task_123"

    def test_resolve_id_with_current_keyword_uppercase(self):
        """Test that resolve_id handles 'CURRENT' (case insensitive)."""
        self.context.set_current_task("task_123")
        result = self.context.resolve_id("task", "CURRENT")
        assert result == "task_123"

    def test_resolve_id_raises_error_when_no_current_set(self):
        """Test that resolve_id raises ValueError when no current ID is set."""
        with pytest.raises(ValueError) as exc_info:
            self.context.resolve_id("task", "current")

        assert "No current task set" in str(exc_info.value)
        assert "set_current task" in str(exc_info.value)

    def test_resolve_id_unknown_resource_type(self):
        """Test that resolve_id raises ValueError for unknown resource type."""
        with pytest.raises(ValueError) as exc_info:
            self.context.resolve_id("unknown", "current")

        assert "Unknown resource type" in str(exc_info.value)

    def test_resolve_id_team_alias_for_workspace(self):
        """Test that 'team' is an alias for 'workspace'."""
        self.context.set_current_workspace("team_123")
        result = self.context.resolve_id("team", "current")
        assert result == "team_123"

    def test_file_permissions(self):
        """Test that context file has secure permissions (Unix only)."""
        if os.name != 'nt':  # Skip on Windows
            self.context.set_current_task("task_123")

            # Check file permissions (should be 0600)
            file_stat = os.stat(self.context_path)
            permissions = oct(file_stat.st_mode)[-3:]
            assert permissions == '600', f"Expected 600, got {permissions}"

    def test_corrupted_file_handling(self):
        """Test that corrupted JSON file is handled gracefully."""
        # Write invalid JSON
        with open(self.context_path, 'w') as f:
            f.write("invalid json {")

        # Should not crash, just start fresh
        context = ContextManager(context_path=self.context_path)
        assert context.get_current_task() is None

    def test_last_updated_timestamp(self):
        """Test that last_updated timestamp is set."""
        self.context.set_current_task("task_123")

        all_context = self.context.get_all()
        assert "last_updated" in all_context
        # Should be ISO format timestamp
        from datetime import datetime
        try:
            datetime.fromisoformat(all_context["last_updated"])
        except ValueError:
            pytest.fail("last_updated is not a valid ISO format timestamp")

    def test_multiple_context_updates(self):
        """Test multiple sequential updates."""
        self.context.set_current_task("task_1")
        self.context.set_current_task("task_2")
        self.context.set_current_list("list_1")

        assert self.context.get_current_task() == "task_2"
        assert self.context.get_current_list() == "list_1"

    def test_context_isolation(self):
        """Test that multiple ContextManager instances are isolated."""
        # Create two different context files
        temp_file_2 = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        temp_file_2.close()
        context_path_2 = temp_file_2.name

        try:
            context1 = ContextManager(context_path=self.context_path)
            context2 = ContextManager(context_path=context_path_2)

            context1.set_current_task("task_1")
            context2.set_current_task("task_2")

            assert context1.get_current_task() == "task_1"
            assert context2.get_current_task() == "task_2"
        finally:
            if os.path.exists(context_path_2):
                os.unlink(context_path_2)
