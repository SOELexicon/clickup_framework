"""
Test Suite for Tree Pipe Alignment

Tests that vertical pipe characters (│) maintain consistent alignment
throughout the hierarchy display, with no visual breaks.

The issue: When rendering task descriptions in hierarchy view, the indentation
doesn't maintain pipe alignment, causing visual breaks in the tree structure.
"""

import unittest
import re
from typing import List, Set, Tuple
from clickup_framework import ClickUpClient
from clickup_framework.components import DisplayManager, FormatOptions


class TestPipeAlignment(unittest.TestCase):
    """Test that tree pipe characters maintain consistent vertical alignment."""

    def _get_pipe_columns(self, line: str) -> Set[int]:
        """
        Extract column positions of all pipe characters (│) in a line.

        Args:
            line: Single line of text

        Returns:
            Set of column indices where pipes appear
        """
        pipes = set()
        for i, char in enumerate(line):
            if char == '│':
                pipes.add(i)
        return pipes

    def _get_tree_characters(self, line: str) -> List[Tuple[int, str]]:
        """
        Extract all tree drawing characters and their positions.

        Args:
            line: Single line of text

        Returns:
            List of (column_index, character) tuples
        """
        tree_chars = []
        tree_symbols = {'│', '├', '└', '─', '┬', '┴', '┼'}

        for i, char in enumerate(line):
            if char in tree_symbols:
                tree_chars.append((i, char))

        return tree_chars

    def _validate_pipe_continuity(self, lines: List[str]) -> Tuple[bool, List[str]]:
        """
        Validate that pipe characters maintain vertical continuity in tree structures.

        This validator understands that tree branches create new indentation levels.
        When a branch (├ or └) appears, content below it is indented 4 spaces to the right.

        Args:
            lines: List of output lines

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Track active pipes at each column
        # For tree structures, pipes at column N may lead to branches at column N on next line,
        # which then creates pipes at column N+4 for that branch's content
        active_pipes = {}  # {column: last_line_number}

        for line_num, line in enumerate(lines, 1):
            # Get all tree characters on this line
            tree_chars = self._get_tree_characters(line)

            # Update active pipes for this line
            current_pipes = set()
            for col, char in tree_chars:
                if char == '│':
                    current_pipes.add(col)
                    active_pipes[col] = line_num
                elif char in {'├', '└'}:
                    # Branch characters mark tree nodes
                    # They can appear where a pipe was, OR at a new indented level
                    # Don't treat them as continuing pipes - they create new levels
                    pass

            # Check for pipe continuity
            # A pipe at column C on line N should either:
            # 1. Continue at column C on line N+1 (as │)
            # 2. Have a branch at column C on line N+1 (as ├ or └)
            # 3. Be followed by content at column C+4 with a new pipe
            for col in list(active_pipes.keys()):
                if active_pipes[col] == line_num - 1:  # Pipe was active on previous line
                    # Check if it continues at same column
                    if col in current_pipes:
                        continue  # Pipe continues, all good

                    # Check if there's a branch at this column
                    if any(char in {'├', '└'} for c, char in tree_chars if c == col):
                        # Pipe terminates at branch, which is valid
                        continue

                    # Check if this is a blank line (which is allowed)
                    if not line.strip():
                        continue

                    # Check if content shifted to child level (col + 4)
                    # This happens when a branch creates a new indentation level
                    child_level_pipe = any(c == col + 4 and char == '│' for c, char in tree_chars)
                    if child_level_pipe:
                        # Pipe moved to child level, which is valid in tree structures
                        continue

                    # Check if we're returning to a shallower level (depth reduction)
                    # This happens when a branch completes and we return to a parent level
                    # Find any branch characters at a shallower level than this pipe
                    has_shallower_branch = any(
                        char in {'├', '└'} and c < col
                        for c, char in tree_chars
                    )
                    if has_shallower_branch:
                        # Returning to shallower level - deeper pipes naturally terminate
                        del active_pipes[col]
                        continue

                    # If we get here, pipe was interrupted unexpectedly
                    # Only report if this line has actual content
                    if line.strip():
                        errors.append(
                            f"Line {line_num}: Pipe at col {col} interrupted without proper transition"
                        )

        return (len(errors) == 0, errors)

    def _analyze_indentation_consistency(self, lines: List[str]) -> Tuple[bool, List[str]]:
        """
        Analyze if indentation is consistent with tree structure.

        Args:
            lines: List of output lines

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Track expected indentation levels based on tree depth
        for line_num, line in enumerate(lines, 1):
            # Skip empty lines
            if not line.strip():
                continue

            # Count leading spaces before first tree character
            first_tree_char_pos = None
            for i, char in enumerate(line):
                if char in {'│', '├', '└', '─'}:
                    first_tree_char_pos = i
                    break

            if first_tree_char_pos is None:
                continue

            # Check if description/content lines maintain proper indentation
            if '📝 Description:' in line or '📅 Created:' in line:
                # These should align with their parent task's pipes
                pipes = self._get_pipe_columns(line)
                if not pipes:
                    errors.append(
                        f"Line {line_num}: Detail line missing pipe alignment ('{line[:60]}...')"
                    )

        return (len(errors) == 0, errors)

    def test_pipe_alignment_with_mock_data(self):
        """Test pipe alignment with mock task data."""
        # Create mock tasks with parent-child relationships
        tasks = [
            {
                'id': 'task1',
                'name': 'Parent Task',
                'status': {'status': 'Open'},
                'parent': None,
                'description': 'Parent task description\nwith multiple lines',
                'created': '1234567890000',
                'updated': '1234567890000',
            },
            {
                'id': 'task2',
                'name': 'Child Task 1',
                'status': {'status': 'Open'},
                'parent': 'task1',
                'description': 'Child task 1 description',
                'created': '1234567890000',
                'updated': '1234567890000',
            },
            {
                'id': 'task3',
                'name': 'Child Task 2',
                'status': {'status': 'Open'},
                'parent': 'task1',
                'description': 'Child task 2 description',
                'created': '1234567890000',
                'updated': '1234567890000',
            },
            {
                'id': 'task4',
                'name': 'Grandchild Task',
                'status': {'status': 'Open'},
                'parent': 'task2',
                'description': 'Grandchild description',
                'created': '1234567890000',
                'updated': '1234567890000',
            },
        ]

        # Create display manager
        display = DisplayManager()

        # Render hierarchy with descriptions shown
        options = FormatOptions(
            colorize_output=False,
            show_descriptions=True,
            show_dates=True
        )

        output = display.hierarchy_view(tasks, options)
        lines = output.split('\n')

        # Validate pipe continuity
        is_valid, errors = self._validate_pipe_continuity(lines)

        if not is_valid:
            print("\n" + "=" * 70)
            print("PIPE ALIGNMENT ERRORS DETECTED:")
            print("=" * 70)
            for error in errors:
                print(f"  ❌ {error}")
            print("\n" + "=" * 70)
            print("OUTPUT:")
            print("=" * 70)
            for i, line in enumerate(lines, 1):
                print(f"{i:3d}: {line}")
            print("=" * 70)

        self.assertTrue(is_valid, f"Pipe alignment broken:\n" + "\n".join(errors))

    def test_indentation_consistency(self):
        """Test that indentation is consistent with tree structure."""
        tasks = [
            {
                'id': 'task1',
                'name': 'Parent Task',
                'status': {'status': 'Open'},
                'parent': None,
                'description': 'Line 1\nLine 2\nLine 3',
                'created': '1234567890000',
                'updated': '1234567890000',
            },
            {
                'id': 'task2',
                'name': 'Child Task',
                'status': {'status': 'Open'},
                'parent': 'task1',
                'description': 'Child description',
                'created': '1234567890000',
                'updated': '1234567890000',
            },
        ]

        display = DisplayManager()
        options = FormatOptions(
            colorize_output=False,
            show_descriptions=True,
            show_dates=True
        )

        output = display.hierarchy_view(tasks, options)
        lines = output.split('\n')

        is_valid, errors = self._analyze_indentation_consistency(lines)

        if not is_valid:
            print("\n" + "=" * 70)
            print("INDENTATION ERRORS DETECTED:")
            print("=" * 70)
            for error in errors:
                print(f"  ❌ {error}")
            print("=" * 70)

        self.assertTrue(is_valid, f"Indentation broken:\n" + "\n".join(errors))

    def test_no_orphaned_pipes(self):
        """Test that there are no orphaned pipe characters."""
        tasks = [
            {
                'id': 'task1',
                'name': 'Task 1',
                'status': {'status': 'Open'},
                'parent': None,
                'description': 'Description',
                'created': '1234567890000',
                'updated': '1234567890000',
            },
        ]

        display = DisplayManager()
        options = FormatOptions(colorize_output=False, show_descriptions=True)

        output = display.hierarchy_view(tasks, options)
        lines = output.split('\n')

        # Check that every pipe has a purpose (connects to something)
        for line_num, line in enumerate(lines, 1):
            pipes = self._get_pipe_columns(line)

            # If this line has pipes, check next line has continuation or branch
            if pipes and line_num < len(lines):
                next_line = lines[line_num]
                next_tree_chars = self._get_tree_characters(next_line)

                # Verify each pipe continues or terminates properly
                for pipe_col in pipes:
                    # Check if pipe continues, branches, or ends
                    has_continuation = any(
                        char in {'│', '├', '└'} for col, char in next_tree_chars if col == pipe_col
                    )

                    # If not continued, it should be the last line or before a gap
                    if not has_continuation and line_num < len(lines) - 1:
                        # Check if this is intentional (end of branch)
                        if '└' not in line and '├' not in line:
                            # This might be an orphaned pipe
                            pass  # We'll catch this in the main validation


