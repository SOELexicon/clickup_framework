"""
Task: stk_2e7a6f12 - Write Unit Tests for Documentation Features
Document: refactor/tests/unit/core/services/test_document_section_service.py
dohcount: 1

Related Tasks:
    - tsk_a5b7c8d9 - Documentation Features Implementation (parent)
    - stk_f2d68857 - Add Document Relationship Types (sibling)
    - stk_c8e76fa1 - Implement Document Section Management (sibling)
    - stk_6da52c43 - Create Documentation CLI Commands (sibling)

Used By:
    - TestRunner: Executes all tests including document section service tests
    - CI/CD Pipeline: Verifies document section service functionality

Purpose:
    Tests the DocumentSectionService class which manages document sections
    and their operations.

Requirements:
    - Must test all public methods of DocumentSectionService
    - Must verify section creation, update, removal and ordering
    - Must test entity reference handling
    - CRITICAL: Must use mocked repositories for isolation
    - CRITICAL: Must verify section order is maintained correctly

Changes:
    - v1: Initial implementation of document section service tests

Lessons Learned:
    - Section ordering tests need to verify the entire order is maintained
    - Mock repositories must preserve section order in their responses
"""

import unittest
from unittest.mock import MagicMock, patch

import pytest

from refactor.core.services.document_section_service import DocumentSectionService
from refactor.core.entities.document_section_entity import (
    DocumentSection,
    SectionType,
    SectionFormat
)
from refactor.core.entities.task_entity import TaskEntity
from refactor.core.exceptions import (
    EntityNotFoundError,
    InvalidValueError,
    BusinessRuleViolationError
)


