#!/usr/bin/env python3
"""
ClickUp Framework MCP Server

Model Context Protocol server that exposes ClickUp Framework functionality
to AI assistants like Claude Desktop.

This server wraps the existing CLI commands and provides them as MCP tools,
preserving all the token-efficient formatting and safeguards.

Usage:
    clickup-mcp
    python -m clickup_framework.mcp_server
"""

import sys
import os
import io
import asyncio
import logging
from contextlib import redirect_stdout, redirect_stderr
from typing import Any

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server

from clickup_framework.mcp_tools import get_all_tools
from clickup_framework import get_context_manager
from clickup_framework.client import ClickUpClient
from clickup_framework.resources.tasks import TasksAPI
from clickup_framework.resources.comments import CommentsAPI
from clickup_framework.components.display import DisplayManager
from clickup_framework.formatters.task import TaskFormatter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("clickup-mcp")

# Initialize server
server = Server("clickup-mcp")

# Initialize ClickUp resources (will auto-load API token from env/context)
context_manager = get_context_manager()


def resolve_resource_id(resource_id: str, resource_type: str) -> str:
    """
    Resolve resource ID, handling 'current' keyword.

    Args:
        resource_id: Resource ID or 'current'
        resource_type: Type of resource (list, task, etc.)

    Returns:
        Resolved resource ID

    Raises:
        ValueError: If 'current' is used but not set
    """
    if resource_id != "current":
        return resource_id

    # Handle 'current' keyword
    if resource_type == "list":
        list_id = context_manager.get_current_list()
        if not list_id:
            raise ValueError("No current list set. Use clickup_set_current to set one.")
        return list_id
    elif resource_type == "task":
        task_id = context_manager.get_current_task()
        if not task_id:
            raise ValueError("No current task set. Use clickup_set_current to set one.")
        return task_id
    elif resource_type == "workspace":
        workspace_id = context_manager.get_current_workspace()
        if not workspace_id:
            raise ValueError("No current workspace set. Use clickup_set_current to set one.")
        return workspace_id
    else:
        raise ValueError(f"'current' keyword not supported for resource type: {resource_type}")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available ClickUp tools.

    Returns all tools defined in mcp_tools.py
    """
    logger.info("Listing available tools")
    return get_all_tools()


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any]
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Execute a ClickUp tool.

    This handler routes tool calls to the appropriate CLI functionality,
    preserving all token-efficient formatting and safeguards.

    Args:
        name: Tool name (e.g., 'clickup_get_task')
        arguments: Tool arguments

    Returns:
        List of content items (typically text)
    """
    logger.info(f"Tool call: {name} with arguments: {arguments}")

    try:
        # Initialize client (will auto-load token)
        client = ClickUpClient()

        # Route to appropriate handler
        if name == "clickup_get_task":
            return await handle_get_task(client, arguments)

        elif name == "clickup_create_task":
            return await handle_create_task(client, arguments)

        elif name == "clickup_update_task":
            return await handle_update_task(client, arguments)

        elif name == "clickup_delete_task":
            return await handle_delete_task(client, arguments)

        elif name == "clickup_set_task_status":
            return await handle_set_task_status(client, arguments)

        elif name == "clickup_set_task_priority":
            return await handle_set_task_priority(client, arguments)

        elif name == "clickup_assign_task":
            return await handle_assign_task(client, arguments)

        elif name == "clickup_unassign_task":
            return await handle_unassign_task(client, arguments)

        elif name == "clickup_set_task_tags":
            return await handle_set_task_tags(client, arguments)

        elif name == "clickup_get_hierarchy":
            return await handle_get_hierarchy(client, arguments)

        elif name == "clickup_get_flat_view":
            return await handle_get_flat_view(client, arguments)

        elif name == "clickup_filter_tasks":
            return await handle_filter_tasks(client, arguments)

        elif name == "clickup_get_assigned_tasks":
            return await handle_get_assigned_tasks(client, arguments)

        elif name == "clickup_get_stats":
            return await handle_get_stats(client, arguments)

        elif name == "clickup_add_comment":
            return await handle_add_comment(client, arguments)

        elif name == "clickup_list_comments":
            return await handle_list_comments(client, arguments)

        elif name == "clickup_update_comment":
            return await handle_update_comment(client, arguments)

        elif name == "clickup_delete_comment":
            return await handle_delete_comment(client, arguments)

        elif name == "clickup_set_current":
            return await handle_set_current(arguments)

        elif name == "clickup_get_current":
            return await handle_get_current()

        elif name == "clickup_clear_current":
            return await handle_clear_current(arguments)

        elif name == "clickup_add_dependency":
            return await handle_add_dependency(client, arguments)

        elif name == "clickup_remove_dependency":
            return await handle_remove_dependency(client, arguments)

        elif name == "clickup_add_task_link":
            return await handle_add_task_link(client, arguments)

        elif name == "clickup_remove_task_link":
            return await handle_remove_task_link(client, arguments)

        elif name == "clickup_bulk_create_tasks":
            return await handle_bulk_create_tasks(client, arguments)

        elif name == "clickup_bulk_update_tasks":
            return await handle_bulk_update_tasks(client, arguments)

        elif name == "clickup_get_list_tasks":
            return await handle_get_list_tasks(client, arguments)

        elif name == "clickup_search_tasks":
            return await handle_search_tasks(client, arguments)

        elif name == "clickup_get_workspace_hierarchy":
            return await handle_get_workspace_hierarchy(client, arguments)

        elif name == "clickup_add_checklist":
            return await handle_add_checklist(client, arguments)

        elif name == "clickup_update_checklist_item":
            return await handle_update_checklist_item(client, arguments)

        elif name == "clickup_set_custom_field":
            return await handle_set_custom_field(client, arguments)

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}", exc_info=True)
        error_message = f"Error: {str(e)}"
        return [types.TextContent(type="text", text=error_message)]


