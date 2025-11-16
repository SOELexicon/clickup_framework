"""
Base Parser Infrastructure

Provides reusable base classes for parsing markdown, mermaid diagrams,
and handling image embedding across comments, docs, pages, and task descriptions.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional


class ParserContext(Enum):
    """Context in which parsing is happening."""
    COMMENT = "comment"
    DOC = "doc"
    PAGE = "page"
    TASK_DESCRIPTION = "task_description"


class BaseParser(ABC):
    """
    Base class for all content parsers.

    Provides common functionality for parsing markdown, mermaid diagrams,
    and handling image embedding in a context-aware manner.
    """

    def __init__(self, context: ParserContext = ParserContext.COMMENT):
        """
        Initialize the parser.

        Args:
            context: The context in which parsing is happening
        """
        self.context = context

    @abstractmethod
    def parse(self, content: str, **options) -> Any:
        """
        Parse the content.

        Args:
            content: Raw content to parse
            **options: Additional parsing options

        Returns:
            Parsed content in appropriate format
        """
        pass

    def can_handle(self, content: str) -> bool:
        """
        Check if this parser can handle the given content.

        Args:
            content: Content to check

        Returns:
            True if parser can handle this content
        """
        return True

    def validate(self, content: str) -> bool:
        """
        Validate content before parsing.

        Args:
            content: Content to validate

        Returns:
            True if content is valid for this parser
        """
        return content is not None and isinstance(content, str)
