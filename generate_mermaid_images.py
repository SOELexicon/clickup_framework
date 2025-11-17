#!/usr/bin/env python3
"""
Pre-generate Mermaid diagram images and cache them
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from clickup_framework.parsers import ContentProcessor, ParserContext

def main():
    # Read the mermaid content file
    with open('mermaid_doc_content.md', 'r') as f:
        content = f.read()

    print("=" * 80)
    print("Generating Mermaid Images")
    print("=" * 80)
    print()

    # Create processor
    processor = ContentProcessor(ParserContext.COMMENT)

    # Process with image generation
    print("Processing content and generating images...")
    result = processor.process(
        content,
        format_markdown=True,
        process_mermaid=True,
        convert_mermaid_to_images=True
    )

    print(f"\n✓ Processing complete!")
    print(f"  Mermaid blocks found: {len(result['mermaid_blocks'])}")
    print(f"  Image references: {len(result['image_refs'])}")
    print(f"  Unuploaded images: {len(result['unuploaded_images'])}")

    # Show cache location
    cache_dir = os.path.expanduser('~/.clickup_framework/image_cache/')
    print(f"\n  Cache directory: {cache_dir}")

    if os.path.exists(cache_dir):
        cached_files = [f for f in os.listdir(cache_dir) if f.endswith('.png')]
        print(f"  Cached images: {len(cached_files)}")

        if cached_files:
            print("\n  Generated images:")
            for i, filename in enumerate(sorted(cached_files), 1):
                filepath = os.path.join(cache_dir, filename)
                size = os.path.getsize(filepath)
                print(f"    {i}. {filename[:16]}... ({size:,} bytes)")

    print("\n" + "=" * 80)
    print("Images generated and cached successfully!")
    print("=" * 80)

if __name__ == "__main__":
    main()
