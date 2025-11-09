"""
List Commands Implementation

This module provides command implementations for list management operations
such as creating, showing, and manipulating lists of tasks.
"""
import json
import sys
import re
import os
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Set, Tuple, Optional, Union
from argparse import ArgumentParser, Namespace
import traceback

from refactor.cli.commands.base import BaseCommand, CompositeCommand, SimpleCommand
from refactor.core.interfaces.core_manager import CoreManager
from refactor.utils.template_finder import get_template_path
from refactor.cli.formatting.tree.hierarchy import format_task_hierarchy
from refactor.cli.formatting.tree.container import format_container_hierarchy
from refactor.cli.formatting.common.task_info import FormatOptions

# Import format_task_list from the correct location
from refactor.cli.commands.utils import format_task_list

# Configure logger
logger = logging.getLogger(__name__)


class CreateListCommand(SimpleCommand):
    """Command for creating a new list."""
    
    def __init__(self, core_manager: CoreManager):
        """
        Initialize with a core manager.
        
        Args:
            core_manager: The core manager to use for list operations
        """
        super().__init__("create", "Create a new list in a folder")
        self._core_manager = core_manager
    
    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        """
        Configure the parser for create list command.
        
        Args:
            parser: The parser to configure
        """
        parser.add_argument(
            "name",
            help="Name of the list to create"
        )
        parser.add_argument(
            "folder",
            help="Parent folder ID or name"
        )
        parser.add_argument(
            "--description",
            help="Description of the list"
        )
        parser.add_argument(
            "--order",
            type=int,
            help="Position in the folder (0-based index)"
        )
        parser.add_argument(
            "--template",
            help="JSON file to use as template"
        )
        parser.add_argument(
            "--color",
            help="Color for the list (hex code or name)"
        )
        parser.add_argument(
            "--icon",
            help="Icon identifier for the list"
        )
    
    def execute(self, args: argparse.Namespace) -> int:
        """
        Execute the create list command.
        
        Args:
            args: Command arguments
            
        Returns:
            Exit code (0 for success)
        """
        try:
            # Find the parent folder
            parent_folder = self._core_manager.find_folder(args.folder)
            if not parent_folder:
                print(f"Folder not found: {args.folder}")
                return 1
            
            # Create the list
            list_entity = self._core_manager.create_list(
                name=args.name,
                folder_id=parent_folder.id,
                description=args.description or "",
                color=args.color,
                icon=args.icon
            )
            
            print(f"List created: {list_entity.name}")
            print(f"ID: {list_entity.id}")
            print(f"Folder: {parent_folder.name}")
            
            if args.description:
                print(f"Description: {args.description}")
                
            # Display color and icon if provided
            if hasattr(list_entity, 'color') and list_entity.color:
                print(f"Color: {list_entity.color}")
            if hasattr(list_entity, 'icon') and list_entity.icon:
                print(f"Icon: {list_entity.icon}")
            
            return 0
        except Exception as e:
            print(f"Error creating list: {str(e)}")
            return 1


class ShowListCommand(SimpleCommand):
    """Command for showing list details."""
    
    def __init__(self, core_manager: CoreManager):
        """
        Initialize with a core manager.
        
        Args:
            core_manager: The core manager to use for list operations
        """
        super().__init__("show", "Show list details")
        self._core_manager = core_manager
    
    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        """
        Configure the parser for show list command.
        
        Args:
            parser: The parser to configure
        """
        parser.add_argument(
            "list",
            help="List ID or name to show"
        )
        parser.add_argument(
            "--with-tasks",
            action="store_true",
            help="Show tasks in the list"
        )
        parser.add_argument(
            "--status",
            help="Filter tasks by status"
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=10,
            help="Maximum number of tasks to show"
        )
    
    def execute(self, args: argparse.Namespace) -> int:
        """
        Execute the show list command.
        
        Args:
            args: Command arguments
            
        Returns:
            Exit code (0 for success)
        """
        try:
            # Find the list
            list_entity = self._core_manager.find_list(args.list)
            if not list_entity:
                print(f"List not found: {args.list}")
                return 1
            
            # Display list information
            print(f"List: {list_entity.name}")
            print(f"ID: {list_entity.id}")
            
            # Get parent folder name
            try:
                folder = self._core_manager.get_folder(list_entity.folder_id)
                print(f"Folder: {folder.name} (ID: {folder.id})")
            except:
                print(f"Folder ID: {list_entity.folder_id}")
            
            if list_entity.description:
                print(f"\nDescription: {list_entity.description}")
                
            # Display color and icon if they exist
            if hasattr(list_entity, 'color') and list_entity.color:
                print(f"Color: {list_entity.color}")
            if hasattr(list_entity, 'icon') and list_entity.icon:
                print(f"Icon: {list_entity.icon}")
            
            # Show tasks if requested
            if args.with_tasks:
                print("\nTasks:")
                
                # Build filter criteria
                criteria = {"list_id": list_entity.id}
                if args.status:
                    criteria["status"] = args.status
                
                # Get tasks
                tasks = self._core_manager.search_tasks(
                    criteria=criteria,
                    limit=args.limit
                )
                
                if not tasks:
                    print("  No tasks found")
                else:
                    for task in tasks:
                        status_str = f"[{task.status.value}]" if hasattr(task, 'status') else ""
                        print(f"  - {task.name} {status_str}")
                        print(f"    ID: {task.id}")
                        print()
                
                # Show pagination info
                if hasattr(tasks, 'total_count') and len(tasks) < tasks.total_count:
                    print(f"Showing {len(tasks)} of {tasks.total_count} tasks.")
                    print(f"Use --limit to see more tasks.")
            
            return 0
        except Exception as e:
            print(f"Error showing list: {str(e)}")
            return 1


