"""
Task: stk_2e7a6f12 - Write Unit Tests for Documentation Features
Document: refactor/tests/unit/core/services/test_document_service.py
dohcount: 1

Related Tasks:
    - tsk_a5b7c8d9 - Documentation Features Implementation (parent)
    - stk_f2d68857 - Add Document Relationship Types (sibling)
    - stk_c8e76fa1 - Implement Document Section Management (sibling)
    - stk_6da52c43 - Create Documentation CLI Commands (sibling)

Used By:
    - TestRunner: Executes all tests including document service tests
    - CI/CD Pipeline: Verifies document service functionality

Purpose:
    Tests the DocumentService class which manages document tasks and their relationships.

Requirements:
    - Must test all public methods of DocumentService
    - Must verify document relationship handling (documents, documented_by)
    - Must test error cases and validation
    - CRITICAL: Must use mocked repositories for isolation
    - CRITICAL: Each test must clean up after itself

Changes:
    - v1: Initial implementation of document service tests

Lessons Learned:
    - Document relationship tests need to verify both sides of relationship
    - Mock repositories must be configured to return consistent results
"""

import unittest
from unittest.mock import MagicMock, patch

import pytest

from refactor.core.services.document_service import DocumentService
from refactor.core.entities.task_entity import TaskEntity, RelationshipType
from refactor.core.exceptions import (
    EntityNotFoundError,
    InvalidValueError,
    BusinessRuleViolationError
)


