"""
Saved Search Commands

This module provides commands for managing saved searches, including:
- Saving a search query
- Loading a saved search query
- Listing all saved searches
- Deleting a saved search
"""

from argparse import ArgumentParser, Namespace
from typing import Dict, List, Optional, Any, Union
import json
import logging

from refactor.cli.command import Command
from refactor.core.interfaces.core_manager import CoreManager
from refactor.storage.saved_searches import SavedSearchesManager, SavedSearch
from refactor.cli.error_handling import CLIError, handle_cli_error
from refactor.core.exceptions import (
    ErrorCode,
    get_storage_error_code,
    get_command_error_code
)

logger = logging.getLogger(__name__)


class SaveSearchCommand(Command):
    """Command for saving a search query."""
    
    def __init__(self, core_manager: CoreManager):
        """Initialize with a core manager."""
        self._core_manager = core_manager
        self._searches_manager = SavedSearchesManager()
    
    @property
    def name(self) -> str:
        """Get the command name."""
        return "save"
    
    @property
    def description(self) -> str:
        """Get the command description."""
        return "Save a search query for later use"
    
    def configure_parser(self, parser: ArgumentParser) -> None:
        """Configure the parser for save command."""
        parser.add_argument("name", help="Name for the saved search")
        parser.add_argument("query", help="Search query to save")
        parser.add_argument("--description", help="Description of the saved search")
        parser.add_argument("--tags", help="Comma-separated list of tags")
        parser.add_argument("--category", default="general", 
                           help="Category for organizing the search (default: general)")
    
    def execute(self, args: Namespace) -> Union[int, str]:
        """Execute the save search command."""
        try:
            # Parse tags
            tags = None
            if args.tags:
                tags = [tag.strip() for tag in args.tags.split(",")]
            
            # Save the search
            search = self._searches_manager.save_search(
                name=args.name,
                query=args.query,
                description=args.description or "",
                tags=tags,
                category=args.category
            )
            
            print(f"Search saved successfully as '{args.name}'")
            return 0
        except Exception as e:
            logger.error(f"Failed to save search: {str(e)}", exc_info=True)
            print(f"Error: Failed to save search: {str(e)}")
            return 1


class ListSearchesCommand(Command):
    """Command for listing saved searches."""
    
    def __init__(self, core_manager: CoreManager):
        """Initialize with a core manager."""
        self._core_manager = core_manager
        self._searches_manager = SavedSearchesManager()
    
    @property
    def name(self) -> str:
        """Get the command name."""
        return "list"
    
    @property
    def description(self) -> str:
        """Get the command description."""
        return "List all saved searches"
    
    def configure_parser(self, parser: ArgumentParser) -> None:
        """Configure the parser for list command."""
        parser.add_argument("--tag", help="Filter by tag")
        parser.add_argument("--category", help="Filter by category")
        parser.add_argument("--name-contains", help="Filter by part of name")
        parser.add_argument("--sort-by", choices=["name", "created_at", "last_used_at", "use_count"], 
                           default="name", help="Sort results by field (default: name)")
        parser.add_argument("--format", choices=["table", "json"], default="table",
                            help="Output format (default: table)")
        parser.add_argument("--show-categories", action="store_true", 
                           help="List all available categories")
        parser.add_argument("--show-tags", action="store_true",
                           help="List all available tags")
    
    def execute(self, args: Namespace) -> Union[int, str]:
        """Execute the list searches command."""
        try:
            # Check if we should just show categories or tags
            if args.show_categories:
                categories = self._searches_manager.list_categories()
                if not categories:
                    print("No categories found.")
                    return 0
                    
                print(f"Available categories ({len(categories)}):")
                for category in sorted(categories):
                    print(f"  - {category}")
                return 0
                
            if args.show_tags:
                tags = self._searches_manager.list_tags()
                if not tags:
                    print("No tags found.")
                    return 0
                    
                print(f"Available tags ({len(tags)}):")
                for tag in sorted(tags):
                    print(f"  - {tag}")
                return 0
                
            # Get searches with filtering and sorting
            searches = self._searches_manager.list_searches(
                tag=args.tag,
                category=args.category,
                name_contains=args.name_contains,
                sort_by=args.sort_by
            )
            
            if not searches:
                print("No saved searches found")
                if args.tag or args.category or args.name_contains:
                    print("Try removing some filters to see more results.")
                return 0
            
            # Output in requested format
            if args.format == "json":
                searches_data = [search.to_dict() for search in searches]
                print(json.dumps(searches_data, indent=2))
            else:
                # Group by category if requested
                print(f"Found {len(searches)} saved searches:\n")
                
                # Sort by category first if showing categories
                if args.sort_by == "name" and not args.category:
                    searches.sort(key=lambda s: (s.category, s.name))
                    
                    # Group by category for display
                    by_category = {}
                    for search in searches:
                        if search.category not in by_category:
                            by_category[search.category] = []
                        by_category[search.category].append(search)
                    
                    for category, cat_searches in sorted(by_category.items()):
                        print(f"Category: {category}")
                        print("-" * (10 + len(category)))
                        
                        for search in cat_searches:
                            print(f"  Name: {search.name}")
                            print(f"  Query: {search.query}")
                            if search.description:
                                print(f"  Description: {search.description}")
                            if search.tags:
                                print(f"  Tags: {', '.join(search.tags)}")
                            print(f"  Used: {search.use_count} times")
                            print()
                else:
                    # Just display as a flat list
                    for search in searches:
                        print(f"Name: {search.name}")
                        print(f"Category: {search.category}")
                        print(f"Query: {search.query}")
                        if search.description:
                            print(f"Description: {search.description}")
                        if search.tags:
                            print(f"Tags: {', '.join(search.tags)}")
                        print(f"Used: {search.use_count} times")
                        print()
            
            return 0
        except Exception as e:
            logger.error(f"Failed to list searches: {str(e)}", exc_info=True)
            print(f"Error: Failed to list searches: {str(e)}")
            return 1


