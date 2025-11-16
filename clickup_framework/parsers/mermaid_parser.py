"""
Mermaid Diagram Parser

Detects and processes mermaid code blocks in markdown content.
Converts mermaid diagrams to images and embeds them above code blocks.
Supports change detection via content hashing and #ignore comments.
"""

import os
import re
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from .base import BaseParser, ParserContext
from .image_embedding import ImageCache
from ..utils.mermaid_cli import MermaidCLI


class MermaidBlock:
    """Represents a mermaid code block."""

    def __init__(self, content: str, start_line: int, end_line: int):
        """
        Initialize a mermaid block.

        Args:
            content: Mermaid diagram code
            start_line: Starting line number
            end_line: Ending line number
        """
        self.content = content
        self.start_line = start_line
        self.end_line = end_line
        self.hash = self._compute_hash()
        self.ignore = self._check_ignore()

    def _compute_hash(self) -> str:
        """Compute SHA256 hash of the mermaid content."""
        return hashlib.sha256(self.content.encode('utf-8')).hexdigest()

    def _check_ignore(self) -> bool:
        """Check if block has #ignore comment."""
        # Check first line for #ignore or %% ignore comments
        lines = self.content.strip().split('\n')
        if lines:
            first_line = lines[0].strip()
            return '#ignore' in first_line.lower() or '%% ignore' in first_line.lower()
        return False