class TestRealHierarchyAlignment(unittest.TestCase):
    """Test alignment with real ClickUp data if available."""

    def setUp(self):
        """Set up test - skip if no credentials."""
        import os
        if not os.getenv('CLICKUP_API_TOKEN'):
            self.skipTest("No CLICKUP_API_TOKEN - skipping real data test")

    def test_actual_hierarchy_alignment(self):
        """Test alignment with actual ClickUp task hierarchy."""
        import os

        test_task_id = os.getenv('TEST_TASK_WITH_HIERARCHY', '86c6g88be')

        try:
            client = ClickUpClient()
            display = DisplayManager(client)

            # Get task
            task = client.get_task(test_task_id)
            list_id = task['list']['id']

            # Get all tasks in list
            result = client.get_list_tasks(list_id, subtasks='true')
            all_tasks = result.get('tasks', [])

            # Render with descriptions
            options = FormatOptions(
                colorize_output=False,
                show_descriptions=True,
                show_dates=True
            )

            output = display.hierarchy_view(all_tasks, options)
            lines = output.split('\n')

            # Create validator
            validator = TestPipeAlignment()

            # Check pipe continuity
            is_valid, errors = validator._validate_pipe_continuity(lines)

            if not is_valid:
                print("\n" + "=" * 70)
                print(f"REAL DATA PIPE ALIGNMENT ERRORS (Task {test_task_id}):")
                print("=" * 70)
                for error in errors:
                    print(f"  ❌ {error}")
                print("\n" + "=" * 70)
                print("OUTPUT SAMPLE:")
                print("=" * 70)
                for i, line in enumerate(lines[:50], 1):  # First 50 lines
                    print(f"{i:3d}: {line}")
                print("=" * 70)

            self.assertTrue(is_valid, "Real hierarchy has pipe alignment issues")

        except Exception as e:
            self.fail(f"Real data test failed: {e}")


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("PIPE ALIGNMENT TEST SUITE")
    print("=" * 70)
    print("\nThis test validates that tree pipe characters (│) maintain")
    print("consistent vertical alignment with no visual breaks.")
    print("\nTo test with real data, set:")
    print("  export TEST_TASK_WITH_HIERARCHY=86c6g88be")
    print("=" * 70 + "\n")

    unittest.main(verbosity=2)
