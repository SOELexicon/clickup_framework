"""
Node label formatting utilities.

This module provides configurable label formatting for nodes in Mermaid diagrams.
Different formats can be used based on diagram size and detail requirements:
- minimal: Just function name (for large diagrams)
- simple: Function name + line numbers
- detailed: Function name + class + file + line numbers
"""
from typing import Dict, Any
from pathlib import Path
from ..exceptions import ConfigurationError


class LabelFormatter:
    """
    Format node labels for different contexts and diagram sizes.

    Use minimal labels for large diagrams to reduce text size,
    and detailed labels for small diagrams where space allows.
    """

    # Predefined format templates
    FORMATS = {
        'minimal': '{func_name}()',
        'simple': '{func_name}()\\nL{line_range}',
        'medium': '{func_name}()\\n{file_name}',
        'detailed': '{func_name}()\\n{class_name}\\n{file_name}',
        'verbose': '{func_name}()\\n{class_name}\\n{file_name}\\nL{line_range}'
    }

    def __init__(self, default_format: str = 'minimal'):
        """
        Initialize label formatter.

        Args:
            default_format: Default format to use ('minimal', 'simple', 'medium', 'detailed', 'verbose')
        """
        if default_format not in self.FORMATS:
            raise ConfigurationError.invalid_value(
                config_name='default_format',
                value=default_format,
                valid_values=list(self.FORMATS.keys())
            )
        self.default_format = default_format

    def format_function_label(
        self,
        func_name: str,
        symbol: Dict[str, Any],
        format_type: str = None
    ) -> str:
        """
        Format function node label.

        Args:
            func_name: Function name (may include qualified name)
            symbol: Symbol metadata dictionary
            format_type: Override format type (if None, uses default_format)

        Returns:
            Formatted label string
        """
        format_type = format_type or self.default_format

        # Extract components
        display_func = func_name.split('.')[-1]  # Get last part if qualified name
        class_name = symbol.get('class', '')
        file_name = Path(symbol.get('path', '')).name if symbol.get('path') else ''
        line_start = symbol.get('line', 0)
        line_end = symbol.get('end', line_start)
        line_range = f'{line_start}-{line_end}' if line_end > line_start else str(line_start)

        # Remove 'module_' prefix from class names
        if class_name.startswith('module_'):
            class_name = ''

        # Build label based on format
        if format_type == 'minimal':
            return f'{display_func}()'

        elif format_type == 'simple':
            return f'{display_func}()\\nL{line_range}'

        elif format_type == 'medium':
            if file_name:
                return f'{display_func}()\\n{file_name}'
            return f'{display_func}()\\nL{line_range}'

        elif format_type == 'detailed':
            parts = [f'{display_func}()']
            if class_name:
                parts.append(class_name)
            if file_name:
                parts.append(file_name)
            return '\\n'.join(parts)

        elif format_type == 'verbose':
            parts = [f'{display_func}()']
            if class_name:
                parts.append(class_name)
            if file_name:
                parts.append(file_name)
            parts.append(f'L{line_range}')
            return '\\n'.join(parts)

        else:
            # Fallback to minimal if unknown format
            return f'{display_func}()'

    def format_class_label(
        self,
        class_name: str,
        methods_count: int = 0,
        format_type: str = 'simple'
    ) -> str:
        """
        Format class node label.

        Args:
            class_name: Class name
            methods_count: Number of methods in class
            format_type: Format type

        Returns:
            Formatted label string
        """
        # Remove 'module_' prefix if present
        display_name = class_name.replace('module_', '')

        if format_type == 'minimal':
            return display_name
        elif format_type in ('simple', 'medium'):
            return f'{display_name}\\n{methods_count} methods' if methods_count else display_name
        else:
            return f'{display_name}\\n{methods_count} methods' if methods_count else display_name

    def format_file_label(
        self,
        file_path: str,
        format_type: str = 'simple'
    ) -> str:
        """
        Format file node label.

        Args:
            file_path: File path
            format_type: Format type

        Returns:
            Formatted label string
        """
        file_name = Path(file_path).name

        if format_type == 'minimal':
            # Just filename without extension
            return Path(file_path).stem
        else:
            # Full filename with extension
            return file_name

    def format_directory_label(
        self,
        dir_name: str,
        format_type: str = 'simple'
    ) -> str:
        """
        Format directory node label.

        Args:
            dir_name: Directory name
            format_type: Format type

        Returns:
            Formatted label string
        """
        # Directories are always simple - just the name
        return f'DIR: {dir_name}'

    def escape_mermaid_text(self, text: str) -> str:
        """
        Escape special characters for Mermaid.

        Args:
            text: Text to escape

        Returns:
            Escaped text safe for Mermaid diagrams
        """
        # Escape special characters that break Mermaid syntax
        replacements = {
            '"': '&quot;',
            '[': '&#91;',
            ']': '&#93;',
            '{': '&#123;',
            '}': '&#125;',
            '<': '&lt;',
            '>': '&gt;',
            '&': '&amp;'
        }

        result = text
        for char, escaped in replacements.items():
            result = result.replace(char, escaped)

        return result

    def get_recommended_format(
        self,
        node_count: int,
        max_nodes: int = 150
    ) -> str:
        """
        Get recommended label format based on diagram size.

        Args:
            node_count: Number of nodes in diagram
            max_nodes: Maximum nodes threshold

        Returns:
            Recommended format name
        """
        if node_count > max_nodes * 0.8:  # 80% of max
            return 'minimal'
        elif node_count > max_nodes * 0.5:  # 50% of max
            return 'simple'
        elif node_count > max_nodes * 0.3:  # 30% of max
            return 'medium'
        else:
            return 'detailed'
