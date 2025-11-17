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

    def to_json_format(self, content: str, image_metadata: Optional[Dict[str, Dict[str, Any]]] = None, attachment_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Convert markdown to ClickUp JSON format.

        For comments, ClickUp requires rich text JSON structure for formatting.
        For task descriptions, markdown_description field works with markdown.

        Args:
            content: Markdown content
            image_metadata: Dict mapping image URLs to their attachment metadata for inline embedding
            attachment_ids: List of attachment IDs to include in the comment (deprecated - use image_metadata)

        Returns:
            Dictionary suitable for ClickUp API
        """
        formatted_content = self.parse(content)

        if self.context == ParserContext.COMMENT:
            # ClickUp comments need rich text JSON structure for formatting
            if self.contains_markdown(formatted_content) or image_metadata:
                result = {
                    "comment": self._markdown_to_rich_text(formatted_content, image_metadata)
                }
                # Add FULL attachment objects (not just IDs) from image_metadata
                if image_metadata:
                    # Extract full attachment objects from image_metadata values
                    result["attachment"] = list(image_metadata.values())
                return result
            else:
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

    def _markdown_to_rich_text(self, content: str, image_metadata: Optional[Dict[str, Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """
        Convert markdown to ClickUp rich text JSON structure.

        ClickUp comments use a structured format:
        {
          "comment": [
            {"text": "content", "attributes": {"bold": true, ...}},
            ...
          ]
        }

        Args:
            content: Markdown formatted content
            image_metadata: Dict mapping image URLs to their attachment metadata for inline embedding

        Returns:
            List of text segments with formatting attributes
        """
        import uuid

        result = []
        lines = content.split('\n')
        i = 0

        while i < len(lines):
            line = lines[i]

            # Handle code blocks
            if line.strip().startswith('```'):
                code_lang = line.strip()[3:].strip() or 'plain'
                code_lines = []
                i += 1
                while i < len(lines) and not lines[i].strip().startswith('```'):
                    code_lines.append(lines[i])
                    i += 1

                code_text = '\n'.join(code_lines)
                if code_text:
                    # Add terminating newline for proper ClickUp rendering
                    if not code_text.endswith('\n'):
                        code_text += '\n'

                    result.append({
                        "text": code_text,
                        "attributes": {
                            "code-block": {"code-block": code_lang}
                        }
                    })
                i += 1
                continue

            # Handle headers (convert to bold text with newlines)
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if header_match:
                header_text = header_match.group(2)
                # Add newline before header if not first line
                if result:
                    result.append({"text": "\n"})

                result.append({
                    "text": header_text,
                    "attributes": {"bold": True}
                })
                result.append({
                    "text": "\n",
                    "attributes": {"block-id": f"block-{uuid.uuid4()}"}
                })
                i += 1
                continue

            # Handle lists
            bullet_match = re.match(r'^(\s*)[-*+]\s+(.+)$', line)
            ordered_match = re.match(r'^(\s*)(\d+)\.\s+(.+)$', line)

            if bullet_match:
                text = bullet_match.group(2)
                segments = self._parse_inline_formatting(text, image_metadata)
                for seg in segments:
                    attrs = seg.get("attributes", {})
                    attrs["list"] = "bullet"  # Fixed: use string not nested object
                    seg["attributes"] = attrs
                    result.append(seg)
                result.append({
                    "text": "\n",
                    "attributes": {"block-id": f"block-{uuid.uuid4()}"}
                })
                i += 1
                continue

            if ordered_match:
                text = ordered_match.group(3)
                segments = self._parse_inline_formatting(text, image_metadata)
                for seg in segments:
                    attrs = seg.get("attributes", {})
                    attrs["list"] = "ordered"  # Fixed: use string not nested object
                    seg["attributes"] = attrs
                    result.append(seg)
                result.append({
                    "text": "\n",
                    "attributes": {"block-id": f"block-{uuid.uuid4()}"}
                })
                i += 1
                continue

            # Handle regular text with inline formatting
            if line.strip():
                segments = self._parse_inline_formatting(line, image_metadata)
                result.extend(segments)

            # Add newline if not last line
            if i < len(lines) - 1:
                result.append({
                    "text": "\n",
                    "attributes": {"block-id": f"block-{uuid.uuid4()}"}
                })

            i += 1

        return result if result else [{"text": content}]

    def _parse_inline_formatting(self, text: str, image_metadata: Optional[Dict[str, Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """
        Parse inline markdown formatting (bold, italic, code, links, images).

        Args:
            text: Text with inline markdown
            image_metadata: Dict mapping image URLs to their attachment metadata for inline embedding

        Returns:
            List of text segments with attributes
        """
        result = []
        remaining = text

        # Pattern to match markdown inline elements
        # Order matters: images, bold+italic, bold, italic, code, links
        # Image pattern: ![alt](url)
        pattern = r'(!\[([^\]]*)\]\(([^)]+)\)|\*\*\*([^*]+)\*\*\*|\*\*([^*]+)\*\*|\*([^*]+)\*|`([^`]+)`|\[([^\]]+)\]\(([^)]+)\))'

        last_end = 0
        for match in re.finditer(pattern, text):
            # Add text before match
            if match.start() > last_end:
                plain_text = text[last_end:match.start()]
                if plain_text:
                    result.append({"text": plain_text, "attributes": {}})

            # Determine type and add formatted segment
            if match.group(1) and match.group(1).startswith('!'):  # ![alt](url) - image
                alt_text = match.group(2)
                url = match.group(3)

                # Check if we have metadata for this image
                if image_metadata and url in image_metadata:
                    # Create inline image block
                    img_block = self._create_inline_image_block(url, alt_text, image_metadata[url])
                    result.append(img_block)
                else:
                    # Fall back to link format if no metadata
                    result.append({
                        "text": alt_text or url,
                        "attributes": {"link": url}
                    })
            elif match.group(4):  # ***bold+italic***
                result.append({
                    "text": match.group(4),
                    "attributes": {"bold": True, "italic": True}
                })
            elif match.group(5):  # **bold**
                result.append({
                    "text": match.group(5),
                    "attributes": {"bold": True}
                })
            elif match.group(6):  # *italic*
                result.append({
                    "text": match.group(6),
                    "attributes": {"italic": True}
                })
            elif match.group(7):  # `code`
                result.append({
                    "text": match.group(7),
                    "attributes": {"code": True}
                })
            elif match.group(8) and match.group(9):  # [text](url)
                result.append({
                    "text": match.group(8),
                    "attributes": {"link": match.group(9)}
                })

            last_end = match.end()

        # Add remaining text
        if last_end < len(text):
            remaining_text = text[last_end:]
            if remaining_text:
                result.append({"text": remaining_text, "attributes": {}})

        return result if result else [{"text": text, "attributes": {}}]

    def _create_inline_image_block(self, url: str, alt_text: str, attachment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an inline image block for ClickUp rich text format.

        Args:
            url: Image URL
            alt_text: Alt text for the image
            attachment_data: Full attachment metadata from ClickUp API

        Returns:
            Inline image block dict
        """
        import json

        # Extract attachment info
        attachment_id = attachment_data.get('id', '')
        filename = attachment_data.get('title') or attachment_data.get('name', alt_text)
        file_ext = attachment_data.get('extension', '').replace('image/', '')
        thumbnail_small = attachment_data.get('thumbnail_small', url)
        thumbnail_medium = attachment_data.get('thumbnail_medium', url)
        thumbnail_large = attachment_data.get('thumbnail_large', url)

        # Get image dimensions if available
        # Default to 300px width (ClickUp's optimal size) to ensure preview rendering
        width = str(attachment_data.get('width', '300'))
        natural_width = str(attachment_data.get('size', {}).get('width', '797'))
        natural_height = str(attachment_data.get('size', {}).get('height', '1289'))

        # Build data-attachment JSON string
        data_attachment = {
            "id": attachment_id,
            "version": str(attachment_data.get('version', '0')),
            "date": attachment_data.get('date', 0),
            "name": filename,
            "title": filename,
            "extension": file_ext,
            "source": 1,
            "thumbnail_small": thumbnail_small,
            "thumbnail_medium": thumbnail_medium,
            "thumbnail_large": thumbnail_large,
            "url": url,
            "url_w_query": f"{url}?view=open",
            "url_w_host": url
        }

        # Create the inline image block
        # NOTE: GUI uses full URL for all thumbnails in image block, not the _small/_medium variants
        image_block = {
            "type": "image",
            "text": filename,
            "image": {
                "id": attachment_id,
                "name": filename,
                "title": filename,
                "type": file_ext,
                "extension": f"image/{file_ext}",
                "thumbnail_large": url,
                "thumbnail_medium": url,
                "thumbnail_small": url,
                "url": url,
                "uploaded": True
            },
            "attributes": {
                "width": width,
                "data-id": attachment_id,
                "data-attachment": json.dumps(data_attachment),
                "data-natural-width": natural_width,
                "data-natural-height": natural_height
            }
        }

        return image_block


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
