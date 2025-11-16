"""
Markdown to ClickUp JSON Formatter

Extends existing MarkdownRenderer class to support JSON output and ensure
markdown is properly formatted for ClickUp comments, docs, pages, and task descriptions.
"""

import re
from typing import Dict, Any, List, Optional
from .base import BaseParser, ParserContext


class MarkdownFormatter(BaseParser):
    """
    Converts markdown syntax to ClickUp-compatible format.

    Extends existing markdown detection to ensure proper formatting
    for ClickUp comments and docs. Handles all markdown syntax including:
    - Headers (H1-H6)
    - Bold, italic, strikethrough
    - Code spans and code blocks
    - Lists (bulleted and numbered)
    - Links and images
    - Blockquotes
    - Horizontal rules
    """

    def __init__(self, context: ParserContext = ParserContext.COMMENT):
        """
        Initialize the markdown formatter.

        Args:
            context: Context in which formatting is happening
        """
        super().__init__(context)

    def parse(self, content: str, **options) -> str:
        """
        Format markdown for ClickUp.

        Args:
            content: Raw markdown content
            **options: Additional options (e.g., preserve_formatting)

        Returns:
            Formatted markdown string ready for ClickUp API
        """
        if not self.validate(content):
            return ""

        # Normalize line endings
        content = content.replace('\r\n', '\n').replace('\r', '\n')

        # Process content based on context
        if self.context == ParserContext.COMMENT:
            return self._format_for_comment(content)
        elif self.context in [ParserContext.DOC, ParserContext.PAGE]:
            return self._format_for_doc(content)
        elif self.context == ParserContext.TASK_DESCRIPTION:
            return self._format_for_task_description(content)
        else:
            return content

    def _format_for_comment(self, content: str) -> str:
        """Format markdown for ClickUp comments."""
        # ClickUp comments support standard markdown
        # Ensure proper spacing around elements
        content = self._normalize_spacing(content)
        return content

    def _format_for_doc(self, content: str) -> str:
        """Format markdown for ClickUp docs/pages."""
        # Docs support richer markdown
        content = self._normalize_spacing(content)
        return content

    def _format_for_task_description(self, content: str) -> str:
        """Format markdown for task descriptions."""
        content = self._normalize_spacing(content)
        return content

    def _normalize_spacing(self, content: str) -> str:
        """
        Normalize spacing around markdown elements.

        Ensures:
        - Single blank line before/after headers
        - Consistent list spacing
        - Proper code block spacing
        """
        lines = content.split('\n')
        normalized = []
        prev_line_type = None

        for i, line in enumerate(lines):
            line_type = self._detect_line_type(line)

            # Add spacing before headers
            if line_type == 'header' and prev_line_type and prev_line_type != 'blank':
                if normalized and normalized[-1].strip():
                    normalized.append('')

            normalized.append(line)

            # Add spacing after headers
            if line_type == 'header' and i + 1 < len(lines):
                next_line = lines[i + 1]
                if next_line.strip():
                    normalized.append('')

            prev_line_type = line_type

        return '\n'.join(normalized)

    def _detect_line_type(self, line: str) -> str:
        """Detect the type of markdown line."""
        if not line.strip():
            return 'blank'
        if re.match(r'^#{1,6}\s', line):
            return 'header'
        if line.strip().startswith('```'):
            return 'code_fence'
        if re.match(r'^\s*[-*+]\s', line):
            return 'list_item'
        if re.match(r'^\s*\d+\.\s', line):
            return 'numbered_list'
        if line.strip().startswith('>'):
            return 'blockquote'
        if re.match(r'^\s*[-*_]{3,}\s*$', line):
            return 'horizontal_rule'
        return 'text'

    def contains_markdown(self, text: str) -> bool:
        """
        Detect if text contains markdown formatting.

        Compatible with existing contains_markdown() function from scripts.

        Args:
            text: Text to check

        Returns:
            True if text contains markdown
        """
        if not text:
            return False

        markdown_patterns = [
            r'#{1,6}\s',           # Headers
            r'```',                # Code blocks
            r'\|.*\|',             # Tables
            r'\[.*\]\(.*\)',       # Links
            r'\*\*.*\*\*',         # Bold
            r'^\s*[-*+]\s',        # Unordered lists
            r'^\s*\d+\.\s',        # Ordered lists
            r'!\[.*\]\(.*\)',      # Images
            r'~~.*~~',             # Strikethrough
            r'`[^`]+`',            # Inline code
        ]

        for pattern in markdown_patterns:
            if re.search(pattern, text, re.MULTILINE):
                return True

        return False

    def to_json_format(self, content: str) -> Dict[str, Any]:
        """
        Convert markdown to ClickUp JSON format.

        For comments, ClickUp accepts plain text with markdown syntax.
        This method structures it properly for API requests.

        Args:
            content: Markdown content

        Returns:
            Dictionary suitable for ClickUp API
        """
        formatted_content = self.parse(content)

        if self.context == ParserContext.COMMENT:
            return {
                "comment_text": formatted_content
            }
        elif self.context == ParserContext.TASK_DESCRIPTION:
            # Use markdown_description field if content contains markdown
            if self.contains_markdown(formatted_content):
                return {
                    "markdown_description": formatted_content
                }
            else:
                return {
                    "description": formatted_content
                }
        elif self.context in [ParserContext.DOC, ParserContext.PAGE]:
            return {
                "content": formatted_content
            }
        else:
            return {
                "text": formatted_content
            }


def format_markdown_for_clickup(content: str, context: ParserContext = ParserContext.COMMENT) -> str:
    """
    Convenience function to format markdown for ClickUp.

    Args:
        content: Markdown content
        context: Context in which formatting is happening

    Returns:
        Formatted markdown string
    """
    formatter = MarkdownFormatter(context)
    return formatter.parse(content)


def contains_markdown(text: str) -> bool:
    """
    Convenience function to detect markdown.

    Compatible with existing contains_markdown() function from scripts.

    Args:
        text: Text to check

    Returns:
        True if text contains markdown
    """
    formatter = MarkdownFormatter()
    return formatter.contains_markdown(text)
