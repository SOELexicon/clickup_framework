"""
Task: tsk_d3a5e976 - Add Container Assignment Command
Document: refactor/cli/commands/container.py
dohcount: 1

Related Tasks:
    - tsk_d3a5e976 - Add Container Assignment Command (current)
    - tsk_4974e964 - Fix Comment Display in CLI (related)
    - tsk_1877feba - Fix Description Newline Parsing (related)
    - tsk_d3c2cc47 - Fix Relationship Display in CLI (related)

Purpose:
    Implements commands for assigning tasks to containers (lists, folders, spaces)
    to ensure tasks appear in their proper location in the container hierarchy
    and don't show up as orphaned tasks when using the --organize-by-container flag.

Requirements:
    - Must validate both task and container exist before association
    - Must handle adding tasks to lists, folders, and spaces
    - Must update the data structure to reflect the association
    - Must handle error cases gracefully
    - Must provide clear feedback to the user
"""
from argparse import ArgumentParser, Namespace
from typing import Dict, List, Any, Optional, Union
import logging

from refactor.cli.commands.base import BaseCommand, CompositeCommand, SimpleCommand
from refactor.core.interfaces.core_manager import CoreManager

# Configure logger
logger = logging.getLogger(__name__)


class AssignTaskCommand(SimpleCommand):
    """Command for assigning tasks to containers."""
    
    def __init__(self, core_manager: CoreManager):
        """
        Initialize with a core manager.
        
        Args:
            core_manager: The core manager to use for operations
        """
        super().__init__("assign-task", "Assign a task to a container (list, folder, or space)")
        self._core_manager = core_manager
    
    def configure_parser(self, parser: ArgumentParser) -> None:
        """
        Task: tsk_ff8e47b1 - Update Task Entity with Parent Tracking
        Document: refactor/cli/commands/container.py
        dohcount: 1
        
        Used By:
            - CLI: For configuring command arguments
            
        Purpose:
            Configures the argument parser for the assign-task command,
            defining required and optional arguments.
            
        Requirements:
            - Must include template, task, and container as required arguments
            - Must provide clear help text for all arguments
            - Must include force flag for reassignment scenarios
            
        Args:
            parser: The parser to configure
        """
        parser.add_argument("template", help="Path to the template file")
        parser.add_argument("task", help="ID or name of the task to assign")
        parser.add_argument("container", help="ID or name of the container")
        parser.add_argument("--type", choices=["list", "folder", "space"], 
                           default="list", help="Type of container (default: list)")
        parser.add_argument("--force", action="store_true",
                           help="Force reassignment even if task is already in another container")
    
    def execute(self, args: Namespace) -> int:
        """
        Task: tsk_ff8e47b1 - Update Task Entity with Parent Tracking
        Document: refactor/cli/commands/container.py
        dohcount: 2
        
        Used By:
            - CLI: Directly executed by users for container assignment
            
        Purpose:
            Executes the assign task command to associate a task with a container,
            updating bidirectional relationships and handling container-specific logic.
            
        Requirements:
            - Must validate both task and container existence
            - Must update the container_id field on the task
            - Must handle different container types (list, folder, space)
            - Must provide clear user feedback
            
        Args:
            args: Command arguments
            
        Returns:
            Exit code (0 for success)
        """
        try:
            # Initialize the core manager with the template path
            self._core_manager.initialize(args.template)
            
            # Find the task by ID or name
            task = None
            try:
                # Try to find the task directly through core manager
                for t in self._core_manager.data.get("tasks", []):
                    if t.get("id") == args.task or t.get("name") == args.task:
                        task = t
                        break
            except Exception as e:
                print(f"Error finding task: {str(e)}")
                return 1
                
            if not task:
                print(f"Task not found: {args.task}")
                return 1
            
            task_id = task.get("id")
            task_name = task.get("name", "Unknown Task")
            
            # Check if task already has a container and force is not enabled
            force = getattr(args, 'force', False)
            
            # Process based on container type
            if args.type == "list":
                # Find the list
                list_obj = None
                for lst in self._core_manager.data.get("lists", []):
                    if lst.get("id") == args.container or lst.get("name") == args.container:
                        list_obj = lst
                        break
                    
                if not list_obj:
                    print(f"List not found: {args.container}")
                    return 1
                
                list_id = list_obj.get("id")
                list_name = list_obj.get("name", "Unknown List")
                
                # Add the task to the list using the updated method with force flag
                try:
                    self._core_manager.add_task_to_list(task_id, list_id, force)
                    print(f"Task '{task_name}' successfully assigned to list '{list_name}'")
                    self._core_manager.save()
                    return 0
                except Exception as e:
                    print(f"Error assigning task to list: {str(e)}")
                    return 1
                    
            elif args.type == "folder":
                # Find the folder
                folder = None
                for fld in self._core_manager.data.get("folders", []):
                    if fld.get("id") == args.container or fld.get("name") == args.container:
                        folder = fld
                        break
                    
                if not folder:
                    print(f"Folder not found: {args.container}")
                    return 1
                
                folder_id = folder.get("id")
                folder_name = folder.get("name", "Unknown Folder")
                
                # Update task's container_id to the folder
                task["container_id"] = folder_id
                
                # If folder doesn't have a tasks array, create one
                if "tasks" not in folder:
                    folder["tasks"] = []
                
                # Add task to folder if not already there
                if task_id not in folder["tasks"]:
                    folder["tasks"].append(task_id)
                
                self._core_manager.save()
                print(f"Task '{task_name}' successfully assigned to folder '{folder_name}'")
                return 0
                    
            elif args.type == "space":
                # Find the space
                space = None
                for spc in self._core_manager.data.get("spaces", []):
                    if spc.get("id") == args.container or spc.get("name") == args.container:
                        space = spc
                        break
                    
                if not space:
                    print(f"Space not found: {args.container}")
                    return 1
                
                space_id = space.get("id")
                space_name = space.get("name", "Unknown Space")
                
                # Update task's container_id to the space
                task["container_id"] = space_id
                
                # If space doesn't have a tasks array, create one
                if "tasks" not in space:
                    space["tasks"] = []
                
                # Add task to space if not already there
                if task_id not in space["tasks"]:
                    space["tasks"].append(task_id)
                
                self._core_manager.save()
                print(f"Task '{task_name}' successfully assigned to space '{space_name}'")
                return 0
            
            print(f"Unknown container type: {args.type}")
            return 1
                
        except Exception as e:
            print(f"Error: {str(e)}")
            return 1


