from typing import List, Dict, Any
import sys

def format_task_tree(
    tasks: List[Dict[str, Any]],
    colorize_output: bool = True,
    show_ids: bool = False,
    show_score: bool = False,
    show_tags: bool = False,
    tag_style: str = "colored",
    show_type_emoji: bool = True,
    show_descriptions: bool = False,
    show_dates: bool = False,
    show_comments: int = 0,
    indent: str = "  "
) -> List[str]:
    """
    Format tasks in a tree structure.
    
    Args:
        tasks: List of task dictionaries
        colorize_output: Whether to use ANSI colors
        show_ids: Whether to show task IDs in square brackets
        show_score: Whether to show task scores
        show_tags: Whether to show task tags
        tag_style: Style for tag display
        show_type_emoji: Whether to show task type emoji
        show_descriptions: Whether to show task descriptions
        show_dates: Whether to show task dates
        show_comments: Number of comments to show
        indent: Indentation string
        
    Returns:
        List of formatted output lines
    """
    # Debug print to stderr so it doesn't get redirected
    print(f"DEBUG: format_task_tree - show_ids={show_ids}", file=sys.stderr)
    
    output_lines = []
    
    # Sort tasks by priority then name
    sorted_tasks = sorted(
        tasks,
        key=lambda t: (t.get('priority', 3), t.get('name', '').lower())
    )
    
    for task in sorted_tasks:
        # Format basic task info
        task_line = format_task_basic_info(
            task,
            colorize_output=colorize_output,
            show_ids=show_ids,
            show_score=show_score,
            show_tags=show_tags,
            tag_style=tag_style,
            show_type_emoji=show_type_emoji,
            show_descriptions=show_descriptions,
            show_dates=show_dates,
            show_comments=show_comments
        )
        
        # Add indentation
        output_lines.append(f"{indent}{task_line}")
        
        # Format subtasks if any
        subtasks = task.get('subtasks', [])
        if subtasks:
            subtask_lines = format_task_tree(
                subtasks,
                colorize_output=colorize_output,
                show_ids=show_ids,
                show_score=show_score,
                show_tags=show_tags,
                tag_style=tag_style,
                show_type_emoji=show_type_emoji,
                show_descriptions=show_descriptions,
                show_dates=show_dates,
                show_comments=show_comments,
                indent=f"{indent}  "
            )
            output_lines.extend(subtask_lines)
    
    return output_lines 