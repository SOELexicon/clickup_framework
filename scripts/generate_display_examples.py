#!/usr/bin/env python3
"""
Generate display examples for screenshot creation.

This script creates example outputs from the display components
and saves them as ANSI-colored text files.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clickup_framework.components import (
    DisplayManager,
    FormatOptions,
    TaskHierarchyFormatter,
    ContainerHierarchyFormatter,
    RichTaskFormatter
)

# Sample task data
SAMPLE_HIERARCHICAL_TASKS = [
    {
        'id': 'parent_1',
        'name': 'Feature Development',
        'status': {'status': 'in progress'},
        'priority': {'priority': '1'},
        'parent': None,
        'custom_type': 'project',
        'tags': [{'name': 'backend'}, {'name': 'api'}],
        'description': 'Develop new API endpoints for user management',
        'date_created': '2024-01-01T10:00:00Z',
        'due_date': '2024-01-31T23:59:59Z',
        'assignees': [{'username': 'alice'}]
    },
    {
        'id': 'child_1',
        'name': 'Add User Authentication Endpoint',
        'status': {'status': 'in progress'},
        'priority': {'priority': '1'},
        'parent': 'parent_1',
        'custom_type': 'feature',
        'tags': [{'name': 'authentication'}, {'name': 'security'}],
        'description': 'Implement JWT-based authentication endpoint with refresh tokens',
        'date_created': '2024-01-05T10:00:00Z',
        'due_date': '2024-01-20T23:59:59Z',
        'assignees': [{'username': 'alice'}, {'username': 'bob'}],
        'dependencies': [{'depends_on': 'docs_1'}]
    },
    {
        'id': 'child_2',
        'name': 'Add User Profile Endpoint',
        'status': {'status': 'to do'},
        'priority': {'priority': '2'},
        'parent': 'parent_1',
        'custom_type': 'feature',
        'tags': [{'name': 'profile'}, {'name': 'api'}],
        'description': 'Create endpoint for user profile management',
        'assignees': [{'username': 'charlie'}]
    },
    {
        'id': 'grandchild_1',
        'name': 'Write API Tests',
        'status': {'status': 'to do'},
        'priority': {'priority': '2'},
        'parent': 'child_1',
        'custom_type': 'test',
        'description': 'Comprehensive test suite for authentication endpoints',
        'assignees': [{'username': 'bob'}]
    },
    {
        'id': 'bug_1',
        'name': 'Fix Login Error Handling',
        'status': {'status': 'blocked'},
        'priority': {'priority': '1'},
        'parent': None,
        'custom_type': 'bug',
        'tags': [{'name': 'critical'}, {'name': 'authentication'}],
        'description': 'Login endpoint does not properly handle invalid credentials'
    },
    {
        'id': 'docs_1',
        'name': 'Update API Documentation',
        'status': {'status': 'complete'},
        'priority': {'priority': '3'},
        'parent': None,
        'custom_type': 'documentation',
        'date_closed': '2024-01-03T15:30:00Z'
    }
]

SAMPLE_CONTAINER_TASKS = [
    {
        'id': 'task_1',
        'name': 'Implement Database Schema',
        'status': {'status': 'in progress'},
        'priority': {'priority': '1'},
        'space': {'id': 'space_1', 'name': 'Engineering'},
        'folder': {'id': 'folder_1', 'name': 'Backend'},
        'list': {'id': 'list_a', 'name': 'Database'},
        'custom_type': 'feature',
        'tags': [{'name': 'database'}, {'name': 'postgresql'}]
    },
    {
        'id': 'task_2',
        'name': 'Add Database Migrations',
        'status': {'status': 'to do'},
        'priority': {'priority': '2'},
        'space': {'id': 'space_1', 'name': 'Engineering'},
        'folder': {'id': 'folder_1', 'name': 'Backend'},
        'list': {'id': 'list_a', 'name': 'Database'},
        'custom_type': 'feature'
    },
    {
        'id': 'task_3',
        'name': 'Design UI Components',
        'status': {'status': 'in progress'},
        'priority': {'priority': '2'},
        'space': {'id': 'space_1', 'name': 'Engineering'},
        'folder': {'id': 'folder_2', 'name': 'Frontend'},
        'list': {'id': 'list_b', 'name': 'UI Components'},
        'custom_type': 'feature',
        'tags': [{'name': 'ui'}, {'name': 'react'}]
    },
    {
        'id': 'task_4',
        'name': 'Create Mockups',
        'status': {'status': 'complete'},
        'priority': {'priority': '3'},
        'space': {'id': 'space_2', 'name': 'Design'},
        'folder': {'id': 'folder_3', 'name': 'Product Design'},
        'list': {'id': 'list_c', 'name': 'Mockups'},
        'custom_type': 'task'
    }
]


def save_output(filename, content):
    """Save output to a file."""
    output_dir = 'outputs'
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"✓ Generated {filename}")


def main():
    """Generate all display examples."""
    print("Generating display component examples...\n")

    display = DisplayManager()

    # 1. Minimal View
    options_minimal = FormatOptions.minimal()
    output = display.hierarchy_view(
        SAMPLE_HIERARCHICAL_TASKS,
        options_minimal,
        header="Minimal View - Task List"
    )
    save_output('01_minimal_view.txt', output)

    # 2. Summary View
    options_summary = FormatOptions.summary()
    output = display.hierarchy_view(
        SAMPLE_HIERARCHICAL_TASKS,
        options_summary,
        header="Summary View - Task Hierarchy"
    )
    save_output('02_summary_view.txt', output)

    # 3. Detailed View with Descriptions
    options_detailed = FormatOptions.detailed()
    output = display.hierarchy_view(
        SAMPLE_HIERARCHICAL_TASKS,
        options_detailed,
        header="Detailed View - Task Hierarchy with Descriptions"
    )
    save_output('03_detailed_view.txt', output)

    # 4. Container Hierarchy View
    output = display.container_view(
        SAMPLE_CONTAINER_TASKS,
        FormatOptions.summary()
    )
    save_output('04_container_hierarchy.txt', output)

    # 5. Filtered View (In Progress Only)
    output = display.filtered_view(
        SAMPLE_HIERARCHICAL_TASKS,
        status="in progress",
        view_mode='hierarchy'
    )
    save_output('05_filtered_in_progress.txt', "Filtered View - In Progress Tasks\n\n" + output)

    # 6. Full View with All Options
    options_full = FormatOptions(
        colorize_output=True,
        show_ids=True,
        show_tags=True,
        show_descriptions=True,
        show_dates=True,
        include_completed=True
    )
    output = display.hierarchy_view(
        SAMPLE_HIERARCHICAL_TASKS,
        options_full,
        header="Full View - All Information"
    )
    save_output('06_full_view.txt', output)

    # 7. Task Statistics
    stats = display.summary_stats(SAMPLE_HIERARCHICAL_TASKS)
    save_output('07_statistics.txt', "Task Statistics\n\n" + stats)

    # 8. Flat View
    output = display.flat_view(
        SAMPLE_HIERARCHICAL_TASKS[:3],
        FormatOptions.summary(),
        header="Flat View - Simple List"
    )
    save_output('08_flat_view.txt', output)

    # 9. Detail View - Child Task with Full Context
    child_task = next(t for t in SAMPLE_HIERARCHICAL_TASKS if t['id'] == 'child_1')
    output = display.detail_view(child_task, SAMPLE_HIERARCHICAL_TASKS, FormatOptions.detailed())
    save_output('09_detail_view_child.txt', output)

    # 10. Detail View - Grandchild Task (Deep Hierarchy)
    grandchild_task = next(t for t in SAMPLE_HIERARCHICAL_TASKS if t['id'] == 'grandchild_1')
    output = display.detail_view(grandchild_task, SAMPLE_HIERARCHICAL_TASKS, FormatOptions.detailed())
    save_output('10_detail_view_grandchild.txt', output)

    # 11. Detail View - Parent Task with Children
    parent_task = next(t for t in SAMPLE_HIERARCHICAL_TASKS if t['id'] == 'parent_1')
    output = display.detail_view(parent_task, SAMPLE_HIERARCHICAL_TASKS, FormatOptions.detailed())
    save_output('11_detail_view_parent.txt', output)

    print("\n✅ All examples generated in 'outputs/' directory")


if __name__ == "__main__":
    main()