class TestDocumentService(unittest.TestCase):
    """Test suite for the DocumentService class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create mocked repositories
        self.task_repository = MagicMock()
        self.config_repository = MagicMock()
        
        # Create the service with mocked dependencies
        self.document_service = DocumentService(
            task_repository=self.task_repository,
            config_repository=self.config_repository
        )
        
        # Create sample tasks for testing
        self.doc_task = TaskEntity(
            id="tsk_doc123",
            name="Documentation Task",
            description="Test documentation task",
            status="in progress",
            priority="normal",
            relationships={}
        )
        
        self.code_task = TaskEntity(
            id="tsk_code123",
            name="Code Task",
            description="Test code task",
            status="in progress",
            priority="normal",
            relationships={}
        )
        
        # Configure mock repository to return tasks
        self.task_repository.find_by_id.side_effect = self._mock_find_by_id
        self.task_repository.find_by_name.side_effect = self._mock_find_by_name
        self.task_repository.save.side_effect = self._mock_save
    
    def _mock_find_by_id(self, task_id):
        """Mock implementation of find_by_id."""
        if task_id == "tsk_doc123":
            return self.doc_task
        elif task_id == "tsk_code123":
            return self.code_task
        else:
            raise EntityNotFoundError(task_id, "Task")
    
    def _mock_find_by_name(self, task_name):
        """Mock implementation of find_by_name."""
        if task_name == "Documentation Task":
            return self.doc_task
        elif task_name == "Code Task":
            return self.code_task
        else:
            raise EntityNotFoundError(task_name, "Task")
    
    def _mock_save(self, task):
        """Mock implementation of save."""
        if task.id == "tsk_doc123":
            self.doc_task = task
        elif task.id == "tsk_code123":
            self.code_task = task
        return task

    def test_create_documentation_task(self):
        """Test creating a new documentation task."""
        # Arrange
        self.task_repository.generate_id.return_value = "tsk_newdoc123"
        self.task_repository.find_by_name.side_effect = EntityNotFoundError("New Doc", "Task")
        
        # Act
        new_task = self.document_service.create_documentation_task(
            name="New Doc",
            description="New documentation task",
            status="to do",
            priority="high",
            tags=["docs", "important"]
        )
        
        # Assert
        self.assertEqual(new_task.name, "New Doc")
        self.assertEqual(new_task.status, "to do")
        self.assertEqual(new_task.priority, "high")
        self.assertIn("docs", new_task.tags)
        self.assertIn("documentation", new_task.tags)  # Should add default tag
        self.task_repository.save.assert_called_once()

    def test_create_documentation_task_existing_name(self):
        """Test creating a documentation task with an existing name."""
        # Arrange - mock will return existing task for "Documentation Task"
        
        # Act & Assert
        with self.assertRaises(BusinessRuleViolationError):
            self.document_service.create_documentation_task(
                name="Documentation Task",
                description="Duplicate doc task",
                status="to do"
            )

    def test_add_document_relationship(self):
        """Test adding a documents relationship between tasks."""
        # Act
        self.document_service.add_document_relationship(
            source_task_id="tsk_doc123",
            target_task_id="tsk_code123"
        )
        
        # Assert
        # Check source task relationship
        self.assertIn(RelationshipType.DOCUMENTS.value, self.doc_task.relationships)
        self.assertIn(
            "tsk_code123", 
            self.doc_task.relationships[RelationshipType.DOCUMENTS.value]
        )
        
        # Check target task relationship
        self.assertIn(RelationshipType.DOCUMENTED_BY.value, self.code_task.relationships)
        self.assertIn(
            "tsk_doc123", 
            self.code_task.relationships[RelationshipType.DOCUMENTED_BY.value]
        )
        
        # Verify saves were called
        self.assertEqual(self.task_repository.save.call_count, 2)

    def test_add_document_relationship_nonexistent_task(self):
        """Test adding a document relationship with nonexistent task."""
        # Act & Assert
        with self.assertRaises(EntityNotFoundError):
            self.document_service.add_document_relationship(
                source_task_id="tsk_doc123",
                target_task_id="tsk_nonexistent"
            )

    def test_remove_document_relationship(self):
        """Test removing a documents relationship between tasks."""
        # Arrange - setup relationship
        self.doc_task.relationships[RelationshipType.DOCUMENTS.value] = ["tsk_code123"]
        self.code_task.relationships[RelationshipType.DOCUMENTED_BY.value] = ["tsk_doc123"]
        
        # Act
        self.document_service.remove_document_relationship(
            source_task_id="tsk_doc123",
            target_task_id="tsk_code123"
        )
        
        # Assert
        # Check source task relationship removed
        self.assertNotIn(
            "tsk_code123",
            self.doc_task.relationships.get(RelationshipType.DOCUMENTS.value, [])
        )
        
        # Check target task relationship removed
        self.assertNotIn(
            "tsk_doc123",
            self.code_task.relationships.get(RelationshipType.DOCUMENTED_BY.value, [])
        )
        
        # Verify saves were called
        self.assertEqual(self.task_repository.save.call_count, 2)

    def test_remove_document_relationship_nonexistent(self):
        """Test removing a nonexistent document relationship."""
        # Arrange - no relationships setup
        
        # Act & Assert
        with self.assertRaises(BusinessRuleViolationError):
            self.document_service.remove_document_relationship(
                source_task_id="tsk_doc123",
                target_task_id="tsk_code123"
            )

    def test_get_documentation_for_task(self):
        """Test getting documentation tasks for a given task."""
        # Arrange
        doc_task2 = TaskEntity(
            id="tsk_doc456",
            name="Another Doc Task",
            status="in progress"
        )
        
        # Setup relationships
        self.code_task.relationships[RelationshipType.DOCUMENTED_BY.value] = [
            "tsk_doc123", "tsk_doc456"
        ]
        
        # Update mock to return the new task
        old_find_by_id = self._mock_find_by_id
        
        def updated_find_by_id(task_id):
            if task_id == "tsk_doc456":
                return doc_task2
            return old_find_by_id(task_id)
        
        self.task_repository.find_by_id.side_effect = updated_find_by_id
        
        # Act
        doc_tasks = self.document_service.get_documentation_for_task("tsk_code123")
        
        # Assert
        self.assertEqual(len(doc_tasks), 2)
        doc_ids = [task.id for task in doc_tasks]
        self.assertIn("tsk_doc123", doc_ids)
        self.assertIn("tsk_doc456", doc_ids)

    def test_get_documented_tasks(self):
        """Test getting tasks documented by a documentation task."""
        # Arrange
        code_task2 = TaskEntity(
            id="tsk_code456",
            name="Another Code Task",
            status="in progress"
        )
        
        # Setup relationships
        self.doc_task.relationships[RelationshipType.DOCUMENTS.value] = [
            "tsk_code123", "tsk_code456"
        ]
        
        # Update mock to return the new task
        old_find_by_id = self._mock_find_by_id
        
        def updated_find_by_id(task_id):
            if task_id == "tsk_code456":
                return code_task2
            return old_find_by_id(task_id)
        
        self.task_repository.find_by_id.side_effect = updated_find_by_id
        
        # Act
        code_tasks = self.document_service.get_documented_tasks("tsk_doc123")
        
        # Assert
        self.assertEqual(len(code_tasks), 2)
        task_ids = [task.id for task in code_tasks]
        self.assertIn("tsk_code123", task_ids)
        self.assertIn("tsk_code456", task_ids)

    def test_is_documentation_task(self):
        """Test checking if a task is a documentation task."""
        # Arrange
        self.doc_task.tags = ["documentation", "important"]
        self.code_task.tags = ["code", "feature"]
        
        # Act & Assert
        self.assertTrue(self.document_service.is_documentation_task(self.doc_task))
        self.assertFalse(self.document_service.is_documentation_task(self.code_task))

    def test_find_documentation_tasks(self):
        """Test finding all documentation tasks."""
        # Arrange
        doc_task2 = TaskEntity(
            id="tsk_doc456",
            name="Another Doc Task",
            tags=["documentation"]
        )
        
        all_tasks = [self.doc_task, self.code_task, doc_task2]
        self.doc_task.tags = ["documentation"]
        self.task_repository.find_all.return_value = all_tasks
        
        # Act
        doc_tasks = self.document_service.find_documentation_tasks()
        
        # Assert
        self.assertEqual(len(doc_tasks), 2)
        doc_ids = [task.id for task in doc_tasks]
        self.assertIn("tsk_doc123", doc_ids)
        self.assertIn("tsk_doc456", doc_ids)
        self.assertNotIn("tsk_code123", doc_ids) 