class ListListsCommand(SimpleCommand):
    """Command for listing all lists."""
    
    def __init__(self, core_manager: CoreManager):
        """
        Initialize with a core manager.
        
        Args:
            core_manager: The core manager to use for list operations
        """
        super().__init__("list", "List all lists or lists in a folder")
        self._core_manager = core_manager
    
    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        """
        Configure the parser for list lists command.
        
        Args:
            parser: The parser to configure
        """
        parser.add_argument(
            "--folder",
            help="Only show lists in this folder (ID or name)"
        )
        parser.add_argument(
            "--space",
            help="Only show lists in this space (ID or name)"
        )
        parser.add_argument(
            "--format",
            choices=["default", "compact", "json"],
            default="default",
            help="Output format"
        )
    
    def execute(self, args: argparse.Namespace) -> int:
        """
        Execute the list lists command.
        
        Args:
            args: Command arguments
            
        Returns:
            Exit code (0 for success)
        """
        try:
            folder_id = None
            space_id = None
            
            # Resolve folder if provided
            if args.folder:
                folder = self._core_manager.find_folder(args.folder)
                if not folder:
                    print(f"Folder not found: {args.folder}")
                    return 1
                folder_id = folder.id
                # Get the space ID from the folder
                space_id = folder.space_id
            
            # Resolve space if provided
            elif args.space:
                space = self._core_manager.find_space(args.space)
                if not space:
                    print(f"Space not found: {args.space}")
                    return 1
                space_id = space.id
            
            # Get lists
            if folder_id:
                lists = self._core_manager.get_lists_in_folder(folder_id)
                scope = f"folder '{args.folder}'"
            elif space_id:
                # Get all folders in the space then get lists in each folder
                folders = self._core_manager.get_folders_in_space(space_id)
                lists = []
                for folder in folders:
                    folder_lists = self._core_manager.get_lists_in_folder(folder.id)
                    lists.extend(folder_lists)
                scope = f"space '{args.space}'"
            else:
                # Get all lists
                lists = self._core_manager.get_all_lists()
                scope = "all spaces"
            
            # Display the lists
            if args.format == "json":
                lists_data = [list_entity.to_dict() for list_entity in lists]
                print(json.dumps(lists_data, indent=2))
            else:
                if not lists:
                    print(f"No lists found in {scope}")
                    return 0
                
                print(f"Lists in {scope} ({len(lists)}):\n")
                
                if args.format == "compact":
                    # Compact format just shows name and ID
                    for list_entity in lists:
                        print(f"{list_entity.name} (ID: {list_entity.id})")
                else:
                    # Default format shows more details
                    for list_entity in lists:
                        print(f"List: {list_entity.name}")
                        print(f"ID: {list_entity.id}")
                        
                        # Try to get folder name
                        try:
                            folder = self._core_manager.get_folder(list_entity.folder_id)
                            print(f"Folder: {folder.name}")
                        except:
                            print(f"Folder ID: {list_entity.folder_id}")
                        
                        print()
            
            return 0
        except Exception as e:
            print(f"Error listing lists: {str(e)}")
            return 1


