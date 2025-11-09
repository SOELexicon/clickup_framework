"""
Task: tsk_783ad768 - Implement Document Section Management
Document: refactor/core/services/document_section_service.py
dohcount: 1

Related Tasks:
    - tsk_708256de - Documentation Features Implementation (parent)
    - tsk_22c4ba4c - Implement Document Relationship Types (sibling)
    - tsk_6c145d4d - Implement TaskType and DocumentSection Entities (depends on)

Used By:
    - DocumentService: For managing document sections with proper ordering
    - CLI Commands: For document section manipulation
    - Document Display: For rendering sections in correct order

Purpose:
    Provides service layer functionality for managing document sections, including
    adding, updating, removing, and ordering sections with proper validation.

Requirements:
    - Must handle section ordering with proper indices
    - Must support entity references in sections
    - Must maintain tag relationships and validation
    - CRITICAL: Must validate entity references
    - CRITICAL: Must maintain section order when sections are added or removed

Parameters:
    N/A - This is a service module file

Returns:
    N/A - This is a service module file

Changes:
    - v1: Initial implementation with core document section management functionality

Lessons Learned:
    - Service classes should handle business logic while repositories handle storage
    - Entity references need validation to maintain data integrity
"""

import logging
import threading
from typing import List, Optional, Dict, Any, Set, Tuple, Union
from datetime import datetime

from refactor.core.entities.document_section_entity import DocumentSection, SectionType, DocumentFormat
from refactor.core.repositories.document_section_repository import DocumentSectionRepository
from refactor.core.repositories.repository_interface import EntityNotFoundError, ValidationError
from refactor.core.utils.validation import validate_not_empty, validate_id_format
from refactor.plugins.hooks.hook_system import global_hook_registry


class DocumentSectionServiceError(Exception):
    """Base exception for document section service errors."""
    pass


