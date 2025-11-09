"""
Task: tsk_9b0dc32e - Create Documentation CLI Commands
Document: refactor/cli/commands/__init__.py
dohcount: 1

Related Tasks:
    - tsk_708256de - Documentation Features Implementation (parent)
    - tsk_783ad768 - Implement Document Section Management (depends on)
    - tsk_22c4ba4c - Implement Document Relationship Types (depends on)

Used By:
    - CLI Application: For registering available commands
    - Command Factory: For instantiating commands

Purpose:
    Provides imports and exports for the CLI command modules

Requirements:
    - Must expose all command classes for use by the CLI application
    - CRITICAL: All new commands must be exported here

Changes:
    - v1: Added import and registration for DocumentCommand class
    - v2: Added import and registration for InitCommand class
"""

from .base import (
    BaseCommand,
    CommandContext,
    CompositeCommand,
    HelpCommand,
    MiddlewareCommand,
    SimpleCommand,
)
from .list import (
    ListCommand,
    CreateListCommand,
    ShowListCommand,
    ListListsCommand,
    UpdateListCommand,
    DeleteListCommand,
    MoveListCommand,
    UpdateListColorsCommand,
    AddTaskToListCommand
)
from .relationship import (
    RelationshipCommand,
    ListRelationshipsCommand,
    AddRelationshipCommand,
    RemoveRelationshipCommand,
    CheckCyclesCommand,
    ValidateRelationshipsCommand
)
from .task import (
    TaskCommand,
    CreateTaskCommand,
    ShowTaskCommand,
    UpdateTaskCommand,
    DeleteTaskCommand,
    CommentTaskCommand,
    ListTasksCommand
)
from .checklist import (
    ChecklistCommand,
    CreateChecklistCommand,
    AddChecklistItemCommand,
    CheckChecklistItemCommand,
    ListChecklistItemsCommand,
    DeleteChecklistCommand
)
from .space import (
    SpaceCommand,
    CreateSpaceCommand,
    ListSpacesCommand,
    ShowSpaceCommand,
    DeleteSpaceCommand,
    UpdateSpaceColorsCommand,
    AddTaskToSpaceCommand
)
from .folder import (
    FolderCommand,
    CreateFolderCommand,
    ListFoldersCommand,
    ShowFolderCommand,
    DeleteFolderCommand,
    UpdateFolderColorsCommand,
    AddTaskToFolderCommand
)
from .search import (
    SearchCommand,
    SearchTasksCommand,
    QueryCommand,
    FindByIdCommand
)
from .dashboard import (
    DashboardCommand,
    TaskMetricsCommand,
    CompletionTimelineCommand,
    TaskHierarchyCommand,
    InteractiveDashboardCommand
)
from .help import (
    GenerateHelpCommand,
    ListCommandsCommand,
    CommandDocumenter
)
from .saved_search import (
    SavedSearchCommand,
    SaveSearchCommand,
    ListSearchesCommand,
    LoadSearchCommand,
    UpdateSearchCommand,
    DeleteSearchCommand
)
from .document import (
    DocumentCommand,
    SectionAddCommand,
    SectionUpdateCommand,
    SectionRemoveCommand,
    SectionListCommand,
    SectionReorderCommand
)
from .container import (
    ContainerCommand,
    AssignTaskCommand
)
from .assign import (
    AssignToListCommand
)
from .init import (
    InitCommand
)

__all__ = [
    # Base commands
    'BaseCommand',
    'CommandContext',
    'CompositeCommand',
    'SimpleCommand',
    'MiddlewareCommand',
    'HelpCommand',
    
    # Search commands
    'SearchCommand',
    'SearchTasksCommand',
    'QueryCommand',
    'FindByIdCommand',
    
    # Saved Search commands
    'SavedSearchCommand',
    'SaveSearchCommand',
    'ListSearchesCommand',
    'LoadSearchCommand',
    'UpdateSearchCommand',
    'DeleteSearchCommand',
    
    # Dashboard commands
    'DashboardCommand',
    'TaskMetricsCommand',
    'CompletionTimelineCommand',
    'TaskHierarchyCommand',
    'InteractiveDashboardCommand',
    
    # Init command
    'InitCommand',
    
    # List commands
    'ListCommand',
    'CreateListCommand',
    'ShowListCommand',
    'ListListsCommand',
    'UpdateListCommand',
    'DeleteListCommand',
    'MoveListCommand',
    'UpdateListColorsCommand',
    'AddTaskToListCommand',
    
    # Relationship commands
    'RelationshipCommand',
    'ListRelationshipsCommand',
    'AddRelationshipCommand',
    'RemoveRelationshipCommand',
    'CheckCyclesCommand',
    'ValidateRelationshipsCommand',
    
    # Task commands
    'TaskCommand',
    'CreateTaskCommand',
    'ShowTaskCommand',
    'UpdateTaskCommand',
    'DeleteTaskCommand',
    'CommentTaskCommand',
    'ListTasksCommand',
    'AssignToListCommand',
    
    # Checklist commands
    'ChecklistCommand',
    'CreateChecklistCommand',
    'AddChecklistItemCommand',
    'CheckChecklistItemCommand',
    'ListChecklistItemsCommand',
    'DeleteChecklistCommand',
    
    # Space commands
    'SpaceCommand',
    'CreateSpaceCommand',
    'ListSpacesCommand',
    'ShowSpaceCommand',
    'DeleteSpaceCommand',
    'UpdateSpaceColorsCommand',
    'AddTaskToSpaceCommand',
    
    # Folder commands
    'FolderCommand',
    'CreateFolderCommand',
    'ListFoldersCommand',
    'ShowFolderCommand',
    'DeleteFolderCommand',
    'UpdateFolderColorsCommand',
    'AddTaskToFolderCommand',
    
    # Help commands
    'GenerateHelpCommand',
    'ListCommandsCommand',
    'CommandDocumenter',
    
    # Document commands
    'DocumentCommand',
    'SectionAddCommand',
    'SectionUpdateCommand',
    'SectionRemoveCommand',
    'SectionListCommand',
    'SectionReorderCommand',
    
    # Container commands
    'ContainerCommand',
    'AssignTaskCommand'
] 