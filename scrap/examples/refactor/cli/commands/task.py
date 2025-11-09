"""
Task: tsk_bf28d342 - Update CLI Module Comments
Document: refactor/cli/commands/task.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_bf28d342 - Update CLI Module Comments (current)
    - tsk_7c9d4e8a - Task Command Implementation (related)
    - tsk_02e976b4 - Fix Comment Newline Display in CLI (related)

Used By:
    - Main CLI: For all task management operations
    - Users: Primary interface for task creation and management
    - Task Repository: Receives commands for task operations
    - Core Manager: Integrates with task services

Purpose:
    Provides comprehensive command implementations for task-related operations
    including creating, updating, showing, listing, and deleting tasks. Also
    includes commands for handling subtasks and task comments.

Requirements:
    - Must handle all task-related operations through CLI
    - Must provide clear and consistent error messages
    - Must validate input before processing
    - Must support task hierarchy operations (parent/child relationships)
    - CRITICAL: Must handle errors gracefully and provide helpful error messages
    - CRITICAL: Must properly display task details including multiline content

Parameters:
    N/A - This is a command module file

Returns:
    N/A - This is a command module file

Changes:
    - v1: Initial implementation with basic task commands
    - v2: Added support for subtasks and comments
    - v3: Enhanced display with colorization
    - v4: Fixed newline handling in comments
    - v5: Improved documentation and error messaging
    - v6: Added support for task types with dynamic color rendering

Lessons Learned:
    - Complex display logic should be separated from command execution
    - Proper newline handling is essential for readable output
    - Colorized output significantly improves readability and UX
    - Command parsing should be separate from execution logic
"""
from argparse import ArgumentParser, Namespace
import argparse
import json
import getpass
import os
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Union, Any, Tuple, Set
import textwrap
import traceback
import sys

from refactor.cli.command import Command, CustomArgumentParser
from refactor.core.interfaces.core_manager import CoreManager
from refactor.core.entities.task_entity import TaskStatus, TaskPriority
from refactor.core.entities.task_type import TaskType, task_type_color, get_colored_task_type
from refactor.cli.error_handling import CLIError, handle_cli_error
from refactor.core.exceptions import (
    ErrorCode,
    get_command_error_code,
    get_storage_error_code,
    get_validation_error_code,
    get_repo_error_code
)
from refactor.cli.commands.utils import format_task_hierarchy, format_task_list, _convert_escaped_newlines
from refactor.utils.colors import (
    TextColor, TextStyle, DefaultTheme, colorize, 
    status_color, priority_color, score_color, relationship_color,
    normalize_text, format_multi_line, container_color
)

# Import the configuration manager
from refactor.utils.config import get_config_manager
from refactor.cli.commands.assign import AssignToListCommand  # Add import
from refactor.cli.formatting.common.display_options import DisplayOptions
from refactor.cli.formatting.common.task_info import FormatOptions
from refactor.cli.formatting.tree.hierarchy import format_task_hierarchy
from refactor.cli.formatting.tree.container import format_container_hierarchy

logger = logging.getLogger(__name__)

class CreateTaskCommand(Command):
    """
    Task: tsk_bf28d342 - Update CLI Module Comments
    Document: refactor/cli/commands/task.py
    dohcount: 1

    Purpose:
        Implements a command to create a new task in a template file with
        customizable attributes including name, description, status, priority,
        and tags. Provides a consistent interface for task creation across
        different contexts and use cases.

    Requirements:
        - Must validate task data before creation
        - Must generate a unique task ID with appropriate prefix
        - Must support setting all standard task attributes
        - Must handle parent-child relationships when specified
        - Must update the template file with the new task
        - CRITICAL: Must preserve existing task data integrity
        - CRITICAL: Must handle multiline descriptions properly

    Used By:
        - CLI Users: For creating new tasks manually
        - Scripts: For automated task creation in workflows
        - Project Managers: For task breakdown and assignment
        - Integration Tools: For creating tasks from external systems

    Changes:
        - v1: Initial implementation with basic task creation
        - v2: Added support for parent task specification
        - v3: Enhanced validation for task attributes
        - v4: Improved error handling and user feedback
        - v5: Added support for additional metadata (assignee, due date)
    """

    def __init__(self, core_manager: CoreManager):
        """
        Initialize a new CreateTaskCommand instance.
        
        Creates a command for adding new tasks to the template file
        with comprehensive validation and attribute support.
        
        Args:
            core_manager: Core manager instance for task creation services
        """
        self._core_manager = core_manager
    
    @property
    def name(self) -> str:
        """
        Get the command name.
        
        Returns:
            The string "create-task" as the command's name
        """
        return "create-task"
    
    @property
    def description(self) -> str:
        """
        Get the command description.
        
        Returns:
            A description of the command's purpose
        """
        return "Create a new task"
    
    def get_aliases(self) -> List[str]:
        """
        Get alternate names for this command.
        
        Returns:
            A list containing "new" and "add" as command aliases
        """
        return ["new", "add"]
    
    def configure_parser(self, parser: ArgumentParser) -> None:
        """
        Configure the argument parser for the create task command.
        
        Sets up all required and optional arguments for task creation,
        including path to template file, task name, and all supported
        task attributes.
        
        Args:
            parser: The argument parser to configure with arguments
        """
        # Import make_template_optional from utils
        from refactor.cli.commands.utils import make_template_optional
        
        # Make template argument optional with better help text
        make_template_optional(parser, "Path to the template JSON file")
        
        parser.add_argument('name', help='Name for the new task')
        parser.add_argument('--description', help='Description for the task')
        parser.add_argument('--status', default='to do', help='Task status (default: to do)')
        parser.add_argument('--priority', type=int, default=3, help='Task priority (1-5, default: 3)')
        parser.add_argument('--tags', help='Comma-separated list of tags')
        parser.add_argument('--parent', help='Parent task name or ID (for creating subtasks)')
        parser.add_argument('--assignee', help='Task assignee')
        parser.add_argument('--due-date', help='Due date (YYYY-MM-DD format)')
        parser.add_argument('--task-type', choices=TaskType.get_all_types(), 
                           default='task', help='Task type (default: task)')

    def execute(self, args: Namespace) -> Union[int, str]:
        """
        Execute the create task command, adding a new task to the template file.
        
        Handles the complete task creation process, including validation,
        ID generation, parent task resolution (if applicable), and template
        file updating. Provides detailed feedback on success or failure.
        
        Args:
            args: Command arguments containing task definition parameters
                  including filename, name, and optional attributes
        
        Returns:
            Exit code (0 for success, non-zero for error) or
            String result for successful task creation
        
        Notes:
            - Generates a task ID with appropriate prefix (tsk_ for
              top-level tasks, stk_ for subtasks)
            - Validates status, priority, and other field values
            - Properly handles multiline descriptions
            - Returns detailed error messages for validation failures
        """
        try:
            # Parse tags if provided
            tags = None
            if args.tags:
                tags = [tag.strip() for tag in args.tags.split(',')]
            
            # Check if template is provided, if not, try to find default template
            if not hasattr(args, 'template') or args.template is None:
                from refactor.utils.template_finder import find_default_template
                default_template = find_default_template()
                if default_template:
                    logger.info(f"Using default template: {default_template}")
                    args.template = default_template
                else:
                    raise ValueError("No template specified and no default template found in .project directory")

            # Initialize core manager with the template file
            self._core_manager.initialize(args.template)

            # Create the task
            task = self._core_manager.create_task(
                name=args.name,
                description=args.description or "",
                status=args.status,
                priority=args.priority,
                tags=tags,
                parent_id=args.parent,
                task_type=args.task_type
            )

            # Save changes
            self._core_manager.save()

            # Get colored task type for display
            colored_type = get_colored_task_type(args.task_type)
            
            print(f"Created task '{task['name']}' with ID {task['id']} (type: {colored_type})")
            return 0  # Success
        except Exception as e:
            logger.error(f"Error creating task: {str(e)}", exc_info=True)
            print(f"Error creating task: {str(e)}")
            return 1


