"""
Core Entities

This package contains entity classes that represent the core data models for
the ClickUp JSON Manager. Entities encapsulate data and provide methods for
data validation and manipulation.

Entities:
    - TaskEntity: Represents a task or subtask
    - TaskStatus: Enumeration of possible task statuses
    - TaskPriority: Enumeration of possible task priorities
    - TaskType: Enumeration of possible task types
    - DocumentSection: Represents a section within a documentation task
    - SectionType: Enumeration of possible document section types
    - (Future) SpaceEntity: Will represent a workspace space
    - (Future) FolderEntity: Will represent a folder within a space
    - (Future) ListEntity: Will represent a list within a folder
"""

from refactor.core.entities.task_entity import TaskEntity, TaskStatus, TaskPriority
from refactor.core.entities.task_type import TaskType
from refactor.core.entities.document_section_entity import DocumentSection, SectionType, DocumentFormat

__all__ = [
    'TaskEntity',
    'TaskStatus',
    'TaskPriority',
    'TaskType',
    'DocumentSection',
    'SectionType',
    'DocumentFormat',
] 