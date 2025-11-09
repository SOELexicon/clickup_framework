"""
Detailed task display formatting

This module defines formatting functions for detailed task displays
"""

from typing import Dict, Any, List, Optional

def format_detailed_task(
    task: Dict[str, Any], 
    colorize_output: bool = False,
    show_description: bool = False,
    show_comments: bool = False
) -> str:
    """
    Format a task with detailed information.
    
    Args:
        task: Task dictionary
        colorize_output: Whether to use ANSI colors
        show_description: Whether to include task description
        show_comments: Whether to show task comments
        
    Returns:
        Detailed formatted task string
    """
    task_name = task.get('name', 'Unnamed Task')
    task_id = task.get('id', '')
    task_status = task.get('status', '')
    task_priority = task.get('priority', 3)
    task_description = task.get('description', '')
    
    # Basic formatting
    lines = [f"{task_name} ({task_id})"]
    lines.append(f"Status: {task_status}")
    lines.append(f"Priority: {task_priority}")
    
    # Add description if requested
    if show_description and task_description:
        lines.append("\nDescription:")
        lines.append(task_description)
    
    # Add comments if requested
    if show_comments and 'comments' in task and task['comments']:
        lines.append("\nComments:")
        for comment in task['comments']:
            lines.append(f"- {comment.get('text', '')}")
    
    return "\n".join(lines)

def format_detailed_task_list(
    tasks: List[Dict[str, Any]], 
    colorize_output: bool = False,
    show_description: bool = False,
    show_comments: bool = False
) -> str:
    """
    Format a list of tasks with detailed information.
    
    Args:
        tasks: List of task dictionaries
        colorize_output: Whether to use ANSI colors
        show_description: Whether to include task descriptions
        show_comments: Whether to show task comments
        
    Returns:
        Formatted string with detailed task list
    """
    sections = []
    for task in tasks:
        sections.append(
            format_detailed_task(
                task, 
                colorize_output, 
                show_description, 
                show_comments
            )
        )
        sections.append("-" * 40)  # Separator
    
    return "\n".join(sections) 