# Markdown Formatting and Image Embedding Guide

## Overview

The ClickUp Framework now supports comprehensive markdown formatting, mermaid diagram processing, and image embedding across comments, docs, pages, and task descriptions.

## Features

### 1. Markdown to ClickUp JSON Formatter

Ensures markdown is properly formatted for ClickUp's API. Supports:

- **Headers** (H1-H6)
- **Bold, italic, strikethrough**
- **Code spans and code blocks**
- **Lists** (bulleted and numbered)
- **Links and images**
- **Blockquotes**
- **Horizontal rules**
- **Tables**

#### Usage

```python
from clickup_framework.parsers import MarkdownFormatter, ParserContext

# Create formatter for comments
formatter = MarkdownFormatter(ParserContext.COMMENT)

# Format markdown content
markdown_text = """
# My Header

This is **bold** and this is *italic*.

- List item 1
- List item 2

\```python
print("Hello, ClickUp!")
\```
"""

formatted = formatter.parse(markdown_text)
api_data = formatter.to_json_format(formatted)
# Returns: {"comment_text": "formatted markdown..."}
```

#### Convenience Functions

```python
from clickup_framework.parsers import format_markdown_for_clickup, contains_markdown

# Format markdown for specific context
formatted = format_markdown_for_clickup(content, ParserContext.TASK_DESCRIPTION)

# Check if text contains markdown
has_md = contains_markdown(text)
```

### 2. Mermaid Diagram Parser

Automatically detects mermaid code blocks and converts them to images.

#### Features

- **Automatic detection** of ```mermaid blocks
- **Content hashing** for change detection
- **Ignore comments** using `#ignore` or `%% ignore`
- **Image embedding** above code blocks
- **Works across** comments, docs, pages, task descriptions

#### Usage

```python
from clickup_framework.parsers import MermaidParser, ParserContext

parser = MermaidParser(ParserContext.COMMENT)

content = """
# System Architecture

\```mermaid
graph TD
    A[Client] --> B[Server]
    B --> C[Database]
\```
"""

# Process mermaid blocks (converts to images)
processed = parser.parse(content, convert_to_images=True, embed_above=True)

# Get mermaid blocks
blocks = parser.get_mermaid_blocks(content)
for block in blocks:
    print(f"Hash: {block.hash}")
    print(f"Content: {block.content}")
    print(f"Ignored: {block.ignore}")
```

#### Ignoring Mermaid Blocks

Add `#ignore` or `%% ignore` to the first line:

```markdown
\```mermaid
%% ignore
graph TD
    A --> B
\```
```

#### Convenience Functions

```python
from clickup_framework.parsers import process_mermaid_diagrams

# Process mermaid diagrams in content
processed = process_mermaid_diagrams(content, ParserContext.DOC)
```

### 3. Image Embedding System

Hash-based image detection and management with automatic upload to ClickUp.

#### Features

- **Hash-based syntax**: `{{image:sha256_hash}}`
- **Image caching** in `~/.clickup_framework/image_cache`
- **Upload tracking** to avoid duplicate uploads
- **Metadata storage** for images

#### Usage

```python
from clickup_framework.parsers import ImageEmbedding, ParserContext

embedding = ImageEmbedding(ParserContext.COMMENT)

# Add image to content
content = "Check out this diagram:"
updated_content, image_hash = embedding.embed_image(content, "/path/to/image.png")
# Returns: "Check out this diagram:\n\n{{image:abc123...}}\n"

# Extract image references
image_refs = embedding.extract_image_references(content)

# Check for unuploaded images
unuploaded = embedding.get_unuploaded_images(content)

# Resolve image hashes to URLs (after upload)
processed = embedding.parse(content, resolve_urls=True)
```

#### Image Cache Management

```python
from clickup_framework.parsers import ImageCache

cache = ImageCache()

# Add image to cache
hash_value = cache.add_image("/path/to/image.png")

# Get image metadata
metadata = cache.get_image(hash_value)

# Mark as uploaded
cache.mark_uploaded(hash_value, "https://clickup.com/uploaded/image.png")

# Check if uploaded
is_uploaded = cache.is_uploaded(hash_value)
```

#### Convenience Functions

```python
from clickup_framework.parsers import embed_image, extract_images

# Embed image in content
updated_content, hash_value = embed_image(content, "/path/to/image.png", ParserContext.COMMENT)

# Extract all image hashes
image_hashes = extract_images(content)
```

### 4. Unified Content Processor

Process markdown, mermaid, and images in a single operation.

#### Usage