# Tool Handlers

async def handle_get_task(client: ClickUpClient, arguments: dict) -> list[types.TextContent]:
    """Get task details with token-efficient formatting."""
    task_id = arguments["task_id"]
    detail_level = arguments.get("detail_level", "detailed")

    tasks_api = TasksAPI(client)
    task_data = tasks_api.get_task(
        task_id=task_id,
        format_output=True,
        detail_level=detail_level
    )

    return [types.TextContent(type="text", text=task_data)]


async def handle_create_task(client: ClickUpClient, arguments: dict) -> list[types.TextContent]:
    """Create a new task with duplicate detection."""
    list_id = resolve_resource_id(arguments["list_id"], "list")
    name = arguments["name"]

    tasks_api = TasksAPI(client)
    task = tasks_api.create_task(
        list_id=list_id,
        name=name,
        description=arguments.get("description"),
        status=arguments.get("status"),
        priority=arguments.get("priority"),
        assignees=arguments.get("assignees"),
        tags=arguments.get("tags"),
        parent=arguments.get("parent")
    )

    result = f"✓ Created task: {task['name']}\n"
    result += f"  ID: {task['id']}\n"
    result += f"  URL: {task['url']}"

    return [types.TextContent(type="text", text=result)]


async def handle_update_task(client: ClickUpClient, arguments: dict) -> list[types.TextContent]:
    """Update task with view-before-modify safeguard."""
    task_id = arguments["task_id"]

    # View before modify (safeguard)
    tasks_api = TasksAPI(client)
    task = tasks_api.get_task(task_id)

    # Build update payload
    updates = {}
    if "name" in arguments:
        updates["name"] = arguments["name"]
    if "description" in arguments:
        updates["description"] = arguments["description"]
    if "status" in arguments:
        updates["status"] = arguments["status"]
    if "priority" in arguments:
        priority_map = {"urgent": 1, "high": 2, "normal": 3, "low": 4}
        pri = arguments["priority"]
        updates["priority"] = priority_map.get(pri.lower(), int(pri) if pri.isdigit() else 3)

    updated_task = tasks_api.update_task(task_id, **updates)

    result = f"✓ Updated task: {updated_task['name']}\n"
    result += f"  ID: {task_id}"

    return [types.TextContent(type="text", text=result)]


async def handle_delete_task(client: ClickUpClient, arguments: dict) -> list[types.TextContent]:
    """Delete a task with view-before-modify safeguard."""
    task_id = arguments["task_id"]
    force = arguments.get("force", False)

    tasks_api = TasksAPI(client)

    # View before delete (safeguard)
    task = tasks_api.get_task(task_id)
    task_name = task.get("name", "Unknown")

    if not force:
        # In MCP context, we'll require force=true for deletion
        return [types.TextContent(
            type="text",
            text=f"⚠️  Deletion requires confirmation. To proceed, set force=true.\nTask to delete: {task_name} (ID: {task_id})"
        )]

    tasks_api.delete_task(task_id)

    return [types.TextContent(type="text", text=f"✓ Deleted task: {task_name} (ID: {task_id})")]


