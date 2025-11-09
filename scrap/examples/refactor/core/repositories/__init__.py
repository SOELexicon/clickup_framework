"""
Repository module for the ClickUp JSON Manager.

This module provides repository implementations for persisting entities.
"""

from refactor.core.repositories.repository_interface import (
    Repository, ITaskRepository, IListRepository, IFolderRepository, ISpaceRepository
)
from refactor.core.repositories.json_repository import JsonRepository
from refactor.core.repositories.task_json_repository import TaskJsonRepository
from refactor.core.repositories.list_json_repository import ListJsonRepository
from refactor.core.repositories.folder_json_repository import FolderJsonRepository
from refactor.core.repositories.space_json_repository import SpaceJsonRepository

__all__ = [
    'Repository',
    'ITaskRepository',
    'IListRepository', 
    'IFolderRepository',
    'ISpaceRepository',
    'JsonRepository',
    'TaskJsonRepository',
    'ListJsonRepository',
    'FolderJsonRepository',
    'SpaceJsonRepository'
] 