#!/usr/bin/env python3
"""
Test Image Upload Integration

Tests the new image upload functionality in the ImageEmbedding system.
"""

import sys
import os
import tempfile

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clickup_framework import ClickUpClient
from clickup_framework.parsers import (
    ImageEmbedding,
    ContentProcessor,
    ParserContext
)


def create_test_image(size=1024):
    """Create a test image file (simple binary data)."""
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(mode='wb', suffix='.png', delete=False)
    temp_path = temp_file.name

    # Write simple binary data (not a real image, just for testing)
    temp_file.write(b'\x89PNG\r\n\x1a\n' + b'\x00' * size)
    temp_file.close()

    return temp_path


def test_image_cache():
    """Test 1: ImageCache basic functionality"""
    print("=" * 80)
    print("Test 1: ImageCache Basic Functionality")
    print("=" * 80)

    # Create test image
    image_path = create_test_image(size=1024)
    print(f"Created test image: {image_path}")

    # Test ImageEmbedding
    embedding = ImageEmbedding(ParserContext.COMMENT)

    # Add image to cache
    content = "Check out this image:"
    updated_content, image_hash = embedding.embed_image(content, image_path)

    print(f"\n✓ Image added to cache")
    print(f"  Hash: {image_hash[:16]}...")
    print(f"  Content: {updated_content[:100]}...")

    # Extract image references
    refs = embedding.extract_image_references(updated_content)
    print(f"\n✓ Extracted {len(refs)} image reference(s)")

    # Check unuploaded
    unuploaded = embedding.get_unuploaded_images(updated_content)
    print(f"✓ {len(unuploaded)} image(s) need uploading")

    # Cleanup
    os.unlink(image_path)
    print("\n✓ Test 1 passed\n")


def test_upload_without_client():
    """Test 2: Upload without client (should fail gracefully)"""
    print("=" * 80)
    print("Test 2: Upload Without Client (Error Handling)")
    print("=" * 80)

    # Create test image
    image_path = create_test_image(size=2048)

    # Test ImageEmbedding without client
    embedding = ImageEmbedding(ParserContext.COMMENT)
    content, image_hash = embedding.embed_image("Test:", image_path)

    try:
        embedding.upload_image(image_hash, "fake_task_id")
        print("✗ Should have raised ValueError")
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {str(e)[:60]}...")

    # Cleanup
    os.unlink(image_path)
    print("\n✓ Test 2 passed\n")


def test_content_processor():
    """Test 3: ContentProcessor with image upload methods"""
    print("=" * 80)
    print("Test 3: ContentProcessor Upload Methods")
    print("=" * 80)

    # Create test image
    image_path = create_test_image(size=3072)

    # Initialize processor without client
    processor = ContentProcessor(ParserContext.COMMENT)

    # Add image
    result = processor.add_image("Test content:", image_path)
    print(f"✓ Image added via ContentProcessor")
    print(f"  Hash: {result['image_hash'][:16]}...")

    # Try upload without client (should fail)
    try:
        processor.upload_all_images(result['content'], "fake_task_id")
        print("✗ Should have raised ValueError")
    except ValueError as e:
        print(f"✓ Correctly raised ValueError for missing client")

    # Cleanup
    os.unlink(image_path)
    print("\n✓ Test 3 passed\n")


def test_with_real_client():
    """Test 4: Upload with real ClickUpClient (requires API token)"""
    print("=" * 80)
    print("Test 4: Upload with Real Client (Optional)")
    print("=" * 80)

    # Check if API token is available
    if not os.environ.get('CLICKUP_API_TOKEN'):
        print("⊘ Skipping - CLICKUP_API_TOKEN not set")
        print("  Set CLICKUP_API_TOKEN to test actual uploads")
        print("\n✓ Test 4 skipped\n")
        return

    # Check if task ID is provided
    test_task_id = os.environ.get('TEST_TASK_ID')
    if not test_task_id:
        print("⊘ Skipping - TEST_TASK_ID not set")
        print("  Set TEST_TASK_ID=<task_id> to test actual uploads")
        print("\n✓ Test 4 skipped\n")
        return

    # Create test image
    image_path = create_test_image(size=4096)

    # Initialize client
    client = ClickUpClient()

    # Create processor with client
    processor = ContentProcessor(ParserContext.COMMENT, client=client)

    # Add image
    result = processor.add_image("Test upload:", image_path)
    image_hash = result['image_hash']

    print(f"✓ Image added to cache: {image_hash[:16]}...")

    # Upload image
    try:
        attachment = processor.upload_image(image_hash, test_task_id)
        print(f"✓ Image uploaded successfully!")
        print(f"  Attachment ID: {attachment.get('id', 'N/A')}")
        print(f"  URL: {attachment.get('url', 'N/A')[:60]}...")

        # Verify cache updated
        cache = processor.get_image_cache()
        if cache.is_uploaded(image_hash):
            print(f"✓ Cache metadata updated correctly")
        else:
            print(f"✗ Cache metadata not updated")

    except Exception as e:
        print(f"✗ Upload failed: {e}")
        import traceback
        traceback.print_exc()

    # Cleanup
    os.unlink(image_path)
    print("\n✓ Test 4 completed\n")


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("IMAGE UPLOAD INTEGRATION TESTS")
    print("=" * 80 + "\n")

    tests = [
        test_image_cache,
        test_upload_without_client,
        test_content_processor,
        test_with_real_client,
    ]

    for test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"\n✗ Test failed: {test_func.__name__}")
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()

    print("=" * 80)
    print("All tests complete!")
    print("=" * 80)
    print("\nTo test actual uploads:")
    print("  export CLICKUP_API_TOKEN=your_token")
    print("  export TEST_TASK_ID=task_id")
    print("  python examples/test_image_upload.py")


if __name__ == "__main__":
    main()
