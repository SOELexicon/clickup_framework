"""
Folder Commands Implementation

This module provides command implementations for folder-related operations
such as creating, listing, and showing folders.
"""
from argparse import ArgumentParser, Namespace
from typing import Dict, List, Optional

from refactor.cli.commands.base import BaseCommand, CompositeCommand, SimpleCommand
from refactor.core.interfaces.core_manager import CoreManager


class CreateFolderCommand(SimpleCommand):
    """Command for creating a new folder."""
    
    def __init__(self, core_manager: CoreManager):
        """
        Initialize with a core manager.
        
        Args:
            core_manager: The core manager to use for task operations
        """
        super().__init__("create", "Create a new folder in a space")
        self._core_manager = core_manager
    
    def configure_parser(self, parser: ArgumentParser) -> None:
        """
        Configure the parser for create folder command.
        
        Args:
            parser: The parser to configure
        """
        parser.add_argument("space", help="ID or name of the space")
        parser.add_argument("name", help="Name of the folder")
        parser.add_argument("--description", "-d", help="Description of the folder")
        parser.add_argument("--color", help="Color for the folder (hex code or name)")
        parser.add_argument("--icon", help="Icon identifier for the folder")
    
    def execute(self, args: Namespace) -> int:
        """
        Execute the create folder command.
        
        Args:
            args: Command arguments
            
        Returns:
            Exit code (0 for success)
        """
        try:
            # Try to get space by ID first, then by name
            space_id = args.space
            try:
                space = self._core_manager.get_space(space_id)
                space_id = space.id
                space_name = space.name
            except:
                space = self._core_manager.get_space_by_name(space_id)
                if space:
                    space_id = space.id
                    space_name = space.name
                else:
                    print(f"Space not found: {args.space}")
                    return 1
            
            # Create the folder
            folder = self._core_manager.create_folder(
                space_id=space_id,
                name=args.name,
                description=args.description or "",
                color=args.color,
                icon=args.icon
            )
            
            print(f"Folder created: {folder.name} (ID: {folder.id}) in space '{space_name}'")
            
            # Display color and icon if provided
            if hasattr(folder, 'color') and folder.color:
                print(f"Color: {folder.color}")
            if hasattr(folder, 'icon') and folder.icon:
                print(f"Icon: {folder.icon}")
                
            return 0
        except Exception as e:
            print(f"Error creating folder: {str(e)}")
            return 1


class ListFoldersCommand(SimpleCommand):
    """Command for listing folders in a space."""
    
    def __init__(self, core_manager: CoreManager):
        """
        Initialize with a core manager.
        
        Args:
            core_manager: The core manager to use for task operations
        """
        super().__init__("list", "List folders in a space")
        self._core_manager = core_manager
    
    def configure_parser(self, parser: ArgumentParser) -> None:
        """
        Configure the parser for list folders command.
        
        Args:
            parser: The parser to configure
        """
        parser.add_argument("space", help="ID or name of the space")
        parser.add_argument(
            "--details", 
            action="store_true",
            help="Show detailed information including lists"
        )
    
    def execute(self, args: Namespace) -> int:
        """
        Execute the list folders command.
        
        Args:
            args: Command arguments
            
        Returns:
            Exit code (0 for success)
        """
        try:
            # Try to get space by ID first, then by name
            space_id = args.space
            try:
                space = self._core_manager.get_space(space_id)
                space_id = space.id
                space_name = space.name
            except:
                space = self._core_manager.get_space_by_name(space_id)
                if space:
                    space_id = space.id
                    space_name = space.name
                else:
                    print(f"Space not found: {args.space}")
                    return 1
            
            # Get folders in the space
            folders = self._core_manager.get_folders(space_id)
            
            if not folders:
                print(f"No folders found in space '{space_name}'")
                return 0
            
            print(f"Folders in space '{space_name}' (ID: {space_id}):\n")
            
            for folder in folders:
                print(f"Folder: {folder.name}")
                print(f"ID: {folder.id}")
                
                if args.details:
                    if hasattr(folder, 'description') and folder.description:
                        print(f"Description: {folder.description}")
                    
                    # Get lists in the folder
                    lists = self._core_manager.get_lists(folder.id)
                    if lists:
                        print(f"Lists ({len(lists)}):")
                        for list_item in lists:
                            print(f"  - {list_item.name} (ID: {list_item.id})")
                
                print()
            
            return 0
        except Exception as e:
            print(f"Error listing folders: {str(e)}")
            return 1