async def handle_set_task_status(client: ClickUpClient, arguments: dict) -> list[types.TextContent]:
    """Set task status with subtask validation."""
    task_ids = arguments["task_ids"]
    status = arguments["status"]

    tasks_api = TasksAPI(client)
    results = []

    for task_id in task_ids:
        try:
            tasks_api.update_status(task_id, status)
            results.append(f"✓ Updated {task_id} to '{status}'")
        except Exception as e:
            results.append(f"✗ Failed to update {task_id}: {e}")

    return [types.TextContent(type="text", text="\n".join(results))]


async def handle_set_task_priority(client: ClickUpClient, arguments: dict) -> list[types.TextContent]:
    """Set task priority."""
    task_id = arguments["task_id"]
    priority = arguments["priority"]

    # Map priority names to numbers
    priority_map = {"urgent": 1, "high": 2, "normal": 3, "low": 4}
    priority_num = priority_map.get(priority.lower(), int(priority) if priority.isdigit() else 3)

    tasks_api = TasksAPI(client)
    tasks_api.update_priority(task_id, priority_num)

    return [types.TextContent(type="text", text=f"✓ Set task {task_id} priority to {priority}")]


async def handle_assign_task(client: ClickUpClient, arguments: dict) -> list[types.TextContent]:
    """Assign users to task."""
    task_id = arguments["task_id"]
    user_ids = arguments["user_ids"]

    tasks_api = TasksAPI(client)
    tasks_api.assign_task(task_id, user_ids)

    return [types.TextContent(type="text", text=f"✓ Assigned {len(user_ids)} user(s) to task {task_id}")]


async def handle_unassign_task(client: ClickUpClient, arguments: dict) -> list[types.TextContent]:
    """Unassign users from task."""
    task_id = arguments["task_id"]
    user_ids = arguments["user_ids"]

    tasks_api = TasksAPI(client)
    tasks_api.unassign_task(task_id, user_ids)

    return [types.TextContent(type="text", text=f"✓ Unassigned {len(user_ids)} user(s) from task {task_id}")]


async def handle_set_task_tags(client: ClickUpClient, arguments: dict) -> list[types.TextContent]:
    """Manage task tags."""
    task_id = arguments["task_id"]
    operation = arguments["operation"]
    tags = arguments["tags"]

    tasks_api = TasksAPI(client)

    if operation == "add":
        for tag in tags:
            tasks_api.add_tag(task_id, tag)
        result = f"✓ Added {len(tags)} tag(s) to task {task_id}"
    elif operation == "remove":
        for tag in tags:
            tasks_api.remove_tag(task_id, tag)
        result = f"✓ Removed {len(tags)} tag(s) from task {task_id}"
    elif operation == "set":
        # Get current task, remove all tags, add new ones
        task = tasks_api.get_task(task_id)
        current_tags = task.get("tags", [])
        for tag in current_tags:
            tasks_api.remove_tag(task_id, tag["name"])
        for tag in tags:
            tasks_api.add_tag(task_id, tag)
        result = f"✓ Set task {task_id} tags to: {', '.join(tags)}"
    else:
        raise ValueError(f"Invalid operation: {operation}")

    return [types.TextContent(type="text", text=result)]


async def handle_get_hierarchy(client: ClickUpClient, arguments: dict) -> list[types.TextContent]:
    """Get hierarchical view of tasks."""
    list_id = resolve_resource_id(arguments["list_id"], "list")
    detail_level = arguments.get("detail_level", "summary")
    include_completed = arguments.get("include_completed", False)

    # Use DisplayManager to get hierarchy view
    display = DisplayManager(client)
    output = display.display_hierarchy(
        list_id=list_id,
        preset=detail_level,
        include_completed=include_completed,
        colorize=False  # Disable colors for MCP output
    )

    return [types.TextContent(type="text", text=output)]


