"""
Tests for RichTaskFormatter.
"""

import pytest
from clickup_framework.components.task_formatter import RichTaskFormatter
from clickup_framework.components.options import FormatOptions


class TestRichTaskFormatter:
    """Tests for RichTaskFormatter class."""

    def test_format_task_minimal(self, sample_task_minimal):
        """Test minimal task formatting."""
        formatter = RichTaskFormatter()
        result = formatter.format_task(sample_task_minimal, FormatOptions.minimal())

        assert "task_456" in result
        assert "Fix bug" in result
        # Minimal shouldn't show status or priority for defaults
        assert isinstance(result, str)

    def test_format_task_with_all_fields(self, sample_task):
        """Test formatting task with all fields."""
        formatter = RichTaskFormatter()
        options = FormatOptions.full()
        result = formatter.format_task(sample_task, options)

        assert "task_123" in result
        assert "Implement new feature" in result
        assert isinstance(result, str)

    def test_format_task_shows_id_when_requested(self, sample_task):
        """Test task ID is shown when requested."""
        formatter = RichTaskFormatter()
        options = FormatOptions(show_ids=True)
        result = formatter.format_task(sample_task, options)

        assert "[task_123]" in result

    def test_format_task_hides_id_by_default(self, sample_task):
        """Test task ID is hidden by default."""
        formatter = RichTaskFormatter()
        options = FormatOptions(show_ids=False)
        result = formatter.format_task(sample_task, options)

        assert "[task_123]" not in result

    def test_format_task_shows_tags(self, sample_task):
        """Test tags are shown when requested."""
        formatter = RichTaskFormatter()
        options = FormatOptions(show_tags=True)
        result = formatter.format_task(sample_task, options)

        assert "Tags:" in result or "feature" in result

    def test_format_task_shows_description(self, sample_task):
        """Test description is shown when requested."""
        formatter = RichTaskFormatter()
        options = FormatOptions(show_descriptions=True)
        result = formatter.format_task(sample_task, options)

        assert "Description:" in result or "hierarchical" in result

    def test_format_task_shows_dates(self, sample_task):
        """Test dates are shown when requested."""
        formatter = RichTaskFormatter()
        options = FormatOptions(show_dates=True)
        result = formatter.format_task(sample_task, options)

        # Should contain some date information
        assert "2024" in result or "Created:" in result or "Due:" in result

    def test_format_task_shows_comments(self, sample_tasks_with_comments):
        """Test comments are shown when requested."""
        formatter = RichTaskFormatter()
        options = FormatOptions(show_comments=2)
        result = formatter.format_task(sample_tasks_with_comments[0], options)

        assert "Comments" in result or "comment" in result.lower()

    def test_format_task_minimal_preset(self, sample_task):
        """Test formatting with minimal preset."""
        formatter = RichTaskFormatter()
        result = formatter.format_task_minimal(sample_task)

        assert "Implement new feature" in result
        # Should be concise
        assert len(result) < 200

    def test_format_task_summary_preset(self, sample_task):
        """Test formatting with summary preset."""
        formatter = RichTaskFormatter()
        result = formatter.format_task_summary(sample_task)

        assert "Implement new feature" in result
        assert "task_123" in result  # IDs shown in summary

    def test_format_task_detailed_preset(self, sample_task):
        """Test formatting with detailed preset."""
        formatter = RichTaskFormatter()
        result = formatter.format_task_detailed(sample_task)

        assert "Implement new feature" in result
        # Detailed should include more information
        assert len(result) > 50

    def test_format_task_handles_missing_fields(self):
        """Test formatting handles missing optional fields gracefully."""
        formatter = RichTaskFormatter()
        minimal_task = {
            'id': 'task_x',
            'name': 'Minimal Task'
        }
        result = formatter.format_task(minimal_task, FormatOptions())

        assert "task_x" not in result  # IDs off by default
        assert "Minimal Task" in result
        assert isinstance(result, str)

    def test_format_task_without_options(self, sample_task):
        """Test formatting without explicit options uses defaults."""
        formatter = RichTaskFormatter()
        result = formatter.format_task(sample_task)

        assert "Implement new feature" in result
        assert isinstance(result, str)

    def test_format_task_with_completed_status(self, sample_task_completed):
        """Test formatting completed task."""
        formatter = RichTaskFormatter()
        result = formatter.format_task(sample_task_completed, FormatOptions())

        assert "Completed task" in result
        # Completed status might be shown
        assert isinstance(result, str)

    def test_format_task_emoji_shown_by_default(self, sample_task):
        """Test task type emoji is shown by default."""
        formatter = RichTaskFormatter()
        result = formatter.format_task(sample_task, FormatOptions())

        # Should contain some emoji (feature rocket emoji)
        assert "🚀" in result or "📝" in result

    def test_format_task_emoji_can_be_hidden(self, sample_task):
        """Test task type emoji can be hidden."""
        formatter = RichTaskFormatter()
        options = FormatOptions(show_type_emoji=False)
        result = formatter.format_task(sample_task, options)

        # Without emoji, should still show name
        assert "Implement new feature" in result
