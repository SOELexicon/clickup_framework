"""Dump command for exporting ClickUp resources to files or console."""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from clickup_framework import ClickUpClient, get_context_manager
from clickup_framework.utils.colors import colorize, TextColor, TextStyle
from clickup_framework.cli_error_handler import handle_cli_error


def sanitize_filename(name: str) -> str:
    """
    Sanitize a string to be safe for use as a filename.

    Args:
        name: The string to sanitize

    Returns:
        A filesystem-safe version of the string
    """
    # Replace problematic characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')

    # Remove leading/trailing whitespace and dots
    name = name.strip('. ')

    # Limit length to avoid filesystem issues
    if len(name) > 200:
        name = name[:200]

    return name or 'unnamed'


def format_task_markdown(task: Dict[str, Any], include_subtasks: bool = False) -> str:
    """
    Format a task as markdown.

    Args:
        task: Task data from ClickUp API
        include_subtasks: Whether to include subtask information

    Returns:
        Markdown formatted task content
    """
    md = []

    # Title
    md.append(f"# {task['name']}\n")

    # Metadata
    md.append("## Metadata\n")
    md.append(f"- **Task ID**: `{task['id']}`")
    md.append(f"- **Status**: {task['status']['status']}")

    if task.get('priority'):
        priority_map = {1: 'Urgent', 2: 'High', 3: 'Normal', 4: 'Low'}
        priority = task['priority'].get('priority')
        if priority:
            md.append(f"- **Priority**: {priority_map.get(int(priority), priority)}")

    if task.get('assignees'):
        assignees = ', '.join([a['username'] for a in task['assignees']])
        md.append(f"- **Assignees**: {assignees}")

    if task.get('tags'):
        tags = ', '.join([t['name'] for t in task['tags']])
        md.append(f"- **Tags**: {tags}")

    if task.get('due_date'):
        md.append(f"- **Due Date**: {task['due_date']}")

    if task.get('date_created'):
        md.append(f"- **Created**: {task['date_created']}")

    if task.get('date_updated'):
        md.append(f"- **Updated**: {task['date_updated']}")

    # URL
    md.append(f"- **URL**: {task['url']}\n")

    # Description
    if task.get('description'):
        md.append("## Description\n")
        md.append(f"{task['description']}\n")

    # Custom fields
    if task.get('custom_fields'):
        md.append("## Custom Fields\n")
        for field in task['custom_fields']:
            name = field.get('name', 'Unknown')
            value = field.get('value', 'N/A')
            md.append(f"- **{name}**: {value}")
        md.append("")

    # Checklists
    if task.get('checklists'):
        md.append("## Checklists\n")
        for checklist in task['checklists']:
            md.append(f"### {checklist.get('name', 'Unnamed Checklist')}\n")
            for item in checklist.get('items', []):
                status = '✓' if item.get('resolved') else '○'
                md.append(f"- [{status}] {item.get('name', 'Unnamed item')}")
            md.append("")

    # Subtasks info
    if include_subtasks and task.get('subtasks'):
        md.append("## Subtasks\n")
        md.append(f"This task has {len(task['subtasks'])} subtask(s). See subdirectories for details.\n")

    # Dependencies
    if task.get('dependencies') or task.get('linked_tasks'):
        md.append("## Dependencies\n")

        if task.get('dependencies'):
            deps = task['dependencies']
            if deps:
                md.append("### Waiting On\n")
                for dep in deps:
                    md.append(f"- {dep.get('task_id', 'Unknown')}")
                md.append("")

        if task.get('linked_tasks'):
            md.append("### Linked Tasks\n")
            for link in task['linked_tasks']:
                md.append(f"- {link.get('task_id', 'Unknown')}")
            md.append("")

    return '\n'.join(md)


def dump_task_to_markdown(client: ClickUpClient, task_id: str, output_dir: Path,
                          recursive: bool = True, depth: int = 0) -> None:
    """
    Dump a task and its subtasks to markdown files.

    Args:
        client: ClickUp client instance
        task_id: ID of the task to dump
        output_dir: Directory to save files in
        recursive: Whether to recursively dump subtasks
        depth: Current recursion depth (for logging)
    """
    try:
        # Fetch task with subtasks
        task = client.get_task(task_id, include_subtasks=True)

        # Create markdown content
        has_subtasks = task.get('subtasks') and len(task['subtasks']) > 0
        content = format_task_markdown(task, include_subtasks=has_subtasks)

        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save task markdown
        task_name = sanitize_filename(task['name'])
        task_file = output_dir / f"{task_name}.md"
        task_file.write_text(content, encoding='utf-8')

        indent = "  " * depth
        print(f"{indent}✓ Dumped: {task['name']} ({task_id})")

        # Recursively dump subtasks
        if recursive and has_subtasks:
            # Create subdirectory for subtasks
            subtasks_dir = output_dir / f"{task_name}_subtasks"

            for subtask in task['subtasks']:
                subtask_id = subtask['id']
                dump_task_to_markdown(client, subtask_id, subtasks_dir, recursive=True, depth=depth+1)

    except Exception as e:
        print(f"Error dumping task {task_id}: {e}", file=sys.stderr)