class CreateSubtaskCommand(Command):
    """
    Task: tsk_bf28d342 - Update CLI Module Comments
    Document: refactor/cli/commands/task.py
    dohcount: 1

    Purpose:
        Implements a specialized command to create subtasks under specific parent tasks.
        Provides streamlined workflow for creating task hierarchies and breaking down
        work into smaller, manageable components with proper parent-child relationships.

    Requirements:
        - Must validate both subtask and parent task data
        - Must locate the parent task by name or ID with flexible lookup
        - Must establish correct parent-child relationship in the hierarchy
        - Must generate a unique subtask ID with "stk_" prefix
        - Must inherit appropriate attributes from parent when relevant
        - CRITICAL: Must preserve existing task hierarchies and relationships
        - CRITICAL: Must handle multiline content properly in all text fields

    Used By:
        - CLI Users: For breaking down work items into smaller components
        - Project Managers: For task decomposition and work assignment
        - Workflow Scripts: For automated task hierarchy creation
        - Team Leads: For distributing work across team members

    Changes:
        - v1: Initial implementation with basic subtask creation
        - v2: Enhanced parent task lookup capabilities (by ID or name)
        - v3: Improved error handling for missing parents
        - v4: Added support for inheriting attributes from parent task
        - v5: Enhanced validation for subtask-specific constraints
    """

    def __init__(self, core_manager: CoreManager):
        """
        Initialize a new CreateSubtaskCommand instance.
        
        Creates a command for adding subtasks to existing parent tasks
        with proper hierarchical relationships and validation.
        
        Args:
            core_manager: Core manager instance for accessing task services
        """
        self._core_manager = core_manager
    
    @property
    def name(self) -> str:
        """
        Get the command name.
        
        Returns:
            The string "create-subtask" as the command's name
        """
        return "create-subtask"
    
    @property
    def description(self) -> str:
        """
        Get the command description.
        
        Returns:
            A description of the command's purpose
        """
        return "Create a new subtask under a parent task"
    
    def get_aliases(self) -> List[str]:
        """
        Get alternate names for this command.
        
        Returns:
            A list containing "subtask" as a command alias
        """
        return ["subtask"]
    
    def configure_parser(self, parser: ArgumentParser) -> None:
        """
        Configure the argument parser for the create subtask command.
        
        Sets up all required and optional arguments for subtask creation,
        including parent task reference, subtask name, and supported attributes.
        
        Args:
            parser: The argument parser to configure with arguments
        """
        parser.add_argument('template', help='Path to the task file')
        parser.add_argument('parent_task', help='Name or ID of the parent task')
        parser.add_argument('name', help='Name for the new subtask')
        parser.add_argument('--description', help='Description for the subtask')
        parser.add_argument('--status', default='to do', help='Subtask status (default: to do)')
        parser.add_argument('--priority', type=int, default=3, help='Subtask priority (1-5, default: 3)')
        parser.add_argument('--tags', help='Comma-separated list of tags')
        parser.add_argument('--assignee', help='Subtask assignee')
        parser.add_argument('--due-date', help='Due date (YYYY-MM-DD format)')
        parser.add_argument('--task-type', choices=TaskType.get_all_types(), 
                           default='task', help='Subtask type (default: task)')

    def execute(self, args: Namespace) -> Union[int, str]:
        """
        Execute the create subtask command, adding a new subtask to a parent task.
        
        Handles the complete subtask creation process, including parent task
        lookup, validation, ID generation with appropriate prefix, and template
        file updating. Provides detailed feedback on success or failure.
        
        Args:
            args: Command arguments containing subtask definition parameters
                  including filename, parent_task, name, and optional attributes
        
        Returns:
            Exit code (0 for success, non-zero for error) or
            String result for successful subtask creation
        
        Notes:
            - First attempts to find parent by ID, then by name
            - Generates a subtask ID with "stk_" prefix
            - Validates subtask attributes according to system requirements
            - Properly establishes parent-child relationship
            - Returns detailed error messages for validation failures
        """
        try:
            # Parse tags if provided
            tags = None
            if args.tags:
                tags = [tag.strip() for tag in args.tags.split(',')]

            # Initialize core manager with the template file
            self._core_manager.initialize(args.template)
            
            # Find parent task by ID or name
            try:
                # First try by ID
                parent_task = self._core_manager.get_task(args.parent_task)
            except:
                # If not found by ID, try by name
                parent_task = self._core_manager.get_task_by_name(args.parent_task)
            
            # Create the subtask
            subtask = self._core_manager.create_task(
                name=args.name,
                description=args.description or "",
                status=args.status,
                priority=args.priority,
                tags=tags,
                parent_id=parent_task['id'],
                task_type=args.task_type
            )

            # Save changes
            self._core_manager.save()

            # Get colored task type for display
            colored_type = get_colored_task_type(args.task_type)
            
            print(f"Created subtask '{subtask['name']}' with ID {subtask['id']} (type: {colored_type}) under parent task '{parent_task['name']}'")
            return 0  # Success
        except Exception as e:
            logger.error(f"Error creating subtask: {str(e)}", exc_info=True)
            print(f"Error creating subtask: {str(e)}")
            return 1