async def handle_get_flat_view(client: ClickUpClient, arguments: dict) -> list[types.TextContent]:
    """Get flat view of tasks."""
    list_id = resolve_resource_id(arguments["list_id"], "list")
    detail_level = arguments.get("detail_level", "summary")

    display = DisplayManager(client)
    output = display.display_flat(
        list_id=list_id,
        preset=detail_level,
        colorize=False
    )

    return [types.TextContent(type="text", text=output)]


async def handle_filter_tasks(client: ClickUpClient, arguments: dict) -> list[types.TextContent]:
    """Get filtered view of tasks."""
    list_id = resolve_resource_id(arguments["list_id"], "list")

    # Build filter criteria
    filter_criteria = {}
    if "status" in arguments:
        filter_criteria["statuses"] = arguments["status"]
    if "priority" in arguments:
        filter_criteria["priorities"] = arguments["priority"]
    if "assignee" in arguments:
        filter_criteria["assignees"] = arguments["assignee"]
    if "tags" in arguments:
        filter_criteria["tags"] = arguments["tags"]

    display = DisplayManager(client)
    output = display.display_filtered(
        list_id=list_id,
        filter_criteria=filter_criteria,
        colorize=False
    )

    return [types.TextContent(type="text", text=output)]


async def handle_get_assigned_tasks(client: ClickUpClient, arguments: dict) -> list[types.TextContent]:
    """Get tasks assigned to user."""
    user_id = arguments.get("user_id")
    if not user_id:
        user_id = context_manager.get_default_assignee()
        if not user_id:
            raise ValueError("No user_id provided and no default assignee set")

    team_id = arguments.get("team_id")
    if not team_id:
        team_id = context_manager.get_current_workspace()
        if not team_id:
            raise ValueError("No team_id provided and no current workspace set")

    display = DisplayManager(client)
    output = display.display_assigned(
        user_id=user_id,
        team_id=team_id,
        colorize=False
    )

    return [types.TextContent(type="text", text=output)]


async def handle_get_stats(client: ClickUpClient, arguments: dict) -> list[types.TextContent]:
    """Get task statistics."""
    list_id = resolve_resource_id(arguments["list_id"], "list")

    display = DisplayManager(client)
    output = display.display_stats(list_id=list_id, colorize=False)

    return [types.TextContent(type="text", text=output)]


async def handle_add_comment(client: ClickUpClient, arguments: dict) -> list[types.TextContent]:
    """Add comment to task."""
    task_id = arguments["task_id"]
    comment_text = arguments["comment_text"]

    comments_api = CommentsAPI(client)
    comment = comments_api.create_comment(task_id, comment_text)

    result = f"✓ Added comment to task {task_id}\n"
    result += f"  Comment ID: {comment['id']}"

    return [types.TextContent(type="text", text=result)]


async def handle_list_comments(client: ClickUpClient, arguments: dict) -> list[types.TextContent]:
    """List comments on task."""
    task_id = arguments["task_id"]
    limit = arguments.get("limit", 25)

    comments_api = CommentsAPI(client)
    comments = comments_api.get_comments(task_id)

    # Format comments
    output = f"Comments on task {task_id}:\n\n"
    for i, comment in enumerate(comments[:limit], 1):
        output += f"{i}. {comment.get('user', {}).get('username', 'Unknown')}: "
        output += f"{comment.get('comment_text', '')}\n"
        output += f"   ID: {comment['id']} | Date: {comment.get('date', 'Unknown')}\n\n"

    return [types.TextContent(type="text", text=output)]


async def handle_update_comment(client: ClickUpClient, arguments: dict) -> list[types.TextContent]:
    """Update a comment."""
    comment_id = arguments["comment_id"]
    comment_text = arguments["comment_text"]

    comments_api = CommentsAPI(client)
    comments_api.update_comment(comment_id, comment_text)

    return [types.TextContent(type="text", text=f"✓ Updated comment {comment_id}")]


async def handle_delete_comment(client: ClickUpClient, arguments: dict) -> list[types.TextContent]:
    """Delete a comment."""
    comment_id = arguments["comment_id"]
    force = arguments.get("force", False)

    if not force:
        return [types.TextContent(
            type="text",
            text=f"⚠️  Deletion requires confirmation. To proceed, set force=true.\nComment ID: {comment_id}"
        )]

    comments_api = CommentsAPI(client)
    comments_api.delete_comment(comment_id)

    return [types.TextContent(type="text", text=f"✓ Deleted comment {comment_id}")]


