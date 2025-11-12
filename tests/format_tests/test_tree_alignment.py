"""
Test Suite for Content Formatting and Display Fixes

Tests for bugfixes implemented in task 86c6g88be:
1. Escaped newlines in content display
2. Status mapping (Complete → Closed)
3. Extra None page prevention
4. Page hierarchy documentation
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from clickup_framework.utils.text import unescape_content
from clickup_framework.utils.status_mapper import StatusMapper, map_status
from clickup_framework.resources.docs import DocsAPI
from clickup_framework.components.detail_view import TaskDetailFormatter
from clickup_framework.components.options import FormatOptions


class TestUnescapeContent(unittest.TestCase):
    """Test the unescape_content utility function."""

    def test_unescape_single_newline(self):
        """Test unescaping single newline."""
        input_text = "Line 1\\nLine 2"
        expected = "Line 1\nLine 2"
        result = unescape_content(input_text)
        self.assertEqual(result, expected)

    def test_unescape_multiple_newlines(self):
        """Test unescaping multiple consecutive newlines."""
        input_text = "Line 1\\n\\nLine 2"
        expected = "Line 1\n\nLine 2"
        result = unescape_content(input_text)
        self.assertEqual(result, expected)

    def test_unescape_tabs(self):
        """Test unescaping tabs."""
        input_text = "Column1\\tColumn2"
        expected = "Column1\tColumn2"
        result = unescape_content(input_text)
        self.assertEqual(result, expected)

    def test_unescape_carriage_returns(self):
        """Test unescaping carriage returns."""
        input_text = "Line 1\\rLine 2"
        expected = "Line 1\rLine 2"
        result = unescape_content(input_text)
        self.assertEqual(result, expected)

    def test_unescape_mixed_escapes(self):
        """Test unescaping mixed escape sequences."""
        input_text = "# Header\\n\\nParagraph with\\ttab\\n\\nAnother paragraph"
        expected = "# Header\n\nParagraph with\ttab\n\nAnother paragraph"
        result = unescape_content(input_text)
        self.assertEqual(result, expected)

    def test_unescape_empty_string(self):
        """Test unescaping empty string."""
        result = unescape_content("")
        self.assertEqual(result, "")

    def test_unescape_none(self):
        """Test unescaping None."""
        result = unescape_content(None)
        self.assertEqual(result, "")

    def test_unescape_no_escapes(self):
        """Test content with no escape sequences."""
        input_text = "Plain text without escapes"
        result = unescape_content(input_text)
        self.assertEqual(result, input_text)

    def test_unescape_markdown_content(self):
        """Test unescaping markdown content with formatting."""
        input_text = "# Test Header\\n\\n**Bold text**\\n- Bullet 1\\n- Bullet 2"
        expected = "# Test Header\n\n**Bold text**\n- Bullet 1\n- Bullet 2"
        result = unescape_content(input_text)
        self.assertEqual(result, expected)


class TestStatusMapping(unittest.TestCase):
    """Test status mapping functionality."""

    def setUp(self):
        """Set up test data."""
        self.available_statuses = [
            {'status': 'Open', 'type': 'open', 'color': '#d3d3d3'},
            {'status': 'in development', 'type': 'custom', 'color': '#4194f6'},
            {'status': 'testing', 'type': 'custom', 'color': '#6fddff'},
            {'status': 'Closed', 'type': 'closed', 'color': '#6bc950'},
        ]

    def test_map_complete_to_closed(self):
        """Test mapping 'Complete' to 'Closed'."""
        result = map_status('Complete', self.available_statuses)
        self.assertEqual(result, 'Closed')

    def test_map_done_to_closed(self):
        """Test mapping 'Done' to 'Closed'."""
        result = map_status('Done', self.available_statuses)
        self.assertEqual(result, 'Closed')

    def test_map_finished_to_closed(self):
        """Test mapping 'Finished' to 'Closed'."""
        result = map_status('Finished', self.available_statuses)
        self.assertEqual(result, 'Closed')

    def test_map_in_dev_to_in_development(self):
        """Test mapping 'In Dev' to 'in development'."""
        result = map_status('In Dev', self.available_statuses)
        self.assertEqual(result, 'in development')

    def test_map_wip_to_in_development(self):
        """Test mapping 'WIP' to 'in development'."""
        result = map_status('WIP', self.available_statuses)
        self.assertEqual(result, 'in development')

    def test_exact_match(self):
        """Test exact match (case-insensitive)."""
        result = map_status('closed', self.available_statuses)
        self.assertEqual(result, 'Closed')

    def test_exact_match_preserves_case(self):
        """Test that exact match preserves original status casing."""
        result = map_status('CLOSED', self.available_statuses)
        self.assertEqual(result, 'Closed')  # Returns original case from available statuses

    def test_no_mapping_found(self):
        """Test when no mapping is found."""
        result = map_status('NonexistentStatus', self.available_statuses)
        self.assertIsNone(result)

    def test_empty_status(self):
        """Test empty status string."""
        result = map_status('', self.available_statuses)
        self.assertIsNone(result)

    def test_none_status(self):
        """Test None status."""
        result = map_status(None, self.available_statuses)
        self.assertIsNone(result)


class TestTaskDescriptionFormatting(unittest.TestCase):
    """Test task description formatting with escaped newlines fix."""

    def setUp(self):
        """Set up test formatter."""
        self.formatter = TaskDetailFormatter()
        self.options = FormatOptions(colorize_output=False)

    def test_format_description_with_escaped_newlines(self):
        """Test formatting description with escaped newlines."""
        task = {
            'name': 'Test Task',
            'description': 'Line 1\\nLine 2\\n\\nLine 3'
        }

        result = self.formatter._format_description(task, self.options)

        # Should contain actual newlines, not escaped ones
        self.assertIn('\n', result)
        self.assertNotIn('\\n', result)
        self.assertIn('Line 1', result)
        self.assertIn('Line 2', result)
        self.assertIn('Line 3', result)

    def test_format_description_with_markdown(self):
        """Test formatting markdown description with escaped newlines."""
        task = {
            'name': 'Test Task',
            'description': '# Header\\n\\n**Bold text**\\n- Item 1\\n- Item 2'
        }

        result = self.formatter._format_description(task, self.options)

        # Should process markdown and newlines correctly
        self.assertIn('Header', result)
        self.assertIn('Bold text', result)
        self.assertIn('Item 1', result)
        self.assertNotIn('\\n', result)

    def test_format_empty_description(self):
        """Test formatting empty description."""
        task = {
            'name': 'Test Task',
            'description': ''
        }

        result = self.formatter._format_description(task, self.options)
        self.assertEqual(result, '')

    def test_format_none_description(self):
        """Test formatting None description."""
        task = {
            'name': 'Test Task',
            'description': None
        }

        result = self.formatter._format_description(task, self.options)
        self.assertEqual(result, '')


class TestDocCreationNonePageFix(unittest.TestCase):
    """Test fix for extra 'None' page creation."""

    def setUp(self):
        """Set up mocked client and DocsAPI."""
        self.mock_client = Mock()
        self.docs_api = DocsAPI(self.mock_client)

    def test_create_doc_with_pages_reuses_blank_page(self):
        """Test that blank 'None' page is reused instead of creating extra page."""
        # Mock doc creation
        self.mock_client.create_doc.return_value = {
            'id': 'doc123',
            'name': 'Test Doc'
        }

        # Mock getting existing pages - returns one blank page
        self.mock_client.get_doc_pages.return_value = [
            {'id': 'page_blank', 'name': 'None', 'content': ''}
        ]

        # Mock update_page
        self.mock_client.update_page.return_value = {
            'id': 'page_blank',
            'name': 'Introduction',
            'content': '# Intro'
        }

        # Create doc with pages
        pages = [
            {'name': 'Introduction', 'content': '# Intro'},
            {'name': 'Setup', 'content': '# Setup'}
        ]

        result = self.docs_api.create_doc_with_pages(
            workspace_id='ws123',
            doc_name='Test Doc',
            pages=pages
        )

        # Should update the blank page for first custom page
        self.mock_client.update_page.assert_called_once()

        # Verify update_page was called with correct parameters
        # The client.update_page signature: update_page(workspace_id, doc_id, page_id, **updates)
        self.mock_client.update_page.assert_called_with(
            'ws123',
            'doc123',
            'page_blank',
            name='Introduction',
            content='# Intro'
        )

        # Should create only one additional page (Setup)
        self.mock_client.create_page.assert_called_once()
        # Verify the second page was created
        # The client.create_page signature: create_page(workspace_id, doc_id, name, content=None, **page_data)
        self.mock_client.create_page.assert_called_with(
            'ws123',
            'doc123',
            'Setup',
            '# Setup'
        )

    def test_create_doc_with_pages_no_blank_page(self):
        """Test normal page creation when no blank page exists."""
        # Mock doc creation
        self.mock_client.create_doc.return_value = {
            'id': 'doc123',
            'name': 'Test Doc'
        }

        # Mock getting existing pages - returns empty list
        self.mock_client.get_doc_pages.return_value = []

        # Mock create_page
        self.mock_client.create_page.return_value = {
            'id': 'page1',
            'name': 'Introduction',
            'content': '# Intro'
        }

        # Create doc with pages
        pages = [
            {'name': 'Introduction', 'content': '# Intro'},
        ]

        result = self.docs_api.create_doc_with_pages(
            workspace_id='ws123',
            doc_name='Test Doc',
            pages=pages
        )

        # Should NOT call update_page
        self.mock_client.update_page.assert_not_called()

        # Should create page normally
        self.mock_client.create_page.assert_called_once()

    def test_create_doc_with_pages_named_blank_page(self):
        """Test handling of existing page with proper name."""
        # Mock doc creation
        self.mock_client.create_doc.return_value = {
            'id': 'doc123',
            'name': 'Test Doc'
        }

        # Mock getting existing pages - returns page with proper name
        self.mock_client.get_doc_pages.return_value = [
            {'id': 'page1', 'name': 'Existing Page', 'content': 'Content'}
        ]

        # Mock create_page
        self.mock_client.create_page.return_value = {
            'id': 'page2',
            'name': 'Introduction',
            'content': '# Intro'
        }

        # Create doc with pages
        pages = [
            {'name': 'Introduction', 'content': '# Intro'},
        ]

        result = self.docs_api.create_doc_with_pages(
            workspace_id='ws123',
            doc_name='Test Doc',
            pages=pages
        )

        # Should NOT update existing named page
        self.mock_client.update_page.assert_not_called()

        # Should create new page
        self.mock_client.create_page.assert_called_once()


class TestPageContentFormatting(unittest.TestCase):
    """Test page content formatting with escaped newlines fix."""

    def test_page_content_unescaping(self):
        """Test that page content is properly unescaped."""
        # This is tested indirectly through the unescape_content function
        # which is called in doc_commands.py
        content = "# Page Title\\n\\nContent paragraph.\\n\\nAnother paragraph."
        expected = "# Page Title\n\nContent paragraph.\n\nAnother paragraph."

        result = unescape_content(content)
        self.assertEqual(result, expected)

    def test_page_preview_formatting(self):
        """Test page preview with newlines replaced by spaces."""
        content = unescape_content("Line 1\\nLine 2\\nLine 3")
        preview = content[:150].replace('\n', ' ')

        # Preview should have spaces instead of newlines
        self.assertNotIn('\n', preview)
        self.assertIn('Line 1 Line 2 Line 3', preview)


class TestStatusMapperIntegration(unittest.TestCase):
    """Integration tests for status mapper."""

    def test_common_mappings_complete(self):
        """Test all common 'complete' variant mappings."""
        mapper = StatusMapper()
        variants = ['complete', 'completed', 'done', 'closed', 'finished']

        for variant in variants:
            self.assertIn(variant, mapper.COMMON_MAPPINGS)
            mappings = mapper.COMMON_MAPPINGS[variant]
            # All should map to completion-related statuses
            self.assertTrue(any(s in mappings for s in ['complete', 'completed', 'closed', 'done']))

    def test_common_mappings_in_progress(self):
        """Test all common 'in progress' variant mappings."""
        mapper = StatusMapper()
        variants = ['in progress', 'in development', 'in dev', 'working', 'active', 'wip']

        for variant in variants:
            self.assertIn(variant, mapper.COMMON_MAPPINGS)
            mappings = mapper.COMMON_MAPPINGS[variant]
            # All should map to in-progress-related statuses
            self.assertTrue(any(s in mappings for s in ['in progress', 'in development', 'working']))

    def test_suggest_status(self):
        """Test status suggestion functionality."""
        available_statuses = [
            {'status': 'Open', 'type': 'open'},
            {'status': 'Closed', 'type': 'closed'},
            {'status': 'in development', 'type': 'custom'},
        ]

        suggestions = StatusMapper.suggest_status('clos', available_statuses, max_suggestions=3)

        # Should suggest 'Closed' for 'clos'
        self.assertIn('Closed', suggestions)


class TestDocAPILimitations(unittest.TestCase):
    """Test documentation of API limitations."""

    def test_get_doc_pages_has_limitation_docs(self):
        """Test that get_doc_pages has limitation documentation."""
        docs_api = DocsAPI(Mock())

        # Check that the method exists and has proper docstring
        self.assertTrue(hasattr(docs_api, 'get_doc_pages'))
        docstring = docs_api.get_doc_pages.__doc__

        # Should mention the limitation
        self.assertIn('limitation', docstring.lower())
        self.assertIn('flat list', docstring.lower())
        self.assertIn('hierarchy', docstring.lower())


if __name__ == '__main__':
    unittest.main()