def dump_list_to_markdown(client: ClickUpClient, list_id: str, output_dir: Path) -> None:
    """
    Dump an entire list with all tasks and their hierarchy.

    Args:
        client: ClickUp client instance
        list_id: ID of the list to dump
        output_dir: Directory to save files in
    """
    try:
        # Get list info
        list_data = client.get_list(list_id)
        list_name = sanitize_filename(list_data['name'])

        print(f"📋 Dumping list: {list_data['name']} ({list_id})")

        # Create list directory
        list_dir = output_dir / list_name
        list_dir.mkdir(parents=True, exist_ok=True)

        # Create list info file
        list_info = f"# {list_data['name']}\n\n"
        list_info += f"**List ID**: `{list_id}`\n\n"
        if list_data.get('content'):
            list_info += f"## Description\n\n{list_data['content']}\n\n"

        (list_dir / "README.md").write_text(list_info, encoding='utf-8')

        # Get all tasks in the list
        tasks = client.get_tasks(list_id, include_closed=True, subtasks=False)

        print(f"Found {len(tasks)} top-level tasks")

        # Dump each top-level task (subtasks will be handled recursively)
        for task in tasks:
            task_id = task['id']
            dump_task_to_markdown(client, task_id, list_dir, recursive=True, depth=1)

        print(f"\n✓ List dump complete: {list_dir}")

    except Exception as e:
        handle_cli_error(e, {'command': 'dump list', 'list_id': list_id})


def dump_task_to_json(client: ClickUpClient, task_id: str) -> Dict[str, Any]:
    """
    Get task data as JSON.

    Args:
        client: ClickUp client instance
        task_id: ID of the task

    Returns:
        Task data dictionary
    """
    return client.get_task(task_id, include_subtasks=True)


def dump_list_to_json(client: ClickUpClient, list_id: str) -> Dict[str, Any]:
    """
    Get list data with all tasks as JSON.

    Args:
        client: ClickUp client instance
        list_id: ID of the list

    Returns:
        Dictionary with list info and all tasks
    """
    list_data = client.get_list(list_id)
    tasks = client.get_tasks(list_id, include_closed=True, subtasks=True)

    return {
        'list': list_data,
        'tasks': tasks,
        'task_count': len(tasks)
    }


def dump_doc_to_markdown(client: ClickUpClient, workspace_id: str, doc_id: str,
                        output_dir: Path) -> None:
    """
    Dump a doc to markdown file.

    Args:
        client: ClickUp client instance
        workspace_id: Workspace ID
        doc_id: Doc ID
        output_dir: Directory to save file in
    """
    try:
        doc = client.get_doc(workspace_id, doc_id)

        doc_name = sanitize_filename(doc.get('name', f'doc_{doc_id}'))

        print(f"📄 Dumping doc: {doc.get('name', 'Unnamed')} ({doc_id})")

        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create markdown content
        md = []
        md.append(f"# {doc.get('name', 'Unnamed Doc')}\n")
        md.append(f"**Doc ID**: `{doc_id}`\n")

        # Add pages
        if doc.get('pages'):
            for page in doc['pages']:
                md.append(f"## {page.get('name', 'Unnamed Page')}\n")
                if page.get('content'):
                    md.append(f"{page['content']}\n")

        content = '\n'.join(md)

        # Save file
        doc_file = output_dir / f"{doc_name}.md"
        doc_file.write_text(content, encoding='utf-8')

        print(f"✓ Doc dump complete: {doc_file}")

    except Exception as e:
        handle_cli_error(e, {'command': 'dump doc', 'workspace_id': workspace_id, 'doc_id': doc_id})


