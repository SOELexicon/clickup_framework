"""
CLI commands for saved search functionality.

This module provides command line interface functions for the saved search features.
"""

import argparse
import sys
import os
import json
from typing import Optional, List, Dict, Any

from refactor.storage.saved_searches import SavedSearchesManager
from refactor.storage.export_controller import SearchExportController
from refactor.storage.search_manager_stats_integration import SearchManagerWithStats


def add_saved_search_commands(subparsers):
    """
    Add saved search commands to the CLI parser.
    
    Args:
        subparsers: The subparsers object to add commands to
    """
    # Saved search command
    saved_search_parser = subparsers.add_parser(
        'saved-search',
        help='Manage saved searches'
    )
    
    saved_search_subparsers = saved_search_parser.add_subparsers(
        dest='saved_search_command',
        help='Saved search command'
    )
    
    # Save command
    save_parser = saved_search_subparsers.add_parser(
        'save',
        help='Save a search query'
    )
    save_parser.add_argument(
        'name',
        help='Name of the saved search'
    )
    save_parser.add_argument(
        'query',
        help='Search query to save'
    )
    save_parser.add_argument(
        '--description',
        help='Description of the search query'
    )
    save_parser.add_argument(
        '--tags',
        help='Tags for the search query, comma separated'
    )
    save_parser.add_argument(
        '--category',
        help='Category for the search query'
    )
    save_parser.add_argument(
        '--favorite',
        action='store_true',
        help='Mark the search as a favorite'
    )
    
    # List command
    list_parser = saved_search_subparsers.add_parser(
        'list',
        help='List saved searches'
    )
    list_parser.add_argument(
        '--category',
        help='Filter by category'
    )
    list_parser.add_argument(
        '--tag',
        help='Filter by tag'
    )
    list_parser.add_argument(
        '--name-contains',
        help='Filter by name containing text'
    )
    list_parser.add_argument(
        '--sort-by',
        choices=['name', 'updated_at', 'created_at', 'use_count'],
        default='name',
        help='Sort field'
    )
    
    # Get command
    get_parser = saved_search_subparsers.add_parser(
        'get',
        help='Get a saved search'
    )
    get_parser.add_argument(
        'name',
        help='Name of the saved search'
    )
    get_parser.add_argument(
        '--execute',
        action='store_true',
        help='Execute the search query'
    )
    get_parser.add_argument(
        '--limit',
        type=int,
        help='Limit the number of results'
    )
    
    # Delete command
    delete_parser = saved_search_subparsers.add_parser(
        'delete',
        help='Delete a saved search'
    )
    delete_parser.add_argument(
        'name',
        help='Name of the saved search'
    )
    
    # Template command
    template_parser = saved_search_subparsers.add_parser(
        'template',
        help='Create a search template with variables'
    )
    template_parser.add_argument(
        'name',
        help='Name of the template'
    )
    template_parser.add_argument(
        'query',
        help='Search query with variable placeholders: ${variable_name}'
    )
    template_parser.add_argument(
        '--variables',
        help='Variable names, comma separated (detected automatically if not provided)'
    )
    template_parser.add_argument(
        '--description',
        help='Description of the template'
    )
    template_parser.add_argument(
        '--tags',
        help='Tags for the template, comma separated'
    )
    template_parser.add_argument(
        '--category',
        help='Category for the template'
    )
    template_parser.add_argument(
        '--favorite',
        action='store_true',
        help='Mark the template as a favorite'
    )
    
    # List templates command
    list_templates_parser = saved_search_subparsers.add_parser(
        'list-templates',
        help='List search templates'
    )
    list_templates_parser.add_argument(
        '--category',
        help='Filter by category'
    )
    list_templates_parser.add_argument(
        '--tag',
        help='Filter by tag'
    )
    list_templates_parser.add_argument(
        '--name-contains',
        help='Filter by name containing text'
    )
    list_templates_parser.add_argument(
        '--sort-by',
        choices=['name', 'updated_at', 'created_at', 'use_count'],
        default='name',
        help='Sort field'
    )
    
    # Execute template command
    execute_template_parser = saved_search_subparsers.add_parser(
        'execute-template',
        help='Execute a search template with variable values'
    )
    execute_template_parser.add_argument(
        'name',
        help='Name of the template'
    )
    execute_template_parser.add_argument(
        '--var',
        action='append',
        nargs=2,
        metavar=('VAR_NAME', 'VALUE'),
        help='Variable name and value (can be used multiple times)'
    )
    execute_template_parser.add_argument(
        '--limit',
        type=int,
        help='Limit the number of results'
    )
    
    # History commands
    history_parser = saved_search_subparsers.add_parser(
        'history',
        help='Manage search history'
    )
    history_subparsers = history_parser.add_subparsers(
        dest='history_command',
        help='History command'
    )
    
    # History list command
    history_list_parser = history_subparsers.add_parser(
        'list',
        help='List search history'
    )
    history_list_parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help='Number of history entries to show'
    )
    history_list_parser.add_argument(
        '--query-contains',
        help='Filter by query containing text'
    )
    
    # History run command
    history_run_parser = history_subparsers.add_parser(
        'run',
        help='Run a search from history'
    )
    history_run_parser.add_argument(
        'timestamp',
        help='Timestamp of the history entry'
    )
    history_run_parser.add_argument(
        '--limit',
        type=int,
        help='Limit the number of results'
    )
    
    # History save command
    history_save_parser = history_subparsers.add_parser(
        'save',
        help='Save a history entry as a saved search'
    )
    history_save_parser.add_argument(
        'timestamp',
        help='Timestamp of the history entry'
    )
    history_save_parser.add_argument(
        'name',
        help='Name for the new saved search'
    )
    history_save_parser.add_argument(
        '--description',
        help='Description of the search query'
    )
    history_save_parser.add_argument(
        '--tags',
        help='Tags for the search query, comma separated'
    )
    history_save_parser.add_argument(
        '--category',
        help='Category for the search query'
    )
    history_save_parser.add_argument(
        '--as-template',
        action='store_true',
        help='Save as a template instead of a regular search'
    )
    
    # History delete command
    history_delete_parser = history_subparsers.add_parser(
        'delete',
        help='Delete a history entry'
    )
    history_delete_parser.add_argument(
        'timestamp',
        help='Timestamp of the history entry'
    )
    
    # History clear command
    history_clear_parser = history_subparsers.add_parser(
        'clear',
        help='Clear all search history'
    )
    history_clear_parser.add_argument(
        '--confirm',
        action='store_true',
        help='Confirm clearing history without prompting'
    )

    # Export command
    export_parser = saved_search_subparsers.add_parser(
        'export',
        help='Export saved searches to a file'
    )
    export_parser.add_argument(
        '--output',
        help='Output file path'
    )
    export_parser.add_argument(
        '--favorites-only',
        action='store_true',
        help='Export only favorite searches'
    )
    export_parser.add_argument(
        '--include-templates',
        action='store_true',
        help='Include templates in the export'
    )
    export_parser.add_argument(
        '--templates-only',
        action='store_true',
        help='Export only templates'
    )
    export_parser.add_argument(
        '--category',
        help='Export only searches in this category'
    )
    export_parser.add_argument(
        '--tag',
        help='Export only searches with this tag'
    )
    
    # Import command
    import_parser = saved_search_subparsers.add_parser(
        'import',
        help='Import saved searches from a file'
    )
    import_parser.add_argument(
        'file',
        help='Path to the file to import'
    )
    import_parser.add_argument(
        '--mode',
        choices=['skip', 'replace', 'rename'],
        default='skip',
        help='Import mode for handling conflicts'
    )
    
    # Favorites commands
    favorites_parser = saved_search_subparsers.add_parser(
        'favorites',
        help='Manage favorite searches'
    )
    favorites_subparsers = favorites_parser.add_subparsers(
        dest='favorites_command',
        help='Favorites command'
    )
    
    # Favorites list command
    favorites_list_parser = favorites_subparsers.add_parser(
        'list',
        help='List favorite searches'
    )
    favorites_list_parser.add_argument(
        '--category',
        help='Filter by category'
    )
    favorites_list_parser.add_argument(
        '--tag',
        help='Filter by tag'
    )
    favorites_list_parser.add_argument(
        '--name-contains',
        help='Filter by name containing text'
    )
    favorites_list_parser.add_argument(
        '--sort-by',
        choices=['name', 'updated_at', 'created_at', 'use_count'],
        default='name',
        help='Sort field'
    )
    
    # Favorites add command
    favorites_add_parser = favorites_subparsers.add_parser(
        'add',
        help='Add a search to favorites'
    )
    favorites_add_parser.add_argument(
        'name',
        help='Name of the search to add to favorites'
    )
    
    # Favorites remove command
    favorites_remove_parser = favorites_subparsers.add_parser(
        'remove',
        help='Remove a search from favorites'
    )
    favorites_remove_parser.add_argument(
        'name',
        help='Name of the search to remove from favorites'
    )
    
    # Batch commands
    batch_parser = saved_search_subparsers.add_parser(
        'batch',
        help='Perform batch operations on multiple searches'
    )
    batch_subparsers = batch_parser.add_subparsers(
        dest='batch_command',
        help='Batch command'
    )
    
    # Batch delete command
    batch_delete_parser = batch_subparsers.add_parser(
        'delete',
        help='Delete multiple searches'
    )
    batch_delete_parser.add_argument(
        'names',
        nargs='+',
        help='Names of searches to delete'
    )
    batch_delete_parser.add_argument(
        '--confirm',
        action='store_true',
        help='Confirm deletion without prompting'
    )
    
    # Batch categorize command
    batch_categorize_parser = batch_subparsers.add_parser(
        'categorize',
        help='Set category for multiple searches'
    )
    batch_categorize_parser.add_argument(
        'names',
        nargs='+',
        help='Names of searches to categorize'
    )
    batch_categorize_parser.add_argument(
        'category',
        help='Category to set'
    )
    
    # Batch tag command
    batch_tag_parser = batch_subparsers.add_parser(
        'tag',
        help='Add tags to multiple searches'
    )
    batch_tag_parser.add_argument(
        'names',
        nargs='+',
        help='Names of searches to tag'
    )
    batch_tag_parser.add_argument(
        'tags',
        nargs='+',
        help='Tags to add'
    )
    
    # Batch untag command
    batch_untag_parser = batch_subparsers.add_parser(
        'untag',
        help='Remove tags from multiple searches'
    )
    batch_untag_parser.add_argument(
        'names',
        nargs='+',
        help='Names of searches to untag'
    )
    batch_untag_parser.add_argument(
        'tags',
        nargs='+',
        help='Tags to remove'
    )
    
    # Batch favorite command
    batch_favorite_parser = batch_subparsers.add_parser(
        'favorite',
        help='Mark multiple searches as favorites'
    )
    batch_favorite_parser.add_argument(
        'names',
        nargs='+',
        help='Names of searches to mark as favorites'
    )
    
    # Batch unfavorite command
    batch_unfavorite_parser = batch_subparsers.add_parser(
        'unfavorite',
        help='Remove multiple searches from favorites'
    )
    batch_unfavorite_parser.add_argument(
        'names',
        nargs='+',
        help='Names of searches to remove from favorites'
    )
    
    # Stats commands
    stats_parser = saved_search_subparsers.add_parser(
        'stats',
        help='View search statistics and analytics'
    )
    stats_subparsers = stats_parser.add_subparsers(
        dest='stats_command',
        help='Statistics command'
    )
    
    # Stats most-used command
    stats_most_used_parser = stats_subparsers.add_parser(
        'most-used',
        help='Show most frequently used searches'
    )
    stats_most_used_parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help='Number of searches to show (default: 10)'
    )
    stats_most_used_parser.add_argument(
        '--format',
        choices=['table', 'json'],
        default='table',
        help='Output format (default: table)'
    )
    
    # Stats slowest command
    stats_slowest_parser = stats_subparsers.add_parser(
        'slowest',
        help='Show searches with highest execution times'
    )
    stats_slowest_parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help='Number of searches to show (default: 10)'
    )
    stats_slowest_parser.add_argument(
        '--format',
        choices=['table', 'json'],
        default='table',
        help='Output format (default: table)'
    )
    
    # Stats search-detail command
    stats_detail_parser = stats_subparsers.add_parser(
        'search-detail',
        help='Show detailed statistics for a specific search'
    )
    stats_detail_parser.add_argument(
        'name',
        help='Name of the search'
    )
    stats_detail_parser.add_argument(
        '--format',
        choices=['table', 'json'],
        default='table',
        help='Output format (default: table)'
    )
    
    # Stats report command
    stats_report_parser = stats_subparsers.add_parser(
        'report',
        help='Generate a comprehensive statistics report'
    )
    stats_report_parser.add_argument(
        '--output',
        help='Output file path (default: stdout)'
    )
    stats_report_parser.add_argument(
        '--format',
        choices=['table', 'json'],
        default='table',
        help='Output format (default: table)'
    )
    
    # Stats suggestions command
    stats_suggestions_parser = stats_subparsers.add_parser(
        'suggestions',
        help='Get search optimization suggestions'
    )
    stats_suggestions_parser.add_argument(
        '--format',
        choices=['table', 'json'],
        default='table',
        help='Output format (default: table)'
    )
    
    # Stats clear command
    stats_clear_parser = stats_subparsers.add_parser(
        'clear',
        help='Clear all search statistics'
    )
    stats_clear_parser.add_argument(
        '--confirm',
        action='store_true',
        help='Confirm clearing statistics without prompting'
    )

    # Stats dashboard command
    stats_dashboard_parser = stats_subparsers.add_parser(
        'dashboard',
        help='View search statistics dashboard'
    )
    stats_dashboard_parser.add_argument(
        '--format',
        choices=['text', 'html', 'json'],
        default='text',
        help='Dashboard format (default: text)'
    )
    stats_dashboard_parser.add_argument(
        '--output',
        help='Output file path for HTML or JSON output'
    )


