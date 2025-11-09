"""
Task: tsk_9b0dc32e - Create Documentation CLI Commands
Document: refactor/cli/commands/document.py
dohcount: 1

Related Tasks:
    - tsk_708256de - Documentation Features Implementation (parent)
    - tsk_783ad768 - Implement Document Section Management (depends on)
    - tsk_22c4ba4c - Implement Document Relationship Types (depends on)

Used By:
    - Main CLI: For document section management operations
    - Task Workflows: For handling documentation-specific operations

Purpose:
    Provides CLI commands for managing documentation tasks and document sections,
    including creating, updating, viewing, and organizing document sections.

Requirements:
    - Must follow the Command pattern used in the codebase
    - Must expose all DocumentSectionService functionality to CLI users
    - Must provide useful help text and examples
    - CRITICAL: Must validate user input before passing to service layer
    - CRITICAL: Must properly integrate with dependency injection system

Parameters:
    N/A - This is a command module file

Returns:
    N/A - This is a command module file

Changes:
    - v1: Initial implementation with document section management commands

Lessons Learned:
    - CLI commands should delegate business logic to service layer
    - Command output formats should be consistent across the application
"""

from argparse import ArgumentParser, Namespace
from typing import Dict, List, Optional, Union, Any
import logging
from datetime import datetime

from refactor.cli.command import Command
from refactor.core.interfaces.core_manager import CoreManager
from refactor.core.entities.document_section_entity import DocumentSection, SectionType, DocumentFormat
from refactor.cli.error_handling import CLIError, handle_cli_error
from refactor.core.exceptions import (
    ErrorCode,
    get_command_error_code,
    get_storage_error_code,
    get_validation_error_code,
    get_repo_error_code
)
from refactor.utils.colors import (
    TextColor, TextStyle, DefaultTheme, colorize, 
    status_color, priority_color, score_color, relationship_color
)

logger = logging.getLogger(__name__)


class SectionAddCommand(Command):
    """Command for adding a document section."""
    
    def __init__(self, core_manager: CoreManager):
        """
        Initialize with a core manager.
        
        Args:
            core_manager: Core manager instance
        """
        self._core_manager = core_manager
        
    @property
    def name(self) -> str:
        """Get the command name."""
        return "section-add"
        
    @property
    def description(self) -> str:
        """Get the command description."""
        return "Add a section to a documentation task"
        
    def configure_parser(self, parser: ArgumentParser) -> None:
        """
        Configure the parser for section add command.
        
        Args:
            parser: The parser to configure
        """
        parser.add_argument("template", help="Template file to update")
        parser.add_argument("document_id", help="ID or name of the documentation task")
        parser.add_argument("name", help="Section name/title")
        parser.add_argument("--content", help="Section content (text)")
        parser.add_argument(
            "--type", 
            choices=[t.value for t in SectionType],
            default=SectionType.CUSTOM.value,
            help="Section type"
        )
        parser.add_argument(
            "--format",
            choices=[f.value for f in DocumentFormat],
            default=DocumentFormat.MARKDOWN.value,
            help="Section format"
        )
        parser.add_argument(
            "--index",
            type=int,
            help="Position index for section (default: end)"
        )
        parser.add_argument(
            "--tags",
            help="Comma-separated list of tags"
        )
        parser.add_argument(
            "--entity-ids",
            help="Comma-separated list of entity IDs referenced in this section"
        )
        
    def execute(self, args: Namespace) -> Union[int, str]:
        """
        Execute the section add command.
        
        Args:
            args: Parsed arguments
            
        Returns:
            Exit code (0 for success) or error code string
        """
        try:
            # Initialize core manager
            self._core_manager.initialize(args.template)
            
            # Get document task by ID or name
            document_task = None
            try:
                # Try by ID first
                document_task = self._core_manager.get_task(args.document_id)
            except:
                try:
                    # Then try by name
                    document_task = self._core_manager.get_task_by_name(args.document_id)
                except Exception as e:
                    raise CLIError(f"Document task not found: {args.document_id}", 
                                  get_repo_error_code("TASK", "001"))
            
            # Process tags if provided
            tags = None
            if args.tags:
                tags = [tag.strip() for tag in args.tags.split(",")]
                
            # Process entity IDs if provided
            entity_ids = None
            if args.entity_ids:
                entity_ids = [entity_id.strip() for entity_id in args.entity_ids.split(",")]
            
            # Get document service
            document_section_service = self._core_manager.get_document_section_service()
            
            # Add the section
            section = document_section_service.add_section(
                document_id=document_task["id"],
                name=args.name,
                content=args.content or "",
                section_type=args.type,
                format=args.format,
                index=args.index,
                tags=tags,
                entity_ids=entity_ids
            )
            
            # Save changes
            self._core_manager.save()
            
            # Output success message
            print(f"Added section '{args.name}' to document '{document_task['name']}' (ID: {section.id})")
            return 0
            
        except Exception as e:
            logger.error(f"Error adding section: {str(e)}", exc_info=True)
            print(f"Error adding section: {str(e)}")
            return 1


