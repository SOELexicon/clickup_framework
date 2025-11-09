#!/usr/bin/env python3
"""
Create CLI Command Implementation Tasks in ClickUp

Creates a comprehensive hierarchical task structure for all missing CLI commands.
Posts tasks to the Testing list (901517404278) with 'to do' status.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clickup_framework import ClickUpClient


# Task hierarchy definition
# Format: (name, description, custom_type, children)
TASK_HIERARCHY = {
    "name": "CLI Command Implementation",
    "description": """# CLI Command Implementation

Implement all missing CLI commands for the ClickUp Framework.
The CLI should provide simplified, user-friendly commands that wrap the resource APIs.

## Goal
Complete command-line interface covering all ClickUp API functionality with:
- Simple, intuitive command structure
- Colored output and tree views
- Context management (current task/list/workspace)
- Proper error handling

## Progress
Track implementation progress through subtasks below.
""",
    "custom_type": "Project",
    "children": [
        {
            "name": "Task Management Commands",
            "description": "Commands for creating, updating, and managing tasks",
            "custom_type": "Feature",
            "children": [
                {"name": "task create - Create new tasks", "custom_type": "User Story"},
                {"name": "task update - Update existing tasks", "custom_type": "User Story"},
                {"name": "task delete - Delete tasks", "custom_type": "User Story"},
                {"name": "task assign - Assign tasks to users", "custom_type": "User Story"},
                {"name": "task unassign - Remove assignees from tasks", "custom_type": "User Story"},
                {"name": "task set-status - Change task status", "custom_type": "User Story"},
                {"name": "task set-priority - Change task priority", "custom_type": "User Story"},
            ]
        },
        {
            "name": "Comment Commands",
            "description": "Commands for managing task comments",
            "custom_type": "Feature",
            "children": [
                {"name": "comment add - Add comment to task", "custom_type": "User Story"},
                {"name": "comment list - List task comments", "custom_type": "User Story"},
                {"name": "comment update - Update comment", "custom_type": "User Story"},
                {"name": "comment delete - Delete comment", "custom_type": "User Story"},
            ]
        },
        {
            "name": "Checklist Commands",
            "description": "Commands for managing task checklists and checklist items",
            "custom_type": "Feature",
            "children": [
                {"name": "checklist create - Create checklist on task", "custom_type": "User Story"},
                {"name": "checklist delete - Delete checklist", "custom_type": "User Story"},
                {"name": "checklist-item add - Add item to checklist", "custom_type": "User Story"},
                {"name": "checklist-item update - Update checklist item", "custom_type": "User Story"},
                {"name": "checklist-item delete - Delete checklist item", "custom_type": "User Story"},
            ]
        },
        {
            "name": "Relationship Commands",
            "description": "Commands for managing task relationships (dependencies and links)",
            "custom_type": "Feature",
            "children": [
                {
                    "name": "Dependency Commands",
                    "description": "Manage task dependencies (blocking/waiting relationships)",
                    "custom_type": "Requirement",
                    "children": [
                        {"name": "task add-dependency - Add task dependency", "custom_type": "User Story"},
                        {"name": "task remove-dependency - Remove task dependency", "custom_type": "User Story"},
                    ]
                },
                {
                    "name": "Link Commands",
                    "description": "Manage simple task links",
                    "custom_type": "Requirement",
                    "children": [
                        {"name": "task add-link - Link two tasks", "custom_type": "User Story"},
                        {"name": "task remove-link - Unlink tasks", "custom_type": "User Story"},
                    ]
                }
            ]
        },
        {
            "name": "Custom Field Commands",
            "description": "Commands for managing custom fields on tasks",
            "custom_type": "Feature",
            "children": [
                {"name": "custom-field set - Set custom field value", "custom_type": "User Story"},
                {"name": "custom-field remove - Remove custom field value", "custom_type": "User Story"},
                {"name": "custom-field list - List available custom fields", "custom_type": "User Story"},
            ]
        },
        {
            "name": "List Commands",
            "description": "Commands for managing lists",
            "custom_type": "Feature",
            "children": [
                {"name": "list create - Create new list", "custom_type": "User Story"},
                {"name": "list update - Update list properties", "custom_type": "User Story"},
                {"name": "list delete - Delete list", "custom_type": "User Story"},
                {"name": "list show - Show list details", "custom_type": "User Story"},
            ]
        },
        {
            "name": "Workspace/Space/Folder Commands",
            "description": "Commands for managing workspace hierarchy",
            "custom_type": "Feature",
            "children": [
                {
                    "name": "Workspace Commands",
                    "description": "Commands for workspace operations",
                    "custom_type": "Requirement",
                    "children": [
                        {"name": "workspace list - List workspaces", "custom_type": "User Story"},
                        {"name": "workspace show - Show workspace details", "custom_type": "User Story"},
                    ]
                },
                {
                    "name": "Space Commands",
                    "description": "Commands for space operations",
                    "custom_type": "Requirement",
                    "children": [
                        {"name": "space list - List spaces in workspace", "custom_type": "User Story"},
                        {"name": "space create - Create new space", "custom_type": "User Story"},
                        {"name": "space show - Show space details", "custom_type": "User Story"},
                    ]
                },
                {
                    "name": "Folder Commands",
                    "description": "Commands for folder operations",
                    "custom_type": "Requirement",
                    "children": [
                        {"name": "folder list - List folders in space", "custom_type": "User Story"},
                        {"name": "folder create - Create new folder", "custom_type": "User Story"},
                        {"name": "folder show - Show folder details", "custom_type": "User Story"},
                    ]
                }
            ]
        },
        {
            "name": "Docs Commands",
            "description": "Commands for managing ClickUp Docs and Pages",
            "custom_type": "Feature",
            "children": [
                {"name": "doc list - List docs in workspace", "custom_type": "User Story"},
                {"name": "doc create - Create new doc", "custom_type": "User Story"},
                {"name": "doc show - Show doc details", "custom_type": "User Story"},
                {
                    "name": "Page Commands",
                    "description": "Commands for managing pages within docs",
                    "custom_type": "Requirement",
                    "children": [
                        {"name": "page list - List pages in doc", "custom_type": "User Story"},
                        {"name": "page create - Create new page", "custom_type": "User Story"},
                        {"name": "page update - Update page content", "custom_type": "User Story"},
                    ]
                }
            ]
        },
        {
            "name": "Time Tracking Commands",
            "description": "Commands for time tracking on tasks",
            "custom_type": "Feature",
            "children": [
                {"name": "time start - Start time tracking", "custom_type": "User Story"},
                {"name": "time stop - Stop time tracking", "custom_type": "User Story"},
                {"name": "time list - List time entries", "custom_type": "User Story"},
            ]
        },
        {
            "name": "View Commands",
            "description": "Commands for managing views",
            "custom_type": "Feature",
            "children": [
                {"name": "view list - List views", "custom_type": "User Story"},
                {"name": "view create - Create new view", "custom_type": "User Story"},
            ]
        },
        {
            "name": "Attachment Commands",
            "description": "Commands for managing file attachments",
            "custom_type": "Feature",
            "children": [
                {"name": "attachment upload - Upload file to task", "custom_type": "User Story"},
                {"name": "attachment list - List task attachments", "custom_type": "User Story"},
            ]
        }
    ]
}


def create_task_recursive(client, list_id, task_def, parent_id=None, level=0):
    """
    Recursively create tasks from hierarchy definition.

    Args:
        client: ClickUpClient instance
        list_id: List ID to create tasks in
        task_def: Task definition dict
        parent_id: Parent task ID (None for root)
        level: Current nesting level (for logging)

    Returns:
        Created task dict
    """
    indent = "  " * level

    # Build task data
    task_data = {
        'name': task_def['name'],
        'status': 'to do',  # Start all tasks as 'to do'
    }

    # Add description if provided
    if 'description' in task_def:
        task_data['markdown_description'] = task_def['description']

    # Add custom_type if provided
    if 'custom_type' in task_def:
        task_data['custom_type'] = task_def['custom_type']

    # Add parent if provided
    if parent_id:
        task_data['parent'] = parent_id

    # Create the task
    print(f"{indent}Creating: {task_def['name']}")
    task = client.create_task(list_id, **task_data)
    print(f"{indent}  ✓ Created: {task['id']} - {task.get('url', 'N/A')}")

    # Create children if any
    if 'children' in task_def:
        for child_def in task_def['children']:
            create_task_recursive(client, list_id, child_def, task['id'], level + 1)

    return task


def main():
    """Main entry point."""
    LIST_ID = "901517404278"  # Testing list

    print("=" * 80)
    print("Creating CLI Command Implementation Tasks")
    print("=" * 80)
    print(f"List ID: {LIST_ID}")
    print()

    # Initialize client
    try:
        client = ClickUpClient()
    except Exception as e:
        print(f"✗ Error initializing ClickUp client: {e}", file=sys.stderr)
        print("Make sure CLICKUP_API_TOKEN environment variable is set.", file=sys.stderr)
        return 1

    # Create task hierarchy
    try:
        root_task = create_task_recursive(client, LIST_ID, TASK_HIERARCHY)

        print()
        print("=" * 80)
        print("SUCCESS")
        print("=" * 80)
        print(f"Root task created: {root_task['id']}")
        print(f"URL: {root_task.get('url', 'N/A')}")
        print()
        print("All CLI command tasks have been created in ClickUp!")
        print("=" * 80)

        return 0

    except Exception as e:
        print(f"\n✗ Error creating tasks: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