class TestDocumentSectionService(unittest.TestCase):
    """Test suite for the DocumentSectionService class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create mocked repositories
        self.document_section_repository = MagicMock()
        self.task_repository = MagicMock()
        
        # Create the service with mocked dependencies
        self.service = DocumentSectionService(
            document_section_repository=self.document_section_repository,
            task_repository=self.task_repository
        )
        
        # Create sample document sections for testing
        self.section1 = DocumentSection(
            id="sec_123",
            name="Introduction",
            content="This is the introduction",
            section_type=SectionType.TEXT.value,
            format=SectionFormat.MARKDOWN.value,
            task_id="tsk_doc123",
            index=0,
            tags=["intro"],
            entity_references=[]
        )
        
        self.section2 = DocumentSection(
            id="sec_456",
            name="Installation",
            content="Installation instructions",
            section_type=SectionType.INSTRUCTIONS.value,
            format=SectionFormat.MARKDOWN.value,
            task_id="tsk_doc123",
            index=1,
            tags=["setup"],
            entity_references=[]
        )
        
        self.task = TaskEntity(
            id="tsk_doc123",
            name="Documentation Task",
            status="in progress"
        )
        
        # Configure mock repositories
        self.document_section_repository.find_by_id.side_effect = self._mock_find_section_by_id
        self.document_section_repository.find_by_task_id.side_effect = self._mock_find_by_task_id
        self.document_section_repository.save.side_effect = self._mock_section_save
        self.document_section_repository.generate_id.return_value = "sec_999"
        
        self.task_repository.find_by_id.side_effect = self._mock_find_task_by_id
    
    def _mock_find_section_by_id(self, section_id):
        """Mock implementation of find_by_id for sections."""
        if section_id == "sec_123":
            return self.section1
        elif section_id == "sec_456":
            return self.section2
        else:
            raise EntityNotFoundError(section_id, "DocumentSection")
    
    def _mock_find_by_task_id(self, task_id):
        """Mock implementation of find_by_task_id."""
        if task_id == "tsk_doc123":
            return [self.section1, self.section2]
        else:
            return []
    
    def _mock_section_save(self, section):
        """Mock implementation of section save."""
        if section.id == "sec_123":
            self.section1 = section
        elif section.id == "sec_456":
            self.section2 = section
        return section
    
    def _mock_find_task_by_id(self, task_id):
        """Mock implementation of find_by_id for tasks."""
        if task_id == "tsk_doc123":
            return self.task
        else:
            raise EntityNotFoundError(task_id, "Task")

    def test_add_section(self):
        """Test adding a new document section."""
        # Act
        new_section = self.service.add_section(
            name="Usage",
            content="How to use the application",
            section_type=SectionType.INSTRUCTIONS.value,
            format=SectionFormat.MARKDOWN.value,
            task_id="tsk_doc123",
            index=2,
            tags=["usage", "guide"],
            entity_references=["tsk_code123"]
        )
        
        # Assert
        self.assertEqual(new_section.id, "sec_999")
        self.assertEqual(new_section.name, "Usage")
        self.assertEqual(new_section.section_type, SectionType.INSTRUCTIONS.value)
        self.assertEqual(new_section.index, 2)
        self.assertEqual(len(new_section.tags), 2)
        self.assertEqual(len(new_section.entity_references), 1)
        self.document_section_repository.save.assert_called_once()

    def test_add_section_nonexistent_task(self):
        """Test adding a section with nonexistent task."""
        # Arrange
        self.task_repository.find_by_id.side_effect = EntityNotFoundError("tsk_nonexistent", "Task")
        
        # Act & Assert
        with self.assertRaises(EntityNotFoundError):
            self.service.add_section(
                name="Test Section",
                content="Test content",
                section_type=SectionType.TEXT.value,
                format=SectionFormat.MARKDOWN.value,
                task_id="tsk_nonexistent"
            )

    def test_add_section_with_custom_index(self):
        """Test adding a section with a specific index."""
        # Act
        new_section = self.service.add_section(
            name="Overview",
            content="Overview content",
            section_type=SectionType.TEXT.value,
            format=SectionFormat.MARKDOWN.value,
            task_id="tsk_doc123",
            index=1  # Insert between existing sections
        )
        
        # Assert
        self.assertEqual(new_section.index, 1)
        
        # Verify sections were reindexed
        self.assertEqual(self.section1.index, 0)  # Unchanged
        self.assertEqual(self.section2.index, 2)  # Incremented
        
        # Verify all sections were saved
        self.assertEqual(self.document_section_repository.save.call_count, 3)

    def test_update_section(self):
        """Test updating an existing document section."""
        # Act
        updated_section = self.service.update_section(
            section_id="sec_123",
            name="Updated Introduction",
            content="This is the updated introduction",
            section_type=SectionType.TEXT.value,
            format=SectionFormat.HTML.value,
            tags=["intro", "updated"],
            entity_references=["tsk_code123"]
        )
        
        # Assert
        self.assertEqual(updated_section.name, "Updated Introduction")
        self.assertEqual(updated_section.content, "This is the updated introduction")
        self.assertEqual(updated_section.format, SectionFormat.HTML.value)
        self.assertEqual(len(updated_section.tags), 2)
        self.assertEqual(len(updated_section.entity_references), 1)
        self.document_section_repository.save.assert_called_once()

    def test_update_section_nonexistent(self):
        """Test updating a nonexistent section."""
        # Act & Assert
        with self.assertRaises(EntityNotFoundError):
            self.service.update_section(
                section_id="sec_nonexistent",
                name="Test",
                content="Test"
            )

    def test_remove_section(self):
        """Test removing a document section."""
        # Arrange
        self.document_section_repository.delete.return_value = True
        
        # Act
        result = self.service.remove_section("sec_123")
        
        # Assert
        self.assertTrue(result)
        self.document_section_repository.delete.assert_called_once_with("sec_123")
        
        # Verify remaining sections are reindexed
        self.assertEqual(self.section2.index, 0)
        self.document_section_repository.save.assert_called_once_with(self.section2)

    def test_remove_section_nonexistent(self):
        """Test removing a nonexistent section."""
        # Arrange
        self.document_section_repository.delete.side_effect = EntityNotFoundError("sec_nonexistent", "DocumentSection")
        
        # Act & Assert
        with self.assertRaises(EntityNotFoundError):
            self.service.remove_section("sec_nonexistent")

    def test_get_section(self):
        """Test getting a specific section by ID."""
        # Act
        section = self.service.get_section("sec_123")
        
        # Assert
        self.assertEqual(section.id, "sec_123")
        self.assertEqual(section.name, "Introduction")

    def test_get_section_nonexistent(self):
        """Test getting a nonexistent section."""
        # Act & Assert
        with self.assertRaises(EntityNotFoundError):
            self.service.get_section("sec_nonexistent")

    def test_get_sections_by_task(self):
        """Test getting all sections for a task."""
        # Act
        sections = self.service.get_sections_by_task("tsk_doc123")
        
        # Assert
        self.assertEqual(len(sections), 2)
        self.assertEqual(sections[0].id, "sec_123")
        self.assertEqual(sections[1].id, "sec_456")

    def test_get_sections_by_nonexistent_task(self):
        """Test getting sections for a nonexistent task."""
        # Act
        sections = self.service.get_sections_by_task("tsk_nonexistent")
        
        # Assert
        self.assertEqual(len(sections), 0)

    def test_reorder_sections(self):
        """Test reordering sections within a task."""
        # Arrange - add a third section
        section3 = DocumentSection(
            id="sec_789",
            name="Conclusion",
            content="Conclusion content",
            section_type=SectionType.TEXT.value,
            format=SectionFormat.MARKDOWN.value,
            task_id="tsk_doc123",
            index=2
        )
        
        # Update mock to include the third section
        old_find_by_task_id = self._mock_find_by_task_id
        
        def updated_find_by_task_id(task_id):
            if task_id == "tsk_doc123":
                return [self.section1, self.section2, section3]
            return old_find_by_task_id(task_id)
        
        self.document_section_repository.find_by_task_id.side_effect = updated_find_by_task_id
        
        old_find_section_by_id = self._mock_find_section_by_id
        
        def updated_find_section_by_id(section_id):
            if section_id == "sec_789":
                return section3
            return old_find_section_by_id(section_id)
        
        self.document_section_repository.find_by_id.side_effect = updated_find_section_by_id
        
        # Act - reorder to: Conclusion, Introduction, Installation
        new_order = ["sec_789", "sec_123", "sec_456"]
        self.service.reorder_sections("tsk_doc123", new_order)
        
        # Assert
        self.assertEqual(section3.index, 0)  # Moved to first
        self.assertEqual(self.section1.index, 1)  # Moved to second
        self.assertEqual(self.section2.index, 2)  # Moved to third
        
        # Verify all sections were saved
        self.assertEqual(self.document_section_repository.save.call_count, 3)

    def test_reorder_sections_invalid_ids(self):
        """Test reordering with invalid section IDs."""
        # Act & Assert
        with self.assertRaises(BusinessRuleViolationError):
            self.service.reorder_sections("tsk_doc123", ["sec_123", "sec_456", "sec_nonexistent"])

    def test_reorder_sections_mismatched_task(self):
        """Test reordering with sections from a different task."""
        # Arrange
        other_section = DocumentSection(
            id="sec_other",
            name="Other Section",
            task_id="tsk_other123",
            index=0
        )
        
        # Update mock to return the other section
        old_find_section_by_id = self._mock_find_section_by_id
        
        def updated_find_section_by_id(section_id):
            if section_id == "sec_other":
                return other_section
            return old_find_section_by_id(section_id)
        
        self.document_section_repository.find_by_id.side_effect = updated_find_section_by_id
        
        # Act & Assert
        with self.assertRaises(BusinessRuleViolationError):
            self.service.reorder_sections("tsk_doc123", ["sec_123", "sec_other"])

    def test_add_entity_reference(self):
        """Test adding an entity reference to a section."""
        # Act
        self.service.add_entity_reference("sec_123", "tsk_code123")
        
        # Assert
        self.assertIn("tsk_code123", self.section1.entity_references)
        self.document_section_repository.save.assert_called_once_with(self.section1)

    def test_add_duplicate_entity_reference(self):
        """Test adding a duplicate entity reference."""
        # Arrange
        self.section1.entity_references = ["tsk_code123"]
        
        # Act
        result = self.service.add_entity_reference("sec_123", "tsk_code123")
        
        # Assert
        self.assertFalse(result)  # Should return False for duplicate
        self.assertEqual(len(self.section1.entity_references), 1)  # Still only one reference
        self.document_section_repository.save.assert_not_called()

    def test_remove_entity_reference(self):
        """Test removing an entity reference from a section."""
        # Arrange
        self.section1.entity_references = ["tsk_code123", "tsk_code456"]
        
        # Act
        result = self.service.remove_entity_reference("sec_123", "tsk_code123")
        
        # Assert
        self.assertTrue(result)
        self.assertNotIn("tsk_code123", self.section1.entity_references)
        self.assertIn("tsk_code456", self.section1.entity_references)
        self.document_section_repository.save.assert_called_once_with(self.section1)

    def test_remove_nonexistent_entity_reference(self):
        """Test removing a nonexistent entity reference."""
        # Arrange
        self.section1.entity_references = ["tsk_code456"]
        
        # Act
        result = self.service.remove_entity_reference("sec_123", "tsk_code123")
        
        # Assert
        self.assertFalse(result)  # Should return False for nonexistent reference
        self.document_section_repository.save.assert_not_called()

    def test_find_sections_by_entity_reference(self):
        """Test finding sections by entity reference."""
        # Arrange
        self.section1.entity_references = ["tsk_code123"]
        self.section2.entity_references = ["tsk_code123", "tsk_code456"]
        
        # Act
        sections = self.service.find_sections_by_entity_reference("tsk_code123")
        
        # Assert
        self.assertEqual(len(sections), 2)
        section_ids = [s.id for s in sections]
        self.assertIn("sec_123", section_ids)
        self.assertIn("sec_456", section_ids)

    def test_find_sections_by_tag(self):
        """Test finding sections by tag."""
        # Arrange
        self.section1.tags = ["intro", "documentation"]
        self.section2.tags = ["setup", "documentation"]
        
        # Act
        sections = self.service.find_sections_by_tag("documentation")
        
        # Assert
        self.assertEqual(len(sections), 2)
        
        # Test with a more specific tag
        sections = self.service.find_sections_by_tag("intro")
        self.assertEqual(len(sections), 1)
        self.assertEqual(sections[0].id, "sec_123") 