```python
from clickup_framework.parsers import ContentProcessor, ParserContext

processor = ContentProcessor(ParserContext.COMMENT)

content = """
# API Documentation

The system uses the following architecture:

\```mermaid
graph LR
    A[API] --> B[Service]
    B --> C[Database]
\```

See the diagram: {{image:abc123...}}
"""

# Process everything
result = processor.process(content,
    format_markdown=True,
    process_mermaid=True,
    convert_mermaid_to_images=True,
    embed_images=True,
    resolve_image_urls=False
)

print(result['content'])  # Processed content
print(result['mermaid_blocks'])  # List of mermaid blocks
print(result['image_refs'])  # List of image references
print(result['unuploaded_images'])  # Images needing upload
print(result['has_markdown'])  # True if contains markdown

# Get API-ready format
api_data = processor.to_api_format(content)
# Returns: {"comment_text": "processed content...", "_metadata": {...}}
```

#### Convenience Functions

```python
from clickup_framework.parsers import process_content, format_for_api

# Process content
result = process_content(content, ParserContext.TASK_DESCRIPTION)

# Get API-ready format
api_data = format_for_api(content, ParserContext.PAGE)
```

### 5. Docs v3 API Integration

Extended support for page icons, colors, and cover images.

#### Page Icons

```python
from clickup_framework import ClickUpClient

client = ClickUpClient()

# Set emoji icon
client.docs.set_page_icon(workspace_id, doc_id, page_id, icon="🚀", icon_type="emoji")

# Set custom icon
client.docs.set_page_icon(workspace_id, doc_id, page_id, icon="custom_icon_id", icon_type="custom")
```

#### Page Colors and Cover Images

```python
# Set page color
client.docs.set_page_color(workspace_id, doc_id, page_id, color="#FF5733")

# Set cover image
client.docs.set_page_color(workspace_id, doc_id, page_id, cover_image_url="https://example.com/cover.jpg")

# Set both
client.docs.set_page_color(workspace_id, doc_id, page_id,
    color="#FF5733",
    cover_image_url="https://example.com/cover.jpg"
)
```

## Parser Contexts

The parsers are context-aware and adjust behavior based on where content is being used:

```python
from clickup_framework.parsers import ParserContext

ParserContext.COMMENT           # For task/view/list comments
ParserContext.TASK_DESCRIPTION  # For task descriptions
ParserContext.DOC               # For ClickUp docs
ParserContext.PAGE              # For ClickUp pages
```

## Complete Example

```python
from clickup_framework import ClickUpClient
from clickup_framework.parsers import ContentProcessor, ParserContext

# Initialize
client = ClickUpClient()
processor = ContentProcessor(ParserContext.COMMENT)

# Create content with markdown and mermaid
content = """
# Implementation Update

## Architecture

\```mermaid
graph TD
    A[Frontend] --> B[API Gateway]
    B --> C[Microservices]
    C --> D[Database]
\```

## Progress
- [x] Design phase complete
- [x] Implementation started
- [ ] Testing pending

**Status**: On track ✅
"""

# Process content
result = processor.process(content,
    format_markdown=True,
    process_mermaid=True,
    convert_mermaid_to_images=True
)

# Create comment
api_data = processor.to_api_format(content)
comment = client.create_task_comment(task_id, comment_text=api_data['comment_text'])

print(f"✓ Comment created with {len(result['mermaid_blocks'])} mermaid diagrams")
```

## Integration with Existing Code

The new parsers are designed to integrate seamlessly with existing code:

```python
from clickup_framework.parsers import contains_markdown

# This is compatible with the existing contains_markdown() function
# used in scripts/post_actions_to_clickup.py
if contains_markdown(description):
    task_data['markdown_description'] = description
else:
    task_data['description'] = description
```

## Best Practices

1. **Always validate** content before sending to API
2. **Cache images** before referencing them in content
3. **Upload images** before resolving URLs
4. **Use appropriate context** for each parser
5. **Process mermaid diagrams** before embedding in comments/docs
6. **Check for unuploaded images** before finalizing content

## Error Handling

```python
from clickup_framework.parsers import ContentProcessor, ParserContext

processor = ContentProcessor(ParserContext.COMMENT)

try:
    result = processor.process(content)

    # Check for issues
    if result['unuploaded_images']:
        print(f"Warning: {len(result['unuploaded_images'])} images need uploading")

    # Proceed with API call
    api_data = processor.to_api_format(content)

except Exception as e:
    print(f"Error processing content: {e}")
```

## Future Enhancements

- Automatic mermaid diagram rendering to PNG/SVG
- Direct image upload integration
- Syntax highlighting for code blocks
- Table parsing and formatting
- LaTeX/math equation support
