"""
Task: stk_2e7a6f12 - Write Unit Tests for Documentation Features
Document: refactor/tests/unit/cli/test_document_commands.py
dohcount: 1

Related Tasks:
    - tsk_a5b7c8d9 - Documentation Features Implementation (parent)
    - stk_f2d68857 - Add Document Relationship Types (sibling)
    - stk_c8e76fa1 - Implement Document Section Management (sibling)
    - stk_6da52c43 - Create Documentation CLI Commands (sibling)

Used By:
    - TestRunner: Executes all CLI command tests including document commands
    - CI/CD Pipeline: Verifies document command functionality

Purpose:
    Tests the DocumentCommand CLI class and its subcommands for managing
    document sections.

Requirements:
    - Must test all document section subcommands
    - Must verify command parsing and execution
    - Must test error handling and validation
    - CRITICAL: Must use mocked services for isolation
    - CRITICAL: Must test output formatting for human readability

Changes:
    - v1: Initial implementation of document command tests

Lessons Learned:
    - CLI command tests need to verify both exit codes and output formatting
    - ArgumentParser error handling requires careful testing approach
"""

import unittest
from unittest.mock import MagicMock, patch
import argparse
import io
import sys
from contextlib import redirect_stdout

from refactor.cli.commands.document import DocumentCommand
from refactor.core.entities.document_section_entity import (
    DocumentSection,
    SectionType,
    DocumentFormat
)
from refactor.core.exceptions import (
    EntityNotFoundError,
    ValidationError,
    BusinessRuleViolationError
)