class LoadSearchCommand(Command):
    """Command for loading and executing a saved search."""
    
    def __init__(self, core_manager: CoreManager):
        """Initialize with a core manager."""
        self._core_manager = core_manager
        self._searches_manager = SavedSearchesManager()
    
    @property
    def name(self) -> str:
        """Get the command name."""
        return "load"
    
    @property
    def description(self) -> str:
        """Get the command description."""
        return "Load and execute a saved search"
    
    def configure_parser(self, parser: ArgumentParser) -> None:
        """Configure the parser for load command."""
        parser.add_argument("name", help="Name of the saved search to load")
        # Add same parameters as search command for overrides
        parser.add_argument("--entity", choices=["task", "list", "folder", "space"],
                            default="task", help="Entity type to query (default: task)")
        parser.add_argument("--format", choices=["table", "json"], default="table",
                           help="Output format (default: table)")
        parser.add_argument("--limit", type=int, default=50,
                           help="Limit number of results (default: 50)")
        parser.add_argument("--offset", type=int, default=0,
                           help="Offset for paginated results (default: 0)")
    
    def execute(self, args: Namespace) -> Union[int, str]:
        """Execute the load search command."""
        try:
            # Get the saved search
            search = self._searches_manager.get_search(args.name)
            print(f"Executing saved search '{args.name}':")
            print(f"Query: {search.query}\n")
            
            # Execute the query
            results = self._core_manager.execute_query(
                query=search.query,
                entity_type=args.entity,
                limit=args.limit,
                offset=args.offset
            )
            
            # Display results
            if not results:
                print(f"No {args.entity}s found matching the query")
                return 0
            
            if args.format == "json":
                # Convert results to JSON format
                result_list = [item.to_dict() for item in results]
                print(json.dumps(result_list, indent=2))
            else:
                # Display as table
                print(f"Found {len(results)} {args.entity}s matching the query:\n")
                
                # Display appropriate fields based on entity type
                if args.entity == "task":
                    for task in results:
                        print(f"Task: {task.name}")
                        print(f"ID: {task.id}")
                        if hasattr(task, 'status'):
                            print(f"Status: {task.status}")
                        if hasattr(task, 'priority'):
                            print(f"Priority: {task.priority}")
                        print()
                elif args.entity == "list":
                    for list_item in results:
                        print(f"List: {list_item.name}")
                        print(f"ID: {list_item.id}")
                        if hasattr(list_item, 'folder_id'):
                            print(f"Folder: {list_item.folder_id}")
                        print()
                elif args.entity == "folder":
                    for folder in results:
                        print(f"Folder: {folder.name}")
                        print(f"ID: {folder.id}")
                        if hasattr(folder, 'space_id'):
                            print(f"Space: {folder.space_id}")
                        print()
                elif args.entity == "space":
                    for space in results:
                        print(f"Space: {space.name}")
                        print(f"ID: {space.id}")
                        print()
            
            # Display pagination info if limited
            if args.limit < len(results):
                print(f"Showing {args.limit} of {len(results)} total results.")
                print(f"Use --offset {args.offset + args.limit} to see the next page.")
            
            return 0
        except Exception as e:
            logger.error(f"Failed to load search: {str(e)}", exc_info=True)
            print(f"Error: Failed to load search: {str(e)}")
            return 1