async def handle_set_current(arguments: dict) -> list[types.TextContent]:
    """Set current context."""
    resource_type = arguments["resource_type"]
    resource_id = arguments["resource_id"]

    setters = {
        'task': context_manager.set_current_task,
        'list': context_manager.set_current_list,
        'space': context_manager.set_current_space,
        'folder': context_manager.set_current_folder,
        'workspace': context_manager.set_current_workspace,
        'assignee': lambda aid: context_manager.set_default_assignee(int(aid)),
    }

    setter = setters.get(resource_type)
    if not setter:
        raise ValueError(f"Unknown resource type: {resource_type}")

    setter(resource_id)

    return [types.TextContent(type="text", text=f"✓ Set current {resource_type} to: {resource_id}")]


async def handle_get_current() -> list[types.TextContent]:
    """Get current context."""
    context_data = {
        "workspace": context_manager.get_current_workspace(),
        "space": context_manager.get_current_space(),
        "folder": context_manager.get_current_folder(),
        "list": context_manager.get_current_list(),
        "task": context_manager.get_current_task(),
        "assignee": context_manager.get_default_assignee(),
    }

    output = "Current Context:\n"
    for key, value in context_data.items():
        if value:
            output += f"  {key}: {value}\n"

    if not any(context_data.values()):
        output += "  (no context set)\n"

    return [types.TextContent(type="text", text=output)]


async def handle_clear_current(arguments: dict) -> list[types.TextContent]:
    """Clear current context."""
    resource_type = arguments.get("resource_type", "all")

    if resource_type == "all":
        context_manager.clear_all()
        return [types.TextContent(type="text", text="✓ Cleared all context")]

    clearers = {
        'task': lambda: context_manager.set_current_task(None),
        'list': lambda: context_manager.set_current_list(None),
        'space': lambda: context_manager.set_current_space(None),
        'folder': lambda: context_manager.set_current_folder(None),
        'workspace': lambda: context_manager.set_current_workspace(None),
        'assignee': lambda: context_manager.set_default_assignee(None),
    }

    clearer = clearers.get(resource_type)
    if not clearer:
        raise ValueError(f"Unknown resource type: {resource_type}")

    clearer()

    return [types.TextContent(type="text", text=f"✓ Cleared {resource_type} context")]


async def handle_add_dependency(client: ClickUpClient, arguments: dict) -> list[types.TextContent]:
    """Add task dependency."""
    task_id = arguments["task_id"]
    depends_on = arguments["depends_on_task_id"]
    dep_type = arguments.get("dependency_type", "waiting_on")

    tasks_api = TasksAPI(client)
    tasks_api.add_dependency(task_id, depends_on, dependency_of=dep_type)

    return [types.TextContent(type="text", text=f"✓ Added {dep_type} dependency: {task_id} -> {depends_on}")]


async def handle_remove_dependency(client: ClickUpClient, arguments: dict) -> list[types.TextContent]:
    """Remove task dependency."""
    task_id = arguments["task_id"]
    depends_on = arguments["depends_on_task_id"]
    dep_type = arguments.get("dependency_type", "waiting_on")

    tasks_api = TasksAPI(client)
    tasks_api.remove_dependency(task_id, depends_on, dependency_of=dep_type)

    return [types.TextContent(type="text", text=f"✓ Removed {dep_type} dependency: {task_id} -> {depends_on}")]


async def handle_add_task_link(client: ClickUpClient, arguments: dict) -> list[types.TextContent]:
    """Add task link."""
    task_id = arguments["task_id"]
    linked_task_id = arguments["linked_task_id"]

    tasks_api = TasksAPI(client)
    tasks_api.add_link(task_id, linked_task_id)

    return [types.TextContent(type="text", text=f"✓ Linked tasks: {task_id} <-> {linked_task_id}")]


async def handle_remove_task_link(client: ClickUpClient, arguments: dict) -> list[types.TextContent]:
    """Remove task link."""
    task_id = arguments["task_id"]
    linked_task_id = arguments["linked_task_id"]

    tasks_api = TasksAPI(client)
    tasks_api.remove_link(task_id, linked_task_id)

    return [types.TextContent(type="text", text=f"✓ Unlinked tasks: {task_id} <-> {linked_task_id}")]


