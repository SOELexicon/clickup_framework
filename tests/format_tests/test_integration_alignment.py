"""
Integration Tests for Content Formatting with Real ClickUp Data

These tests verify that the bugfixes work correctly with actual ClickUp API data.
They require valid ClickUp credentials and will be skipped if not available.

Run with: pytest tests/format_tests/test_integration_alignment.py -v
"""

import unittest
import os
from unittest import skipIf, SkipTest
from clickup_framework import ClickUpClient
from clickup_framework.resources.docs import DocsAPI
from clickup_framework.components.detail_view import TaskDetailFormatter
from clickup_framework.components.options import FormatOptions
from clickup_framework.utils.text import unescape_content
from clickup_framework.utils.status_mapper import map_status, get_available_statuses


# Check if we have credentials
HAS_CREDENTIALS = os.getenv('CLICKUP_API_TOKEN') is not None
SKIP_MESSAGE = "Requires CLICKUP_API_TOKEN environment variable"


@skipIf(not HAS_CREDENTIALS, SKIP_MESSAGE)
class TestTaskDescriptionAlignmentIntegration(unittest.TestCase):
    """Integration tests for task description formatting with real data."""

    @classmethod
    def setUpClass(cls):
        """Set up client and test data."""
        cls.client = ClickUpClient()
        cls.formatter = TaskDetailFormatter(cls.client)
        cls.options = FormatOptions(colorize_output=False)

    def test_task_with_multiline_description(self):
        """Test task with multi-line description renders correctly."""
        # Create a test task with escaped newlines in description
        try:
            # Get a test list ID from environment or use default
            test_list_id = os.getenv('TEST_LIST_ID')
            if not test_list_id:
                self.skipTest("TEST_LIST_ID not set - cannot create test task")

            # Create task with markdown description
            task = self.client.create_task(
                test_list_id,
                name="[TEST] Description Alignment Test",
                description="# Test Header\\n\\n**Bold text**\\n\\n- Item 1\\n- Item 2\\n\\n`code block`"
            )

            # Fetch the task back
            fetched_task = self.client.get_task(task['id'])

            # Format the description
            formatted = self.formatter._format_description(fetched_task, self.options)

            # Verify newlines were unescaped
            self.assertIn('\n', formatted)
            self.assertNotIn('\\n', formatted)

            # Verify content is present
            self.assertIn('Test Header', formatted)
            self.assertIn('Bold text', formatted)
            self.assertIn('Item 1', formatted)

            # Cleanup
            self.client.delete_task(task['id'])

        except SkipTest:
            raise  # Re-raise skip exceptions
        except Exception as e:
            self.fail(f"Integration test failed: {e}")

    def test_task_description_none_handling(self):
        """Test that tasks without descriptions don't cause errors."""
        try:
            test_list_id = os.getenv('TEST_LIST_ID')
            if not test_list_id:
                self.skipTest("TEST_LIST_ID not set")

            # Create task without description
            task = self.client.create_task(
                test_list_id,
                name="[TEST] No Description Test"
            )

            # Fetch and format
            fetched_task = self.client.get_task(task['id'])
            formatted = self.formatter._format_description(fetched_task, self.options)

            # Should return empty string without error
            self.assertEqual(formatted, '')

            # Cleanup
            self.client.delete_task(task['id'])

        except SkipTest:
            raise  # Re-raise skip exceptions
        except Exception as e:
            self.fail(f"Integration test failed: {e}")


