"""
Space Commands Implementation

This module provides command implementations for space-related operations
such as creating, listing, and showing spaces.
"""
from argparse import ArgumentParser, Namespace
from typing import Dict, List, Optional

from refactor.cli.commands.base import BaseCommand, CompositeCommand, SimpleCommand
from refactor.core.interfaces.core_manager import CoreManager


class CreateSpaceCommand(SimpleCommand):
    """Command for creating a new space."""
    
    def __init__(self, core_manager: CoreManager):
        """
        Initialize with a core manager.
        
        Args:
            core_manager: The core manager to use for task operations
        """
        super().__init__("create", "Create a new space")
        self._core_manager = core_manager
    
    def configure_parser(self, parser: ArgumentParser) -> None:
        """
        Configure the parser for create space command.
        
        Args:
            parser: The parser to configure
        """
        parser.add_argument("name", help="Name of the space")
        parser.add_argument("--description", "-d", help="Description of the space")
        parser.add_argument("--color", help="Color for the space (hex code or name)")
        parser.add_argument("--icon", help="Icon identifier for the space")
    
    def execute(self, args: Namespace) -> int:
        """
        Execute the create space command.
        
        Args:
            args: Command arguments
            
        Returns:
            Exit code (0 for success)
        """
        try:
            # Create the space
            space = self._core_manager.create_space(
                name=args.name,
                description=args.description or "",
                color=args.color,
                icon=args.icon
            )
            
            print(f"Space created: {space.name} (ID: {space.id})")
            
            # Display color and icon if provided
            if hasattr(space, 'color') and space.color:
                print(f"Color: {space.color}")
            if hasattr(space, 'icon') and space.icon:
                print(f"Icon: {space.icon}")
                
            return 0
        except Exception as e:
            print(f"Error creating space: {str(e)}")
            return 1


class ListSpacesCommand(SimpleCommand):
    """Command for listing all spaces."""
    
    def __init__(self, core_manager: CoreManager):
        """
        Initialize with a core manager.
        
        Args:
            core_manager: The core manager to use for task operations
        """
        super().__init__("list", "List all spaces")
        self._core_manager = core_manager
    
    def configure_parser(self, parser: ArgumentParser) -> None:
        """
        Configure the parser for list spaces command.
        
        Args:
            parser: The parser to configure
        """
        parser.add_argument(
            "--details", 
            action="store_true",
            help="Show detailed information including folders"
        )
    
    def execute(self, args: Namespace) -> int:
        """
        Execute the list spaces command.
        
        Args:
            args: Command arguments
            
        Returns:
            Exit code (0 for success)
        """
        try:
            # Get all spaces
            spaces = self._core_manager.get_spaces()
            
            if not spaces:
                print("No spaces found")
                return 0
            
            print(f"Found {len(spaces)} spaces:\n")
            
            for space in spaces:
                print(f"Space: {space.name}")
                print(f"ID: {space.id}")
                
                if args.details:
                    if space.description:
                        print(f"Description: {space.description}")
                    
                    # Get folders in the space
                    folders = self._core_manager.get_folders(space.id)
                    if folders:
                        print(f"Folders ({len(folders)}):")
                        for folder in folders:
                            print(f"  - {folder.name} (ID: {folder.id})")
                
                print()
            
            return 0
        except Exception as e:
            print(f"Error listing spaces: {str(e)}")
            return 1


class ShowSpaceCommand(SimpleCommand):
    """Command for showing space details."""
    
    def __init__(self, core_manager: CoreManager):
        """
        Initialize with a core manager.
        
        Args:
            core_manager: The core manager to use for task operations
        """
        super().__init__("show", "Show space details")
        self._core_manager = core_manager
    
    def configure_parser(self, parser: ArgumentParser) -> None:
        """
        Configure the parser for show space command.
        
        Args:
            parser: The parser to configure
        """
        parser.add_argument("space", help="ID or name of the space to show")
    
    def execute(self, args: Namespace) -> int:
        """
        Execute the show space command.
        
        Args:
            args: Command arguments
            
        Returns:
            Exit code (0 for success)
        """
        try:
            # Try to get space by ID first, then by name
            space = None
            try:
                space = self._core_manager.get_space(args.space)
            except:
                space = self._core_manager.get_space_by_name(args.space)
                
            if not space:
                print(f"Space not found: {args.space}")
                return 1
                
            # Display space information
            print(f"Space: {space.name}")
            print(f"ID: {space.id}")
            
            if space.description:
                print(f"Description: {space.description}")
                
            # Display color and icon if they exist
            if hasattr(space, 'color') and space.color:
                print(f"Color: {space.color}")
            if hasattr(space, 'icon') and space.icon:
                print(f"Icon: {space.icon}")
            
            # Get folders in the space
            folders = self._core_manager.get_folders(space.id)
            if folders:
                print(f"\nFolders ({len(folders)}):")
                for folder in folders:
                    print(f"  - {folder.name} (ID: {folder.id})")
                    
                    # Get lists in the folder
                    lists = self._core_manager.get_lists(folder.id)
                    if lists:
                        print(f"    Lists ({len(lists)}):")
                        for list_item in lists:
                            print(f"      - {list_item.name} (ID: {list_item.id})")
            
            return 0
        except Exception as e:
            print(f"Error showing space: {str(e)}")
            return 1


