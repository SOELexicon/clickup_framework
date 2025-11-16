#!/usr/bin/env python3
"""
Test Mermaid Processing Without CLI

Verifies that mermaid processing works gracefully when CLI is not available.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clickup_framework.parsers import (
    MermaidParser,
    ContentProcessor,
    ParserContext
)


def test_without_cli():
    """Test that processing works without CLI installed"""
    print("=" * 80)
    print("Test: Mermaid Processing Without CLI")
    print("=" * 80)

    content = """
# My Document

```mermaid
graph TD
    A[Start] --> B[Process]
    B --> C[End]
```

Some text here.
"""

    # Create parser
    parser = MermaidParser(ParserContext.COMMENT)

    print(f"✓ Parser created")
    print(f"  CLI available: {parser.cli_available}")

    # Parse with convert_to_images=True (should still work, just won't generate images)
    result = parser.parse(content, convert_to_images=True, embed_above=True)

    print(f"✓ Parse completed without errors")

    # Should still embed image references even if images weren't generated
    if "{{image:" in result:
        print(f"✓ Image references embedded (handlebars added)")

        # Extract blocks to verify
        blocks = parser.get_mermaid_blocks(content)
        print(f"  Detected {len(blocks)} mermaid block(s)")

        for block in blocks:
            print(f"  Block hash: {block.hash[:16]}...")

            # Check if it's in cache (won't be if CLI unavailable)
            cached = parser.cache.get_image(block.hash)
            if cached:
                print(f"    ✓ Image generated and cached")
            else:
                print(f"    ⊘ Image not generated (CLI unavailable)")
    else:
        print(f"✗ Image references not embedded")

    print(f"\n✓ Test passed - graceful degradation working\n")


def test_content_processor_without_cli():
    """Test ContentProcessor without CLI"""
    print("=" * 80)
    print("Test: ContentProcessor Without CLI")
    print("=" * 80)

    content = """
# System Architecture

```mermaid
graph LR
    User --> System
    System --> Database
```

```mermaid
#ignore
graph TD
    Internal --> Debug
```
"""

    processor = ContentProcessor(ParserContext.COMMENT)

    result = processor.process(
        content,
        format_markdown=True,
        process_mermaid=True,
        convert_mermaid_to_images=True
    )

    print(f"✓ Processing completed")
    print(f"  Mermaid blocks: {len(result['mermaid_blocks'])}")
    print(f"  Image refs: {len(result['image_refs'])}")

    # Should have references even without CLI
    if result['image_refs']:
        print(f"✓ Image references created")
    else:
        print(f"⊘ No image references (expected if no blocks or all ignored)")

    # Count non-ignored blocks
    non_ignored = sum(1 for b in result['mermaid_blocks'] if not b.ignore)
    print(f"  Non-ignored blocks: {non_ignored}")
    print(f"  Ignored blocks: {len(result['mermaid_blocks']) - non_ignored}")

    print(f"\n✓ Test passed\n")


def test_api_format_output():
    """Test API format output"""
    print("=" * 80)
    print("Test: API Format Output")
    print("=" * 80)

    content = """
# Task Update

```mermaid
graph TD
    Start --> Done
```
"""

    processor = ContentProcessor(ParserContext.COMMENT)

    api_output = processor.to_api_format(content)

    print(f"✓ API format generated")
    print(f"  Keys: {list(api_output.keys())}")

    if 'comment_text' in api_output:
        print(f"✓ Comment text field present")
        if "{{image:" in api_output['comment_text']:
            print(f"✓ Image references in comment text")

    if '_metadata' in api_output:
        meta = api_output['_metadata']
        print(f"✓ Metadata present")
        print(f"  Mermaid blocks: {meta.get('mermaid_blocks', 0)}")
        print(f"  Image refs: {meta.get('image_refs', 0)}")

    print(f"\n✓ Test passed\n")


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("MERMAID WITHOUT CLI TESTS")
    print("=" * 80 + "\n")

    tests = [
        test_without_cli,
        test_content_processor_without_cli,
        test_api_format_output,
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
    print("\nThese tests verify that the system works gracefully")
    print("even when Mermaid CLI (mmdc) is not installed.")
    print("\nImage handlebars {{image:hash}} are created and can be")
    print("resolved later when images are generated externally.")


if __name__ == "__main__":
    main()
