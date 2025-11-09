"""
Document Section Repository Module

This module defines the repository for DocumentSection entities.
"""
from typing import Dict, List, Optional, Set, Any, Tuple, Union
import json
import uuid
from datetime import datetime

from refactor.core.repositories.repository_interface import EntityRepository
from refactor.core.entities.document_section_entity import DocumentSection, SectionType
from refactor.core.exceptions import EntityError, EntityNotFoundError


class DocumentSectionRepository(EntityRepository[DocumentSection]):
    """
    Repository for managing DocumentSection entities.
    
    This repository handles the storage, retrieval, and management of
    document sections that make up documentation tasks.
    """
    
    def __init__(self, data: Optional[Dict[str, Any]] = None):
        """
        Initialize the DocumentSectionRepository.
        
        Args:
            data: Optional dictionary containing section data
        """
        self._sections: Dict[str, DocumentSection] = {}
        
        if data:
            self._load_from_dict(data)
    
    def get_by_id(self, entity_id: str) -> DocumentSection:
        """
        Get a document section by its ID.
        
        Args:
            entity_id: The ID of the section to retrieve
            
        Returns:
            The requested DocumentSection
            
        Raises:
            EntityNotFoundError: If no section with the given ID exists
        """
        if entity_id not in self._sections:
            raise EntityNotFoundError(f"Document section not found: {entity_id}")
        
        return self._sections[entity_id]
    
    def get_all(self) -> List[DocumentSection]:
        """
        Get all document sections.
        
        Returns:
            List of all DocumentSection entities
        """
        return list(self._sections.values())
    
    def add(self, entity: DocumentSection) -> DocumentSection:
        """
        Add a document section to the repository.
        
        Args:
            entity: The DocumentSection to add
            
        Returns:
            The added DocumentSection
            
        Raises:
            EntityError: If validation fails or if a section with the same ID already exists
        """
        # Validate the section
        validation_result = entity.validate()
        if not validation_result.is_valid:
            raise EntityError(f"Invalid document section: {validation_result.errors}")
        
        # Check for existing section with the same ID
        if entity.id in self._sections:
            raise EntityError(f"Document section with ID '{entity.id}' already exists")
        
        # Add the section
        self._sections[entity.id] = entity
        return entity
    
    def update(self, entity: DocumentSection) -> DocumentSection:
        """
        Update an existing document section.
        
        Args:
            entity: The DocumentSection to update
            
        Returns:
            The updated DocumentSection
            
        Raises:
            EntityNotFoundError: If no section with the given ID exists
            EntityError: If validation fails
        """
        # Check if the section exists
        if entity.id not in self._sections:
            raise EntityNotFoundError(f"Document section not found: {entity.id}")
        
        # Validate the section
        validation_result = entity.validate()
        if not validation_result.is_valid:
            raise EntityError(f"Invalid document section: {validation_result.errors}")
        
        # Update the section
        self._sections[entity.id] = entity
        return entity
    
    def delete(self, entity_id: str) -> None:
        """
        Delete a document section.
        
        Args:
            entity_id: The ID of the section to delete
            
        Raises:
            EntityNotFoundError: If no section with the given ID exists
        """
        if entity_id not in self._sections:
            raise EntityNotFoundError(f"Document section not found: {entity_id}")
        
        del self._sections[entity_id]
    
    def exists(self, entity_id: str) -> bool:
        """
        Check if a document section exists.
        
        Args:
            entity_id: The ID of the section to check
            
        Returns:
            True if the section exists, False otherwise
        """
        return entity_id in self._sections
    
    def get_by_document_id(self, document_id: str) -> List[DocumentSection]:
        """
        Get all sections for a specific document.
        
        Args:
            document_id: The ID of the document
            
        Returns:
            List of DocumentSection entities for the document, sorted by index
        """
        sections = [
            section for section in self._sections.values()
            if section.document_id == document_id
        ]
        
        # Sort by index
        return sorted(sections, key=lambda s: s.index)
    
    def get_by_section_type(self, section_type: Union[str, SectionType]) -> List[DocumentSection]:
        """
        Get all sections of a specific type.
        
        Args:
            section_type: The section type to filter by
            
        Returns:
            List of DocumentSection entities of the specified type
        """
        # Convert string to enum if needed
        if isinstance(section_type, str):
            try:
                section_type = SectionType.from_string(section_type)
            except ValueError:
                return []  # Return empty list for invalid section type
        
        return [
            section for section in self._sections.values()
            if section.section_type == section_type
        ]
    
    def get_by_tag(self, tag: str) -> List[DocumentSection]:
        """
        Get all sections with a specific tag.
        
        Args:
            tag: The tag to filter by
            
        Returns:
            List of DocumentSection entities with the specified tag
        """
        return [
            section for section in self._sections.values()
            if tag in section.tags
        ]
    
    def get_sections_referencing_entity(self, entity_id: str) -> List[DocumentSection]:
        """
        Get all sections that reference a specific entity.
        
        Args:
            entity_id: The ID of the entity to check references for
            
        Returns:
            List of DocumentSection entities that reference the specified entity
        """
        return [
            section for section in self._sections.values()
            if entity_id in section.entity_ids
        ]
    
    def update_section_indices(self, document_id: str, section_order: List[str]) -> None:
        """
        Update the indices of sections within a document based on the provided order.
        
        Args:
            document_id: The ID of the document
            section_order: List of section IDs in the desired order
            
        Raises:
            EntityNotFoundError: If any section in the order list doesn't exist
            EntityError: If a section in the order list doesn't belong to the document
        """
        # Check that all sections exist and belong to the document
        for index, section_id in enumerate(section_order):
            if section_id not in self._sections:
                raise EntityNotFoundError(f"Document section not found: {section_id}")
            
            section = self._sections[section_id]
            if section.document_id != document_id:
                raise EntityError(
                    f"Section '{section_id}' does not belong to document '{document_id}'"
                )
            
            # Update the section index
            section.index = index
    
    def extract_entity_references(self) -> None:
        """
        Update entity references for all sections by analyzing their content.
        
        This method scans through all sections and updates their entity reference
        lists based on the content.
        """
        for section in self._sections.values():
            section.update_entity_references()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the repository to a dictionary.
        
        Returns:
            Dictionary representation of the repository
        """
        return {
            "sections": [section.to_dict() for section in self._sections.values()]
        }
    
    def _load_from_dict(self, data: Dict[str, Any]) -> None:
        """
        Load document sections from a dictionary.
        
        Args:
            data: Dictionary containing section data
        """
        sections_data = data.get("sections", [])
        
        for section_data in sections_data:
            try:
                section = DocumentSection.from_dict(section_data)
                self._sections[section.id] = section
            except Exception as e:
                # Log the error and continue with the next section
                print(f"Error loading document section: {e}")
    
    def reindex_document_sections(self, document_id: str) -> None:
        """
        Reindex sections for a document to ensure sequential indices.
        
        Args:
            document_id: The ID of the document to reindex
        """
        sections = self.get_by_document_id(document_id)
        
        # Update indices to match their sorted order
        for i, section in enumerate(sections):
            if section.index != i:
                section.index = i