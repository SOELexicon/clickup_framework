#!/usr/bin/env python3
"""
Test Mermaid Diagram Generation from Markdown Document

Tests generating mermaid diagrams from a markdown document into the mdmermaidtests folder.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clickup_framework.parsers import ContentProcessor, ParserContext


def main():
    """Test mermaid generation from markdown document."""
    print("=" * 80)
    print("Testing Mermaid Diagram Generation from Markdown")
    print("=" * 80)
    
    # Set up paths
    test_dir = Path(__file__).parent
    input_file = test_dir / "test_document.md"
    output_file = test_dir / "test_document_processed.md"
    cache_dir = test_dir / "cache"
    
    # Read input markdown
    print(f"\n[READ] Reading input file: {input_file}")
    if not input_file.exists():
        print(f"[ERROR] Input file not found: {input_file}")
        return 1
    
    content = input_file.read_text(encoding='utf-8')
    print(f"   Content length: {len(content)} characters")
    
    # Create processor with cache directory in test folder
    print(f"\n[SETUP] Creating ContentProcessor...")
    print(f"   Cache directory: {cache_dir}")
    processor = ContentProcessor(
        context=ParserContext.COMMENT,
        cache_dir=str(cache_dir)
    )
    
    # Process the content
    print(f"\n[PROCESS] Processing markdown with mermaid diagrams...")
    print("   Options: format_markdown=True, process_mermaid=True, convert_mermaid_to_images=True")
    
    try:
        result = processor.process(
            content,
            format_markdown=True,
            process_mermaid=True,
            convert_mermaid_to_images=True,
            embed_above=True,
            image_format='png',
            theme='dark',
            background_color='transparent'
        )
        
        # Display results
        print(f"\n[SUCCESS] Processing complete!")
        print(f"   Mermaid blocks found: {len(result.get('mermaid_blocks', []))}")
        print(f"   Generated images: {len(result.get('generated_images', []))}")
        
        if result.get('generated_images'):
            print(f"\n[IMAGES] Generated images:")
            for img_info in result['generated_images']:
                img_path = img_info.get('path', 'N/A')
                img_hash = img_info.get('hash', 'N/A')
                print(f"   - {img_path} (hash: {img_hash[:16]}...)")
        
        # Save processed output
        print(f"\n[SAVE] Saving processed document...")
        output_file.write_text(result['content'], encoding='utf-8')
        print(f"   Output saved to: {output_file}")
        
        # Show preview of processed content
        print(f"\n[PREVIEW] Preview of processed content (first 500 chars):")
        print("-" * 80)
        preview = result['content'][:500]
        print(preview)
        if len(result['content']) > 500:
            print("...")
        print("-" * 80)
        
        print(f"\n[SUCCESS] Test completed successfully!")
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] Error during processing: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

