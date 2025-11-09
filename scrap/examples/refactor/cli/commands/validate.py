#!/usr/bin/env python3
"""
Task: tsk_7c921d5e - Implement Structure Validation
Document: refactor/cli/commands/validate.py
dohcount: 2

Related Tasks:
    - tsk_40d54e79 - Fix Unit Test Failures (parent)
    - tsk_1ad30b7b - Fix Cross-Platform Compatibility Issues (related)

Used By:
    - CLI: Provides the 'validate' command for checking task structure integrity
    - TaskManager: Uses validation functions to ensure data consistency

Purpose:
    Validates the task structure in a ClickUp JSON template, checking for common
    issues like circular references, duplicate tasks, inconsistent statuses, and
    deleted task references.

Requirements:
    - Must detect circular references in subtask relationships
    - Must identify tasks appearing in multiple containers
    - Must detect inconsistent status values
    - Must identify deleted tasks still referenced in lists/subtasks
    - CRITICAL: Must not modify the JSON file, only report issues

Parameters:
    json_file (str): Path to the JSON template file to validate
    fix (bool): Whether to automatically fix issues (optional)

Returns:
    (bool): True if validation passed, False if issues were found

Raises:
    FileNotFoundError: When specified JSON file doesn't exist
    ValidationError: When validation encounters a critical error

Changes:
    - v1: Initial implementation with basic structure validation
    - v2: Fixed import path for logger module

Lessons Learned:
    - Circular references can cause infinite loops in tree displays
    - Status inconsistencies lead to confusing task views
    - Duplicate task references cause multiple listing issues
"""

import sys
import json
import argparse
from typing import Dict, List, Set, Tuple, Any, Optional

from ...core.task_manager import TaskManager
from refactor.common.logging import get_logger

logger = get_logger(__name__)

def build_task_index(data: Dict) -> Dict[str, Dict]:
    """
    Build a lookup index of all tasks by their ID.
    
    Args:
        data (Dict): The JSON data containing tasks
        
    Returns:
        Dict[str, Dict]: A dictionary mapping task IDs to task objects
    """
    task_index = {}
    
    for task in data.get('tasks', []):
        task_id = task.get('id')
        if task_id:
            task_index[task_id] = task
    
    return task_index

def find_container_references(data: Dict) -> Dict[str, List[Tuple[str, str]]]:
    """
    Find all places where tasks are referenced in containers.
    
    Args:
        data (Dict): The JSON data containing lists, folders, and spaces
        
    Returns:
        Dict[str, List[Tuple[str, str]]]: A dictionary mapping task IDs to lists of container references
    """
    container_refs = {}
    
    # Check lists
    for lst in data.get('lists', []):
        list_id = lst.get('id')
        for task_id in lst.get('tasks', []):
            if task_id not in container_refs:
                container_refs[task_id] = []
            container_refs[task_id].append(('list', list_id))
    
    # Check folders
    for folder in data.get('folders', []):
        folder_id = folder.get('id')
        for task_id in folder.get('tasks', []):
            if task_id not in container_refs:
                container_refs[task_id] = []
            container_refs[task_id].append(('folder', folder_id))
    
    # Check spaces
    for space in data.get('spaces', []):
        space_id = space.get('id')
        for task_id in space.get('tasks', []):
            if task_id not in container_refs:
                container_refs[task_id] = []
            container_refs[task_id].append(('space', space_id))
    
    return container_refs

def detect_circular_references(data: Dict, task_index: Dict) -> List[Tuple[str, str, List[str]]]:
    """
    Detect circular references in the subtask hierarchy.
    
    Args:
        data (Dict): The JSON data containing tasks
        task_index (Dict): Task index mapping task IDs to task objects
        
    Returns:
        List[Tuple[str, str, List[str]]]: A list of circular references, each containing 
            parent ID, subtask ID, and the chain of references forming the circle
    """
    circular_refs = []
    
    for task in data.get('tasks', []):
        task_id = task.get('id')
        
        # Skip if no subtasks
        if 'subtasks' not in task or not task['subtasks']:
            continue
        
        for subtask_id in task['subtasks']:
            # Skip self-references (immediate circular)
            if subtask_id == task_id:
                circular_refs.append((task_id, subtask_id, [task_id, subtask_id]))
                continue
            
            # Check for indirect circular references (A -> B -> C -> A)
            chain = find_circular_chain(task_id, subtask_id, task_index)
            if chain:
                circular_refs.append((task_id, subtask_id, chain))
    
    return circular_refs