class ListContainersCommand(SimpleCommand):
    """Command for listing all containers."""
    
    def __init__(self, core_manager: CoreManager):
        """
        Initialize with a core manager.
        
        Args:
            core_manager: The core manager to use for operations
        """
        super().__init__("list", "List all containers (spaces, folders, lists)")
        self._core_manager = core_manager
    
    def configure_parser(self, parser: ArgumentParser) -> None:
        """
        Configure the argument parser for the list command.
        
        Args:
            parser: The parser to configure
        """
        parser.add_argument("template", help="Path to the template file")
        parser.add_argument("--type", choices=["all", "spaces", "folders", "lists"], 
                           default="all", help="Type of containers to list (default: all)")
        parser.add_argument("--show-ids", action="store_true",
                           help="Show container IDs")
        parser.add_argument("--flat", action="store_true",
                           help="Show containers in a flat list instead of hierarchical tree")
        parser.add_argument("--colorize", action="store_true", 
                           help="Colorize the output")
    
    def execute(self, args: Namespace) -> int:
        """
        Execute the list containers command.
        
        Args:
            args: Command arguments
            
        Returns:
            Exit code (0 for success)
        """
        try:
            # Initialize the core manager with the template path
            self._core_manager.initialize(args.template)
            
            # Get container data
            spaces = self._core_manager.data.get("spaces", [])
            folders = self._core_manager.data.get("folders", [])
            lists = self._core_manager.data.get("lists", [])
            
            # Colorize settings
            colorize_output = args.colorize
            
            if colorize_output:
                from refactor.utils.colors import TextColor, colorize, container_color
                
            # Filter based on type
            if args.type == "spaces":
                folders = []
                lists = []
            elif args.type == "folders":
                spaces = []
                lists = []
            elif args.type == "lists":
                spaces = []
                folders = []
                
            # Build hierarchy maps
            space_to_folders = {}
            folder_to_lists = {}
            
            for folder in folders:
                space_id = folder.get("space_id", "")
                if space_id:
                    if space_id not in space_to_folders:
                        space_to_folders[space_id] = []
                    space_to_folders[space_id].append(folder)
                    
            for lst in lists:
                folder_id = lst.get("folder_id", "")
                if folder_id:
                    if folder_id not in folder_to_lists:
                        folder_to_lists[folder_id] = []
                    folder_to_lists[folder_id].append(lst)
            
            # Display results
            if args.flat:
                # Flat display
                if args.type in ["all", "spaces"]:
                    print("\nSpaces:")
                    for space in spaces:
                        space_id = space.get("id", "")
                        space_name = space.get("name", "Unknown Space")
                        id_display = f" (ID: {space_id})" if args.show_ids else ""
                        
                        if colorize_output:
                            print(f"  {colorize(space_name, container_color(space))}{id_display}")
                        else:
                            print(f"  {space_name}{id_display}")
                
                if args.type in ["all", "folders"]:
                    print("\nFolders:")
                    for folder in folders:
                        folder_id = folder.get("id", "")
                        folder_name = folder.get("name", "Unknown Folder")
                        space_id = folder.get("space_id", "")
                        space_name = ""
                        
                        # Find space name
                        for space in spaces:
                            if space.get("id") == space_id:
                                space_name = space.get("name", "")
                                break
                                
                        id_display = f" (ID: {folder_id})" if args.show_ids else ""
                        space_display = f" - Space: {space_name}" if space_name else ""
                        
                        if colorize_output:
                            print(f"  {colorize(folder_name, container_color(folder))}{id_display}{space_display}")
                        else:
                            print(f"  {folder_name}{id_display}{space_display}")
                
                if args.type in ["all", "lists"]:
                    print("\nLists:")
                    for lst in lists:
                        list_id = lst.get("id", "")
                        list_name = lst.get("name", "Unknown List")
                        folder_id = lst.get("folder_id", "")
                        folder_name = ""
                        
                        # Find folder name
                        for folder in folders:
                            if folder.get("id") == folder_id:
                                folder_name = folder.get("name", "")
                                break
                                
                        id_display = f" (ID: {list_id})" if args.show_ids else ""
                        folder_display = f" - Folder: {folder_name}" if folder_name else ""
                        
                        if colorize_output:
                            print(f"  {colorize(list_name, container_color(lst))}{id_display}{folder_display}")
                        else:
                            print(f"  {list_name}{id_display}{folder_display}")
            else:
                # Tree display
                print("\nContainer Hierarchy:")
                
                for space_idx, space in enumerate(spaces):
                    space_id = space.get("id", "")
                    space_name = space.get("name", "Unknown Space")
                    is_last_space = space_idx == len(spaces) - 1
                    
                    id_display = f" (ID: {space_id})" if args.show_ids else ""
                    
                    # Space line
                    if colorize_output:
                        space_line = f"├─{colorize(space_name, container_color(space))}{id_display}"
                        if is_last_space:
                            space_line = f"└─{colorize(space_name, container_color(space))}{id_display}"
                    else:
                        space_line = f"├─{space_name}{id_display}"
                        if is_last_space:
                            space_line = f"└─{space_name}{id_display}"
                    
                    print(space_line)
                    
                    # Folder lines
                    space_folders = space_to_folders.get(space_id, [])
                    for folder_idx, folder in enumerate(space_folders):
                        folder_id = folder.get("id", "")
                        folder_name = folder.get("name", "Unknown Folder")
                        is_last_folder = folder_idx == len(space_folders) - 1
                        
                        id_display = f" (ID: {folder_id})" if args.show_ids else ""
                        
                        # Space prefix
                        space_prefix = "  " if is_last_space else "│ "
                        
                        # Folder line
                        if colorize_output:
                            folder_line = f"{space_prefix}├─{colorize(folder_name, container_color(folder))}{id_display}"
                            if is_last_folder:
                                folder_line = f"{space_prefix}└─{colorize(folder_name, container_color(folder))}{id_display}"
                        else:
                            folder_line = f"{space_prefix}├─{folder_name}{id_display}"
                            if is_last_folder:
                                folder_line = f"{space_prefix}└─{folder_name}{id_display}"
                        
                        print(folder_line)
                        
                        # List lines
                        folder_lists = folder_to_lists.get(folder_id, [])
                        for list_idx, lst in enumerate(folder_lists):
                            list_id = lst.get("id", "")
                            list_name = lst.get("name", "Unknown List")
                            is_last_list = list_idx == len(folder_lists) - 1
                            
                            id_display = f" (ID: {list_id})" if args.show_ids else ""
                            
                            # Folder prefix
                            folder_prefix = "  " if is_last_folder else "│ "
                            
                            # List line prefix
                            list_prefix = f"{space_prefix}{folder_prefix}"
                            
                            # List line
                            if colorize_output:
                                list_line = f"{list_prefix}├─{colorize(list_name, container_color(lst))}{id_display}"
                                if is_last_list:
                                    list_line = f"{list_prefix}└─{colorize(list_name, container_color(lst))}{id_display}"
                            else:
                                list_line = f"{list_prefix}├─{list_name}{id_display}"
                                if is_last_list:
                                    list_line = f"{list_prefix}└─{list_name}{id_display}"
                            
                            print(list_line)
            
            return 0
        except Exception as e:
            print(f"Error listing containers: {str(e)}")
            return 1