def handle_saved_search_commands(args):
    """
    Handle saved search commands based on parsed arguments.
    
    Args:
        args: The parsed command line arguments
    """
    # Create manager
    manager = SavedSearchesManager()
    
    # Handle subcommands
    if args.saved_search_command == 'save':
        # Parse tags
        tags = []
        if args.tags:
            tags = [tag.strip() for tag in args.tags.split(',')]
        
        # Save the search
        search = manager.save_search(
            name=args.name,
            query=args.query,
            description=args.description or '',
            tags=tags,
            category=args.category or ''
        )
        
        # Mark as favorite if requested
        if args.favorite:
            manager.add_to_favorites(args.name)
            print(f"Saved search '{args.name}' and marked as favorite")
        else:
            print(f"Saved search '{args.name}'")
    
    elif args.saved_search_command == 'list':
        # List searches with optional filters
        searches = manager.list_searches(
            category=args.category,
            tag=args.tag,
            name_contains=args.name_contains,
            sort_by=args.sort_by
        )
        
        # Display results
        if not searches:
            print("No saved searches found")
        else:
            print(f"Found {len(searches)} saved searches:")
            for search in searches:
                favorite_mark = "★ " if search.is_favorite else "  "
                category_info = f" [{search.category}]" if search.category else ""
                tags_info = f" (tags: {', '.join(search.tags)})" if search.tags else ""
                print(f"{favorite_mark}{search.name}{category_info}{tags_info}")
                if search.description:
                    print(f"  Description: {search.description}")
                print(f"  Query: {search.query}")
                print()
    
    elif args.saved_search_command == 'export':
        # Create export controller
        export_controller = SearchExportController(manager)
        
        # Export searches
        json_data = export_controller.export_searches(
            output_path=args.output,
            favorites_only=args.favorites_only,
            include_templates=args.include_templates,
            templates_only=args.templates_only,
            category=args.category,
            tag=args.tag
        )
        
        # If no output file specified, print to stdout
        if not args.output:
            print(json_data)
        else:
            print(f"Exported searches to {args.output}")
    
    elif args.saved_search_command == 'import':
        # Create export controller
        export_controller = SearchExportController(manager)
        
        # Import searches
        stats = export_controller.import_searches(
            import_path=args.file,
            mode=args.mode
        )
        
        # Display results
        print(f"Import complete:")
        print(f"  Total: {stats['total']}")
        print(f"  Imported: {stats['imported']}")
        print(f"  Skipped: {stats['skipped']}")
        print(f"  Replaced: {stats['replaced']}")
        print(f"  Renamed: {stats['renamed']}")
        print(f"  Errors: {stats['errors']}")
    
    elif args.saved_search_command == 'favorites':
        # Handle favorites subcommands
        if args.favorites_command == 'list':
            # List favorite searches
            favorites = manager.list_favorites(
                category=args.category,
                tag=args.tag,
                name_contains=args.name_contains,
                sort_by=args.sort_by
            )
            
            # Display results
            if not favorites:
                print("No favorite searches found")
            else:
                print(f"Found {len(favorites)} favorite searches:")
                for search in favorites:
                    category_info = f" [{search.category}]" if search.category else ""
                    tags_info = f" (tags: {', '.join(search.tags)})" if search.tags else ""
                    print(f"★ {search.name}{category_info}{tags_info}")
                    if search.description:
                        print(f"  Description: {search.description}")
                    print(f"  Query: {search.query}")
                    print()
        
        elif args.favorites_command == 'add':
            # Add search to favorites
            result = manager.add_to_favorites(args.name)
            if result:
                print(f"Added '{args.name}' to favorites")
            else:
                print(f"Error: Search '{args.name}' not found")
                sys.exit(1)
        
        elif args.favorites_command == 'remove':
            # Remove search from favorites
            result = manager.remove_from_favorites(args.name)
            if result:
                print(f"Removed '{args.name}' from favorites")
            else:
                print(f"Error: Search '{args.name}' not found or not in favorites")
                sys.exit(1)
    
    elif args.saved_search_command == 'batch':
        # Handle batch subcommands
        if args.batch_command == 'delete':
            # Confirm deletion if not already confirmed
            if not args.confirm:
                confirm = input(f"Delete {len(args.names)} searches? (y/n): ")
                if confirm.lower() != 'y':
                    print("Operation cancelled")
                    return
            
            # Delete searches
            success_count, failed_names = manager.batch_delete(args.names)
            
            # Display results
            print(f"Deleted {success_count} searches")
            if failed_names:
                print(f"Failed to delete {len(failed_names)} searches:")
                for name in failed_names:
                    print(f"  - {name}")
        
        elif args.batch_command == 'categorize':
            # Set category for searches
            success_count, failed_names = manager.batch_categorize(args.names, args.category)
            
            # Display results
            print(f"Set category '{args.category}' for {success_count} searches")
            if failed_names:
                print(f"Failed to update {len(failed_names)} searches:")
                for name in failed_names:
                    print(f"  - {name}")
        
        elif args.batch_command == 'tag':
            # Add tags to searches
            success_count, failed_names = manager.batch_add_tags(args.names, args.tags)
            
            # Display results
            tags_str = ", ".join(args.tags)
            print(f"Added tags '{tags_str}' to {success_count} searches")
            if failed_names:
                print(f"Failed to update {len(failed_names)} searches:")
                for name in failed_names:
                    print(f"  - {name}")
        
        elif args.batch_command == 'untag':
            # Remove tags from searches
            success_count, failed_names = manager.batch_remove_tags(args.names, args.tags)
            
            # Display results
            tags_str = ", ".join(args.tags)
            print(f"Removed tags '{tags_str}' from {success_count} searches")
            if failed_names:
                print(f"Failed to update {len(failed_names)} searches:")
                for name in failed_names:
                    print(f"  - {name}")
        
        elif args.batch_command == 'favorite':
            # Mark searches as favorites
            success_count, failed_names = manager.batch_toggle_favorite(args.names, True)
            
            # Display results
            print(f"Marked {success_count} searches as favorites")
            if failed_names:
                print(f"Failed to update {len(failed_names)} searches:")
                for name in failed_names:
                    print(f"  - {name}")
        
        elif args.batch_command == 'unfavorite':
            # Remove searches from favorites
            success_count, failed_names = manager.batch_toggle_favorite(args.names, False)
            
            # Display results
            print(f"Removed {success_count} searches from favorites")
            if failed_names:
                print(f"Failed to update {len(failed_names)} searches:")
                for name in failed_names:
                    print(f"  - {name}")
    
    elif args.saved_search_command == 'stats':
        # Create stats manager
        stats_manager = SearchManagerWithStats(manager)
        
        # Handle stats subcommands
        if args.stats_command == 'most-used':
            # Get most used searches
            most_used = stats_manager.get_most_used_searches(args.limit)
            
            # Format and display results
            if not most_used:
                print("No search usage data found")
                return
            
            if args.format == 'json':
                result = [{"name": name, "count": count} for name, count in most_used]
                print(json.dumps(result, indent=2))
            else:
                print(f"Most frequently used searches (top {len(most_used)}):")
                print()
                print(f"{'SEARCH NAME':<30} {'USAGE COUNT':<12}")
                print(f"{'-'*30} {'-'*12}")
                for name, count in most_used:
                    print(f"{name:<30} {count:<12}")
        
        elif args.stats_command == 'slowest':
            # Get slowest searches
            slowest = stats_manager.get_slowest_searches(args.limit)
            
            # Format and display results
            if not slowest:
                print("No search performance data found")
                return
            
            if args.format == 'json':
                result = [{"name": name, "avg_execution_time_ms": time} for name, time in slowest]
                print(json.dumps(result, indent=2))
            else:
                print(f"Slowest searches by average execution time (top {len(slowest)}):")
                print()
                print(f"{'SEARCH NAME':<30} {'AVG TIME (MS)':<15}")
                print(f"{'-'*30} {'-'*15}")
                for name, time in slowest:
                    print(f"{name:<30} {time:<15.2f}")
        
        elif args.stats_command == 'search-detail':
            # Get detailed stats for the search
            stats = stats_manager.get_search_performance_stats(args.name)
            
            if not stats:
                print(f"No statistics found for search '{args.name}'")
                return
            
            if args.format == 'json':
                print(json.dumps(stats, indent=2))
            else:
                print(f"Performance statistics for '{args.name}':")
                print()
                print(f"{'METRIC':<20} {'VALUE':<15}")
                print(f"{'-'*20} {'-'*15}")
                
                if 'min' in stats:
                    print(f"{'Min time (ms)':<20} {stats['min']:<15.2f}")
                if 'max' in stats:
                    print(f"{'Max time (ms)':<20} {stats['max']:<15.2f}")
                if 'avg' in stats:
                    print(f"{'Avg time (ms)':<20} {stats['avg']:<15.2f}")
                if 'min' in stats:
                    print(f"{'Sample count':<20} {stats.get('count', 0):<15}")
                
                print()
                if 'min_results' in stats:
                    print(f"{'Min results':<20} {stats['min_results']:<15}")
                if 'max_results' in stats:
                    print(f"{'Max results':<20} {stats['max_results']:<15}")
                if 'avg_results' in stats:
                    print(f"{'Avg results':<20} {stats['avg_results']:<15.2f}")
        
        elif args.stats_command == 'report':
            # Generate comprehensive report
            report = stats_manager.get_stats_report()
            
            # Format and output
            if args.format == 'json':
                if args.output:
                    with open(args.output, 'w') as f:
                        json.dump(report, f, indent=2)
                    print(f"Report saved to {args.output}")
                else:
                    print(json.dumps(report, indent=2))
            else:
                # Print summary section
                print("SEARCH STATISTICS REPORT")
                print("========================")
                print()
                print("SUMMARY:")
                print(f"  Total searches executed: {report['summary'].get('total_searches', 0)}")
                print(f"  Unique searches used: {report['summary'].get('unique_searches', 0)}")
                print(f"  Total favorites used: {report['summary'].get('total_favorites_used', 0)}")
                print(f"  Unique favorites: {report['summary'].get('unique_favorites', 0)}")
                if 'avg_execution_time' in report['summary']:
                    print(f"  Average execution time: {report['summary']['avg_execution_time']:.2f}ms")
                print(f"  Last updated: {report['summary'].get('last_updated', 'N/A')}")
                
                # Print top searches
                if report.get('top_searches'):
                    print()
                    print("TOP SEARCHES:")
                    for name, count in report['top_searches']:
                        print(f"  {name}: {count} uses")
                
                # Print slowest searches
                if report.get('slowest_searches'):
                    print()
                    print("SLOWEST SEARCHES:")
                    for name, time in report['slowest_searches']:
                        print(f"  {name}: {time:.2f}ms average")
                
                # Print usage patterns
                if report.get('usage_patterns') and report['usage_patterns'].get('by_hour'):
                    print()
                    print("USAGE BY HOUR:")
                    hours = report['usage_patterns']['by_hour']
                    for hour in sorted(hours.keys(), key=int):
                        print(f"  Hour {hour}: {hours[hour]} searches")
                
                if args.output:
                    # Write full report to file
                    with open(args.output, 'w') as f:
                        f.write("SEARCH STATISTICS REPORT\n")
                        f.write("========================\n\n")
                        
                        f.write("SUMMARY:\n")
                        for key, value in report['summary'].items():
                            if key == 'avg_execution_time':
                                f.write(f"  {key}: {value:.2f}ms\n")
                            else:
                                f.write(f"  {key}: {value}\n")
                        
                        f.write("\nTOP SEARCHES:\n")
                        for name, count in report.get('top_searches', []):
                            f.write(f"  {name}: {count} uses\n")
                        
                        f.write("\nSLOWEST SEARCHES:\n")
                        for name, time in report.get('slowest_searches', []):
                            f.write(f"  {name}: {time:.2f}ms average\n")
                        
                        # Include more detailed sections in the file
                        f.write("\nPOPULAR SEARCH TERMS:\n")
                        for term, count in report.get('popular_terms', []):
                            f.write(f"  {term}: {count} occurrences\n")
                        
                        f.write("\nCATEGORY USAGE:\n")
                        for category, count in report.get('category_usage', []):
                            f.write(f"  {category}: {count} uses\n")
                    
                    print(f"\nDetailed report saved to {args.output}")
        
        elif args.stats_command == 'suggestions':
            # Get optimization suggestions
            suggestions = stats_manager.get_optimization_suggestions()
            
            if not suggestions:
                print("No optimization suggestions available")
                return
            
            if args.format == 'json':
                print(json.dumps(suggestions, indent=2))
            else:
                print("SEARCH OPTIMIZATION SUGGESTIONS")
                print("===============================")
                print()
                
                for i, suggestion in enumerate(suggestions, 1):
                    print(f"Suggestion {i}:")
                    print(f"  Target: {suggestion.get('target', 'N/A')}")
                    print(f"  Type: {suggestion.get('type', 'general')}")
                    print(f"  Reason: {suggestion.get('reason', 'N/A')}")
                    print(f"  Action: {suggestion.get('action', 'N/A')}")
                    print()
        
        elif args.stats_command == 'clear':
            # Confirm clearing if not already confirmed
            if not args.confirm:
                confirm = input("Clear all search statistics? This action cannot be undone. (y/n): ")
                if confirm.lower() != 'y':
                    print("Operation cancelled")
                    return
            
            # Clear statistics
            stats_manager.clear_stats()
            print("All search statistics have been cleared")
        
        elif args.stats_command == 'dashboard':
            # Generate dashboard
            from refactor.dashboard.search_stats_dashboard import generate_dashboard
            generate_dashboard(args.output, args.format)
    
    # Add handling for other commands as needed 