"""
MCP Tool Definitions for ClickUp Framework

This module defines all MCP tool schemas that map to CLI commands.
Each tool corresponds to one or more CLI commands from the commands/ directory.
"""

import mcp.types as types


def get_all_tools() -> list[types.Tool]:
    """
    Get all available ClickUp MCP tools.

    Returns:
        List of Tool definitions with schemas
    """
    return [
        # Task Operations
        types.Tool(
            name="clickup_get_task",
            description="Get detailed information about a ClickUp task with token-efficient formatting",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Task ID to retrieve"
                    },
                    "list_id": {
                        "type": "string",
                        "description": "List ID (optional, helps with caching)"
                    },
                    "detail_level": {
                        "type": "string",
                        "enum": ["minimal", "summary", "detailed", "full"],
                        "description": "Level of detail in output (default: detailed)",
                        "default": "detailed"
                    }
                },
                "required": ["task_id"]
            }
        ),

        types.Tool(
            name="clickup_create_task",
            description="Create a new ClickUp task with duplicate detection and safeguards",
            inputSchema={
                "type": "object",
                "properties": {
                    "list_id": {
                        "type": "string",
                        "description": "List ID to create task in (use 'current' for current list)"
                    },
                    "name": {
                        "type": "string",
                        "description": "Task name/title"
                    },
                    "description": {
                        "type": "string",
                        "description": "Task description (markdown supported)"
                    },
                    "status": {
                        "type": "string",
                        "description": "Initial status (e.g., 'to do', 'in progress')"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["1", "2", "3", "4", "urgent", "high", "normal", "low"],
                        "description": "Task priority (1=urgent, 4=low)"
                    },
                    "assignees": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Array of user IDs to assign"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Array of tag names"
                    },
                    "parent": {
                        "type": "string",
                        "description": "Parent task ID (creates as subtask)"
                    }
                },
                "required": ["list_id", "name"]
            }
        ),

        types.Tool(
            name="clickup_update_task",
            description="Update an existing ClickUp task (requires view-before-modify)",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Task ID to update"
                    },
                    "name": {
                        "type": "string",
                        "description": "New task name"
                    },
                    "description": {
                        "type": "string",
                        "description": "New task description"
                    },
                    "status": {
                        "type": "string",
                        "description": "New status"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["1", "2", "3", "4", "urgent", "high", "normal", "low"],
                        "description": "New priority"
                    }
                },
                "required": ["task_id"]
            }
        ),

        types.Tool(
            name="clickup_delete_task",
            description="Delete a ClickUp task (requires view-before-modify)",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Task ID to delete"
                    },
                    "force": {
                        "type": "boolean",
                        "description": "Skip confirmation prompt",
                        "default": False
                    }
                },
                "required": ["task_id"]
            }
        ),

        types.Tool(
            name="clickup_set_task_status",
            description="Update task status with subtask validation",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Array of task IDs to update"
                    },
                    "status": {
                        "type": "string",
                        "description": "New status name"
                    }
                },
                "required": ["task_ids", "status"]
            }
        ),

        types.Tool(
            name="clickup_set_task_priority",
            description="Update task priority",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Task ID to update"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["1", "2", "3", "4", "urgent", "high", "normal", "low"],
                        "description": "New priority (1=urgent, 4=low)"
                    }
                },
                "required": ["task_id", "priority"]
            }
        ),

        types.Tool(
            name="clickup_assign_task",
            description="Assign users to a task",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Task ID"
                    },
                    "user_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Array of user IDs to assign"
                    }
                },
                "required": ["task_id", "user_ids"]
            }
        ),

        types.Tool(
            name="clickup_unassign_task",
            description="Remove assignees from a task",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Task ID"
                    },
                    "user_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Array of user IDs to unassign"
                    }
                },
                "required": ["task_id", "user_ids"]
            }
        ),

        types.Tool(
            name="clickup_set_task_tags",
            description="Manage task tags (add, remove, or set)",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Task ID"
                    },
                    "operation": {
                        "type": "string",
                        "enum": ["add", "remove", "set"],
                        "description": "Tag operation: add new tags, remove existing, or set (replace all)"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Array of tag names"
                    }
                },
                "required": ["task_id", "operation", "tags"]
            }
        ),

        # View Commands
        types.Tool(
            name="clickup_get_hierarchy",
            description="Get hierarchical parent-child tree view of tasks in a list (token-efficient 90-98% reduction)",
            inputSchema={
                "type": "object",
                "properties": {
                    "list_id": {
                        "type": "string",
                        "description": "List ID to view (use 'current' for current list)"
                    },
                    "detail_level": {
                        "type": "string",
                        "enum": ["minimal", "summary", "detailed", "full"],
                        "description": "Level of detail (default: summary)",
                        "default": "summary"
                    },
                    "include_completed": {
                        "type": "boolean",
                        "description": "Include completed tasks",
                        "default": False
                    }
                },
                "required": ["list_id"]
            }
        ),

        types.Tool(
            name="clickup_get_flat_view",
            description="Get flat list view of all tasks (no hierarchy)",
            inputSchema={
                "type": "object",
                "properties": {
                    "list_id": {
                        "type": "string",
                        "description": "List ID"
                    },
                    "detail_level": {
                        "type": "string",
                        "enum": ["minimal", "summary", "detailed", "full"],
                        "description": "Level of detail",
                        "default": "summary"
                    }
                },
                "required": ["list_id"]
            }
        ),

        types.Tool(
            name="clickup_filter_tasks",
            description="Get filtered view of tasks by status, priority, assignee, or tags",
            inputSchema={
                "type": "object",
                "properties": {
                    "list_id": {
                        "type": "string",
                        "description": "List ID"
                    },
                    "status": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by status names"
                    },
                    "priority": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by priority (urgent, high, normal, low)"
                    },
                    "assignee": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Filter by assignee user IDs"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by tag names"
                    }
                },
                "required": ["list_id"]
            }
        ),

        types.Tool(
            name="clickup_get_assigned_tasks",
            description="Get tasks assigned to a user, sorted by difficulty score",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "integer",
                        "description": "User ID (uses current assignee if not specified)"
                    },
                    "team_id": {
                        "type": "integer",
                        "description": "Team/workspace ID"
                    }
                },
                "required": []
            }
        ),

        types.Tool(
            name="clickup_get_stats",
            description="Get aggregate statistics for tasks in a list",
            inputSchema={
                "type": "object",
                "properties": {
                    "list_id": {
                        "type": "string",
                        "description": "List ID"
                    }
                },
                "required": ["list_id"]
            }
        ),

        # Comment Management
        types.Tool(
            name="clickup_add_comment",
            description="Add a comment to a task",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Task ID"
                    },
                    "comment_text": {
                        "type": "string",
                        "description": "Comment text (markdown supported)"
                    }
                },
                "required": ["task_id", "comment_text"]
            }
        ),

        types.Tool(
            name="clickup_list_comments",
            description="List all comments on a task",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Task ID"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of comments to return",
                        "default": 25
                    }
                },
                "required": ["task_id"]
            }
        ),

        types.Tool(
            name="clickup_update_comment",
            description="Update an existing comment",
            inputSchema={
                "type": "object",
                "properties": {
                    "comment_id": {
                        "type": "string",
                        "description": "Comment ID"
                    },
                    "comment_text": {
                        "type": "string",
                        "description": "New comment text"
                    }
                },
                "required": ["comment_id", "comment_text"]
            }
        ),

        types.Tool(
            name="clickup_delete_comment",
            description="Delete a comment",
            inputSchema={
                "type": "object",
                "properties": {
                    "comment_id": {
                        "type": "string",
                        "description": "Comment ID"
                    },
                    "force": {
                        "type": "boolean",
                        "description": "Skip confirmation",
                        "default": False
                    }
                },
                "required": ["comment_id"]
            }
        ),

        # Context Management
        types.Tool(
            name="clickup_set_current",
            description="Set current context (workspace, list, task, or assignee) for use with 'current' keyword",
            inputSchema={
                "type": "object",
                "properties": {
                    "resource_type": {
                        "type": "string",
                        "enum": ["workspace", "space", "folder", "list", "task", "assignee"],
                        "description": "Type of resource to set"
                    },
                    "resource_id": {
                        "type": "string",
                        "description": "ID of the resource (user ID for assignee)"
                    }
                },
                "required": ["resource_type", "resource_id"]
            }
        ),

        types.Tool(
            name="clickup_get_current",
            description="Get current context settings",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),

        types.Tool(
            name="clickup_clear_current",
            description="Clear current context (all or specific type)",
            inputSchema={
                "type": "object",
                "properties": {
                    "resource_type": {
                        "type": "string",
                        "enum": ["workspace", "space", "folder", "list", "task", "assignee", "all"],
                        "description": "Type of resource to clear (default: all)"
                    }
                },
                "required": []
            }
        ),

        # Task Dependencies
        types.Tool(
            name="clickup_add_dependency",
            description="Add a task dependency (blocking or waiting-on relationship)",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Task ID"
                    },
                    "depends_on_task_id": {
                        "type": "string",
                        "description": "Task ID that this task depends on"
                    },
                    "dependency_type": {
                        "type": "string",
                        "enum": ["waiting_on", "blocking"],
                        "description": "Type of dependency (default: waiting_on)",
                        "default": "waiting_on"
                    }
                },
                "required": ["task_id", "depends_on_task_id"]
            }
        ),

        types.Tool(
            name="clickup_remove_dependency",
            description="Remove a task dependency",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Task ID"
                    },
                    "depends_on_task_id": {
                        "type": "string",
                        "description": "Task ID to remove dependency from"
                    },
                    "dependency_type": {
                        "type": "string",
                        "enum": ["waiting_on", "blocking"],
                        "description": "Type of dependency",
                        "default": "waiting_on"
                    }
                },
                "required": ["task_id", "depends_on_task_id"]
            }
        ),

        types.Tool(
            name="clickup_add_task_link",
            description="Create a link between two tasks",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "First task ID"
                    },
                    "linked_task_id": {
                        "type": "string",
                        "description": "Second task ID to link"
                    }
                },
                "required": ["task_id", "linked_task_id"]
            }
        ),

        types.Tool(
            name="clickup_remove_task_link",
            description="Remove a link between two tasks",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "First task ID"
                    },
                    "linked_task_id": {
                        "type": "string",
                        "description": "Second task ID"
                    }
                },
                "required": ["task_id", "linked_task_id"]
            }
        ),

        # Bulk Operations
        types.Tool(
            name="clickup_bulk_create_tasks",
            description="Create multiple tasks at once (bulk operation)",
            inputSchema={
                "type": "object",
                "properties": {
                    "list_id": {
                        "type": "string",
                        "description": "List ID to create tasks in"
                    },
                    "tasks": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "description": {"type": "string"},
                                "status": {"type": "string"},
                                "priority": {"type": "string"},
                                "tags": {"type": "array", "items": {"type": "string"}},
                                "assignees": {"type": "array", "items": {"type": "integer"}},
                                "parent": {"type": "string"}
                            },
                            "required": ["name"]
                        },
                        "description": "Array of task objects to create"
                    }
                },
                "required": ["list_id", "tasks"]
            }
        ),

        types.Tool(
            name="clickup_bulk_update_tasks",
            description="Update multiple tasks with the same changes (bulk operation)",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Array of task IDs to update"
                    },
                    "updates": {
                        "type": "object",
                        "properties": {
                            "status": {"type": "string"},
                            "priority": {"type": "string"},
                            "tags": {"type": "array", "items": {"type": "string"}},
                            "add_tags": {"type": "array", "items": {"type": "string"}},
                            "remove_tags": {"type": "array", "items": {"type": "string"}}
                        },
                        "description": "Updates to apply to all tasks"
                    }
                },
                "required": ["task_ids", "updates"]
            }
        ),

        # List Operations
        types.Tool(
            name="clickup_get_list_tasks",
            description="Get all tasks from a list (raw task data, not formatted view)",
            inputSchema={
                "type": "object",
                "properties": {
                    "list_id": {
                        "type": "string",
                        "description": "List ID"
                    },
                    "include_closed": {
                        "type": "boolean",
                        "description": "Include completed/closed tasks",
                        "default": False
                    },
                    "subtasks": {
                        "type": "boolean",
                        "description": "Include subtasks",
                        "default": True
                    },
                    "detail_level": {
                        "type": "string",
                        "enum": ["minimal", "summary", "detailed", "full"],
                        "description": "Level of detail for each task",
                        "default": "summary"
                    }
                },
                "required": ["list_id"]
            }
        ),

        # Search
        types.Tool(
            name="clickup_search_tasks",
            description="Search for tasks across workspace using keywords",
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace_id": {
                        "type": "string",
                        "description": "Workspace/team ID (use 'current' for current workspace)"
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query string"
                    },
                    "detail_level": {
                        "type": "string",
                        "enum": ["minimal", "summary", "detailed", "full"],
                        "description": "Level of detail",
                        "default": "summary"
                    }
                },
                "required": ["workspace_id", "query"]
            }
        ),

        # Workspace Operations
        types.Tool(
            name="clickup_get_workspace_hierarchy",
            description="Get complete workspace hierarchy (spaces, folders, lists)",
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace_id": {
                        "type": "string",
                        "description": "Workspace/team ID"
                    }
                },
                "required": ["workspace_id"]
            }
        ),

        # Checklists
        types.Tool(
            name="clickup_add_checklist",
            description="Add a checklist to a task",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Task ID"
                    },
                    "checklist_name": {
                        "type": "string",
                        "description": "Checklist name/title"
                    },
                    "items": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Array of checklist item names"
                    }
                },
                "required": ["task_id", "checklist_name"]
            }
        ),

        types.Tool(
            name="clickup_update_checklist_item",
            description="Update a checklist item (mark as complete/incomplete)",
            inputSchema={
                "type": "object",
                "properties": {
                    "checklist_id": {
                        "type": "string",
                        "description": "Checklist ID"
                    },
                    "checklist_item_id": {
                        "type": "string",
                        "description": "Checklist item ID"
                    },
                    "resolved": {
                        "type": "boolean",
                        "description": "Mark as complete (true) or incomplete (false)"
                    }
                },
                "required": ["checklist_id", "checklist_item_id", "resolved"]
            }
        ),

        # Custom Fields
        types.Tool(
            name="clickup_set_custom_field",
            description="Set a custom field value on a task",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Task ID"
                    },
                    "field_id": {
                        "type": "string",
                        "description": "Custom field ID"
                    },
                    "value": {
                        "description": "Field value (type depends on field type)"
                    }
                },
                "required": ["task_id", "field_id", "value"]
            }
        ),
    ]