class ShowFolderCommand(SimpleCommand):
    """Command for showing folder details."""
    
    def __init__(self, core_manager: CoreManager):
        """
        Initialize with a core manager.
        
        Args:
            core_manager: The core manager to use for task operations
        """
        super().__init__("show", "Show folder details")
        self._core_manager = core_manager
    
    def configure_parser(self, parser: ArgumentParser) -> None:
        """
        Configure the parser for show folder command.
        
        Args:
            parser: The parser to configure
        """
        parser.add_argument("folder", help="ID or name of the folder to show")
    
    def execute(self, args: Namespace) -> int:
        """
        Execute the show folder command.
        
        Args:
            args: Command arguments
            
        Returns:
            Exit code (0 for success)
        """
        try:
            # Try to get folder by ID first, then by name
            folder = None
            try:
                folder = self._core_manager.get_folder(args.folder)
            except:
                folder = self._core_manager.get_folder_by_name(args.folder)
                
            if not folder:
                print(f"Folder not found: {args.folder}")
                return 1
                
            # Display folder information
            print(f"Folder: {folder.name}")
            print(f"ID: {folder.id}")
            print(f"Space ID: {folder.space_id}")
            
            if hasattr(folder, 'description') and folder.description:
                print(f"Description: {folder.description}")
                
            # Display color and icon if they exist
            if hasattr(folder, 'color') and folder.color:
                print(f"Color: {folder.color}")
            if hasattr(folder, 'icon') and folder.icon:
                print(f"Icon: {folder.icon}")
            
            # Get space information
            try:
                space = self._core_manager.get_space(folder.space_id)
                print(f"Space: {space.name} (ID: {space.id})")
            except:
                print(f"Space: Unknown (ID: {folder.space_id})")
            
            # Get lists in the folder
            lists = self._core_manager.get_lists(folder.id)
            if lists:
                print(f"\nLists ({len(lists)}):")
                for list_item in lists:
                    print(f"  - {list_item.name} (ID: {list_item.id})")
                    
                    # Get task count for the list (if the method exists)
                    if hasattr(self._core_manager, 'get_task_count_in_list'):
                        try:
                            task_count = self._core_manager.get_task_count_in_list(list_item.id)
                            print(f"    Tasks: {task_count}")
                        except:
                            pass
            
            return 0
        except Exception as e:
            print(f"Error showing folder: {str(e)}")
            return 1


class DeleteFolderCommand(SimpleCommand):
    """Command for deleting a folder."""
    
    def __init__(self, core_manager: CoreManager):
        """
        Initialize with a core manager.
        
        Args:
            core_manager: The core manager to use for task operations
        """
        super().__init__("delete", "Delete a folder")
        self._core_manager = core_manager
    
    def configure_parser(self, parser: ArgumentParser) -> None:
        """
        Configure the parser for delete folder command.
        
        Args:
            parser: The parser to configure
        """
        parser.add_argument("folder", help="ID or name of the folder to delete")
        parser.add_argument(
            "--force", 
            action="store_true",
            help="Force deletion even if the folder contains lists"
        )
    
    def execute(self, args: Namespace) -> int:
        """
        Execute the delete folder command.
        
        Args:
            args: Command arguments
            
        Returns:
            Exit code (0 for success)
        """
        try:
            # Try to get folder by ID first, then by name
            folder_id = args.folder
            try:
                folder = self._core_manager.get_folder(folder_id)
                folder_id = folder.id
                folder_name = folder.name
            except:
                folder = self._core_manager.get_folder_by_name(folder_id)
                if folder:
                    folder_id = folder.id
                    folder_name = folder.name
                else:
                    print(f"Folder not found: {args.folder}")
                    return 1
            
            # Check if the folder has lists
            if not args.force:
                lists = self._core_manager.get_lists(folder_id)
                if lists:
                    print(f"Folder '{folder_name}' contains {len(lists)} lists.")
                    print("Use --force to delete the folder and all its contents.")
                    return 1
            
            # Ask for confirmation
            confirm = input(f"Are you sure you want to delete folder '{folder_name}'? (y/N): ")
            if confirm.lower() != 'y':
                print("Deletion cancelled")
                return 0
            
            # Delete the folder
            result = self._core_manager.delete_folder(folder_id)
            
            if result:
                print(f"Folder '{folder_name}' has been deleted")
                return 0
            else:
                print(f"Failed to delete folder")
                return 1
        except Exception as e:
            print(f"Error deleting folder: {str(e)}")
            return 1