class UpdateListCommand(SimpleCommand):
    """Command for updating a list."""
    
    def __init__(self, core_manager: CoreManager):
        """
        Initialize with a core manager.
        
        Args:
            core_manager: The core manager to use for list operations
        """
        super().__init__("update", "Update list properties")
        self._core_manager = core_manager
    
    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        """
        Configure the parser for update list command.
        
        Args:
            parser: The parser to configure
        """
        parser.add_argument(
            "list",
            help="List ID or name to update"
        )
        parser.add_argument(
            "--name",
            help="New name for the list"
        )
        parser.add_argument(
            "--description",
            help="New description for the list"
        )
        parser.add_argument(
            "--folder",
            help="Move list to this folder (ID or name)"
        )
        parser.add_argument(
            "--order",
            type=int,
            help="New position in the folder (0-based index)"
        )
    
    def execute(self, args: argparse.Namespace) -> int:
        """
        Execute the update list command.
        
        Args:
            args: Command arguments
            
        Returns:
            Exit code (0 for success)
        """
        try:
            # Check if at least one update field is provided
            if not (args.name or args.description is not None or args.folder or args.order is not None):
                print("Error: No updates specified. Use --name, --description, --folder, or --order.")
                return 1
            
            # Find the list
            list_entity = self._core_manager.find_list(args.list)
            if not list_entity:
                print(f"List not found: {args.list}")
                return 1
            
            # Prepare update data
            updates = {}
            folder_id = None
            
            if args.name:
                updates["name"] = args.name
            
            if args.description is not None:
                updates["description"] = args.description
            
            if args.order is not None:
                updates["order"] = args.order
            
            if args.folder:
                folder = self._core_manager.find_folder(args.folder)
                if not folder:
                    print(f"Folder not found: {args.folder}")
                    return 1
                folder_id = folder.id
                updates["folder_id"] = folder_id
            
            # Update the list
            updated_list = self._core_manager.update_list(list_entity.id, **updates)
            
            print(f"List updated: {updated_list.name}")
            print(f"ID: {updated_list.id}")
            
            # Show what was updated
            if args.name:
                print(f"Name: {args.name}")
            
            if args.description is not None:
                print(f"Description: {args.description}")
            
            if folder_id:
                print(f"Moved to folder: {args.folder}")
            
            if args.order is not None:
                print(f"Order: {args.order}")
            
            return 0
        except Exception as e:
            print(f"Error updating list: {str(e)}")
            return 1


class DeleteListCommand(SimpleCommand):
    """Command for deleting a list."""
    
    def __init__(self, core_manager: CoreManager):
        """
        Initialize with a core manager.
        
        Args:
            core_manager: The core manager to use for list operations
        """
        super().__init__("delete", "Delete a list")
        self._core_manager = core_manager
    
    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        """
        Configure the parser for delete list command.
        
        Args:
            parser: The parser to configure
        """
        parser.add_argument(
            "list",
            help="List ID or name to delete"
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force deletion even if the list contains tasks"
        )
        parser.add_argument(
            "--move-tasks",
            help="Move tasks to this list before deleting (ID or name)"
        )
    
    def execute(self, args: argparse.Namespace) -> int:
        """
        Execute the delete list command.
        
        Args:
            args: Command arguments
            
        Returns:
            Exit code (0 for success)
        """
        try:
            # Find the list
            list_entity = self._core_manager.find_list(args.list)
            if not list_entity:
                print(f"List not found: {args.list}")
                return 1
            
            # Check if list has tasks
            task_count = self._core_manager.count_tasks_in_list(list_entity.id)
            
            if task_count > 0:
                if args.move_tasks:
                    # Find target list for moving tasks
                    target_list = self._core_manager.find_list(args.move_tasks)
                    if not target_list:
                        print(f"Target list not found: {args.move_tasks}")
                        return 1
                    
                    # Move tasks
                    self._core_manager.move_tasks_to_list(
                        source_list_id=list_entity.id,
                        target_list_id=target_list.id
                    )
                    
                    print(f"Moved {task_count} task(s) to list '{target_list.name}'")
                    
                elif not args.force:
                    print(f"List '{list_entity.name}' contains {task_count} task(s).")
                    print("Use --force to delete it anyway, or --move-tasks to move tasks before deleting.")
                    return 1
                else:
                    print(f"Warning: Deleting list with {task_count} task(s).")
            
            # Delete the list
            self._core_manager.delete_list(list_entity.id)
            
            print(f"List deleted: {list_entity.name}")
            return 0
        except Exception as e:
            print(f"Error deleting list: {str(e)}")
            return 1