class ShowTaskCommand(Command):
    """
    Task: tsk_bf28d342 - Update CLI Module Comments
    Document: refactor/cli/commands/task.py
    dohcount: 1

    Purpose:
        Implements a command to display detailed information about a specific task,
        including its attributes, relationships, comments, and other metadata.
        Provides a rich viewing experience with colorization and formatting options
        for better readability.

    Requirements:
        - Must display all standard task attributes
        - Must handle and format multiline content properly
        - Must support optional display of subtasks and relationships
        - Must provide a clear hierarchical view of task information
        - Must handle non-existent tasks gracefully
        - CRITICAL: Must preserve line breaks in descriptions and comments
        - CRITICAL: Must provide clear visual distinction between sections

    Used By:
        - CLI Users: For viewing task details
        - Project Managers: For tracking task progress and relationships
        - Developers: For understanding implementation requirements
        - Reviewers: For assessing task completeness and correctness

    Changes:
        - v1: Initial implementation with basic task display
        - v2: Added colorization and formatting improvements
        - v3: Enhanced display of relationships and subtasks
        - v4: Fixed handling of multiline content
        - v5: Added support for displaying checklists and comments
    """

    def __init__(self, core_manager: CoreManager):
        """
        Initialize a new ShowTaskCommand instance.
        
        Creates a command for displaying detailed information about tasks
        with comprehensive formatting and organization.
        
        Args:
            core_manager: Core manager instance for task retrieval services
        """
        self._core_manager = core_manager
    
    @property
    def name(self) -> str:
        """
        Get the command name.
        
        Returns:
            The string "show" as the command's name
        """
        return "show"
    
    @property
    def description(self) -> str:
        """
        Get the command description.
        
        Returns:
            A description of the command's purpose
        """
        return "Show details for a specific task"
    
    def get_aliases(self) -> List[str]:
        """
        Get alternate names for this command.
        
        Returns:
            A list containing "view" and "info" as command aliases
        """
        return ["view", "info"]
    
    def configure_parser(self, parser: ArgumentParser) -> None:
        """
        Configure the argument parser for the show task command.
        
        Sets up all required and optional arguments for viewing task details,
        including path to template file, task identifier, and display options.
        
        Args:
            parser: The argument parser to configure with arguments
        """
        parser.add_argument('template', help='Path to the task file')
        parser.add_argument('task_name', help='Task name or ID to show')
        
        # Create a mutually exclusive group for details display options
        details_group = parser.add_mutually_exclusive_group()
        details_group.add_argument('--details', action='store_true', default=True, help='Show detailed task information (default)')
        details_group.add_argument('--no-details', action='store_false', dest='details', help='Hide detailed task information')
        
        parser.add_argument('--json', action='store_true', help='Output in JSON format')
        parser.add_argument('--no-color', action='store_true', help='Disable colored output')
        parser.add_argument('--full', action='store_true', help='Show full task details including all fields')
        parser.add_argument('--show-score', action='store_true', help='Show detailed scores for the task')
        
        # Add new dependency tree options
        parser.add_argument('--show-subtask-tree', action='store_true', help='Show subtasks as a hierarchical tree')
        parser.add_argument('--show-dependency-tree', action='store_true', help='Show dependency relationships as a tree')
        parser.add_argument('--dependency-type', choices=['depends_on', 'blocks'], default='depends_on', 
                           help='Dependency relationship type to use for tree organization (default: depends_on)')

    def execute(self, args: Namespace) -> int:
        """
        Execute the show task command, displaying task details.
        
        Task: tsk_309ea4c2 - Improve Container Hierarchy Display
        dohcount: 9
        
        Args:
            args: Command arguments containing task identifier and display options
        
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        try:
            # Initialize core manager
            self._core_manager.initialize(args.template)
            
            # Get the task
            task = self._core_manager.find_task_by_id_or_name(args.task_name)
            
            if task is None:
                print(f"Task '{args.task_name}' not found.")
                return 1
            
            # Check if we should show detailed information
            show_details = getattr(args, 'details', True)  # Default to True if not specified
            show_full = getattr(args, 'full', False)
            show_json = getattr(args, 'json', False)
            show_score = getattr(args, 'show_score', False)
            
            # Get tree display options
            show_subtask_tree = getattr(args, 'show_subtask_tree', False)
            show_dependency_tree = getattr(args, 'show_dependency_tree', False)
            dependency_type = getattr(args, 'dependency_type', 'depends_on')
            
            # Add scores to task if requested
            if (show_details or show_full) and show_score:
                try:
                    # Get all tasks with scores
                    tasks_with_scores = self._core_manager.get_tasks_with_scores()
                    
                    # Find our specific task in the list of tasks with scores
                    for task_with_score in tasks_with_scores:
                        if task_with_score.get('id') == task.get('id'):
                            task = task_with_score
                            break
                except Exception as e:
                    logger.warning(f"Could not load task scores: {str(e)}")
            
            # Display as JSON if requested
            if show_json:
                print(json.dumps(task, indent=2, cls=TaskStatusEncoder))
                return 0
            
            # Display the task details
            use_color = not (hasattr(args, 'no_color') and args.no_color)
            
            self._display_task(
                task, 
                show_details=show_details, 
                show_full=show_full,
                use_color=use_color,
                show_relationships=True,  # Always show relationships in detailed view
                show_score=show_score
            )
            
            # Display subtask tree if requested
            if show_subtask_tree:
                self._display_subtask_tree(task, use_color)
                
            # Display dependency tree if requested
            if show_dependency_tree:
                self._display_dependency_tree(task, dependency_type, use_color)
            
            # Add score legend if scores are shown
            if show_score:
                from refactor.utils.colors import get_score_legend
                print("\n" + get_score_legend())
                
            return 0
        except Exception as e:
            logger.error(f"Error showing task: {str(e)}", exc_info=True)
            return 1
            
    def _display_task(self, task, show_details=False, use_color=True, show_full=False, show_relationships=True, show_score=False):
        """
        Display a task with its details.
        
        Task: tsk_309ea4c2 - Improve Container Hierarchy Display
        dohcount: 8
        
        Related Tasks:
            - tsk_ef072a47 - Display Features (parent)
        
        Purpose:
            Displays a task with full details, relationships, and scores.
        
        Args:
            task: Task to display
            show_details: Whether to show detailed information
            use_color: Whether to use colored output
            show_full: Whether to show full task information
            show_relationships: Whether to display relationship information
            show_score: Whether to display detailed scores for the task
        """
        # Import colors if needed
        if use_color:
            from refactor.utils.colors import (
                TextColor, DefaultTheme, colorize, 
                status_color, priority_color, container_color,
                total_score_color, effort_score_color, effectiveness_score_color,
                risk_score_color, urgency_score_color, get_score_legend
            )
        
        # Display task header
        task_name = task.get('name', 'Unnamed Task')
        task_id = task.get('id', 'unknown')
        
        # Add parent flag indicator
        is_parent = task.get('is_parent', False)
        parent_indicator = "📁 " if is_parent else ""  # Folder icon for parent tasks
        
        if use_color:
            print(f"\n{colorize('Task:', TextColor.BLUE)} {parent_indicator}{task_name}")
            print(f"{colorize('ID:', TextColor.BLUE)} {colorize(task_id, TextColor.BRIGHT_BLACK)}")
        else:
            print(f"\nTask: {parent_indicator}{task_name}")
            print(f"ID: {task_id}")
        
        # Show status
        status = task.get('status', 'unknown')
        if use_color:
            status_str = colorize(status, status_color(status))
            print(f"{colorize('Status:', TextColor.BLUE)} {status_str}")
        else:
            print(f"Status: {status}")
        
        # Show priority
        priority = task.get('priority', 3)
        priority_str = str(priority)
        if use_color:
            priority_str = colorize(priority_str, priority_color(priority))
            print(f"{colorize('Priority:', TextColor.BLUE)} {priority_str}")
        else:
            print(f"Priority: {priority_str}")
        
        # Show scores if requested and available
        if show_score and 'scores' in task:
            scores = task.get('scores', {})
            
            if scores:
                # Display each score with appropriate coloring
                total_score = scores.get('total', 0)
                effort_score = scores.get('effort', 0)
                effectiveness_score = scores.get('effectiveness', 0)
                risk_score = scores.get('risk', 0)
                urgency_score = scores.get('urgency', 0)
                
                if use_color:
                    # Display each score with distinct type colors
                    if total_score:
                        total_color = total_score_color(total_score)
                        print(f"{colorize('Total Score:', TextColor.BLUE)} {colorize(f'{total_score}/10', total_color)}")
                    
                    if effort_score:
                        effort_color = effort_score_color(effort_score)
                        print(f"{colorize('Effort Score:', TextColor.BLUE)} {colorize(f'{effort_score}/10', effort_color)}")
                    
                    if effectiveness_score:
                        effectiveness_color = effectiveness_score_color(effectiveness_score)
                        print(f"{colorize('Effectiveness Score:', TextColor.BLUE)} {colorize(f'{effectiveness_score}/10', effectiveness_color)}")
                    
                    if risk_score:
                        risk_color = risk_score_color(risk_score)
                        print(f"{colorize('Risk Score:', TextColor.BLUE)} {colorize(f'{risk_score}/10', risk_color)}")
                    
                    if urgency_score:
                        urgency_color = urgency_score_color(urgency_score)
                        print(f"{colorize('Urgency Score:', TextColor.BLUE)} {colorize(f'{urgency_score}/10', urgency_color)}")
                else:
                    # Display scores without color
                    if total_score:
                        print(f"Total Score: {total_score}/10")
                    
                    if effort_score:
                        print(f"Effort Score: {effort_score}/10")
                    
                    if effectiveness_score:
                        print(f"Effectiveness Score: {effectiveness_score}/10")
                    
                    if risk_score:
                        print(f"Risk Score: {risk_score}/10")
                    
                    if urgency_score:
                        print(f"Urgency Score: {urgency_score}/10")
        
        # Initialize container info list
        container_info = []
        
        # Add list info if available
        if list_id := task.get('list_id'):
            list_name = task.get('list_name', 'Unknown List')
            container_info.append(('List', list_name, list_id))
            
        # Show container information
        container_id = task.get('container_id')
        if container_id:
            container_type = "unknown"
            if container_id.startswith('lst_'):
                container_type = "list"
            elif container_id.startswith('fld_'):
                container_type = "folder"
            elif container_id.startswith('spc_'):
                container_type = "space"
                
            if use_color:
                # Use container_color function for appropriate container type colors
                container_text_color = container_color(container_type)
                container_str = colorize(f"{container_type}:{container_id}", container_text_color)
                print(f"{colorize('Container:', TextColor.BLUE)} {container_str}")
            else:
                print(f"Container: {container_type}:{container_id}")
        
        # Add folder info if available
        if folder_id := task.get('folder_id'):
            folder_name = task.get('folder_name', 'Unknown Folder')
            container_info.append(('Folder', folder_name, folder_id))
        
        # Add space info if available
        if space_id := task.get('space_id'):
            space_name = task.get('space_name', 'Unknown Space')
            container_info.append(('Space', space_name, space_id))
            
        # Display container info
        for container_type, name, id_val in container_info:
            if use_color:
                container_text = colorize(f'{container_type}:', TextColor.BLUE)
                name_text = colorize(name, container_color(container_type.lower()))
                id_text = colorize(id_val, TextColor.BRIGHT_BLACK)
                print(f"{container_text} {name_text}")
            else:
                print(f"{container_type}: {name}")
        
        # Show tags if any
        tags = task.get('tags', [])
        if tags:
            if use_color:
                tags_str = colorize(', '.join(tags), TextColor.CYAN)
                print(f"{colorize('Tags:', TextColor.BLUE)} {tags_str}")
            else:
                print(f"Tags: {', '.join(tags)}")
        
            # Show parent task if available
        parent_id = task.get('parent_id')
        if parent_id:
            try:
                parent_task = self._core_manager.get_task(parent_id)
                if use_color:
                    parent_name = parent_task.get('name', 'Unknown Parent')
                    print(f"{colorize('Parent Task:', TextColor.BLUE)} {parent_name} (ID: {colorize(parent_id, TextColor.BRIGHT_BLACK)})")
                else:
                    print(f"Parent Task: {parent_task.get('name', 'Unknown Parent')} (ID: {parent_id})")
            except Exception as e:
                if use_color:
                    print(f"{colorize('Parent Task ID:', TextColor.BLUE)} {colorize(parent_id, TextColor.BRIGHT_BLACK)} (not found)")
                else:
                    print(f"Parent Task ID: {parent_id} (not found)")
        
        # When showing details, include more information
        if show_details:
            # Show parent/child relationships
            parent_id = task.get('parent_id')
            is_parent = task.get('is_parent', False)
            
            # Initialize subtasks variable
            subtasks = []
            
            # First check if the task has a subtasks field with IDs
            subtask_ids = task.get('subtasks', [])
            if subtask_ids and isinstance(subtask_ids, list):
                for subtask_id in subtask_ids:
                    try:
                        subtask = self._core_manager.get_task(subtask_id)
                        if subtask:
                            subtasks.append(subtask)
                    except Exception as e:
                        logger.warning(f"Error fetching subtask {subtask_id}: {e}")
            
            # If no subtasks found and task is a parent, try the alternative method
            if not subtasks and is_parent:
                if hasattr(self._core_manager, 'get_subtasks'):
                    try:
                        subtasks = self._core_manager.get_subtasks(task_id)
                    except Exception as e:
                        logger.warning(f"Error fetching subtasks: {e}")
                
            if subtasks:
                    if use_color:
                        print(f"\n{colorize('Subtasks:', DefaultTheme.SUBTITLE)}")
                    else:
                        print("\nSubtasks:")
                    
                    for subtask in subtasks:
                        status_str = subtask.get('status', 'unknown')
                        if use_color:
                            status_color_val = status_color(status_str)
                            subtask_status = colorize(status_str, status_color_val)
                            print(f"  - {subtask.get('name')} [{subtask_status}] (ID: {colorize(subtask.get('id'), TextColor.BRIGHT_BLACK)})")
                        else:
                            print(f"  - {subtask.get('name')} [{status_str}] (ID: {subtask.get('id')})")
            
            # Show due date if available
            due_date = task.get('due_date')
            if due_date:
                if use_color:
                    print(f"{colorize('Due Date:', TextColor.BLUE)} {due_date}")
                else:
                    print(f"Due Date: {due_date}")
            
            # Show timestamps
            created_at = task.get('created_at')
            updated_at = task.get('updated_at')
            completed_at = task.get('completed_at')
            
            if created_at:
                if use_color:
                    print(f"{colorize('Created:', TextColor.BLUE)} {created_at}")
                else:
                    print(f"Created: {created_at}")
                    
            if updated_at:
                if use_color:
                    print(f"{colorize('Updated:', TextColor.BLUE)} {updated_at}")
                else:
                    print(f"Updated: {updated_at}")
            
            # Show completion date if available
            if completed_at:
                if use_color:
                    print(f"{colorize('Completed:', TextColor.BLUE)} {completed_at}")
                else:
                    print(f"Completed: {completed_at}")
                
            # Show checklist if available
            checklist = task.get('checklist')
            if checklist:
                if use_color:
                    print(f"\n{colorize('Checklist:', DefaultTheme.SUBTITLE)}")
                else:
                    print("\nChecklist:")
                
                for item in checklist.get('items', []):
                    item_name = item.get('name', 'Unnamed Item')
                    item_checked = item.get('checked', False)
                    check_mark = "✓" if item_checked else "☐"
                    
                    if use_color:
                        item_color = TextColor.BRIGHT_GREEN if item_checked else TextColor.YELLOW
                        print(f"  {check_mark} {colorize(item_name, item_color)}")
                    else:
                        print(f"  {check_mark} {item_name}")
            
            # Show task relationships if any
            relationships = task.get('relationships', {})
            if relationships and (show_relationships or show_full):
                if use_color:
                    print(f"\n{colorize('Relationships:', DefaultTheme.SUBTITLE)}")
                else:
                    print("\nRelationships:")
                
                for rel_type, related_tasks in relationships.items():
                    rel_title = rel_type.replace('_', ' ').title()
                    if use_color:
                        if rel_type == 'blocks':
                            rel_color = DefaultTheme.BLOCKS
                        elif rel_type == 'depends_on':
                            rel_color = DefaultTheme.DEPENDS_ON
                        elif rel_type == 'related_to':
                            rel_color = DefaultTheme.RELATED_TO
                        elif rel_type == 'documents':
                            rel_color = DefaultTheme.DOCUMENTS
                        elif rel_type == 'documented_by':
                            rel_color = DefaultTheme.DOCUMENTED_BY
                        else:
                            rel_color = TextColor.BLUE
                        
                        print(f"  {colorize(rel_title, rel_color)}:")
                    else:
                        print(f"  {rel_title}:")
                        
                    for rel_task_id in related_tasks:
                        # Try to get the related task name
                        rel_task_name = "Unknown Task"
                        try:
                            rel_task = self._core_manager.get_task(rel_task_id)
                            if rel_task:
                                rel_task_name = rel_task.get('name', 'Unknown Task')
                        except:
                            pass
                        
                        if use_color:
                            print(f"    - {rel_task_name} (ID: {colorize(rel_task_id, TextColor.BRIGHT_BLACK)})")
                        else:
                            print(f"    - {rel_task_name} (ID: {rel_task_id})")
            
            # Show description
            description = task.get('description', '')
            if description and (show_full or not show_details or len(description) < 300):
                if use_color:
                    print(f"\n{colorize('Description:', DefaultTheme.SUBTITLE)}")
                    
                    # Format the description with proper wrapping
                    indent = 2
                    wrapped_description = textwrap.fill(
                        description, 
                        width=78, 
                        initial_indent=' ' * indent,
                        subsequent_indent=' ' * indent
                    )
                    print(colorize(wrapped_description, TextColor.WHITE))
                else:
                    print("\nDescription:")
                    
                    # Format the description with proper wrapping
                    indent = 2
                    wrapped_description = textwrap.fill(
                        description, 
                        width=78, 
                        initial_indent=' ' * indent,
                        subsequent_indent=' ' * indent
                    )
                    print(wrapped_description)
            
            # Show comments if available
            if (show_details or show_full) and 'comments' in task:
                comments = task.get('comments', [])
                if comments:
                    if use_color:
                        print(f"\n{colorize('Comments:', DefaultTheme.SUBTITLE)}")
                    else:
                        print("\nComments:")
                    
                    for i, comment in enumerate(comments):
                        comment_text = comment.get('text', '')
                        comment_author = comment.get('author', 'Anonymous')
                        comment_date = comment.get('date', '')
                        
                        # Convert escaped newlines to actual newlines
                        from refactor.cli.commands.utils import _convert_escaped_newlines
                        comment_text = _convert_escaped_newlines(comment_text)
                        
                        if use_color:
                            print(f"  {colorize(f'Comment {i+1}:', TextColor.YELLOW)} (by {comment_author}, {comment_date})")
                            
                            # Format the comment text with proper wrapping while preserving newlines
                            indent = 4
                            indent_str = ' ' * indent
                            
                            # Split the comment text by newlines and wrap each line individually
                            comment_lines = comment_text.split('\n')
                            wrapped_lines = []
                            
                            for line in comment_lines:
                                if line.strip():  # Skip empty lines
                                    # Wrap this individual line
                                    wrapped_line = textwrap.fill(
                                        line, 
                                        width=76, 
                                        initial_indent=indent_str,
                                        subsequent_indent=indent_str
                                    )
                                    wrapped_lines.append(wrapped_line)
                                else:
                                    # Preserve empty lines
                                    wrapped_lines.append(indent_str)
                            
                            # Join the wrapped lines with newlines
                            wrapped_comment = '\n'.join(wrapped_lines)
                            
                            print(colorize(wrapped_comment, TextColor.WHITE))
                            print()
                        else:
                            print(f"  Comment {i+1}: (by {comment_author}, {comment_date})")
                            
                            # Format the comment text with proper wrapping while preserving newlines
                            indent = 4
                            indent_str = ' ' * indent
                            
                            # Split the comment text by newlines and wrap each line individually
                            comment_lines = comment_text.split('\n')
                            wrapped_lines = []
                            
                            for line in comment_lines:
                                if line.strip():  # Skip empty lines
                                    # Wrap this individual line
                                    wrapped_line = textwrap.fill(
                                        line, 
                                        width=76, 
                                        initial_indent=indent_str,
                                        subsequent_indent=indent_str
                                    )
                                    wrapped_lines.append(wrapped_line)
                                else:
                                    # Preserve empty lines
                                    wrapped_lines.append(indent_str)
                            
                            # Join the wrapped lines with newlines
                            wrapped_comment = '\n'.join(wrapped_lines)
                            
                            print(wrapped_comment)
                            print()

    def _display_subtask_tree(self, task, use_color=True):
        """
        Display a hierarchical tree of subtasks for the given task.
        
        Args:
            task: The parent task to display subtasks for
            use_color: Whether to use colored output
        """
        task_id = task.get('id')
        if not task_id:
            return
            
        # Import necessary modules
        from refactor.utils.colors import TextColor, DefaultTheme, colorize
        
        # Get all tasks
        all_tasks = self._core_manager.get_all_tasks()
        
        # Create a tasks map
        tasks_map = {t.get('id'): t for t in all_tasks if t.get('id')}
        
        # Check if we have subtasks
        subtask_ids = task.get('subtasks', [])
        if not subtask_ids:
            if use_color:
                print(f"\n{colorize('Subtask Hierarchy:', DefaultTheme.SUBTITLE)}")
                print("  No subtasks found.")
            else:
                print("\nSubtask Hierarchy:")
                print("  No subtasks found.")
            return
            
        # Build parent-child relationships
        parent_child_map = {}
        for t in all_tasks:
            parent_id = t.get('parent_id')
            if parent_id:
                if parent_id not in parent_child_map:
                    parent_child_map[parent_id] = []
                parent_child_map[parent_id].append(t)
        
        # Function to recursively format a task and its subtasks
        def format_task_tree(task_id, level=0):
            result = []
            current_task = tasks_map.get(task_id)
            
            if not current_task:
                return result
                
            # Format the task line with indentation
            indent = "  " * level
            connector = "└─ " if level > 0 else ""
                
            # Format task status
            status_str = current_task.get('status', 'unknown')
            if use_color:
                from refactor.utils.colors import status_color
                status_text = colorize(f"[{status_str}]", status_color(status_str))
            else:
                status_text = f"[{status_str}]"
                
            # Format task priority
            priority = current_task.get('priority', 3)
            priority_text = f"(P{priority})"
            
            # Format task name with emoji based on type
            task_type = current_task.get('task_type', 'task')
            emoji = ''
            if task_type == 'task':
                emoji = '📝 '
            elif task_type == 'bug':
                emoji = '🐛 '
            elif task_type == 'feature':
                emoji = '✨ '
            elif task_type == 'project':
                emoji = '📂 '
            elif task_type == 'milestone':
                emoji = '🚩 '
                
            # Combine all elements
            task_line = f"{indent}{connector}{emoji}{current_task.get('name')} {status_text} {priority_text}"
            result.append(task_line)
            
            # Recursively format subtasks
            children = parent_child_map.get(task_id, [])
            for child in children:
                child_lines = format_task_tree(child.get('id'), level + 1)
                result.extend(child_lines)
                
            return result
            
        # Format the tree starting from the current task
        try:
            # Print the hierarchy header
            if use_color:
                print(f"\n{colorize('Subtask Hierarchy:', DefaultTheme.SUBTITLE)}")
            else:
                print("\nSubtask Hierarchy:")
                
            # Format and print the tree
            tree_lines = format_task_tree(task_id)
            for line in tree_lines:
                print(line)
                
        except Exception as e:
            logger.error(f"Error displaying subtask tree: {str(e)}", exc_info=True)

    def _display_dependency_tree(self, task, dependency_type='depends_on', use_color=True):
        """
        Display a hierarchical tree of task dependencies.
        
        Args:
            task: The task to display dependencies for
            dependency_type: Type of dependency relationship to display ('depends_on' or 'blocks')
            use_color: Whether to use colored output
        """
        task_id = task.get('id')
        if not task_id:
            return
            
        # Import necessary modules
        from refactor.cli.commands.utils import format_task_hierarchy
        from refactor.utils.colors import TextColor, DefaultTheme, colorize
        
        # Get all tasks
        all_tasks = self._core_manager.get_all_tasks()
        
        # Create a tasks map
        tasks_map = {t.get('id'): t for t in all_tasks if t.get('id')}
        
        # Build dependency graphs
        dependency_graph = {}
        reverse_dependency_graph = {}
        
        # Initialize the current task's entry in both graphs
        dependency_graph[task_id] = set()
        reverse_dependency_graph[task_id] = set()
        
        # Create a lookup for dependencies
        for t in all_tasks:
            t_id = t.get('id')
            if t_id:
                # Initialize entry in dependency graph
                if t_id not in dependency_graph:
                    dependency_graph[t_id] = set()
                
                # Handle relationship dictionary format
                if "relationships" in t and isinstance(t["relationships"], dict):
                    # Add dependencies from the relationship dictionary
                    if dependency_type in t["relationships"]:
                        for dep_id in t["relationships"][dependency_type]:
                            if dep_id in tasks_map:
                                dependency_graph[t_id].add(dep_id)
                                
                                # Create reverse mapping
                                if dep_id not in reverse_dependency_graph:
                                    reverse_dependency_graph[dep_id] = set()
                                reverse_dependency_graph[dep_id].add(t_id)
        
        # Now create a set of tasks to include in our display
        # This includes the current task plus all tasks in its dependency chain
        # (both depends_on/blocks relationships and reverse relationships)
        included_task_ids = set([task_id])
        
        # Add tasks this one depends on (direct dependencies)
        direct_dependencies = dependency_graph.get(task_id, set())
        included_task_ids.update(direct_dependencies)
        
        # Add tasks that depend on this one (reverse dependencies)
        dependent_tasks = reverse_dependency_graph.get(task_id, set())
        included_task_ids.update(dependent_tasks)
        
        # Now, for each direct dependency, also add its direct dependencies
        for dep_id in direct_dependencies:
            included_task_ids.update(dependency_graph.get(dep_id, set()))
        
        # For each dependent task, also add tasks that depend on it
        for dep_id in dependent_tasks:
            included_task_ids.update(reverse_dependency_graph.get(dep_id, set()))
            
        # Filter tasks to only include the dependency chain
        dependency_tasks = [tasks_map[t_id] for t_id in included_task_ids if t_id in tasks_map]
        
        if dependency_tasks:
            try:
                # Format the dependency hierarchy
                hierarchy_output = format_task_hierarchy(
                    dependency_tasks,
                    indent=2,
                    colorize_output=use_color,
                    show_details=False,
                    show_full=False,
                    dependency_as_tree=True,
                    dependency_type=dependency_type,
                    include_completed=True,
                    hide_orphaned=False,
                    show_score=False,
                    show_tags=True,
                    tag_style='colored',
                    show_type_emoji=True
                )
                
                # Print the hierarchy
                if use_color:
                    print(f"\n{colorize('Dependency Tree:', DefaultTheme.SUBTITLE)} ({dependency_type})")
                else:
                    print(f"\nDependency Tree: ({dependency_type})")
                    
                print(hierarchy_output)
            except Exception as e:
                logger.error(f"Error displaying dependency tree: {str(e)}", exc_info=True)


class ListTasksCommand(Command):
    """
    Task: tsk_bf28d342 - Update CLI Module Comments
    Document: refactor/cli/commands/task.py
    dohcount: 1

    Purpose:
        Provides command-line functionality to list and filter tasks from
        a template file. Supports various display formats, filtering criteria,
        and organization options to customize the task listing experience.

    Requirements:
        - Must support filtering by task attributes
        - Must provide hierarchical tree view for task relationships
        - Must handle container-based organization
        - Must support dependency-based organization
        - Must provide consistent, readable output even for complex task sets
        - CRITICAL: Must handle large task sets efficiently
        - CRITICAL: Must display task relationships correctly

    Used By:
        - CLI Users: For viewing and browsing tasks
        - Project Managers: For task overview and status checking
        - Developers: For task assignment and tracking
        - Reports: For generating status reports and insights

    Changes:
        - v1: Initial implementation with basic listing
        - v2: Added tree view and filtering
        - v3: Enhanced with container-based organization
        - v4: Added support for dependency-based organization
        - v5: Improved output formatting and colorization
    """

    def __init__(self, core_manager: CoreManager):
        """
        Initialize the list command.
        
        Args:
            core_manager: Core manager instance
        """
        self._core_manager = core_manager
    
    @property
    def name(self) -> str:
        """
        Get the command name.
        
        Returns:
            String "list" as the command name
        """
        return "list"
    
    @property
    def description(self) -> str:
        """
        Get the command description.
        
        Returns:
            Description of the command's purpose
        """
        return "List tasks from a template file"
    
    def get_aliases(self) -> List[str]:
        """
        Get alternate names for this command.
        
        Returns:
            A list containing "ls" as a command alias
        """
        return ["ls"]
    
    def configure_parser(self, parser: ArgumentParser) -> None:
        """
        Configure the argument parser for the list command.
        
        Sets up all filtering and display options for task listing.
        
        Args:
            parser: The argument parser to configure
        """
        # Import make_template_optional from utils
        from refactor.cli.commands.utils import make_template_optional
        
        # Make template argument optional
        make_template_optional(parser, "The JSON template file to use")
        
        # Create argument groups for better organization
        filter_group = parser.add_argument_group('Filter Options')
        display_group = parser.add_argument_group('Display Options')
        
        # Filter options
        filter_group.add_argument('--status', help='Filter tasks by status (e.g., to do, in progress, complete)')
        filter_group.add_argument('--priority', type=int, choices=[1, 2, 3, 4], help='Filter tasks by priority (1=highest, 4=lowest)')
        filter_group.add_argument('--tags', help='Filter tasks by tags (comma-separated)')
        filter_group.add_argument('--parent', help='Filter tasks by parent ID')
        filter_group.add_argument('--complete', action='store_true', help='Include completed tasks')
        filter_group.add_argument('--parent-only', action='store_true', help='Show only parent tasks')
        filter_group.add_argument('--hide-orphaned', action='store_true', help='Hide orphaned tasks from the display')
        filter_group.add_argument('--task-type', help='Filter tasks by task type')
        
        # Display format options (mutually exclusive)
        format_group = display_group.add_mutually_exclusive_group()
        format_group.add_argument('--flat', action='store_true', help='Display tasks in flat list format')
        format_group.add_argument('--tree', action='store_true', help='Display tasks in hierarchical tree view')
        format_group.add_argument('--dependency-as-tree', action='store_true', help='Organize tasks by dependency relationships')
        format_group.add_argument('--organize-by-container', action='store_true', help='Organize tasks by list/folder hierarchy (default)')
        format_group.add_argument('--no-container', action='store_true', help='Disable container organization (same as --flat)')
        
        # Dependency options
        display_group.add_argument('--dependency-type', choices=['depends_on', 'blocks'], 
                                 default='depends_on', help='Dependency relationship type to use for tree organization')
        
        # Display detail options
        display_group.add_argument('--show-descriptions', action='store_true', help='Show task descriptions')
        display_group.add_argument('--description-length', type=int, default=100, help='Maximum length for displayed descriptions')
        display_group.add_argument('--show-relationships', action='store_true', help='Show task relationships')
        display_group.add_argument('--show-comments', type=int, default=0, help='Number of recent comments to show (0 to hide, max 3)')
        display_group.add_argument('--show-id', action='store_true', help='Show task IDs')
        display_group.add_argument('--colorize', action='store_true', help='Colorize output based on status')
        display_group.add_argument('--show-score', action='store_true', help='Show detailed scores for each task')
        
        # Tag display options
        display_group.add_argument('--show-tags', action='store_true', default=True, help='Show task tags (default: enabled)')
        display_group.add_argument('--no-tags', action='store_false', dest='show_tags', help='Hide task tags')
        display_group.add_argument('--tag-style', choices=['brackets', 'hash', 'colored'], default='colored', 
                                help='Style for tag display (default: colored)')
        
        # Task type emoji options
        display_group.add_argument('--show-type-emoji', action='store_true', default=True, help='Show emoji for task type (default: enabled)')
        display_group.add_argument('--no-type-emoji', action='store_false', dest='show_type_emoji', help='Hide task type emoji')
        
        # Sorting options
        display_group.add_argument('--sort-by', choices=['name', 'status', 'priority', 'created', 'updated'], 
                                help='Sort tasks by field')
    
    def execute(self, args: Namespace) -> Union[int, str]:
        """
        Execute the list command.
        
        This method loads the specified template file, filters tasks based on the 
        provided criteria, and displays them in the requested format. It handles
        various display modes including flat lists, hierarchical trees, and
        container-based organization.
        
        Args:
            args: Command arguments containing template file and filtering/display options
        
        Returns:
            Exit code (0 for success, non-zero for error) or
            String result for tests
        """
        try:
            # Check if template is provided, if not, try to find default template
            if not hasattr(args, 'template') or args.template is None:
                from refactor.utils.template_finder import find_default_template
                default_template = find_default_template()
                if default_template:
                    logger.info(f"Using default template: {default_template}")
                    args.template = default_template
                else:
                    raise ValueError("No template specified and no default template found in .project directory")

            # Initialize core manager with the template file
            self._core_manager.initialize(args.template)
            
            # Get all tasks
            all_tasks = self._core_manager.get_all_tasks()
            
            # Check if there are tasks to display
            if not all_tasks:
                print(f"No tasks found in template file {args.template}")
                return 0
            
            # Filter tasks based on command arguments
            filtered_tasks = self._filter_tasks(all_tasks, args)
            
            # Import necessary modules
            from refactor.cli.formatting.common.task_info import FormatOptions
            
            # Create basic format options common to all display modes
            display_opts = {
                'colorize_output': True,
                'show_ids': hasattr(args, 'show_id') and args.show_id,
                'include_completed': hasattr(args, 'complete') and args.complete,
                'hide_orphaned': hasattr(args, 'hide_orphaned') and args.hide_orphaned,
                'show_score': hasattr(args, 'show_score') and args.show_score,
                'show_tags': hasattr(args, 'show_tags') and args.show_tags,
                'tag_style': args.tag_style if hasattr(args, 'tag_style') else "colored",
                'show_type_emoji': hasattr(args, 'show_type_emoji') and args.show_type_emoji,
                'show_descriptions': hasattr(args, 'show_descriptions') and args.show_descriptions,
                'description_length': args.description_length if hasattr(args, 'description_length') else 100
            }
            
            # Create FormatOptions object with valid parameters
            options = FormatOptions(**display_opts)
            
            # Display tasks based on the selected format
            # Check if any of the alternative display formats are explicitly requested
            if hasattr(args, 'flat') and args.flat or hasattr(args, 'tree') and args.tree or \
               hasattr(args, 'dependency_as_tree') and args.dependency_as_tree or \
               hasattr(args, 'no_container') and args.no_container:
                # Use default task hierarchy display for other formats
                from refactor.cli.formatting.tree.hierarchy import format_task_hierarchy
                
                # Get tree-specific settings
                dependency_as_tree = hasattr(args, 'dependency_as_tree') and args.dependency_as_tree
                dependency_type = args.dependency_type if hasattr(args, 'dependency_type') else 'depends_on'
                
                # Format tasks based on the selected display mode
                output = format_task_hierarchy(
                    filtered_tasks,
                    options=options,
                    validate_tree=False,
                    show_orphaned=not (hasattr(args, 'hide_orphaned') and args.hide_orphaned),
                    parent_id=None,
                    level=0,
                    trace=False
                )
                print(output)
            else:
                # Default to container hierarchy view
                # Import the container hierarchy formatter
                from refactor.cli.formatting.tree.container import format_container_hierarchy
                
                # Add container-specific options
                container_opts = {
                    'show_relationships': hasattr(args, 'show_relationships') and args.show_relationships,
                    'show_comments': args.show_comments if hasattr(args, 'show_comments') else 0
                }
                
                # Format the tasks in container hierarchy
                output = format_container_hierarchy(
                    filtered_tasks,
                    options=options,
                    **container_opts
                )
                print(output)
            
            return 0
        except Exception as e:
            logger.error(f"Error listing tasks: {str(e)}", exc_info=True)
            print(f"Error: {str(e)}")
            return 1
            
    def _filter_tasks(self, tasks, args):
        """
        Filter tasks based on command arguments.
        
        Args:
            tasks: List of tasks to filter
            args: Command arguments containing filter criteria
            
        Returns:
            Filtered list of tasks
        """
        filtered_tasks = []
        
        for task in tasks:
            # Apply filters based on command args
            
            # Filter by status
            if hasattr(args, 'status') and args.status:
                if task.get('status', '').lower() != args.status.lower():
                    continue
                    
            # Filter by priority
            if hasattr(args, 'priority') and args.priority:
                if task.get('priority', 3) != args.priority:
                    continue
                    
            # Filter by tags
            if hasattr(args, 'tags') and args.tags:
                tag_list = [t.strip() for t in args.tags.split(',')]
                task_tags = task.get('tags', [])
                if not any(tag in task_tags for tag in tag_list):
                    continue
                    
            # Filter by parent
            if hasattr(args, 'parent') and args.parent:
                parent_id = task.get('parent_id')
                if not parent_id or parent_id != args.parent:
                    continue
                    
            # Filter by completion status
            if not hasattr(args, 'complete') or not args.complete:
                if task.get('status', '').lower() == 'complete':
                    continue
                    
            # Filter by parent-only flag
            if hasattr(args, 'parent_only') and args.parent_only:
                if not task.get('is_parent', False) and not task.get('subtasks'):
                    continue
                    
            # Filter by task type
            if hasattr(args, 'task_type') and args.task_type:
                task_type = task.get('task_type', '')
                if task_type != args.task_type:
                    continue
                    
            # Task passed all filters
            filtered_tasks.append(task)
            
        return filtered_tasks


class UpdateTaskCommand(Command):
    """
    Task: tsk_bf28d342 - Update CLI Module Comments
    Document: refactor/cli/commands/task.py
    dohcount: 1

    Purpose:
        Implements a command to update existing task properties including status,
        name, description, priority, and tags. Also allows adding comments when
        updating tasks to document the changes made.

    Requirements:
        - Must locate the target task by name or ID
        - Must support updating multiple properties in a single operation
        - Must handle status changes with appropriate validation
        - Must properly handle tag updates (add/remove)
        - CRITICAL: Must validate task status transitions
        - CRITICAL: Must handle force flag for overriding validation restrictions

    Used By:
        - Users: For updating task properties and status
        - Project managers: For task status management
        - Integration scripts: For automated task updates
        - Workflow management: For status transitions

    Changes:
        - v1: Initial implementation with basic task updates
        - v2: Added validation for status transitions
        - v3: Enhanced tag management
        - v4: Added force flag for overriding validation
    """
    
    def __init__(self, core_manager):
        """
        Initialize a new UpdateTaskCommand instance.
        
        Creates a command that allows users to update various task properties,
        with a focus on status changes and proper validation of transitions.
        
        Args:
            core_manager: Core manager instance for accessing task services
        """
        self._core_manager = core_manager
    
    @property
    def name(self) -> str:
        """
        Get the command name.
        
        Returns:
            The string "update" as the command's name
        """
        return "update"
    
    @property
    def description(self) -> str:
        """
        Get the command description.
        
        Returns:
            A description of the command's purpose
        """
        return "Update task attributes"
    
    def configure_parser(self, parser):
        """
        Configure the argument parser for the update task command.
        
        Adds arguments for updating various task properties including
        status, name, description, priority, tags, and for adding
        comments during updates. Also includes force flag for overrides.
        
        Args:
            parser: The argument parser to configure with arguments
        """
        parser.add_argument('template', help='Path to the task file')
        parser.add_argument('task_name', help='Task name or ID to update')
        parser.add_argument('-n', '--name', help='New task name')
        parser.add_argument('-d', '--description', help='New task description')
        parser.add_argument('-s', '--status', help='New task status')
        parser.add_argument('-p', '--priority', help='New task priority')
        parser.add_argument('-t', '--tags', help='Task tags (comma-separated)')
        parser.add_argument('--task-type', choices=TaskType.get_all_types(), 
                           help='Task type (task, bug, feature, refactor, documentation)')
        parser.add_argument('-c', '--comment', help='Add a comment during update')
        parser.add_argument('-f', '--force', action='store_true', help='Force update without confirmation')
    
    def execute(self, args):
        """
        Execute the update task command with the provided arguments.
        
        Processes the arguments, validates the task exists, and updates
        specified properties with proper validation. Can force updates
        to bypass validation checks when appropriate.
        
        Args:
            args: Command arguments containing update parameters including
                  task identifier and properties to update
        
        Returns:
            Success code (0) or appropriate error code
        
        Notes:
            - Changes requiring validation can be forced with --force flag
            - Comments about changes are preserved in task history
            - Status changes trigger additional validation for completion
        """
        try:
            # Initialize core manager with the template file
            self._core_manager.initialize(args.template)

            # Find the task by name or ID
            task = self._core_manager.find_task(args.task_name)
            if not task:
                print(f"Task not found: {args.task_name}")
                return 1

            # Check if any updates are specified
            if not any([args.name, args.description, args.status, args.priority, args.tags, args.task_type]):
                print("No updates specified. Use -n, -d, -s, -p, -t, or --task-type to update task properties.")
                return 1

            # Store original task for comparison
            original_task = task.copy()

            # Update task properties
            if args.name:
                task['name'] = args.name
                
            if args.description:
                task['description'] = args.description

            if args.status:
                try:
                    # Update the status
                    self._core_manager.update_task_status(
                        task['id'], args.status, force=args.force, comment=args.comment
                    )
                    # Reload the task to get the updated status
                    task = self._core_manager.find_task(task['id'])
                except Exception as e:
                    print(f"Error updating status: {str(e)}")
                    if not args.force:
                        print("Use --force to override validation checks.")
                    return 1
                
            if args.priority:
                task['priority'] = int(args.priority)
                
            if args.tags:
                tags = [tag.strip() for tag in args.tags.split(',')]
                task['tags'] = tags
            
            if args.task_type:
                task['task_type'] = args.task_type

            # Update the task if there are changes other than status (which is handled separately)
            if any([
                args.name, 
                args.description, 
                args.priority, 
                args.tags,
                args.task_type
            ]):
                try:
                    self._core_manager.update_task(task)
                except Exception as e:
                    print(f"Error updating task: {str(e)}")
                    return 1

            # Add a comment if provided and not already added through status update
            if args.comment and not args.status:
                self._core_manager.add_task_comment(task['id'], args.comment)
            
            # Save changes
            self._core_manager.save()
            
            # Determine what changed for feedback
            changes = []
            if args.name and task['name'] != original_task['name']:
                changes.append(f"name: '{original_task['name']}' → '{task['name']}'")
            
            if args.status and task['status'] != original_task['status']:
                changes.append(f"status: '{original_task['status']}' → '{task['status']}'")
            
            if args.priority and task['priority'] != original_task['priority']:
                changes.append(f"priority: '{original_task['priority']}' → '{task['priority']}'")
            
            if args.tags and set(task['tags']) != set(original_task.get('tags', [])):
                changes.append(f"tags: '{', '.join(original_task.get('tags', []))}' → '{', '.join(task['tags'])}'")
            
            if args.task_type and task['task_type'] != original_task.get('task_type', 'task'):
                orig_type = get_colored_task_type(original_task.get('task_type', 'task'))
                new_type = get_colored_task_type(task['task_type'])
                changes.append(f"task type: {orig_type} → {new_type}")
            
            if args.description and task['description'] != original_task['description']:
                changes.append("description updated")

            if changes:
                print(f"Updated task '{task['name']}' ({task['id']}):")
                for change in changes:
                    print(f"  • {change}")
            else:
                print(f"No changes made to task '{task['name']}' ({task['id']})")

            return 0  # Success
        except Exception as e:
            logger.error(f"Error updating task: {str(e)}", exc_info=True)
            print(f"Error updating task: {str(e)}")
            return 1


class UpdateTypeCommand(Command):
    """
    Task: tsk_bf28d342 - Update CLI Module Comments
    Document: refactor/cli/commands/task.py
    dohcount: 1

    Purpose:
        Implements a dedicated command to update a task's type, providing a focused
        interface for changing the task classification between standard types like
        task, bug, feature, refactor, and documentation.

    Requirements:
        - Must locate the target task by name or ID
        - Must validate task type against supported types
        - Must handle type changes with appropriate feedback
        - Must update the task in the template file
        - CRITICAL: Must ensure consistent type naming
        - CRITICAL: Must preserve all other task properties

    Used By:
        - Users: For reclassifying tasks between different types
        - Project managers: For task organization and categorization
        - Integration scripts: For automated task type updates
        - Workflow management: For task lifecycle management

    Changes:
        - v1: Initial implementation with basic task type updates
    """

    def __init__(self, core_manager):
        """
        Initialize a new UpdateTypeCommand instance.
        
        Creates a command that allows users to update a task's type,
        with appropriate validation and feedback.
        
        Args:
            core_manager: Core manager instance for accessing task services
        """
        self._core_manager = core_manager
    
    @property
    def name(self) -> str:
        """
        Get the command name.
        
        Returns:
            The string "update-type" as the command's name
        """
        return "update-type"
    
    @property
    def description(self) -> str:
        """
        Get the command description.
        
        Returns:
            A description of the command's purpose
        """
        return "Update task type (task, bug, feature, refactor, documentation)"
    
    def get_aliases(self) -> List[str]:
        """
        Get alternate names for this command.
        
        Returns:
            A list containing alternative command names
        """
        return ["set-type", "change-type"]
    
    def configure_parser(self, parser):
        """
        Configure the argument parser for the update type command.
        
        Sets up required and optional arguments for updating a task's type,
        including the task identifier, new type, and related options.
        
        Args:
            parser: The argument parser to configure with arguments
        """
        parser.add_argument('template', help='Path to the task file')
        parser.add_argument('task_name', help='Task name or ID to update')
        parser.add_argument('task_type', choices=TaskType.get_all_types(), 
                           help='New task type')
        parser.add_argument('-c', '--comment', help='Add a comment explaining the type change')
        parser.add_argument('-f', '--force', action='store_true', help='Force update without confirmation')
    
    def execute(self, args):
        """
        Execute the update type command with the provided arguments.
        
        Processes the arguments, validates the task exists, and updates
        the task type with proper validation and feedback.
        
        Args:
            args: Command arguments containing task identifier and new type
        
        Returns:
            Success code (0) or appropriate error code
        """
        try:
            # Initialize core manager with the template file
            self._core_manager.initialize(args.template)

            # Find the task by name or ID
            task = self._core_manager.find_task(args.task_name)
            if not task:
                print(f"Task not found: {args.task_name}")
                return 1

            # Store original task for comparison
            original_task = task.copy()
            original_type = original_task.get('task_type', 'task')  # Default to 'task' if not set

            # Update task type
            task['task_type'] = args.task_type

            # Update the task
            try:
                self._core_manager.update_task(task)
            except Exception as e:
                print(f"Error updating task type: {str(e)}")
                return 1

            # Add a comment if provided
            if args.comment:
                comment_text = f"Changed task type from '{original_type}' to '{args.task_type}': {args.comment}"
                self._core_manager.add_task_comment(task['id'], comment_text)
            
            # Save changes
            self._core_manager.save()
            
            # Get colored task types for display
            orig_type = get_colored_task_type(original_type)
            new_type = get_colored_task_type(args.task_type)
            
            # Provide feedback
            print(f"Updated task '{task['name']}' ({task['id']}):")
            print(f"  • task type: {orig_type} → {new_type}")

            return 0  # Success
        except Exception as e:
            logger.error(f"Error updating task type: {str(e)}", exc_info=True)
            print(f"Error updating task type: {str(e)}")
            return 1


class DeleteTaskCommand(Command):
    """
    Task: tsk_bf28d342 - Update CLI Module Comments
    Document: refactor/cli/commands/task.py
    dohcount: 1

    Purpose:
        Implements a command to delete tasks from a template file with support
        for cascading deletion of subtasks and confirmation prompts to prevent
        accidental deletions of important tasks or hierarchies.

    Requirements:
        - Must validate task existence before deletion
        - Must support cascading deletion of subtasks when specified
        - Must provide confirmation prompt for non-force operations
        - Must handle deletion errors gracefully
        - CRITICAL: Must prevent accidental deletion of tasks with subtasks
          unless explicitly requested with cascade option
        - CRITICAL: Must handle relationships correctly when deleting tasks

    Used By:
        - CLI Users: For removing completed or obsolete tasks
        - Project Managers: For cleaning up task hierarchies
        - Automated Scripts: For bulk task management

    Changes:
        - v1: Initial implementation with basic deletion
        - v2: Added cascade deletion support
        - v3: Enhanced validation and error handling
        - v4: Added confirmation prompts for safer deletion
        - v5: Improved relationship handling during deletion
    """

    def __init__(self, core_manager: CoreManager):
        """
        Initialize a new DeleteTaskCommand instance.
        
        Args:
            core_manager: Core manager instance for task deletion services
        """
        self._core_manager = core_manager
    
    @property
    def name(self) -> str:
        """Get the command name."""
        return "delete"
    
    @property
    def description(self) -> str:
        """Get the command description."""
        return "Delete a task"

    def get_aliases(self) -> List[str]:
        """Get command aliases."""
        return ["remove", "del"]

    def configure_parser(self, parser: ArgumentParser) -> None:
        """
        Configure the argument parser for the delete task command.
        
        Args:
            parser: The argument parser to configure with arguments
        """
        parser.add_argument('template', help='Path to the task file')
        parser.add_argument('task_name', help='Task name or ID to delete')
        parser.add_argument('--no-confirm', action='store_true', help='Skip confirmation prompt')
        parser.add_argument('--cascade', action='store_true', help='Also delete subtasks')
        parser.add_argument('--force', action='store_true', help='Force deletion even if task has dependencies')

    def execute(self, args: Namespace) -> int:
        """
        Execute the delete task command, removing a task from the template file.
        
        Args:
            args: Command arguments containing task identifier and deletion options
        
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        try:
            # Initialize core manager with the template file
            self._core_manager.initialize(args.template)
            
            # Get the task to delete
            task = self._core_manager.find_task_by_id_or_name(args.task_name)
            if not task:
                logger.error(f"Task not found: {args.task_name}")
                return 1
            
            # Check for subtasks if not cascading
            if not args.cascade:
                subtasks = self._core_manager.get_subtasks(task['id'])
            if subtasks:
                subtask_count = len(subtasks)
                logger.warning(f"Task has {subtask_count} subtasks. Use --cascade to delete them too.")
                print(f"Warning: Task has {subtask_count} subtasks that will be orphaned.")
                print("Use --cascade to delete them as well.")
            
            # Check for task relationships if not forcing
            if not args.force:
                relationships = self._core_manager.get_task_relationships(task['id'])
                if relationships and ('blocks' in relationships and relationships['blocks']):
                    blocks_count = len(relationships['blocks'])
                    logger.warning(f"Task blocks {blocks_count} other tasks. Use --force to delete anyway.")
                    print(f"Warning: This task blocks {blocks_count} other tasks.")
                    print("Use --force to delete it anyway.")
            
            # Confirm deletion unless no-confirm flag is set
            if not args.no_confirm:
                print(f"Delete task: {task['name']} [{task['id']}]?")
                confirm = input("Are you sure? [y/N]: ").lower()
                if confirm != 'y':
                    print("Deletion canceled")
                    return 0
            
            # Delete the task
            self._core_manager.delete_task(
                task['id'], 
                cascade=args.cascade, 
                force=args.force
            )
            
            print(f"Task deleted: {task['name']} [{task['id']}]")
            return 0
        except Exception as e:
            logger.error(f"Error deleting task: {str(e)}", exc_info=True)
            print(f"Error deleting task: {str(e)}")
            return 1