class SectionUpdateCommand(Command):
    """Command for updating a document section."""
    
    def __init__(self, core_manager: CoreManager):
        """
        Initialize with a core manager.
        
        Args:
            core_manager: Core manager instance
        """
        self._core_manager = core_manager
        
    @property
    def name(self) -> str:
        """Get the command name."""
        return "section-update"
        
    @property
    def description(self) -> str:
        """Get the command description."""
        return "Update a document section"
        
    def configure_parser(self, parser: ArgumentParser) -> None:
        """
        Configure the parser for section update command.
        
        Args:
            parser: The parser to configure
        """
        parser.add_argument("template", help="Template file to update")
        parser.add_argument("section_id", help="ID of the section to update")
        parser.add_argument("--name", help="New section name/title")
        parser.add_argument("--content", help="New section content (text)")
        parser.add_argument(
            "--type", 
            choices=[t.value for t in SectionType],
            help="New section type"
        )
        parser.add_argument(
            "--format",
            choices=[f.value for f in DocumentFormat],
            help="New section format"
        )
        parser.add_argument(
            "--tags",
            help="Comma-separated list of tags (replaces existing tags)"
        )
        parser.add_argument(
            "--entity-ids",
            help="Comma-separated list of entity IDs (replaces existing references)"
        )
        
    def execute(self, args: Namespace) -> Union[int, str]:
        """
        Execute the section update command.
        
        Args:
            args: Parsed arguments
            
        Returns:
            Exit code (0 for success) or error code string
        """
        try:
            # Initialize core manager
            self._core_manager.initialize(args.template)
            
            # Process tags if provided
            tags = None
            if args.tags:
                tags = [tag.strip() for tag in args.tags.split(",")]
                
            # Process entity IDs if provided
            entity_ids = None
            if args.entity_ids:
                entity_ids = [entity_id.strip() for entity_id in args.entity_ids.split(",")]
            
            # Get document service
            document_section_service = self._core_manager.get_document_section_service()
            
            # Make sure at least one update field is provided
            if all(value is None for value in [args.name, args.content, args.type, args.format, tags, entity_ids]):
                raise CLIError("No update fields provided", get_command_error_code("PARAMS", "001"))
            
            # Update the section
            section = document_section_service.update_section(
                section_id=args.section_id,
                name=args.name,
                content=args.content,
                section_type=args.type,
                format=args.format,
                tags=tags,
                entity_ids=entity_ids
            )
            
            # Save changes
            self._core_manager.save()
            
            # Output success message
            print(f"Updated section '{section.name}' (ID: {section.id})")
            return 0
            
        except Exception as e:
            logger.error(f"Error updating section: {str(e)}", exc_info=True)
            print(f"Error updating section: {str(e)}")
            return 1


class SectionRemoveCommand(Command):
    """Command for removing a document section."""
    
    def __init__(self, core_manager: CoreManager):
        """
        Initialize with a core manager.
        
        Args:
            core_manager: Core manager instance
        """
        self._core_manager = core_manager
        
    @property
    def name(self) -> str:
        """Get the command name."""
        return "section-remove"
        
    @property
    def description(self) -> str:
        """Get the command description."""
        return "Remove a document section"
        
    def configure_parser(self, parser: ArgumentParser) -> None:
        """
        Configure the parser for section remove command.
        
        Args:
            parser: The parser to configure
        """
        parser.add_argument("template", help="Template file to update")
        parser.add_argument("section_id", help="ID of the section to remove")
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force removal without confirmation"
        )
        
    def execute(self, args: Namespace) -> Union[int, str]:
        """
        Execute the section remove command.
        
        Args:
            args: Parsed arguments
            
        Returns:
            Exit code (0 for success) or error code string
        """
        try:
            # Initialize core manager
            self._core_manager.initialize(args.template)
            
            # Get document service
            document_section_service = self._core_manager.get_document_section_service()
            
            # Get section for display in confirmation
            try:
                # Get section to show details
                section_repository = self._core_manager.get_document_section_repository()
                section = section_repository.get_by_id(args.section_id)
                section_name = section.name
                document_id = section.document_id
            except:
                raise CLIError(f"Section not found: {args.section_id}", 
                              get_repo_error_code("SECTION", "001"))
            
            # Confirm removal if not forced
            if not args.force:
                confirm = input(f"Are you sure you want to remove section '{section_name}' (ID: {args.section_id})? [y/N] ")
                if confirm.lower() not in ["y", "yes"]:
                    print("Operation cancelled.")
                    return 0
            
            # Remove the section
            document_section_service.remove_section(args.section_id)
            
            # Save changes
            self._core_manager.save()
            
            # Output success message
            print(f"Removed section '{section_name}' (ID: {args.section_id})")
            return 0
            
        except Exception as e:
            logger.error(f"Error removing section: {str(e)}", exc_info=True)
            print(f"Error removing section: {str(e)}")
            return 1