@skipIf(not HAS_CREDENTIALS, SKIP_MESSAGE)
class TestStatusMappingIntegration(unittest.TestCase):
    """Integration tests for status mapping with real list statuses."""

    @classmethod
    def setUpClass(cls):
        """Set up client."""
        cls.client = ClickUpClient()

    def test_status_mapping_with_real_list(self):
        """Test status mapping works with actual list statuses."""
        try:
            test_list_id = os.getenv('TEST_LIST_ID')
            if not test_list_id:
                self.skipTest("TEST_LIST_ID not set")

            # Get list data
            list_data = self.client.get_list(test_list_id)
            available_statuses = get_available_statuses(list_data)

            # Test common mappings
            test_cases = [
                ('Complete', ['Closed', 'complete', 'completed']),
                ('Done', ['Closed', 'complete', 'done']),
                ('In Dev', ['in development', 'in progress']),
                ('WIP', ['in development', 'in progress']),
            ]

            for user_input, possible_matches in test_cases:
                result = map_status(user_input, available_statuses)
                if result:
                    # Verify it mapped to one of the expected statuses
                    self.assertTrue(
                        any(match.lower() in result.lower() for match in possible_matches),
                        f"Mapped '{user_input}' to '{result}', expected one of {possible_matches}"
                    )

        except SkipTest:
            raise  # Re-raise skip exceptions
        except Exception as e:
            self.fail(f"Integration test failed: {e}")

    def test_task_status_update_with_mapping(self):
        """Test updating task status using mapped status."""
        try:
            test_list_id = os.getenv('TEST_LIST_ID')
            if not test_list_id:
                self.skipTest("TEST_LIST_ID not set")

            # Create test task
            task = self.client.create_task(
                test_list_id,
                name="[TEST] Status Mapping Test"
            )

            # Get list data for mapping
            list_data = self.client.get_list(test_list_id)
            available_statuses = get_available_statuses(list_data)

            # Try to map 'Complete' to actual status
            mapped_status = map_status('Complete', available_statuses)

            if mapped_status:
                # Update task with mapped status
                updated = self.client.update_task(task['id'], status=mapped_status)

                # Verify status was updated
                self.assertEqual(
                    updated['status']['status'] if isinstance(updated['status'], dict) else updated['status'],
                    mapped_status
                )

            # Cleanup
            self.client.delete_task(task['id'])

        except SkipTest:
            raise  # Re-raise skip exceptions
        except Exception as e:
            self.fail(f"Integration test failed: {e}")


@skipIf(not HAS_CREDENTIALS, SKIP_MESSAGE)
class TestDocContentAlignmentIntegration(unittest.TestCase):
    """Integration tests for doc content formatting with real data."""

    @classmethod
    def setUpClass(cls):
        """Set up client and docs API."""
        cls.client = ClickUpClient()
        cls.docs_api = DocsAPI(cls.client)

    def test_doc_creation_without_none_page(self):
        """Test that creating doc with pages doesn't create extra None page."""
        try:
            workspace_id = os.getenv('TEST_WORKSPACE_ID')
            if not workspace_id:
                self.skipTest("TEST_WORKSPACE_ID not set")

            # Create doc with multiple pages
            pages = [
                {'name': 'Introduction', 'content': '# Introduction\\n\\nThis is the intro.'},
                {'name': 'Setup', 'content': '# Setup\\n\\nSetup instructions.'},
            ]

            result = self.docs_api.create_doc_with_pages(
                workspace_id=workspace_id,
                doc_name='[TEST] Alignment Test Doc',
                pages=pages
            )

            doc_id = result['doc']['id']

            # Fetch pages
            fetched_pages = self.docs_api.get_doc_pages(workspace_id, doc_id)

            # Should have exactly 2 pages, not 3
            self.assertEqual(
                len(fetched_pages),
                2,
                f"Expected 2 pages, got {len(fetched_pages)}: {[p.get('name') for p in fetched_pages]}"
            )

            # Verify no 'None' page exists
            page_names = [p.get('name') for p in fetched_pages]
            self.assertNotIn('None', page_names)
            self.assertNotIn('', page_names)

            # Verify expected pages exist
            self.assertIn('Introduction', page_names)
            self.assertIn('Setup', page_names)

            # Cleanup - Note: Doc deletion might not be available in API
            # Manual cleanup may be required
            print(f"\n⚠️  Manual cleanup required: Delete doc {doc_id} from ClickUp UI")

        except SkipTest:
            raise  # Re-raise skip exceptions
        except Exception as e:
            self.fail(f"Integration test failed: {e}")

    def test_page_content_unescaping(self):
        """Test that page content with escaped newlines is properly unescaped."""
        try:
            workspace_id = os.getenv('TEST_WORKSPACE_ID')
            if not workspace_id:
                self.skipTest("TEST_WORKSPACE_ID not set")

            # Create doc with page containing escaped newlines
            pages = [
                {'name': 'Test Page', 'content': 'Line 1\\nLine 2\\n\\nLine 3'},
            ]

            result = self.docs_api.create_doc_with_pages(
                workspace_id=workspace_id,
                doc_name='[TEST] Content Escape Test',
                pages=pages
            )

            doc_id = result['doc']['id']
            # Handle different possible response structures
            first_page = result['pages'][0]
            page_id = first_page.get('id') or first_page.get('page', {}).get('id')

            if not page_id:
                self.skipTest(f"Unable to extract page_id from response structure: {list(first_page.keys())}")

            # Fetch the page
            page = self.docs_api.get_page(workspace_id, doc_id, page_id)

            # Get content and unescape
            content = page.get('content', '')
            unescaped = unescape_content(content)

            # Verify newlines were unescaped
            self.assertIn('\n', unescaped)
            self.assertIn('Line 1', unescaped)
            self.assertIn('Line 2', unescaped)
            self.assertIn('Line 3', unescaped)

            # Cleanup
            print(f"\n⚠️  Manual cleanup required: Delete doc {doc_id} from ClickUp UI")

        except SkipTest:
            raise  # Re-raise skip exceptions
        except Exception as e:
            self.fail(f"Integration test failed: {e}")


