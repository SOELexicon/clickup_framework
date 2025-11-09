"""
Manual test for multiline content in task hierarchy display.

This module tests the rendering of multiline content (descriptions, comments) in hierarchical task displays.
"""
import sys
import os
import json
from datetime import datetime

# Correctly add the path to import the module
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from refactor.cli.commands.utils import format_task_hierarchy

def main():
    """Run the multiline content display test."""
    
    # Create sample tasks with multiline content
    tasks = [
        {
            'id': 'tsk_00000001',
            'name': 'Parent Task with Multiline Description',
            'status': 'in progress',
            'priority': 1,
            'description': "# Multiline Description\n\nThis description has multiple paragraphs.\n\n- Bullet point 1\n- Bullet point 2\n\n## Section\nMore text in a section.",
            'comments': [
                {
                    'text': "This is a\nmultiline comment\nwith several lines\nof text.",
                    'author': 'User 1',
                    'date': datetime.now().isoformat()
                }
            ],
            'relationships': {
                'blocks': ['tsk_00000002']
            }
        },
        {
            'id': 'tsk_00000002',
            'name': 'Child Task',
            'status': 'to do',
            'priority': 2,
            'parent_id': 'tsk_00000001',
            'description': "Single line description",
            'comments': [
                {
                    'text': "Single line comment",
                    'author': 'User 2',
                    'date': datetime.now().isoformat()
                }
            ]
        }
    ]
    
    # Test normal tree view
    print("\n===== TESTING TREE VIEW WITH DESCRIPTIONS =====")
    result = format_task_hierarchy(
        tasks,
        indent=2,
        colorize_output=False,
        show_descriptions=True,
        description_length=100,
        show_comments=0,
        validate_pipes=True
    )
    print(result)
    
    # Test tree view with comments
    print("\n===== TESTING TREE VIEW WITH COMMENTS =====")
    result = format_task_hierarchy(
        tasks,
        indent=2,
        colorize_output=False,
        show_descriptions=False,
        show_comments=1,
        validate_pipes=True
    )
    print(result)
    
    # Test dependency tree view
    print("\n===== TESTING DEPENDENCY TREE VIEW WITH DESCRIPTIONS AND COMMENTS =====")
    result = format_task_hierarchy(
        tasks,
        indent=2,
        colorize_output=False,
        show_descriptions=True,
        description_length=100,
        show_comments=1,
        dependency_as_tree=True,
        dependency_type="blocks",
        validate_pipes=True
    )
    print(result)
    
    print("\nTree structure validation should maintain proper pipe alignment for all multiline content.")
    print("If any vertical pipes are misaligned, the test has failed.")

if __name__ == "__main__":
    main() 