async def handle_bulk_create_tasks(client: ClickUpClient, arguments: dict) -> list[types.TextContent]:
    """Bulk create tasks."""
    list_id = resolve_resource_id(arguments["list_id"], "list")
    tasks_data = arguments["tasks"]

    tasks_api = TasksAPI(client)
    created_tasks = []
    failed_tasks = []

    for i, task_data in enumerate(tasks_data, 1):
        try:
            task = tasks_api.create_task(
                list_id=list_id,
                name=task_data["name"],
                description=task_data.get("description"),
                status=task_data.get("status"),
                priority=task_data.get("priority"),
                tags=task_data.get("tags"),
                assignees=task_data.get("assignees"),
                parent=task_data.get("parent")
            )
            created_tasks.append(f"✓ Task {i}: {task['name']} (ID: {task['id']})")
        except Exception as e:
            failed_tasks.append(f"✗ Task {i} ({task_data['name']}): {str(e)}")

    result = f"Bulk Create Results:\n"
    result += f"Created: {len(created_tasks)}/{len(tasks_data)}\n"
    result += f"Failed: {len(failed_tasks)}/{len(tasks_data)}\n\n"

    if created_tasks:
        result += "Created Tasks:\n" + "\n".join(created_tasks) + "\n\n"

    if failed_tasks:
        result += "Failed Tasks:\n" + "\n".join(failed_tasks)

    return [types.TextContent(type="text", text=result)]


async def handle_bulk_update_tasks(client: ClickUpClient, arguments: dict) -> list[types.TextContent]:
    """Bulk update tasks."""
    task_ids = arguments["task_ids"]
    updates = arguments["updates"]

    tasks_api = TasksAPI(client)
    updated_tasks = []
    failed_tasks = []

    # Map priority strings to numbers
    priority_map = {"urgent": 1, "high": 2, "normal": 3, "low": 4}
    if "priority" in updates:
        pri = updates["priority"]
        updates["priority"] = priority_map.get(pri.lower(), int(pri) if pri.isdigit() else 3)

    for task_id in task_ids:
        try:
            # Handle tag operations separately
            if "add_tags" in updates:
                for tag in updates["add_tags"]:
                    tasks_api.add_tag(task_id, tag)
            if "remove_tags" in updates:
                for tag in updates["remove_tags"]:
                    tasks_api.remove_tag(task_id, tag)

            # Apply other updates
            update_payload = {k: v for k, v in updates.items() if k not in ["add_tags", "remove_tags"]}
            if update_payload:
                tasks_api.update_task(task_id, **update_payload)

            updated_tasks.append(f"✓ Updated task: {task_id}")
        except Exception as e:
            failed_tasks.append(f"✗ Failed to update {task_id}: {str(e)}")

    result = f"Bulk Update Results:\n"
    result += f"Updated: {len(updated_tasks)}/{len(task_ids)}\n"
    result += f"Failed: {len(failed_tasks)}/{len(task_ids)}\n\n"

    if updated_tasks:
        result += "\n".join(updated_tasks) + "\n\n"

    if failed_tasks:
        result += "Failures:\n" + "\n".join(failed_tasks)

    return [types.TextContent(type="text", text=result)]


async def handle_get_list_tasks(client: ClickUpClient, arguments: dict) -> list[types.TextContent]:
    """Get all tasks from a list."""
    list_id = resolve_resource_id(arguments["list_id"], "list")
    include_closed = arguments.get("include_closed", False)
    subtasks = arguments.get("subtasks", True)
    detail_level = arguments.get("detail_level", "summary")

    # Build query params
    params = {
        "archived": False,
        "subtasks": subtasks,
        "include_closed": include_closed
    }

    result = client.get_list_tasks(list_id, **params)
    tasks = result.get("tasks", [])

    # Format tasks
    output = f"Tasks in list {list_id}:\n"
    output += f"Total: {len(tasks)} tasks\n\n"

    formatter = TaskFormatter()
    for i, task in enumerate(tasks, 1):
        formatted = formatter.format(task, detail_level=detail_level)
        output += f"{i}. {formatted}\n"
        if detail_level != "minimal":
            output += "\n"

    return [types.TextContent(type="text", text=output)]


