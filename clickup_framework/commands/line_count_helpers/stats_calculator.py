"""
Statistical analysis and calculations for line count data.

This module provides utilities to compute aggregated statistics from line count
results, including totals, averages, percentiles, and language breakdowns.

Variables:    None
Classes:      StatsCalculator
"""

from typing import Dict, Any
from statistics import quantiles


class StatsCalculator:
    """
    Calculate statistical metrics from line count data.

    Purpose:    Compute aggregate statistics, percentiles, and language breakdowns
    Usage:      Call static methods with loc_data dict from LineCounter.count_files()
    Version:    0.1.0
    Changes:    [v0.1.0] Initial: statistics calculation engine
    """

    @staticmethod
    def total_lines(loc_data: Dict[str, Dict[str, Any]]) -> int:
        """
        Calculate total lines across all files.

        Args:
            loc_data: Dictionary mapping file paths to line count data

        Returns:
            Total line count across all files
        """
        return sum(file_info.get('total', 0) for file_info in loc_data.values())

    @staticmethod
    def total_files(loc_data: Dict[str, Dict[str, Any]]) -> int:
        """
        Count total number of files analyzed.

        Args:
            loc_data: Dictionary mapping file paths to line count data

        Returns:
            Number of files in the dataset
        """
        return len(loc_data)

    @staticmethod
    def average_file_size(loc_data: Dict[str, Dict[str, Any]]) -> float:
        """
        Calculate average lines per file.

        Args:
            loc_data: Dictionary mapping file paths to line count data

        Returns:
            Average lines per file (0 if no files)
        """
        total_files = StatsCalculator.total_files(loc_data)
        if total_files == 0:
            return 0.0

        total_lines = StatsCalculator.total_lines(loc_data)
        return total_lines / total_files

    @staticmethod
    def lines_by_language(loc_data: Dict[str, Dict[str, Any]]) -> Dict[str, int]:
        """
        Aggregate line counts by programming language.

        Args:
            loc_data: Dictionary mapping file paths to line count data

        Returns:
            Dictionary mapping language name to total lines in that language,
            sorted by line count descending
        """
        language_totals = {}
        for file_info in loc_data.values():
            language = file_info.get('language', 'Unknown')
            total = file_info.get('total', 0)
            language_totals[language] = language_totals.get(language, 0) + total

        # Sort by line count descending
        return dict(sorted(language_totals.items(),
                          key=lambda x: x[1],
                          reverse=True))

    @staticmethod
    def percentile_analysis(loc_data: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate percentiles for file sizes.

        Computes p50 (median), p75, p90, p95, and p99 percentiles for line counts
        across all files to understand distribution.

        Args:
            loc_data: Dictionary mapping file paths to line count data

        Returns:
            Dictionary with keys: 'p50', 'p75', 'p90', 'p95', 'p99'
            Each value is the line count at that percentile (0 if < 5 files)
        """
        file_counts = [info.get('total', 0) for info in loc_data.values()]

        # Need at least 5 files for meaningful percentiles
        if len(file_counts) < 5:
            return {
                'p50': 0.0,
                'p75': 0.0,
                'p90': 0.0,
                'p95': 0.0,
                'p99': 0.0,
            }

        # Sort to compute percentiles
        sorted_counts = sorted(file_counts)

        # Use quantiles to compute percentiles
        # quantiles returns n-1 cut points dividing into n equal groups
        try:
            q_results = quantiles(sorted_counts, n=100)
            return {
                'p50': float(q_results[49]),    # Index 49 = 50th percentile
                'p75': float(q_results[74]),    # Index 74 = 75th percentile
                'p90': float(q_results[89]),    # Index 89 = 90th percentile
                'p95': float(q_results[94]),    # Index 94 = 95th percentile
                'p99': float(q_results[98]),    # Index 98 = 99th percentile
            }
        except (ValueError, IndexError):
            # Fallback if quantiles fails
            return {
                'p50': 0.0,
                'p75': 0.0,
                'p90': 0.0,
                'p95': 0.0,
                'p99': 0.0,
            }
