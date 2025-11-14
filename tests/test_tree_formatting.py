"""
Tests for tree formatting and hierarchy display.

Tests the TreeFormatter class to ensure proper formatting of hierarchical structures
with correct indentation, pipe characters, and metadata line handling.
"""

import unittest
from clickup_framework.components.tree import TreeFormatter


class TestTreeFormatting(unittest.TestCase):
    """Test tree formatting with proper indentation and structure."""

    def test_no_stray_pipe_after_header(self):
        """Test that there's no stray pipe character after the header."""
        items = [
            {'id': '1', 'name': 'Task 1'},
        ]

        def format_fn(item):
            return f"[{item['id']}] {item['name']}"

        def get_children_fn(item):
            return []

        result = TreeFormatter.render(
            items,
            format_fn,
            get_children_fn,
            header="Test Header"
        )

        lines = result.split('\n')
        # Line 0 is header
        # Line 1 should be blank, NOT a pipe
        # Line 2 should be the task
        self.assertEqual(lines[0], "Test Header")
        self.assertEqual(lines[1], "")
        self.assertIn("[1] Task 1", lines[2])

    def test_metadata_lines_properly_indented(self):
        """Test that metadata lines (like dates) are properly indented without extra pipes."""
        items = [
            {'id': '1', 'name': 'Task 1', 'has_children': True},
        ]

        def format_fn(item):
            # Return multi-line content (like task with dates)
            return f"[{item['id']}] {item['name']}\n  📅 Created: 2025-11-14"

        def get_children_fn(item):
            if item['id'] == '1':
                return [{'id': '2', 'name': 'Subtask', 'has_children': False}]
            return []

        result = TreeFormatter.render(
            items,
            format_fn,
            get_children_fn
        )

        lines = result.split('\n')

        # Find the date line
        date_line = None
        for i, line in enumerate(lines):
            if '📅 Created' in line:
                date_line = line
                date_line_idx = i
                break

        self.assertIsNotNone(date_line, "Date line not found in output")

        # Date line SHOULD have pipe characters to show it belongs to the task above
        # and continues the tree structure
        # Format: "    │     📅 Created: 2025-11-14" (for root level with children)
        self.assertTrue('│' in date_line,
                        f"Date line should have pipe marker: {date_line}")

        # Date line should be properly indented with child_prefix + "│   "
        # At root level with children, this is "    │     "
        self.assertTrue(date_line.startswith('    │     '),
                       f"Date line should start with proper pipe indentation: {repr(date_line)}")

    def test_deep_hierarchy_alignment(self):
        """Test that deep hierarchies maintain proper alignment."""
        # Create a 3-level hierarchy
        items = [
            {'id': '1', 'name': 'Level 1', 'level': 1},
        ]

        def format_fn(item):
            return f"[{item['id']}] Level {item['level']}\n  📅 Date line"

        def get_children_fn(item):
            level = item['level']
            if level < 3:
                return [{'id': f'{item["id"]}.1', 'name': f'Level {level+1}', 'level': level+1}]
            return []

        result = TreeFormatter.render(
            items,
            format_fn,
            get_children_fn
        )

        lines = result.split('\n')

        # Check that each level is properly indented
        # Level 1 should start at column 0
        # Level 2 should start after 4 chars (├── )
        # Level 3 should start after 8 chars (├── ... ├── )

        for line in lines:
            # Date lines SHOULD have pipes before them to show tree structure continuation
            if '📅' in line:
                self.assertTrue('│' in line[:line.index('📅')],
                               f"Date line should have pipe before date marker: {line}")

    def test_last_item_indentation(self):
        """Test that last items use proper spacing without vertical pipes."""
        items = [
            {'id': '1', 'name': 'Task 1'},
            {'id': '2', 'name': 'Task 2'},  # Last item
        ]

        def format_fn(item):
            return f"[{item['id']}] {item['name']}\n  📅 Date"

        def get_children_fn(item):
            return []

        result = TreeFormatter.render(
            items,
            format_fn,
            get_children_fn
        )

        lines = result.split('\n')

        # Task 1 should use ├──
        # Task 2 should use └──
        self.assertIn('├──', lines[0])
        self.assertIn('└──', lines[2])

    def test_children_alignment(self):
        """Test that children are properly aligned under parents."""
        items = [
            {'id': '1', 'name': 'Parent'},
        ]

        def format_fn(item):
            return f"[{item['id']}] {item['name']}\n  📅 Date"

        def get_children_fn(item):
            if item['id'] == '1':
                return [
                    {'id': '1.1', 'name': 'Child 1'},
                    {'id': '1.2', 'name': 'Child 2'},
                ]
            return []

        result = TreeFormatter.render(
            items,
            format_fn,
            get_children_fn
        )

        lines = result.split('\n')

        # Children should be indented exactly 4 characters from parent
        parent_line = None
        child_lines = []

        for line in lines:
            if 'Parent' in line:
                parent_line = line
            elif 'Child' in line:
                child_lines.append(line)

        self.assertEqual(len(child_lines), 2)

        # Each child should start with 4 spaces (no initial indent) + ├── or └──
        for child in child_lines:
            # Find the branch character
            self.assertTrue('──' in child, f"Child line missing branch: {child}")

    def test_header_without_root_connector(self):
        """Test that header doesn't add a root connector pipe."""
        items = [{'id': '1', 'name': 'Task'}]

        def format_fn(item):
            return f"{item['name']}"

        def get_children_fn(item):
            return []

        # Test with show_root_connector=False (default)
        result = TreeFormatter.render(
            items,
            format_fn,
            get_children_fn,
            header="Header",
            show_root_connector=False
        )

        lines = result.split('\n')
        # Should NOT have a pipe on line 1
        self.assertNotEqual(lines[1], "│")
        self.assertEqual(lines[1], "")

    def test_multiline_content_without_children(self):
        """Test multiline content for tasks without children."""
        items = [{'id': '1', 'name': 'Task', 'has_children': False}]

        def format_fn(item):
            return "Task Line 1\n  Metadata Line 2\n  Metadata Line 3"

        def get_children_fn(item):
            return []

        result = TreeFormatter.render(
            items,
            format_fn,
            get_children_fn
        )

        lines = result.split('\n')

        # Metadata lines should be indented properly with pipe to show continuation
        # For a task without children (last item), the format is:
        # "    │   Metadata" (4 spaces + pipe + 3 spaces)
        for i, line in enumerate(lines):
            if i > 0 and 'Metadata' in line:
                # Should have proper pipe indentation
                self.assertTrue(line.startswith('    │   '),
                              f"Metadata line {i} not properly indented: {repr(line)}")
                self.assertTrue('│' in line[:8],
                               f"Metadata line {i} should have pipe in indentation: {repr(line)}")


if __name__ == '__main__':
    unittest.main()
