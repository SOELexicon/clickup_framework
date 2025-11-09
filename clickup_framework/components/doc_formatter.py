"""
Rich Doc Formatter Module

Provides enhanced formatting for individual docs and pages with emojis, colors, and detailed information.
"""

from typing import Dict, Any, Optional
from clickup_framework.components.options import FormatOptions
from clickup_framework.utils.colors import (
    colorize, TextColor, TextStyle
)
from clickup_framework.utils.text import truncate


class RichDocFormatter:
    """
    Enhanced doc formatter with emojis, colors, and styling.

    Provides methods to format doc and page information with various levels of detail.
    """

    @staticmethod
    def format_doc(doc: Dict[str, Any], options: Optional[FormatOptions] = None) -> str:
        """
        Format a single doc with all requested information.

        Args:
            doc: Doc dictionary from ClickUp API
            options: Format options (uses defaults if not provided)

        Returns:
            Formatted doc string
        """
        if options is None:
            options = FormatOptions()

        parts = []

        # Add doc ID if requested
        if options.show_ids and doc.get('id'):
            id_str = f"[{doc['id']}]"
            if options.colorize_output:
                id_str = colorize(id_str, TextColor.BRIGHT_BLACK)
            parts.append(id_str)

        # Add doc emoji
        parts.append("📄")

        # Add doc name
        name = doc.get('name', 'Untitled Doc')
        if options.colorize_output:
            name = colorize(name, TextColor.CYAN, TextStyle.BOLD)
        parts.append(name)

        # Combine the main line
        main_line = ' '.join(parts)

        # Add additional sections if requested
        additional_lines = []

        # Show parent ID if present
        if options.show_relationships and doc.get('parent_id'):
            parent_str = f"🔗 Parent: {doc['parent_id']}"
            if options.colorize_output:
                parent_str = colorize(parent_str, TextColor.BRIGHT_CYAN)
            additional_lines.append(f"│  {parent_str}")

        # Dates
        if options.show_dates:
            date_parts = []
            if doc.get('date_created'):
                date_parts.append(f"Created: {doc['date_created']}")
            if doc.get('date_updated'):
                date_parts.append(f"Updated: {doc['date_updated']}")

            if date_parts:
                date_str = f"📅 {' | '.join(date_parts)}"
                if options.colorize_output:
                    date_str = colorize(date_str, TextColor.CYAN)
                additional_lines.append(f"│  {date_str}")

        # Creator info
        if doc.get('creator'):
            creator = doc['creator']
            creator_name = creator.get('username', creator.get('email', 'Unknown'))
            creator_str = f"👤 Creator: {creator_name}"
            if options.colorize_output:
                creator_str = colorize(creator_str, TextColor.BRIGHT_WHITE)
            additional_lines.append(f"│  {creator_str}")

        # Combine everything
        if additional_lines:
            # Add final line marker
            additional_lines.append("└─")
            return main_line + "\n" + "\n".join(additional_lines)
        else:
            return main_line

    @staticmethod
    def format_page(page: Dict[str, Any], options: Optional[FormatOptions] = None) -> str:
        """
        Format a single page with all requested information.

        Args:
            page: Page dictionary from ClickUp API
            options: Format options (uses defaults if not provided)

        Returns:
            Formatted page string
        """
        if options is None:
            options = FormatOptions()

        parts = []

        # Add page ID if requested
        if options.show_ids and page.get('id'):
            id_str = f"[{page['id']}]"
            if options.colorize_output:
                id_str = colorize(id_str, TextColor.BRIGHT_BLACK)
            parts.append(id_str)

        # Add page emoji
        parts.append("📃")

        # Add page name
        name = page.get('name', 'Untitled Page')
        if options.colorize_output:
            name = colorize(name, TextColor.WHITE)
        parts.append(name)

        # Combine the main line
        main_line = ' '.join(parts)

        # Add additional sections if requested
        additional_lines = []

        # Content preview
        if options.show_descriptions and page.get('content'):
            content = page['content']
            # Remove markdown headers and clean up
            content = content.replace('#', '').strip()
            if len(content) > options.description_length:
                content = truncate(content, options.description_length)
            if content:
                content_str = f"📝 Content:"
                if options.colorize_output:
                    content_str = colorize(content_str, TextColor.BRIGHT_WHITE, TextStyle.BOLD)
                additional_lines.append(f"│  {content_str}")
                additional_lines.append(f"│    {content}")

        # Dates
        if options.show_dates:
            date_parts = []
            if page.get('date_created'):
                date_parts.append(f"Created: {page['date_created']}")
            if page.get('date_updated'):
                date_parts.append(f"Updated: {page['date_updated']}")

            if date_parts:
                date_str = f"📅 {' | '.join(date_parts)}"
                if options.colorize_output:
                    date_str = colorize(date_str, TextColor.CYAN)
                additional_lines.append(f"│  {date_str}")

        # Creator info
        if page.get('creator'):
            creator = page['creator']
            creator_name = creator.get('username', creator.get('email', 'Unknown'))
            creator_str = f"👤 Creator: {creator_name}"
            if options.colorize_output:
                creator_str = colorize(creator_str, TextColor.BRIGHT_WHITE)
            additional_lines.append(f"│  {creator_str}")

        # Combine everything
        if additional_lines:
            # Add final line marker
            additional_lines.append("└─")
            return main_line + "\n" + "\n".join(additional_lines)
        else:
            return main_line

    @staticmethod
    def format_doc_minimal(doc: Dict[str, Any]) -> str:
        """
        Format a doc with minimal information (ID and name only).

        Args:
            doc: Doc dictionary

        Returns:
            Minimal formatted doc string
        """
        return RichDocFormatter.format_doc(doc, FormatOptions.minimal())

    @staticmethod
    def format_page_minimal(page: Dict[str, Any]) -> str:
        """
        Format a page with minimal information (ID and name only).

        Args:
            page: Page dictionary

        Returns:
            Minimal formatted page string
        """
        return RichDocFormatter.format_page(page, FormatOptions.minimal())

    @staticmethod
    def format_doc_summary(doc: Dict[str, Any]) -> str:
        """
        Format a doc with summary information.

        Args:
            doc: Doc dictionary

        Returns:
            Summary formatted doc string
        """
        return RichDocFormatter.format_doc(doc, FormatOptions.summary())

    @staticmethod
    def format_page_summary(page: Dict[str, Any]) -> str:
        """
        Format a page with summary information.

        Args:
            page: Page dictionary

        Returns:
            Summary formatted page string
        """
        return RichDocFormatter.format_page(page, FormatOptions.summary())

    @staticmethod
    def format_doc_detailed(doc: Dict[str, Any]) -> str:
        """
        Format a doc with detailed information.

        Args:
            doc: Doc dictionary

        Returns:
            Detailed formatted doc string
        """
        return RichDocFormatter.format_doc(doc, FormatOptions.detailed())

    @staticmethod
    def format_page_detailed(page: Dict[str, Any]) -> str:
        """
        Format a page with detailed information.

        Args:
            page: Page dictionary

        Returns:
            Detailed formatted page string
        """
        return RichDocFormatter.format_page(page, FormatOptions.detailed())
