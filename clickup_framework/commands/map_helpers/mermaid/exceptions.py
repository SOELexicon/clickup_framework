"""Custom exceptions for Mermaid diagram generation.

This module provides specific exception classes for different error scenarios
with context-rich error messages and actionable suggestions for users.
"""

from typing import Optional, List, Dict, Any


class MermaidGenerationError(Exception):
    """Base exception for all Mermaid diagram generation errors.

    All custom exceptions inherit from this base class, allowing callers
    to catch all generation-related errors with a single except clause.
    """

    def __init__(self, message: str, suggestions: Optional[List[str]] = None,
                 context: Optional[Dict[str, Any]] = None):
        """Initialize error with message, suggestions, and context.

        Args:
            message: Human-readable error description
            suggestions: Optional list of actionable suggestions to fix the error
            context: Optional dictionary with additional context (file paths, values, etc.)
        """
        super().__init__(message)
        self.suggestions = suggestions or []
        self.context = context or {}

    def format_error(self) -> str:
        """Format error message with suggestions and context.

        Returns:
            Formatted multi-line error message string
        """
        lines = [f"ERROR: {str(self)}"]

        if self.context:
            lines.append("\nContext:")
            for key, value in self.context.items():
                lines.append(f"  {key}: {value}")

        if self.suggestions:
            lines.append("\nSuggestions:")
            for suggestion in self.suggestions:
                lines.append(f"  • {suggestion}")

        return '\n'.join(lines)


class DataValidationError(MermaidGenerationError):
    """Raised when input data fails validation checks.

    Examples:
        - Missing required fields in stats dictionary
        - Empty data structures when non-empty expected
        - Incorrect data types or formats
    """

    @classmethod
    def missing_required_field(cls, field_name: str, generator_type: str,
                              stats_keys: Optional[List[str]] = None) -> 'DataValidationError':
        """Create error for missing required field in stats data.

        Args:
            field_name: Name of the missing required field
            generator_type: Type of generator (e.g., 'flowchart', 'class_diagram')
            stats_keys: Optional list of keys actually present in stats

        Returns:
            Configured DataValidationError instance
        """
        message = f"Required field '{field_name}' not found in stats data for {generator_type} generator"

        suggestions = [
            f"Ensure ctags scan completed successfully and found symbols",
            f"Check that the codebase contains files matching the language filter",
            f"Verify tags file (.tags.json) exists and contains '{field_name}' data",
            f"Try running: cum map --help to see required options",
        ]

        context = {
            'generator_type': generator_type,
            'required_field': field_name,
        }

        if stats_keys:
            context['available_fields'] = ', '.join(sorted(stats_keys))
            suggestions.insert(0, f"Found fields: {', '.join(sorted(stats_keys))}")

        return cls(message, suggestions, context)

    @classmethod
    def empty_data_structure(cls, field_name: str, generator_type: str,
                            data_size: int = 0) -> 'DataValidationError':
        """Create error for empty data structure.

        Args:
            field_name: Name of the field containing empty data
            generator_type: Type of generator
            data_size: Size of the empty structure (0)

        Returns:
            Configured DataValidationError instance
        """
        message = f"Field '{field_name}' exists but is empty for {generator_type} generator"

        suggestions = [
            "Verify that the codebase directory contains supported source files",
            "Check that ctags successfully parsed the source files",
            "Try increasing tree_depth or max_collection_depth in configuration",
            "Ensure file extensions match supported languages",
        ]

        context = {
            'generator_type': generator_type,
            'field_name': field_name,
            'data_size': data_size,
        }

        return cls(message, suggestions, context)


class ConfigurationError(MermaidGenerationError):
    """Raised when configuration is invalid or incompatible.

    Examples:
        - Invalid configuration values
        - Conflicting configuration options
        - Missing required configuration
    """

    @classmethod
    def invalid_value(cls, config_name: str, value: Any, valid_values: Optional[List[Any]] = None,
                     value_type: Optional[str] = None) -> 'ConfigurationError':
        """Create error for invalid configuration value.

        Args:
            config_name: Name of the configuration parameter
            value: The invalid value provided
            valid_values: Optional list of valid values
            value_type: Optional expected value type description

        Returns:
            Configured ConfigurationError instance
        """
        message = f"Invalid value '{value}' for configuration parameter '{config_name}'"

        suggestions = []
        if valid_values:
            valid_str = ', '.join(str(v) for v in valid_values)
            suggestions.append(f"Valid values: {valid_str}")
        if value_type:
            suggestions.append(f"Expected type: {value_type}")

        suggestions.extend([
            "Check configuration documentation for allowed values",
            "Verify configuration is loaded correctly from environment or config file",
        ])

        context = {
            'config_name': config_name,
            'provided_value': value,
        }

        if valid_values:
            context['valid_values'] = valid_values

        return cls(message, suggestions, context)

    @classmethod
    def out_of_range(cls, config_name: str, value: Any, min_value: Optional[Any] = None,
                    max_value: Optional[Any] = None) -> 'ConfigurationError':
        """Create error for out-of-range configuration value.

        Args:
            config_name: Name of the configuration parameter
            value: The out-of-range value
            min_value: Optional minimum allowed value
            max_value: Optional maximum allowed value

        Returns:
            Configured ConfigurationError instance
        """
        range_desc = []
        if min_value is not None:
            range_desc.append(f"min={min_value}")
        if max_value is not None:
            range_desc.append(f"max={max_value}")

        range_str = f" ({', '.join(range_desc)})" if range_desc else ""
        message = f"Value '{value}' for '{config_name}' is out of valid range{range_str}"

        suggestions = [
            f"Provide a value within the valid range{range_str}",
            "Check configuration documentation for value constraints",
        ]

        context = {
            'config_name': config_name,
            'provided_value': value,
        }

        if min_value is not None:
            context['min_value'] = min_value
        if max_value is not None:
            context['max_value'] = max_value

        return cls(message, suggestions, context)