@skipIf(not HAS_CREDENTIALS, SKIP_MESSAGE)
class TestAlignmentVisualVerification(unittest.TestCase):
    """Visual verification tests - prints formatted output for manual inspection."""

    @classmethod
    def setUpClass(cls):
        """Set up client."""
        cls.client = ClickUpClient()
        cls.formatter = TaskDetailFormatter(cls.client)

    def test_print_formatted_task(self):
        """Print a formatted task for visual verification of alignment."""
        try:
            # Get a real task from environment
            test_task_id = os.getenv('TEST_TASK_ID')
            if not test_task_id:
                self.skipTest("TEST_TASK_ID not set - cannot verify formatting")

            # Fetch task
            task = self.client.get_task(test_task_id)

            # Format with and without colors
            options_no_color = FormatOptions(colorize_output=False)
            options_color = FormatOptions(colorize_output=True)

            print("\n" + "=" * 70)
            print("FORMATTED TASK (No Color):")
            print("=" * 70)
            formatted_no_color = self.formatter.format_detail(task, options_no_color)
            print(formatted_no_color)

            print("\n" + "=" * 70)
            print("FORMATTED TASK (With Color):")
            print("=" * 70)
            formatted_color = self.formatter.format_detail(task, options_color)
            print(formatted_color)

            print("\n" + "=" * 70)
            print("Visual verification: Check that:")
            print("  1. Newlines are properly rendered (not \\n)")
            print("  2. Markdown formatting is applied correctly")
            print("  3. Content alignment looks clean and readable")
            print("  4. No double-escaped characters visible")
            print("=" * 70)

        except SkipTest:
            raise  # Re-raise skip exceptions
        except Exception as e:
            self.fail(f"Visual verification test failed: {e}")


if __name__ == '__main__':
    # Print usage information
    print("\n" + "=" * 70)
    print("INTEGRATION TEST SUITE - Content Formatting & Alignment")
    print("=" * 70)
    print("\nThese tests verify bugfixes work with real ClickUp data.")
    print("\nRequired environment variables:")
    print("  - CLICKUP_API_TOKEN: Your ClickUp API token")
    print("  - TEST_LIST_ID: ID of a list for creating test tasks")
    print("  - TEST_WORKSPACE_ID: ID of workspace for doc tests")
    print("  - TEST_TASK_ID: (Optional) ID of existing task for visual verification")
    print("\nExample:")
    print("  export CLICKUP_API_TOKEN='your_token'")
    print("  export TEST_LIST_ID='123456789'")
    print("  export TEST_WORKSPACE_ID='90151898946'")
    print("  pytest tests/format_tests/test_integration_alignment.py -v -s")
    print("=" * 70 + "\n")

    unittest.main()