class SectionListCommand(Command):
    """Command for listing document sections."""
    
    def __init__(self, core_manager: CoreManager):
        """
        Initialize with a core manager.
        
        Args:
            core_manager: Core manager instance
        """
        self._core_manager = core_manager
        
    @property
    def name(self) -> str:
        """Get the command name."""
        return "section-list"
        
    @property
    def description(self) -> str:
        """Get the command description."""
        return "List sections in a document"
        
    def configure_parser(self, parser: ArgumentParser) -> None:
        """
        Configure the parser for section list command.
        
        Args:
            parser: The parser to configure
        """
        parser.add_argument("template", help="Template file to read")
        parser.add_argument("document_id", help="ID or name of the documentation task")
        parser.add_argument(
            "--format",
            choices=["simple", "detailed"],
            default="simple",
            help="Output format (simple: names only, detailed: all metadata)"
        )
        parser.add_argument(
            "--by-type",
            action="store_true",
            help="Group sections by type"
        )
        parser.add_argument(
            "--tag",
            help="Filter sections by tag"
        )
        
    def execute(self, args: Namespace) -> Union[int, str]:
        """
        Execute the section list command.
        
        Args:
            args: Parsed arguments
            
        Returns:
            Exit code (0 for success) or error code string
        """
        try:
            # Initialize core manager
            self._core_manager.initialize(args.template)
            
            # Get document task by ID or name
            document_task = None
            try:
                # Try by ID first
                document_task = self._core_manager.get_task(args.document_id)
            except:
                try:
                    # Then try by name
                    document_task = self._core_manager.get_task_by_name(args.document_id)
                except Exception as e:
                    raise CLIError(f"Document task not found: {args.document_id}", 
                                  get_repo_error_code("TASK", "001"))
            
            # Get document service
            document_section_service = self._core_manager.get_document_section_service()
            
            # Get sections
            sections = document_section_service.get_sections(document_task["id"])
            
            # Filter by tag if requested
            if args.tag:
                sections = [s for s in sections if args.tag in s.tags]
            
            # Check if any sections were found
            if not sections:
                print(f"No sections found for document '{document_task['name']}' (ID: {document_task['id']})")
                return 0
            
            # Output sections
            print(f"Sections for document '{document_task['name']}' (ID: {document_task['id']}):")
            print("")
            
            if args.by_type:
                # Group by type
                section_types = {}
                for section in sections:
                    section_type = section.section_type.value
                    if section_type not in section_types:
                        section_types[section_type] = []
                    section_types[section_type].append(section)
                
                # Display by type
                for section_type, type_sections in sorted(section_types.items()):
                    print(f"{section_type.upper()}:")
                    for section in sorted(type_sections, key=lambda s: s.index):
                        if args.format == "simple":
                            print(f"  [{section.index}] {section.name} (ID: {section.id})")
                        else:
                            self._print_detailed_section(section, indent="  ")
                    print("")
            else:
                # Display in index order
                for section in sorted(sections, key=lambda s: s.index):
                    if args.format == "simple":
                        print(f"[{section.index}] {section.name} (ID: {section.id})")
                    else:
                        self._print_detailed_section(section)
                        print("")
            
            return 0
            
        except Exception as e:
            logger.error(f"Error listing sections: {str(e)}", exc_info=True)
            print(f"Error listing sections: {str(e)}")
            return 1
    
    def _print_detailed_section(self, section: DocumentSection, indent: str = "") -> None:
        """
        Print detailed section information.
        
        Args:
            section: The section to print
            indent: Indentation to apply
        """
        print(f"{indent}[{section.index}] {colorize(section.name, TextColor.BRIGHT_CYAN, TextStyle.BOLD)} (ID: {section.id})")
        print(f"{indent}  Type: {section.section_type.value}")
        print(f"{indent}  Format: {section.format.value}")
        if section.tags:
            print(f"{indent}  Tags: {', '.join(section.tags)}")
        if section.entity_ids:
            print(f"{indent}  Referenced Entities: {', '.join(section.entity_ids)}")
        if section.content and len(section.content) > 80:
            # Truncate long content
            content_preview = section.content[:77] + "..."
            print(f"{indent}  Content Preview: {content_preview}")
        elif section.content:
            print(f"{indent}  Content: {section.content}")


