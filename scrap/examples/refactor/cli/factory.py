"""
Task: tsk_9b0dc32e - Create Documentation CLI Commands
Document: refactor/cli/factory.py
dohcount: 1

Related Tasks:
    - tsk_708256de - Documentation Features Implementation (parent)
    - tsk_783ad768 - Implement Document Section Management (depends on)
    - tsk_22c4ba4c - Implement Document Relationship Types (depends on)

Used By:
    - CLI Application: For registering available commands

Purpose:
    Updates the CommandFactory to register the new DocumentCommand

Requirements:
    - Must register all command classes for use by the CLI application
    - CRITICAL: All new commands must be registered here

Changes:
    - v1: Added registration for DocumentCommand class
"""

from typing import Dict, List, Optional, Union
import logging

from refactor.cli.command import Command
from refactor.cli.commands import commands
from refactor.core.interfaces.core_manager import CoreManager

logger = logging.getLogger(__name__)


class CommandFactory:
    """Factory for creating command instances."""
    
    def __init__(self):
        """Initialize the command factory."""
        self.commands = {}
    
    def register(self, command: Command) -> None:
        """
        Register a command.
        
        Args:
            command: Command to register
        """
        self.commands[command.name] = command
    
    def get_command(self, name: str) -> Optional[Command]:
        """
        Get a command by name.
        
        Args:
            name: Command name
            
        Returns:
            Command instance or None if not found
        """
        return self.commands.get(name)
    
    def get_all_commands(self) -> Dict[str, Command]:
        """
        Get all registered commands.
        
        Returns:
            Dictionary of commands by name
        """
        return self.commands


def create_commands(core_manager: CoreManager) -> Dict[str, Command]:
    """
    Creates command instances.
    
    Args:
        core_manager: The core manager instance
        
    Returns:
        Dictionary of command instances by name
    """
    # Create command factory
    factory = CommandFactory()
    
    # Register task commands
    factory.register(commands.TaskCommand(core_manager))
    factory.register(commands.CreateTaskCommand(core_manager))
    factory.register(commands.ShowTaskCommand(core_manager))
    factory.register(commands.UpdateTaskCommand(core_manager))
    factory.register(commands.DeleteTaskCommand(core_manager))
    factory.register(commands.CommentTaskCommand(core_manager))
    factory.register(commands.ListTasksCommand(core_manager))
    factory.register(commands.AssignToListCommand(core_manager))
    
    # Register list commands
    factory.register(commands.ListCommand(core_manager))
    factory.register(commands.CreateListCommand(core_manager))
    factory.register(commands.ShowListCommand(core_manager))
    factory.register(commands.ListListsCommand(core_manager))
    factory.register(commands.UpdateListCommand(core_manager))
    factory.register(commands.DeleteListCommand(core_manager))
    factory.register(commands.MoveListCommand(core_manager))
    
    # Register folder commands
    factory.register(commands.FolderCommand(core_manager))
    factory.register(commands.CreateFolderCommand(core_manager))
    factory.register(commands.ListFoldersCommand(core_manager))
    factory.register(commands.ShowFolderCommand(core_manager))
    factory.register(commands.DeleteFolderCommand(core_manager))
    
    # Register space commands
    factory.register(commands.SpaceCommand(core_manager))
    factory.register(commands.CreateSpaceCommand(core_manager))
    factory.register(commands.ListSpacesCommand(core_manager))
    factory.register(commands.ShowSpaceCommand(core_manager))
    factory.register(commands.DeleteSpaceCommand(core_manager))
    
    # Register container commands
    factory.register(commands.ContainerCommand(core_manager))
    
    # Register checklist commands
    factory.register(commands.ChecklistCommand(core_manager))
    factory.register(commands.CreateChecklistCommand(core_manager))
    factory.register(commands.AddChecklistItemCommand(core_manager))
    factory.register(commands.CheckChecklistItemCommand(core_manager))
    factory.register(commands.ListChecklistItemsCommand(core_manager))
    factory.register(commands.DeleteChecklistCommand(core_manager))
    
    # Register relationship commands
    factory.register(commands.RelationshipCommand(core_manager))
    factory.register(commands.ListRelationshipsCommand(core_manager))
    factory.register(commands.AddRelationshipCommand(core_manager))
    factory.register(commands.RemoveRelationshipCommand(core_manager))
    factory.register(commands.CheckCyclesCommand(core_manager))
    factory.register(commands.ValidateRelationshipsCommand(core_manager))
    
    # Register search commands
    factory.register(commands.SearchCommand(core_manager))
    factory.register(commands.SearchTasksCommand(core_manager))
    factory.register(commands.QueryCommand(core_manager))
    factory.register(commands.FindByIdCommand(core_manager))
    
    # Register saved search commands
    factory.register(commands.SavedSearchCommand(core_manager))
    factory.register(commands.SaveSearchCommand(core_manager))
    factory.register(commands.ListSearchesCommand(core_manager))
    factory.register(commands.LoadSearchCommand(core_manager))
    factory.register(commands.UpdateSearchCommand(core_manager))
    factory.register(commands.DeleteSearchCommand(core_manager))
    
    # Register dashboard commands
    factory.register(commands.DashboardCommand(core_manager))
    factory.register(commands.TaskMetricsCommand(core_manager))
    factory.register(commands.CompletionTimelineCommand(core_manager))
    factory.register(commands.TaskHierarchyCommand(core_manager))
    factory.register(commands.InteractiveDashboardCommand(core_manager))
    
    # Register help commands
    factory.register(commands.ListCommandsCommand(core_manager))
    
    # Register document commands
    factory.register(commands.DocumentCommand(core_manager))
    
    # Return all registered commands
    logger.debug(f"Created {len(factory.commands)} commands")
    return factory.get_all_commands() 