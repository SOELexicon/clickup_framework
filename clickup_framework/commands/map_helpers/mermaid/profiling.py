"""Performance profiling utilities for Mermaid diagram generation.

This module provides tools to measure and report on diagram generation performance:
- Execution time tracking for generation phases
- Memory usage monitoring
- Performance report generation
- Configurable profiling levels

Usage:
    from clickup_framework.commands.map_helpers.mermaid.profiling import (
        PerformanceProfiler, profile_method
    )

    # Use as context manager
    with PerformanceProfiler('diagram_generation') as profiler:
        # ... code to profile ...
        profiler.checkpoint('validation')
        # ... more code ...
        profiler.checkpoint('body_generation')

    # Get report
    report = profiler.get_report()

    # Use as decorator
    @profile_method('generate_diagram')
    def my_generate_function():
        pass
"""

import time
import os
import psutil
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from functools import wraps
from contextlib import contextmanager


@dataclass
class ProfileCheckpoint:
    """A single performance checkpoint in the profiling timeline."""
    name: str
    timestamp: float
    memory_mb: float
    elapsed_since_start: float
    elapsed_since_prev: float


@dataclass
class ProfileReport:
    """Complete performance profile report."""
    operation_name: str
    total_time: float
    total_memory_delta: float
    peak_memory: float
    checkpoints: List[ProfileCheckpoint] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary format."""
        return {
            'operation_name': self.operation_name,
            'total_time_seconds': round(self.total_time, 4),
            'total_memory_delta_mb': round(self.total_memory_delta, 2),
            'peak_memory_mb': round(self.peak_memory, 2),
            'checkpoints': [
                {
                    'name': cp.name,
                    'elapsed_since_start': round(cp.elapsed_since_start, 4),
                    'elapsed_since_prev': round(cp.elapsed_since_prev, 4),
                    'memory_mb': round(cp.memory_mb, 2)
                }
                for cp in self.checkpoints
            ],
            'metadata': self.metadata
        }

    def format_text(self) -> str:
        """Format report as human-readable text."""
        lines = [
            f"\n{'='*70}",
            f"Performance Profile: {self.operation_name}",
            f"{'='*70}",
            f"Total Time: {self.total_time:.4f}s",
            f"Memory Delta: {self.total_memory_delta:+.2f} MB",
            f"Peak Memory: {self.peak_memory:.2f} MB",
            f"\nCheckpoints:"
        ]

        if self.checkpoints:
            lines.append(f"{'Name':<30} {'Elapsed':<12} {'Delta':<12} {'Memory':<12}")
            lines.append("-" * 70)
            for cp in self.checkpoints:
                lines.append(
                    f"{cp.name:<30} "
                    f"{cp.elapsed_since_start:>10.4f}s "
                    f"{cp.elapsed_since_prev:>10.4f}s "
                    f"{cp.memory_mb:>10.2f}MB"
                )

        if self.metadata:
            lines.append(f"\nMetadata:")
            for key, value in self.metadata.items():
                lines.append(f"  {key}: {value}")

        lines.append(f"{'='*70}\n")
        return '\n'.join(lines)


class PerformanceProfiler:
    """Performance profiler for tracking execution time and memory usage.

    This class provides detailed profiling capabilities:
    - Records timestamps and memory at checkpoints
    - Calculates elapsed time between checkpoints
    - Tracks memory delta throughout execution
    - Generates formatted reports

    Can be used as context manager or manually started/stopped.

    Example:
        with PerformanceProfiler('my_operation') as profiler:
            do_work()
            profiler.checkpoint('work_done')
            do_more_work()
            profiler.checkpoint('more_work_done')

        print(profiler.get_report().format_text())
    """

    def __init__(self, operation_name: str, enabled: bool = True):
        """Initialize profiler.

        Args:
            operation_name: Name of operation being profiled
            enabled: Whether profiling is enabled (can disable for production)
        """
        self.operation_name = operation_name
        self.enabled = enabled
        self.start_time: Optional[float] = None
        self.start_memory: Optional[float] = None
        self.checkpoints: List[ProfileCheckpoint] = []
        self.metadata: Dict[str, Any] = {}
        self.process = psutil.Process(os.getpid()) if enabled else None

    def __enter__(self) -> 'PerformanceProfiler':
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False

    def start(self) -> None:
        """Start profiling."""
        if not self.enabled:
            return

        self.start_time = time.perf_counter()
        self.start_memory = self._get_memory_mb()
        self.checkpoint('start')

    def stop(self) -> None:
        """Stop profiling."""
        if not self.enabled or self.start_time is None:
            return

        self.checkpoint('end')

    def checkpoint(self, name: str) -> None:
        """Record a performance checkpoint.

        Args:
            name: Name/label for this checkpoint
        """
        if not self.enabled or self.start_time is None:
            return

        now = time.perf_counter()
        elapsed_since_start = now - self.start_time
        elapsed_since_prev = (
            elapsed_since_start if not self.checkpoints
            else elapsed_since_start - self.checkpoints[-1].elapsed_since_start
        )

        memory_mb = self._get_memory_mb()

        checkpoint = ProfileCheckpoint(
            name=name,
            timestamp=now,
            memory_mb=memory_mb,
            elapsed_since_start=elapsed_since_start,
            elapsed_since_prev=elapsed_since_prev
        )

        self.checkpoints.append(checkpoint)

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the profile report.

        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value

    def get_report(self) -> ProfileReport:
        """Generate performance report.

        Returns:
            ProfileReport with timing and memory statistics
        """
        if not self.enabled or not self.checkpoints:
            return ProfileReport(
                operation_name=self.operation_name,
                total_time=0.0,
                total_memory_delta=0.0,
                peak_memory=0.0,
                checkpoints=[],
                metadata=self.metadata
            )

        total_time = self.checkpoints[-1].elapsed_since_start
        start_mem = self.checkpoints[0].memory_mb
        end_mem = self.checkpoints[-1].memory_mb
        peak_mem = max(cp.memory_mb for cp in self.checkpoints)

        return ProfileReport(
            operation_name=self.operation_name,
            total_time=total_time,
            total_memory_delta=end_mem - start_mem,
            peak_memory=peak_mem,
            checkpoints=self.checkpoints,
            metadata=self.metadata
        )

    def _get_memory_mb(self) -> float:
        """Get current process memory usage in MB.

        Returns:
            Memory usage in megabytes
        """
        if not self.enabled or not self.process:
            return 0.0

        try:
            return self.process.memory_info().rss / 1024 / 1024
        except Exception:
            return 0.0


def profile_method(operation_name: Optional[str] = None) -> Callable:
    """Decorator to profile a method or function.

    Automatically profiles the decorated function and stores the report
    as an attribute on the instance (if method) or prints it (if function).

    Args:
        operation_name: Optional custom name (defaults to function name)

    Example:
        @profile_method('generate_diagram')
        def generate(self):
            # ... implementation ...
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get profiling enabled state from config if available
            enabled = True
            if args and hasattr(args[0], 'config'):
                # Try to get profiling config from instance
                config = getattr(args[0], 'config', None)
                if config and hasattr(config, 'profiling'):
                    enabled = config.profiling.enabled

            name = operation_name or func.__name__
            with PerformanceProfiler(name, enabled=enabled) as profiler:
                result = func(*args, **kwargs)

                # Store report on instance if it's a method
                if args and hasattr(args[0], '__dict__'):
                    args[0]._profile_report = profiler.get_report()

                return result

        return wrapper
    return decorator


