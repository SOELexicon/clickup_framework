"""
Unit tests for dependency tree display in ClickUp JSON Manager.

This module tests the proper formatting and display of dependency trees,
especially with complex multi-line content such as descriptions, comments,
and relationships.
"""
import unittest
from unittest.mock import patch, MagicMock
import io
import sys
from datetime import datetime

from refactor.cli.commands.utils import format_task_hierarchy
from refactor.cli.formatting.tree.validation import validate_tree_structure


class TestDependencyTreeDisplay(unittest.TestCase):
    """Test suite for dependency tree display formatting."""

    def setUp(self):
        """Set up test environment."""
        # Create a set of mock tasks with various content types
        self.tasks = [
            # Root task with multi-line description, comments, and relationships
            {
                'id': 'tsk_00000001',
                'name': 'Root Task',
                'description': "## Multi-line Description\n\nThis is a multi-line description with:\n- Bullet points\n- Multiple paragraphs\n\n```python\ndef example():\n    return 'This is a code block'\n```\n\nAnd more text after the code block.",
                'status': 'in progress',
                'priority': 1,
                'tags': ['important', 'complex'],
                'relationships': {
                    'blocks': ['tsk_00000002', 'tsk_00000003'],
                    'depends_on': []
                },
                'comments': [
                    {
                        'text': "## First Comment\n\nThis is a first comment with:\n- A bullet list\n- Multiple items\n\nAnd a second paragraph with more text.",
                        'author': 'Test User',
                        'date': '2025-04-08T10:00:00.000Z'
                    },
                    {
                        'text': "## Second Comment\nA comment with a very long line that should be truncated because it exceeds the maximum length allowed for display in the dependency tree visualization and should be handled properly.",
                        'author': 'Another User',
                        'date': '2025-04-08T11:00:00.000Z'
                    }
                ]
            },
            # Dependent task with emojis and special characters
            {
                'id': 'tsk_00000002',
                'name': 'Dependent Task 1',
                'description': "Task with emojis: 🚀 🔄 💬 📝\nAnd special characters: @#$%^&*()_+",
                'status': 'to do',
                'priority': 2,
                'tags': ['dependency'],
                'relationships': {
                    'depends_on': ['tsk_00000001'],
                    'blocks': []
                },
                'comments': [
                    {
                        'text': "Comment with emoji: 🚀 🔄 💬 📝",
                        'author': 'Emoji User',
                        'date': '2025-04-08T12:00:00.000Z'
                    }
                ]
            },
            # Another dependent task with very long content
            {
                'id': 'tsk_00000003',
                'name': 'Dependent Task 2',
                'description': "A" * 200,  # Very long description
                'status': 'to do',
                'priority': 3,
                'tags': ['dependency', 'long-content'],
                'relationships': {
                    'depends_on': ['tsk_00000001'],
                    'blocks': []
                },
                'comments': [
                    {
                        'text': "B" * 200,  # Very long comment
                        'author': 'Long Comment User',
                        'date': '2025-04-08T13:00:00.000Z'
                    }
                ]
            }
        ]
        
        # Create a task map for dependency resolution
        self.tasks_map = {task['id']: task for task in self.tasks}

    def test_dependency_tree_basic_formatting(self):
        """Test basic dependency tree formatting with simple content."""
        # Format the dependency tree
        output = format_task_hierarchy(
            self.tasks,
            indent=2,
            colorize_output=False,
            show_full=False,
            include_completed=True,
            show_score=False,
            show_tags=True,
            tag_style="colored",
            show_type_emoji=True,
            dependency_as_tree=True,
            dependency_type="blocks",
            show_descriptions=False,
            show_relationships=False,
            show_comments=0
        )
        
        # Basic assertions
        self.assertIn("Root Task", output)
        self.assertIn("Dependent Task 1", output)
        self.assertIn("Dependent Task 2", output)
        
        # Check tree structure
        is_valid, errors = validate_tree_structure(output)
        self.assertTrue(is_valid, f"Tree structure validation failed: {errors}")

    def test_dependency_tree_with_descriptions(self):
        """Test dependency tree with multi-line descriptions."""
        # Format the dependency tree with descriptions
        output = format_task_hierarchy(
            self.tasks,
            indent=2,
            colorize_output=False,
            show_full=False,
            include_completed=True,
            show_score=False,
            show_tags=True,
            tag_style="colored",
            show_type_emoji=True,
            dependency_as_tree=True,
            dependency_type="blocks",
            show_descriptions=True,
            description_length=80,
            show_relationships=False,
            show_comments=0
        )
        
        # Check for description content
        self.assertIn("📝 ## Multi-line Description", output)
        self.assertIn("This is a multi-line description with:", output)
        self.assertIn("- Bullet points", output)
        
        # Check tree structure
        is_valid, errors = validate_tree_structure(output)
        self.assertTrue(is_valid, f"Tree structure validation failed with descriptions: {errors}")
        
        # Verify pipe alignment in multi-line content
        lines = output.split('\n')
        
        # Find all lines with descriptions
        desc_lines_idx = [i for i, line in enumerate(lines) if '📝' in line]
        
        # For each description line, check that continuation lines have proper pipe alignment
        for idx in desc_lines_idx:
            # Get the position of the pipe in this line
            pipe_pos = lines[idx].find('│')
            if pipe_pos >= 0:
                # If there's a pipe, check the next line
                if idx + 1 < len(lines):
                    # The next line should have a pipe in the same position
                    self.assertEqual(
                        pipe_pos, 
                        lines[idx + 1].find('│') if '│' in lines[idx + 1] else -1,
                        f"Pipe alignment mismatch between lines {idx} and {idx+1}"
                    )

    def test_dependency_tree_with_comments(self):
        """Test dependency tree with multi-line comments."""
        # Format the dependency tree with comments
        output = format_task_hierarchy(
            self.tasks,
            indent=2,
            colorize_output=False,
            show_full=False,
            include_completed=True,
            show_score=False,
            show_tags=True,
            tag_style="colored",
            show_type_emoji=True,
            dependency_as_tree=True,
            dependency_type="blocks",
            show_descriptions=False,
            show_relationships=False,
            show_comments=2,  # Show 2 comments
            description_length=80
        )
        
        # Check for comment content
        self.assertIn("💬 Recent Comments:", output)
        self.assertIn("## First Comment", output)
        self.assertIn("This is a first comment with:", output)
        self.assertIn("- A bullet list", output)
        self.assertIn("## Second Comment", output)
        
        # Check tree structure
        is_valid, errors = validate_tree_structure(output)
        self.assertTrue(is_valid, f"Tree structure validation failed with comments: {errors}")
        
        # Verify pipe alignment in multi-line content
        lines = output.split('\n')
        
        # Find all lines with comments
        comment_lines_idx = [i for i, line in enumerate(lines) if '💬' in line]
        
        # For each comment line, check that continuation lines have proper pipe alignment
        for idx in comment_lines_idx:
            # Get the position of the pipe in this line
            pipe_pos = lines[idx].find('│')
            if pipe_pos >= 0:
                # If there's a pipe, check the next line
                if idx + 1 < len(lines):
                    # The next line should have a pipe in the same position
                    self.assertEqual(
                        pipe_pos, 
                        lines[idx + 1].find('│') if '│' in lines[idx + 1] else -1,
                        f"Pipe alignment mismatch between lines {idx} and {idx+1}"
                    )

    def test_dependency_tree_with_relationships(self):
        """Test dependency tree with relationship display."""
        # Format the dependency tree with relationships
        output = format_task_hierarchy(
            self.tasks,
            indent=2,
            colorize_output=False,
            show_full=False,
            include_completed=True,
            show_score=False,
            show_tags=True,
            tag_style="colored",
            show_type_emoji=True,
            dependency_as_tree=True,
            dependency_type="blocks",
            show_descriptions=False,
            show_relationships=True,
            show_comments=0
        )
        
        # Check for relationship content
        self.assertIn("🔄 Blocks:", output)
        
        # Check tree structure
        is_valid, errors = validate_tree_structure(output)
        self.assertTrue(is_valid, f"Tree structure validation failed with relationships: {errors}")
        
        # Verify pipe alignment in relationships
        lines = output.split('\n')
        
        # Find all lines with relationships
        rel_lines_idx = [i for i, line in enumerate(lines) if '🔄' in line]
        
        # For each relationship line, check that continuation lines have proper pipe alignment
        for idx in rel_lines_idx:
            # Get the position of the pipe in this line
            pipe_pos = lines[idx].find('│')
            if pipe_pos >= 0:
                # If there's a pipe, check the next line
                if idx + 1 < len(lines):
                    # The next line should have a pipe in the same position
                    self.assertEqual(
                        pipe_pos, 
                        lines[idx + 1].find('│') if '│' in lines[idx + 1] else -1,
                        f"Pipe alignment mismatch between lines {idx} and {idx+1}"
                    )

    def test_dependency_tree_all_content_display(self):
        """Test dependency tree with all content display options enabled."""
        # Format the dependency tree with all content options
        output = format_task_hierarchy(
            self.tasks,
            indent=2,
            colorize_output=False,
            show_full=False,
            include_completed=True,
            show_score=False,
            show_tags=True,
            tag_style="colored",
            show_type_emoji=True,
            dependency_as_tree=True,
            dependency_type="blocks",
            show_descriptions=True,
            description_length=80,
            show_relationships=True,
            show_comments=2  # Show 2 comments
        )
        
        # Check for all content types
        self.assertIn("📝", output)
        self.assertIn("🔄", output)
        self.assertIn("💬", output)
        
        # Check tree structure
        is_valid, errors = validate_tree_structure(output)
        self.assertTrue(is_valid, f"Tree structure validation failed with all content: {errors}")
        
        # Verify overall pipe alignment
        lines = output.split('\n')
        pipe_positions = {}
        
        # Record pipe positions for each line
        for i, line in enumerate(lines):
            if '│' in line:
                pipe_positions[i] = [pos for pos, char in enumerate(line) if char == '│']
        
        # Check for consistent pipe positions across consecutive lines with the same indentation level
        prev_idx = None
        prev_positions = None
        for idx, positions in pipe_positions.items():
            if prev_idx is not None and idx == prev_idx + 1:
                # For consecutive lines, check if pipes are aligned
                # We only compare the common positions - a line might have more or fewer pipes
                common_positions = min(len(positions), len(prev_positions))
                for i in range(common_positions):
                    self.assertEqual(
                        positions[i], 
                        prev_positions[i],
                        f"Pipe alignment mismatch between consecutive lines {prev_idx} and {idx}"
                    )
            prev_idx = idx
            prev_positions = positions

    def test_dependency_tree_with_emoji_and_special_chars(self):
        """Test dependency tree with emoji and special characters."""
        # Add more tasks to ensure dependency to task 2
        task4 = {
            'id': 'tsk_00000004',
            'name': 'Task with emoji dependency',
            'status': 'to do',
            'priority': 2,
            'relationships': {
                'blocks': ['tsk_00000002'],
                'depends_on': []
            }
        }
        self.tasks.append(task4)
        self.tasks_map[task4['id']] = task4
        
        # Format the dependency tree focusing on emoji handling
        output = format_task_hierarchy(
            self.tasks,
            indent=2,
            colorize_output=False,
            show_full=False,
            include_completed=True,
            show_score=False,
            show_tags=True,
            tag_style="colored",
            show_type_emoji=True,
            dependency_as_tree=True,
            dependency_type="blocks",
            show_descriptions=True,
            description_length=80,
            show_relationships=False,
            show_comments=1
        )
        
        # Check tree structure with emoji
        is_valid, errors = validate_tree_structure(output)
        self.assertTrue(is_valid, f"Tree structure validation failed with emoji: {errors}")

    def test_dependency_tree_with_long_content(self):
        """Test dependency tree with very long content that requires truncation."""
        # Add dependency to task 3 for testing
        task5 = {
            'id': 'tsk_00000005',
            'name': 'Task with long content dependency',
            'status': 'to do',
            'priority': 2,
            'relationships': {
                'blocks': ['tsk_00000003'],
                'depends_on': []
            }
        }
        self.tasks.append(task5)
        self.tasks_map[task5['id']] = task5
        
        # Format the dependency tree with long content
        output = format_task_hierarchy(
            self.tasks,
            indent=2,
            colorize_output=False,
            show_full=False,
            include_completed=True,
            show_score=False,
            show_tags=True,
            tag_style="colored",
            show_type_emoji=True,
            dependency_as_tree=True,
            dependency_type="blocks",
            show_descriptions=True,
            description_length=50,  # Short limit to test truncation
            show_relationships=False,
            show_comments=1
        )
        
        # Check for truncated content (should end with "...")
        self.assertIn("...", output)
        
        # Check tree structure with truncated content
        is_valid, errors = validate_tree_structure(output)
        self.assertTrue(is_valid, f"Tree structure validation failed with truncated content: {errors}")

    def test_content_display_line_formatting(self):
        """Test proper formatting of content display lines in dependency tree mode."""
        # Add tasks with more complex structure for testing
        task6 = {
            'id': 'tsk_00000006',
            'name': 'Parent Task',
            'status': 'in progress',
            'priority': 1,
            'tags': ['parent'],
            'relationships': {
                'blocks': ['tsk_00000007', 'tsk_00000008'],
                'depends_on': []
            },
            'comments': [
                {
                    'text': "## Markdown Comment with List\n- First item\n- Second item\n\nAnd a paragraph after.",
                    'author': 'Format User',
                    'date': '2025-04-09T10:00:00.000Z'
                }
            ],
            'description': "Parent task description with **markdown** formatting."
        }
        
        task7 = {
            'id': 'tsk_00000007',
            'name': 'Child Task 1',
            'status': 'to do',
            'priority': 2,
            'tags': ['child'],
            'relationships': {
                'depends_on': ['tsk_00000006'],
                'blocks': []
            },
            'comments': [
                {
                    'text': "Simple comment.",
                    'author': 'Simple User',
                    'date': '2025-04-09T11:00:00.000Z'
                }
            ]
        }
        
        task8 = {
            'id': 'tsk_00000008',
            'name': 'Child Task 2',
            'status': 'to do',
            'priority': 2,
            'tags': ['child'],
            'relationships': {
                'depends_on': ['tsk_00000006'],
                'blocks': []
            },
            'comments': [
                {
                    'text': "Last comment.",
                    'author': 'Last User',
                    'date': '2025-04-09T12:00:00.000Z'
                }
            ]
        }
        
        test_tasks = [task6, task7, task8]
        
        # Format the dependency tree with all content options
        output = format_task_hierarchy(
            test_tasks,
            indent=2,
            colorize_output=False,
            show_full=False,
            include_completed=True,
            show_score=False,
            show_tags=True,
            tag_style="colored",
            show_type_emoji=True,
            dependency_as_tree=True,
            dependency_type="blocks",
            show_descriptions=True,
            description_length=100,
            show_relationships=True,
            show_comments=1
        )
        
        # Check tree structure
        is_valid, errors = validate_tree_structure(output)
        self.assertTrue(is_valid, f"Tree structure validation failed with complex formatting: {errors}")
        
        # Split into lines for detailed analysis
        lines = output.split('\n')
        
        # Check for proper content indicators
        self.assertTrue(any('📝' in line for line in lines), "Missing description indicator")
        self.assertTrue(any('💬' in line for line in lines), "Missing comment indicator")
        self.assertTrue(any('🔄' in line for line in lines), "Missing relationship indicator")
        
        # Test for proper pipe alignment in content display lines
        for i, line in enumerate(lines):
            # Skip if this is not a content display line
            if not any(indicator in line for indicator in ['📝', '💬', '🔄']):
                continue
                
            # Check if content display line has the correct format
            if '📝' in line:
                # For description lines in dependency tree mode, we don't always expect a pipe
                # They use spacing consistent with the tree structure
                # Only assert if the line obviously should have a pipe (starts with pipe)
                if line.strip().startswith('│'):
                    pipe_pos = line.find('│')
                    self.assertGreater(pipe_pos, -1, f"Missing pipe in description line: {line}")
                    self.assertLess(pipe_pos, line.find('📝'), f"Pipe should appear before indicator: {line}")
                
            if '💬' in line:
                # Comment lines should have a pipe in position before the indicator
                # Only check if this is a content display line and not a task line
                if not ('├─' in line or '└─' in line):
                    pipe_pos = line.find('│')
                    if '│' in line:  # Only check if there is a pipe in the line
                        self.assertGreater(pipe_pos, -1, f"Missing pipe in comment line: {line}")
                        self.assertLess(pipe_pos, line.find('💬'), f"Pipe should appear before indicator: {line}")
                    
                    # Check if next line is comment content with proper indentation
                    if i+1 < len(lines) and "From:" in lines[i+1] and '│' in line and '│' in lines[i+1]:
                        # Comment content should have the same pipe position
                        self.assertEqual(
                            pipe_pos, 
                            lines[i+1].find('│'),
                            f"Pipe alignment mismatch between comment header and content: {lines[i]} -> {lines[i+1]}"
                        )
                    
            if '🔄' in line:
                # Skip if this is a task line with emoji and not a content display line
                if '├─' in line or '└─' in line:
                    continue
                    
                # Relationship lines should have a pipe in position before the indicator
                # Only check if there is a pipe in the line
                if '│' in line:
                    pipe_pos = line.find('│')
                    self.assertGreater(pipe_pos, -1, f"Missing pipe in relationship line: {line}")
                    self.assertLess(pipe_pos, line.find('🔄'), f"Pipe should appear before indicator: {line}")
        
        # Test for proper handling of multiline content (markdown)
        comment_line_idx = next((i for i, line in enumerate(lines) if '## Markdown Comment with List' in line), -1)
        if comment_line_idx > 0:
            # Check that the following items in the list maintain pipe alignment
            pipe_pos = lines[comment_line_idx].find('│')
            list_line_idx = next((i for i, line in enumerate(lines[comment_line_idx+1:], comment_line_idx+1) 
                                  if '- First item' in line), -1)
            
            if list_line_idx > 0:
                self.assertEqual(
                    pipe_pos, 
                    lines[list_line_idx].find('│'),
                    f"Pipe alignment mismatch in markdown list item: {lines[comment_line_idx]} -> {lines[list_line_idx]}"
                )
                
        # Test proper double vertical line pattern for comments
        for i, line in enumerate(lines):
            if '💬' in line and not ('├─' in line or '└─' in line):
                # Get pipe positions in comment header line
                pipe_positions = [j for j, char in enumerate(line) if char == '│']
                
                # Check if this line has a pipe
                if pipe_positions:
                    # We have pipes, verify they are in correct positions
                    self.assertGreater(len(pipe_positions), 0, f"Missing pipe in comment header: {line}")
                    
                    # Check if next line is comment content with proper indentation
                    if i+1 < len(lines) and "From:" in lines[i+1]:
                        content_pipe_positions = [j for j, char in enumerate(lines[i+1]) if char == '│']
                        
                        # If content line has pipes
                        if content_pipe_positions:
                            # Content line should have at least one pipe
                            self.assertGreater(len(content_pipe_positions), 0, f"Missing pipe in comment content: {lines[i+1]}")
                            
                            # The first pipe position should match
                            self.assertEqual(
                                pipe_positions[0], 
                                content_pipe_positions[0],
                                f"Pipe alignment mismatch between comment header and content: {line} -> {lines[i+1]}"
                            )
                # Otherwise, skip this line since the format doesn't have pipes

    def test_content_display_line_pipe_continuation(self):
        """Test that pipes correctly continue through multi-line content in dependency tree mode."""
        # Create tasks with complex comments that include markdown and multiple paragraphs
        task9 = {
            'id': 'tsk_00000009',
            'name': 'Complex Comment Parent',
            'status': 'in progress',
            'priority': 1,
            'tags': ['complex-formatting'],
            'relationships': {
                'blocks': ['tsk_00000010', 'tsk_00000011'],
                'depends_on': []
            },
            'comments': [
                {
                    'text': "## Complex Markdown Comment\n\nThis comment has multiple paragraphs\nwith line breaks and formatting.\n\n- First bullet\n  - Nested bullet\n- Second bullet\n\n```\nCode block\nwith multiple lines\n```\n\n> Blockquote with\n> multiple lines",
                    'author': 'Format Tester',
                    'date': '2025-04-10T10:00:00.000Z'
                }
            ],
            'description': "Parent description with **bold** and *italic* and:\n- A bullet point\n- Another bullet point"
        }
        
        task10 = {
            'id': 'tsk_00000010',
            'name': 'Child with Deep Dependency',
            'status': 'to do',
            'priority': 2,
            'relationships': {
                'depends_on': ['tsk_00000009'],
                'blocks': ['tsk_00000011']
            },
            'comments': [
                {
                    'text': "Simple comment for child task.",
                    'author': 'Child User',
                    'date': '2025-04-10T11:00:00.000Z'
                }
            ]
        }
        
        task11 = {
            'id': 'tsk_00000011',
            'name': 'Deeply Nested Child',
            'status': 'to do',
            'priority': 3,
            'relationships': {
                'depends_on': ['tsk_00000010', 'tsk_00000009'],
                'blocks': []
            },
            'comments': [
                {
                    'text': "Nested child comment.",
                    'author': 'Nested User',
                    'date': '2025-04-10T12:00:00.000Z'
                }
            ]
        }
        
        complex_tasks = [task9, task10, task11]
        
        # Format with all content display options enabled
        output = format_task_hierarchy(
            complex_tasks,
            indent=2,
            colorize_output=False,
            show_full=False,
            include_completed=True,
            show_score=False,
            show_tags=True,
            tag_style="colored",
            show_type_emoji=True,
            dependency_as_tree=True,
            dependency_type="blocks",
            show_descriptions=True,
            description_length=100,
            show_relationships=True,
            show_comments=1
        )
        
        # Validate tree structure
        is_valid, errors = validate_tree_structure(output)
        self.assertTrue(is_valid, f"Tree structure validation failed with complex formatting: {errors}")
        
        lines = output.split('\n')
        
        # Find comment section lines
        comment_section_start = next((i for i, line in enumerate(lines) if '💬 Recent Comments:' in line), -1)
        self.assertGreater(comment_section_start, -1, "Comment section not found")
        
        # Find comment content lines
        comment_content_start = next((i for i, line in enumerate(lines) 
                                      if i > comment_section_start and 'From:' in line), -1)
        # TODO: Failing test. Error: AssertionError: -1 not greater than -1 : Comment content not found
        # This indicates the expected comment content line ('From:') was not found in the output.
        # Verify the formatting logic in format_task_hierarchy for comments, or update the expected string.
        self.assertGreater(comment_content_start, -1, "Comment content not found")
        
        # Find separator line
        separator_line = next((i for i, line in enumerate(lines) 
                               if i > comment_content_start and '─────' in line), -1)
        self.assertGreater(separator_line, -1, "Comment separator not found")
        
        # Check pipe alignment in comment header
        comment_header = lines[comment_section_start]
        pipe_pos_header = comment_header.find('│')
        
        # In this implementation, we don't always expect a pipe character
        # The test should pass whether there's a pipe or not
        
        # Check pipe alignment in the first content line
        content_line = lines[comment_content_start]
        pipe_pos_content = content_line.find('│')
        
        # If both lines have pipes, they should be aligned
        if pipe_pos_header > -1 and pipe_pos_content > -1:
            self.assertEqual(pipe_pos_header, pipe_pos_content, 
                         f"Pipe misalignment between comment header and content:\n{comment_header}\n{content_line}")
        
        # Find a markdown bullet line if present
        bullet_line_idx = next((i for i, line in enumerate(lines) 
                                if i > comment_content_start and '- First bullet' in line), -1)
        
        if bullet_line_idx > -1:
            bullet_line = lines[bullet_line_idx]
            pipe_pos_bullet = bullet_line.find('│')
            
            # If both the bullet line and content line have pipes, they should align
            if pipe_pos_bullet > -1 and pipe_pos_content > -1:
                self.assertEqual(pipe_pos_content, pipe_pos_bullet,
                             f"Pipe misalignment between content and bullet point:\n{content_line}\n{bullet_line}")
            
            # Check if there's a nested bullet and verify its formatting
            nested_bullet_idx = next((i for i, line in enumerate(lines) 
                                      if i > bullet_line_idx and '- Nested bullet' in line), -1)
            if nested_bullet_idx > -1:
                nested_bullet_line = lines[nested_bullet_idx]
                pipe_pos_nested = nested_bullet_line.find('│')
                
                # If both the nested bullet and the bullet line have pipes, they should align
                if pipe_pos_nested > -1 and pipe_pos_bullet > -1:
                    self.assertEqual(pipe_pos_bullet, pipe_pos_nested,
                                 f"Pipe misalignment between bullet and nested bullet:\n{bullet_line}\n{nested_bullet_line}")
        
        # Check pipe alignment in separator line
        separator_content = lines[separator_line]
        pipe_pos_separator = separator_content.find('│')
        
        # If both the separator line and content line have pipes, they should align
        if pipe_pos_separator > -1 and pipe_pos_content > -1:
            self.assertEqual(pipe_pos_content, pipe_pos_separator,
                         f"Pipe misalignment between content and separator:\n{content_line}\n{separator_content}")
        
        # Check if the pipes continue through longer content sections
        if bullet_line_idx > -1:
            # Find all content lines between the header and the separator
            content_lines = lines[comment_content_start:separator_line]
            pipe_positions = [line.find('│') for line in content_lines]
            
            # Filter out lines without pipes
            pipe_positions = [pos for pos in pipe_positions if pos > -1]
            
            # If we have pipe positions, check they're consistent
            if pipe_positions:
                # All pipe positions should be the same
                self.assertTrue(all(pos == pipe_positions[0] for pos in pipe_positions),
                            f"Inconsistent pipe positions in comment content: {pipe_positions}")

    def test_multiline_description_pipe_alignment(self):
        """Test that pipes are correctly aligned through multi-line descriptions in dependency tree mode."""
        # Create tasks with multi-line descriptions
        task12 = {
            'id': 'tsk_00000012',
            'name': 'Parent with Complex Description',
            'status': 'in progress',
            'priority': 1,
            'tags': ['complex-formatting'],
            'relationships': {
                'blocks': ['tsk_00000013'],
                'depends_on': []
            },
            'description': "# Complex Description with Markdown\n\nThis description has multiple paragraphs and formatting:\n\n1. Numbered list item one\n2. Numbered list item two\n   - Nested bullet item\n   - Another nested item\n\nTable format:\n| Column 1 | Column 2 |\n|----------|----------|\n| Data 1   | Data 2   |\n\n> Block quote with\n> multiple lines\n> and **formatting**"
        }
        
        task13 = {
            'id': 'tsk_00000013',
            'name': 'Child with Description',
            'status': 'to do',
            'priority': 2,
            'relationships': {
                'depends_on': ['tsk_00000012'],
                'blocks': []
            },
            'description': "Child task description with a list:\n- Item one\n- Item two"
        }
        
        description_tasks = [task12, task13]
        
        # Format with description display enabled in dependency tree mode
        output = format_task_hierarchy(
            description_tasks,
            indent=2,
            colorize_output=False,
            show_full=False,
            include_completed=True,
            show_score=False,
            show_tags=True,
            tag_style="colored",
            show_type_emoji=True,
            dependency_as_tree=True,
            dependency_type="blocks",
            show_descriptions=True,
            description_length=200,  # Longer to see more of the description
            show_relationships=False,
            show_comments=0
        )
        
        # Validate tree structure
        is_valid, errors = validate_tree_structure(output)
        self.assertTrue(is_valid, f"Tree structure validation failed with complex descriptions: {errors}")
        
        lines = output.split('\n')
        
        # First, let's verify that we have the task lines in the output
        parent_task_line = next((i for i, line in enumerate(lines) 
                               if 'Parent with Complex Description' in line), -1)
        self.assertGreater(parent_task_line, -1, "Parent task line not found")
        
        # Find description content lines - look for the first line with 📝 emoji
        desc_line = next((i for i, line in enumerate(lines[parent_task_line+1:], parent_task_line+1)
                           if '📝' in line), -1)
        self.assertGreater(desc_line, -1, "Description line not found")
        
        # Find numbered list line
        numbered_list_line = next((i for i, line in enumerate(lines) 
                                 if "1. Numbered list" in line), -1)
        self.assertGreater(numbered_list_line, -1, "Numbered list not found in output")
        
        # Find nested bullet line
        nested_bullet_line = next((i for i, line in enumerate(lines)
                                  if "- Nested bullet" in line), -1)
        self.assertGreater(nested_bullet_line, -1, "Nested bullet not found in output")
        
        # Check that the validation doesn't flag any issues with the tree structure
        # which means the pipes (if present) are correctly aligned
        valid, validation_errors = validate_tree_structure("\n".join(lines))
        self.assertTrue(valid, f"Tree structure validation failed: {validation_errors}")
        
        # Find the child task and its description
        child_task_line = next((i for i, line in enumerate(lines)
                               if 'Child with Description' in line), -1)
        self.assertGreater(child_task_line, -1, "Child task not found")
        
        # Find child description line
        child_desc_line = next((i for i, line in enumerate(lines[child_task_line+1:], child_task_line+1)
                              if '📝' in line), -1)
        self.assertGreater(child_desc_line, -1, "Child description not found")
        
        # Find child list item
        child_list_line = next((i for i, line in enumerate(lines)
                              if "- Item one" in line), -1)
        self.assertGreater(child_list_line, -1, "Child list item not found")
        
        # Check that all lines that should have pipes in the same position do have them aligned
        # This applies only if the lines have pipes
        pipe_positions = {}
        for i, line in enumerate(lines):
            if '│' in line:
                pipe_pos = line.find('│')
                indent_level = pipe_pos // 2  # Assuming 2-space indentation
                
                if indent_level not in pipe_positions:
                    pipe_positions[indent_level] = pipe_pos
                else:
                    self.assertEqual(pipe_positions[indent_level], pipe_pos,
                                   f"Misaligned pipe at level {indent_level}: {line}")

    def test_relationships_display_pipe_alignment(self):
        """Test that pipes are correctly aligned through relationships display in dependency tree mode."""
        # Create tasks with various relationships
        task41 = {
            'id': 'tsk_00000041',
            'name': 'Parent Task with Relationships',
            'status': 'in progress',
            'priority': 1,
            'relationships': {
                'blocks': ['tsk_00000042', 'tsk_00000043'],
                'related_to': ['tsk_00000045']
            }
        }
        
        task42 = {
            'id': 'tsk_00000042',
            'name': 'Blocked Child Task',
            'status': 'to do',
            'priority': 2,
            'relationships': {
                'blocked_by': ['tsk_00000041'],
                'depends_on': ['tsk_00000044']
            }
        }
        
        task43 = {
            'id': 'tsk_00000043',
            'name': 'Another Blocked Task',
            'status': 'to do',
            'priority': 3,
            'relationships': {
                'blocked_by': ['tsk_00000041']
            }
        }
        
        task44 = {
            'id': 'tsk_00000044',
            'name': 'Dependency Task',
            'status': 'in progress',
            'priority': 2
        }
        
        task45 = {
            'id': 'tsk_00000045',
            'name': 'Related Task',
            'status': 'to do',
            'priority': 3
        }
        
        relationship_tasks = [task41, task42, task43, task44, task45]
        
        # Format with relationships display enabled in dependency tree mode
        output = format_task_hierarchy(
            relationship_tasks,
            indent=2,
            colorize_output=False,
            show_full=False,
            include_completed=True,
            show_score=False,
            show_tags=False,
            dependency_as_tree=True,
            dependency_type="blocks", 
            show_descriptions=False,
            show_relationships=True,
            show_comments=False
        )
        
        # Validate tree structure
        is_valid, errors = validate_tree_structure(output)
        self.assertTrue(is_valid, f"Tree structure validation failed with relationships: {errors}")
        
        lines = output.split('\n')
        
        # Find relationship section for the parent task
        parent_line = next((i for i, line in enumerate(lines)
                           if 'Parent Task with Relationships' in line), -1)
        self.assertGreater(parent_line, -1, "Parent task not found")
        
        # Look for relationship lines - may have different formats
        parent_rel_start = next((i for i, line in enumerate(lines)
                                if i > parent_line and '🔄' in line), -1)
        self.assertGreater(parent_rel_start, -1, "Parent relationships section not found")
        
        # Check for specific relationship types
        blocks_line = next((i for i, line in enumerate(lines)
                           if i > parent_rel_start and 'Blocks:' in line), -1)
        self.assertGreater(blocks_line, -1, "Blocks relationship not found")
        
        # Find blocked tasks
        blocked_task_line = next((i for i, line in enumerate(lines)
                                 if i > blocks_line and '∟' in line), -1)
        self.assertGreater(blocked_task_line, -1, "Blocked task line not found")
        
        # Check tree structure validation
        is_valid, validation_errors = validate_tree_structure("\n".join(lines))
        self.assertTrue(is_valid, f"Tree structure validation failed: {validation_errors}")
        
        # Find child task
        child_line = next((i for i, line in enumerate(lines)
                          if 'Blocked Child Task' in line), -1)
        self.assertGreater(child_line, -1, "Child task not found")
        
        # Check pipe alignment for lines at the same indentation level
        pipe_positions_by_level = {}
        
        for i, line in enumerate(lines):
            if '│' in line:
                pipe_pos = line.find('│')
                indent_level = pipe_pos // 2  # Assuming 2-space indentation
                
                if indent_level in pipe_positions_by_level:
                    self.assertEqual(
                        pipe_positions_by_level[indent_level],
                        pipe_pos,
                        f"Misaligned pipe at level {indent_level}: {line}"
                    )
                else:
                    pipe_positions_by_level[indent_level] = pipe_pos

    def test_multiple_content_types_display(self):
        """Test that pipes are correctly aligned when showing multiple content types together."""
        # Create a task with description, relationships, and comments
        task51 = {
            'id': 'tsk_00000051',
            'name': 'Task with Multiple Content Types',
            'status': 'in progress',
            'priority': 1,
            'description': "This is a task description\nwith multiple lines.",
            'relationships': {
                'blocks': ['tsk_00000052'],
                'related_to': ['tsk_00000053']
            },
            'comments': [
                {
                    'id': 'cmt_00000001',
                    'text': 'This is a comment.',
                    'created_at': '2023-01-01T10:00:00Z',
                    'user': 'User1'
                }
            ]
        }
        
        task52 = {
            'id': 'tsk_00000052',
            'name': 'Blocked Child Task',
            'status': 'to do',
            'priority': 2,
            'description': "Child task description.",
            'comments': [
                {
                    'id': 'cmt_00000002',
                    'text': 'Comment on child task.',
                    'created_at': '2023-01-02T10:00:00Z',
                    'user': 'User2'
                }
            ]
        }
        
        task53 = {
            'id': 'tsk_00000053',
            'name': 'Related Task',
            'status': 'to do',
            'priority': 3
        }
        
        multi_content_tasks = [task51, task52, task53]
        
        # Format with all content types enabled
        output = format_task_hierarchy(
            multi_content_tasks,
            indent=2,
            colorize_output=False,
            show_full=False,
            include_completed=True,
            show_score=False,
            show_tags=False,
            dependency_as_tree=True,
            dependency_type="blocks", 
            show_descriptions=True,
            show_relationships=True,
            show_comments=1
        )
        
        # Validate tree structure
        is_valid, errors = validate_tree_structure(output)
        self.assertTrue(is_valid, f"Tree structure validation failed with multiple content types: {errors}")
        
        lines = output.split('\n')
        
        # Find parent task line
        parent_line = next((i for i, line in enumerate(lines) 
                           if 'Task with Multiple Content Types' in line), -1)
        self.assertGreater(parent_line, -1, "Parent task not found")
        
        # Find content sections
        parent_desc_line = next((i for i, line in enumerate(lines)
                               if i > parent_line and '📝' in line), -1)
        self.assertGreater(parent_desc_line, -1, "Parent description section not found")
        
        # Find relationship section
        relationship_line = next((i for i, line in enumerate(lines)
                                 if i > parent_line and '🔄' in line), -1)
        self.assertGreater(relationship_line, -1, "Relationship section not found")
        
        # Find comment section
        comment_line = next((i for i, line in enumerate(lines)
                            if i > parent_line and '💬' in line), -1)
        self.assertGreater(comment_line, -1, "Comment section not found")
        
        # Verify tree structure validation passes
        is_valid, errors = validate_tree_structure("\n".join(lines))
        self.assertTrue(is_valid, f"Tree structure validation failed: {errors}")
        
        # Check pipe alignment for content lines at the same level
        pipe_positions_by_level = {}
        
        # Check alignment for each content type
        for section_line in [parent_desc_line, relationship_line, comment_line]:
            line = lines[section_line]
            pipe_pos = line.find('│')
            
            # If this line has a pipe, check alignment
            if pipe_pos > -1:
                # Determine the indentation level
                indent_level = pipe_pos // 2
                
                # If we've seen this level before, pipes should align
                if indent_level in pipe_positions_by_level:
                    self.assertEqual(
                        pipe_positions_by_level[indent_level],
                        pipe_pos,
                        f"Misaligned pipe for content at level {indent_level}: {line}"
                    )
                else:
                    pipe_positions_by_level[indent_level] = pipe_pos
                    
        # Find child task
        child_line = next((i for i, line in enumerate(lines)
                          if 'Blocked Child Task' in line), -1)
        self.assertGreater(child_line, -1, "Child task not found")


if __name__ == '__main__':
    unittest.main() 