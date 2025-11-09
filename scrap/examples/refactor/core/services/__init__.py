"""
Services Package

This package contains service classes that implement the business logic of the application.
Each service encapsulates operations related to a specific domain entity or functionality,
and orchestrates interactions between repositories, entities, and validation rules.

Services:
    - TaskService: Manages task-related operations and business logic
    - DocumentService: Manages documentation tasks and their relationships
    - DocumentSectionService: Manages document section operations including ordering and content handling
    - RelationshipService: Manages task relationships including dependency and documentation relationships
    - ChecklistService: Manages task checklists and checklist items
    - SpaceService: Manages space-related operations
    - FolderService: Manages folder-related operations
    - ListService: Manages list-related operations
    - QueryService: Manages data querying operations
    - SearchService: Manages search operations
    - StatusService: Manages task status operations
    - PluginService: Manages plugin operations and extensions
"""

from refactor.core.services.task_service import TaskService
from refactor.core.services.document_service import DocumentService
from refactor.core.services.document_section_service import DocumentSectionService
from refactor.core.services.relationship_service import RelationshipService
from refactor.core.services.checklist_service import ChecklistService
from refactor.core.services.space_service import SpaceService
from refactor.core.services.folder_service import FolderService
from refactor.core.services.list_service import ListService
from refactor.core.services.query_service import QueryService
from refactor.core.services.search_service import SearchService
from refactor.core.services.status_service import StatusService
from refactor.core.services.plugin_service import PluginService

__all__ = [
    'TaskService',
    'DocumentService',
    'DocumentSectionService',
    'RelationshipService',
    'ChecklistService',
    'SpaceService',
    'FolderService',
    'ListService',
    'QueryService',
    'SearchService',
    'StatusService',
    'PluginService',
] 