def find_circular_chain(start_id: str, current_id: str, task_index: Dict, visited: Optional[Set[str]] = None) -> List[str]:
    """
    Find a chain of references that forms a circle starting from start_id.
    
    Args:
        start_id (str): The starting task ID
        current_id (str): The current task ID in the traversal
        task_index (Dict): Task index mapping task IDs to task objects
        visited (Set[str], optional): Set of already visited task IDs
        
    Returns:
        List[str]: The chain of task IDs forming a circle, or empty list if no circle is found
    """
    if visited is None:
        visited = set()
    
    # If we've seen this task before, skip it to avoid infinite loops
    if current_id in visited:
        return []
    
    # Add current task to visited set
    visited.add(current_id)
    
    # Get current task
    current_task = task_index.get(current_id)
    if not current_task:
        return []
    
    # Check if any of current task's subtasks is the start_id (circle found)
    subtasks = current_task.get('subtasks', [])
    if start_id in subtasks:
        return [current_id, start_id]
    
    # Recursive check for each subtask
    for subtask_id in subtasks:
        chain = find_circular_chain(start_id, subtask_id, task_index, visited.copy())
        if chain:
            return [current_id] + chain
    
    # No circle found
    return []

def detect_duplicate_tasks(data: Dict) -> Dict[str, List[Tuple[str, str]]]:
    """
    Detect tasks that appear in multiple containers.
    
    Args:
        data (Dict): The JSON data containing lists, folders, and spaces
        
    Returns:
        Dict[str, List[Tuple[str, str]]]: A dictionary mapping task IDs to lists of container references
    """
    container_refs = find_container_references(data)
    
    # Filter to only tasks that appear in multiple containers
    duplicate_tasks = {task_id: refs for task_id, refs in container_refs.items() if len(refs) > 1}
    
    return duplicate_tasks

def detect_missing_tasks(data: Dict, task_index: Dict) -> Dict[str, List[Tuple[str, str]]]:
    """
    Detect references to tasks that don't exist or are deleted.
    
    Args:
        data (Dict): The JSON data containing lists, folders, spaces, and tasks
        task_index (Dict): Task index mapping task IDs to task objects
        
    Returns:
        Dict[str, List[Tuple[str, str]]]: A dictionary mapping task IDs to lists of references
    """
    missing_tasks = {}
    
    # Check lists
    for lst in data.get('lists', []):
        list_id = lst.get('id')
        for task_id in lst.get('tasks', []):
            if task_id not in task_index:
                if task_id not in missing_tasks:
                    missing_tasks[task_id] = []
                missing_tasks[task_id].append(('list', list_id))
            elif task_index[task_id].get('status') == 'deleted':
                if task_id not in missing_tasks:
                    missing_tasks[task_id] = []
                missing_tasks[task_id].append(('list-deleted', list_id))
    
    # Check folders
    for folder in data.get('folders', []):
        folder_id = folder.get('id')
        for task_id in folder.get('tasks', []):
            if task_id not in task_index:
                if task_id not in missing_tasks:
                    missing_tasks[task_id] = []
                missing_tasks[task_id].append(('folder', folder_id))
            elif task_index[task_id].get('status') == 'deleted':
                if task_id not in missing_tasks:
                    missing_tasks[task_id] = []
                missing_tasks[task_id].append(('folder-deleted', folder_id))
    
    # Check subtasks
    for task in data.get('tasks', []):
        task_id = task.get('id')
        for subtask_id in task.get('subtasks', []):
            if subtask_id not in task_index:
                if subtask_id not in missing_tasks:
                    missing_tasks[subtask_id] = []
                missing_tasks[subtask_id].append(('subtask', task_id))
            elif task_index[subtask_id].get('status') == 'deleted':
                if subtask_id not in missing_tasks:
                    missing_tasks[subtask_id] = []
                missing_tasks[subtask_id].append(('subtask-deleted', task_id))
    
    return missing_tasks

def detect_inconsistent_statuses(data: Dict) -> List[Tuple[str, str, str]]:
    """
    Detect tasks with status indicators in names that don't match their actual status.
    
    Args:
        data (Dict): The JSON data containing tasks
        
    Returns:
        List[Tuple[str, str, str]]: A list of tuples containing task ID, task name, and actual status
    """
    inconsistent_statuses = []
    
    status_indicators = [
        ('[to do]', 'to do'),
        ('[in progress]', 'in progress'),
        ('[complete]', 'complete'),
        ('[done]', 'complete'),
        ('[deleted]', 'deleted'),
        ('[in review]', 'in review')
    ]
    
    for task in data.get('tasks', []):
        task_id = task.get('id')
        task_name = task.get('name', '')
        task_status = task.get('status', '')
        
        for indicator, expected_status in status_indicators:
            if indicator in task_name and task_status != expected_status:
                inconsistent_statuses.append((task_id, task_name, task_status))
                break
    
    return inconsistent_statuses