class DeleteSpaceCommand(SimpleCommand):
    """Command for deleting a space."""
    
    def __init__(self, core_manager: CoreManager):
        """
        Initialize with a core manager.
        
        Args:
            core_manager: The core manager to use for task operations
        """
        super().__init__("delete", "Delete a space")
        self._core_manager = core_manager
    
    def configure_parser(self, parser: ArgumentParser) -> None:
        """
        Configure the parser for delete space command.
        
        Args:
            parser: The parser to configure
        """
        parser.add_argument("space", help="ID or name of the space to delete")
        parser.add_argument(
            "--force", 
            action="store_true",
            help="Force deletion even if the space contains folders"
        )
    
    def execute(self, args: Namespace) -> int:
        """
        Execute the delete space command.
        
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
            
            # Check if the space has folders
            if not args.force:
                folders = self._core_manager.get_folders(space_id)
                if folders:
                    print(f"Space '{space_name}' contains {len(folders)} folders.")
                    print("Use --force to delete the space and all its contents.")
                    return 1
            
            # Ask for confirmation
            confirm = input(f"Are you sure you want to delete space '{space_name}'? (y/N): ")
            if confirm.lower() != 'y':
                print("Deletion cancelled")
                return 0
            
            # Delete the space
            result = self._core_manager.delete_space(space_id)
            
            if result:
                print(f"Space '{space_name}' has been deleted")
                return 0
            else:
                print(f"Failed to delete space")
                return 1
        except Exception as e:
            print(f"Error deleting space: {str(e)}")
            return 1


class UpdateSpaceColorsCommand(SimpleCommand):
    """Command for updating space colors and icons."""
    
    def __init__(self, core_manager: CoreManager):
        """
        Initialize with a core manager.
        
        Args:
            core_manager: The core manager to use for task operations
        """
        super().__init__("update-colors", "Update color and icon for a space")
        self._core_manager = core_manager
    
    def configure_parser(self, parser: ArgumentParser) -> None:
        """
        Configure the parser for update colors command.
        
        Args:
            parser: The parser to configure
        """
        parser.add_argument("space", help="ID or name of the space to update")
        parser.add_argument("--color", help="New color for the space (hex code or name)")
        parser.add_argument("--icon", help="New icon identifier for the space")
    
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
            
            # Update the space colors
            if hasattr(self._core_manager, 'update_space_colors'):
                updated_space = self._core_manager.update_space_colors(
                    space_id=space_id,
                    color=args.color,
                    icon=args.icon
                )
                
                print(f"Updated space: {space_name}")
                
                if args.color:
                    print(f"Color set to: {args.color}")
                if args.icon:
                    print(f"Icon set to: {args.icon}")
                    
                return 0
            else:
                print("Error: Core manager does not support updating space colors")
                return 1
        except Exception as e:
            print(f"Error updating space colors: {str(e)}")
            return 1


class AddTaskToSpaceCommand(SimpleCommand):
    """
    Task: tsk_d3a5e976 - Add Container Assignment Command
    Document: refactor/cli/commands/space.py
    dohcount: 1
    
    Purpose:
        Implements a command to add a task to a space container, ensuring
        tasks are properly associated with containers and don't appear
        as orphaned tasks in the container hierarchy display.
    
    Requirements:
        - Must validate both task and space exist before association
        - Must add the task's ID to the space's tasks array
        - Must update the data structure to reflect the association
        - Must handle error cases gracefully
    
    Used By:
        - CLI Users: For manually assigning tasks to spaces
        - Scripts: For automating task container assignment
    """
    
    def __init__(self, core_manager: CoreManager):
        """
        Initialize with a core manager.
        
        Args:
            core_manager: The core manager to use for space operations
        """
        super().__init__("add-task", "Add a task to a space")
        self._core_manager = core_manager
    
    def configure_parser(self, parser: ArgumentParser) -> None:
        """
        Configure the parser for add task to space command.
        
        Args:
            parser: The parser to configure
        """
        parser.add_argument("template", help="Path to the template file")
        parser.add_argument("task", help="ID or name of the task to add")
        parser.add_argument("space", help="ID or name of the space to add the task to")
    
    def execute(self, args: Namespace) -> int:
        """
        Execute the add task to space command.
        
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
                
            # Find the space by ID or name
            space = None
            try:
                space = self._core_manager.get_space(args.space)
            except:
                space = self._core_manager.get_space_by_name(args.space)
                
            if not space:
                print(f"Space not found: {args.space}")
                return 1
                
            # Add the task to the space
            try:
                # Check if the task is already in the space
                space_tasks = space.get('tasks', [])
                task_id = task.get('id')
                
                if task_id in space_tasks:
                    print(f"Task '{task.get('name')}' is already in space '{space.get('name')}'")
                    return 0
                
                # If space doesn't have a tasks array, create one
                if 'tasks' not in space:
                    space['tasks'] = []
                
                # Add the task to the space
                space['tasks'].append(task_id)
                
                # Save the changes
                self._core_manager.save()
                
                print(f"Task '{task.get('name')}' successfully added to space '{space.get('name')}'")
                return 0
            except Exception as e:
                print(f"Error adding task to space: {str(e)}")
                return 1
                
        except Exception as e:
            print(f"Error: {str(e)}")
            return 1


class SpaceCommand(CompositeCommand):
    """
    Space command group.
    
    This command group provides subcommands for space operations.
    """
    
    def __init__(self, core_manager: CoreManager):
        """
        Initialize with a core manager.
        
        Args:
            core_manager: The core manager to use for task operations
        """
        super().__init__("space", "Space operations")
        
        # Add subcommands
        self.add_subcommand(CreateSpaceCommand(core_manager))
        self.add_subcommand(ListSpacesCommand(core_manager))
        self.add_subcommand(ShowSpaceCommand(core_manager))
        self.add_subcommand(DeleteSpaceCommand(core_manager))
        self.add_subcommand(UpdateSpaceColorsCommand(core_manager))
        self.add_subcommand(AddTaskToSpaceCommand(core_manager)) 