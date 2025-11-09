"""
Container Hierarchy Formatting Module

This module provides utilities for formatting tasks in a container hierarchy (spaces -> folders -> lists).

Task: tsk_1e88842d - Tree Structure Validation
dohcount: 2

Related Tasks:
    - tsk_bf28d342 - Update CLI Module Comments (related)

Used By:
    - list_command.py: For displaying tasks organized by container

Purpose:
    Provides functionality to format and display tasks organized by their container hierarchy,
    ensuring proper indentation, branch characters, and visual representation of the hierarchy.

Requirements:
    - Must handle all container levels (spaces, folders, lists)
    - Must format tasks with correct hierarchical relationships
    - Must handle orphaned tasks gracefully
    - CRITICAL: Must validate vertical pipe characters for consistent tree structure
"""

from typing import Dict, List, Any, Set, Tuple, Optional
import logging
import json
import os
import sys
import re
import traceback

# Initialize logger
logger = logging.getLogger(__name__)

# Remove the import of _convert_escaped_newlines
# from refactor.cli.commands.utils import _convert_escaped_newlines

from refactor.cli.formatting.tree.validation import validate_tree_structure, fix_tree_structure
from refactor.cli.formatting.common.task_info import (
    FormatOptions, 
    format_task_basic_info, 
    format_task_score, 
    get_task_status_color, 
    get_task_priority_color,
    get_task_type_emoji,
    get_task_emoji
)
from refactor.utils.colors import colorize, TextColor, TextStyle

# Helper functions for container formatting
def container_color(container_type):
    """Return the color for a container type."""
    if container_type == 'space':
        return TextColor.BRIGHT_BLUE
    elif container_type == 'folder':
        return TextColor.BRIGHT_GREEN
    elif container_type == 'list':
        return TextColor.BRIGHT_YELLOW
    return TextColor.WHITE

def completion_stats_color(completed, total):
    """Return the color for completion stats based on completion percentage."""
    if total == 0:
        return TextColor.BRIGHT_BLACK
    percentage = (completed / total) * 100
    if percentage == 100:
        return TextColor.BRIGHT_GREEN
    elif percentage >= 75:
        return TextColor.GREEN
    elif percentage >= 50:
        return TextColor.BRIGHT_YELLOW
    elif percentage >= 25:
        return TextColor.YELLOW
    return TextColor.RED

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

def _format_container_tasks(
    tasks_in_list: List[Dict[str, Any]],
    tasks_map: Dict[str, Dict],
    displayed_task_ids: Set[str],
    task_prefix: str,
    orphaned_task_ids: Set[str],
    is_last_space: bool,
    is_last_folder: bool,
    is_last_list: bool,
    result_lines: List[str],
    format_options: FormatOptions,
    trace: bool = False  # Add trace parameter
) -> None:
    """
    Format tasks within a container (list) and add them to the result lines.

    Task: tsk_1e88842d - Tree Structure Validation
    dohcount: 3

    Args:
        tasks_in_list: Tasks in the current list
        tasks_map: Map of task IDs to tasks
        displayed_task_ids: Set of task IDs that have already been displayed
        task_prefix: Prefix for the task lines based on container hierarchy
        orphaned_task_ids: Set of task IDs that are orphaned
        is_last_space: Whether this is in the last space
        is_last_folder: Whether this is in the last folder
        is_last_list: Whether this is the last list
        result_lines: List of strings to append formatted output to
        format_options: FormatOptions instance managing display settings.
        trace: Whether to show detailed stack traces on error
    """
    try:
        if trace:
            # Log key information to aid in debugging
            logger.debug(f"_format_container_tasks called with format_options: {format_options.__dict__}")
            logger.debug(f"Show IDs setting: {format_options.show_ids}")
            
        include_completed = format_options.include_completed
        hide_orphaned = format_options.hide_orphaned

        # Get the list tasks (only parent/root tasks within this list)
        list_tasks = []
        for task_id in set([t.get('id') for t in tasks_in_list]):
            # Skip orphaned tasks if hide_orphaned is True
            if hide_orphaned and task_id in orphaned_task_ids:
                continue
            
            if task_id in tasks_map:
                task = tasks_map[task_id]
                list_tasks.append(task)
        
        # Gather root tasks (no parent or parent not in our tasks)
        root_tasks = []
        for task in tasks_in_list:
            parent_id = task.get('parent_id')
            # Add to root tasks only if:
            # 1. Not a subtask of any task in our task map, OR
            # 2. Parent task is not in this list
            if not parent_id or parent_id not in tasks_map or parent_id not in [t.get('id') for t in tasks_in_list]:
                # Filter based on include_completed status
                if include_completed or str(task.get('status', '')).lower() != 'complete':
                    root_tasks.append(task)
        
        # Sort root tasks
        sorted_root_tasks = sorted(
            root_tasks,
            key=lambda t: (
                str(t.get('status', '')).lower() == 'complete',
                int(t.get('priority', 4)),                  # Lower priority first
                t.get('name', '')                           # Alphabetical
            )
        )
        
        # Format tasks under this list with proper visual hierarchy
        for root_idx, root_task in enumerate(sorted_root_tasks):
            try:
                is_last_root = root_idx == len(sorted_root_tasks) - 1
                
                # Skip if already displayed
                if root_task.get('id') in displayed_task_ids:
                    continue
                
                # Format task with proper indentation
                task_lines = []
                
                # Add debug info here
                if trace:
                    logger.debug(f"Formatting task {root_task.get('id')} with show_ids={format_options.show_ids}")
                    
                # Pass format_options to format_task_basic_info
                task_description = format_task_basic_info(
                    root_task,
                    options=format_options
                )
                branch = "└─" if is_last_root else "├─"
                
                # Handle multi-line output from format_task_basic_info
                if "\n" in task_description:
                    # Split the description into lines
                    desc_lines = task_description.split("\n")
                    # First line gets the branch character
                    first_task_line = f"{task_prefix}{branch}{desc_lines[0]}"
                    task_lines.append(first_task_line)
                    
                    # Additional lines get indentation that accounts for the branch
                    for additional_line in desc_lines[1:]:
                        # Use the same prefix as subtasks would use
                        additional_prefix = task_prefix + ("  " if is_last_root else "│ ")
                        task_lines.append(f"{additional_prefix}{additional_line}")
                else:
                    # Single line output
                    first_task_line = f"{task_prefix}{branch}{task_description}"
                    task_lines.append(first_task_line)
                
                # Mark task as displayed
                displayed_task_ids.add(root_task.get('id'))
                
                # Pass format_options to _format_subtask_hierarchy
                _format_subtask_hierarchy(
                    root_task,
                    tasks_map,
                    task_lines,
                    displayed_task_ids,
                    task_prefix + ("  " if is_last_root else "│ "),
                    orphaned_task_ids,
                    format_options,
                    trace=trace  # Pass trace parameter
                )
                
                # Add task lines to result lines
                for line in task_lines:
                    result_lines.append(line)
            except Exception as e:
                error_msg = f"Error formatting task {root_task.get('id')}: {e}"
                if trace:
                    error_msg += f"\n{traceback.format_exc()}"
                logger.error(error_msg)
                # Add an error line to the output
                result_lines.append(f"{task_prefix}⚠️ Error formatting task: {e}")
        
    except Exception as e:
        error_msg = f"Error in _format_container_tasks: {e}"
        if trace:
            error_msg += f"\n{traceback.format_exc()}"
        logger.error(error_msg)
        # Add an error line to the output
        result_lines.append(f"⚠️ Error formatting container tasks: {e}")