class UpdateSearchCommand(Command):
    """Command for updating a saved search."""
    
    def __init__(self, core_manager: CoreManager):
        """Initialize with a core manager."""
        self._core_manager = core_manager
        self._searches_manager = SavedSearchesManager()
    
    @property
    def name(self) -> str:
        """Get the command name."""
        return "update"
    
    @property
    def description(self) -> str:
        """Get the command description."""
        return "Update a saved search"
    
    def configure_parser(self, parser: ArgumentParser) -> None:
        """Configure the parser for update command."""
        parser.add_argument("name", help="Name of the saved search to update")
        parser.add_argument("--query", help="New search query")
        parser.add_argument("--description", help="New description")
        parser.add_argument("--tags", help="New comma-separated list of tags")
        parser.add_argument("--category", help="New category")
    
    def execute(self, args: Namespace) -> Union[int, str]:
        """Execute the update search command."""
        try:
            # Parse tags
            tags = None
            if args.tags:
                tags = [tag.strip() for tag in args.tags.split(",")]
            
            # Check if at least one field is being updated
            if not any([args.query, args.description, args.tags, args.category]):
                print("Error: At least one field must be specified for update")
                print("Use --query, --description, --tags, or --category to update those fields")
                return 1
            
            # Update the search
            search = self._searches_manager.update_search(
                name=args.name,
                query=args.query,
                description=args.description,
                tags=tags,
                category=args.category
            )
            
            print(f"Search '{args.name}' updated successfully")
            return 0
        except Exception as e:
            logger.error(f"Failed to update search: {str(e)}", exc_info=True)
            print(f"Error: Failed to update search: {str(e)}")
            return 1


class DeleteSearchCommand(Command):
    """Command for deleting a saved search."""
    
    def __init__(self, core_manager: CoreManager):
        """Initialize with a core manager."""
        self._core_manager = core_manager
        self._searches_manager = SavedSearchesManager()
    
    @property
    def name(self) -> str:
        """Get the command name."""
        return "delete"
    
    @property
    def description(self) -> str:
        """Get the command description."""
        return "Delete a saved search"
    
    def configure_parser(self, parser: ArgumentParser) -> None:
        """Configure the parser for delete command."""
        parser.add_argument("name", help="Name of the saved search to delete")
    
    def execute(self, args: Namespace) -> Union[int, str]:
        """Execute the delete search command."""
        try:
            # Delete the search
            success = self._searches_manager.delete_search(args.name)
            
            if success:
                print(f"Search '{args.name}' deleted successfully")
                return 0
            else:
                print(f"No saved search found with name '{args.name}'")
                return 1
        except Exception as e:
            logger.error(f"Failed to delete search: {str(e)}", exc_info=True)
            print(f"Error: Failed to delete search: {str(e)}")
            return 1


class SavedSearchCommand(Command):
    """Command for managing saved searches."""
    
    def __init__(self, core_manager: CoreManager):
        """Initialize with a core manager."""
        self._core_manager = core_manager
        self._subcommands = {}
        
        # Add subcommands
        self.add_subcommand(SaveSearchCommand(core_manager))
        self.add_subcommand(ListSearchesCommand(core_manager))
        self.add_subcommand(LoadSearchCommand(core_manager))
        self.add_subcommand(UpdateSearchCommand(core_manager))
        self.add_subcommand(DeleteSearchCommand(core_manager))
    
    @property
    def name(self) -> str:
        """Get the command name."""
        return "saved-search"
    
    @property
    def description(self) -> str:
        """Get the command description."""
        return "Manage saved searches"
    
    def get_aliases(self) -> List[str]:
        """Get command aliases."""
        return ["search-save", "ss"]
    
    def add_subcommand(self, command: Command) -> None:
        """Add a subcommand."""
        self._subcommands[command.name] = command
    
    def configure_parser(self, parser: ArgumentParser) -> None:
        """Configure the argument parser for saved search commands."""
        subparsers = parser.add_subparsers(
            dest="subcommand",
            help="Saved search subcommands",
            required=True
        )
        
        for name, command in self._subcommands.items():
            subparser = subparsers.add_parser(name, help=command.description)
            command.configure_parser(subparser)
    
    def execute(self, args: Namespace) -> Union[int, str]:
        """Execute a saved search subcommand."""
        if not hasattr(args, 'subcommand') or not args.subcommand:
            print("Error: No subcommand specified")
            return 1
            
        command = self._subcommands.get(args.subcommand)
        if not command:
            print(f"Error: Unknown subcommand '{args.subcommand}'")
            return 1
            
        return command.execute(args) 