class MermaidParser(BaseParser):
    """
    Parser for mermaid diagram code blocks.

    Detects mermaid blocks in markdown, generates images, and embeds them.
    Supports change detection and selective processing.
    """

    def __init__(self, context: ParserContext = ParserContext.COMMENT, cache_dir: Optional[str] = None):
        """
        Initialize the mermaid parser.

        Args:
            context: Context in which parsing is happening
            cache_dir: Directory for image cache (default: ~/.clickup_framework/image_cache)
        """
        super().__init__(context)
        self.blocks: List[MermaidBlock] = []
        self.cache = ImageCache(cache_dir)
        self.mermaid_cli = MermaidCLI()
        self.cli_available = self.mermaid_cli.is_available()

    def parse(self, content: str, **options) -> str:
        """
        Parse markdown content and process mermaid blocks.

        Args:
            content: Markdown content with mermaid blocks
            **options: Options including:
                - convert_to_images: Whether to convert diagrams to images (default: True)
                - image_format: Format for images ('png', 'svg') (default: 'png')
                - embed_above: Whether to embed images above code blocks (default: True)
                - background_color: Background color for images (default: 'white')
                - width: Image width in pixels (optional)
                - height: Image height in pixels (optional)

        Returns:
            Processed markdown with image references
        """
        if not self.validate(content):
            return ""

        convert_to_images = options.get('convert_to_images', True)
        embed_above = options.get('embed_above', True)
        image_format = options.get('image_format', 'png')
        background_color = options.get('background_color', 'white')
        width = options.get('width', None)
        height = options.get('height', None)

        # Extract mermaid blocks
        self.blocks = self._extract_mermaid_blocks(content)

        if not self.blocks:
            return content

        if not convert_to_images:
            return content

        # Process each block
        processed_content = content
        for block in reversed(self.blocks):  # Process in reverse to maintain line numbers
            if block.ignore:
                continue

            # Generate image if CLI is available
            if self.cli_available:
                self._generate_image_for_block(
                    block,
                    image_format=image_format,
                    background_color=background_color,
                    width=width,
                    height=height
                )

            if embed_above:
                # Generate image reference using hash
                image_ref = f"{{{{image:{block.hash}}}}}"
                # Find the code block and add image above it
                processed_content = self._embed_image_above_block(
                    processed_content,
                    block,
                    image_ref
                )

        return processed_content

    def _extract_mermaid_blocks(self, content: str) -> List[MermaidBlock]:
        """
        Extract all mermaid code blocks from markdown.

        Args:
            content: Markdown content

        Returns:
            List of MermaidBlock objects
        """
        blocks = []
        lines = content.split('\n')
        in_mermaid_block = False
        current_block_content = []
        start_line = 0

        for i, line in enumerate(lines):
            # Check for mermaid code block start
            if re.match(r'^```mermaid\s*$', line.strip(), re.IGNORECASE):
                in_mermaid_block = True
                start_line = i
                current_block_content = []
                continue

            # Check for code block end
            if in_mermaid_block and re.match(r'^```\s*$', line.strip()):
                # Create block
                block = MermaidBlock(
                    content='\n'.join(current_block_content),
                    start_line=start_line,
                    end_line=i
                )
                blocks.append(block)
                in_mermaid_block = False
                current_block_content = []
                continue

            # Collect block content
            if in_mermaid_block:
                current_block_content.append(line)

        return blocks

    def _embed_image_above_block(self, content: str, block: MermaidBlock, image_ref: str) -> str:
        """
        Embed image reference above mermaid code block.

        Args:
            content: Full markdown content
            block: Mermaid block to process
            image_ref: Image reference string

        Returns:
            Updated markdown content
        """
        lines = content.split('\n')

        # Insert image reference before the code block
        # Add blank line before and after for proper spacing
        insert_lines = ['', image_ref, '']

        # Insert at start_line
        lines[block.start_line:block.start_line] = insert_lines

        return '\n'.join(lines)

    def _generate_image_for_block(
        self,
        block: MermaidBlock,
        image_format: str = 'png',
        background_color: str = 'white',
        width: Optional[int] = None,
        height: Optional[int] = None
    ) -> bool:
        """
        Generate image for a mermaid block and store in cache.

        Args:
            block: Mermaid block to process
            image_format: Output format ('png' or 'svg')
            background_color: Background color
            width: Image width in pixels (optional)
            height: Image height in pixels (optional)

        Returns:
            True if image was generated successfully
        """
        # Check if image already exists in cache
        if self.cache.get_image(block.hash):
            # Image already cached
            return True

        # Generate temporary output file path
        output_ext = f'.{image_format}'
        output_path = str(self.cache.cache_dir / f'{block.hash}{output_ext}')

        # Generate image using Mermaid CLI
        success, error_msg = self.mermaid_cli.generate_image(
            mermaid_code=block.content,
            output_path=output_path,
            image_format=image_format,
            background_color=background_color,
            width=width,
            height=height
        )

        if success:
            # Add to image cache
            # Since we already know the hash, we can update metadata directly
            file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
            self.cache.metadata[block.hash] = {
                'filename': f'mermaid_{block.hash[:8]}{output_ext}',
                'extension': output_ext,
                'size': file_size,
                'cached_path': output_path,
                'uploaded': False,
                'upload_url': None,
                'source': 'mermaid'
            }
            self.cache._save_metadata()
            return True
        else:
            # Log error but don't fail - we'll just use the handlebar reference
            # User can still manually upload or fix the diagram
            return False

    def can_handle(self, content: str) -> bool:
        """
        Check if content contains mermaid blocks.

        Args:
            content: Content to check

        Returns:
            True if content contains mermaid code blocks
        """
        return bool(re.search(r'```mermaid', content, re.IGNORECASE))

    def get_mermaid_blocks(self, content: str) -> List[MermaidBlock]:
        """
        Get all mermaid blocks from content.

        Args:
            content: Markdown content

        Returns:
            List of mermaid blocks
        """
        return self._extract_mermaid_blocks(content)

    def generate_image_references(self, content: str) -> Dict[str, str]:
        """
        Generate mapping of mermaid hashes to image references.

        Args:
            content: Markdown content with mermaid blocks

        Returns:
            Dictionary mapping hash to mermaid content
        """
        blocks = self._extract_mermaid_blocks(content)
        return {block.hash: block.content for block in blocks if not block.ignore}


def process_mermaid_diagrams(content: str, context: ParserContext = ParserContext.COMMENT, **options) -> str:
    """
    Convenience function to process mermaid diagrams.

    Args:
        content: Markdown content
        context: Parser context
        **options: Parser options

    Returns:
        Processed markdown with image references
    """
    parser = MermaidParser(context)
    return parser.parse(content, **options)