def _format_orphaned_list_tasks(
    tasks_in_list: List[Dict[str, Any]],
    tasks_map: Dict[str, Dict],
    displayed_task_ids: Set[str],
    orphaned_task_ids: Set[str],
    is_last_space: bool,
    is_last_folder: bool,
    is_last_list: bool,
    result_lines: List[str],
    format_options: FormatOptions
) -> None:
    """
    Format orphaned tasks within a list.
    
    Task: tsk_1e88842d - Tree Structure Validation
    dohcount: 2
    
    Args:
        tasks_in_list: Tasks in the current list
        tasks_map: Map of task IDs to tasks
        displayed_task_ids: Set of task IDs that have already been displayed
        orphaned_task_ids: Set of task IDs that are orphaned
        is_last_space: Whether this is in the last space
        is_last_folder: Whether this is in the last folder
        is_last_list: Whether this is the last list
        result_lines: List of strings to append formatted output to
        format_options: FormatOptions instance managing display settings.
    """
    # Check for orphaned tasks (not in hierarchy but in this list)
    # We're skipping adding the orphaned tasks section if hide_orphaned is True
    if not format_options.hide_orphaned:
        orphaned_tasks = [
            task for task in tasks_in_list 
            if task.get('id') not in displayed_task_ids
        ]
        
        # Filter out tasks that have a parent_id set but parent isn't in the tree
        # Only include completely orphaned tasks (no parent at all)
        truly_orphaned_tasks = [
            task for task in orphaned_tasks 
            if not task.get('parent_id')  # No parent ID means truly orphaned
        ]
        
        # Skip adding orphaned section if we only had tasks with invisible parents
        if not truly_orphaned_tasks:
            return
            
        # Create task prefix that accounts for all parent containers
        orphan_prefix = ""
        if is_last_space:
            orphan_prefix += "  "  # Space is last, no pipe
        else:
            orphan_prefix += "│ "  # Space continues, need pipe
            
        if is_last_folder:
            orphan_prefix += "  "  # Folder is last, no pipe
        else:
            orphan_prefix += "│ "  # Folder continues, need pipe
            
        if is_last_list:
            orphan_prefix += "  "  # List is last, no pipe
        else:
            orphan_prefix += "│ "  # List continues, need pipe
        
        # Add orphaned tasks header with proper branch character
        if format_options.colorize_output:
            result_lines.append(f"{orphan_prefix}└─{colorize('📦 Orphaned Tasks:', TextColor.BRIGHT_RED)}")
        else:
            result_lines.append(f"{orphan_prefix}└─📦 Orphaned Tasks:")
        
        # Sort orphaned tasks
        sorted_orphans = sorted(
            truly_orphaned_tasks,
            key=lambda t: (
                str(t.get('status', '')).lower() == 'complete',
                int(t.get('priority', 4)),
                t.get('name', '')
            )
        )
        
        # Create orphaned tasks prefix (one level deeper)
        orphan_items_prefix = orphan_prefix + "  "  # Orphaned header is last, no pipe
        
        # Format each orphaned task
        for orphan_idx, orphan in enumerate(sorted_orphans):
            is_last_orphan = orphan_idx == len(sorted_orphans) - 1
            
            # Format task with all required parameters
            task_line = format_task_basic_info(
                orphan, 
                options=format_options
            )
            branch = "└─" if is_last_orphan else "├─"
            
            # Handle multi-line output from format_task_basic_info
            if "\n" in task_line:
                # Split the description into lines
                desc_lines = task_line.split("\n")
                # First line gets the branch character
                result_lines.append(f"{orphan_items_prefix}{branch}{desc_lines[0]}")
                
                # Additional lines get indentation that accounts for the branch
                for additional_line in desc_lines[1:]:
                    # Use the same prefix as subtasks would use
                    additional_prefix = orphan_items_prefix + ("  " if is_last_orphan else "│ ")
                    result_lines.append(f"{additional_prefix}{additional_line}")
            else:
                # Single line output
                result_lines.append(f"{orphan_items_prefix}{branch}{task_line}")
            
            # Mark as displayed
            displayed_task_ids.add(orphan.get('id'))
            
            # Format subtask hierarchy
            subtask_lines = []
            
            # Recursively display all subtasks of the orphaned task
            _format_subtask_hierarchy(
                orphan,
                tasks_map,
                subtask_lines,
                displayed_task_ids,
                orphan_items_prefix + ("  " if is_last_orphan else "│ "),
                orphaned_task_ids,
                format_options,
                trace=format_options.trace
            )
            
            # Add subtask lines to result
            for line in subtask_lines:
                result_lines.append(line)

