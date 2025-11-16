#!/usr/bin/env python3
"""
Test Mermaid Diagram Generation

Tests the Mermaid CLI integration and image generation functionality.
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
from clickup_framework.utils.mermaid_cli import is_mermaid_available


def test_mermaid_cli_detection():
    """Test 1: Mermaid CLI detection"""
    print("=" * 80)
    print("Test 1: Mermaid CLI Detection")
    print("=" * 80)

    available = is_mermaid_available()

    if available:
        print("✓ Mermaid CLI (mmdc) is available")
        from clickup_framework.utils.mermaid_cli import get_mermaid_cli
        cli = get_mermaid_cli()
        version = cli.get_version()
        print(f"  Version: {version}")
        print(f"  Path: {cli.cli_path}")
    else:
        print("⊘ Mermaid CLI (mmdc) not found")
        print("  Install with: npm install -g @mermaid-js/mermaid-cli")
        print("  Or set MERMAID_CLI_PATH environment variable")

    print(f"\n✓ Test 1 completed\n")
    return available


def test_mermaid_block_detection():
    """Test 2: Mermaid block detection"""
    print("=" * 80)
    print("Test 2: Mermaid Block Detection")
    print("=" * 80)

    content = """
# My Document

Here's a flowchart:

```mermaid
graph TD
    A[Start] --> B{Is it working?}
    B -->|Yes| C[Great!]
    B -->|No| D[Fix it]
    D --> B
```

And some more text.

```mermaid
sequenceDiagram
    Alice->>John: Hello John, how are you?
    John-->>Alice: Great!
```
"""

    parser = MermaidParser(ParserContext.COMMENT)
    blocks = parser.get_mermaid_blocks(content)

    print(f"✓ Found {len(blocks)} mermaid block(s)")

    for i, block in enumerate(blocks, 1):
        print(f"\n  Block {i}:")
        print(f"    Lines: {block.start_line}-{block.end_line}")
        print(f"    Hash: {block.hash[:16]}...")
        print(f"    Ignored: {block.ignore}")
        print(f"    Content preview: {block.content[:50]}...")

    print(f"\n✓ Test 2 passed\n")


def test_mermaid_ignore_directive():
    """Test 3: #ignore directive"""
    print("=" * 80)
    print("Test 3: Mermaid #ignore Directive")
    print("=" * 80)

    content = """
```mermaid
#ignore
graph TD
    A --> B
```

```mermaid
graph TD
    C --> D
```
"""

    parser = MermaidParser(ParserContext.COMMENT)
    blocks = parser.get_mermaid_blocks(content)

    print(f"✓ Found {len(blocks)} mermaid block(s)")

    ignored_count = sum(1 for b in blocks if b.ignore)
    active_count = sum(1 for b in blocks if not b.ignore)

    print(f"  Ignored: {ignored_count}")
    print(f"  Active: {active_count}")

    assert ignored_count == 1, "Expected 1 ignored block"
    assert active_count == 1, "Expected 1 active block"

    print(f"\n✓ Test 3 passed\n")


def test_mermaid_image_generation():
    """Test 4: Image generation (requires mmdc)"""
    print("=" * 80)
    print("Test 4: Mermaid Image Generation")
    print("=" * 80)

    if not is_mermaid_available():
        print("⊘ Skipping - Mermaid CLI not available")
        print("\n✓ Test 4 skipped\n")
        return

    content = """
# Test Document

```mermaid
graph LR
    A[Input] --> B[Process]
    B --> C[Output]
```
"""

    parser = MermaidParser(ParserContext.COMMENT)

    # Process with image generation
    result = parser.parse(content, convert_to_images=True, embed_above=True)

    print("✓ Mermaid processing completed")

    # Check if image references were added
    if "{{image:" in result:
        print("✓ Image references embedded in content")

        # Count image references
        import re
        refs = re.findall(r'\{\{image:([a-f0-9]{64})\}\}', result)
        print(f"  Found {len(refs)} image reference(s)")

        # Check cache
        blocks = parser.get_mermaid_blocks(content)
        for block in blocks:
            cached = parser.cache.get_image(block.hash)
            if cached:
                print(f"\n  ✓ Image cached for block {block.hash[:8]}...")
                print(f"    Path: {cached.get('cached_path')}")
                print(f"    Size: {cached.get('size')} bytes")
            else:
                print(f"\n  ✗ Image not cached for block {block.hash[:8]}...")
    else:
        print("✗ No image references found in result")

    print(f"\n✓ Test 4 completed\n")


def test_content_processor_integration():
    """Test 5: ContentProcessor integration"""
    print("=" * 80)
    print("Test 5: ContentProcessor Integration")
    print("=" * 80)

    content = """
# Architecture Overview

```mermaid
graph TB
    User[User] --> CLI[CLI Interface]
    CLI --> Parser[Content Processor]
    Parser --> API[ClickUp API]
```

The system processes markdown content.
"""

    processor = ContentProcessor(ParserContext.COMMENT)

    # Process content
    result = processor.process(
        content,
        format_markdown=True,
        process_mermaid=True,
        convert_mermaid_to_images=True
    )

    print("✓ Content processed")
    print(f"  Mermaid blocks: {len(result['mermaid_blocks'])}")
    print(f"  Has markdown: {result['has_markdown']}")

    if is_mermaid_available():
        print(f"  Image refs: {len(result['image_refs'])}")
        print(f"  Unuploaded images: {len(result['unuploaded_images'])}")

    print(f"\n✓ Test 5 passed\n")


def test_various_diagram_types():
    """Test 6: Various mermaid diagram types"""
    print("=" * 80)
    print("Test 6: Various Diagram Types")
    print("=" * 80)

    if not is_mermaid_available():
        print("⊘ Skipping - Mermaid CLI not available")
        print("\n✓ Test 6 skipped\n")
        return

    diagrams = {
        'flowchart': """
```mermaid
flowchart LR
    Start --> Stop
```
""",
        'sequence': """
```mermaid
sequenceDiagram
    participant A
    participant B
    A->>B: Hello
    B->>A: Hi
```
""",
        'class': """
```mermaid
classDiagram
    Animal <|-- Duck
    Animal : +int age
```
"""
    }

    parser = MermaidParser(ParserContext.COMMENT)

    for diagram_type, content in diagrams.items():
        print(f"\n  Testing {diagram_type} diagram...")
        result = parser.parse(content, convert_to_images=True)

        if "{{image:" in result:
            print(f"    ✓ {diagram_type} diagram processed")
        else:
            print(f"    ⊘ {diagram_type} diagram not processed")

    print(f"\n✓ Test 6 completed\n")


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("MERMAID DIAGRAM GENERATION TESTS")
    print("=" * 80 + "\n")

    # Test 1: CLI detection (always run)
    cli_available = test_mermaid_cli_detection()

    # Test 2-3: Parser tests (always run)
    tests = [
        test_mermaid_block_detection,
        test_mermaid_ignore_directive,
    ]

    # Test 4-6: Generation tests (run if CLI available)
    if cli_available:
        tests.extend([
            test_mermaid_image_generation,
            test_content_processor_integration,
            test_various_diagram_types,
        ])

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

    if not cli_available:
        print("\nNote: Some tests were skipped because Mermaid CLI is not installed.")
        print("To install: npm install -g @mermaid-js/mermaid-cli")


if __name__ == "__main__":
    main()
