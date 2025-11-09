"""
Tests for RichDocFormatter.
"""

import pytest
from clickup_framework.components.doc_formatter import RichDocFormatter
from clickup_framework.components.options import FormatOptions


class TestRichDocFormatter:
    """Tests for RichDocFormatter class."""

    def test_format_doc_basic(self, sample_doc):
        """Test basic doc formatting."""
        formatter = RichDocFormatter()
        result = formatter.format_doc(sample_doc)

        # Should contain doc name and emoji
        assert "Project Documentation" in result
        assert "📄" in result

    def test_format_doc_with_id(self, sample_doc):
        """Test doc formatting with ID display."""
        formatter = RichDocFormatter()
        options = FormatOptions(show_ids=True, colorize_output=False)
        result = formatter.format_doc(sample_doc, options)

        # Should show doc ID
        assert "doc_123" in result
        assert "Project Documentation" in result

    def test_format_doc_minimal(self, sample_doc):
        """Test minimal doc formatting."""
        formatter = RichDocFormatter()
        result = formatter.format_doc_minimal(sample_doc)

        # Should have doc name and emoji
        assert "Project Documentation" in result
        assert "📄" in result

    def test_format_doc_with_dates(self, sample_doc):
        """Test doc formatting with dates."""
        formatter = RichDocFormatter()
        options = FormatOptions(show_dates=True, colorize_output=False)
        result = formatter.format_doc(sample_doc, options)

        # Should show dates
        assert "Created:" in result or "📅" in result
        assert "2024-01-01" in result

    def test_format_page_basic(self, sample_page):
        """Test basic page formatting."""
        formatter = RichDocFormatter()
        result = formatter.format_page(sample_page)

        # Should contain page name and emoji
        assert "Getting Started" in result
        assert "📃" in result

    def test_format_page_with_id(self, sample_page):
        """Test page formatting with ID display."""
        formatter = RichDocFormatter()
        options = FormatOptions(show_ids=True, colorize_output=False)
        result = formatter.format_page(sample_page, options)

        # Should show page ID
        assert "page_456" in result
        assert "Getting Started" in result

    def test_format_page_with_content(self, sample_page):
        """Test page formatting with content preview."""
        formatter = RichDocFormatter()
        options = FormatOptions(show_descriptions=True, colorize_output=False)
        result = formatter.format_page(sample_page, options)

        # Should show content preview
        assert "Content:" in result or "📝" in result
        assert "Welcome to our documentation" in result

    def test_format_page_minimal(self, sample_page):
        """Test minimal page formatting."""
        formatter = RichDocFormatter()
        result = formatter.format_page_minimal(sample_page)

        # Should have page name and emoji
        assert "Getting Started" in result
        assert "📃" in result

    def test_format_doc_summary(self, sample_doc):
        """Test summary doc formatting."""
        formatter = RichDocFormatter()
        result = formatter.format_doc_summary(sample_doc)

        assert "Project Documentation" in result
        assert isinstance(result, str)

    def test_format_page_summary(self, sample_page):
        """Test summary page formatting."""
        formatter = RichDocFormatter()
        result = formatter.format_page_summary(sample_page)

        assert "Getting Started" in result
        assert isinstance(result, str)

    def test_format_doc_detailed(self, sample_doc):
        """Test detailed doc formatting."""
        formatter = RichDocFormatter()
        result = formatter.format_doc_detailed(sample_doc)

        assert "Project Documentation" in result
        assert isinstance(result, str)

    def test_format_page_detailed(self, sample_page):
        """Test detailed page formatting."""
        formatter = RichDocFormatter()
        result = formatter.format_page_detailed(sample_page)

        assert "Getting Started" in result
        assert isinstance(result, str)

    def test_format_doc_with_parent(self):
        """Test doc formatting with parent relationship."""
        doc = {
            'id': 'doc_child',
            'name': 'Child Doc',
            'parent_id': 'doc_parent'
        }
        formatter = RichDocFormatter()
        options = FormatOptions(show_relationships=True, colorize_output=False)
        result = formatter.format_doc(doc, options)

        # Should show parent relationship
        assert "Parent:" in result or "🔗" in result
        assert "doc_parent" in result

    def test_format_doc_no_colorize(self, sample_doc):
        """Test doc formatting without colors."""
        formatter = RichDocFormatter()
        options = FormatOptions(colorize_output=False)
        result = formatter.format_doc(sample_doc, options)

        # Should not contain ANSI color codes
        assert "\033[" not in result
        assert "Project Documentation" in result

    def test_format_page_no_colorize(self, sample_page):
        """Test page formatting without colors."""
        formatter = RichDocFormatter()
        options = FormatOptions(colorize_output=False)
        result = formatter.format_page(sample_page, options)

        # Should not contain ANSI color codes
        assert "\033[" not in result
        assert "Getting Started" in result

    def test_format_doc_with_creator(self, sample_doc):
        """Test doc formatting with creator info."""
        formatter = RichDocFormatter()
        options = FormatOptions(colorize_output=False)
        result = formatter.format_doc(sample_doc, options)

        # Should show creator
        assert "Creator:" in result or "👤" in result
        assert "john_doe" in result

    def test_format_page_truncates_long_content(self):
        """Test that page content is truncated when too long."""
        page = {
            'id': 'page_long',
            'name': 'Long Content Page',
            'content': '# Long Content\n\n' + 'A' * 500
        }
        formatter = RichDocFormatter()
        options = FormatOptions(
            show_descriptions=True,
            description_length=100,
            colorize_output=False
        )
        result = formatter.format_page(page, options)

        # Content should be truncated
        assert "..." in result or len(result) < len(page['content'])