def _format_subtask_hierarchy(
    parent_task: Dict[str, Any],
    tasks_map: Dict[str, Dict],
    lines: List[str],
    displayed_task_ids: Set[str],
    current_prefix: str,
    orphaned_task_ids: Set[str],
    format_options: FormatOptions,
    trace: bool = False  # Add trace parameter
) -> None:
    """
    Format a task's subtasks and add them to the lines list with proper indentation.

    Task: tsk_1e88842d - Tree Structure Validation
    dohcount: 3

    Args:
        parent_task: The parent task
        tasks_map: Map of task IDs to tasks
        lines: List to append formatted output lines to
        displayed_task_ids: Set of task IDs that have already been displayed
        current_prefix: Current prefix for indentation
        orphaned_task_ids: Set of orphaned task IDs (used for filtering)
        format_options: FormatOptions instance managing display settings.
        trace: Whether to show detailed stack traces on error
    """
    try:
        if trace:
            # Log key information to aid in debugging
            logger.debug(f"_format_subtask_hierarchy for task {parent_task.get('id')} with format_options.show_ids={format_options.show_ids}")
            
        # Extract necessary options
        include_completed = format_options.include_completed
        hide_orphaned = format_options.hide_orphaned
        show_ids = format_options.show_ids

        # Get all subtasks of this task
        subtasks = _get_subtasks(parent_task, tasks_map, include_completed)
        
        # If no subtasks, return
        if not subtasks:
            return
        
        # Format each subtask
        for idx, subtask in enumerate(subtasks):
            try:
                # Skip if already displayed
                if subtask.get('id') in displayed_task_ids:
                    continue
                
                # Skip if orphaned and hide_orphaned is True
                if hide_orphaned and subtask.get('id') in orphaned_task_ids:
                    continue
                
                # Check if this is the last subtask
                is_last = idx == len(subtasks) - 1
                
                # Format task info using format_options
                if trace:
                    logger.debug(f"Formatting subtask {subtask.get('id')} with show_ids={format_options.show_ids}")
                    
                task_description = format_task_basic_info(
                    subtask,
                    options=format_options
                )
                branch = "└─" if is_last else "├─"
                
                # Handle multi-line output from format_task_basic_info
                if "\n" in task_description:
                    # Split the description into lines
                    desc_lines = task_description.split("\n")
                    # First line gets the branch character
                    lines.append(f"{current_prefix}{branch}{desc_lines[0]}")
                    
                    # Additional lines get indentation that accounts for the branch
                    for additional_line in desc_lines[1:]:
                        # Use the same prefix as child tasks would use
                        additional_prefix = current_prefix + ("  " if is_last else "│ ")
                        lines.append(f"{additional_prefix}{additional_line}")
                else:
                    # Single line output
                    task_line = f"{current_prefix}{branch}{task_description}"
                    lines.append(task_line)
                
                # Mark as displayed
                displayed_task_ids.add(subtask.get('id'))
                
                # Calculate new prefix for child tasks
                new_prefix = current_prefix + ("  " if is_last else "│ ")
                
                # Format subtasks recursively, passing format_options
                _format_subtask_hierarchy(
                    subtask,
                    tasks_map,
                    lines,
                    displayed_task_ids,
                    new_prefix,
                    orphaned_task_ids,
                    format_options,
                    trace=trace  # Pass trace parameter
                )
            except Exception as e:
                error_msg = f"Error formatting subtask {subtask.get('id')}: {e}"
                if trace:
                    error_msg += f"\n{traceback.format_exc()}"
                logger.error(error_msg)
                # Add an error line to the output
                lines.append(f"{current_prefix}⚠️ Error formatting subtask: {e}")
    except Exception as e:
        error_msg = f"Error in _format_subtask_hierarchy for parent {parent_task.get('id')}: {e}"
        if trace:
            error_msg += f"\n{traceback.format_exc()}"
        logger.error(error_msg)
        # Add an error line to the output
        lines.append(f"{current_prefix}⚠️ Error formatting subtask hierarchy: {e}")