class MoveListCommand(SimpleCommand):
    """Command for moving a list to a different folder."""
    
    def __init__(self, core_manager: CoreManager):
        """
        Initialize with a core manager.
        
        Args:
            core_manager: The core manager to use for list operations
        """
        super().__init__("move", "Move a list to another folder")
        self._core_manager = core_manager
    
    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        """
        Configure the parser for move list command.
        
        Args:
            parser: The parser to configure
        """
        parser.add_argument(
            "list",
            help="List ID or name to move"
        )
        parser.add_argument(
            "folder",
            help="Target folder ID or name"
        )
        parser.add_argument(
            "--order",
            type=int,
            help="Position in the target folder (0-based index)"
        )
    
    def execute(self, args: argparse.Namespace) -> int:
        """
        Execute the move list command.
        
        Args:
            args: Command arguments
            
        Returns:
            Exit code (0 for success)
        """
        try:
            # Find the list
            list_entity = self._core_manager.find_list(args.list)
            if not list_entity:
                print(f"List not found: {args.list}")
                return 1
            
            # Find the target folder
            target_folder = self._core_manager.find_folder(args.folder)
            if not target_folder:
                print(f"Target folder not found: {args.folder}")
                return 1
            
            # Find the current folder
            try:
                current_folder = self._core_manager.get_folder(list_entity.folder_id)
                current_folder_name = current_folder.name
            except:
                current_folder_name = list_entity.folder_id
            
            # Move the list
            moved_list = self._core_manager.move_list(
                list_id=list_entity.id,
                target_folder_id=target_folder.id,
                order=args.order
            )
            
            print(f"List moved: {moved_list.name}")
            print(f"From folder: {current_folder_name}")
            print(f"To folder: {target_folder.name}")
            
            if args.order is not None:
                print(f"Position: {args.order}")
            
            return 0
        except Exception as e:
            print(f"Error moving list: {str(e)}")
            return 1


class UpdateListColorsCommand(SimpleCommand):
    """Command for updating list colors and icons."""
    
    def __init__(self, core_manager: CoreManager):
        """
        Initialize with a core manager.
        
        Args:
            core_manager: The core manager to use for list operations
        """
        super().__init__("update-colors", "Update color and icon for a list")
        self._core_manager = core_manager
    
    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        """
        Configure the parser for update colors command.
        
        Args:
            parser: The parser to configure
        """
        parser.add_argument("list", help="ID or name of the list to update")
        parser.add_argument("--color", help="New color for the list (hex code or name)")
        parser.add_argument("--icon", help="New icon identifier for the list")
    
    def execute(self, args: argparse.Namespace) -> int:
        """
        Execute the update colors command.
        
        Args:
            args: Command arguments
            
        Returns:
            Exit code (0 for success)
        """
        try:
            if not args.color and not args.icon:
                print("Error: At least one of --color or --icon must be specified")
                return 1
                
            # Find the list
            list_entity = self._core_manager.find_list(args.list)
            if not list_entity:
                print(f"List not found: {args.list}")
                return 1
            
            # Update the list colors
            if hasattr(self._core_manager, 'update_list_colors'):
                updated_list = self._core_manager.update_list_colors(
                    list_id=list_entity.id,
                    color=args.color,
                    icon=args.icon
                )
                
                print(f"Updated list: {list_entity.name}")
                
                if args.color:
                    print(f"Color set to: {args.color}")
                if args.icon:
                    print(f"Icon set to: {args.icon}")
                    
                return 0
            else:
                print("Error: Core manager does not support updating list colors")
                return 1
        except Exception as e:
            print(f"Error updating list colors: {str(e)}")
            return 1