class UpdateFolderColorsCommand(SimpleCommand):
    """Command for updating folder colors and icons."""
    
    def __init__(self, core_manager: CoreManager):
        """
        Initialize with a core manager.
        
        Args:
            core_manager: The core manager to use for task operations
        """
        super().__init__("update-colors", "Update color and icon for a folder")
        self._core_manager = core_manager
    
    def configure_parser(self, parser: ArgumentParser) -> None:
        """
        Configure the parser for update colors command.
        
        Args:
            parser: The parser to configure
        """
        parser.add_argument("folder", help="ID or name of the folder to update")
        parser.add_argument("--color", help="New color for the folder (hex code or name)")
        parser.add_argument("--icon", help="New icon identifier for the folder")
    
    def execute(self, args: Namespace) -> int:
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
                
            # Try to get folder by ID first, then by name
            folder_id = args.folder
            try:
                folder = self._core_manager.get_folder(folder_id)
                folder_id = folder.id
                folder_name = folder.name
            except:
                folder = self._core_manager.get_folder_by_name(folder_id)
                if folder:
                    folder_id = folder.id
                    folder_name = folder.name
                else:
                    print(f"Folder not found: {args.folder}")
                    return 1
            
            # Update the folder colors
            if hasattr(self._core_manager, 'update_folder_colors'):
                updated_folder = self._core_manager.update_folder_colors(
                    folder_id=folder_id,
                    color=args.color,
                    icon=args.icon
                )
                
                print(f"Updated folder: {folder_name}")
                
                if args.color:
                    print(f"Color set to: {args.color}")
                if args.icon:
                    print(f"Icon set to: {args.icon}")
                    
                return 0
            else:
                print("Error: Core manager does not support updating folder colors")
                return 1
        except Exception as e:
            print(f"Error updating folder colors: {str(e)}")
            return 1


class AddTaskToFolderCommand(SimpleCommand):
    """
    Task: tsk_d3a5e976 - Add Container Assignment Command
    Document: refactor/cli/commands/folder.py
    dohcount: 1
    
    Purpose:
        Implements a command to add a task to a folder container, ensuring
        tasks are properly associated with containers and don't appear
        as orphaned tasks in the container hierarchy display.
    
    Requirements:
        - Must validate both task and folder exist before association
        - Must add the task's ID to the folder's tasks array
        - Must update the data structure to reflect the association
        - Must handle error cases gracefully
    
    Used By:
        - CLI Users: For manually assigning tasks to folders
        - Scripts: For automating task container assignment
    """
    
    def __init__(self, core_manager: CoreManager):
        """
        Initialize with a core manager.
        
        Args:
            core_manager: The core manager to use for folder operations
        """
        super().__init__("add-task", "Add a task to a folder")
        self._core_manager = core_manager
    
    def configure_parser(self, parser: ArgumentParser) -> None:
        """
        Configure the parser for add task to folder command.
        
        Args:
            parser: The parser to configure
        """
        parser.add_argument("template", help="Path to the template file")
        parser.add_argument("task", help="ID or name of the task to add")
        parser.add_argument("folder", help="ID or name of the folder to add the task to")
    
    def execute(self, args: Namespace) -> int:
        """
        Execute the add task to folder command.
        
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
                
            # Find the folder by ID or name
            folder = None
            try:
                folder = self._core_manager.get_folder(args.folder)
            except:
                folder = self._core_manager.find_folder_by_name(args.folder)
                
            if not folder:
                print(f"Folder not found: {args.folder}")
                return 1
                
            # Add the task to the folder
            try:
                # Check if the task is already in the folder
                folder_tasks = folder.get('tasks', [])
                task_id = task.get('id')
                
                if task_id in folder_tasks:
                    print(f"Task '{task.get('name')}' is already in folder '{folder.get('name')}'")
                    return 0
                
                # If folder doesn't have a tasks array, create one
                if 'tasks' not in folder:
                    folder['tasks'] = []
                
                # Add the task to the folder
                folder['tasks'].append(task_id)
                
                # Save the changes
                self._core_manager.save()
                
                print(f"Task '{task.get('name')}' successfully added to folder '{folder.get('name')}'")
                return 0
            except Exception as e:
                print(f"Error adding task to folder: {str(e)}")
                return 1
                
        except Exception as e:
            print(f"Error: {str(e)}")
            return 1


class FolderCommand(CompositeCommand):
    """
    Folder command group.
    
    This command group provides subcommands for folder operations.
    """
    
    def __init__(self, core_manager: CoreManager):
        """
        Initialize with a core manager.
        
        Args:
            core_manager: The core manager to use for task operations
        """
        super().__init__("folder", "Folder operations")
        
        # Add subcommands
        self.add_subcommand(CreateFolderCommand(core_manager))
        self.add_subcommand(ListFoldersCommand(core_manager))
        self.add_subcommand(ShowFolderCommand(core_manager))
        self.add_subcommand(DeleteFolderCommand(core_manager))
        self.add_subcommand(UpdateFolderColorsCommand(core_manager))
        self.add_subcommand(AddTaskToFolderCommand(core_manager)) 