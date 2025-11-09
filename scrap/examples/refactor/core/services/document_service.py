"""
Document Service Module

This module provides services for managing documentation tasks and their sections.
It handles the creation, retrieval, and modification of documentation and sections.
"""
from typing import Dict, List, Optional, Any, Union, Tuple
import uuid
from datetime import datetime

from refactor.core.entities.task_entity import TaskEntity, TaskType, TaskStatus, RelationshipType
from refactor.core.entities.document_section_entity import DocumentSection, SectionType, DocumentFormat
from refactor.core.repositories.task_repository import TaskRepository
from refactor.core.repositories.document_section_repository import DocumentSectionRepository
from refactor.core.exceptions import EntityError, EntityNotFoundError


class DocumentService:
    """
    Service for managing documentation tasks and document sections.
    
    This service provides methods for creating and managing documentation
    tasks and their associated section content.
    """
    
    def __init__(self, 
                task_repository: TaskRepository,
                document_section_repository: DocumentSectionRepository):
        """
        Initialize the DocumentService.
        
        Args:
            task_repository: Repository for managing task entities
            document_section_repository: Repository for managing document section entities
        """
        self._task_repository = task_repository
        self._document_section_repository = document_section_repository
    
    def create_documentation_task(self, 
                                 name: str,
                                 description: str = "",
                                 status: TaskStatus = TaskStatus.TO_DO,
                                 parent_id: Optional[str] = None,
                                 document_section: Optional[SectionType] = None,
                                 format: DocumentFormat = DocumentFormat.MARKDOWN,
                                 target_audience: Optional[str] = None) -> TaskEntity:
        """
        Create a new documentation task.
        
        Args:
            name: Name of the documentation task
            description: Description of the documentation
            status: Status of the task
            parent_id: Optional parent task ID
            document_section: Type of documentation section
            format: Format of the documentation
            target_audience: Target audience for the documentation
            
        Returns:
            The created documentation task entity
            
        Raises:
            EntityError: If validation fails
        """
        # Create the task with type DOCUMENTATION
        task = TaskEntity(
            id=f"tsk_{uuid.uuid4().hex[:8]}",
            name=name,
            description=description,
            status=status,
            task_type=TaskType.DOCUMENTATION,
            parent_id=parent_id
        )
        
        # Set documentation-specific properties
        if document_section:
            task.set_property("document_section", document_section.value)
        
        task.set_property("format", format.value)
        
        if target_audience:
            task.set_property("target_audience", target_audience)
        
        # Add the task to the repository
        return self._task_repository.add(task)
    
    def get_documentation_task(self, task_id: str) -> TaskEntity:
        """
        Get a documentation task by ID.
        
        Args:
            task_id: ID of the documentation task
            
        Returns:
            The documentation task entity
            
        Raises:
            EntityNotFoundError: If no task with the given ID exists
            EntityError: If the task is not a documentation task
        """
        task = self._task_repository.get_by_id(task_id)
        
        # Verify that this is a documentation task
        if task.task_type != TaskType.DOCUMENTATION:
            raise EntityError(f"Task '{task_id}' is not a documentation task")
        
        return task
    
    def get_all_documentation_tasks(self) -> List[TaskEntity]:
        """
        Get all documentation tasks.
        
        Returns:
            List of documentation task entities
        """
        return [
            task for task in self._task_repository.get_all()
            if task.task_type == TaskType.DOCUMENTATION
        ]
    
    def add_section_to_document(self, 
                              document_id: str,
                              name: str,
                              content: str = "",
                              section_type: SectionType = SectionType.CUSTOM,
                              format: DocumentFormat = DocumentFormat.MARKDOWN) -> DocumentSection:
        """
        Add a section to a documentation task.
        
        Args:
            document_id: ID of the documentation task
            name: Name of the section
            content: Content of the section
            section_type: Type of section
            format: Format of the section content
            
        Returns:
            The created document section entity
            
        Raises:
            EntityNotFoundError: If no task with the given ID exists
            EntityError: If the task is not a documentation task or validation fails
        """
        # Verify the document task exists and is a documentation task
        task = self.get_documentation_task(document_id)
        
        # Get the current number of sections to determine index
        existing_sections = self._document_section_repository.get_by_document_id(document_id)
        next_index = len(existing_sections)
        
        # Create the section
        section = DocumentSection(
            name=name,
            content=content,
            section_type=section_type,
            index=next_index,
            format=format,
            document_id=document_id
        )
        
        # Add the section to the repository
        return self._document_section_repository.add(section)
    
    def get_sections_for_document(self, document_id: str) -> List[DocumentSection]:
        """
        Get all sections for a documentation task.
        
        Args:
            document_id: ID of the documentation task
            
        Returns:
            List of document section entities, sorted by index
            
        Raises:
            EntityNotFoundError: If no task with the given ID exists
            EntityError: If the task is not a documentation task
        """
        # Verify the document task exists and is a documentation task
        self.get_documentation_task(document_id)
        
        # Return sections sorted by index
        return self._document_section_repository.get_by_document_id(document_id)
    
    def update_section(self, 
                      section_id: str, 
                      name: Optional[str] = None,
                      content: Optional[str] = None,
                      section_type: Optional[SectionType] = None) -> DocumentSection:
        """
        Update a document section.
        
        Args:
            section_id: ID of the section to update
            name: New name for the section (if provided)
            content: New content for the section (if provided)
            section_type: New section type (if provided)
            
        Returns:
            The updated document section entity
            
        Raises:
            EntityNotFoundError: If no section with the given ID exists
        """
        # Get the section
        section = self._document_section_repository.get_by_id(section_id)
        
        # Update fields if provided
        if name is not None:
            section.name = name
        
        if content is not None:
            section.content = content
            
            # Update entity references when content changes
            section.update_entity_references()
        
        if section_type is not None:
            section.section_type = section_type
        
        # Update the section in the repository
        return self._document_section_repository.update(section)
    
    def reorder_sections(self, document_id: str, section_order: List[str]) -> None:
        """
        Reorder sections within a document.
        
        Args:
            document_id: ID of the documentation task
            section_order: List of section IDs in the desired order
            
        Raises:
            EntityNotFoundError: If no task or section with the given ID exists
            EntityError: If the task is not a documentation task or a section doesn't belong to the document
        """
        # Verify the document task exists and is a documentation task
        self.get_documentation_task(document_id)
        
        # Update section indices
        self._document_section_repository.update_section_indices(document_id, section_order)
    
    def delete_section(self, section_id: str) -> None:
        """
        Delete a document section.
        
        Args:
            section_id: ID of the section to delete
            
        Raises:
            EntityNotFoundError: If no section with the given ID exists
        """
        # Get the section to retrieve its document ID and index
        section = self._document_section_repository.get_by_id(section_id)
        document_id = section.document_id
        
        # Delete the section
        self._document_section_repository.delete(section_id)
        
        # Reindex remaining sections if this section was part of a document
        if document_id:
            self._document_section_repository.reindex_document_sections(document_id)
    
    def create_document_relationship(self, 
                                   documentation_task_id: str, 
                                   target_task_id: str) -> Tuple[TaskEntity, TaskEntity]:
        """
        Create a relationship between a documentation task and a target task.
        
        Args:
            documentation_task_id: ID of the documentation task
            target_task_id: ID of the task being documented
            
        Returns:
            Tuple of (documentation task, target task)
            
        Raises:
            EntityNotFoundError: If either task doesn't exist
            EntityError: If the first task is not a documentation task
        """
        # Get both tasks
        doc_task = self.get_documentation_task(documentation_task_id)
        target_task = self._task_repository.get_by_id(target_task_id)
        
        # Add bidirectional relationship
        doc_task.add_relationship(target_task_id, RelationshipType.DOCUMENTS)
        target_task.add_relationship(documentation_task_id, RelationshipType.DOCUMENTED_BY)
        
        # Update both tasks
        self._task_repository.update(doc_task)
        self._task_repository.update(target_task)
        
        return doc_task, target_task
    
    def remove_document_relationship(self, 
                                    documentation_task_id: str, 
                                    target_task_id: str) -> Tuple[TaskEntity, TaskEntity]:
        """
        Remove a relationship between a documentation task and a target task.
        
        Args:
            documentation_task_id: ID of the documentation task
            target_task_id: ID of the task being documented
            
        Returns:
            Tuple of (documentation task, target task)
            
        Raises:
            EntityNotFoundError: If either task doesn't exist
        """
        # Get both tasks
        doc_task = self._task_repository.get_by_id(documentation_task_id)
        target_task = self._task_repository.get_by_id(target_task_id)
        
        # Remove bidirectional relationship
        doc_task.remove_relationship(target_task_id, RelationshipType.DOCUMENTS)
        target_task.remove_relationship(documentation_task_id, RelationshipType.DOCUMENTED_BY)
        
        # Update both tasks
        self._task_repository.update(doc_task)
        self._task_repository.update(target_task)
        
        return doc_task, target_task
    
    def get_tasks_documented_by(self, documentation_task_id: str) -> List[TaskEntity]:
        """
        Get all tasks documented by a specific documentation task.
        
        Args:
            documentation_task_id: ID of the documentation task
            
        Returns:
            List of task entities documented by the specified documentation task
            
        Raises:
            EntityNotFoundError: If the documentation task doesn't exist
        """
        # Get the documentation task
        doc_task = self._task_repository.get_by_id(documentation_task_id)
        
        # Get IDs of tasks documented by this task
        documented_task_ids = doc_task.get_relationships(RelationshipType.DOCUMENTS)
        
        # Retrieve and return the tasks
        return [
            self._task_repository.get_by_id(task_id)
            for task_id in documented_task_ids
        ]
    
    def get_documentation_for_task(self, task_id: str) -> List[TaskEntity]:
        """
        Get all documentation tasks for a specific task.
        
        Args:
            task_id: ID of the task
            
        Returns:
            List of documentation task entities for the specified task
            
        Raises:
            EntityNotFoundError: If the task doesn't exist
        """
        # Get the task
        task = self._task_repository.get_by_id(task_id)
        
        # Get IDs of documentation tasks for this task
        documentation_task_ids = task.get_relationships(RelationshipType.DOCUMENTED_BY)
        
        # Retrieve and return the documentation tasks
        return [
            self._task_repository.get_by_id(doc_task_id)
            for doc_task_id in documentation_task_ids
        ]