def dump_command(args):
    """Main dump command handler."""
    context = get_context_manager()
    client = ClickUpClient()

    # Determine resource type
    resource_type = args.resource_type

    # Handle output format
    output_format = args.format if hasattr(args, 'format') else 'markdown'
    output_dir = Path(args.output_dir if hasattr(args, 'output_dir') and args.output_dir else './dump')

    try:
        if resource_type == 'list':
            # Resolve list ID
            list_id = context.resolve_id('list', args.resource_id)

            if output_format == 'json':
                data = dump_list_to_json(client, list_id)
                if hasattr(args, 'output_dir') and args.output_dir:
                    output_file = output_dir / f"list_{list_id}.json"
                    output_dir.mkdir(parents=True, exist_ok=True)
                    output_file.write_text(json.dumps(data, indent=2), encoding='utf-8')
                    print(f"✓ Saved to: {output_file}")
                else:
                    print(json.dumps(data, indent=2))

            elif output_format == 'console':
                data = dump_list_to_json(client, list_id)
                print(f"\n📋 List: {data['list']['name']}")
                print(f"   Tasks: {data['task_count']}")
                print("\nTasks:")
                for task in data['tasks']:
                    status = task['status']['status']
                    print(f"  • [{status}] {task['name']} ({task['id']})")

            else:  # markdown (default)
                dump_list_to_markdown(client, list_id, output_dir)

        elif resource_type == 'task':
            # Resolve task ID
            task_id = context.resolve_id('task', args.resource_id)

            if output_format == 'json':
                data = dump_task_to_json(client, task_id)
                if hasattr(args, 'output_dir') and args.output_dir:
                    output_file = output_dir / f"task_{task_id}.json"
                    output_dir.mkdir(parents=True, exist_ok=True)
                    output_file.write_text(json.dumps(data, indent=2), encoding='utf-8')
                    print(f"✓ Saved to: {output_file}")
                else:
                    print(json.dumps(data, indent=2))

            elif output_format == 'console':
                task = dump_task_to_json(client, task_id)
                print(f"\n📋 Task: {task['name']}")
                print(f"   ID: {task['id']}")
                print(f"   Status: {task['status']['status']}")
                if task.get('description'):
                    print(f"\n{task['description']}")

            else:  # markdown (default)
                dump_task_to_markdown(client, task_id, output_dir, recursive=True)

        elif resource_type == 'doc':
            # Need workspace_id and doc_id
            if not hasattr(args, 'doc_id'):
                print("Error: doc requires both workspace_id and doc_id", file=sys.stderr)
                print("Usage: cum dump doc <workspace_id> <doc_id>", file=sys.stderr)
                sys.exit(1)

            workspace_id = context.resolve_id('workspace', args.resource_id)
            doc_id = args.doc_id

            if output_format == 'json':
                data = client.get_doc(workspace_id, doc_id)
                if hasattr(args, 'output_dir') and args.output_dir:
                    output_file = output_dir / f"doc_{doc_id}.json"
                    output_dir.mkdir(parents=True, exist_ok=True)
                    output_file.write_text(json.dumps(data, indent=2), encoding='utf-8')
                    print(f"✓ Saved to: {output_file}")
                else:
                    print(json.dumps(data, indent=2))

            elif output_format == 'console':
                doc = client.get_doc(workspace_id, doc_id)
                print(f"\n📄 Doc: {doc.get('name', 'Unnamed')}")
                print(f"   ID: {doc_id}")
                if doc.get('pages'):
                    print(f"   Pages: {len(doc['pages'])}")

            else:  # markdown (default)
                dump_doc_to_markdown(client, workspace_id, doc_id, output_dir)

        else:
            print(f"Error: Unknown resource type '{resource_type}'", file=sys.stderr)
            print("Supported types: list, task, doc", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        if os.getenv('DEBUG'):
            raise
        handle_cli_error(e)


def register_command(subparsers):
    """Register the dump command and its subcommands."""
    dump_parser = subparsers.add_parser(
        'dump',
        help='Dump ClickUp resources (lists, tasks, docs) to files or console'
    )

    dump_subparsers = dump_parser.add_subparsers(dest='resource_type', help='Resource type to dump')

    # List dump
    list_parser = dump_subparsers.add_parser('list', help='Dump a list with all tasks and hierarchy')
    list_parser.add_argument('resource_id', help='List ID (or "current")')
    list_parser.add_argument('--output-dir', '-o', help='Output directory (default: ./dump)')
    list_parser.add_argument('--format', '-f', choices=['markdown', 'json', 'console'],
                           default='markdown', help='Output format (default: markdown)')
    list_parser.set_defaults(func=dump_command)

    # Task dump
    task_parser = dump_subparsers.add_parser('task', help='Dump a task and its subtasks')
    task_parser.add_argument('resource_id', help='Task ID (or "current")')
    task_parser.add_argument('--output-dir', '-o', help='Output directory (default: ./dump)')
    task_parser.add_argument('--format', '-f', choices=['markdown', 'json', 'console'],
                           default='markdown', help='Output format (default: markdown)')
    task_parser.set_defaults(func=dump_command)

    # Doc dump
    doc_parser = dump_subparsers.add_parser('doc', help='Dump a doc to markdown')
    doc_parser.add_argument('resource_id', help='Workspace ID (or "current")')
    doc_parser.add_argument('doc_id', help='Doc ID')
    doc_parser.add_argument('--output-dir', '-o', help='Output directory (default: ./dump)')
    doc_parser.add_argument('--format', '-f', choices=['markdown', 'json', 'console'],
                           default='markdown', help='Output format (default: markdown)')
    doc_parser.set_defaults(func=dump_command)
