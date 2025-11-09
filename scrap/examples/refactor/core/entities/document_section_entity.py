"""
Task: tsk_6c145d4d - Implement TaskType and DocumentSection Entities
Document: refactor/core/entities/document_section_entity.py
dohcount: 1

Related Tasks:
    - tsk_708256de - Documentation Features Implementation (parent)
    - tsk_fc8d352e - Create DocumentSection Entity (subtask)
    - tsk_4a3e98f7 - Update TaskType Enum (subtask)

Used By:
    - TaskEntity: For specifying document sections in documentation tasks
    - DocumentSectionService: For managing document sections
    - DocumentCLI: For creating and manipulating document sections

Purpose:
    Defines the DocumentSection entity class and related enums for representing 
    sections within documentation tasks, with support for different section types,
    formatting, and entity references.

Requirements:
    - Must inherit from BaseEntity
    - Must support multiple section types via enum
    - Must support document formats for content
    - CRITICAL: Must validate entity IDs follow proper format
    - CRITICAL: Must maintain entity reference integrity

Parameters:
    N/A - This is an entity definition file

Returns:
    N/A - This is an entity definition file

Changes:
    - v1: Initial implementation with SectionType, DocumentFormat, and DocumentSection

Lessons Learned:
    - Entity structures need explicit validation for ID format
    - Immutable properties should use private variables with controlled property access
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional, Union, Set
import uuid
import re
from refactor.core.entities.base_entity import BaseEntity, EntityType, ValidationResult


class SectionType(Enum):
    """Types of document sections."""
    INTRODUCTION = "introduction"
    OVERVIEW = "overview"
    SPECIFICATION = "specification"
    API = "api"
    USAGE = "usage"
    EXAMPLES = "examples"
    ARCHITECTURE = "architecture"
    IMPLEMENTATION = "implementation"
    CONFIGURATION = "configuration"
    TROUBLESHOOTING = "troubleshooting"
    FAQ = "faq"
    GLOSSARY = "glossary"
    REFERENCES = "references"
    NOTES = "notes"
    CODE_SAMPLES = "code_samples"
    RELEASE_NOTES = "release_notes"
    INSTALLATION = "installation"
    DEPLOYMENT = "deployment"
    CUSTOMIZATION = "customization"
    MIGRATION = "migration"
    CUSTOM = "custom"
    
    @classmethod
    def from_string(cls, value: str) -> 'SectionType':
        """
        Convert a string to a SectionType enum value.
        
        Args:
            value: The section type string to convert
            
        Returns:
            The corresponding SectionType enum value
            
        Raises:
            ValueError: If the string doesn't match any section type
        """
        if not value:
            return cls.CUSTOM
            
        section_map = {
            "introduction": cls.INTRODUCTION,
            "overview": cls.OVERVIEW,
            "specification": cls.SPECIFICATION,
            "api": cls.API,
            "usage": cls.USAGE,
            "examples": cls.EXAMPLES,
            "architecture": cls.ARCHITECTURE,
            "implementation": cls.IMPLEMENTATION,
            "configuration": cls.CONFIGURATION,
            "troubleshooting": cls.TROUBLESHOOTING,
            "faq": cls.FAQ,
            "glossary": cls.GLOSSARY,
            "references": cls.REFERENCES,
            "notes": cls.NOTES,
            "code_samples": cls.CODE_SAMPLES,
            "release_notes": cls.RELEASE_NOTES,
            "installation": cls.INSTALLATION,
            "deployment": cls.DEPLOYMENT,
            "customization": cls.CUSTOMIZATION,
            "migration": cls.MIGRATION,
            "custom": cls.CUSTOM
        }
        
        lower_value = value.lower()
        if lower_value not in section_map:
            return cls.CUSTOM  # Default to CUSTOM for unrecognized values
            
        return section_map[lower_value]


class DocumentFormat(Enum):
    """Supported documentation formats."""
    MARKDOWN = "markdown"
    HTML = "html"
    RST = "rst"
    ASCIIDOC = "asciidoc"
    PDF = "pdf"
    DOCX = "docx"
    WIKI = "wiki"
    TEXT = "text"
    
    @classmethod
    def from_string(cls, value: str) -> 'DocumentFormat':
        """
        Convert a string to a DocumentFormat enum value.
        
        Args:
            value: The format string to convert
            
        Returns:
            The corresponding DocumentFormat enum value
            
        Raises:
            ValueError: If the string doesn't match any format
        """
        if not value:
            return cls.MARKDOWN
            
        format_map = {
            "markdown": cls.MARKDOWN,
            "md": cls.MARKDOWN,
            "html": cls.HTML,
            "rst": cls.RST,
            "asciidoc": cls.ASCIIDOC,
            "pdf": cls.PDF,
            "docx": cls.DOCX,
            "wiki": cls.WIKI,
            "text": cls.TEXT,
            "txt": cls.TEXT
        }
        
        lower_value = value.lower()
        if lower_value not in format_map:
            return cls.MARKDOWN  # Default to Markdown for unrecognized values
            
        return format_map[lower_value]


class DocumentSection(BaseEntity):
    """
    Represents a section within a documentation task.
    
    A document section contains content, tags, references to other entities,
    and can be ordered within a document.
    
    Attributes:
        section_id: Unique identifier for the section
        name: Name/title of the section
        content: The content of the section
        section_type: Type of section (e.g., introduction, API, examples)
        index: Order index for the section within a document
        tags: List of tags for categorizing the section
        entity_ids: List of entity IDs referenced in this section
        format: The format used for the section content
        created_at: When the section was created
        updated_at: When the section was last updated
    """
    
    def __init__(self, 
                 entity_id: Optional[str] = None, 
                 name: str = "", 
                 content: str = "",
                 section_type: Union[str, SectionType] = SectionType.CUSTOM,
                 index: int = 0,
                 tags: Optional[List[str]] = None,
                 entity_ids: Optional[List[str]] = None,
                 format: Union[str, DocumentFormat] = DocumentFormat.MARKDOWN,
                 document_id: Optional[str] = None,
                 created_at: Optional[int] = None,
                 updated_at: Optional[int] = None,
                 properties: Optional[Dict[str, Any]] = None):
        """
        Initialize a DocumentSection.
        
        Args:
            entity_id: Unique identifier for the section, generated if not provided
            name: Name/title of the section
            content: The content of the section
            section_type: Type of section
            index: Order index for the section within a document
            tags: List of tags for categorizing the section
            entity_ids: List of entity IDs referenced in this section
            format: The format used for the section content
            document_id: ID of the document this section belongs to
            created_at: Timestamp when section was created
            updated_at: Timestamp when section was last updated
            properties: Additional properties stored with the section
        """
        # Generate section ID if not provided
        if entity_id is None:
            entity_id = f"sec_{uuid.uuid4().hex[:8]}"
        
        # Initialize the base entity
        super().__init__(
            entity_id=entity_id,
            name=name,
            created_at=created_at,
            updated_at=updated_at,
            properties=properties
        )
        
        # Initialize section-specific fields
        self._content = content
        
        # Handle section type
        if isinstance(section_type, str):
            self._section_type = SectionType.from_string(section_type)
        else:
            self._section_type = section_type
            
        self._index = index
        self._tags = tags or []
        self._entity_ids = entity_ids or []
        
        # Handle format
        if isinstance(format, str):
            self._format = DocumentFormat.from_string(format)
        else:
            self._format = format
            
        self._document_id = document_id
    
    def get_entity_type(self) -> EntityType:
        """
        Get the entity type.
        
        Returns:
            EntityType.DOCUMENT_SECTION
        """
        return EntityType.DOCUMENT_SECTION
    
    def _validate(self, result: ValidationResult) -> None:
        """
        Perform entity-specific validations.
        
        Args:
            result: ValidationResult to add errors to
        """
        # Section ID must start with 'sec_'
        if not self._id.startswith("sec_"):
            result.add_error("Section ID must start with 'sec_'")
        
        # Section type must be valid
        if not isinstance(self._section_type, SectionType):
            result.add_error("Invalid section type")
            
        # Format must be valid
        if not isinstance(self._format, DocumentFormat):
            result.add_error("Invalid document format")
            
        # Index must be non-negative
        if self._index < 0:
            result.add_error("Section index must be non-negative")
            
        # Document ID must be provided if this section belongs to a document
        if self._document_id and not self._document_id.startswith("tsk_"):
            result.add_error("Document ID must start with 'tsk_'")
    
    def _to_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add entity-specific data to dictionary representation.
        
        Args:
            data: Base dictionary with common properties
            
        Returns:
            Dictionary with entity-specific properties added
        """
        # Add section-specific fields
        data.update({
            "content": self._content,
            "section_type": self._section_type.value,
            "index": self._index,
            "tags": self._tags.copy(),
            "entity_ids": self._entity_ids.copy(),
            "format": self._format.value
        })
        
        # Add document ID if present
        if self._document_id:
            data["document_id"] = self._document_id
            
        return data
    
    @property
    def content(self) -> str:
        """Get the section content."""
        return self._content
    
    @content.setter
    def content(self, value: str) -> None:
        """
        Set the section content.
        
        Args:
            value: New content for the section
        """
        if value != self._content:
            self._content = value
            self._updated_at = int(datetime.now().timestamp())
    
    @property
    def section_type(self) -> SectionType:
        """Get the section type."""
        return self._section_type
    
    @section_type.setter
    def section_type(self, value: Union[str, SectionType]) -> None:
        """
        Set the section type.
        
        Args:
            value: New section type (string or SectionType enum)
        """
        old_type = self._section_type
        
        if isinstance(value, str):
            self._section_type = SectionType.from_string(value)
        else:
            self._section_type = value
            
        if old_type != self._section_type:
            self._updated_at = int(datetime.now().timestamp())
    
    @property
    def index(self) -> int:
        """Get the section index."""
        return self._index
    
    @index.setter
    def index(self, value: int) -> None:
        """
        Set the section index.
        
        Args:
            value: New index for the section
        """
        if value != self._index:
            self._index = max(0, value)  # Ensure non-negative
            self._updated_at = int(datetime.now().timestamp())
    
    @property
    def tags(self) -> List[str]:
        """Get the section tags."""
        return self._tags.copy()
    
    def add_tag(self, tag: str) -> None:
        """
        Add a tag to the section.
        
        Args:
            tag: The tag to add
        """
        if tag and tag not in self._tags:
            self._tags.append(tag)
            self._updated_at = int(datetime.now().timestamp())
    
    def remove_tag(self, tag: str) -> None:
        """
        Remove a tag from the section.
        
        Args:
            tag: The tag to remove
        """
        if tag in self._tags:
            self._tags.remove(tag)
            self._updated_at = int(datetime.now().timestamp())
    
    @property
    def entity_ids(self) -> List[str]:
        """Get the entity IDs referenced in this section."""
        return self._entity_ids.copy()
    
    def add_entity_reference(self, entity_id: str) -> None:
        """
        Add an entity reference to the section.
        
        Args:
            entity_id: The entity ID to add
        """
        if entity_id and entity_id not in self._entity_ids:
            self._entity_ids.append(entity_id)
            self._updated_at = int(datetime.now().timestamp())
    
    def remove_entity_reference(self, entity_id: str) -> None:
        """
        Remove an entity reference from the section.
        
        Args:
            entity_id: The entity ID to remove
        """
        if entity_id in self._entity_ids:
            self._entity_ids.remove(entity_id)
            self._updated_at = int(datetime.now().timestamp())
    
    @property
    def format(self) -> DocumentFormat:
        """Get the document format."""
        return self._format
    
    @format.setter
    def format(self, value: Union[str, DocumentFormat]) -> None:
        """
        Set the document format.
        
        Args:
            value: New format (string or DocumentFormat enum)
        """
        old_format = self._format
        
        if isinstance(value, str):
            self._format = DocumentFormat.from_string(value)
        else:
            self._format = value
            
        if old_format != self._format:
            self._updated_at = int(datetime.now().timestamp())
    
    @property
    def document_id(self) -> Optional[str]:
        """Get the document ID this section belongs to."""
        return self._document_id
    
    @document_id.setter
    def document_id(self, value: Optional[str]) -> None:
        """
        Set the document ID this section belongs to.
        
        Args:
            value: New document ID
        """
        if value != self._document_id:
            self._document_id = value
            self._updated_at = int(datetime.now().timestamp())
    
    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> 'DocumentSection':
        """
        Create a DocumentSection from a dictionary.
        
        Args:
            data: Dictionary containing section data
            
        Returns:
            A DocumentSection instance
        """
        entity_id = data.get("id") or data.get("section_id")
        name = data.get("name", "")
        content = data.get("content", "")
        
        # Handle section type
        section_type_val = data.get("section_type", "custom")
        if isinstance(section_type_val, str):
            section_type = SectionType.from_string(section_type_val)
        else:
            section_type = section_type_val
            
        # Get other fields
        index = int(data.get("index", 0))
        tags = data.get("tags", [])
        entity_ids = data.get("entity_ids", [])
        
        # Handle format
        format_val = data.get("format", "markdown")
        if isinstance(format_val, str):
            doc_format = DocumentFormat.from_string(format_val)
        else:
            doc_format = format_val
            
        document_id = data.get("document_id")
        
        # Handle timestamps
        created_at = data.get("created_at")
        updated_at = data.get("updated_at")
        
        # Convert string timestamps to integers if needed
        if isinstance(created_at, str):
            try:
                created_at = int(datetime.fromisoformat(created_at).timestamp())
            except (ValueError, TypeError):
                created_at = None
                
        if isinstance(updated_at, str):
            try:
                updated_at = int(datetime.fromisoformat(updated_at).timestamp())
            except (ValueError, TypeError):
                updated_at = None
        
        # Get properties
        properties = data.get("properties", {})
        
        # Create and return the instance
        return cls(
            entity_id=entity_id,
            name=name,
            content=content,
            section_type=section_type,
            index=index,
            tags=tags,
            entity_ids=entity_ids,
            format=doc_format,
            document_id=document_id,
            created_at=created_at,
            updated_at=updated_at,
            properties=properties
        )
    
    def __str__(self) -> str:
        """Get a string representation of the section."""
        return f"DocumentSection(id={self._id}, name={self._name}, type={self._section_type.value})"

    def extract_entity_references_from_content(self) -> List[str]:
        """
        Extract entity references from the content using regex.
        
        Returns:
            List of entity IDs found in the content
        """
        # Match patterns like "tsk_12345678" or "sec_12345678"
        id_pattern = r'\b(tsk_[a-f0-9]{8}|sec_[a-f0-9]{8})\b'
        references = re.findall(id_pattern, self._content)
        return list(set(references))  # Remove duplicates
    
    def update_entity_references(self) -> None:
        """
        Update entity references based on content analysis.
        
        This method scans the content for entity ID patterns and
        updates the entity_ids list accordingly.
        """
        # Get references from content
        content_refs = self.extract_entity_references_from_content()
        
        # Update entity_ids list
        new_refs = set(content_refs) - set(self._entity_ids)
        if new_refs:
            self._entity_ids.extend(list(new_refs))
            self._updated_at = int(datetime.now().timestamp())

    def get_section_summary(self, max_length: int = 100) -> str:
        """
        Get a summary of the section content.
        
        Args:
            max_length: Maximum length of the summary
            
        Returns:
            A truncated summary of the section content
        """
        if not self._content:
            return ""
            
        # Remove markdown formatting for cleaner summary
        content = re.sub(r'[#*_`~]', '', self._content)
        
        # Replace newlines with spaces
        content = content.replace('\n', ' ').replace('\r', '')
        
        # Truncate if needed
        if len(content) > max_length:
            return content[:max_length].strip() + '...'
        
        return content.strip() 