class AddTaskToListCommand(SimpleCommand):
    """
    Task: tsk_d3a5e976 - Add Container Assignment Command
    Document: refactor/cli/commands/list.py
    dohcount: 1
    
    Purpose:
        Implements a command to add a task to a list container, ensuring
        tasks are properly associated with containers and don't appear
        as orphaned tasks in the container hierarchy display.
    
    Requirements:
        - Must validate both task and list exist before association
        - Must add the task's ID to the list's tasks array
        - Must update the data structure to reflect the association
        - Must handle error cases gracefully
    
    Used By:
        - CLI Users: For manually assigning tasks to lists
        - Scripts: For automating task container assignment
    """
    
    def __init__(self, core_manager: CoreManager):
        """
        Initialize with a core manager.
        
        Args:
            core_manager: The core manager to use for list operations
        """
        super().__init__("add-task", "Add a task to a list")
        self._core_manager = core_manager
    
    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        """
        Configure the parser for add task to list command.
        
        Args:
            parser: The parser to configure
        """
        parser.add_argument("template", help="Path to the template file")
        parser.add_argument("task", help="ID or name of the task to add")
        parser.add_argument("list", help="ID or name of the list to add the task to")
    
    def execute(self, args: argparse.Namespace) -> int:
        """
        Execute the add task to list command.
        
        Args:
            args: Command arguments
            
        Returns:
            Exit code (0 for success)
        """
        try:
            # Make sure the template path is set in the core manager
            self._core_manager.file_path = args.template
            
            # Find the task by ID or name
            task = None
            try:
                task = self._core_manager.get_task(args.task)
            except:
                task = self._core_manager.find_task_by_name(args.task)
                
            if not task:
                print(f"Task not found: {args.task}")
                return 1
                
            # Find the list by ID or name
            list_entity = None
            try:
                list_entity = self._core_manager.get_list(args.list)
            except:
                list_entity = self._core_manager.find_list_by_name(args.list)
                
            if not list_entity:
                print(f"List not found: {args.list}")
                return 1
                
            # Add the task to the list
            try:
                # Check if the task is already in the list
                list_tasks = list_entity.get('tasks', [])
                task_id = task.get('id')
                
                if task_id in list_tasks:
                    print(f"Task '{task.get('name')}' is already in list '{list_entity.get('name')}'")
                    return 0
                
                # Add the task to the list
                self._core_manager.add_task_to_list(task_id, list_entity.get('id'))
                
                print(f"Task '{task.get('name')}' successfully added to list '{list_entity.get('name')}'")
                return 0
            except Exception as e:
                print(f"Error adding task to list: {str(e)}")
                return 1
                
        except Exception as e:
            print(f"Error: {str(e)}")
            return 1


class ListCommand(CompositeCommand):
    """
    List command group.
    
    This command group provides subcommands for list management operations.
    """
    
    def __init__(self, core_manager: CoreManager):
        """
        Initialize with a core manager.
        
        Args:
            core_manager: The core manager to use for list operations
        """
        super().__init__("list", "List management operations")
        
        # Add subcommands
        self.add_subcommand(CreateListCommand(core_manager))
        self.add_subcommand(ShowListCommand(core_manager))
        self.add_subcommand(ListListsCommand(core_manager))
        self.add_subcommand(UpdateListCommand(core_manager))
        self.add_subcommand(DeleteListCommand(core_manager))
        self.add_subcommand(MoveListCommand(core_manager))
        self.add_subcommand(UpdateListColorsCommand(core_manager))
        self.add_subcommand(AddTaskToListCommand(core_manager))


