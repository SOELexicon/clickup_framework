"""
Tests for FormatOptions dataclass.
"""

import pytest
from clickup_framework.components.options import FormatOptions


class TestFormatOptions:
    """Tests for FormatOptions class."""

    def test_default_values(self):
        """Test default option values."""
        options = FormatOptions()

        assert options.colorize_output is True
        assert options.show_ids is False
        assert options.show_score is False
        assert options.show_tags is True
        assert options.tag_style == "colored"
        assert options.show_type_emoji is True
        assert options.show_descriptions is False
        assert options.show_dates is False
        assert options.show_comments == 0
        assert options.show_relationships is False
        assert options.include_completed is False
        assert options.hide_orphaned is False
        assert options.description_length == 100
        assert options.show_container_diff is True
        assert options.trace is False

    def test_custom_values(self):
        """Test custom option values."""
        options = FormatOptions(
            colorize_output=False,
            show_ids=True,
            show_tags=False,
            description_length=200
        )

        assert options.colorize_output is False
        assert options.show_ids is True
        assert options.show_tags is False
        assert options.description_length == 200

    def test_from_dict(self):
        """Test creating options from dictionary."""
        opts_dict = {
            'colorize_output': False,
            'show_ids': True,
            'show_descriptions': True,
            'description_length': 150,
            'unknown_field': 'ignored'  # Should be ignored
        }

        options = FormatOptions.from_dict(opts_dict)

        assert options.colorize_output is False
        assert options.show_ids is True
        assert options.show_descriptions is True
        assert options.description_length == 150
        # Unknown fields are filtered out
        assert not hasattr(options, 'unknown_field')

    def test_minimal_preset(self):
        """Test minimal preset."""
        options = FormatOptions.minimal()

        assert options.colorize_output is False
        assert options.show_ids is True
        assert options.show_tags is False
        assert options.show_type_emoji is False
        assert options.show_descriptions is False

    def test_summary_preset(self):
        """Test summary preset."""
        options = FormatOptions.summary()

        assert options.colorize_output is True
        assert options.show_ids is True
        assert options.show_tags is True
        assert options.show_type_emoji is True
        assert options.show_dates is True
        assert options.show_descriptions is False

    def test_detailed_preset(self):
        """Test detailed preset."""
        options = FormatOptions.detailed()

        assert options.colorize_output is True
        assert options.show_ids is True
        assert options.show_tags is True
        assert options.show_type_emoji is True
        assert options.show_descriptions is True
        assert options.show_dates is True
        assert options.show_relationships is True
        assert options.show_comments == 0  # Still disabled by default

    def test_full_preset(self):
        """Test full preset."""
        options = FormatOptions.full()

        assert options.colorize_output is True
        assert options.show_ids is True
        assert options.show_score is True
        assert options.show_tags is True
        assert options.show_type_emoji is True
        assert options.show_descriptions is True
        assert options.show_dates is True
        assert options.show_comments == 3
        assert options.show_relationships is True
        assert options.include_completed is True
