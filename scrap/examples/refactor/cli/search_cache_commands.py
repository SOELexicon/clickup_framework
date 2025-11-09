"""
Search Cache CLI Commands

This module provides CLI commands for managing the search cache functionality,
including viewing cache statistics, clearing the cache, and configuring cache settings.
"""

import argparse
import textwrap
from typing import Dict, List, Optional, Any

from refactor.storage.saved_searches import SavedSearchesManager
from refactor.storage.cache.search_cache import SearchCache
from refactor.storage.cache.search_manager_cache_integration import SearchManagerWithCache


def add_cache_commands(subparsers):
    """
    Add cache-related commands to the CLI parser.
    
    Args:
        subparsers: argparse subparsers object to add commands to
    """
    # Cache statistics command
    cache_stats_parser = subparsers.add_parser(
        'cache-stats',
        help='View search cache statistics',
        description='Display statistics about the search cache, including hit rate and cache size.'
    )
    cache_stats_parser.add_argument(
        'template_file',
        help='Path to the ClickUp JSON template file'
    )
    cache_stats_parser.set_defaults(func=show_cache_stats)
    
    # Clear cache command
    clear_cache_parser = subparsers.add_parser(
        'clear-cache',
        help='Clear the search cache',
        description='Remove all entries from the search cache.'
    )
    clear_cache_parser.add_argument(
        'template_file',
        help='Path to the ClickUp JSON template file'
    )
    clear_cache_parser.set_defaults(func=clear_cache)
    
    # Configure cache command
    configure_cache_parser = subparsers.add_parser(
        'configure-cache',
        help='Configure the search cache settings',
        description='Update search cache configuration settings, such as maximum size and expiration time.'
    )
    configure_cache_parser.add_argument(
        'template_file',
        help='Path to the ClickUp JSON template file'
    )
    configure_cache_parser.add_argument(
        '--max-size',
        type=int,
        help='Maximum number of entries in the cache'
    )
    configure_cache_parser.add_argument(
        '--expiration',
        type=int,
        help='Default expiration time in seconds'
    )
    configure_cache_parser.set_defaults(func=configure_cache)
    
    # Invalidate cache entry command
    invalidate_cache_parser = subparsers.add_parser(
        'invalidate-cache',
        help='Invalidate specific cache entries',
        description='Remove specific entries from the search cache.'
    )
    invalidate_cache_parser.add_argument(
        'template_file',
        help='Path to the ClickUp JSON template file'
    )
    cache_target_group = invalidate_cache_parser.add_mutually_exclusive_group(required=True)
    cache_target_group.add_argument(
        '--query',
        help='Specific query string to invalidate in the cache'
    )
    cache_target_group.add_argument(
        '--search',
        help='Name of saved search to invalidate in the cache'
    )
    cache_target_group.add_argument(
        '--all',
        action='store_true',
        help='Invalidate all cache entries'
    )
    invalidate_cache_parser.set_defaults(func=invalidate_cache)


def get_cache_manager(template_file: str) -> SearchManagerWithCache:
    """
    Create a SearchManagerWithCache instance for the given template file.
    
    Args:
        template_file: Path to the ClickUp JSON template file
        
    Returns:
        SearchManagerWithCache instance
    """
    # Create the basic SavedSearchesManager first
    search_manager = SavedSearchesManager()
    
    # Wrap it with the cache integration
    return SearchManagerWithCache(search_manager)


def show_cache_stats(args):
    """
    Handle the cache-stats command.
    
    Args:
        args: Command line arguments
    """
    cache_manager = get_cache_manager(args.template_file)
    stats = cache_manager.get_cache_stats()
    
    # Format the stats for display
    print("\nSearch Cache Statistics")
    print("======================")
    print(f"Cache Size: {stats['size']} / {stats['max_size']} entries")
    print(f"Hit Rate: {stats['hit_rate']:.2%}")
    print(f"Hits: {stats['hits']}")
    print(f"Misses: {stats['misses']}")
    print(f"Inserts: {stats['inserts']}")
    print(f"Evictions: {stats['evictions']}")
    print(f"Expirations: {stats['expirations']}")
    print()
    
    # Provide interpretation
    if stats['hit_rate'] < 0.3 and (stats['hits'] + stats['misses']) > 10:
        print("Note: Low hit rate suggests the cache may not be effectively utilized.")
        print("Consider reviewing search patterns or increasing cache size.")
    elif stats['evictions'] > stats['size'] * 2:
        print("Note: High eviction rate suggests the cache may be too small.")
        print("Consider increasing the cache size for better performance.")


def clear_cache(args):
    """
    Handle the clear-cache command.
    
    Args:
        args: Command line arguments
    """
    cache_manager = get_cache_manager(args.template_file)
    cache_manager.clear_cache()
    print("Search cache cleared successfully.")


def configure_cache(args):
    """
    Handle the configure-cache command.
    
    Args:
        args: Command line arguments
    """
    cache_manager = get_cache_manager(args.template_file)
    
    # Check which parameters were provided
    max_size = args.max_size
    expiration = args.expiration
    
    if max_size is None and expiration is None:
        print("Error: At least one configuration parameter must be provided.")
        print("Use --max-size and/or --expiration to set configuration values.")
        return
    
    # Get current stats for comparison
    before_stats = cache_manager.get_cache_stats()
    
    # Update the configuration
    cache_manager.configure_cache(
        max_size=max_size,
        default_expiration=expiration
    )
    
    # Show what was updated
    print("Cache configuration updated:")
    if max_size is not None:
        print(f"  - Max size: {before_stats['max_size']} → {max_size}")
    if expiration is not None:
        print(f"  - Default expiration: {cache_manager.cache_manager.default_expiration} → {expiration} seconds")


def invalidate_cache(args):
    """
    Handle the invalidate-cache command.
    
    Args:
        args: Command line arguments
    """
    cache_manager = get_cache_manager(args.template_file)
    
    if args.all:
        cache_manager.clear_cache()
        print("All cache entries invalidated successfully.")
    elif args.query:
        if cache_manager.invalidate_cache_entry(args.query):
            print(f"Cache entry for query '{args.query}' invalidated successfully.")
        else:
            print(f"No cache entry found for query '{args.query}'.")
    elif args.search:
        if cache_manager.invalidate_search_cache(args.search):
            print(f"Cache entry for saved search '{args.search}' invalidated successfully.")
        else:
            print(f"No cache entry found for saved search '{args.search}' or search does not exist.") 