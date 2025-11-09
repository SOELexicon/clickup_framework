"""
Search statistics tracking module for monitoring search usage patterns.

This module provides functionality for recording and analyzing search usage,
including tracking frequency, performance metrics, and popular search patterns.
"""

import os
import json
import time
from datetime import datetime
from collections import defaultdict, Counter
from typing import Dict, List, Optional, Any, Tuple, Union


class SearchStatsManager:
    """
    Manages the collection and analysis of search usage statistics.
    
    This class tracks search usage patterns, including:
    - Search frequency (most used searches)
    - Execution time statistics
    - Result count statistics
    - Popular search terms and patterns
    - Favorites usage analytics
    
    The statistics are stored in a JSON file and can be queried for reporting
    and optimization purposes.
    """
    
    def __init__(self, storage_path: str):
        """
        Initialize the search statistics manager.
        
        Args:
            storage_path: Directory path where statistics will be stored
        """
        self.storage_path = storage_path
        self.stats_file = os.path.join(storage_path, "search_stats.json")
        self.stats = self._load_stats()
        
    def _load_stats(self) -> Dict[str, Any]:
        """
        Load statistics from the stats file or create default structure if not exists.
        
        Returns:
            Dictionary containing search statistics data
        """
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                # Return default structure if file is corrupted or unreadable
                return self._create_default_stats()
        else:
            return self._create_default_stats()
    
    def _create_default_stats(self) -> Dict[str, Any]:
        """
        Create the default statistics data structure.
        
        Returns:
            Dictionary with default statistics structure
        """
        return {
            "search_counts": {},  # Search name -> count
            "execution_times": {},  # Search name -> list of execution times
            "result_counts": {},  # Search name -> list of result counts
            "favorite_usage": {},  # Favorite search name -> count
            "term_frequency": {},  # Search term -> count
            "category_usage": {},  # Category -> count
            "tag_usage": {},  # Tag -> count
            "hourly_usage": {str(i): 0 for i in range(24)},  # Hour -> count
            "daily_usage": {str(i): 0 for i in range(7)},  # Day of week -> count
            "last_updated": datetime.now().isoformat()
        }
        
    def _save_stats(self) -> None:
        """Save the current statistics to the stats file."""
        os.makedirs(os.path.dirname(self.stats_file), exist_ok=True)
        with open(self.stats_file, "w") as f:
            json.dump(self.stats, f, indent=2)
        
    def record_search(self, search_name: str, query: str, 
                      execution_time_ms: float, result_count: int,
                      is_favorite: bool = False, category: Optional[str] = None,
                      tags: Optional[List[str]] = None) -> None:
        """
        Record a search operation in the statistics.
        
        Args:
            search_name: Name of the search
            query: The search query string
            execution_time_ms: Execution time in milliseconds
            result_count: Number of results returned
            is_favorite: Whether the search is a favorite
            category: Search category, if any
            tags: Search tags, if any
        """
        # Update search counts
        self.stats["search_counts"][search_name] = self.stats["search_counts"].get(search_name, 0) + 1
        
        # Update execution times
        if search_name not in self.stats["execution_times"]:
            self.stats["execution_times"][search_name] = []
        self.stats["execution_times"][search_name].append(execution_time_ms)
        
        # Limit the number of execution times stored to prevent excessive growth
        if len(self.stats["execution_times"][search_name]) > 100:
            self.stats["execution_times"][search_name] = self.stats["execution_times"][search_name][-100:]
            
        # Update result counts
        if search_name not in self.stats["result_counts"]:
            self.stats["result_counts"][search_name] = []
        self.stats["result_counts"][search_name].append(result_count)
        
        # Limit the number of result counts stored
        if len(self.stats["result_counts"][search_name]) > 100:
            self.stats["result_counts"][search_name] = self.stats["result_counts"][search_name][-100:]
            
        # Update favorite usage
        if is_favorite:
            self.stats["favorite_usage"][search_name] = self.stats["favorite_usage"].get(search_name, 0) + 1
            
        # Update term frequency (simple tokenization)
        terms = query.lower().split()
        for term in terms:
            self.stats["term_frequency"][term] = self.stats["term_frequency"].get(term, 0) + 1
            
        # Update category usage
        if category:
            self.stats["category_usage"][category] = self.stats["category_usage"].get(category, 0) + 1
            
        # Update tag usage
        if tags:
            for tag in tags:
                self.stats["tag_usage"][tag] = self.stats["tag_usage"].get(tag, 0) + 1
                
        # Update time-based usage
        now = datetime.now()
        hour = str(now.hour)
        day = str(now.weekday())
        
        self.stats["hourly_usage"][hour] = self.stats["hourly_usage"].get(hour, 0) + 1
        self.stats["daily_usage"][day] = self.stats["daily_usage"].get(day, 0) + 1
        
        # Update last updated timestamp
        self.stats["last_updated"] = now.isoformat()
        
        # Save updated stats
        self._save_stats()
        
    def get_most_used_searches(self, limit: int = 10) -> List[Tuple[str, int]]:
        """
        Get the most frequently used searches.
        
        Args:
            limit: Maximum number of searches to return
            
        Returns:
            List of (search_name, count) tuples, sorted by count descending
        """
        return sorted(
            self.stats["search_counts"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]
        
    def get_slowest_searches(self, limit: int = 10) -> List[Tuple[str, float]]:
        """
        Get the searches with the highest average execution time.
        
        Args:
            limit: Maximum number of searches to return
            
        Returns:
            List of (search_name, avg_time_ms) tuples, sorted by time descending
        """
        avg_times = []
        for name, times in self.stats["execution_times"].items():
            if times:  # Ensure we have data
                avg_time = sum(times) / len(times)
                avg_times.append((name, avg_time))
                
        return sorted(avg_times, key=lambda x: x[1], reverse=True)[:limit]
        
    def get_most_used_favorites(self, limit: int = 10) -> List[Tuple[str, int]]:
        """
        Get the most frequently used favorite searches.
        
        Args:
            limit: Maximum number of searches to return
            
        Returns:
            List of (search_name, count) tuples, sorted by count descending
        """
        return sorted(
            self.stats["favorite_usage"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]
        
    def get_popular_search_terms(self, limit: int = 20) -> List[Tuple[str, int]]:
        """
        Get the most frequently used search terms.
        
        Args:
            limit: Maximum number of terms to return
            
        Returns:
            List of (term, count) tuples, sorted by count descending
        """
        return sorted(
            self.stats["term_frequency"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]
        
    def get_category_usage(self) -> List[Tuple[str, int]]:
        """
        Get category usage statistics.
        
        Returns:
            List of (category, count) tuples, sorted by count descending
        """
        return sorted(
            self.stats["category_usage"].items(),
            key=lambda x: x[1],
            reverse=True
        )
        
    def get_tag_usage(self, limit: int = 20) -> List[Tuple[str, int]]:
        """
        Get tag usage statistics.
        
        Args:
            limit: Maximum number of tags to return
            
        Returns:
            List of (tag, count) tuples, sorted by count descending
        """
        return sorted(
            self.stats["tag_usage"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]
        
    def get_usage_by_hour(self) -> Dict[str, int]:
        """
        Get search usage grouped by hour of day.
        
        Returns:
            Dictionary mapping hour (0-23) to usage count
        """
        return self.stats["hourly_usage"]
        
    def get_usage_by_day(self) -> Dict[str, int]:
        """
        Get search usage grouped by day of week.
        
        Returns:
            Dictionary mapping day (0-6, Monday is 0) to usage count
        """
        return self.stats["daily_usage"]
        
    def get_execution_time_stats(self, search_name: str) -> Dict[str, float]:
        """
        Get execution time statistics for a specific search.
        
        Args:
            search_name: Name of the search
            
        Returns:
            Dictionary with min, max, avg execution times
            Empty dict if search doesn't exist
        """
        if search_name not in self.stats["execution_times"]:
            return {}
            
        times = self.stats["execution_times"][search_name]
        if not times:
            return {}
            
        return {
            "min": min(times),
            "max": max(times),
            "avg": sum(times) / len(times),
            "count": len(times)
        }
        
    def get_result_count_stats(self, search_name: str) -> Dict[str, Union[float, int]]:
        """
        Get result count statistics for a specific search.
        
        Args:
            search_name: Name of the search
            
        Returns:
            Dictionary with min, max, avg result counts
            Empty dict if search doesn't exist
        """
        if search_name not in self.stats["result_counts"]:
            return {}
            
        counts = self.stats["result_counts"][search_name]
        if not counts:
            return {}
            
        return {
            "min": min(counts),
            "max": max(counts),
            "avg": sum(counts) / len(counts),
            "count": len(counts)
        }
        
    def clear_stats(self) -> None:
        """Reset all statistics to defaults."""
        self.stats = self._create_default_stats()
        self._save_stats()
        
    def generate_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive statistics report.
        
        Returns:
            Dictionary containing summary statistics and insights
        """
        report = {
            "summary": {
                "total_searches": sum(self.stats["search_counts"].values()),
                "unique_searches": len(self.stats["search_counts"]),
                "total_favorites_used": sum(self.stats["favorite_usage"].values()),
                "unique_favorites": len(self.stats["favorite_usage"]),
                "last_updated": self.stats["last_updated"]
            },
            "top_searches": self.get_most_used_searches(10),
            "top_favorites": self.get_most_used_favorites(10),
            "slowest_searches": self.get_slowest_searches(5),
            "popular_terms": self.get_popular_search_terms(10),
            "category_usage": self.get_category_usage(),
            "tag_usage": self.get_tag_usage(10),
            "usage_patterns": {
                "by_hour": self.get_usage_by_hour(),
                "by_day": self.get_usage_by_day()
            }
        }
        
        # Calculate average execution time across all searches
        all_times = []
        for times in self.stats["execution_times"].values():
            all_times.extend(times)
            
        if all_times:
            report["summary"]["avg_execution_time"] = sum(all_times) / len(all_times)
            
        return report

    def get_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """
        Generate suggestions for search optimizations based on statistics.
        
        Returns:
            List of suggestion dictionaries with reason and action
        """
        suggestions = []
        
        # Check for slow searches that are frequently used
        most_used = dict(self.get_most_used_searches(20))
        slowest = dict(self.get_slowest_searches(20))
        
        for name in set(most_used.keys()).intersection(set(slowest.keys())):
            if most_used[name] > 5 and slowest[name] > 100:  # Used more than 5 times and >100ms
                suggestions.append({
                    "type": "performance",
                    "target": name,
                    "reason": f"Frequently used search ({most_used[name]} times) with high execution time ({slowest[name]:.1f}ms)",
                    "action": "Consider optimizing or caching this search query"
                })
                
        # Suggest making frequently used searches into favorites
        for name, count in self.get_most_used_searches(20):
            if count > 10 and name not in self.stats["favorite_usage"]:
                suggestions.append({
                    "type": "usability",
                    "target": name,
                    "reason": f"Frequently used search ({count} times) that isn't a favorite",
                    "action": "Consider marking as a favorite for quicker access"
                })
                
        # Suggest categories for organization if many searches without categories
        uncategorized = []
        for name in self.stats["search_counts"].keys():
            has_category = False
            for category in self.stats["category_usage"].keys():
                if category in name.lower():
                    has_category = True
                    break
            if not has_category:
                uncategorized.append(name)
                
        if len(uncategorized) > 5:
            suggestions.append({
                "type": "organization",
                "target": "multiple",
                "reason": f"Found {len(uncategorized)} searches without categories",
                "action": "Consider organizing searches into categories for better management"
            })
            
        return suggestions 