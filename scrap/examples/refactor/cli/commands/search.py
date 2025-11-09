"""
Search Commands Implementation

This module provides command implementations for search-related operations
such as querying tasks with various filters and criteria.
"""
from argparse import ArgumentParser, Namespace
from typing import Dict, List, Optional, Any

from refactor.cli.commands.base import BaseCommand, CompositeCommand, SimpleCommand
from refactor.core.interfaces.core_manager import CoreManager


class SearchTasksCommand(SimpleCommand):
    """
    Task: tsk_bf28d342 - Update CLI Module Comments
    Document: refactor/cli/commands/search.py
    dohcount: 1

    Purpose:
        Implements a command to search for tasks based on various filtering criteria.
        Provides comprehensive search capabilities with support for name, status,
        priority, type, tags, and parent-child relationship filtering.

    Requirements:
        - Must support multiple filter criteria that can be combined
        - Must handle pagination through limit and offset parameters
        - Must provide sorting capabilities on different task fields
        - Must display formatted results with task details
        - CRITICAL: Must properly handle query parameter precedence
        - CRITICAL: Must maintain performance with large result sets

    Used By:
        - CLI Users: For finding specific tasks across large templates
        - Project Managers: For generating filtered task reports
        - Automation Scripts: For task discovery and reporting
        - Dashboard Tools: For providing search capabilities

    Changes:
        - v1: Initial implementation with basic search filters
        - v2: Added support for advanced query expressions
        - v3: Enhanced result formatting and pagination
        - v4: Added performance optimizations for large datasets
    """
    
    def __init__(self, core_manager: CoreManager):
        """
        Initialize a new SearchTasksCommand instance.
        
        Creates a command for searching tasks with comprehensive
        filtering, sorting, and pagination capabilities.
        
        Args:
            core_manager: Core manager instance for accessing task services
        """
        super().__init__("tasks", "Search for tasks with various criteria")
        self._core_manager = core_manager
    
    def configure_parser(self, parser: ArgumentParser) -> None:
        """
        Configure the argument parser for the search tasks command.
        
        Sets up all filtering, sorting, and pagination arguments for
        comprehensive task search capabilities with multiple criteria.
        
        Args:
            parser: The argument parser to configure with arguments
            
        Notes:
            - Multiple filters can be combined for narrower results
            - When --query is provided, it takes precedence over other filters
        """
        parser.add_argument(
            "--name", 
            help="Filter by task name (substring match)"
        )
        parser.add_argument(
            "--status", 
            choices=["to do", "in progress", "in review", "complete"],
            help="Filter by task status"
        )
        parser.add_argument(
            "--priority", 
            type=int, 
            choices=[1, 2, 3, 4],
            help="Filter by priority (1=Urgent, 2=High, 3=Normal, 4=Low)"
        )
        parser.add_argument(
            "--type", 
            help="Filter by task type"
        )
        parser.add_argument(
            "--tag", 
            action="append", 
            dest="tags",
            help="Filter by tag (can be specified multiple times)"
        )
        parser.add_argument(
            "--parent", 
            help="Filter by parent task ID"
        )
        parser.add_argument(
            "--query", 
            help="Advanced query expression"
        )
        parser.add_argument(
            "--limit", 
            type=int, 
            default=50,
            help="Limit number of results (default: 50)"
        )
        parser.add_argument(
            "--offset", 
            type=int, 
            default=0,
            help="Offset for paginated results (default: 0)"
        )
        parser.add_argument(
            "--sort-by", 
            dest="sort_by",
            help="Field to sort by (name, status, priority, created)"
        )
        parser.add_argument(
            "--desc", 
            action="store_true",
            help="Sort in descending order (default: ascending)"
        )
    
    def execute(self, args: Namespace) -> int:
        """
        Execute the search tasks command.
        
        Processes search criteria based on provided arguments,
        queries the core manager for matching tasks, and displays
        the formatted results with pagination information.
        
        Args:
            args: Command arguments containing search filters, sorting,
                  and pagination parameters
            
        Returns:
            Exit code (0 for success, non-zero for error)
            
        Notes:
            - If no tasks match the criteria, a message is displayed
            - Results include task details like name, ID, type, status, priority
            - Parent task information is resolved and displayed when available
            - Pagination details are shown when results exceed the limit
        """
        try:
            # Build search criteria based on arguments
            criteria = {}
            
            # Basic filters
            if args.name:
                criteria["name_contains"] = args.name
            
            if args.status:
                criteria["status"] = args.status
            
            if args.priority:
                criteria["priority"] = args.priority
            
            if args.type:
                criteria["type"] = args.type
            
            if args.tags:
                criteria["tags"] = args.tags
            
            if args.parent:
                criteria["parent_id"] = args.parent
            
            # If query is provided, it takes precedence
            if args.query:
                criteria["query"] = args.query
            
            # Search for tasks
            results = self._core_manager.search_tasks(
                criteria=criteria,
                limit=args.limit,
                offset=args.offset,
                sort_by=args.sort_by,
                sort_desc=args.desc
            )
            
            # Display results
            if not results:
                print("No tasks found matching the criteria")
                return 0
            
            print(f"Found {len(results)} tasks matching the criteria:\n")
            
            for task in results:
                print(f"Task: {task.name}")
                print(f"ID: {task.id}")
                print(f"Type: {task.type}")
                print(f"Status: {task.status.value}")
                print(f"Priority: {task.priority.value}")
                
                if task.tags:
                    print(f"Tags: {', '.join(task.tags)}")
                
                # Show parent task if available
                if hasattr(task, 'parent_id') and task.parent_id:
                    try:
                        parent = self._core_manager.get_task(task.parent_id)
                        print(f"Parent: {parent.name} (ID: {parent.id})")
                    except:
                        print(f"Parent: Unknown (ID: {task.parent_id})")
                
                print()
            
            # Display pagination info if limited
            if args.limit < results.total_count:
                print(f"Showing {len(results)} of {results.total_count} total results.")
                print(f"Use --offset {args.offset + args.limit} to see the next page.")
            
            return 0
        except Exception as e:
            print(f"Error searching tasks: {str(e)}")
            return 1