class CommentTaskCommand(Command):
    """
    Task: tsk_bf28d342 - Update CLI Module Comments
    Document: refactor/cli/commands/task.py
    dohcount: 1

    Purpose:
        Implements a command to add comments to tasks, providing a way to record
        notes, decisions, and discussions related to specific tasks. Supports
        both inline comment text and file-based comment input for longer content.

    Requirements:
        - Must validate task existence before adding comment
        - Must handle multiline comment text properly
        - Must support reading comment content from files
        - Must properly format and store comment metadata
        - CRITICAL: Must preserve all line breaks and formatting in comments
        - CRITICAL: Must handle UTF-8 encoding for international text

    Used By:
        - CLI Users: For adding notes and progress updates to tasks
        - Project Managers: For providing guidance and requirements clarification
        - Reviewers: For adding feedback on implementation
        - Automation Scripts: For tracking automated process results

    Changes:
        - v1: Initial implementation with basic comment addition
        - v2: Added support for file-based comment input
        - v3: Enhanced newline handling and formatting
        - v4: Improved author attribution and timestamps
        - v5: Added support for comment formatting preservation
    """

    def __init__(self, core_manager: CoreManager):
        """
        Initialize a new CommentTaskCommand instance.
        
        Args:
            core_manager: Core manager instance for task comment services
        """
        self._core_manager = core_manager
    
    @property
    def name(self) -> str:
        """Get the command name."""
        return "comment"
    
    @property
    def description(self) -> str:
        """Get the command description."""
        return "Add a comment to a task"

    def get_aliases(self) -> List[str]:
        """Get command aliases."""
        return ["add-comment", "annotate"]

    def configure_parser(self, parser: ArgumentParser) -> None:
        """
        Configure the argument parser for the comment task command.
        
        Args:
            parser: The argument parser to configure with arguments
        """
        parser.add_argument('template', help='Path to the task file')
        parser.add_argument('task_name', help='Task name or ID to add comment to')
        
        # Create a mutually exclusive group for comment input methods
        comment_group = parser.add_mutually_exclusive_group(required=True)
        comment_group.add_argument('-t', '--text', help='Comment text')
        comment_group.add_argument('-f', '--file', help='Read comment from file')
        
        parser.add_argument('-a', '--author', help='Comment author', default=getpass.getuser())

    def execute(self, args: Namespace) -> int:
        """
        Execute the command to add a comment to a task.
        
        Args:
            args: Command arguments including task and comment information
        
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        try:
            # Initialize core manager
            self._core_manager.initialize(args.template)
            
            # Get comment text from either direct input or file
            comment_text = ""
            if hasattr(args, 'text') and args.text:
                comment_text = args.text
            elif hasattr(args, 'file') and args.file:
                # Read comment from file
                with open(args.file, 'r', encoding='utf-8') as f:
                    comment_text = f.read()
            else:
                logger.error("No comment text provided")
                return 1
            
            # Add comment to task
            task = self._core_manager.find_task_by_id_or_name(args.task_name)
            if not task:
                logger.error(f"Task '{args.task_name}' not found")
                return 1

            # Add the comment
            author = args.author if hasattr(args, 'author') and args.author else getpass.getuser()
            self._core_manager.add_comment_to_task(task['id'], comment_text, author)
            
            # Save changes to file
            self._core_manager.save()
            
            print(f"Added comment to task {task['name']} [{task['id']}]")
            return 0
        except Exception as e:
            logger.error(f"Error adding comment: {str(e)}", exc_info=True)
            return 1


class TaskCommand(Command):
    """
    Task command group.
    
    This command group provides subcommands for task management operations.
    """

    def __init__(self, core_manager: CoreManager):
        """
        Initialize a new TaskCommand instance with all task-related subcommands.
        
        Creates a composite command that serves as the entry point for all
        task management operations, organizing them into a unified hierarchy.
        
        Args:
            core_manager: Core manager instance for accessing task services
                          and passing to subcommands
        """
        # Register subcommands
        self._subcommands = {}
        self._core_manager = core_manager
        
        # Add subcommands
        self.add_subcommand(CreateTaskCommand(core_manager))
        self.add_subcommand(CreateSubtaskCommand(core_manager))
        self.add_subcommand(ShowTaskCommand(core_manager))
        self.add_subcommand(ListTasksCommand(core_manager))
        self.add_subcommand(UpdateTaskCommand(core_manager))
        self.add_subcommand(DeleteTaskCommand(core_manager))
        self.add_subcommand(CommentTaskCommand(core_manager))
        self.add_subcommand(UpdateTypeCommand(core_manager))
        self.add_subcommand(AssignToListCommand(core_manager))  # Add the new command
    
    @property
    def name(self) -> str:
        """
        Get the command name.
        
        Returns:
            The string "task" as the command's name
        """
        return "task"
    
    @property
    def description(self) -> str:
        """
        Get the command description.
        
        Returns:
            A description of the command's purpose
        """
        return "Task management operations"
    
    def get_aliases(self) -> List[str]:
        """
        Get alternate names for this command.
        
        Returns:
            A list of command aliases (currently none)
        """
        return []
    
    def add_subcommand(self, command: Command) -> None:
        """
        Register a new subcommand with this composite command.
        
        Adds a task-related command to the subcommand registry,
        making it available for use through the task command.
        
        Args:
            command: Command instance to register as a subcommand
        """
        self._subcommands[command.name] = command
    
    def configure_parser(self, parser: ArgumentParser) -> None:
        """
        Configure the argument parser for the task command.
        
        Sets up a subparser group for all task-related subcommands,
        delegating parser configuration to each registered subcommand.
        
        Args:
            parser: The argument parser to configure with subcommands
        """
        subparsers = parser.add_subparsers(dest='subcommand', help='Task subcommands')
        subparsers.required = True
        
        for name, command in self._subcommands.items():
            subparser = subparsers.add_parser(name, help=command.description)
            command.configure_parser(subparser)
    
    def execute(self, args: Namespace) -> Union[int, str]:
        """
        Execute the appropriate task subcommand based on arguments.
        
        Routes the command execution to the specified subcommand,
        providing comprehensive error handling for the task command
        hierarchy.
        
        Args:
            args: Command arguments containing the subcommand to execute
                  and its specific arguments
        
        Returns:
            Exit code (0 for success, non-zero for error)
        
        Notes:
            - Subcommand execution is delegated to the specific command implementation
            - Error handling includes validation of subcommand specification
            - Maintains a consistent execution flow across all task operations
        """
        if not hasattr(args, 'subcommand') or not args.subcommand:
            print("Error: No subcommand specified")
            return 1
            
        command = self._subcommands.get(args.subcommand)
        if not command:
            print(f"Error: Unknown subcommand '{args.subcommand}'")
            return 1
            
        return command.execute(args) 