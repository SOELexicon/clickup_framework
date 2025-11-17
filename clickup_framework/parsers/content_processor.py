"""
Content Processor - Unified Interface

Provides a unified interface for processing markdown content with
mermaid diagrams and image embedding across all contexts.
"""

from typing import Dict, Any, Optional, List
from .base import ParserContext
from .markdown_formatter import MarkdownFormatter
from .mermaid_parser import MermaidParser
from .image_embedding import ImageEmbedding, ImageCache


class ContentProcessor:
    """
    Unified content processor for markdown, mermaid, and images.

    Combines all parsers into a single easy-to-use interface.
    Handles the complete pipeline: markdown formatting -> mermaid processing -> image embedding.
    """

    def __init__(self, context: ParserContext = ParserContext.COMMENT, cache_dir: Optional[str] = None, client=None):
        """
        Initialize the content processor.

        Args:
            context: Context for processing (comment, doc, page, task_description)
            cache_dir: Directory for image cache
            client: ClickUpClient instance for uploads (optional)
        """
        self.context = context
        self.client = client
        self.cache_dir = cache_dir
        self.markdown_formatter = MarkdownFormatter(context)
        self.mermaid_parser = MermaidParser(context, cache_dir)
        self.image_embedding = ImageEmbedding(context, cache_dir, client)

    def process(self, content: str, **options) -> Dict[str, Any]:
        """
        Process content through full pipeline.

        Args:
            content: Raw markdown content
            **options: Processing options:
                - format_markdown: Format markdown (default: True)
                - process_mermaid: Process mermaid diagrams (default: True)
                - convert_mermaid_to_images: Convert mermaid to images (default: True)
                - embed_images: Process image handlebars (default: True)
                - resolve_image_urls: Resolve image hashes to URLs (default: False)

        Returns:
            Dictionary with:
                - content: Processed content
                - mermaid_blocks: List of mermaid blocks found
                - image_refs: List of image references
                - unuploaded_images: List of images needing upload
        """
        format_markdown = options.get('format_markdown', True)
        process_mermaid = options.get('process_mermaid', True)
        convert_mermaid = options.get('convert_mermaid_to_images', True)
        embed_images = options.get('embed_images', True)
        resolve_urls = options.get('resolve_image_urls', False)

        processed_content = content

        # Step 1: Format markdown
        if format_markdown:
            processed_content = self.markdown_formatter.parse(processed_content)

        # Step 2: Process mermaid diagrams
        mermaid_blocks = []
        if process_mermaid and self.mermaid_parser.can_handle(processed_content):
            mermaid_blocks = self.mermaid_parser.get_mermaid_blocks(processed_content)
            if convert_mermaid:
                processed_content = self.mermaid_parser.parse(
                    processed_content,
                    convert_to_images=True,
                    embed_above=True
                )

        # Step 3: Process image embedding
        image_refs = []
        unuploaded_images = []
        if embed_images and self.image_embedding.can_handle(processed_content):
            image_refs = self.image_embedding.extract_image_references(processed_content)
            unuploaded_images = self.image_embedding.get_unuploaded_images(processed_content)

            if resolve_urls:
                processed_content = self.image_embedding.parse(
                    processed_content,
                    resolve_urls=True
                )

        return {
            'content': processed_content,
            'mermaid_blocks': mermaid_blocks,
            'image_refs': image_refs,
            'unuploaded_images': unuploaded_images,
            'has_markdown': self.markdown_formatter.contains_markdown(processed_content),
        }

    def to_api_format(self, content: str, **options) -> Dict[str, Any]:
        """
        Process content and format for ClickUp API.

        Args:
            content: Raw markdown content
            **options: Processing options (same as process())

        Returns:
            Dictionary suitable for ClickUp API request
        """
        result = self.process(content, **options)
        processed = result['content']

        # Format based on context
        if self.context == ParserContext.COMMENT:
            return {
                "comment_text": processed,
                "_metadata": {
                    "mermaid_blocks": len(result['mermaid_blocks']),
                    "image_refs": len(result['image_refs']),
                    "unuploaded_images": len(result['unuploaded_images']),
                }
            }
        elif self.context == ParserContext.TASK_DESCRIPTION:
            if result['has_markdown']:
                return {
                    "markdown_description": processed,
                    "_metadata": {
                        "mermaid_blocks": len(result['mermaid_blocks']),
                        "image_refs": len(result['image_refs']),
                    }
                }
            else:
                return {
                    "description": processed
                }
        elif self.context in [ParserContext.DOC, ParserContext.PAGE]:
            return {
                "content": processed,
                "_metadata": {
                    "mermaid_blocks": len(result['mermaid_blocks']),
                    "image_refs": len(result['image_refs']),
                }
            }
        else:
            return {"text": processed}

    def add_image(self, content: str, file_path: str) -> Dict[str, Any]:
        """
        Add an image to content.

        Args:
            content: Existing content
            file_path: Path to image file

        Returns:
            Dictionary with:
                - content: Updated content
                - image_hash: Hash of added image
        """
        updated_content, image_hash = self.image_embedding.embed_image(content, file_path)

        return {
            'content': updated_content,
            'image_hash': image_hash
        }

    def get_image_cache(self) -> ImageCache:
        """
        Get the image cache instance.

        Returns:
            ImageCache instance
        """
        return self.image_embedding.cache

    def upload_image(self, image_hash: str, task_id: str) -> Dict[str, Any]:
        """
        Upload a single image to ClickUp.

        Args:
            image_hash: SHA256 hash of the image
            task_id: Task ID to attach image to

        Returns:
            Attachment data from ClickUp

        Raises:
            ValueError: If client not provided
        """
        if self.client is None:
            raise ValueError("ClickUpClient instance required for uploads. Pass client to ContentProcessor constructor.")

        return self.image_embedding.upload_image(image_hash, task_id)

    def upload_all_images(self, content: str, task_id: str) -> Dict[str, Any]:
        """
        Upload all unuploaded images referenced in content.

        Args:
            content: Markdown content with image references
            task_id: Task ID to attach images to

        Returns:
            Dictionary with upload results:
                - uploaded: List of successfully uploaded hashes
                - already_uploaded: List of already uploaded hashes
                - errors: List of (hash, error_message) tuples
        """
        if self.client is None:
            raise ValueError("ClickUpClient instance required for uploads. Pass client to ContentProcessor constructor.")

        return self.image_embedding.upload_all_images(content, task_id)

    def process_and_upload(self, content: str, task_id: str, **options) -> Dict[str, Any]:
        """
        Process content and automatically upload all images.

        Args:
            content: Raw markdown content
            task_id: Task ID to attach images to
            **options: Processing options (same as process())

        Returns:
            Dictionary with:
                - content: Processed content with handlebars resolved to image URLs
                - upload_results: Results from upload_all_images()
                - mermaid_blocks: List of mermaid blocks
                - image_refs: List of image references
                - image_metadata: Dict mapping image URLs to attachment metadata
                - attachment_ids: List of attachment IDs
        """
        if self.client is None:
            raise ValueError("ClickUpClient instance required for uploads. Pass client to ContentProcessor constructor.")

        # Step 1: Process content (format markdown, process mermaid, but don't resolve URLs yet)
        result = self.process(content, **options)

        # Step 2: Upload all images to ClickUp
        upload_results = {'uploaded': [], 'already_uploaded': [], 'errors': []}
        image_metadata = {}
        attachment_ids = []

        if result['image_refs']:
            upload_results = self.upload_all_images(result['content'], task_id)

            # Build image metadata map for inline embedding
            for hash_value in result['image_refs']:
                cached_meta = self.image_embedding.cache.get_image(hash_value)
                if cached_meta and cached_meta.get('uploaded'):
                    url = cached_meta.get('upload_url', '')
                    attachment_data = cached_meta.get('attachment_data', {})
                    if url and attachment_data:
                        image_metadata[url] = attachment_data
                        # Collect attachment ID
                        attachment_id = attachment_data.get('id')
                        if attachment_id and attachment_id not in attachment_ids:
                            attachment_ids.append(attachment_id)

        # Step 3: Resolve image handlebars to actual URLs now that images are uploaded
        final_content = result['content']
        if result['image_refs']:
            final_content = self.image_embedding.parse(
                result['content'],
                resolve_urls=True
            )

        return {
            'content': final_content,
            'upload_results': upload_results,
            'mermaid_blocks': result['mermaid_blocks'],
            'image_refs': result['image_refs'],
            'has_markdown': result['has_markdown'],
            'image_metadata': image_metadata,
            'attachment_ids': attachment_ids,
        }


def process_content(content: str, context: ParserContext = ParserContext.COMMENT, **options) -> Dict[str, Any]:
    """
    Convenience function to process content.

    Args:
        content: Raw markdown content
        context: Processing context
        **options: Processing options

    Returns:
        Processed content dictionary
    """
    processor = ContentProcessor(context)
    return processor.process(content, **options)


def format_for_api(content: str, context: ParserContext = ParserContext.COMMENT, **options) -> Dict[str, Any]:
    """
    Convenience function to format content for ClickUp API.

    Args:
        content: Raw markdown content
        context: Processing context
        **options: Processing options

    Returns:
        API-ready dictionary
    """
    processor = ContentProcessor(context)
    return processor.to_api_format(content, **options)
