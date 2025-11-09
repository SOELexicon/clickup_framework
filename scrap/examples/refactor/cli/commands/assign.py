"""
Task: tsk_a3f74d5d - Implement List Assignment Command
Document: refactor/cli/commands/assign.py
dohcount: 4

Purpose:
    Command implementation for assigning tasks to lists
    and managing task container relationships.
"""
from argparse import ArgumentParser, Namespace
from typing import Dict, List, Optional

from refactor.cli.commands.base import SimpleCommand
from refactor.core.interfaces.core_manager import CoreManager
from refactor.cli.error_handling import CLIError, ErrorCode


class AssignToListCommand(SimpleCommand):
    """Command for assigning a task to a list."""
    
    def __init__(self, core_manager: CoreManager):
        """
        Initialize with a core manager.
        
        Args:
            core_manager: The core manager to use for task operations
        """
        # Call super with required parameters
        super().__init__("assign", "Assign a task to a list", core_manager)
    
    def configure_parser(self, parser: ArgumentParser) -> None:
        """
        Configure the parser for assign task command.
        
        Args:
            parser: The parser to configure
        """
        parser.add_argument(
            "template",
            help="Path to the template file"
        )
        parser.add_argument(
            "task_id",
            help="ID of the task to assign"
        )
        parser.add_argument(
            "list_id",
            help="ID of the list to assign the task to"
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force assignment even if task has existing container"
        )
    
    def execute(self, args: Namespace) -> int:
        """
        Task: tsk_a3f74d5d - Implement List Assignment Command
        Document: refactor/cli/commands/assign.py
        dohcount: 6
        
        Used By:
            - CLI: Directly executed by users
            
        Purpose:
            Executes the assign task command to associate a task with a list container,
            updating bidirectional relationships and checking for existing assignments.
            
        Requirements:
            - Must validate task and list existence
            - Must use the proper container_id field
            - Must respect the force flag for reassignment
            - Must provide clear user feedback
            
        Args:
            args: The parsed command arguments
            
        Returns:
            Exit code (0 for success, 1 for failure)
            
        Changes:
            - v1: Basic task assignment
            - v2: Added support for task lookup by name
            - v3: Added container check and force flag
            - v4: Updated to use core_manager methods directly
            - v5: Updated to use container_id for parent tracking
            - v6: Improved handling of both dictionary and entity objects
        """
        try:
            # Initialize the core manager with the template file
            self._core_manager.initialize(args.template)
            
            # Find the task and get its ID and name
            task = None
            try:
                # Try direct dictionary access first for FileManager compatibility
                for t in self._core_manager.data.get("tasks", []):
                    if t.get("id") == args.task_id or t.get("name") == args.task_id:
                        task = t
                        break
                
                # If not found, try core_manager methods
                if not task:
                    task = self._core_manager.get_task(args.task_id)
            except Exception as e:
                print(f"Error: Task '{args.task_id}' not found: {str(e)}")
                return 1
                
            if not task:
                print(f"Error: Task '{args.task_id}' not found")
                return 1
            
            # Get task ID and name
            task_id = task.id if hasattr(task, 'id') else task.get('id')
            task_name = task.name if hasattr(task, 'name') else task.get('name', 'Unknown Task')
            
            # Check if task is already assigned to a container
            container_id = None
            if hasattr(task, 'container_id'):
                container_id = task.container_id
            elif isinstance(task, dict) and 'container_id' in task:
                container_id = task.get('container_id')
                
            if container_id and not args.force:
                print(f"Error: Task '{task_name}' is already assigned to container '{container_id}'. Use --force to reassign.")
                return 1

            # Find the list to verify it exists
            list_exists = False
            list_name = args.list_id
            for lst in self._core_manager.data.get('lists', []):
                if lst.get('id') == args.list_id:
                    list_exists = True
                    list_name = lst.get('name', list_name)
                    break
            
            if not list_exists:
                print(f"Error: List '{args.list_id}' not found")
                return 1
                
            # Use the built-in method to add task to list with force flag
            try:
                self._core_manager.add_task_to_list(task_id, args.list_id, args.force)
                print(f"Successfully assigned task '{task_name}' to list '{list_name}'")
                self._core_manager.save()
                return 0
            except Exception as e:
                print(f"Error assigning task to list: {str(e)}")
                return 1
                
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return 1 