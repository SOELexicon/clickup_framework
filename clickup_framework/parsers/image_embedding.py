"""
Image Embedding System

Handles hash-based image detection, caching, and automatic upload to ClickUp.
Processes {{image:sha256_hash}} handlebar syntax in comments, docs, pages, and task descriptions.
"""

import os
import re
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from .base import BaseParser, ParserContext


class ImageCache:
    """
    Manages cached images and their metadata.

    Stores images locally with hash-based keys and tracks upload status.
    """

    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize the image cache.

        Args:
            cache_dir: Directory for cache storage (default: ~/.clickup_framework/image_cache)
        """
        if cache_dir is None:
            cache_dir = os.path.join(
                os.path.expanduser('~'),
                '.clickup_framework',
                'image_cache'
            )

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.metadata_file = self.cache_dir / 'metadata.json'
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> Dict[str, Any]:
        """Load cache metadata from disk."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_metadata(self):
        """Save cache metadata to disk."""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)

    def compute_hash(self, file_path: str) -> str:
        """
        Compute SHA256 hash of a file.

        Args:
            file_path: Path to the file

        Returns:
            SHA256 hash as hex string
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            # Read file in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def add_image(self, file_path: str, hash_value: Optional[str] = None) -> str:
        """
        Add an image to the cache.

        Args:
            file_path: Path to the image file
            hash_value: Pre-computed hash (optional)

        Returns:
            Hash of the image
        """
        if hash_value is None:
            hash_value = self.compute_hash(file_path)

        # Copy file to cache with hash as filename
        file_ext = Path(file_path).suffix
        cached_file = self.cache_dir / f"{hash_value}{file_ext}"

        # Only copy if not already cached
        if not cached_file.exists():
            import shutil
            shutil.copy2(file_path, cached_file)

        # Update metadata
        self.metadata[hash_value] = {
            'filename': os.path.basename(file_path),
            'extension': file_ext,
            'size': os.path.getsize(file_path),
            'cached_path': str(cached_file),
            'uploaded': False,
            'upload_url': None
        }
        self._save_metadata()

        return hash_value

    def get_image(self, hash_value: str) -> Optional[Dict[str, Any]]:
        """
        Get image metadata by hash.

        Args:
            hash_value: Image hash

        Returns:
            Image metadata or None if not found
        """
        return self.metadata.get(hash_value)

    def mark_uploaded(self, hash_value: str, upload_url: str, attachment_data: Optional[Dict[str, Any]] = None):
        """
        Mark an image as uploaded.

        Args:
            hash_value: Image hash
            upload_url: URL where image was uploaded
            attachment_data: Full attachment metadata from ClickUp API (optional)
        """
        if hash_value in self.metadata:
            self.metadata[hash_value]['uploaded'] = True
            self.metadata[hash_value]['upload_url'] = upload_url
            # Store full attachment data if provided
            if attachment_data:
                self.metadata[hash_value]['attachment_data'] = attachment_data
            self._save_metadata()

    def get_cached_path(self, hash_value: str) -> Optional[str]:
        """
        Get local path to cached image.

        Args:
            hash_value: Image hash

        Returns:
            Path to cached file or None
        """
        metadata = self.get_image(hash_value)
        if metadata:
            return metadata.get('cached_path')
        return None

    def is_uploaded(self, hash_value: str) -> bool:
        """
        Check if image has been uploaded.

        Args:
            hash_value: Image hash

        Returns:
            True if uploaded
        """
        metadata = self.get_image(hash_value)
        return metadata.get('uploaded', False) if metadata else False


class ImageEmbedding(BaseParser):
    """
    Processes image embedding syntax in markdown content.

    Handles {{image:sha256_hash}} handlebars and manages image uploads.
    """

    def __init__(self, context: ParserContext = ParserContext.COMMENT, cache_dir: Optional[str] = None, client=None):
        """
        Initialize the image embedding parser.

        Args:
            context: Context in which parsing is happening
            cache_dir: Directory for image cache
            client: ClickUpClient instance for uploads (optional)
        """
        super().__init__(context)
        self.cache = ImageCache(cache_dir)
        self.client = client

    def parse(self, content: str, **options) -> str:
        """
        Process image embedding syntax in content.

        Args:
            content: Markdown content with image handlebars
            **options: Options including:
                - resolve_urls: Whether to resolve hashes to URLs (default: False)
                - upload_missing: Whether to upload missing images (default: False)

        Returns:
            Processed markdown with image references
        """
        if not self.validate(content):
            return ""

        resolve_urls = options.get('resolve_urls', False)

        if not resolve_urls:
            return content

        # Find all {{image:hash}} patterns
        pattern = r'\{\{image:([a-f0-9]{64})\}\}'
        matches = re.finditer(pattern, content)

        processed = content
        for match in matches:
            hash_value = match.group(1)
            metadata = self.cache.get_image(hash_value)

            if metadata and metadata.get('uploaded'):
                # Replace with markdown image syntax
                upload_url = metadata.get('upload_url', '')
                filename = metadata.get('filename', 'image')
                image_markdown = f"![{filename}]({upload_url})"
                processed = processed.replace(match.group(0), image_markdown)

        return processed

    def extract_image_references(self, content: str) -> List[str]:
        """
        Extract all image hash references from content.

        Args:
            content: Markdown content

        Returns:
            List of image hashes
        """
        pattern = r'\{\{image:([a-f0-9]{64})\}\}'
        matches = re.findall(pattern, content)
        return matches

    def embed_image(self, content: str, file_path: str, position: Optional[int] = None) -> Tuple[str, str]:
        """
        Embed an image in content using hash syntax.

        Args:
            content: Existing markdown content
            file_path: Path to image file
            position: Position to insert (None = append)

        Returns:
            Tuple of (updated_content, image_hash)
        """
        # Add image to cache
        hash_value = self.cache.add_image(file_path)

        # Create image reference
        image_ref = f"{{{{image:{hash_value}}}}}"

        # Insert into content
        if position is None:
            # Append at end
            if content and not content.endswith('\n'):
                content += '\n'
            content += f"\n{image_ref}\n"
        else:
            # Insert at position
            content = content[:position] + image_ref + content[position:]

        return content, hash_value

    def can_handle(self, content: str) -> bool:
        """
        Check if content contains image embedding syntax.

        Args:
            content: Content to check

        Returns:
            True if content contains image handlebars
        """
        pattern = r'\{\{image:[a-f0-9]{64}\}\}'
        return bool(re.search(pattern, content))

    def get_missing_images(self, content: str) -> List[str]:
        """
        Get list of image hashes that aren't in cache.

        Args:
            content: Markdown content

        Returns:
            List of missing image hashes
        """
        image_refs = self.extract_image_references(content)
        missing = []

        for hash_value in image_refs:
            if not self.cache.get_image(hash_value):
                missing.append(hash_value)

        return missing

    def get_unuploaded_images(self, content: str) -> List[str]:
        """
        Get list of image hashes that haven't been uploaded.

        Args:
            content: Markdown content

        Returns:
            List of unuploaded image hashes
        """
        image_refs = self.extract_image_references(content)
        unuploaded = []

        for hash_value in image_refs:
            if not self.cache.is_uploaded(hash_value):
                unuploaded.append(hash_value)

        return unuploaded

    def upload_image(self, hash_value: str, task_id: str) -> Dict[str, Any]:
        """
        Upload an image to ClickUp as an attachment.

        Args:
            hash_value: Image hash
            task_id: Task ID to attach image to

        Returns:
            Attachment data from ClickUp API

        Raises:
            ValueError: If client not provided or image not in cache
            FileNotFoundError: If cached image file doesn't exist
        """
        if self.client is None:
            raise ValueError("ClickUpClient instance required for uploads. Pass client to ImageEmbedding constructor.")

        # Get image metadata
        metadata = self.cache.get_image(hash_value)
        if not metadata:
            raise ValueError(f"Image with hash {hash_value} not found in cache")

        # Get cached file path
        cached_path = metadata.get('cached_path')
        if not cached_path or not os.path.exists(cached_path):
            raise FileNotFoundError(f"Cached image file not found: {cached_path}")

        # Upload to ClickUp
        attachment_data = self.client.create_task_attachment(task_id, cached_path)

        # Extract URL from response
        upload_url = attachment_data.get('url', '')

        # Update cache metadata with full attachment data
        self.cache.mark_uploaded(hash_value, upload_url, attachment_data)

        return attachment_data

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
        image_refs = self.extract_image_references(content)

        results = {
            'uploaded': [],
            'already_uploaded': [],
            'errors': []
        }

        for hash_value in image_refs:
            # Skip if already uploaded
            if self.cache.is_uploaded(hash_value):
                results['already_uploaded'].append(hash_value)
                continue

            # Try to upload
            try:
                self.upload_image(hash_value, task_id)
                results['uploaded'].append(hash_value)
            except Exception as e:
                results['errors'].append((hash_value, str(e)))

        return results


def embed_image(content: str, file_path: str, context: ParserContext = ParserContext.COMMENT) -> Tuple[str, str]:
    """
    Convenience function to embed an image in content.

    Args:
        content: Markdown content
        file_path: Path to image file
        context: Parser context

    Returns:
        Tuple of (updated_content, image_hash)
    """
    embedding = ImageEmbedding(context)
    return embedding.embed_image(content, file_path)


def extract_images(content: str) -> List[str]:
    """
    Convenience function to extract image hashes from content.

    Args:
        content: Markdown content

    Returns:
        List of image hashes
    """
    embedding = ImageEmbedding()
    return embedding.extract_image_references(content)
