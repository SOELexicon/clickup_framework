"""
Simple task display formatting

This module defines basic task formatting functions for simple text output
"""

from typing import Dict, Any, List, Optional

def format_simple_task(task: Dict[str, Any], colorize_output: bool = False) -> str:
    """
    Format a task in a simple one-line format.
    
    Args:
        task: Task dictionary
        colorize_output: Whether to use ANSI colors
        
    Returns:
        Simple formatted task string
    """
    task_name = task.get('name', 'Unnamed Task')
    task_status = task.get('status', '')
    
    return f"{task_name} [{task_status}]"

def format_simple_task_list(tasks: List[Dict[str, Any]], colorize_output: bool = False) -> str:
    """
    Format a list of tasks in a simple format.
    
    Args:
        tasks: List of task dictionaries
        colorize_output: Whether to use ANSI colors
        
    Returns:
        Formatted string with simple task list
    """
    lines = []
    for task in tasks:
        lines.append(format_simple_task(task, colorize_output))
    
    return "\n".join(lines) 