class FileOperationError(MermaidGenerationError):
    """Raised when file operations fail.

    Examples:
        - Cannot write output file
        - Permission denied on directory
        - Disk space issues
    """

    @classmethod
    def cannot_write(cls, file_path: str, reason: Optional[str] = None) -> 'FileOperationError':
        """Create error for file write failure.

        Args:
            file_path: Path to file that could not be written
            reason: Optional specific reason for failure

        Returns:
            Configured FileOperationError instance
        """
        reason_str = f": {reason}" if reason else ""
        message = f"Cannot write output file '{file_path}'{reason_str}"

        suggestions = [
            "Check that the output directory exists and is writable",
            "Verify you have write permissions for the target location",
            "Ensure sufficient disk space is available",
            "Try specifying a different output path with --output option",
        ]

        context = {
            'file_path': file_path,
        }

        if reason:
            context['reason'] = reason

        return cls(message, suggestions, context)

    @classmethod
    def cannot_read(cls, file_path: str, reason: Optional[str] = None) -> 'FileOperationError':
        """Create error for file read failure.

        Args:
            file_path: Path to file that could not be read
            reason: Optional specific reason for failure

        Returns:
            Configured FileOperationError instance
        """
        reason_str = f": {reason}" if reason else ""
        message = f"Cannot read input file '{file_path}'{reason_str}"

        suggestions = [
            "Verify the file exists at the specified path",
            "Check that you have read permissions for the file",
            "Ensure the file is not locked by another process",
        ]

        context = {
            'file_path': file_path,
        }

        if reason:
            context['reason'] = reason

        return cls(message, suggestions, context)


class DiagramSyntaxError(MermaidGenerationError):
    """Raised when generated diagram has invalid Mermaid syntax.

    Examples:
        - Invalid node identifiers
        - Malformed edge syntax
        - Unescaped special characters
    """

    @classmethod
    def validation_failed(cls, errors: List[str], diagram_type: str,
                         line_count: int) -> 'DiagramSyntaxError':
        """Create error for diagram syntax validation failure.

        Args:
            errors: List of specific validation error messages
            diagram_type: Type of diagram (e.g., 'flowchart', 'sequence')
            line_count: Number of lines in the generated diagram

        Returns:
            Configured DiagramSyntaxError instance
        """
        error_summary = f"{len(errors)} validation error(s)"
        message = f"Generated {diagram_type} diagram failed validation: {error_summary}"

        suggestions = [
            "Review the validation errors below for specific issues",
            "Check for special characters in symbol names that need escaping",
            "Try reducing diagram complexity with configuration limits",
            "Report this issue if it appears to be a generator bug",
        ]

        context = {
            'diagram_type': diagram_type,
            'line_count': line_count,
            'error_count': len(errors),
            'errors': errors[:10],  # Limit to first 10 errors for readability
        }

        if len(errors) > 10:
            context['additional_errors'] = f"{len(errors) - 10} more errors..."

        return cls(message, suggestions, context)


class ResourceLimitError(MermaidGenerationError):
    """Raised when resource limits are exceeded.

    Examples:
        - Diagram too large (too many nodes/edges)
        - Memory consumption too high
        - Generation timeout exceeded
    """

    @classmethod
    def diagram_too_large(cls, node_count: int, max_nodes: int,
                        diagram_type: str) -> 'ResourceLimitError':
        """Create error for diagram exceeding size limits.

        Args:
            node_count: Actual number of nodes in diagram
            max_nodes: Maximum allowed nodes
            diagram_type: Type of diagram

        Returns:
            Configured ResourceLimitError instance
        """
        message = f"Diagram would contain {node_count} nodes, exceeding limit of {max_nodes}"

        suggestions = [
            f"Reduce max_nodes in {diagram_type} configuration (currently {max_nodes})",
            "Increase max_nodes limit if you need larger diagrams",
            "Try filtering to specific files or directories",
            "Consider generating multiple smaller diagrams instead of one large one",
        ]

        context = {
            'diagram_type': diagram_type,
            'node_count': node_count,
            'max_nodes': max_nodes,
            'overflow': node_count - max_nodes,
        }

        return cls(message, suggestions, context)

    @classmethod
    def memory_exceeded(cls, current_mb: float, peak_mb: float,
                       threshold_mb: float) -> 'ResourceLimitError':
        """Create error for memory limit exceeded.

        Args:
            current_mb: Current memory usage in MB
            peak_mb: Peak memory usage in MB
            threshold_mb: Memory threshold that was exceeded

        Returns:
            Configured ResourceLimitError instance
        """
        message = f"Memory usage ({current_mb:.1f}MB) exceeded threshold ({threshold_mb:.1f}MB)"

        suggestions = [
            "Reduce max_nodes or max_depth in configuration",
            "Process the codebase in smaller chunks",
            "Increase available system memory",
            "Use profiling to identify memory-intensive operations",
        ]

        context = {
            'current_memory_mb': current_mb,
            'peak_memory_mb': peak_mb,
            'threshold_mb': threshold_mb,
            'overflow_mb': current_mb - threshold_mb,
        }

        return cls(message, suggestions, context)
