"""
Statistics display formatting

This module defines formatting functions for displaying task statistics and summaries
"""

from typing import Dict, Any, List, Optional
from collections import Counter

def format_task_stats(tasks: List[Dict[str, Any]], colorize_output: bool = False) -> str:
    """
    Format statistics about a collection of tasks.
    
    Args:
        tasks: List of task dictionaries
        colorize_output: Whether to use ANSI colors
        
    Returns:
        Formatted string with task statistics
    """
    # Count tasks by status
    status_counts = Counter(task.get('status', 'unknown') for task in tasks)
    
    # Count tasks by priority
    priority_counts = Counter(task.get('priority', 'unknown') for task in tasks)
    
    # Count tasks by type
    type_counts = Counter(task.get('task_type', 'task') for task in tasks)
    
    # Build statistics output
    lines = [f"Task Statistics (Total: {len(tasks)})"]
    lines.append("\nStatus:")
    for status, count in status_counts.items():
        lines.append(f"  {status}: {count}")
    
    lines.append("\nPriority:")
    for priority, count in priority_counts.items():
        lines.append(f"  P{priority}: {count}")
    
    lines.append("\nTask Type:")
    for task_type, count in type_counts.items():
        lines.append(f"  {task_type}: {count}")
    
    return "\n".join(lines)

def format_completion_stats(tasks: List[Dict[str, Any]], colorize_output: bool = False) -> str:
    """
    Format completion statistics for a collection of tasks.
    
    Args:
        tasks: List of task dictionaries
        colorize_output: Whether to use ANSI colors
        
    Returns:
        Formatted string with completion statistics
    """
    # Get task completion counts
    total = len(tasks)
    completed = sum(1 for task in tasks if str(task.get('status', '')).lower() == 'complete')
    
    # Calculate completion percentage
    completion_pct = (completed / total) * 100 if total > 0 else 0
    
    # Build completion stats output
    lines = [f"Completion Progress: {completion_pct:.1f}%"]
    lines.append(f"Completed: {completed}/{total} tasks")
    
    # Calculate progress bar
    bar_width = 40
    completed_width = int((completed / total) * bar_width) if total > 0 else 0
    progress_bar = '[' + '#' * completed_width + ' ' * (bar_width - completed_width) + ']'
    lines.append(progress_bar)
    
    return "\n".join(lines) 