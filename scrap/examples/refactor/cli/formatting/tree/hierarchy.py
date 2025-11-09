"""
Tree Hierarchy Formatting Module

This module handles formatting tasks in hierarchical tree structures.

Task: tsk_1e88842d - Tree Structure Validation
dohcount: 1
"""

from typing import List, Dict, Any, Optional, Set, Tuple
import logging
import re
import sys
import traceback

# Remove the import of _convert_escaped_newlines
# from refactor.cli.commands.utils import _convert_escaped_newlines

# Import common tag handling
from refactor.cli.formatting.common.tags import format_tag_line, TAG_EMOJI
from refactor.cli.formatting.common.task_info import FormatOptions, format_task_basic_info, format_task_score

# Add the function directly in this module
def _convert_escaped_newlines(text: str) -> str:
    """
    Convert escaped newline sequences (\\n) to actual newlines.
    
    This ensures proper processing and indentation of multi-line text
    in tree views and other formatted output.
    
    Args:
        text: The text that may contain escaped newlines
        
    Returns:
        Text with escaped newlines converted to actual newlines
    """
    if text and isinstance(text, str) and '\\n' in text:
        return text.replace('\\n', '\n')
    return text

def format_task_hierarchy(
    tasks: List[Dict[str, Any]],
    options: FormatOptions,
    level: int = 0,
    parent_id: str = None,
    displayed_task_ids: Optional[Set[str]] = None,
    validate_tree: bool = False,
    show_orphaned: bool = True,
    trace: bool = False
) -> List[str]:
    """
    Format a list of task dictionaries into a hierarchical structure.
    
    This function returns a list of formatted lines, not a single string.
    
    Args:
        tasks: List of task dictionaries
        options: Format options
        level: Current indentation level
        parent_id: ID of the parent task for this level
        displayed_task_ids: Set of task IDs already displayed to avoid duplicates
        validate_tree: Whether to validate the tree structure
        show_orphaned: Whether to show orphaned tasks at the bottom
        trace: Whether to show detailed stack traces on error
        
    Returns:
        List of formatted task lines
    """
    from refactor.cli.formatting.task import format_task_basic_info
    
    try:
        # Initialize result list
        result_lines = []
        
        # Initialize displayed task IDs set if not provided
        if displayed_task_ids is None:
            displayed_task_ids = set()
        
        # Create a map of task IDs to tasks for quick lookup
        tasks_map = {task.get('id'): task for task in tasks if task.get('id')}
        
        # Filter tasks for this level (parent_id == None for root tasks)
        current_level_tasks = [
            task for task in tasks 
            if task.get('parent_id') == parent_id and task.get('id') not in displayed_task_ids
        ]
        
        # Sort tasks by status (incomplete first), then priority (lowest first), then name
        current_level_tasks = sorted(
            current_level_tasks,
            key=lambda t: (
                str(t.get('status', '')).lower() == 'complete', 
                int(t.get('priority', 4)),
                t.get('name', '')
            )
        )
        
        # Log the number of tasks at this level
        if level == 0:
            logging.debug(f"Found {len(current_level_tasks)} root tasks")
        
        # Calculate indentation for this level
        indent = '  ' * level
        
        # Process each task at this level
        for idx, task in enumerate(current_level_tasks):
            task_id = task.get('id')
            if not task_id:
                continue
            
            # Skip if already displayed
            if task_id in displayed_task_ids:
                continue
            
            # Mark this task as displayed
            displayed_task_ids.add(task_id)
            
            # Determine prefixes (will be empty at root level)
            prefix = indent
            
            # Format task with basic info
            formatted_task = format_task_basic_info(
                task,
                colorize_output=options.colorize_output,
                show_ids=options.show_ids,
                show_score=options.show_score,
                show_tags=options.show_tags,
                show_description=options.show_descriptions,
                show_comments=options.show_comments,
                show_dates=options.show_dates
            )
            
            # Add the formatted task to the results
            result_lines.append(formatted_task)
            
            # Process child tasks recursively
            child_tasks = [
                t for t in tasks 
                if t.get('parent_id') == task_id and t.get('id') not in displayed_task_ids
            ]
            
            if child_tasks:
                # Format child tasks recursively
                child_lines = format_task_hierarchy(
                    tasks,
                    options,
                    level + 1,
                    parent_id=task_id,
                    displayed_task_ids=displayed_task_ids,
                    validate_tree=validate_tree
                )
                
                # Add child lines to results
                result_lines.extend(child_lines)
        
        # Process orphaned tasks if at root level and requested
        if level == 0 and show_orphaned:
            # Find all orphaned tasks (have parent_id but parent not in tasks)
            orphaned_tasks = [
                task for task in tasks
                if task.get('parent_id') and 
                task.get('parent_id') not in tasks_map and 
                task.get('id') not in displayed_task_ids
            ]
            
            if orphaned_tasks:
                # Add a separator for orphaned tasks
                if options.colorize_output:
                    from refactor.utils.colors import TextColor, colorize
                    result_lines.append(colorize("\nOrphaned Tasks (parent missing):", TextColor.BRIGHT_YELLOW))
                else:
                    result_lines.append("\nOrphaned Tasks (parent missing):")
                
                # Format each orphaned task
                orphaned_formatted = format_task_hierarchy(
                    orphaned_tasks,
                    options,
                    level=0,  # Start at level 0 for orphaned tasks
                    parent_id=None,  # No parent
                    displayed_task_ids=displayed_task_ids,
                    validate_tree=False,  # No need to validate orphaned tasks
                    show_orphaned=False  # Prevent recursive orphan search
                )
                
                result_lines.extend(orphaned_formatted)
        
        # Validate tree structure if requested (find cycles, etc.)
        if level == 0 and validate_tree:
            # Build task parent-child map
            parent_child_map = {}
            for task in tasks:
                task_id = task.get('id')
                parent_id = task.get('parent_id')
                
                if task_id:
                    if parent_id:
                        if parent_id not in parent_child_map:
                            parent_child_map[parent_id] = []
                        parent_child_map[parent_id].append(task_id)
            
            # Detect cycles in the task hierarchy
            visited = set()
            recursive_stack = set()
            
            def has_cycle(node):
                visited.add(node)
                recursive_stack.add(node)
                
                # Check all children
                for child in parent_child_map.get(node, []):
                    if child not in visited:
                        if has_cycle(child):
                            return True
                    elif child in recursive_stack:
                        return True
                
                recursive_stack.remove(node)
                return False
            
            # Check all tasks that haven't been visited yet
            cycles_found = False
            for task in tasks:
                task_id = task.get('id')
                if task_id and task_id not in visited:
                    if has_cycle(task_id):
                        cycles_found = True
                        if options.colorize_output:
                            from refactor.utils.colors import TextColor, colorize
                            result_lines.append(colorize("\nWARNING: Cycles detected in task hierarchy!", TextColor.BRIGHT_RED))
                        else:
                            result_lines.append("\nWARNING: Cycles detected in task hierarchy!")
                        break
        
        # Add summary at the root level
        if level == 0:
            # Calculate the total tasks that could be displayed based on filters
            displayable_tasks = []
            for task in tasks:
                task_id = task.get('id')
                if not options.include_completed and str(task.get('status', '')).lower() == 'complete':
                    continue
                displayable_tasks.append(task)
            
            total_displayable_tasks = len(displayable_tasks)
            # Ensure status is converted to string before comparison
            completed_displayable_tasks = sum(1 for task in displayable_tasks if str(task.get('status', '')).lower() == 'complete')
            
            # Count actual visible IDs in the output 
            visible_ids = set()
            for line in result_lines:
                # Extract task IDs using regex
                ids = re.findall(r'\[tsk_[a-f0-9]{8}\]', line)
                for id_match in ids:
                    # Extract just the ID part without brackets
                    task_id = id_match[1:-1]  # Remove [ and ]
                    visible_ids.add(task_id)
            
            # Use the visible IDs count instead of displayed_task_ids
            total_task_ids = len(visible_ids)
            
            # Count duplicates by comparing the number of task IDs to the number of tasks
            # that should have been displayed
            duplicate_count = 0
            if total_displayable_tasks > total_task_ids:
                duplicate_count = total_displayable_tasks - total_task_ids
            
            # Add empty line before summary
            result_lines.append("")
            
            # Format summary line
            if options.colorize_output:
                from refactor.utils.colors import TextColor, colorize
                completion_color = TextColor.GREEN if completed_displayable_tasks == total_displayable_tasks else TextColor.YELLOW
                summary = f"Total Displayed: {colorize(f'{completed_displayable_tasks}/{total_displayable_tasks} tasks complete', completion_color)}"
                summary += f"\nTask IDs: {total_task_ids}, Duplicates: {duplicate_count}"
            else:
                summary = f"Total Displayed: {completed_displayable_tasks}/{total_displayable_tasks} tasks complete"
                summary += f"\nTask IDs: {total_task_ids}, Duplicates: {duplicate_count}"
            
            result_lines.append(summary)
        
        return result_lines
    except Exception as e:
        error_msg = f"Error in format_task_hierarchy: {e}"
        if trace:
            error_msg += f"\n{traceback.format_exc()}"
        logging.error(error_msg)
        return f"Error formatting task hierarchy: {e}" 