@contextmanager
def profile_section(name: str, profiler: Optional[PerformanceProfiler] = None):
    """Context manager for profiling a code section.

    Args:
        name: Name for this section
        profiler: Optional existing profiler to add checkpoint to

    Example:
        with PerformanceProfiler('main') as profiler:
            with profile_section('init', profiler):
                initialize()

            with profile_section('process', profiler):
                process_data()
    """
    if profiler:
        start_checkpoint = f"{name}_start"
        end_checkpoint = f"{name}_end"
        profiler.checkpoint(start_checkpoint)

        try:
            yield profiler
        finally:
            profiler.checkpoint(end_checkpoint)
    else:
        # Standalone section profiler
        section_profiler = PerformanceProfiler(name)
        section_profiler.start()

        try:
            yield section_profiler
        finally:
            section_profiler.stop()


# Global profiler registry for collecting multiple profiles
_profiler_registry: Dict[str, ProfileReport] = {}


def register_profile(report: ProfileReport) -> None:
    """Register a profile report in the global registry.

    Args:
        report: Profile report to register
    """
    _profiler_registry[report.operation_name] = report


def get_registered_profiles() -> Dict[str, ProfileReport]:
    """Get all registered profile reports.

    Returns:
        Dictionary of operation name to profile report
    """
    return _profiler_registry.copy()


def clear_registry() -> None:
    """Clear all registered profiles."""
    _profiler_registry.clear()


def print_all_profiles() -> None:
    """Print all registered profiles to stdout."""
    if not _profiler_registry:
        print("No profiles registered.")
        return

    print(f"\n{'='*70}")
    print(f"All Registered Profiles ({len(_profiler_registry)} total)")
    print(f"{'='*70}")

    for report in _profiler_registry.values():
        print(report.format_text())