class ContainerCommand(CompositeCommand):
    """Command for managing container operations."""
    
    def __init__(self, core_manager: CoreManager):
        """
        Initialize with a core manager.
        
        Args:
            core_manager: The core manager to use for operations
        """
        super().__init__("container", "Container management commands")
        self._core_manager = core_manager
        self._subcommands = {}
        self.add_subcommand(AssignTaskCommand(core_manager))
        self.add_subcommand(ListContainersCommand(core_manager))
    
    def add_subcommand(self, command: BaseCommand) -> None:
        """
        Add a subcommand to this command.
        
        Args:
            command: The subcommand to add
        """
        self._subcommands[command.name] = command
    
    def get_aliases(self) -> List[str]:
        """
        Get command aliases.
        
        Returns:
            List of command aliases
        """
        return ["cont"]
    
    def configure_parser(self, parser: ArgumentParser) -> None:
        """
        Configure the parser for container command.
        
        Args:
            parser: The parser to configure
        """
        # Set up subparsers for subcommands
        subparsers = parser.add_subparsers(
            dest="subcommand",
            help="Container subcommand to execute",
            required=True
        )
        
        # Let each subcommand configure its own parser
        for name, command in self._subcommands.items():
            subparser = subparsers.add_parser(name, help=command.description)
            command.configure_parser(subparser)
    
    def execute(self, args: Namespace) -> int:
        """
        Execute the container command.
        
        Args:
            args: Command arguments
            
        Returns:
            Exit code (0 for success)
        """
        # Find and execute the appropriate subcommand
        subcommand = self._subcommands.get(args.subcommand)
        if not subcommand:
            print(f"Unknown subcommand: {args.subcommand}")
            return 1
        
        return subcommand.execute(args) 