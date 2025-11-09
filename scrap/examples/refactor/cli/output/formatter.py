"""
Output Formatting Module

This module provides interfaces and implementations for formatting command output.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import json
import yaml
from rich.console import Console
from rich.table import Table
from rich.text import Text


class OutputFormat(Enum):
    """Output format options."""
    TEXT = 'text'
    JSON = 'json'
    YAML = 'yaml'
    TABLE = 'table'


@dataclass
class OutputOptions:
    """Options for output formatting."""
    format: OutputFormat = OutputFormat.TEXT
    color: bool = True
    verbose: bool = False
    metadata: Dict[str, Any] = None


class OutputFormatter(ABC):
    """Base class for output formatters."""
    
    @abstractmethod
    def format(self, data: Any, options: OutputOptions) -> str:
        """
        Format data according to options.
        
        Args:
            data: Data to format
            options: Formatting options
            
        Returns:
            Formatted string
        """
        pass


class TextFormatter(OutputFormatter):
    """Formats output as plain text."""
    
    def format(self, data: Any, options: OutputOptions) -> str:
        if isinstance(data, (list, tuple)):
            return self._format_sequence(data, options)
        elif isinstance(data, dict):
            return self._format_dict(data, options)
        else:
            return str(data)
    
    def _format_sequence(self, data: List[Any], options: OutputOptions) -> str:
        return '\n'.join(str(item) for item in data)
    
    def _format_dict(self, data: Dict[str, Any], options: OutputOptions) -> str:
        lines = []
        for key, value in data.items():
            lines.append(f'{key}: {value}')
        return '\n'.join(lines)


class JsonFormatter(OutputFormatter):
    """Formats output as JSON."""
    
    def format(self, data: Any, options: OutputOptions) -> str:
        return json.dumps(
            data,
            indent=2 if options.verbose else None,
            sort_keys=True
        )


class YamlFormatter(OutputFormatter):
    """Formats output as YAML."""
    
    def format(self, data: Any, options: OutputOptions) -> str:
        return yaml.dump(
            data,
            default_flow_style=False,
            sort_keys=True
        )


class TableFormatter(OutputFormatter):
    """Formats output as a rich table."""
    
    def format(self, data: Any, options: OutputOptions) -> str:
        if not isinstance(data, (list, tuple)) or not data:
            return str(data)
        
        console = Console(color_system='auto' if options.color else None)
        table = self._create_table(data, options)
        
        with console.capture() as capture:
            console.print(table)
        
        return capture.get()
    
    def _create_table(self, data: List[Dict[str, Any]], options: OutputOptions) -> Table:
        table = Table(show_header=True)
        
        # Extract headers from first row
        if isinstance(data[0], dict):
            headers = list(data[0].keys())
            for header in headers:
                table.add_column(str(header))
            
            # Add rows
            for row in data:
                table.add_row(*[str(row.get(h, '')) for h in headers])
        else:
            table.add_column('Value')
            for item in data:
                table.add_row(str(item))
        
        return table


class OutputManager:
    """Manages output formatting based on format selection."""
    
    def __init__(self):
        self._formatters = {
            OutputFormat.TEXT: TextFormatter(),
            OutputFormat.JSON: JsonFormatter(),
            OutputFormat.YAML: YamlFormatter(),
            OutputFormat.TABLE: TableFormatter()
        }
    
    def format(self, data: Any, options: Optional[OutputOptions] = None) -> str:
        """
        Format data using the specified options.
        
        Args:
            data: Data to format
            options: Formatting options (defaults to TEXT format)
            
        Returns:
            Formatted string
        """
        if options is None:
            options = OutputOptions()
        
        formatter = self._formatters.get(options.format)
        if not formatter:
            raise ValueError(f'Unsupported output format: {options.format}')
        
        return formatter.format(data, options) 