class SectionReorderCommand(Command):
    """Command for reordering document sections."""
    
    def __init__(self, core_manager: CoreManager):
        """
        Initialize with a core manager.
        
        Args:
            core_manager: Core manager instance
        """
        self._core_manager = core_manager
        
    @property
    def name(self) -> str:
        """Get the command name."""
        return "section-reorder"
        
    @property
    def description(self) -> str:
        """Get the command description."""
        return "Reorder sections in a document"
        
    def configure_parser(self, parser: ArgumentParser) -> None:
        """
        Configure the parser for section reorder command.
        
        Args:
            parser: The parser to configure
        """
        parser.add_argument("template", help="Template file to update")
        parser.add_argument("document_id", help="ID or name of the documentation task")
        parser.add_argument(
            "section_order",
            help="Comma-separated list of section IDs in desired order"
        )
        
    def execute(self, args: Namespace) -> Union[int, str]:
        """
        Execute the section reorder command.
        
        Args:
            args: Parsed arguments
            
        Returns:
            Exit code (0 for success) or error code string
        """
        try:
            # Initialize core manager
            self._core_manager.initialize(args.template)
            
            # Get document task by ID or name
            document_task = None
            try:
                # Try by ID first
                document_task = self._core_manager.get_task(args.document_id)
            except:
                try:
                    # Then try by name
                    document_task = self._core_manager.get_task_by_name(args.document_id)
                except Exception as e:
                    raise CLIError(f"Document task not found: {args.document_id}", 
                                  get_repo_error_code("TASK", "001"))
            
            # Parse section order
            section_order = [section_id.strip() for section_id in args.section_order.split(",")]
            
            # Get document service
            document_section_service = self._core_manager.get_document_section_service()
            
            # Reorder sections
            document_section_service.reorder_sections(
                document_id=document_task["id"],
                section_order=section_order
            )
            
            # Save changes
            self._core_manager.save()
            
            # Output success message
            print(f"Reordered sections in document '{document_task['name']}' (ID: {document_task['id']})")
            return 0
            
        except Exception as e:
            logger.error(f"Error reordering sections: {str(e)}", exc_info=True)
            print(f"Error reordering sections: {str(e)}")
            return 1


class DocumentCommand(Command):
    """Command for managing documentation tasks and sections."""
    
    def __init__(self, core_manager: CoreManager):
        """
        Initialize with a core manager.
        
        Args:
            core_manager: Core manager instance
        """
        self._core_manager = core_manager
        self._subcommands = {}
        
        # Register subcommands
        self.add_subcommand(SectionAddCommand(core_manager))
        self.add_subcommand(SectionUpdateCommand(core_manager))
        self.add_subcommand(SectionRemoveCommand(core_manager))
        self.add_subcommand(SectionListCommand(core_manager))
        self.add_subcommand(SectionReorderCommand(core_manager))
        
    @property
    def name(self) -> str:
        """Get the command name."""
        return "document"
        
    @property
    def description(self) -> str:
        """Get the command description."""
        return "Manage documentation tasks and sections"
        
    def add_subcommand(self, command: Command) -> None:
        """
        Add a subcommand.
        
        Args:
            command: The command to add
        """
        self._subcommands[command.name] = command
        
    def configure_parser(self, parser: ArgumentParser) -> None:
        """
        Configure the parser for document command.
        
        Args:
            parser: The parser to configure
        """
        subparsers = parser.add_subparsers(
            dest="doc_command",
            title="document commands",
            help="Available document commands"
        )
        subparsers.required = True
        
        # Configure subcommands
        for name, command in self._subcommands.items():
            subparser = subparsers.add_parser(name, help=command.description)
            command.configure_parser(subparser)
            
    def execute(self, args: Namespace) -> Union[int, str]:
        """
        Execute the document command.
        
        Args:
            args: Parsed arguments
            
        Returns:
            Exit code (0 for success) or error code string
        """
        try:
            # Delegate to the appropriate subcommand
            if args.doc_command in self._subcommands:
                return self._subcommands[args.doc_command].execute(args)
            else:
                print(f"Unknown document command: {args.doc_command}")
                return 1
        except Exception as e:
            logger.error(f"Error executing document command: {str(e)}", exc_info=True)
            print(f"Error executing document command: {str(e)}")
            return 1 