#!/usr/bin/env python3
"""
Example: Using Markdown Formatting and Image Embedding

Demonstrates how to use the new markdown formatting, mermaid diagram processing,
and image embedding features in the ClickUp Framework.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clickup_framework import ClickUpClient
from clickup_framework.parsers import (
    ContentProcessor,
    ParserContext,
    MarkdownFormatter,
    MermaidParser,
    ImageEmbedding,
    process_content,
    format_for_api,
    contains_markdown
)


def example_markdown_formatter():
    """Example 1: Basic markdown formatting"""
    print("=" * 80)
    print("Example 1: Markdown Formatting")
    print("=" * 80)

    formatter = MarkdownFormatter(ParserContext.COMMENT)

    content = """
# Project Update

## Progress

We've made significant progress on the following:

- **Authentication** - Complete ✅
- **API Integration** - In Progress 🚧
- **Testing** - Pending ⏳

## Code Example

\```python
def authenticate(username, password):
    # Implementation here
    return token
\```

## Next Steps

1. Complete API integration
2. Write comprehensive tests
3. Deploy to staging

*Last updated: 2025-01-15*
"""

    # Check if contains markdown
    has_md = formatter.contains_markdown(content)
    print(f"\nContains markdown: {has_md}")

    # Format for ClickUp
    formatted = formatter.parse(content)
    print("\nFormatted content:")
    print(formatted)

    # Get API format
    api_data = formatter.to_json_format(formatted)
    print("\nAPI format:")
    print(api_data)
    print()


def example_mermaid_parser():
    """Example 2: Mermaid diagram processing"""
    print("=" * 80)
    print("Example 2: Mermaid Diagram Processing")
    print("=" * 80)

    parser = MermaidParser(ParserContext.DOC)

    content = """
# System Architecture

Our system follows a microservices architecture:

\```mermaid
graph TD
    A[Client Application] --> B[API Gateway]
    B --> C[Auth Service]
    B --> D[User Service]
    B --> E[Data Service]
    C --> F[User Database]
    D --> F
    E --> G[Data Database]
\```

## Data Flow

\```mermaid
sequenceDiagram
    participant C as Client
    participant A as API
    participant D as Database
    C->>A: Request Data
    A->>D: Query
    D-->>A: Results
    A-->>C: Response
\```
"""

    # Check if can handle
    can_handle = parser.can_handle(content)
    print(f"\nCan handle mermaid: {can_handle}")

    # Get mermaid blocks
    blocks = parser.get_mermaid_blocks(content)
    print(f"\nFound {len(blocks)} mermaid blocks:")
    for i, block in enumerate(blocks):
        print(f"\n  Block {i + 1}:")
        print(f"    Hash: {block.hash[:16]}...")
        print(f"    Lines: {block.start_line}-{block.end_line}")
        print(f"    Ignored: {block.ignore}")

    # Process (convert to images)
    processed = parser.parse(content, convert_to_images=True, embed_above=True)
    print("\nProcessed content (with image references):")
    print(processed[:500] + "...")
    print()


def example_image_embedding():
    """Example 3: Image embedding"""
    print("=" * 80)
    print("Example 3: Image Embedding")
    print("=" * 80)

    embedding = ImageEmbedding(ParserContext.COMMENT)

    content = "Check out this architecture diagram:"

    # Note: This would work with an actual image file
    # For demo purposes, we'll just show the syntax
    print("\nOriginal content:")
    print(content)

    # Simulate embedding an image
    # In real usage: updated, hash_val = embedding.embed_image(content, "/path/to/diagram.png")
    simulated_content = """Check out this architecture diagram:

{{image:a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2}}
"""

    print("\nContent with embedded image:")
    print(simulated_content)

    # Extract image references
    image_refs = embedding.extract_image_references(simulated_content)
    print(f"\nFound {len(image_refs)} image reference(s):")
    for ref in image_refs:
        print(f"  {ref[:16]}...")

    # Check for unuploaded
    unuploaded = embedding.get_unuploaded_images(simulated_content)
    print(f"\nUnuploaded images: {len(unuploaded)}")

    # Get cache info
    cache = embedding.cache
    print(f"\nImage cache directory: {cache.cache_dir}")
    print()


def example_content_processor():
    """Example 4: Unified content processing"""
    print("=" * 80)
    print("Example 4: Unified Content Processor")
    print("=" * 80)

    processor = ContentProcessor(ParserContext.COMMENT)

    content = """
# Sprint Review

## Accomplishments

\```mermaid
graph LR
    A[Planning] --> B[Development]
    B --> C[Testing]
    C --> D[Deployment]
\```

### Completed Tasks
- [x] User authentication
- [x] Dashboard UI
- [x] API endpoints
- [ ] Documentation

## Metrics

**Velocity**: 32 story points
**Quality**: 98% test coverage ✅

See detailed breakdown: {{image:example123456789abcdef}}
"""

    # Process everything
    result = processor.process(content,
        format_markdown=True,
        process_mermaid=True,
        convert_mermaid_to_images=True,
        embed_images=True
    )

    print("\nProcessing results:")
    print(f"  Markdown detected: {result['has_markdown']}")
    print(f"  Mermaid blocks: {len(result['mermaid_blocks'])}")
    print(f"  Image references: {len(result['image_refs'])}")
    print(f"  Unuploaded images: {len(result['unuploaded_images'])}")

    # Get API format
    api_data = processor.to_api_format(content)
    print("\nAPI-ready format:")
    print(f"  Keys: {list(api_data.keys())}")
    print(f"  Comment length: {len(api_data.get('comment_text', ''))}")
    print()


def example_convenience_functions():
    """Example 5: Using convenience functions"""
    print("=" * 80)
    print("Example 5: Convenience Functions")
    print("=" * 80)

    content = """
# Quick Update

Just wanted to share that we've **completed** the migration!

\```python
def migrate():
    return "Success"
\```
"""

    # Check for markdown
    has_md = contains_markdown(content)
    print(f"\nHas markdown: {has_md}")

    # Process content
    result = process_content(content, ParserContext.TASK_DESCRIPTION)
    print(f"\nProcessed successfully: {result['has_markdown']}")

    # Format for API
    api_data = format_for_api(content, ParserContext.COMMENT)
    print(f"\nAPI format keys: {list(api_data.keys())}")
    print()


def example_complete_workflow():
    """Example 6: Complete workflow with ClickUp client"""
    print("=" * 80)
    print("Example 6: Complete Workflow")
    print("=" * 80)

    # This example shows how to use the processor with the ClickUp client
    # Note: Requires CLICKUP_API_TOKEN environment variable

    print("\nComplete workflow example:")
    print("1. Create content with markdown and mermaid")
    print("2. Process content")
    print("3. Create comment/task with processed content")

    content = """
# Feature Implementation

## Design

\```mermaid
graph TD
    A[User Input] --> B[Validation]
    B --> C[Processing]
    C --> D[Response]
\```

## Implementation Status
- [x] Backend API
- [x] Frontend UI
- [ ] Tests

**ETA**: End of sprint
"""

    processor = ContentProcessor(ParserContext.COMMENT)

    # Process
    result = processor.process(content)
    print(f"\n✓ Processed: {len(result['mermaid_blocks'])} mermaid blocks")

    # Get API format
    api_data = processor.to_api_format(content)
    print(f"✓ API format ready: comment_text field with {len(api_data['comment_text'])} chars")

    # In real usage, you would create the comment:
    # client = ClickUpClient()
    # comment = client.create_task_comment(task_id, comment_text=api_data['comment_text'])
    # print(f"✓ Comment created: {comment['id']}")

    print("\n(Skipping actual API call - set CLICKUP_API_TOKEN to test)")
    print()


def main():
    """Run all examples"""
    print("\n" + "=" * 80)
    print("MARKDOWN FORMATTING & IMAGE EMBEDDING EXAMPLES")
    print("=" * 80 + "\n")

    examples = [
        example_markdown_formatter,
        example_mermaid_parser,
        example_image_embedding,
        example_content_processor,
        example_convenience_functions,
        example_complete_workflow
    ]

    for example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"\nError in {example_func.__name__}: {e}")
            import traceback
            traceback.print_exc()

    print("=" * 80)
    print("Examples complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
