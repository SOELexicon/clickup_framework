"""
Tests for color utilities.
"""

import pytest
from clickup_framework.utils.colors import (
    colorize, status_color, priority_color, container_color,
    completion_color, get_task_emoji, TextColor, TextStyle
)


class TestColorize:
    """Tests for colorize function."""

    def test_colorize_with_color(self):
        """Test colorizing text with color."""
        result = colorize("Hello", TextColor.RED, force=True)
        assert "\033[31m" in result  # Red color code
        assert "Hello" in result
        assert "\033[0m" in result  # Reset code

    def test_colorize_with_style(self):
        """Test colorizing text with style."""
        result = colorize("Hello", style=TextStyle.BOLD, force=True)
        assert "\033[1m" in result  # Bold style code
        assert "Hello" in result
        assert "\033[0m" in result  # Reset code

    def test_colorize_with_color_and_style(self):
        """Test colorizing text with both color and style."""
        result = colorize("Hello", TextColor.BLUE, TextStyle.BOLD, force=True)
        assert "\033[34m" in result  # Blue color code
        assert "\033[1m" in result  # Bold style code
        assert "Hello" in result
        assert "\033[0m" in result  # Reset code

    def test_colorize_without_color_or_style(self):
        """Test colorizing without color or style returns plain text."""
        result = colorize("Hello")
        assert result == "Hello"


class TestStatusColor:
    """Tests for status_color function."""

    def test_status_to_do(self):
        """Test color for to do status."""
        assert status_color("to do") == TextColor.YELLOW
        assert status_color("todo") == TextColor.YELLOW
        assert status_color("open") == TextColor.YELLOW

    def test_status_in_progress(self):
        """Test color for in progress status."""
        assert status_color("in progress") == TextColor.BRIGHT_BLUE
        assert status_color("in review") == TextColor.BRIGHT_BLUE

    def test_status_complete(self):
        """Test color for complete status."""
        assert status_color("complete") == TextColor.BRIGHT_GREEN
        assert status_color("completed") == TextColor.BRIGHT_GREEN
        assert status_color("done") == TextColor.BRIGHT_GREEN
        assert status_color("closed") == TextColor.BRIGHT_GREEN

    def test_status_blocked(self):
        """Test color for blocked status."""
        assert status_color("blocked") == TextColor.BRIGHT_RED
        assert status_color("block") == TextColor.BRIGHT_RED

    def test_status_unknown(self):
        """Test color for unknown status."""
        assert status_color("unknown") == TextColor.WHITE
        assert status_color("") == TextColor.WHITE
        assert status_color(None) == TextColor.WHITE

    def test_status_case_insensitive(self):
        """Test status color is case insensitive."""
        assert status_color("TO DO") == TextColor.YELLOW
        assert status_color("IN PROGRESS") == TextColor.BRIGHT_BLUE
        assert status_color("COMPLETE") == TextColor.BRIGHT_GREEN


class TestPriorityColor:
    """Tests for priority_color function."""

    def test_priority_urgent(self):
        """Test color for urgent priority."""
        assert priority_color(1) == TextColor.BRIGHT_RED
        assert priority_color("1") == TextColor.BRIGHT_RED

    def test_priority_high(self):
        """Test color for high priority."""
        assert priority_color(2) == TextColor.BRIGHT_YELLOW
        assert priority_color("2") == TextColor.BRIGHT_YELLOW

    def test_priority_normal(self):
        """Test color for normal priority."""
        assert priority_color(3) == TextColor.BRIGHT_BLUE
        assert priority_color("3") == TextColor.BRIGHT_BLUE

    def test_priority_low(self):
        """Test color for low priority."""
        assert priority_color(4) == TextColor.BRIGHT_GREEN
        assert priority_color("4") == TextColor.BRIGHT_GREEN

    def test_priority_default(self):
        """Test default priority color."""
        assert priority_color(5) == TextColor.WHITE
        assert priority_color(0) == TextColor.WHITE
        assert priority_color("invalid") == TextColor.WHITE


class TestContainerColor:
    """Tests for container_color function."""

    def test_workspace_color(self):
        """Test color for workspace container."""
        assert container_color("workspace") == TextColor.BRIGHT_MAGENTA

    def test_space_color(self):
        """Test color for space container."""
        assert container_color("space") == TextColor.BRIGHT_BLUE

    def test_folder_color(self):
        """Test color for folder container."""
        assert container_color("folder") == TextColor.BRIGHT_CYAN

    def test_list_color(self):
        """Test color for list container."""
        assert container_color("list") == TextColor.BRIGHT_YELLOW

    def test_unknown_container(self):
        """Test color for unknown container."""
        assert container_color("unknown") == TextColor.WHITE

    def test_container_case_insensitive(self):
        """Test container color is case insensitive."""
        assert container_color("SPACE") == TextColor.BRIGHT_BLUE
        assert container_color("Folder") == TextColor.BRIGHT_CYAN


class TestCompletionColor:
    """Tests for completion_color function."""

    def test_fully_complete(self):
        """Test color when all tasks complete."""
        assert completion_color(10, 10) == TextColor.BRIGHT_GREEN

    def test_mostly_complete(self):
        """Test color when 75-99% complete."""
        assert completion_color(8, 10) == TextColor.GREEN

    def test_half_complete(self):
        """Test color when 50-74% complete."""
        assert completion_color(6, 10) == TextColor.BRIGHT_YELLOW

    def test_quarter_complete(self):
        """Test color when 25-49% complete."""
        assert completion_color(3, 10) == TextColor.YELLOW

    def test_barely_started(self):
        """Test color when 1-24% complete."""
        assert completion_color(1, 10) == TextColor.BRIGHT_RED

    def test_no_tasks(self):
        """Test color when no tasks."""
        assert completion_color(0, 0) == TextColor.BRIGHT_BLACK


class TestGetTaskEmoji:
    """Tests for get_task_emoji function."""

    def test_task_emoji(self):
        """Test emoji for task type."""
        assert get_task_emoji("task") == "📝"

    def test_bug_emoji(self):
        """Test emoji for bug type."""
        assert get_task_emoji("bug") == "🐛"

    def test_feature_emoji(self):
        """Test emoji for feature type."""
        assert get_task_emoji("feature") == "🚀"

    def test_refactor_emoji(self):
        """Test emoji for refactor type."""
        assert get_task_emoji("refactor") == "♻️"

    def test_documentation_emoji(self):
        """Test emoji for documentation type."""
        assert get_task_emoji("documentation") == "📚"
        assert get_task_emoji("docs") == "📚"

    def test_unknown_type(self):
        """Test default emoji for unknown type."""
        assert get_task_emoji("unknown") == "📝"
        assert get_task_emoji("") == "📝"
        assert get_task_emoji(None) == "📝"

    def test_case_insensitive(self):
        """Test emoji lookup is case insensitive."""
        assert get_task_emoji("BUG") == "🐛"
        assert get_task_emoji("Feature") == "🚀"