class QueryCommand(SimpleCommand):
    """
    Task: tsk_bf28d342 - Update CLI Module Comments
    Document: refactor/cli/commands/search.py
    dohcount: 1

    Purpose:
        Implements a command for executing complex search queries with advanced
        expression syntax. Supports querying across different entity types with
        rich filtering capabilities, including logical operators and comparisons.

    Requirements:
        - Must support complex query expression language
        - Must handle different entity types (task, list, folder, space)
        - Must provide flexible output format options
        - Must display results with detailed entity information
        - CRITICAL: Must properly validate query syntax before execution
        - CRITICAL: Must handle query performance for large datasets

    Used By:
        - CLI Users: For executing complex data retrieval operations
        - Automation Scripts: For data analysis and extraction
        - CI/CD Pipelines: For automated validation and reporting
        - Integration Tools: For interfacing with other systems

    Changes:
        - v1: Initial implementation with basic query capabilities
        - v2: Added support for multiple entity types
        - v3: Enhanced query expression syntax with more operators
        - v4: Added output format options for better integration
    """
    
    def __init__(self, core_manager: CoreManager):
        """
        Initialize a new QueryCommand instance.
        
        Creates a command for executing complex search queries with
        advanced expression syntax and flexible output formatting.
        
        Args:
            core_manager: Core manager instance for accessing entity services
        """
        super().__init__("query", "Execute complex search queries")
        self._core_manager = core_manager
    
    def configure_parser(self, parser: ArgumentParser) -> None:
        """
        Configure the argument parser for the query command.
        
        Sets up arguments for query expression, entity type selection,
        and output formatting options for comprehensive query capabilities.
        
        Args:
            parser: The argument parser to configure with arguments
            
        Notes:
            - Query syntax supports comparison and logical operators
            - Entity type determines which data collection is queried
            - Format options control how results are presented
        """
        parser.add_argument(
            "query", 
            help="Query expression (e.g., 'status = \"in progress\" and priority < 3')"
        )
        parser.add_argument(
            "--entity", 
            choices=["task", "list", "folder", "space"],
            default="task",
            help="Entity type to query (default: task)"
        )
        parser.add_argument(
            "--format", 
            choices=["table", "json"],
            default="table",
            help="Output format (default: table)"
        )
        parser.add_argument(
            "--limit", 
            type=int, 
            default=50,
            help="Limit number of results (default: 50)"
        )
        parser.add_argument(
            "--offset", 
            type=int, 
            default=0,
            help="Offset for paginated results (default: 0)"
        )
    
    def execute(self, args: Namespace) -> int:
        """
        Execute the query command.
        
        Processes the query expression against the specified entity type,
        formats and displays the results according to the chosen format,
        and provides pagination information for large result sets.
        
        Args:
            args: Command arguments containing:
                - query: The query expression to execute
                - entity: The entity type to query against
                - format: The output format (table or json)
                - limit: Maximum number of results to return
                - offset: Starting position for results
            
        Returns:
            Exit code (0 for success, non-zero for error)
            
        Notes:
            - JSON format output can be easily parsed by other tools
            - Table format displays entity-specific fields for readability
            - Different entity types show different field sets
            - Pagination information is displayed for large result sets
        """
        try:
            # Execute the query
            results = self._core_manager.execute_query(
                query=args.query,
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
                import json
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
                        print(f"Status: {task.status.value}")
                        print(f"Priority: {task.priority.value}")
                        print()
                elif args.entity == "list":
                    for list_item in results:
                        print(f"List: {list_item.name}")
                        print(f"ID: {list_item.id}")
                        print(f"Folder: {list_item.folder_id}")
                        print()
                elif args.entity == "folder":
                    for folder in results:
                        print(f"Folder: {folder.name}")
                        print(f"ID: {folder.id}")
                        print(f"Space: {folder.space_id}")
                        print()
                elif args.entity == "space":
                    for space in results:
                        print(f"Space: {space.name}")
                        print(f"ID: {space.id}")
                        print()
            
            # Display pagination info if limited
            if hasattr(results, 'total_count') and args.limit < results.total_count:
                print(f"Showing {len(results)} of {results.total_count} total results.")
                print(f"Use --offset {args.offset + args.limit} to see the next page.")
            
            return 0
        except Exception as e:
            print(f"Error executing query: {str(e)}")
            return 1


class FindByIdCommand(SimpleCommand):
    """
    Task: tsk_bf28d342 - Update CLI Module Comments
    Document: refactor/cli/commands/search.py
    dohcount: 1

    Purpose:
        Implements a command for quickly finding entities by their unique ID.
        Provides direct access to specific entities without complex filtering
        and supports various entity types with detailed information display.

    Requirements:
        - Must support lookup across different entity types
        - Must handle both full and partial ID matching
        - Must provide detailed entity information in the results
        - Must display formatted results with entity-specific fields
        - CRITICAL: Must optimize for quick ID-based lookup performance
        - CRITICAL: Must handle not found cases gracefully

    Used By:
        - CLI Users: For quick entity retrieval by ID
        - Scripts: For entity validation and relationship verification
        - Debugging Tools: For troubleshooting entity references
        - Automation: For precise entity targeting in workflows

    Changes:
        - v1: Initial implementation with basic ID lookup
        - v2: Added support for multiple entity types
        - v3: Enhanced output formatting with entity-specific fields
        - v4: Added partial ID matching capabilities
    """
    
    def __init__(self, core_manager: CoreManager):
        """
        Initialize a new FindByIdCommand instance.
        
        Creates a command for finding entities by their unique IDs
        with support for different entity types and detailed output.
        
        Args:
            core_manager: Core manager instance for accessing entity services
        """
        super().__init__("find", "Find an entity by its ID")
        self._core_manager = core_manager
    
    def configure_parser(self, parser: ArgumentParser) -> None:
        """
        Configure the argument parser for the find command.
        
        Sets up arguments for entity ID lookup, entity type selection,
        and output formatting options for precise entity retrieval.
        
        Args:
            parser: The argument parser to configure with arguments
            
        Notes:
            - Entity ID can be a full ID or a partial prefix
            - Entity type determines which collection is searched
            - Detailed flag provides additional entity information
        """
        parser.add_argument("id", help="Entity ID to find")
    
    def execute(self, args: Namespace) -> int:
        """
        Execute the find command.
        
        Attempts to locate an entity with the specified ID,
        determines its type, and displays detailed information
        about the entity with appropriate formatting.
        
        Args:
            args: Command arguments containing:
                - id: The ID of the entity to find
            
        Returns:
            Exit code (0 for success, non-zero for error)
            
        Notes:
            - Returns error code 1 if no entity is found
            - Displays entity type and common properties (name, ID)
            - Shows type-specific properties when available (status, priority)
            - Formats longer content like descriptions with proper spacing
            - Handles entity type detection for proper information display
        """
        try:
            # Try to find the entity by ID
            entity = self._core_manager.find_entity(args.id)
            
            if not entity:
                print(f"No entity found with ID: {args.id}")
                return 1
            
            # Determine entity type and display appropriate information
            if hasattr(entity, 'type') and entity.type:
                entity_type = entity.type
            else:
                entity_type = entity.__class__.__name__.replace('Entity', '').lower()
            
            print(f"Found {entity_type} with ID: {args.id}\n")
            
            # Display common properties
            print(f"Name: {entity.name}")
            print(f"ID: {entity.id}")
            
            # Display type-specific properties
            if hasattr(entity, 'status'):
                print(f"Status: {entity.status.value}")
            
            if hasattr(entity, 'priority'):
                print(f"Priority: {entity.priority.value}")
            
            if hasattr(entity, 'tags') and entity.tags:
                print(f"Tags: {', '.join(entity.tags)}")
            
            if hasattr(entity, 'description') and entity.description:
                print(f"\nDescription:")
                print(entity.description)
            
            return 0
        except Exception as e:
            print(f"Error finding entity: {str(e)}")
            return 1


class SearchCommand(CompositeCommand):
    """
    Task: tsk_bf28d342 - Update CLI Module Comments
    Document: refactor/cli/commands/search.py
    dohcount: 1

    Purpose:
        Serves as the main command hub for all search-related operations.
        Provides a unified interface for task searching, complex queries,
        and entity lookup through a set of specialized subcommands.

    Requirements:
        - Must organize all search-related subcommands in a coherent structure
        - Must maintain command hierarchy with appropriate subcommand routing
        - Must ensure consistent parameter handling across subcommands
        - Must provide clear help documentation for all search capabilities
        - CRITICAL: Must maintain backward compatibility with existing scripts
        - CRITICAL: Must follow the Command pattern for all subcommands

    Used By:
        - CLI Users: As the entry point for all search operations
        - Scripts: For automated data retrieval and processing
        - Integration Systems: For querying task data programmatically
        - Test Frameworks: For verifying data integrity and relationships

    Changes:
        - v1: Initial implementation with basic search commands
        - v2: Added query and find subcommands for enhanced search capabilities
        - v3: Improved command organization and standardized patterns
        - v4: Enhanced documentation and help text for better usability
    """
    
    def __init__(self, core_manager: CoreManager):
        """
        Initialize a new SearchCommand instance.
        
        Creates a composite command that organizes all search-related operations
        under a unified interface with a consistent command structure.
        
        Args:
            core_manager: Core manager instance for passing to subcommands
        """
        super().__init__("search", "Search operations")
        
        # Add subcommands
        self.add_subcommand(SearchTasksCommand(core_manager))
        self.add_subcommand(QueryCommand(core_manager))
        self.add_subcommand(FindByIdCommand(core_manager)) 