class TestDocumentCommand(unittest.TestCase):
    """Test suite for the DocumentCommand class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create mocked core manager and services
        self.core_manager = MagicMock()
        self.document_service = MagicMock()
        self.document_section_service = MagicMock()
        
        # Configure core manager to return mocked services
        self.core_manager.get_document_service.return_value = self.document_service
        self.core_manager.get_document_section_service.return_value = self.document_section_service
        
        # Create command instance
        self.command = DocumentCommand(self.core_manager)
        
        # Create sample document sections for testing
        self.section1 = DocumentSection(
            entity_id="sec_123",
            name="Introduction",
            content="This is the introduction",
            section_type=SectionType.INTRODUCTION.value,
            format=DocumentFormat.MARKDOWN.value,
            document_id="tsk_doc123",
            index=0,
            tags=["intro"],
            entity_ids=[]
        )
        
        self.section2 = DocumentSection(
            entity_id="sec_456",
            name="Installation",
            content="Installation instructions",
            section_type=SectionType.INSTALLATION.value,
            format=DocumentFormat.MARKDOWN.value,
            document_id="tsk_doc123",
            index=1,
            tags=["setup"],
            entity_ids=[]
        )

    def test_subcommand_registration(self):
        """Test that subcommands are registered correctly."""
        parser = argparse.ArgumentParser()
        
        # Configure the parser using the command's method
        self.command.configure_parser(parser)
        
        # This test needs adjustment. Instead of checking subparsers directly,
        # we should test if parsing known subcommands works.
        # Try parsing args for each subcommand
        subcommands = [
            "section-add", "section-update", "section-remove",
            "section-list", "section-reorder"
        ]
        
        for subcmd in subcommands:
            try:
                # Attempt to parse minimal args for each subcommand to check registration
                # This requires knowing the minimal required args for each.
                if subcmd == "section-add":
                    parser.parse_args([subcmd, "--name", "t", "--content", "c", "--task-id", "tid"])
                elif subcmd == "section-update":
                     parser.parse_args([subcmd, "--section-id", "sid", "--name", "n"])
                elif subcmd == "section-remove":
                     parser.parse_args([subcmd, "--section-id", "sid"])
                elif subcmd == "section-list":
                     parser.parse_args([subcmd, "--task-id", "tid"])
                elif subcmd == "section-reorder":
                     parser.parse_args([subcmd, "--task-id", "tid", "--section-ids", "s1,s2"])
                # If parsing doesn't raise an error, the subcommand is likely registered.
            except SystemExit as e:
                # argparse raises SystemExit on error
                self.fail(f"Subcommand '{subcmd}' failed to parse minimal arguments. Error: {e}")

    def test_section_add_command(self):
        """Test adding a document section."""
        # Arrange
        self.document_section_service.add_section.return_value = self.section1
        
        args = argparse.Namespace(
            document_command="section-add",
            name="Introduction",
            content="This is the introduction",
            task_id="tsk_doc123",
            section_type=SectionType.CUSTOM.value,
            format=DocumentFormat.MARKDOWN.value,
            index=None,
            tags=["intro"],
            entity_ids=[]
        )
        
        # Act
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            exit_code = self.command.execute(args)
            output = fake_out.getvalue()
        
        # Assert
        self.assertEqual(exit_code, 0)
        self.document_section_service.add_section.assert_called_once_with(
            name="Introduction",
            content="This is the introduction",
            task_id="tsk_doc123",
            section_type=SectionType.CUSTOM.value,
            format=DocumentFormat.MARKDOWN.value,
            index=None,
            tags=["intro"],
            entity_references=[]
        )
        self.assertIn("Added document section", output)
        self.assertIn("sec_123", output)

    def test_section_add_command_error(self):
        """Test error handling when adding a document section."""
        # Arrange
        self.document_section_service.add_section.side_effect = EntityNotFoundError(
            "tsk_nonexistent", "Task"
        )
        
        args = argparse.Namespace(
            document_command="section-add",
            name="Introduction",
            content="This is the introduction",
            task_id="tsk_nonexistent",
            section_type=SectionType.CUSTOM.value,
            format=DocumentFormat.MARKDOWN.value,
            index=None,
            tags=[],
            entity_ids=[]
        )
        
        # Act
        with patch("sys.stdout", new=io.StringIO()):
            exit_code = self.command.execute(args)
        
        # Assert
        self.assertNotEqual(exit_code, 0)  # Should return error code
        self.document_section_service.add_section.assert_called_once()

    def test_section_update_command(self):
        """Test updating a document section."""
        # Arrange
        self.document_section_service.update_section.return_value = self.section1
        
        args = argparse.Namespace(
            document_command="section-update",
            section_id="sec_123",
            name="Updated Introduction",
            content="Updated content",
            section_type=SectionType.CUSTOM.value,
            format=DocumentFormat.MARKDOWN.value,
            tags=["intro", "updated"],
            entity_ids=["tsk_code123"]
        )
        
        # Act
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            exit_code = self.command.execute(args)
            output = fake_out.getvalue()
        
        # Assert
        self.assertEqual(exit_code, 0)
        self.document_section_service.update_section.assert_called_once_with(
            section_id="sec_123",
            name="Updated Introduction",
            content="Updated content",
            section_type=SectionType.CUSTOM.value,
            format=DocumentFormat.MARKDOWN.value,
            tags=["intro", "updated"],
            entity_references=["tsk_code123"]
        )
        self.assertIn("Updated document section", output)
        self.assertIn("sec_123", output)

    def test_section_update_command_error(self):
        """Test error handling when updating a document section."""
        # Arrange
        self.document_section_service.update_section.side_effect = EntityNotFoundError(
            "sec_nonexistent", "DocumentSection"
        )
        
        args = argparse.Namespace(
            document_command="section-update",
            section_id="sec_nonexistent",
            name="Updated Section",
            content="Updated content",
            section_type=None,
            format=None,
            tags=None,
            entity_ids=None
        )
        
        # Act
        with patch("sys.stdout", new=io.StringIO()):
            exit_code = self.command.execute(args)
        
        # Assert
        self.assertNotEqual(exit_code, 0)  # Should return error code

    def test_section_remove_command(self):
        """Test removing a document section."""
        # Arrange
        self.document_section_service.remove_section.return_value = True
        self.document_section_service.get_section.return_value = self.section1
        
        args = argparse.Namespace(
            document_command="section-remove",
            section_id="sec_123",
            force=True
        )
        
        # Act
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            exit_code = self.command.execute(args)
            output = fake_out.getvalue()
        
        # Assert
        self.assertEqual(exit_code, 0)
        self.document_section_service.remove_section.assert_called_once_with("sec_123")
        self.assertIn("Removed document section", output)
        self.assertIn("sec_123", output)

    def test_section_remove_command_with_confirmation(self):
        """Test removing a document section with confirmation."""
        # Arrange
        self.document_section_service.get_section.return_value = self.section1
        
        args = argparse.Namespace(
            document_command="section-remove",
            section_id="sec_123",
            force=False
        )
        
        # Act
        with patch("builtins.input", return_value="y"), \
             patch("sys.stdout", new=io.StringIO()) as fake_out:
            exit_code = self.command.execute(args)
            output = fake_out.getvalue()
        
        # Assert
        self.assertEqual(exit_code, 0)
        self.document_section_service.remove_section.assert_called_once_with("sec_123")
        self.assertIn("Removed document section", output)

    def test_section_remove_command_cancel_confirmation(self):
        """Test canceling section removal during confirmation."""
        # Arrange
        self.document_section_service.get_section.return_value = self.section1
        
        args = argparse.Namespace(
            document_command="section-remove",
            section_id="sec_123",
            force=False
        )
        
        # Act
        with patch("builtins.input", return_value="n"), \
             patch("sys.stdout", new=io.StringIO()) as fake_out:
            exit_code = self.command.execute(args)
            output = fake_out.getvalue()
        
        # Assert
        self.assertEqual(exit_code, 0)
        self.document_section_service.remove_section.assert_not_called()
        self.assertIn("Operation canceled", output)

    def test_section_list_command(self):
        """Test listing document sections for a task."""
        # Arrange
        self.document_section_service.get_sections_by_task.return_value = [
            self.section1, self.section2
        ]
        
        args = argparse.Namespace(
            document_command="section-list",
            task_id="tsk_doc123",
            format="table",
            group_by_type=False,
            tag=None
        )
        
        # Act
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            exit_code = self.command.execute(args)
            output = fake_out.getvalue()
        
        # Assert
        self.assertEqual(exit_code, 0)
        self.document_section_service.get_sections_by_task.assert_called_once_with("tsk_doc123")
        self.assertIn("Introduction", output)
        self.assertIn("Installation", output)
        self.assertIn("sec_123", output)
        self.assertIn("sec_456", output)

    def test_section_list_command_with_tag_filter(self):
        """Test listing document sections with tag filtering."""
        # Arrange
        self.document_section_service.find_sections_by_tag.return_value = [self.section1]
        
        args = argparse.Namespace(
            document_command="section-list",
            task_id="tsk_doc123",
            format="table",
            group_by_type=False,
            tag="intro"
        )
        
        # Act
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            exit_code = self.command.execute(args)
            output = fake_out.getvalue()
        
        # Assert
        self.assertEqual(exit_code, 0)
        self.document_section_service.find_sections_by_tag.assert_called_once_with("intro")
        # Further filter by task_id would be handled by the command
        self.assertIn("Introduction", output)
        self.assertNotIn("Installation", output)

    def test_section_list_json_format(self):
        """Test listing document sections in JSON format."""
        # Arrange
        self.document_section_service.get_sections_by_task.return_value = [
            self.section1, self.section2
        ]
        
        args = argparse.Namespace(
            document_command="section-list",
            task_id="tsk_doc123",
            format="json",
            group_by_type=False,
            tag=None
        )
        
        # Act
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            exit_code = self.command.execute(args)
            output = fake_out.getvalue()
        
        # Assert
        self.assertEqual(exit_code, 0)
        self.assertIn('"id": "sec_123"', output)
        self.assertIn('"name": "Introduction"', output)
        self.assertIn('"id": "sec_456"', output)
        self.assertIn('"name": "Installation"', output)

    def test_section_list_grouped_by_type(self):
        """Test listing document sections grouped by type."""
        # Arrange
        self.document_section_service.get_sections_by_task.return_value = [
            self.section1, self.section2
        ]
        
        args = argparse.Namespace(
            document_command="section-list",
            task_id="tsk_doc123",
            format="table",
            group_by_type=True,
            tag=None
        )
        
        # Act
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            exit_code = self.command.execute(args)
            output = fake_out.getvalue()
        
        # Assert
        self.assertEqual(exit_code, 0)
        # Should contain type headers
        self.assertIn("TEXT", output)
        self.assertIn("INSTRUCTIONS", output)

    def test_section_reorder_command(self):
        """Test reordering document sections."""
        # Arrange
        self.document_section_service.reorder_sections.return_value = True
        
        args = argparse.Namespace(
            document_command="section-reorder",
            task_id="tsk_doc123",
            section_ids=["sec_456", "sec_123"]  # Reverse order
        )
        
        # Act
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            exit_code = self.command.execute(args)
            output = fake_out.getvalue()
        
        # Assert
        self.assertEqual(exit_code, 0)
        self.document_section_service.reorder_sections.assert_called_once_with(
            "tsk_doc123", ["sec_456", "sec_123"]
        )
        self.assertIn("Reordered document sections", output)

    def test_section_reorder_command_error(self):
        """Test error handling when reordering document sections."""
        # Arrange
        self.document_section_service.reorder_sections.side_effect = BusinessRuleViolationError(
            "Invalid section order", "Some sections don't belong to the task"
        )
        
        args = argparse.Namespace(
            document_command="section-reorder",
            task_id="tsk_doc123",
            section_ids=["sec_123", "sec_nonexistent"]
        )
        
        # Act
        with patch("sys.stdout", new=io.StringIO()):
            exit_code = self.command.execute(args)
        
        # Assert
        self.assertNotEqual(exit_code, 0)  # Should return error code

    def test_execute_unknown_command(self):
        """Test handling of unknown subcommands."""
        # Arrange
        args = argparse.Namespace(
            document_command="unknown-command"
        )
        
        # Act
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            exit_code = self.command.execute(args)
            output = fake_out.getvalue()
        
        # Assert
        self.assertNotEqual(exit_code, 0)  # Should return error code
        self.assertIn("Unknown document command", output) 