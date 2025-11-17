#!/usr/bin/env python3
"""
Direct Mermaid Image Generation Test

Tests directly generating mermaid images from the markdown document.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clickup_framework.parsers import MermaidParser, ParserContext


def main():
    """Test direct mermaid image generation."""
    print("=" * 80)
    print("Direct Mermaid Image Generation Test")
    print("=" * 80)
    
    # Set up paths
    test_dir = Path(__file__).parent
    input_file = test_dir / "test_document.md"
    output_dir = test_dir / "generated_images"
    cache_dir = test_dir / "cache"
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    # Read input markdown
    print(f"\n[READ] Reading input file: {input_file}")
    content = input_file.read_text(encoding='utf-8')
    
    # Create mermaid parser
    print(f"\n[SETUP] Creating MermaidParser...")
    parser = MermaidParser(
        context=ParserContext.COMMENT,
        cache_dir=str(cache_dir)
    )
    
    # Check if CLI is available
    if not parser.cli_available:
        print("[WARNING] Mermaid CLI not available - images cannot be generated")
        print("   Install with: npm install -g @mermaid-js/mermaid-cli")
        return 1
    
    print(f"[INFO] Mermaid CLI is available")
    
    # Process the content
    print(f"\n[PROCESS] Processing markdown with mermaid diagrams...")
    
    try:
        result = parser.parse(
            content,
            convert_to_images=True,
            embed_above=True,
            image_format='png',
            theme='dark',
            background_color='transparent'
        )
        
        print(f"\n[SUCCESS] Processing complete!")
        print(f"   Processed content length: {len(result)} characters")
        
        # Check for image references in the output
        import re
        image_refs = re.findall(r'\{\{image:([a-f0-9]{64})\}\}', result)
        print(f"   Image references found: {len(image_refs)}")
        
        if image_refs:
            print(f"\n[IMAGES] Image references:")
            for i, img_hash in enumerate(image_refs, 1):
                print(f"   {i}. {img_hash[:16]}...")
                
                # Check if image exists in cache
                cached_path = parser.cache.get_cached_path(img_hash)
                if cached_path and Path(cached_path).exists():
                    print(f"      -> Cached at: {cached_path}")
                    # Copy to output directory
                    import shutil
                    output_path = output_dir / f"diagram_{i}_{img_hash[:16]}.png"
                    shutil.copy2(cached_path, output_path)
                    print(f"      -> Copied to: {output_path}")
                else:
                    print(f"      -> Not found in cache")
        
        # Save processed output
        output_file = test_dir / "test_document_with_images.md"
        output_file.write_text(result, encoding='utf-8')
        print(f"\n[SAVE] Processed document saved to: {output_file}")
        
        print(f"\n[SUCCESS] Test completed!")
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] Error during processing: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

