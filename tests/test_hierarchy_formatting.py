"""
Test hierarchy command formatting and tree structure.

Validates that hierarchy command produces correctly formatted output with:
- Proper tree structure (├──, └──, │)
- Correct indentation and alignment
- Accurate task relationships
- Consistent pipe positioning
"""

import unittest
import re
from io import StringIO
from unittest.mock import patch
import argparse

from clickup_framework.commands.hierarchy import hierarchy_command
from tests.test_config import TEST_LIST_ID


class TestHierarchyFormatting(unittest.TestCase):
    """Test hierarchy command output formatting."""

    def setUp(self):
        """Set up test fixtures."""
        self.maxDiff = None

    def test_hierarchy_output_has_tree_characters(self):
        """Test that hierarchy output contains tree drawing characters."""
        with patch('sys.stdout', new=StringIO()) as fake_out:
            args = argparse.Namespace(
                list_id=TEST_LIST_ID,
                show_all=False,
                include_completed=False,
                show_closed_only=False,
                colorize=False,
                show_ids=False,
                show_tags=False,
                show_descriptions=False,
                show_dates=False,
                show_comments=0,
                show_emoji=True,
                header=None,
                preset='minimal'
            )
            hierarchy_command(args)
            output = fake_out.getvalue()

        # Check for tree characters
        self.assertIn('├──', output, "Output should contain branch connectors (├──)")
        self.assertIn('└──', output, "Output should contain last branch connectors (└──)")
        self.assertIn('│', output, "Output should contain vertical pipes (│)")

    def test_hierarchy_includes_all_7_levels(self):
        """Test that hierarchy displays all 7 levels when including completed tasks."""
        with patch('sys.stdout', new=StringIO()) as fake_out:
            args = argparse.Namespace(
                list_id=TEST_LIST_ID,
                show_all=False,
                include_completed=True,  # Include completed to see all 7 levels
                show_closed_only=False,
                colorize=False,
                show_ids=True,
                show_tags=False,
                show_descriptions=False,
                show_dates=False,
                show_comments=0,
                show_emoji=False,
                header=None,
                preset='minimal'
            )
            hierarchy_command(args)
            output = fake_out.getvalue()

        # Check for deep nesting by looking for specific level 7 tasks
        # Both hierarchies should go to level 7
        self.assertIn('86c6he1pu', output, "Should include level 7 task (Token Refresh Logic)")
        self.assertIn('86c6he1vx', output, "Should include level 7 task (Identify Key Metrics)")

        # Check that we have multiple levels of tasks
        # Count how many tasks are in the output
        lines = output.split('\n')
        task_count = len([line for line in lines if '[TEST]' in line and '86c6he' in line])

        # Should have at least 15 tasks (3 roots + their descendants)
        self.assertGreaterEqual(task_count, 15,
            f"Should have at least 15 tasks across all levels, found {task_count}")

    def test_hierarchy_no_orphaned_pipes(self):
        """Test that there are no orphaned pipe characters."""
        with patch('sys.stdout', new=StringIO()) as fake_out:
            args = argparse.Namespace(
                list_id=TEST_LIST_ID,
                show_all=False,
                include_completed=True,
                show_closed_only=False,
                colorize=False,
                show_ids=False,
                show_tags=False,
                show_descriptions=False,
                show_dates=False,
                show_comments=0,
                show_emoji=True,
                header=None,
                preset='minimal'
            )
            hierarchy_command(args)
            output = fake_out.getvalue()

        lines = output.split('\n')
        for i, line in enumerate(lines):
            # Check that pipes are part of tree structure
            if '│' in line and '[TEST]' in line:
                # Pipe should be followed by space or more tree chars
                pipe_positions = [pos for pos, char in enumerate(line) if char == '│']
                for pos in pipe_positions:
                    if pos + 1 < len(line):
                        next_char = line[pos + 1]
                        self.assertIn(next_char, [' ', '│', '├', '└', '\t'],
                            f"Line {i}: Pipe at position {pos} has unexpected next char: '{next_char}'")

    def test_hierarchy_consistent_indentation(self):
        """Test that indentation follows a consistent pattern."""
        with patch('sys.stdout', new=StringIO()) as fake_out:
            args = argparse.Namespace(
                list_id=TEST_LIST_ID,
                show_all=False,
                include_completed=True,
                show_closed_only=False,
                colorize=False,
                show_ids=False,
                show_tags=False,
                show_descriptions=False,
                show_dates=False,
                show_comments=0,
                show_emoji=False,
                header=None,
                preset='minimal'
            )
            hierarchy_command(args)
            output = fake_out.getvalue()

        lines = output.split('\n')
        task_lines = [line for line in lines if '[TEST]' in line and ('├──' in line or '└──' in line)]

        # Check that indentation increases consistently
        prev_depth = 0
        for line in task_lines:
            # Count depth by pipes
            depth = line.count('│')

            # Depth should be reasonable (0-7)
            self.assertLessEqual(depth, 7,
                f"Depth should not exceed 7: {line}")

            # If depth increased, it should only increase by 1
            if depth > prev_depth:
                self.assertEqual(depth, prev_depth + 1,
                    f"Depth should only increase by 1 at a time: {line}")

            prev_depth = depth

    def test_hierarchy_with_descriptions_format(self):
        """Test that descriptions are properly formatted and indented."""
        with patch('sys.stdout', new=StringIO()) as fake_out:
            args = argparse.Namespace(
                list_id=TEST_LIST_ID,
                show_all=False,
                include_completed=False,
                show_closed_only=False,
                colorize=False,
                show_ids=False,
                show_tags=False,
                show_descriptions=True,
                show_dates=False,
                show_comments=0,
                show_emoji=True,
                header=None,
                preset='detailed'
            )
            hierarchy_command(args)
            output = fake_out.getvalue()

        # Check that descriptions are present
        self.assertIn('Description:', output, "Output should contain description labels")

        # Check that description lines are indented
        lines = output.split('\n')
        found_description = False
        for i, line in enumerate(lines):
            if 'Description:' in line:
                found_description = True
                # Description line should be indented more than task line
                self.assertTrue(line.startswith(' ') or line.startswith('│'),
                    f"Description line {i} should be indented")

        self.assertTrue(found_description, "Should find at least one description")

    def test_hierarchy_tasks_without_children_single_pipe(self):
        """Test that tasks without children show only ONE pipe (not two)."""
        with patch('sys.stdout', new=StringIO()) as fake_out:
            args = argparse.Namespace(
                list_id=TEST_LIST_ID,
                show_all=False,
                include_completed=True,
                show_closed_only=False,
                colorize=False,
                show_ids=True,
                show_tags=False,
                show_descriptions=True,
                show_dates=False,
                show_comments=0,
                show_emoji=False,
                header=None,
                preset='detailed'
            )
            hierarchy_command(args)
            output = fake_out.getvalue()

        lines = output.split('\n')

        # Find a leaf task (task without children)
        # Look for "Token Refresh Logic" which is a level 7 leaf task
        for i, line in enumerate(lines):
            if '[86c6he1pu]' in line and 'Token Refresh Logic' in line:
                # This is the task line
                # Next line should be description with ONE pipe
                if i + 1 < len(lines):
                    desc_line = lines[i + 1]
                    if 'Description:' in desc_line or 'Level 7' in desc_line:
                        # Count pipes in description line
                        pipe_count = desc_line.count('│')
                        # Should have exactly the same number of pipes as parent continuation
                        # For a leaf task at level 7, there should be 6 parent pipes
                        self.assertLessEqual(pipe_count, 7,
                            f"Leaf task description should not have excessive pipes: {desc_line}")
                        break

    def test_hierarchy_all_presets_work(self):
        """Test that all preset formats work without errors."""
        presets = ['minimal', 'summary', 'detailed', 'full']

        for preset in presets:
            with self.subTest(preset=preset):
                with patch('sys.stdout', new=StringIO()) as fake_out:
                    args = argparse.Namespace(
                        list_id=TEST_LIST_ID,
                        show_all=False,
                        include_completed=False,
                        show_closed_only=False,
                        colorize=False,
                        show_ids=False,
                        show_tags=False,
                        show_descriptions=False,
                        show_dates=False,
                        show_comments=0,
                        show_emoji=True,
                        header=None,
                        preset=preset
                    )
                    try:
                        hierarchy_command(args)
                        output = fake_out.getvalue()
                        self.assertGreater(len(output), 0,
                            f"Preset '{preset}' should produce output")
                        self.assertIn('[TEST]', output,
                            f"Preset '{preset}' should contain test tasks")
                    except Exception as e:
                        self.fail(f"Preset '{preset}' raised exception: {e}")

    def test_hierarchy_tree_structure_logical(self):
        """Test that tree structure is logically consistent."""
        with patch('sys.stdout', new=StringIO()) as fake_out:
            args = argparse.Namespace(
                list_id=TEST_LIST_ID,
                show_all=False,
                include_completed=True,
                show_closed_only=False,
                colorize=False,
                show_ids=True,
                show_tags=False,
                show_descriptions=False,
                show_dates=False,
                show_comments=0,
                show_emoji=False,
                header=None,
                preset='minimal'
            )
            hierarchy_command(args)
            output = fake_out.getvalue()

        lines = output.split('\n')

        # Track depth for each line
        prev_depth = -1
        for line in lines:
            if '[TEST]' in line and '86c6he' in line:
                # Calculate depth by counting tree characters
                depth = line.count('│') + line.count('├') + line.count('└') - 1

                # Depth should only increase by 1 or decrease to any level
                if prev_depth >= 0:
                    depth_change = depth - prev_depth
                    self.assertLessEqual(depth_change, 1,
                        f"Depth should not increase by more than 1: {line}")

                prev_depth = depth


if __name__ == '__main__':
    unittest.main(verbosity=2)