class ListTasksCommand(SimpleCommand):
    """Command for listing tasks."""
    
    def __init__(self, core_manager: CoreManager):
        """
        Initialize the list tasks command.
        
        Args:
            core_manager: Core manager instance
        """
        super().__init__(core_manager)
        
    @property
    def name(self) -> str:
        return "list"
        
    @property
    def description(self) -> str:
        return "List tasks with optional filtering"
        
    def configure_parser(self, parser: ArgumentParser) -> None:
        """
        Configure the argument parser for the list command.
        
        Args:
            parser: Argument parser to configure
        """
        parser.add_argument(
            "template",
            help="The JSON template file to use",
            nargs="?"
        )
        
        parser.add_argument(
            "--status",
            help="Filter by task status",
            choices=["to do", "in progress", "complete", "blocked"],
            default=None
        )
        parser.add_argument(
            "--priority",
            help="Filter by task priority (1-3)",
            type=int,
            choices=[1, 2, 3, 4],
            default=None
        )
        parser.add_argument(
            "--tags",
            help="Filter by tags (comma-separated)",
            default=None
        )
        parser.add_argument(
            "--parent",
            help="Filter by parent ID",
            default=None
        )
        parser.add_argument(
            "--complete",
            help="Include completed tasks",
            action="store_true"
        )
        parser.add_argument(
            "--parent-only",
            help="Show only parent tasks",
            action="store_true"
        )
        parser.add_argument(
            "--hide-orphaned",
            help="Hide orphaned tasks from the display",
            action="store_true"
        )
        parser.add_argument(
            "--task-type",
            help="Filter tasks by task type",
            default=None
        )
        
        # Display methods group
        display_group = parser.add_mutually_exclusive_group()
        display_group.add_argument(
            "--flat",
            help="Display tasks in flat list format",
            action="store_true"
        )
        display_group.add_argument(
            "--tree", 
            help="Display tasks in hierarchical tree view (default)",
            action="store_true"
        )
        display_group.add_argument(
            "--dependency-as-tree",
            help="Organize tasks by dependency relationships",
            action="store_true"
        )
        display_group.add_argument(
            "--organize-by-container",
            help="Organize tasks by list/folder hierarchy",
            action="store_true"
        )
        display_group.add_argument(
            "--no-container",
            help="Disable container organization (same as --flat)",
            action="store_true"
        )
        
        parser.add_argument(
            "--dependency-type",
            help="Dependency relationship type to use for tree organization",
            choices=["depends_on", "blocks"],
            default="depends_on"
        )
        
        parser.add_argument(
            "--show-descriptions",
            help="Show task descriptions",
            action="store_true"
        )
        
        parser.add_argument(
            "--description-length",
            help="Maximum length for displayed descriptions",
            type=int,
            default=100
        )
        
        parser.add_argument(
            "--show-relationships",
            help="Show task relationships",
            action="store_true"
        )
        
        parser.add_argument(
            "--show-comments",
            help="Number of recent comments to show (0 to hide, max 3)",
            type=int,
            default=0
        )
        
        parser.add_argument(
            "--show-id",
            help="Show task IDs",
            action="store_true"
        )
        
        parser.add_argument(
            "--colorize",
            help="Colorize output based on status",
            action="store_true"
        )
        
        parser.add_argument(
            "--show-score",
            help="Show detailed scores for each task",
            action="store_true"
        )
        
        parser.add_argument(
            "--show-tags",
            help="Show task tags (default: enabled)",
            action="store_true",
            default=True
        )
        
        parser.add_argument(
            "--no-tags",
            help="Hide task tags",
            action="store_true"
        )
        
        parser.add_argument(
            "--tag-style",
            help="Style for tag display (default: colored)",
            choices=["brackets", "hash", "colored"],
            default="colored"
        )
        
        parser.add_argument(
            "--show-type-emoji",
            help="Show emoji for task type (default: enabled)",
            action="store_true",
            default=True
        )
        
        parser.add_argument(
            "--no-type-emoji",
            help="Hide task type emoji",
            action="store_true"
        )
        
        # Add sort-by option
        parser.add_argument(
            "--sort-by",
            help="Sort tasks by field",
            choices=["name", "status", "priority", "created", "updated"],
            default=None
        )
        
        # Global arguments (for compatibility)
        parser.add_argument(
            "--trace",
            help=argparse.SUPPRESS,  # Hide from help but accept it
            action="store_true"
        )
        
    def execute(self, args: Namespace) -> None:
        """
        Execute the list command.
        
        Args:
            args: Parsed command arguments
        """
        # Remove direct debugging print statements
        logger = logging.getLogger(__name__)
        logger.debug(f"Starting execute with args: {vars(args)}")
        
        try:
            # Find the template file to use
            template_file = get_template_path(args.template)
            
            if not template_file:
                print("Error: No template file specified and no default template found.", file=sys.stderr)
                print("Please specify a template file or run './cujm init' to create a default template.", file=sys.stderr)
                return 1
            
            # Load the template file
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    template_data = json.load(f)
            except Exception as e:
                print(f"Error loading template file: {e}", file=sys.stderr)
                return 1
            
            # Load data into core manager
            self.core_manager.load_template(template_file)
            
            # Get all tasks
            tasks = template_data.get('tasks', [])
            logger.debug(f"Loaded {len(tasks)} tasks from template")
            
            # Filter by status if provided
            if args.status:
                logging.debug(f"Filtering by status: {args.status}")
                tasks = [t for t in tasks if str(t.get('status', '')).lower() == args.status.lower()]
            elif args.hide_completed:
                logging.debug("Hiding completed tasks")
                tasks = [t for t in tasks if str(t.get('status', '')).lower() != 'complete']
            
            if args.priority:
                tasks = [t for t in tasks if t.get('priority', 0) == args.priority]
            
            if args.tags:
                tag_list = [tag.strip() for tag in args.tags.split(',')]
                tasks = [
                    t for t in tasks 
                    if any(tag.lower() in [t_tag.lower() for t_tag in t.get('tags', [])]
                        for tag in tag_list)
                ]
            
            if args.parent:
                tasks = [t for t in tasks if t.get('parent_id') == args.parent]
            
            if args.parent_only:
                # Only include tasks that are parents (have subtasks)
                parent_ids = set()
                for task in tasks:
                    if task.get('parent_id'):
                        parent_ids.add(task.get('parent_id'))
                tasks = [t for t in tasks if t.get('id') in parent_ids]
            
            if args.task_type:
                tasks = [t for t in tasks if str(t.get('task_type', '')).lower() == args.task_type.lower()]
            
            # Determine display flags
            show_tags = True
            if hasattr(args, 'no_tags') and args.no_tags:
                show_tags = False
                logger.debug("Tags display disabled by --no-tags flag")
            elif hasattr(args, 'show_tags'):
                show_tags = args.show_tags
                logger.debug(f"Tags display set to {show_tags} by --show-tags flag")
            
            show_type_emoji = True
            if hasattr(args, 'no_type_emoji') and args.no_type_emoji:
                show_type_emoji = False
                logger.debug("Type emoji display disabled by --no-type-emoji flag")
            elif hasattr(args, 'show_type_emoji'):
                show_type_emoji = args.show_type_emoji
                logger.debug(f"Type emoji display set to {show_type_emoji} by --show-type-emoji flag")
            
            # Create a FormatOptions object for better parameter management
            logger.debug(f"Creating FormatOptions with show_id={getattr(args, 'show_id', False)}")
            format_options = FormatOptions(
                colorize_output=getattr(args, 'colorize', True),
                show_ids=getattr(args, 'show_id', False),
                show_score=getattr(args, 'show_score', False),
                show_tags=show_tags,
                tag_style=getattr(args, 'tag_style', 'colored'),
                show_type_emoji=show_type_emoji,
                show_descriptions=getattr(args, 'show_descriptions', False),
                show_dates=False,  # Default value
                show_comments=getattr(args, 'show_comments', 0),
                show_relationships=getattr(args, 'show_relationships', False),
                include_completed=getattr(args, 'complete', False),
                hide_orphaned=getattr(args, 'hide_orphaned', False),
                description_length=getattr(args, 'description_length', 100)
            )
            
            # Add debug logging to verify show_ids value
            logger.debug(f"FormatOptions initialized with show_ids={format_options.show_ids}")
            
            # Format and display tasks
            # Force the use of flat display if flat flag is set
            use_flat = getattr(args, 'flat', False)
            use_no_container = getattr(args, 'no_container', False)
            
            # TEMPORARY WORKAROUND: Force flat display when --show-id is used
            if getattr(args, 'show_id', False):
                logger.debug("WORKAROUND: Forcing flat display because --show-id is used")
                use_flat = True
                print("Note: Using flat display mode with --show-id flag")
                
            logger.debug(f"flat={use_flat}, no_container={use_no_container}")
            
            # Sort tasks if sort-by parameter provided
            if hasattr(args, 'sort_by') and args.sort_by:
                logger.debug(f"Sorting by: {args.sort_by}")
                
                if args.sort_by == "name":
                    tasks = sorted(tasks, key=lambda t: t.get('name', '').lower())
                elif args.sort_by == "status":
                    # Ensure status is converted to string before sorting
                    tasks = sorted(tasks, key=lambda t: str(t.get('status', '')).lower())
                elif args.sort_by == "priority":
                    tasks = sorted(tasks, key=lambda t: int(t.get('priority', 4)))
                elif args.sort_by == "created":
                    tasks = sorted(tasks, key=lambda t: t.get('date_created', 0))
                elif args.sort_by == "updated":
                    tasks = sorted(tasks, key=lambda t: t.get('date_updated', 0))
                    
                logger.debug(f"After sorting, first task name: {tasks[0].get('name', '') if tasks else 'No tasks'}")
            
            if use_flat or use_no_container:
                # Use proper logging instead of debug prints
                logger.debug(f"Using flat display format. Task count: {len(tasks)}")
                
                if not tasks:
                    print("No tasks found matching the criteria.")
                    return 0
                
                # Flat list display using format_task_list
                try:
                    # Import the function directly to ensure we have the right version
                    from refactor.cli.commands.utils import format_task_list
                    
                    # Debug logging of tasks
                    if len(tasks) > 0:
                        first_task = tasks[0]
                        logger.debug(f"Sample task: ID={first_task.get('id')}, Name={first_task.get('name')}")
                    
                    logger.debug(f"Calling format_task_list with show_ids={format_options.show_ids}")
                    formatted_output = format_task_list(
                        tasks=tasks,
                        show_ids=format_options.show_ids,
                        truncate=True,
                        truncate_length=format_options.description_length,
                        colorize=format_options.colorize_output,
                        show_tags=format_options.show_tags,
                        tag_style=format_options.tag_style,
                        show_type_emoji=format_options.show_type_emoji,
                        show_descriptions=format_options.show_descriptions,
                        show_score=format_options.show_score,
                        id_at_beginning=True  # Always show IDs at the beginning in flat mode
                    )
                    
                    # Check if we got any output
                    if not formatted_output or formatted_output == "No tasks found.":
                        print("No tasks matching the criteria were found.")
                    else:
                        logger.debug(f"Got formatted output, length = {len(formatted_output)}")
                        print(formatted_output)
                except Exception as e:
                    logger.error(f"Error in format_task_list: {str(e)}")
                    import traceback
                    traceback_str = traceback.format_exc()
                    logger.error(f"Full traceback:\n{traceback_str}")
                    print(f"Error formatting tasks: {str(e)}")
            else:
                # Tree display
                organize_by_container = getattr(args, 'organize_by_container', True)
                dependency_as_tree = getattr(args, 'dependency_as_tree', False)
                
                if organize_by_container:
                    # Use container hierarchy
                    if args.trace:
                        logger.debug(f"Formatting {len(tasks)} tasks with container hierarchy")
                        logger.debug(f"Using show_ids={args.show_id} in format_options")
                    
                    formatted_output = format_container_hierarchy(
                        tasks=tasks,
                        options=format_options,
                        organize_by_container=organize_by_container,
                        dependency_as_tree=dependency_as_tree,
                        dependency_type=getattr(args, 'dependency_type', 'depends_on'),
                        trace=args.trace  # Pass trace parameter to enable detailed error logging
                    )
                    print(formatted_output)
                else:
                    # Use regular task hierarchy
                    try:
                        formatted_output = format_task_hierarchy(
                            tasks=tasks,
                            colorize_output=format_options.colorize_output,
                            show_score=format_options.show_score,
                            show_tags=format_options.show_tags,
                            tag_style=format_options.tag_style,
                            show_ids=format_options.show_ids,
                            show_descriptions=format_options.show_descriptions,
                            description_length=format_options.description_length,
                            show_relationships=format_options.show_relationships,
                            show_comments=format_options.show_comments,
                            organize_by_container=organize_by_container,
                            dependency_as_tree=dependency_as_tree,
                            dependency_type=getattr(args, 'dependency_type', 'depends_on'),
                            include_completed=format_options.include_completed,
                            hide_orphaned=format_options.hide_orphaned,
                            show_type_emoji=format_options.show_type_emoji
                        )
                        
                        print(formatted_output)
                    except Exception as e:
                        logger.error(f"Error formatting task hierarchy: {str(e)}")
                        import traceback
                        traceback_str = traceback.format_exc()
                        logger.error(f"Full traceback:\n{traceback_str}")
                        print(f"Error formatting tasks: {str(e)}")
                        print("Falling back to flat list display")
                        
                        # Fall back to flat display
                        try:
                            from refactor.cli.commands.utils import format_task_list
                            
                            formatted_output = format_task_list(
                                tasks=tasks,
                                show_ids=format_options.show_ids,
                                truncate=True,
                                truncate_length=format_options.description_length,
                                colorize=format_options.colorize_output,
                                show_tags=format_options.show_tags,
                                tag_style=format_options.tag_style,
                                show_type_emoji=format_options.show_type_emoji,
                                show_descriptions=format_options.show_descriptions,
                                show_score=format_options.show_score,
                                id_at_beginning=True  # Always show IDs at the beginning in flat mode
                            )
                            
                            print(formatted_output)
                        except Exception as e2:
                            logger.error(f"Error in fallback flat display: {str(e2)}")
                            print(f"Error in fallback display: {str(e2)}")
            
            return 0
            
        except Exception as e:
            logger.error(f"Error listing tasks: {str(e)}")
            import traceback
            traceback_str = traceback.format_exc()
            logger.error(f"Full traceback:\n{traceback_str}")
            print(f"Error: {str(e)}")
            return 1 