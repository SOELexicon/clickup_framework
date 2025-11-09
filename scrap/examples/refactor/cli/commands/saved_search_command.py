"""
SavedSearch Command

This module provides CLI commands for managing saved searches, including:
- Creating new saved searches
- Listing existing saved searches
- Executing saved searches
- Deleting saved searches
- Tracking search history

Saved searches allow users to store and reuse complex search queries
for more efficient task management.
"""

import argparse
import sys
import datetime
from typing import List, Optional, Any, Dict, TextIO

from refactor.cli.command import Command
from refactor.storage.saved_searches import SavedSearchesManager, SearchHistoryEntry
from refactor.core.interfaces.core_manager import CoreManager
from refactor.utils.formatting import (
    format_table, 
    colorize, 
    Color
)
from refactor.utils.json_utils import load_json_data
from refactor.utils.error_formatter import format_error_message


class SavedSearchCommand(Command):
    """
    Command for managing saved search queries.
    
    This command provides a set of subcommands for working with saved searches:
    - save: Store a new search query
    - list: List all saved search queries
    - get: Retrieve and execute a saved search
    - delete: Remove a saved search
    - export: Export saved searches to a JSON file
    - import: Import saved searches from a JSON file
    - history: Manage search history
    
    Saved searches are stored persistently and can be reused across sessions.
    """
    
    def __init__(self, core_manager: CoreManager):
        """
        Initialize the saved search command.
        
        Args:
            core_manager: The core manager for accessing application functionality
        """
        self.core_manager = core_manager
        # Create the saved searches manager for persistent storage
        self.saved_searches = SavedSearchesManager()
        
    @property
    def name(self) -> str:
        """
        Get the command name.
        
        Returns:
            The command name for CLI registration
        """
        return "saved-search"
    
    @property
    def description(self) -> str:
        """
        Get the command description.
        
        Returns:
            The command description for help text
        """
        return "Manage saved search queries"
    
    @property
    def category(self) -> str:
        """
        Get the command category.
        
        Returns:
            The category name for organizing commands
        """
        return "search"
    
    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        """
        Configure the argument parser for this command.
        
        This method sets up the subcommands (save, list, get, delete)
        and their respective arguments.
        
        Args:
            parser: The argument parser to configure
        """
        # Create subparsers for different saved search operations
        subparsers = parser.add_subparsers(dest="saved_search_command")
        
        # --- Save subcommand ---
        save_parser = subparsers.add_parser("save", help="Save a search query")
        save_parser.add_argument("name", help="Name for the saved search")
        save_parser.add_argument("query", help="Search query to save")
        save_parser.add_argument("-d", "--description", help="Description of the search")
        save_parser.add_argument("-t", "--tags", nargs="+", help="Tags for categorizing the search")
        save_parser.add_argument("-c", "--category", default="general", 
                               help="Category for organizing searches (default: general)")
        save_parser.add_argument("-f", "--favorite", action="store_true", 
                               help="Mark this search as a favorite")
        
        # --- Template subcommand ---
        template_parser = subparsers.add_parser("template", help="Create a search template with variables")
        template_parser.add_argument("name", help="Name for the search template")
        template_parser.add_argument("query", help="Search query template with variables (e.g., '${variable}')")
        template_parser.add_argument("-d", "--description", help="Description of the template")
        template_parser.add_argument("-t", "--tags", nargs="+", help="Tags for categorizing the template")
        template_parser.add_argument("-c", "--category", default="templates", 
                                   help="Category for organizing templates (default: templates)")
        template_parser.add_argument("-v", "--variables", nargs="+", 
                                   help="Optional explicit list of variable names (otherwise extracted from query)")
        template_parser.add_argument("-f", "--favorite", action="store_true", 
                                   help="Mark this template as a favorite")
        
        # --- Execute Template subcommand ---
        execute_template_parser = subparsers.add_parser("execute-template", 
                                                    help="Execute a search template with variable values")
        execute_template_parser.add_argument("name", help="Name of the search template")
        execute_template_parser.add_argument("-v", "--var", action="append", nargs=2, metavar=("NAME", "VALUE"),
                                          help="Variable name and value pairs (can be specified multiple times)")
        execute_template_parser.add_argument("-l", "--limit", type=int, help="Limit the number of results")
        execute_template_parser.add_argument("--track-history", action="store_true", default=True,
                                          help="Track this execution in search history (default: True)")
        
        # --- List Templates subcommand ---
        list_templates_parser = subparsers.add_parser("list-templates", help="List search templates")
        list_templates_parser.add_argument("-t", "--tag", help="Filter by tag")
        list_templates_parser.add_argument("-c", "--category", help="Filter by category")
        list_templates_parser.add_argument("-n", "--name-contains", help="Filter by name containing text")
        list_templates_parser.add_argument("-s", "--sort-by", choices=["name", "created_at", "last_used_at", "use_count"],
                                         default="name", help="Sort templates by field")
        
        # --- List subcommand ---
        list_parser = subparsers.add_parser("list", help="List saved search queries")
        list_parser.add_argument("-t", "--tag", help="Filter by tag")
        list_parser.add_argument("-c", "--category", help="Filter by category")
        list_parser.add_argument("-n", "--name-contains", help="Filter by name containing text")
        list_parser.add_argument("-s", "--sort-by", choices=["name", "created_at", "last_used_at", "use_count"],
                               default="name", help="Sort searches by field")
        
        # --- Favorites subcommand ---
        favorites_parser = subparsers.add_parser("favorites", help="Manage favorite searches")
        favorites_subparsers = favorites_parser.add_subparsers(dest="favorites_command")
        
        # --- Favorites list subcommand ---
        favorites_list_parser = favorites_subparsers.add_parser("list", help="List favorite searches")
        favorites_list_parser.add_argument("-t", "--tag", help="Filter by tag")
        favorites_list_parser.add_argument("-c", "--category", help="Filter by category")
        favorites_list_parser.add_argument("-n", "--name-contains", help="Filter by name containing text")
        favorites_list_parser.add_argument("-s", "--sort-by", choices=["name", "created_at", "last_used_at", "use_count"],
                                         default="name", help="Sort favorites by field")
        
        # --- Favorites add subcommand ---
        favorites_add_parser = favorites_subparsers.add_parser("add", help="Add a search to favorites")
        favorites_add_parser.add_argument("name", help="Name of the search to add to favorites")
        
        # --- Favorites remove subcommand ---
        favorites_remove_parser = favorites_subparsers.add_parser("remove", help="Remove a search from favorites")
        favorites_remove_parser.add_argument("name", help="Name of the search to remove from favorites")
        
        # --- Batch subcommand ---
        batch_parser = subparsers.add_parser("batch", help="Perform batch operations on multiple searches")
        batch_subparsers = batch_parser.add_subparsers(dest="batch_command")
        
        # --- Batch delete subcommand ---
        batch_delete_parser = batch_subparsers.add_parser("delete", help="Delete multiple searches")
        batch_delete_parser.add_argument("names", nargs="+", help="Names of searches to delete")
        batch_delete_parser.add_argument("--confirm", action="store_true", help="Skip confirmation prompt")
        
        # --- Batch categorize subcommand ---
        batch_categorize_parser = batch_subparsers.add_parser("categorize", help="Set category for multiple searches")
        batch_categorize_parser.add_argument("names", nargs="+", help="Names of searches to update")
        batch_categorize_parser.add_argument("category", help="Category to assign")
        
        # --- Batch tag subcommand ---
        batch_tag_parser = batch_subparsers.add_parser("tag", help="Add tags to multiple searches")
        batch_tag_parser.add_argument("names", nargs="+", help="Names of searches to update")
        batch_tag_parser.add_argument("tags", nargs="+", help="Tags to add")
        
        # --- Batch untag subcommand ---
        batch_untag_parser = batch_subparsers.add_parser("untag", help="Remove tags from multiple searches")
        batch_untag_parser.add_argument("names", nargs="+", help="Names of searches to update")
        batch_untag_parser.add_argument("tags", nargs="+", help="Tags to remove")
        
        # --- Batch favorite subcommand ---
        batch_favorite_parser = batch_subparsers.add_parser("favorite", help="Add multiple searches to favorites")
        batch_favorite_parser.add_argument("names", nargs="+", help="Names of searches to update")
        
        # --- Batch unfavorite subcommand ---
        batch_unfavorite_parser = batch_subparsers.add_parser("unfavorite", help="Remove multiple searches from favorites")
        batch_unfavorite_parser.add_argument("names", nargs="+", help="Names of searches to update")
        
        # --- Get subcommand ---
        get_parser = subparsers.add_parser("get", help="Get and execute a saved search query")
        get_parser.add_argument("name", help="Name of the saved search to retrieve")
        get_parser.add_argument("-e", "--execute", action="store_true", 
                              help="Execute the search query")
        get_parser.add_argument("-l", "--limit", type=int, help="Limit the number of results")
        get_parser.add_argument("--track-history", action="store_true", default=True,
                              help="Track this execution in search history (default: True)")
        
        # --- Delete subcommand ---
        delete_parser = subparsers.add_parser("delete", help="Delete a saved search query")
        delete_parser.add_argument("name", help="Name of the saved search to delete")
        
        # --- Export subcommand ---
        export_parser = subparsers.add_parser("export", help="Export saved searches to a JSON file")
        export_parser.add_argument("-o", "--output", help="Output file (defaults to stdout)")
        export_parser.add_argument("-c", "--category", help="Export only searches from this category")
        export_parser.add_argument("-t", "--tag", help="Export only searches with this tag")
        export_parser.add_argument("--include-templates", action="store_true", 
                                help="Include templates in export (default: include all)")
        export_parser.add_argument("--templates-only", action="store_true", 
                                help="Export only templates (default: include all)")
        export_parser.add_argument("--favorites-only", action="store_true", 
                                help="Export only favorite searches (default: include all)")
        
        # --- Import subcommand ---
        import_parser = subparsers.add_parser("import", help="Import saved searches from a JSON file")
        import_parser.add_argument("file", help="JSON file containing saved searches")
        import_parser.add_argument("-m", "--mode", choices=["skip", "replace", "rename"], default="skip",
                                help="How to handle conflicts: skip, replace existing searches, or rename imports")
        
        # --- History subcommand ---
        history_parser = subparsers.add_parser("history", help="Manage search history")
        history_subparsers = history_parser.add_subparsers(dest="history_command")
        
        # --- History list subcommand ---
        history_list_parser = history_subparsers.add_parser("list", help="List search history")
        history_list_parser.add_argument("-l", "--limit", type=int, default=10,
                                       help="Maximum number of history entries to show")
        history_list_parser.add_argument("-q", "--query-contains", 
                                       help="Filter history by search query content")
        
        # --- History clear subcommand ---
        history_clear_parser = history_subparsers.add_parser("clear", 
                                                          help="Clear search history")
        history_clear_parser.add_argument("--confirm", action="store_true", 
                                        help="Confirm clearing without prompting")
        
        # --- History delete subcommand ---
        history_delete_parser = history_subparsers.add_parser("delete", 
                                                           help="Delete a specific history entry")
        history_delete_parser.add_argument("timestamp", type=float, 
                                         help="Timestamp of the history entry to delete")
        
        # --- History run subcommand ---
        history_run_parser = history_subparsers.add_parser("run", 
                                                        help="Run a query from history")
        history_run_parser.add_argument("timestamp", type=float, 
                                      help="Timestamp of the history entry to run")
        history_run_parser.add_argument("-l", "--limit", type=int, 
                                      help="Limit the number of results")
        
        # --- History save subcommand ---
        history_save_parser = history_subparsers.add_parser("save", 
                                                         help="Save a query from history as a saved search")
        history_save_parser.add_argument("timestamp", type=float, 
                                       help="Timestamp of the history entry to save")
        history_save_parser.add_argument("name", help="Name for the new saved search")
        history_save_parser.add_argument("-d", "--description", help="Description of the search")
        history_save_parser.add_argument("-t", "--tags", nargs="+", help="Tags for categorizing the search")
        history_save_parser.add_argument("-c", "--category", default="general", 
                                       help="Category for the search")
        history_save_parser.add_argument("--as-template", action="store_true",
                                       help="Save as a template with variables")
        history_save_parser.add_argument("-f", "--favorite", action="store_true",
                                       help="Mark as a favorite search")
    
    def execute(self, args: argparse.Namespace) -> int:
        """
        Execute the command with the provided arguments.
        
        This method dispatches to the appropriate handler based on the 
        subcommand specified in the arguments.
        
        Args:
            args: The parsed command-line arguments
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        try:
            # Dispatch to the appropriate subcommand handler
            if args.saved_search_command == "save":
                return self._handle_save(args)
            elif args.saved_search_command == "template":
                return self._handle_template(args)
            elif args.saved_search_command == "execute-template":
                return self._handle_execute_template(args)
            elif args.saved_search_command == "list-templates":
                return self._handle_list_templates(args)
            elif args.saved_search_command == "list":
                return self._handle_list(args)
            elif args.saved_search_command == "get":
                return self._handle_get(args)
            elif args.saved_search_command == "delete":
                return self._handle_delete(args)
            elif args.saved_search_command == "export":
                return self._handle_export(args)
            elif args.saved_search_command == "import":
                return self._handle_import(args)
            elif args.saved_search_command == "history":
                return self._handle_history(args)
            elif args.saved_search_command == "favorites":
                return self._handle_favorites(args)
            elif args.saved_search_command == "batch":
                return self._handle_batch(args)
            else:
                print("Please specify a subcommand. Use --help for options.")
                return 1
        except Exception as e:
            # Format and print the error message
            print(format_error_message(str(e)), file=sys.stderr)
            return 1
    
    def _handle_save(self, args: argparse.Namespace) -> int:
        """
        Handle the 'save' subcommand.
        
        This method saves a new search query with the provided name and options.
        
        Args:
            args: The parsed command-line arguments
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        try:
            # Save the search query with the provided options
            self.saved_searches.save_search(
                name=args.name,
                query=args.query,
                description=args.description or "",
                tags=args.tags or [],
                category=args.category,
                is_favorite=args.favorite if hasattr(args, "favorite") else False
            )
            print(f"Saved search '{args.name}' successfully.")
            return 0
        except ValueError as e:
            # Handle case where a search with the same name already exists
            print(f"Error: {str(e)}")
            return 1
    
    def _handle_list(self, args: argparse.Namespace) -> int:
        """
        Handle the 'list' subcommand.
        
        This method lists all saved searches, optionally filtered by the 
        provided criteria and sorted by the specified field.
        
        Args:
            args: The parsed command-line arguments
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        # Get saved searches with filters
        searches = self.saved_searches.list_searches(
            tag=args.tag,
            category=args.category,
            name_contains=args.name_contains,
            sort_by=args.sort_by
        )
        
        if not searches:
            print("No saved searches found matching the criteria.")
            return 0
        
        # Format the searches as a table
        headers = ["Name", "Category", "Query", "Description", "Tags", "Usage"]
        rows = []
        
        for search in searches:
            # Format the search data for display
            tags_str = ", ".join(search.tags) if search.tags else ""
            usage_str = f"{search.use_count} times"
            if search.last_used_at:
                import datetime
                last_used = datetime.datetime.fromtimestamp(search.last_used_at)
                usage_str += f", last: {last_used.strftime('%Y-%m-%d')}"
            
            rows.append([
                search.name,
                search.category,
                search.query,
                search.description,
                tags_str,
                usage_str
            ])
        
        # Print the table
        print(format_table(headers, rows))
        print(f"\nTotal: {len(searches)} saved searches")
        return 0
    
    def _handle_get(self, args: argparse.Namespace) -> int:
        """
        Handle the 'get' subcommand.
        
        This method retrieves a saved search by name and optionally executes it.
        
        Args:
            args: The parsed command-line arguments
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        try:
            # Retrieve the saved search
            search = self.saved_searches.get_search(args.name)
            
            # Print the search details
            print(f"Name: {colorize(search.name, Color.CYAN)}")
            print(f"Category: {search.category}")
            print(f"Query: {colorize(search.query, Color.GREEN)}")
            if search.description:
                print(f"Description: {search.description}")
            if search.tags:
                print(f"Tags: {', '.join(search.tags)}")
            
            # Execute the search if requested
            if args.execute:
                print("\nExecuting search query...\n")
                
                # TODO: Implement actual search execution using core_manager
                # For now, just simulate execution
                result_count = 0  # This would be the actual result count
                
                # Add to history if tracking is enabled
                if args.track_history:
                    self.saved_searches.add_to_history(
                        query=search.query,
                        saved_search_name=search.name,
                        result_count=result_count
                    )
                
                # Print the query that would be executed
                print(f"Search query: {search.query}")
                if args.limit:
                    print(f"Limited to {args.limit} results")
            
            return 0
        except KeyError as e:
            # Handle case where the search doesn't exist
            print(f"Error: {str(e)}")
            return 1
    
    def _handle_delete(self, args: argparse.Namespace) -> int:
        """
        Handle the 'delete' subcommand.
        
        This method deletes a saved search by name.
        
        Args:
            args: The parsed command-line arguments
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        # Delete the saved search
        success = self.saved_searches.delete_search(args.name)
        
        if success:
            print(f"Deleted saved search '{args.name}' successfully.")
            return 0
        else:
            print(f"Error: No saved search found with name '{args.name}'.")
            return 1
    
    def _handle_export(self, args: argparse.Namespace) -> int:
        """
        Handle the 'export' subcommand.
        
        This method exports saved searches to a JSON file or stdout.
        
        Args:
            args: The parsed command-line arguments
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        import json
        
        # Get searches with filters
        searches = self.saved_searches.list_searches(
            tag=args.tag,
            category=args.category
        )
        
        # Filter based on template options
        if args.templates_only:
            searches = [s for s in searches if s.is_template]
        elif not args.include_templates:
            searches = [s for s in searches if not s.is_template]
        
        # Filter for favorites if specified
        if args.favorites_only:
            searches = [s for s in searches if s.is_favorite]
        
        if not searches:
            print("No saved searches found matching the criteria.")
            return 0
        
        # Convert searches to dictionaries
        export_data = {
            "version": "1.0",
            "searches": [search.to_dict() for search in searches]
        }
        
        # Determine where to output the data
        output_file = None
        try:
            if args.output:
                # Write to the specified file
                with open(args.output, 'w') as f:
                    json.dump(export_data, f, indent=2)
                print(f"Exported {len(searches)} saved searches to {args.output}")
            else:
                # Write to stdout
                print(json.dumps(export_data, indent=2))
            
            return 0
        except Exception as e:
            print(f"Error exporting saved searches: {str(e)}")
            return 1
        finally:
            if output_file and not output_file.closed:
                output_file.close()
    
    def _handle_import(self, args: argparse.Namespace) -> int:
        """
        Handle the 'import' subcommand.
        
        This method imports saved searches from a JSON file.
        
        Args:
            args: The parsed command-line arguments
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        try:
            # Load the JSON data from the file
            import_data = load_json_data(args.file)
            
            # Verify the data structure
            if not isinstance(import_data, dict) or "searches" not in import_data:
                print("Error: Invalid saved searches file format.")
                return 1
            
            # Import each search
            imported = 0
            skipped = 0
            replaced = 0
            
            for search_data in import_data["searches"]:
                try:
                    name = search_data["name"]
                    # Check if a search with this name already exists
                    if name in self.saved_searches.searches:
                        if args.mode == "skip":
                            print(f"Skipping: '{name}' already exists")
                            skipped += 1
                            continue
                        elif args.mode == "replace":
                            self.saved_searches.delete_search(name)
                            replaced += 1
                        elif args.mode == "rename":
                            # Find a unique name by appending a suffix
                            suffix = 1
                            new_name = f"{name}_{suffix}"
                            while new_name in self.saved_searches.searches:
                                suffix += 1
                                new_name = f"{name}_{suffix}"
                            search_data["name"] = new_name
                            name = new_name
                    
                    # Create the search
                    self.saved_searches.save_search(
                        name=name,
                        query=search_data["query"],
                        description=search_data.get("description", ""),
                        tags=search_data.get("tags", []),
                        category=search_data.get("category", "general")
                    )
                    imported += 1
                except Exception as e:
                    print(f"Error importing search '{search_data.get('name', 'unknown')}': {str(e)}")
            
            # Print a summary
            print(f"Imported {imported} saved searches")
            if skipped > 0:
                print(f"Skipped {skipped} existing searches")
            if replaced > 0:
                print(f"Replaced {replaced} existing searches")
            
            return 0
        except Exception as e:
            print(f"Error importing saved searches: {str(e)}")
            return 1
    
    def _handle_history(self, args: argparse.Namespace) -> int:
        """
        Handle the 'history' subcommand.
        
        This method dispatches to the appropriate history subcommand handler.
        
        Args:
            args: The parsed command-line arguments
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        if not hasattr(args, "history_command") or not args.history_command:
            print("Please specify a history subcommand. Use --help for options.")
            return 1
        
        # Dispatch to the appropriate history subcommand handler
        if args.history_command == "list":
            return self._handle_history_list(args)
        elif args.history_command == "clear":
            return self._handle_history_clear(args)
        elif args.history_command == "delete":
            return self._handle_history_delete(args)
        elif args.history_command == "run":
            return self._handle_history_run(args)
        elif args.history_command == "save":
            return self._handle_history_save(args)
        else:
            print(f"Unknown history subcommand: {args.history_command}")
            return 1
    
    def _handle_history_list(self, args: argparse.Namespace) -> int:
        """
        Handle the 'history list' subcommand.
        
        This method lists search history entries, optionally filtered and limited.
        
        Args:
            args: The parsed command-line arguments
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        try:
            # Get history entries with optional filtering and limit
            entries = self.saved_searches.get_history(
                limit=args.limit,
                query_contains=args.query_contains
            )
            
            if not entries:
                print("No search history entries found matching the criteria.")
                return 0
            
            # Format the entries as a table
            headers = ["Timestamp", "Search Query", "From Saved", "Results"]
            rows = []
            
            for entry in entries:
                # Handle both object and dictionary style entries
                if isinstance(entry, dict):
                    # Dictionary style entry (from mock)
                    executed_at = entry["executed_at"]
                    query = entry["query"]
                    saved_search_name = entry.get("saved_search_name", "")
                    result_count = entry.get("result_count", 0)
                else:
                    # Object style entry (from real class)
                    executed_at = entry.executed_at
                    query = entry.query
                    saved_search_name = entry.saved_search_name or ""
                    result_count = entry.result_count
                
                # Format the timestamp for display
                timestamp_str = datetime.datetime.fromtimestamp(
                    executed_at
                ).strftime("%Y-%m-%d %H:%M:%S")
                
                # Format the query (truncate if too long)
                if len(query) > 60:
                    query = query[:57] + "..."
                
                # Create the row
                rows.append([
                    f"{executed_at:.6f}",  # Precise timestamp for reference
                    query,
                    saved_search_name,
                    str(result_count)
                ])
            
            # Print the table
            print(format_table(headers, rows))
            print(f"\nTotal: {len(entries)} history entries")
            print("Note: Use the timestamp value with other history commands.")
            return 0
        except Exception as e:
            print(format_error_message(str(e)))
            return 1
    
    def _handle_history_clear(self, args: argparse.Namespace) -> int:
        """
        Handle the 'history clear' subcommand.
        
        This method clears all search history entries after confirmation.
        
        Args:
            args: The parsed command-line arguments
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        # If confirmation is required, prompt the user
        if not args.confirm:
            response = input("Are you sure you want to clear all search history? (y/N): ")
            if response.lower() not in ["y", "yes"]:
                print("Operation cancelled.")
                return 0
        
        # Clear the history
        count = self.saved_searches.clear_history()
        print(f"Cleared {count} search history entries.")
        return 0
    
    def _handle_history_delete(self, args: argparse.Namespace) -> int:
        """
        Handle the 'history delete' subcommand.
        
        This method deletes a specific search history entry by timestamp.
        
        Args:
            args: The parsed command-line arguments
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        # Delete the specific history entry
        success = self.saved_searches.delete_history_entry(args.timestamp)
        
        if success:
            print(f"Deleted history entry with timestamp {args.timestamp}.")
            return 0
        else:
            print(f"Error: No history entry found with timestamp {args.timestamp}.")
            return 1
    
    def _handle_history_run(self, args: argparse.Namespace) -> int:
        """
        Handle the 'history run' subcommand.
        
        This method runs a search query from history.
        
        Args:
            args: The parsed command-line arguments
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        try:
            # Find the history entry with the given timestamp
            entries = self.saved_searches.get_history()
            entry = None
            
            # Handle both object and dictionary style entries
            for e in entries:
                # Get the executed_at value based on entry type
                if isinstance(e, dict):
                    executed_at = e["executed_at"]
                else:
                    executed_at = e.executed_at
                    
                # Check if this is the entry we're looking for
                if abs(executed_at - args.timestamp) < 0.001:
                    entry = e
                    break
            
            if not entry:
                print(format_error_message(f"No history entry found with timestamp {args.timestamp}."))
                return 1
            
            # Get values based on entry type
            if isinstance(entry, dict):
                # Dictionary style entry (from mock)
                query = entry["query"]
                saved_search_name = entry.get("saved_search_name")
                executed_at = entry["executed_at"]
            else:
                # Object style entry (from real class)
                query = entry.query
                saved_search_name = entry.saved_search_name
                executed_at = entry.executed_at
            
            # Print the search details
            print(f"Re-running search query from history:")
            print(f"Timestamp: {datetime.datetime.fromtimestamp(executed_at).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Query: {colorize(query, Color.GREEN)}")
            if saved_search_name:
                print(f"From saved search: {saved_search_name}")
            
            # Execute the search
            print("\nExecuting search query...\n")
            
            # Execute the search
            return self.execute_search(query, limit=args.limit)
            
        except Exception as e:
            print(format_error_message(str(e)))
            return 1
    
    def _handle_history_save(self, args: argparse.Namespace) -> int:
        """
        Handle the 'history save' subcommand.
        
        This method creates a new saved search from a history entry.
        
        Args:
            args: The parsed command-line arguments
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        try:
            # Find the history entry with the given timestamp
            entries = self.saved_searches.get_history()
            entry = None
            
            # Handle both object and dictionary style entries
            for e in entries:
                # Get the executed_at value based on entry type
                if isinstance(e, dict):
                    executed_at = e["executed_at"]
                else:
                    executed_at = e.executed_at
                    
                # Check if this is the entry we're looking for
                if abs(executed_at - args.timestamp) < 0.001:
                    entry = e
                    break
            
            if not entry:
                print(format_error_message(f"No history entry found with timestamp {args.timestamp}."))
                return 1
            
            # Get the query from the entry based on type
            if isinstance(entry, dict):
                query = entry["query"]
            else:
                query = entry.query
            
            # Create a template from the history entry
            success = self._create_template_from_history(
                query=query,
                name=args.name,
                description=args.description or "",
                tags=args.tags or [],
                category=args.category,
                is_template=getattr(args, "as_template", False),
                is_favorite=args.favorite if hasattr(args, "favorite") else False
            )
            
            if success:
                print(f"Saved search '{args.name}' successfully from history entry.")
                return 0
            else:
                print(format_error_message(f"Failed to save search '{args.name}' from history."))
                return 1
                
        except ValueError as e:
            # Handle case where a search with the same name already exists
            print(format_error_message(str(e)))
            return 1
        except Exception as e:
            print(format_error_message(str(e)))
            return 1
            
    def _create_template_from_history(self, query, name, description, tags, category, is_template, is_favorite):
        """
        Create a template or saved search from a history entry.
        
        Args:
            query: The search query
            name: Name for the saved search
            description: Description of the search
            tags: Tags for categorizing the search
            category: Category for organizing searches
            is_template: Whether this is a template with variables
            is_favorite: Whether this is a favorite search
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if is_template:
                # Ask the user to identify variables in the query
                print("Creating a template from the search query.")
                print(f"Original query: {query}")
                print("\nTo create a template, you need to identify variables in the query.")
                print("Variables should be in the format ${variable_name}.")
                print("Example: status == '${status}' and priority >= ${min_priority}\n")
                
                template_query = input("Enter the template query with variables: ")
                variables = []
                
                # Create a new saved search template from the history entry
                self.saved_searches.save_search(
                    name=name,
                    query=template_query,
                    description=description,
                    tags=tags,
                    category=category,
                    is_template=True,
                    variables=variables,  # This will be extracted from the query
                    is_favorite=is_favorite
                )
                
                return True
            else:
                # Create a new regular saved search from the history entry
                self.saved_searches.save_search(
                    name=name,
                    query=query,
                    description=description,
                    tags=tags,
                    category=category,
                    is_favorite=is_favorite
                )
                return True
        except Exception:
            return False
            
    def execute_search(self, query, limit=None, file_path=None):
        """
        Execute a search query.
        
        Args:
            query: The search query to execute
            limit: Maximum number of results to return
            file_path: Optional file path to search in
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        try:
            # In a real implementation, this would use the core_manager to perform the search
            print(f"Executing search: {query}")
            if limit:
                print(f"Limited to {limit} results")
            
            # Add to history
            self.saved_searches.add_to_history(
                query=query,
                result_count=0  # Placeholder for actual result count
            )
            
            return 0
        except Exception as e:
            print(format_error_message(str(e)))
            return 1
    
    def _handle_template(self, args: argparse.Namespace) -> int:
        """
        Handle the 'template' subcommand.
        
        This method creates a new search template with variables.
        
        Args:
            args: The parsed command-line arguments
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        try:
            # Create the search template
            template = self.saved_searches.save_search(
                name=args.name,
                query=args.query,
                description=args.description or "",
                tags=args.tags or [],
                category=args.category,
                is_template=True,
                variables=args.variables,
                is_favorite=args.favorite if hasattr(args, "favorite") else False
            )
            
            # Print success message with variable information
            print(f"Created search template '{args.name}' successfully.")
            
            # Show the variables detected in the template
            if template.variables:
                print(f"Variables: {', '.join(template.variables)}")
                print("Use these variables when executing the template with 'execute-template' command.")
            else:
                print("No variables detected in the template.")
            
            return 0
        except ValueError as e:
            # Handle case where a template with the same name already exists
            print(f"Error: {str(e)}")
            return 1
    
    def _handle_execute_template(self, args: argparse.Namespace) -> int:
        """
        Handle the 'execute-template' subcommand.
        
        This method executes a search template with the provided variable values.
        
        Args:
            args: The parsed command-line arguments
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        try:
            # Get the search template
            template = self.saved_searches.get_search(args.name)
            
            # Check if it's a template
            if not template.is_template:
                print(f"Error: '{args.name}' is not a search template.")
                return 1
            
            # Parse variables from the arguments
            variables = {}
            if args.var:
                for name, value in args.var:
                    variables[name] = value
            
            # List missing variables
            missing_vars = []
            for var_name in template.variables:
                if var_name not in variables:
                    missing_vars.append(var_name)
            
            if missing_vars:
                print(f"Error: Missing values for template variables: {', '.join(missing_vars)}")
                print(f"Required variables: {', '.join(template.variables)}")
                return 1
            
            # Execute the template with variables
            query, used_vars = self.saved_searches.execute_search_template(args.name, variables)
            
            # Print the template details
            print(f"Template: {colorize(template.name, Color.CYAN)}")
            print(f"Variables: {', '.join([f'{k}={v}' for k, v in used_vars.items()])}")
            print(f"Resulting query: {colorize(query, Color.GREEN)}")
            
            # Execute the search
            print("\nExecuting search query...\n")
            
            # TODO: Implement actual search execution using core_manager
            # For now, just simulate execution
            result_count = 0  # This would be the actual result count
            
            # Add to history if tracking is enabled
            if args.track_history:
                self.saved_searches.add_to_history(
                    query=query,
                    saved_search_name=template.name,
                    result_count=result_count,
                    template_variables=used_vars
                )
            
            # Print the query that would be executed
            print(f"Search query: {query}")
            if args.limit:
                print(f"Limited to {args.limit} results")
            
            return 0
        except (KeyError, ValueError) as e:
            # Handle case where the template doesn't exist or variables are missing
            print(f"Error: {str(e)}")
            return 1
    
    def _handle_list_templates(self, args: argparse.Namespace) -> int:
        """
        Handle the 'list-templates' subcommand.
        
        This method lists all search templates, optionally filtered by the 
        provided criteria and sorted by the specified field.
        
        Args:
            args: The parsed command-line arguments
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        # Get templates with filters
        templates = self.saved_searches.list_templates(
            tag=args.tag,
            category=args.category,
            name_contains=args.name_contains,
            sort_by=args.sort_by
        )
        
        if not templates:
            print("No search templates found matching the criteria.")
            return 0
        
        # Format the templates as a table
        headers = ["Name", "Category", "Query", "Variables", "Description", "Tags", "Usage"]
        rows = []
        
        for template in templates:
            # Format the template data for display
            tags_str = ", ".join(template.tags) if template.tags else ""
            variables_str = ", ".join(template.variables) if template.variables else ""
            usage_str = f"{template.use_count} times"
            if template.last_used_at:
                import datetime
                last_used = datetime.datetime.fromtimestamp(template.last_used_at)
                usage_str += f", last: {last_used.strftime('%Y-%m-%d')}"
            
            rows.append([
                template.name,
                template.category,
                template.query,
                variables_str,
                template.description,
                tags_str,
                usage_str
            ])
        
        # Print the table
        print(format_table(headers, rows))
        print(f"\nTotal: {len(templates)} search templates")
        return 0
    
    def _handle_favorites(self, args: argparse.Namespace) -> int:
        """
        Handle the 'favorites' subcommand.
        
        This method dispatches to the appropriate favorites subcommand handler.
        
        Args:
            args: The parsed command-line arguments
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        if not hasattr(args, "favorites_command") or not args.favorites_command:
            print("Please specify a favorites subcommand. Use --help for options.")
            return 1
        
        # Dispatch to the appropriate favorites subcommand handler
        if args.favorites_command == "list":
            return self._handle_favorites_list(args)
        elif args.favorites_command == "add":
            return self._handle_favorites_add(args)
        elif args.favorites_command == "remove":
            return self._handle_favorites_remove(args)
        else:
            print(f"Unknown favorites subcommand: {args.favorites_command}")
            return 1
    
    def _handle_favorites_list(self, args: argparse.Namespace) -> int:
        """
        Handle the 'favorites list' subcommand.
        
        This method lists favorite searches, optionally filtered by the 
        provided criteria and sorted by the specified field.
        
        Args:
            args: The parsed command-line arguments
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        # Get favorite searches with filters
        searches = self.saved_searches.list_favorites(
            tag=args.tag,
            category=args.category,
            name_contains=args.name_contains,
            sort_by=args.sort_by
        )
        
        if not searches:
            print("No favorite searches found matching the criteria.")
            return 0
        
        # Format the searches as a table
        headers = ["Name", "Category", "Query", "Description", "Tags", "Usage"]
        rows = []
        
        for search in searches:
            # Format the search data for display
            tags_str = ", ".join(search.tags) if search.tags else ""
            usage_str = f"{search.use_count} times"
            if search.last_used_at:
                import datetime
                last_used = datetime.datetime.fromtimestamp(search.last_used_at)
                usage_str += f", last: {last_used.strftime('%Y-%m-%d')}"
            
            rows.append([
                search.name,
                search.category,
                search.query,
                search.description,
                tags_str,
                usage_str
            ])
        
        # Print the table
        print(format_table(headers, rows))
        print(f"\nTotal: {len(searches)} favorite searches")
        return 0
    
    def _handle_favorites_add(self, args: argparse.Namespace) -> int:
        """
        Handle the 'favorites add' subcommand.
        
        This method adds a search to favorites.
        
        Args:
            args: The parsed command-line arguments
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        # Add the search to favorites
        success = self.saved_searches.add_to_favorites(args.name)
        
        if success:
            print(f"Added search '{args.name}' to favorites successfully.")
            return 0
        else:
            print(f"Error: No search found with name '{args.name}'.")
            return 1
    
    def _handle_favorites_remove(self, args: argparse.Namespace) -> int:
        """
        Handle the 'favorites remove' subcommand.
        
        This method removes a search from favorites.
        
        Args:
            args: The parsed command-line arguments
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        # Remove the search from favorites
        success = self.saved_searches.remove_from_favorites(args.name)
        
        if success:
            print(f"Removed search '{args.name}' from favorites successfully.")
            return 0
        else:
            print(f"Error: No search found with name '{args.name}'.")
            return 1
    
    def _handle_batch(self, args: argparse.Namespace) -> int:
        """
        Handle the 'batch' subcommand.
        
        This method dispatches to the appropriate batch subcommand handler.
        
        Args:
            args: The parsed command-line arguments
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        if not hasattr(args, "batch_command") or not args.batch_command:
            print("Please specify a batch subcommand. Use --help for options.")
            return 1
        
        # Dispatch to the appropriate batch subcommand handler
        if args.batch_command == "delete":
            return self._handle_batch_delete(args)
        elif args.batch_command == "categorize":
            return self._handle_batch_categorize(args)
        elif args.batch_command == "tag":
            return self._handle_batch_tag(args)
        elif args.batch_command == "untag":
            return self._handle_batch_untag(args)
        elif args.batch_command == "favorite":
            return self._handle_batch_favorite(args)
        elif args.batch_command == "unfavorite":
            return self._handle_batch_unfavorite(args)
        else:
            print(f"Unknown batch subcommand: {args.batch_command}")
            return 1
    
    def _handle_batch_delete(self, args: argparse.Namespace) -> int:
        """
        Handle the 'batch delete' subcommand.
        
        This method deletes multiple searches.
        
        Args:
            args: The parsed command-line arguments
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        # Delete the specified searches
        success = self.saved_searches.delete_searches(args.names)
        
        if success:
            print(f"Deleted {len(args.names)} searches successfully.")
            return 0
        else:
            print(f"Error: Failed to delete some searches.")
            return 1
    
    def _handle_batch_categorize(self, args: argparse.Namespace) -> int:
        """
        Handle the 'batch categorize' subcommand.
        
        This method sets a category for multiple searches.
        
        Args:
            args: The parsed command-line arguments
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        # Set the category for the specified searches
        success = self.saved_searches.categorize_searches(args.names, args.category)
        
        if success:
            print(f"Set category for {len(args.names)} searches successfully.")
            return 0
        else:
            print(f"Error: Failed to set category for some searches.")
            return 1
    
    def _handle_batch_tag(self, args: argparse.Namespace) -> int:
        """
        Handle the 'batch tag' subcommand.
        
        This method adds tags to multiple searches.
        
        Args:
            args: The parsed command-line arguments
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        # Add tags to the specified searches
        success = self.saved_searches.tag_searches(args.names, args.tags)
        
        if success:
            print(f"Added {len(args.tags)} tags to {len(args.names)} searches successfully.")
            return 0
        else:
            print(f"Error: Failed to add tags to some searches.")
            return 1
    
    def _handle_batch_untag(self, args: argparse.Namespace) -> int:
        """
        Handle the 'batch untag' subcommand.
        
        This method removes tags from multiple searches.
        
        Args:
            args: The parsed command-line arguments
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        # Remove tags from the specified searches
        success = self.saved_searches.untag_searches(args.names, args.tags)
        
        if success:
            print(f"Removed {len(args.tags)} tags from {len(args.names)} searches successfully.")
            return 0
        else:
            print(f"Error: Failed to remove tags from some searches.")
            return 1
    
    def _handle_batch_favorite(self, args: argparse.Namespace) -> int:
        """
        Handle the 'batch favorite' subcommand.
        
        This method adds multiple searches to favorites.
        
        Args:
            args: The parsed command-line arguments
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        # Add the specified searches to favorites
        success = self.saved_searches.add_to_favorites(args.names)
        
        if success:
            print(f"Added {len(args.names)} searches to favorites successfully.")
            return 0
        else:
            print(f"Error: Failed to add some searches to favorites.")
            return 1
    
    def _handle_batch_unfavorite(self, args: argparse.Namespace) -> int:
        """
        Handle the 'batch unfavorite' subcommand.
        
        This method removes multiple searches from favorites.
        
        Args:
            args: The parsed command-line arguments
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        # Remove the specified searches from favorites
        success = self.saved_searches.remove_from_favorites(args.names)
        
        if success:
            print(f"Removed {len(args.names)} searches from favorites successfully.")
            return 0
        else:
            print(f"Error: Failed to remove some searches from favorites.")
            return 1 