class DocumentSectionService:
    """
    Service for managing document sections with proper ordering, content handling, and validation.
    
    This service provides methods for creating, updating, removing, and ordering document
    sections, as well as handling tags and entity references within sections.
    """
    
    def __init__(self, section_repository: DocumentSectionRepository, hook_registry=None):
        """
        Initialize the DocumentSectionService.
        
        Args:
            section_repository: Repository for document section entities
            hook_registry: Registry for hooks (defaults to global registry)
        """
        self.section_repository = section_repository
        self.hook_registry = hook_registry or global_hook_registry
        self.logger = logging.getLogger(__name__)
        self._lock = threading.RLock()  # For thread safety
    
    def add_section(self, 
                   document_id: str,
                   name: str,
                   content: str = "",
                   section_type: Union[str, SectionType] = SectionType.CUSTOM,
                   format: Union[str, DocumentFormat] = DocumentFormat.MARKDOWN,
                   index: Optional[int] = None,
                   tags: Optional[List[str]] = None,
                   entity_ids: Optional[List[str]] = None) -> DocumentSection:
        """
        Add a new section to a document.
        
        Args:
            document_id: ID of the document to add the section to
            name: Name/title of the section
            content: Content of the section
            section_type: Type of section
            format: Format of the section content
            index: Optional position index for the section (defaults to end)
            tags: Optional list of tags for the section
            entity_ids: Optional list of entity IDs referenced in the section
            
        Returns:
            The newly created DocumentSection
            
        Raises:
            DocumentSectionServiceError: If validation fails or other errors occur
        """
        try:
            with self._lock:
                # Validate inputs
                validate_not_empty(document_id, "Document ID")
                validate_id_format(document_id, "Document ID") 
                validate_not_empty(name, "Section name")
                
                # Get existing sections to determine index if not provided
                existing_sections = self.section_repository.get_by_document_id(document_id)
                
                # Set index if not provided
                if index is None:
                    index = len(existing_sections)
                else:
                    # Validate index is within acceptable range
                    if index < 0:
                        index = 0
                    elif index > len(existing_sections):
                        index = len(existing_sections)
                
                # Create the section
                section = DocumentSection(
                    name=name,
                    content=content,
                    section_type=section_type,
                    format=format,
                    index=index,
                    tags=tags or [],
                    entity_ids=entity_ids or [],
                    document_id=document_id
                )
                
                # Execute pre-add hooks
                hook_data = {"section": section, "document_id": document_id}
                self.hook_registry.execute_hook("pre_section_add", hook_data)
                
                # If we're inserting in the middle, reindex other sections
                if index < len(existing_sections):
                    # Shift indices of other sections
                    for other_section in existing_sections:
                        if other_section.index >= index:
                            other_section.index += 1
                            self.section_repository.update(other_section)
                
                # Add the section to the repository
                new_section = self.section_repository.add(section)
                
                # Execute post-add hooks
                hook_data["section"] = new_section
                self.hook_registry.execute_hook("post_section_add", hook_data)
                
                self.logger.info(f"Added section '{name}' to document {document_id}")
                return new_section
                
        except (ValueError, EntityNotFoundError, ValidationError) as e:
            self.logger.error(f"Error adding section: {str(e)}")
            raise DocumentSectionServiceError(f"Failed to add section: {str(e)}")
    
    def update_section(self,
                      section_id: str,
                      name: Optional[str] = None,
                      content: Optional[str] = None,
                      section_type: Optional[Union[str, SectionType]] = None,
                      format: Optional[Union[str, DocumentFormat]] = None,
                      tags: Optional[List[str]] = None,
                      entity_ids: Optional[List[str]] = None) -> DocumentSection:
        """
        Update an existing document section.
        
        Args:
            section_id: ID of the section to update
            name: New name for the section (if provided)
            content: New content for the section (if provided)
            section_type: New section type (if provided)
            format: New format for the section content (if provided)
            tags: New tags for the section (if provided)
            entity_ids: New entity IDs referenced in the section (if provided)
            
        Returns:
            The updated DocumentSection
            
        Raises:
            DocumentSectionServiceError: If the section doesn't exist or validation fails
        """
        try:
            with self._lock:
                # Validate section ID
                validate_id_format(section_id, "Section ID")
                
                # Get the section
                section = self.section_repository.get_by_id(section_id)
                
                # Execute pre-update hooks
                hook_data = {"section": section, "updates": {}}
                
                # Update fields if provided
                if name is not None:
                    validate_not_empty(name, "Section name")
                    hook_data["updates"]["name"] = {"old": section.name, "new": name}
                    section.name = name
                
                if content is not None:
                    hook_data["updates"]["content"] = {"old": section.content, "new": content}
                    section.content = content
                
                if section_type is not None:
                    hook_data["updates"]["section_type"] = {"old": section.section_type, "new": section_type}
                    section.section_type = section_type
                
                if format is not None:
                    hook_data["updates"]["format"] = {"old": section.format, "new": format}
                    section.format = format
                    
                if tags is not None:
                    hook_data["updates"]["tags"] = {"old": section.tags, "new": tags}
                    section.tags = tags
                    
                if entity_ids is not None:
                    # Validate entity IDs format
                    for entity_id in entity_ids:
                        validate_id_format(entity_id, "Entity ID")
                    
                    hook_data["updates"]["entity_ids"] = {"old": section.entity_ids, "new": entity_ids}
                    section.entity_ids = entity_ids
                
                # Only proceed if at least one field was updated
                if not hook_data["updates"]:
                    self.logger.info(f"No updates provided for section {section_id}")
                    return section
                
                # Execute pre-update hooks
                self.hook_registry.execute_hook("pre_section_update", hook_data)
                
                # Update the section
                updated_section = self.section_repository.update(section)
                
                # Execute post-update hooks
                hook_data["section"] = updated_section
                self.hook_registry.execute_hook("post_section_update", hook_data)
                
                self.logger.info(f"Updated section {section_id}")
                return updated_section
                
        except (ValueError, EntityNotFoundError, ValidationError) as e:
            self.logger.error(f"Error updating section: {str(e)}")
            raise DocumentSectionServiceError(f"Failed to update section: {str(e)}")
    
    def remove_section(self, section_id: str) -> None:
        """
        Remove a document section.
        
        Args:
            section_id: ID of the section to remove
            
        Raises:
            DocumentSectionServiceError: If the section doesn't exist
        """
        try:
            with self._lock:
                # Validate section ID
                validate_id_format(section_id, "Section ID")
                
                # Get the section
                section = self.section_repository.get_by_id(section_id)
                document_id = section.document_id
                removed_index = section.index
                
                # Execute pre-remove hooks
                hook_data = {"section": section, "document_id": document_id}
                self.hook_registry.execute_hook("pre_section_remove", hook_data)
                
                # Remove the section
                self.section_repository.delete(section_id)
                
                # Reindex remaining sections
                sections = self.section_repository.get_by_document_id(document_id)
                
                # Update indices for remaining sections
                for other_section in sections:
                    if other_section.index > removed_index:
                        other_section.index -= 1
                        self.section_repository.update(other_section)
                
                # Execute post-remove hooks
                self.hook_registry.execute_hook("post_section_remove", hook_data)
                
                self.logger.info(f"Removed section {section_id} from document {document_id}")
                
        except (EntityNotFoundError, ValidationError) as e:
            self.logger.error(f"Error removing section: {str(e)}")
            raise DocumentSectionServiceError(f"Failed to remove section: {str(e)}")
    
    def get_sections(self, document_id: str) -> List[DocumentSection]:
        """
        Get all sections for a document, sorted by index.
        
        Args:
            document_id: ID of the document
            
        Returns:
            List of DocumentSection entities, sorted by index
            
        Raises:
            DocumentSectionServiceError: If validation fails
        """
        try:
            # Validate document ID
            validate_id_format(document_id, "Document ID")
            
            # Get and return sections
            return self.section_repository.get_by_document_id(document_id)
            
        except (ValueError) as e:
            self.logger.error(f"Error getting sections: {str(e)}")
            raise DocumentSectionServiceError(f"Failed to get sections: {str(e)}")
    
    def reorder_sections(self, document_id: str, section_order: List[str]) -> None:
        """
        Reorder sections within a document.
        
        Args:
            document_id: ID of the document
            section_order: List of section IDs in the desired order
            
        Raises:
            DocumentSectionServiceError: If validation fails or sections don't exist
        """
        try:
            with self._lock:
                # Validate document ID
                validate_id_format(document_id, "Document ID")
                
                # Get existing sections
                existing_sections = self.section_repository.get_by_document_id(document_id)
                existing_ids = {section.id for section in existing_sections}
                
                # Validate that all sections in the order list exist and belong to the document
                if not all(section_id in existing_ids for section_id in section_order):
                    missing = [section_id for section_id in section_order if section_id not in existing_ids]
                    raise ValueError(f"Invalid section IDs in order list: {missing}")
                
                # Validate that all sections from the document are included in the order list
                if len(section_order) != len(existing_sections):
                    missing = [section.id for section in existing_sections if section.id not in section_order]
                    raise ValueError(f"Missing section IDs in order list: {missing}")
                
                # Execute pre-reorder hooks
                hook_data = {
                    "document_id": document_id,
                    "old_order": [section.id for section in existing_sections],
                    "new_order": section_order
                }
                self.hook_registry.execute_hook("pre_section_reorder", hook_data)
                
                # Update section indices
                for index, section_id in enumerate(section_order):
                    section = self.section_repository.get_by_id(section_id)
                    section.index = index
                    self.section_repository.update(section)
                
                # Execute post-reorder hooks
                self.hook_registry.execute_hook("post_section_reorder", hook_data)
                
                self.logger.info(f"Reordered sections in document {document_id}")
                
        except (ValueError, EntityNotFoundError, ValidationError) as e:
            self.logger.error(f"Error reordering sections: {str(e)}")
            raise DocumentSectionServiceError(f"Failed to reorder sections: {str(e)}")
    
    def get_sections_by_tag(self, tag: str) -> List[DocumentSection]:
        """
        Get all sections with a specific tag.
        
        Args:
            tag: Tag to search for
            
        Returns:
            List of DocumentSection entities with the specified tag
        """
        return self.section_repository.get_by_tag(tag)
    
    def get_sections_referencing_entity(self, entity_id: str) -> List[DocumentSection]:
        """
        Get all sections that reference a specific entity.
        
        Args:
            entity_id: ID of the entity to search for
            
        Returns:
            List of DocumentSection entities referencing the entity
            
        Raises:
            DocumentSectionServiceError: If validation fails
        """
        try:
            # Validate entity ID
            validate_id_format(entity_id, "Entity ID")
            
            # Get and return sections
            return self.section_repository.get_sections_referencing_entity(entity_id)
            
        except (ValueError) as e:
            self.logger.error(f"Error getting sections by entity: {str(e)}")
            raise DocumentSectionServiceError(f"Failed to get sections by entity: {str(e)}")
    
    def get_sections_by_type(self, section_type: Union[str, SectionType]) -> List[DocumentSection]:
        """
        Get all sections of a specific type.
        
        Args:
            section_type: Type of sections to get
            
        Returns:
            List of DocumentSection entities of the specified type
        """
        return self.section_repository.get_by_section_type(section_type) 