def detect_parent_relationship_issues(data: Dict, task_index: Dict) -> List[Dict]:
    """
    Detect issues with parent-child relationships.
    
    Args:
        data (Dict): The JSON data containing tasks
        task_index (Dict): Task index mapping task IDs to task objects
        
    Returns:
        List[Dict]: A list of issues found
    """
    issues = []
    
    for task in data.get('tasks', []):
        task_id = task.get('id')
        parent_id = task.get('parent_id')
        
        # Skip if no parent
        if not parent_id:
            continue
        
        # Skip if this task is deleted - it's expected to be removed from parent's subtasks
        if task.get('status') == 'deleted':
            continue
        
        # Check if parent exists
        if parent_id not in task_index:
            issues.append({
                'type': 'missing_parent',
                'task_id': task_id,
                'parent_id': parent_id,
                'task_name': task.get('name', '')
            })
            continue
        
        # Check if parent is deleted
        if task_index[parent_id].get('status') == 'deleted':
            issues.append({
                'type': 'deleted_parent',
                'task_id': task_id,
                'parent_id': parent_id,
                'task_name': task.get('name', ''),
                'parent_name': task_index[parent_id].get('name', '')
            })
            continue
        
        # Check if this task is in parent's subtasks
        parent_task = task_index[parent_id]
        if 'subtasks' not in parent_task or task_id not in parent_task['subtasks']:
            issues.append({
                'type': 'missing_subtask_reference',
                'task_id': task_id,
                'parent_id': parent_id,
                'task_name': task.get('name', ''),
                'parent_name': parent_task.get('name', '')
            })
    
    return issues

def validate_task_structure(data: Dict) -> Dict[str, Any]:
    """
    Validate the task structure and return a report of issues found.
    
    Args:
        data (Dict): The JSON data to validate
        
    Returns:
        Dict[str, Any]: A report of validation results
    """
    validation_report = {
        'circular_references': [],
        'duplicate_tasks': {},
        'missing_tasks': {},
        'inconsistent_statuses': [],
        'parent_relationship_issues': []
    }
    
    # Build task index
    task_index = build_task_index(data)
    logger.info(f"Built index of {len(task_index)} tasks")
    
    # Detect circular references
    circular_refs = detect_circular_references(data, task_index)
    validation_report['circular_references'] = circular_refs
    
    # Detect duplicate tasks
    duplicate_tasks = detect_duplicate_tasks(data)
    validation_report['duplicate_tasks'] = duplicate_tasks
    
    # Detect missing tasks
    missing_tasks = detect_missing_tasks(data, task_index)
    validation_report['missing_tasks'] = missing_tasks
    
    # Detect inconsistent statuses
    inconsistent_statuses = detect_inconsistent_statuses(data)
    validation_report['inconsistent_statuses'] = inconsistent_statuses
    
    # Detect parent relationship issues
    parent_issues = detect_parent_relationship_issues(data, task_index)
    validation_report['parent_relationship_issues'] = parent_issues
    
    # Calculate overall validity
    validation_report['valid'] = (
        len(circular_refs) == 0 and
        len(duplicate_tasks) == 0 and
        len([k for k, v in missing_tasks.items() if not any('deleted' in t[0] for t in v)]) == 0 and
        len(inconsistent_statuses) == 0 and
        len(parent_issues) == 0
    )
    
    return validation_report