def _get_subtasks(
    task: Dict[str, Any], 
    tasks_map: Dict[str, Dict], 
    include_completed: bool = False
) -> List[Dict]:
    """
    Get all subtasks of a task.
    
    Task: tsk_1e88842d - Tree Structure Validation
    dohcount: 2
    
    Args:
        task: The parent task
        tasks_map: Map of task IDs to tasks
        include_completed: Whether to include completed tasks
        
    Returns:
        List of subtask dictionaries
    """
    task_id = task.get('id')
    if not task_id:
        return []
        
    # Find all tasks with this task as parent
    subtasks = []
    for t_id, t in tasks_map.items():
        if t.get('parent_id') == task_id:
            # Skip completed tasks if not including them
            # Ensure status is converted to string before comparison
            if not include_completed and str(t.get('status', '')).lower() == 'complete':
                continue
            subtasks.append(t)
            
    # Sort by status, priority, name
    # Ensure all comparisons use string conversion for status
    return sorted(
        subtasks,
        key=lambda t: (
            str(t.get('status', '')).lower() == 'complete',  # Incomplete first
            int(t.get('priority', 4)),                  # Lower priority first
            t.get('name', '')                           # Alphabetical
        )
    )

def format_container_hierarchy(
    tasks: List[Dict[str, Any]],
    indent: int = 2,
    colorize_output: bool = True,
    show_details: bool = False,
    show_ids: bool = False,
    include_completed: bool = False,
    hide_orphaned: bool = False,
    show_score: bool = False,
    show_tags: bool = False,
    tag_style: str = "colored",
    show_type_emoji: bool = True,
    validate_pipes: bool = True,
    show_descriptions: bool = False,
    description_length: int = 100,
    show_relationships: bool = False,
    show_comments: int = 0,
    show_dates: bool = False,
    options: Optional[FormatOptions] = None,
    trace: bool = False
) -> str:
    """
    Format tasks organized by container hierarchy.
    
    Task: tsk_1e88842d - Tree Structure Validation
    dohcount: 3
    
    Args:
        tasks: List of tasks to format
        indent: Number of spaces to indent for each level of hierarchy
        colorize_output: Whether to use ANSI colors
        show_details: Whether to show detailed information about tasks
        show_ids: Whether to show task IDs
        include_completed: Whether to include completed tasks
        hide_orphaned: Whether to hide orphaned tasks
        show_score: Whether to show task scores
        show_tags: Whether to show task tags
        tag_style: Style for tag display
        show_type_emoji: Whether to show task type emoji
        validate_pipes: Whether to validate and fix tree structure
        show_descriptions: Whether to show task descriptions
        description_length: Maximum length of task descriptions
        show_relationships: Whether to show task relationships
        show_comments: Number of comments to show (0 to hide)
        show_dates: Whether to show task dates
        options: FormatOptions instance (if provided, overrides individual parameters)
        trace: Whether to show detailed stack traces on error
        
    Returns:
        Formatted string representation of tasks in container hierarchy
    """
    try:
        # Use the options object if provided, otherwise use the individual parameters
        if options is None:
            # Create FormatOptions from individual arguments if not provided
            format_options = FormatOptions(
                colorize_output=colorize_output,
                show_ids=show_ids,
                show_score=show_score,
                show_tags=show_tags,
                tag_style=tag_style,
                show_type_emoji=show_type_emoji,
                show_descriptions=show_descriptions,
                show_dates=show_dates,
                show_comments=show_comments,
                show_relationships=show_relationships,
                include_completed=include_completed,
                hide_orphaned=hide_orphaned,
                description_length=description_length
            )
        else:
            # Use the provided options object
            format_options = options
            # Update individual variables from options for local use if needed
            # (or just access format_options.xyz directly)
            colorize_output = format_options.colorize_output
            show_ids = format_options.show_ids
            include_completed = format_options.include_completed
            hide_orphaned = format_options.hide_orphaned
            # ... etc ...

        if trace:
            # Log the format options to aid in debugging
            logger.debug(f"Container hierarchy format options: {format_options.__dict__}")
            
        # Build a mapping of task IDs to tasks
        tasks_map = {task.get('id'): task for task in tasks if 'id' in task}
        
        # Set to track tasks that should be excluded from counts if hiding orphaned
        orphaned_task_ids = set()
        
        # Initialize the set to track displayed task IDs
        displayed_task_ids = set()
        
        # Track tasks that are subtasks of other tasks - we'll exclude these from container displays
        subtask_ids = set()
        for task in tasks:
            parent_id = task.get('parent_id')
            if parent_id and parent_id in tasks_map:
                subtask_ids.add(task.get('id'))
        
        # Identify tasks with no container assignment
        top_level_orphaned_tasks = []
        for task in tasks:
            # Check for direct container fields
            space_id = task.get('space_id', '')
            folder_id = task.get('folder_id', '')
            list_id = task.get('list_id', '')
            # Also check for container_id field which is set by assign command
            container_id = task.get('container_id', '')
            
            if not space_id and not folder_id and not list_id and not container_id:
                top_level_orphaned_tasks.append(task)
        
        # Get container information from task data
        containers = {
            'spaces': {},
            'folders': {},
            'lists': {}
        }
        
        # Track container hierarchy
        container_hierarchy = {
            'space_to_folders': {},  # space_id -> [folder_ids]
            'folder_to_lists': {},   # folder_id -> [list_ids]
            'list_to_tasks': {}      # list_id -> [task_ids]
        }
        
        # Pre-identify orphaned tasks and their subtasks recursively
        if format_options.hide_orphaned: # Use format_options
            # First, build parent-child relationships
            child_to_parent = {}
            for task in tasks:
                parent_id = task.get('parent_id')
                if parent_id:
                    child_to_parent[task.get('id')] = parent_id
            
            # Identify root orphans (tasks with non-existent parents)
            root_orphans = set()
            for task in tasks:
                parent_id = task.get('parent_id')
                if parent_id and parent_id not in tasks_map:
                    root_orphans.add(task.get('id'))
            
            # Function to recursively collect all subtasks of orphaned tasks
            def collect_orphaned_subtasks(task_id):
                orphaned_task_ids.add(task_id)
                for potential_subtask in tasks:
                    if potential_subtask.get('parent_id') == task_id:
                        collect_orphaned_subtasks(potential_subtask.get('id'))
            
            # Collect all orphaned tasks and their subtasks
            for orphan_id in root_orphans:
                collect_orphaned_subtasks(orphan_id)
        
        # First pass: collect container info
        for task in tasks:
            # Skip orphaned tasks when counting if hide_orphaned is True
            if format_options.hide_orphaned and task.get('id') in orphaned_task_ids: # Use format_options
                continue
            
            # Extract container info
            space_id = task.get('space_id', '')
            folder_id = task.get('folder_id', '')
            list_id = task.get('list_id', '')
            container_id = task.get('container_id', '')
            
            # If container_id is set but specific container fields aren't, try to determine container type
            if container_id and not (space_id or folder_id or list_id):
                # Check if container_id matches a list
                for lst in containers.get('lists', {}).values():
                    if lst.get('id') == container_id:
                        list_id = container_id
                        break
                
                # If not a list, check if it's a folder
                if not list_id:
                    for folder in containers.get('folders', {}).values():
                        if folder.get('id') == container_id:
                            folder_id = container_id
                            break
                
                # If not a folder, check if it's a space
                if not folder_id and not list_id:
                    for space in containers.get('spaces', {}).values():
                        if space.get('id') == container_id:
                            space_id = container_id
                            break
            
            # Skip if no container info is found
            if not space_id and not folder_id and not list_id and not container_id:
                continue
            
            # Add space if new
            if space_id and space_id not in containers['spaces']:
                containers['spaces'][space_id] = {
                    'id': space_id,
                    'name': task.get('space_name', f"Space {space_id}"),
                    'task_count': 0,
                    'completed_count': 0
                }
            
            # Add folder if new
            if folder_id and folder_id not in containers['folders']:
                containers['folders'][folder_id] = {
                    'id': folder_id,
                    'name': task.get('folder_name', f"Folder {folder_id}"),
                    'space_id': space_id,
                    'task_count': 0,
                    'completed_count': 0
                }
                
                # Update space-to-folders mapping
                if space_id:
                    if space_id not in container_hierarchy['space_to_folders']:
                        container_hierarchy['space_to_folders'][space_id] = []
                    if folder_id not in container_hierarchy['space_to_folders'][space_id]:
                        container_hierarchy['space_to_folders'][space_id].append(folder_id)
                
            # Add list if new - check for duplicates based on list name within the same folder
            if list_id and list_id not in containers['lists']:
                list_name = task.get('list_name', f"List {list_id}")
                
                # Check if we already have a list with the same name in the same folder
                duplicate_list_id = None
                for existing_id, existing_list in containers['lists'].items():
                    if (existing_list['folder_id'] == folder_id and 
                        existing_list['name'] == list_name):
                        duplicate_list_id = existing_id
                        break
                
                # If we found a duplicate, use that list_id instead of creating a new one
                if duplicate_list_id:
                    list_id = duplicate_list_id
                else:
                    # Add new list
                    containers['lists'][list_id] = {
                        'id': list_id,
                        'name': list_name,
                        'folder_id': folder_id,
                        'space_id': space_id,
                        'task_count': 0,
                        'completed_count': 0
                    }
                    
                    # Update folder-to-lists mapping
                    if folder_id:
                        if folder_id not in container_hierarchy['folder_to_lists']:
                            container_hierarchy['folder_to_lists'][folder_id] = []
                        if list_id not in container_hierarchy['folder_to_lists'][folder_id]:
                            container_hierarchy['folder_to_lists'][folder_id].append(list_id)
            
            # Update list-to-tasks mapping - include all tasks including subtasks
            if list_id:
                if list_id not in container_hierarchy['list_to_tasks']:
                    container_hierarchy['list_to_tasks'][list_id] = []
                if task['id'] not in container_hierarchy['list_to_tasks'][list_id]:
                    container_hierarchy['list_to_tasks'][list_id].append(task['id'])
            
            # Update container counts - only if not filtered by include_completed
            # Add logging before calling .lower()
            logger.debug(f"Task status before lower: {task.get('status', '')} (type: {type(task.get('status', ''))})")

            # Wrap .lower() call in try-except
            try:
                is_completed = str(task.get('status', '')).lower() == 'complete'
            except AttributeError as e:
                logger.error(f"Error converting status to lower for task ID {task.get('id')}: {e}")
                is_completed = False  # Default to not completed on error
                raise
            
            should_count = format_options.include_completed or not is_completed
            
            if should_count:
                if space_id:
                    containers['spaces'][space_id]['task_count'] += 1
                    if is_completed:
                        containers['spaces'][space_id]['completed_count'] += 1
                    
                if folder_id:
                    containers['folders'][folder_id]['task_count'] += 1
                    if is_completed:
                        containers['folders'][folder_id]['completed_count'] += 1
                    
                if list_id:
                    containers['lists'][list_id]['task_count'] += 1
                    if is_completed:
                        containers['lists'][list_id]['completed_count'] += 1
        
        # Second pass: recalculate container counts from child containers
        # Ensure lists have the correct counts
        for list_id, list_item in containers['lists'].items():
            tasks_in_list = container_hierarchy['list_to_tasks'].get(list_id, [])
            # Get all tasks (including subtasks) - remove the subtask_ids filter
            list_tasks = [t for t in tasks_in_list if 
                        (not format_options.hide_orphaned or t not in orphaned_task_ids)]
            
            # Count completed tasks, including subtasks
            completed_count = sum(1 for t in list_tasks if t in tasks_map and 
                                str(tasks_map[t].get('status', '')).lower() == 'complete')
            
            # Update counts - include all tasks, not just top-level ones
            list_item['task_count'] = len(list_tasks)
            list_item['completed_count'] = completed_count
        
        # Recalculate folder counts to include all tasks in their lists
        for folder_id, folder in containers['folders'].items():
            folder_lists = container_hierarchy['folder_to_lists'].get(folder_id, [])
            folder['task_count'] = sum(containers['lists'][l]['task_count'] for l in folder_lists if l in containers['lists'])
            folder['completed_count'] = sum(containers['lists'][l]['completed_count'] for l in folder_lists if l in containers['lists'])
        
        # Recalculate space counts to include all tasks in their folders
        for space_id, space in containers['spaces'].items():
            space_folders = container_hierarchy['space_to_folders'].get(space_id, [])
            space['task_count'] = sum(containers['folders'][f]['task_count'] for f in space_folders if f in containers['folders'])
            space['completed_count'] = sum(containers['folders'][f]['completed_count'] for f in space_folders if f in containers['folders'])
        
        # List to hold the formatted output lines
        result_lines = []
        
        # Helper function to format container with stats
        def format_container(name, container_type, task_count, completed_count, id_str=""):
            stats = f"({completed_count}/{task_count})"
            
            if format_options.colorize_output: # Use format_options
                color = container_color(container_type)
                stats_color = completion_stats_color(completed_count, task_count)
                # Move ID to the end and ensure consistent display
                if id_str and format_options.show_ids: # Use format_options
                    return f"{colorize(name, color)} {colorize(stats, stats_color)} {colorize(id_str, TextColor.BRIGHT_BLACK)}"
                else:
                    return f"{colorize(name, color)} {colorize(stats, stats_color)}"
            else:
                # Move ID to the end and ensure consistent display
                if id_str and format_options.show_ids: # Use format_options
                    return f"{name} {stats} {id_str}"
                else:
                    return f"{name} {stats}"
        
        # Add a header line
        if format_options.colorize_output:
            result_lines.append(colorize("Tasks organized by container:", TextColor.BRIGHT_WHITE))
        else:
            result_lines.append("Tasks organized by container:")
        
        result_lines.append("")  # Empty line for better readability
        
        # Generate container hierarchy display
        for space_idx, (space_id, space) in enumerate(containers['spaces'].items()):
            # Skip if no tasks or filter out completed
            if space['task_count'] == 0 or (not format_options.include_completed and space['completed_count'] == space['task_count']): # Use format_options
                continue
            
            # Track if this is the last space
            is_last_space = space_idx == len(containers['spaces']) - 1
            
            # Format space line using the updated helper
            space_line = format_container(
                space['name'],
                'space',
                space['task_count'],
                space['completed_count'],
                space_id
            )
            
            # Add branch character for top-level items
            if is_last_space and (format_options.hide_orphaned or not top_level_orphaned_tasks): # Use format_options
                result_lines.append(f"└─{space_line}")
            else:
                result_lines.append(f"├─{space_line}")
            
            # Get folders in this space
            space_folders = container_hierarchy['space_to_folders'].get(space_id, [])
            
            # Process each folder
            for folder_idx, folder_id in enumerate(space_folders):
                folder = containers['folders'].get(folder_id)
                if not folder:
                    continue
                
                # Skip if no tasks or filter out completed
                if folder['task_count'] == 0 or (not format_options.include_completed and folder['completed_count'] == folder['task_count']): # Use format_options
                    continue
                
                # Format folder line with proper branch character
                is_last_folder = folder_idx == len(space_folders) - 1
                
                # Create proper folder prefix with pipes
                if is_last_space and (format_options.hide_orphaned or not top_level_orphaned_tasks): # Use format_options
                    folder_prefix = "  "
                else:
                    folder_prefix = "│ "
                
                branch = "└─" if is_last_folder else "├─"
                
                # Format folder line using the updated helper
                folder_line = format_container(
                    folder['name'],
                    'folder',
                    folder['task_count'],
                    folder['completed_count'],
                    folder_id
                )
                result_lines.append(f"{folder_prefix}{branch}{folder_line}")
                
                # Get lists in this folder - ensure unique list IDs
                folder_lists = list(set(container_hierarchy['folder_to_lists'].get(folder_id, [])))
                
                # Process each list - use set to avoid duplicates
                for list_idx, list_id in enumerate(sorted(folder_lists)):
                    list_item = containers['lists'].get(list_id)
                    if not list_item:
                        continue
                    
                    # Skip if no tasks or filter out completed
                    if list_item['task_count'] == 0 or (not format_options.include_completed and list_item['completed_count'] == list_item['task_count']): # Use format_options
                        continue
                    
                    # Format list line with proper branch character
                    is_last_list = list_idx == len(folder_lists) - 1
                    
                    # Calculate list prefix based on container branch status
                    list_prefix = ""
                    if is_last_space and (format_options.hide_orphaned or not top_level_orphaned_tasks): # Use format_options
                        list_prefix += "  "
                    else:
                        list_prefix += "│ "
                    
                    if is_last_folder:
                        list_prefix += "  "
                    else:
                        list_prefix += "│ "
                    
                    branch = "└─" if is_last_list else "├─"
                    
                    # Format list line using the updated helper
                    list_line = format_container(
                        list_item['name'],
                        'list',
                        list_item['task_count'],
                        list_item['completed_count'],
                        list_id
                    )
                    result_lines.append(f"{list_prefix}{branch}{list_line}")
                    
                    # Get tasks in this list - ensure unique task IDs
                    list_tasks_ids = list(set(container_hierarchy['list_to_tasks'].get(list_id, [])))
                    
                    # Collect and sort tasks
                    tasks_in_list = []
                    for task_id in list_tasks_ids:
                        # Skip orphaned tasks if hide_orphaned is True
                        if format_options.hide_orphaned and task_id in orphaned_task_ids: # Use format_options
                            continue
                        if task_id in tasks_map:
                            tasks_in_list.append(tasks_map[task_id])
                    
                    # Skip lists with no displayable tasks
                    if not tasks_in_list:
                        continue
                    
                    # Calculate task prefix based on container branch status
                    task_prefix = ""
                    if is_last_space and (format_options.hide_orphaned or not top_level_orphaned_tasks): # Use format_options
                        task_prefix += "  "
                    else:
                        task_prefix += "│ "
                    
                    if is_last_folder:
                        task_prefix += "  "
                    else:
                        task_prefix += "│ "
                    
                    if is_last_list:
                        task_prefix += "  "
                    else:
                        task_prefix += "│ "
                    
                    # Track which tasks have been displayed IN THIS LIST CONTEXT
                    list_displayed_task_ids = set() # Use a local set for this list
                    
                    # Format and add tasks using the helper function, passing format_options
                    _format_container_tasks(
                        tasks_in_list,
                        tasks_map,
                        list_displayed_task_ids, # Pass local set
                        task_prefix,
                        orphaned_task_ids, # Pass global orphan set for filtering
                        is_last_space,
                        is_last_folder,
                        is_last_list,
                        result_lines,
                        format_options=format_options, # Pass the options object
                        trace=trace  # Pass trace parameter
                    )
                    
                    # Keep track of globally displayed tasks
                    displayed_task_ids.update(list_displayed_task_ids)
        
        # Add top-level orphaned tasks section (tasks with no container)
        if top_level_orphaned_tasks and not format_options.hide_orphaned: # Use format_options
            # Filter to only include tasks with no parent (truly orphaned)
            # Also filter based on include_completed status
            truly_orphaned_root_tasks = [
                task for task in top_level_orphaned_tasks
                if not task.get('parent_id') and # Truly orphaned root
                   (format_options.include_completed or str(task.get('status', '')).lower() != 'complete') # Use format_options
            ]

            # Skip if there are no truly orphaned tasks to display
            if not truly_orphaned_root_tasks:
                pass # Continue to summary and validation
            else:
                # Add a separator line if we have container tasks
                if containers['spaces']:
                    result_lines.append("")

                # Format the orphaned tasks header
                if format_options.colorize_output: # Use format_options
                    orphaned_header = colorize("📦 NO CONTAINER TASKS", TextColor.BRIGHT_YELLOW, style=TextStyle.BOLD)
                else:
                    orphaned_header = "📦 NO CONTAINER TASKS"

                # Use appropriate branch for the header
                # If no spaces were displayed, this is the only top-level item
                is_only_item = not any("├─" in line or "└─" in line for line in result_lines)
                header_branch = "└─" if is_only_item else "├─" # Or should it always be last? Let's assume last.
                result_lines.append(f"└─{orphaned_header}")

                # Sort orphaned root tasks
                sorted_orphans = sorted(
                    truly_orphaned_root_tasks,
                    key=lambda t: (
                        str(t.get('status', '')).lower() == 'complete',  # Incomplete first
                        int(t.get('priority', 4)),                 # Lower priority first
                        t.get('name', '')                          # Alphabetical
                    )
                )

                # Set to track displayed tasks in this section
                top_orphan_displayed = set() # This seems redundant if we use the main displayed_task_ids

                # Format each top-level orphaned task
                branch_prefix = "   "  # Indentation under the orphaned header
                for i, orphan in enumerate(sorted_orphans):
                     is_last = i == len(sorted_orphans) - 1

                     # Format task info using format_options
                     task_description = format_task_basic_info(
                         orphan,
                         options=format_options # Pass options object
                     )
                     branch = "└─" if is_last else "├─"

                     # Handle multi-line orphaned task descriptions
                     if "\n" in task_description:
                         desc_lines = task_description.split("\n")
                         result_lines.append(f"{branch_prefix}{branch}{desc_lines[0]}")
                         orphan_sub_prefix = branch_prefix + ("  " if is_last else "│ ")
                         for line in desc_lines[1:]:
                             result_lines.append(f"{orphan_sub_prefix}{line}")
                     else:
                         result_lines.append(f"{branch_prefix}{branch}{task_description}")

                     # Mark as displayed (already done globally? Check _format_container_tasks)
                     # Let's assume it needs to be added to the global set here too.
                     displayed_task_ids.add(orphan.get('id'))

                     # Calculate prefix for subtasks
                     subtask_prefix = branch_prefix + ("  " if is_last else "│ ")

                     # Format subtasks using _format_subtask_hierarchy
                     temp_subtask_lines = []
                     _format_subtask_hierarchy(
                         orphan, # Pass the parent orphan task
                         tasks_map,
                         temp_subtask_lines, # Use a temporary list
                         displayed_task_ids, # Use global displayed set
                         subtask_prefix, # Pass correct prefix
                         orphaned_task_ids, # Pass global orphan set for filtering
                         format_options, # Pass options object
                         trace=trace  # Pass trace parameter
                     )
                     result_lines.extend(temp_subtask_lines) # Add formatted subtask lines

        # Add a summary line with total task count
        result_lines.append("")

        # Count tasks based on filters applied (include_completed, hide_orphaned)
        displayable_tasks = []
        for task in tasks:
            task_id = task.get('id')
            if format_options.hide_orphaned and task_id in orphaned_task_ids: # Use format_options
                continue
            if not format_options.include_completed and str(task.get('status', '')).lower() == 'complete': # Use format_options
                continue
            displayable_tasks.append(task)

        total_displayable_tasks = len(displayable_tasks)
        # Ensure status is converted to string before comparison
        completed_displayable_tasks = sum(1 for task in displayable_tasks if str(task.get('status', '')).lower() == 'complete')

        # Count unique task IDs that were displayed
        unique_task_ids = displayed_task_ids.copy()
        total_task_ids = len(unique_task_ids)
        
        # Count duplicates by comparing the number of task IDs to the number of tasks
        # that should have been displayed
        duplicate_count = 0
        if total_displayable_tasks > total_task_ids:
            duplicate_count = total_displayable_tasks - total_task_ids
        
        # Count container IDs (lists, folders, spaces)
        list_ids = list(containers['lists'].keys())
        folder_ids = list(containers['folders'].keys())
        space_ids = list(containers['spaces'].keys())
        total_container_ids = len(list_ids) + len(folder_ids) + len(space_ids)

        # Format summary line
        if format_options.colorize_output: # Use format_options
            completion_color = completion_stats_color(completed_displayable_tasks, total_displayable_tasks)
            summary = f"Total Displayed: {colorize(f'{completed_displayable_tasks}/{total_displayable_tasks} tasks complete', completion_color)}"
            summary += f"\nTask IDs: {total_task_ids}, Container IDs: {total_container_ids}, Duplicates: {duplicate_count}"
        else:
            summary = f"Total Displayed: {completed_displayable_tasks}/{total_displayable_tasks} tasks complete"
            summary += f"\nTask IDs: {total_task_ids}, Container IDs: {total_container_ids}, Duplicates: {duplicate_count}"

        result_lines.append(summary)

        # Validate tree structure
        if validate_pipes:
            valid, errors = validate_tree_structure(result_lines)
            if not valid:
                logging.warning("Tree structure validation failed:")
                for error in errors:
                    logging.warning(error)

                # Apply auto-correction
                result_lines = fix_tree_structure(result_lines)

        # Add debugging info for specific issues
        if trace and show_ids:
            logger.debug(f"Show IDs is enabled, format_options.show_ids={format_options.show_ids}")
            
        return "\n".join(result_lines)
    except Exception as e:
        error_msg = f"Error in format_container_hierarchy: {e}"
        if trace:
            error_msg += f"\n{traceback.format_exc()}"
        logger.error(error_msg)
        return f"Error formatting task container hierarchy: {e}" 