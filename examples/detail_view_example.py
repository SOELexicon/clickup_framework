#!/usr/bin/env python3
"""
Example demonstrating the task detail view with relationship tree.

This example shows how to display a single task with its full context:
- Parent chain (ancestry)
- Current task details
- Sibling tasks
- Child tasks (subtasks) in tree view
- Dependencies
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clickup_framework.components import (
    DisplayManager,
    FormatOptions,
    TaskDetailFormatter
)

# Sample hierarchical task data with relationships
SAMPLE_TASKS = [
    {
        'id': 'epic_1',
        'name': 'Q1 Product Launch',
        'status': {'status': 'in progress'},
        'priority': {'priority': '1'},
        'parent': None,
        'custom_type': 'milestone',
        'description': 'Complete product launch for Q1 including all features, testing, and documentation',
        'date_created': '2024-01-01T09:00:00Z',
        'due_date': '2024-03-31T23:59:59Z',
        'tags': [{'name': 'Q1'}, {'name': 'product'}]
    },
    {
        'id': 'feature_1',
        'name': 'Authentication System',
        'status': {'status': 'in progress'},
        'priority': {'priority': '1'},
        'parent': 'epic_1',
        'custom_type': 'feature',
        'description': 'Implement comprehensive authentication system with OAuth, JWT, and 2FA support',
        'date_created': '2024-01-05T10:00:00Z',
        'due_date': '2024-02-15T23:59:59Z',
        'tags': [{'name': 'backend'}, {'name': 'security'}],
        'assignees': [{'username': 'alice'}]
    },
    {
        'id': 'feature_2',
        'name': 'User Dashboard',
        'status': {'status': 'to do'},
        'priority': {'priority': '2'},
        'parent': 'epic_1',
        'custom_type': 'feature',
        'description': 'Create user dashboard with analytics and activity feeds',
        'tags': [{'name': 'frontend'}, {'name': 'ui'}],
        'dependencies': [{'depends_on': 'feature_1'}]
    },
    {
        'id': 'task_1',
        'name': 'Implement OAuth Provider Integration',
        'status': {'status': 'in progress'},
        'priority': {'priority': '1'},
        'parent': 'feature_1',
        'custom_type': 'task',
        'description': 'Integrate OAuth providers: Google, GitHub, Microsoft',
        'tags': [{'name': 'oauth'}, {'name': 'integration'}],
        'assignees': [{'username': 'alice'}],
        'comments': [
            {
                'user': {'username': 'bob'},
                'date': '2024-01-10',
                'comment_text': 'Google OAuth is working, testing GitHub next'
            }
        ]
    },
    {
        'id': 'task_2',
        'name': 'Implement JWT Token Management',
        'status': {'status': 'complete'},
        'priority': {'priority': '1'},
        'parent': 'feature_1',
        'custom_type': 'task',
        'description': 'Create JWT token generation, validation, and refresh logic',
        'tags': [{'name': 'jwt'}, {'name': 'tokens'}],
        'date_closed': '2024-01-12T15:30:00Z'
    },
    {
        'id': 'task_3',
        'name': 'Add Two-Factor Authentication',
        'status': {'status': 'to do'},
        'priority': {'priority': '2'},
        'parent': 'feature_1',
        'custom_type': 'task',
        'description': 'Implement 2FA using TOTP (Time-based One-Time Password)',
        'tags': [{'name': '2fa'}, {'name': 'security'}],
        'dependencies': [{'depends_on': 'task_1'}]
    },
    {
        'id': 'subtask_1',
        'name': 'Setup Google OAuth App',
        'status': {'status': 'complete'},
        'priority': {'priority': '1'},
        'parent': 'task_1',
        'custom_type': 'task',
        'date_closed': '2024-01-08T11:00:00Z'
    },
    {
        'id': 'subtask_2',
        'name': 'Setup GitHub OAuth App',
        'status': {'status': 'in progress'},
        'priority': {'priority': '1'},
        'parent': 'task_1',
        'custom_type': 'task'
    },
    {
        'id': 'subtask_3',
        'name': 'Setup Microsoft OAuth App',
        'status': {'status': 'to do'},
        'priority': {'priority': '2'},
        'parent': 'task_1',
        'custom_type': 'task'
    },
    {
        'id': 'feature_3',
        'name': 'API Documentation',
        'status': {'status': 'to do'},
        'priority': {'priority': '3'},
        'parent': 'epic_1',
        'custom_type': 'documentation',
        'description': 'Complete API documentation with examples and tutorials',
        'tags': [{'name': 'docs'}]
    }
]


def main():
    """Demonstrate task detail view with relationships."""
    print("=" * 80)
    print("Task Detail View Examples")
    print("=" * 80)
    print()

    display = DisplayManager()

    # Example 1: Show a task deep in the hierarchy
    print("Example 1: OAuth Integration Task (deep in hierarchy)")
    print("-" * 80)

    task_1 = next(t for t in SAMPLE_TASKS if t['id'] == 'task_1')
    options = FormatOptions.detailed()

    output = display.detail_view(task_1, SAMPLE_TASKS, options)
    print(output)

    print("\n" + "=" * 80 + "\n")

    # Example 2: Show a mid-level feature task
    print("Example 2: Authentication System Feature")
    print("-" * 80)

    feature_1 = next(t for t in SAMPLE_TASKS if t['id'] == 'feature_1')

    output = display.detail_view(feature_1, SAMPLE_TASKS, options)
    print(output)

    print("\n" + "=" * 80 + "\n")

    # Example 3: Show top-level epic
    print("Example 3: Q1 Product Launch Epic (top level)")
    print("-" * 80)

    epic_1 = next(t for t in SAMPLE_TASKS if t['id'] == 'epic_1')

    output = display.detail_view(epic_1, SAMPLE_TASKS, options)
    print(output)

    print("\n" + "=" * 80 + "\n")

    # Example 4: Using TaskDetailFormatter directly
    print("Example 4: Using TaskDetailFormatter Directly")
    print("-" * 80)

    formatter = TaskDetailFormatter()
    subtask_2 = next(t for t in SAMPLE_TASKS if t['id'] == 'subtask_2')

    output = formatter.format_with_context(subtask_2, SAMPLE_TASKS, options)
    print(output)

    print("\n" + "=" * 80)
    print("Examples Complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