def print_validation_report(report: Dict[str, Any]) -> None:
    """
    Print a human-readable validation report.
    
    Args:
        report (Dict[str, Any]): The validation report to print
    """
    print("\n═══════════════════════════════════════════════")
    print("          TASK STRUCTURE VALIDATION REPORT            ")
    print("═══════════════════════════════════════════════\n")
    
    # Print summary
    is_valid = report.get('valid', False)
    print(f"Overall Validity: {'✅ VALID' if is_valid else '❌ INVALID'}\n")
    
    # Print circular references
    circular_refs = report.get('circular_references', [])
    print(f"Circular References: {len(circular_refs)}")
    if circular_refs:
        for i, (parent_id, subtask_id, chain) in enumerate(circular_refs, 1):
            chain_str = " -> ".join(chain)
            print(f"  {i}. Circular reference: {chain_str}")
    print()
    
    # Print duplicate tasks
    duplicate_tasks = report.get('duplicate_tasks', {})
    print(f"Duplicate Task References: {len(duplicate_tasks)}")
    if duplicate_tasks:
        for i, (task_id, refs) in enumerate(duplicate_tasks.items(), 1):
            refs_str = ", ".join([f"{container_type}:{container_id}" for container_type, container_id in refs])
            print(f"  {i}. Task {task_id} appears in multiple containers: {refs_str}")
    print()
    
    # Print missing tasks
    missing_tasks = report.get('missing_tasks', {})
    non_deleted_missing = {k: v for k, v in missing_tasks.items() if not all('deleted' in t[0] for t in v)}
    deleted_references = {k: v for k, v in missing_tasks.items() if any('deleted' in t[0] for t in v)}
    
    print(f"Missing Task References: {len(non_deleted_missing)}")
    if non_deleted_missing:
        for i, (task_id, refs) in enumerate(non_deleted_missing.items(), 1):
            refs_str = ", ".join([f"{container_type}:{container_id}" for container_type, container_id in refs])
            print(f"  {i}. Non-existent task {task_id} referenced in: {refs_str}")
    print()
    
    print(f"Deleted Task References: {len(deleted_references)}")
    if deleted_references:
        for i, (task_id, refs) in enumerate(deleted_references.items(), 1):
            refs_str = ", ".join([f"{container_type}:{container_id}" for container_type, container_id in refs 
                                 if 'deleted' in container_type])
            print(f"  {i}. Deleted task {task_id} referenced in: {refs_str}")
    print()
    
    # Print inconsistent statuses
    inconsistent_statuses = report.get('inconsistent_statuses', [])
    print(f"Inconsistent Status Indicators: {len(inconsistent_statuses)}")
    if inconsistent_statuses:
        for i, (task_id, task_name, task_status) in enumerate(inconsistent_statuses, 1):
            print(f"  {i}. Task {task_id} name suggests different status than actual '{task_status}': {task_name}")
    print()
    
    # Print parent relationship issues
    parent_issues = report.get('parent_relationship_issues', [])
    print(f"Parent Relationship Issues: {len(parent_issues)}")
    if parent_issues:
        for i, issue in enumerate(parent_issues, 1):
            issue_type = issue.get('type', '')
            if issue_type == 'missing_parent':
                print(f"  {i}. Task {issue.get('task_id')} references non-existent parent {issue.get('parent_id')}")
            elif issue_type == 'deleted_parent':
                print(f"  {i}. Task {issue.get('task_id')} references deleted parent {issue.get('parent_id')}")
            elif issue_type == 'missing_subtask_reference':
                print(f"  {i}. Task {issue.get('task_id')} is not in parent {issue.get('parent_id')}'s subtasks")
    print()
    
    # Print recommendation
    if not is_valid:
        print("\nRecommendation:")
        print("  Run the fix_task_structure.py script to automatically fix these issues:")
        print("  $ python3 fix_task_structure.py <json_file>")
    print("\n═══════════════════════════════════════════════\n")

def validate_command(args):
    """Execute the validate command."""
    logger.info(f"Validating task structure in {args.template_file}")
    
    # Load the data
    try:
        with open(args.template_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON file: {e}")
        sys.exit(1)
    
    # Validate the task structure
    validation_report = validate_task_structure(data)
    
    # Print the validation report
    print_validation_report(validation_report)
    
    # Output report to file if requested
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(validation_report, f, indent=2)
            logger.info(f"Validation report saved to {args.output}")
        except Exception as e:
            logger.error(f"Error saving validation report: {e}")
    
    # Exit with error code if validation failed
    if not validation_report.get('valid', False):
        if args.fix:
            logger.error("Automatic fixing not implemented yet. Please run fix_task_structure.py script.")
            logger.error("Example: python3 fix_task_structure.py " + args.template_file)
        sys.exit(1)
    
    return True

# Add a command class for the validate command

class ValidateCommand:
    """Command class for validating task structure."""
    
    def __init__(self, core_manager):
        """Initialize with core manager."""
        self.core_manager = core_manager
        self.name = "validate"
        self.description = "Validate task structure in a JSON template file"
    
    def get_aliases(self):
        """Get command aliases."""
        return []
    
    def configure_parser(self, parser):
        """Configure the argument parser for this command."""
        parser.add_argument('template_file', help='JSON template file to validate')
        parser.add_argument('--fix', action='store_true', help='Automatically fix issues (not implemented yet)')
        parser.add_argument('--output', '-o', help='Output file for validation report (JSON format)')
        parser.set_defaults(func=self.execute)
    
    def execute(self, args):
        """Execute the validate command."""
        return validate_command(args)

# Keep the original setup_args function for backwards compatibility
def setup_args(subparsers):
    """Set up the argument parser for the validate command."""
    parser = subparsers.add_parser('validate', help='Validate task structure in a JSON template file')
    parser.add_argument('template_file', help='JSON template file to validate')
    parser.add_argument('--fix', action='store_true', help='Automatically fix issues (not implemented yet)')
    parser.add_argument('--output', '-o', help='Output file for validation report (JSON format)')
    parser.set_defaults(func=validate_command) 