async def handle_search_tasks(client: ClickUpClient, arguments: dict) -> list[types.TextContent]:
    """Search tasks across workspace."""
    workspace_id = resolve_resource_id(arguments["workspace_id"], "workspace")
    query = arguments["query"]
    detail_level = arguments.get("detail_level", "summary")

    result = client.search(workspace_id, query)
    tasks = result.get("tasks", [])

    output = f"Search results for '{query}':\n"
    output += f"Found: {len(tasks)} tasks\n\n"

    formatter = TaskFormatter()
    for i, task in enumerate(tasks, 1):
        formatted = formatter.format(task, detail_level=detail_level)
        output += f"{i}. {formatted}\n"
        if detail_level != "minimal":
            output += "\n"

    return [types.TextContent(type="text", text=output)]


async def handle_get_workspace_hierarchy(client: ClickUpClient, arguments: dict) -> list[types.TextContent]:
    """Get workspace hierarchy."""
    workspace_id = arguments["workspace_id"]

    hierarchy = client.get_workspace_hierarchy(workspace_id)

    # Format hierarchy
    output = f"Workspace Hierarchy (ID: {workspace_id}):\n\n"

    for space in hierarchy.get("teams", [{}])[0].get("spaces", []):
        space_name = space.get("name", "Unnamed Space")
        space_id = space.get("id")
        output += f"📁 Space: {space_name} (ID: {space_id})\n"

        for folder in space.get("folders", []):
            folder_name = folder.get("name", "Unnamed Folder")
            folder_id = folder.get("id")
            output += f"  📂 Folder: {folder_name} (ID: {folder_id})\n"

            for list_item in folder.get("lists", []):
                list_name = list_item.get("name", "Unnamed List")
                list_id = list_item.get("id")
                output += f"    📋 List: {list_name} (ID: {list_id})\n"

        # Lists without folders
        for list_item in space.get("lists", []):
            list_name = list_item.get("name", "Unnamed List")
            list_id = list_item.get("id")
            output += f"  📋 List: {list_name} (ID: {list_id})\n"

        output += "\n"

    return [types.TextContent(type="text", text=output)]


async def handle_add_checklist(client: ClickUpClient, arguments: dict) -> list[types.TextContent]:
    """Add checklist to task."""
    task_id = arguments["task_id"]
    checklist_name = arguments["checklist_name"]
    items = arguments.get("items", [])

    # Create checklist
    checklist = client.create_checklist(task_id, checklist_name)
    checklist_id = checklist["id"]

    # Add items
    for item_name in items:
        client.create_checklist_item(checklist_id, item_name)

    result = f"✓ Created checklist: {checklist_name}\n"
    result += f"  Checklist ID: {checklist_id}\n"
    result += f"  Items added: {len(items)}"

    return [types.TextContent(type="text", text=result)]


async def handle_update_checklist_item(client: ClickUpClient, arguments: dict) -> list[types.TextContent]:
    """Update checklist item."""
    checklist_id = arguments["checklist_id"]
    checklist_item_id = arguments["checklist_item_id"]
    resolved = arguments["resolved"]

    client.update_checklist_item(checklist_id, checklist_item_id, resolved=resolved)

    status = "completed" if resolved else "reopened"
    result = f"✓ Checklist item {status}\n"
    result += f"  Checklist ID: {checklist_id}\n"
    result += f"  Item ID: {checklist_item_id}"

    return [types.TextContent(type="text", text=result)]


async def handle_set_custom_field(client: ClickUpClient, arguments: dict) -> list[types.TextContent]:
    """Set custom field value."""
    task_id = arguments["task_id"]
    field_id = arguments["field_id"]
    value = arguments["value"]

    client.set_custom_field(task_id, field_id, value)

    result = f"✓ Set custom field\n"
    result += f"  Task ID: {task_id}\n"
    result += f"  Field ID: {field_id}\n"
    result += f"  Value: {value}"

    return [types.TextContent(type="text", text=result)]


async def async_main():
    """Run the MCP server (async implementation)."""
    logger.info("Starting ClickUp MCP Server...")

    # Check if API token is configured
    token = context_manager.get_api_token()
    if not token:
        logger.warning("No API token found. Set CLICKUP_API_TOKEN environment variable or use clickup_set_current to set it.")

    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        logger.info("MCP Server ready")
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


def main():
    """Entry point for the MCP server (sync wrapper)."""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
