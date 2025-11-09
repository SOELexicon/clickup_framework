# ClickUp Docs API - Implementation Guide

Complete guide for using the ClickUp Docs API (v3) to create and manage documentation.

## Table of Contents

- [Quick Start](#quick-start)
- [Basic Usage](#basic-usage)
- [Creating Hierarchical Documentation](#creating-hierarchical-documentation)
- [API Reference](#api-reference)
- [Markdown Formatting](#markdown-formatting)
- [Examples](#examples)

## Quick Start

```python
from clickup_framework import ClickUpClient
from clickup_framework.resources import DocsAPI

# Initialize
client = ClickUpClient()
docs = DocsAPI(client)

workspace_id = "90151898946"

# Create a doc
doc = docs.create_doc(workspace_id, "My Documentation")
doc_id = doc['id']

# Create pages
page = docs.create_page(
    workspace_id=workspace_id,
    doc_id=doc_id,
    name="Getting Started",
    content="# Getting Started\n\nWelcome to the documentation!"
)
```

## Basic Usage

### 1. List All Docs in Workspace

```python
docs_list = docs.get_workspace_docs(workspace_id)

for doc in docs_list['docs']:
    print(f"Doc: {doc['name']} (ID: {doc['id']})")
```

### 2. Create a Doc

```python
doc = docs.create_doc(
    workspace_id=workspace_id,
    name="API Documentation"
)

doc_id = doc['id']
print(f"Created doc: {doc_id}")
```

### 3. Get Doc Details

```python
doc_details = docs.get_doc(workspace_id, doc_id)
print(f"Doc name: {doc_details['name']}")
print(f"Created: {doc_details['date_created']}")
```

### 4. Create Pages

```python
page = docs.create_page(
    workspace_id=workspace_id,
    doc_id=doc_id,
    name="Introduction",
    content="""# Introduction

This is the introduction page.

## Features

- Feature 1
- Feature 2
- Feature 3
"""
)
```

### 5. List All Pages in a Doc

```python
pages = docs.get_doc_pages(workspace_id, doc_id)

for page in pages:
    print(f"Page: {page['name']}")
    print(f"  ID: {page['id']}")
    print(f"  Content length: {len(page.get('content', ''))}")
```

### 6. Update a Page

```python
updated_page = docs.update_page(
    workspace_id=workspace_id,
    doc_id=doc_id,
    page_id=page_id,
    name="Updated Introduction",
    content="# Updated Introduction\n\nThis content has been updated."
)
```

## Creating Hierarchical Documentation

ClickUp Docs support hierarchical organization through parent-child relationships. Here's how to create structured documentation:

### Index Page Pattern

Create an index page that links to child pages:

```python
# Create the main doc
doc = docs.create_doc(
    workspace_id=workspace_id,
    name="Product Documentation"
)
doc_id = doc['id']

# Create index/overview page
index_page = docs.create_page(
    workspace_id=workspace_id,
    doc_id=doc_id,
    name="Documentation Index",
    content="""# Product Documentation

## Table of Contents

### Getting Started
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)

### User Guide
- [Basic Features](#basic-features)
- [Advanced Features](#advanced-features)
- [Best Practices](#best-practices)

### API Reference
- [Core API](#core-api)
- [Authentication](#authentication)
- [Examples](#examples)

### Deployment
- [Development](#development)
- [Staging](#staging)
- [Production](#production)
"""
)

# Create child pages for each section
sections = [
    ("Getting Started", """# Getting Started

## Installation

Steps to install the product...

## Quick Start

Quick start guide...

## Configuration

Configuration options...
"""),
    ("User Guide", """# User Guide

## Basic Features

Description of basic features...

## Advanced Features

Advanced functionality...

## Best Practices

Recommended practices...
"""),
    ("API Reference", """# API Reference

## Core API

Core API documentation...

## Authentication

Authentication methods...

## Examples

Code examples...
"""),
    ("Deployment", """# Deployment

## Development

Development environment setup...

## Staging

Staging deployment process...

## Production

Production deployment checklist...
""")
]

for name, content in sections:
    page = docs.create_page(
        workspace_id=workspace_id,
        doc_id=doc_id,
        name=name,
        content=content
    )
    print(f"Created: {name}")
```

### Subdirectory Pattern

Organize pages into logical subdirectories:

```python
# Create documentation structure
structure = {
    "README": "# Main Documentation\n\nWelcome to our documentation.",
    "getting-started/installation": "# Installation\n\nInstallation instructions...",
    "getting-started/quickstart": "# Quick Start\n\nQuick start guide...",
    "user-guide/basics": "# Basics\n\nBasic usage...",
    "user-guide/advanced": "# Advanced\n\nAdvanced features...",
    "api/reference": "# API Reference\n\nAPI documentation...",
    "api/examples": "# Examples\n\nCode examples..."
}

# Create doc
doc = docs.create_doc(workspace_id, "Complete Documentation")
doc_id = doc['id']

# Create pages organized by path
for path, content in structure.items():
    # Extract directory and filename
    parts = path.split('/')
    if len(parts) > 1:
        category = parts[0].replace('-', ' ').title()
        page_name = f"{category} - {parts[1].replace('-', ' ').title()}"
    else:
        page_name = parts[0].upper()

    page = docs.create_page(
        workspace_id=workspace_id,
        doc_id=doc_id,
        name=page_name,
        content=content
    )
    print(f"Created: {page_name}")
```

### Multi-Level Hierarchy

Create a deep hierarchy with parent-child relationships:

```python
# Level 1: Main doc
main_doc = docs.create_doc(workspace_id, "Engineering Documentation")
main_doc_id = main_doc['id']

# Level 2: Major sections
backend_content = """# Backend Documentation

This section contains all backend-related documentation.

## Contents
- Architecture
- API Design
- Database Schema
- Testing
"""

frontend_content = """# Frontend Documentation

This section contains all frontend-related documentation.

## Contents
- Components
- State Management
- Styling
- Testing
"""

# Create section pages
backend_page = docs.create_page(
    workspace_id, main_doc_id,
    "Backend", backend_content
)

frontend_page = docs.create_page(
    workspace_id, main_doc_id,
    "Frontend", frontend_content
)

# Level 3: Subsections
backend_topics = {
    "Architecture": "# Backend Architecture\n\nArchitecture overview...",
    "API Design": "# API Design\n\nAPI design principles...",
    "Database Schema": "# Database Schema\n\nDatabase structure...",
    "Testing": "# Backend Testing\n\nTesting strategies..."
}

for topic_name, topic_content in backend_topics.items():
    docs.create_page(
        workspace_id, main_doc_id,
        f"Backend - {topic_name}",
        topic_content
    )
```

## API Reference

### DocsAPI Class

```python
from clickup_framework.resources import DocsAPI

docs = DocsAPI(client)
```

#### Methods

##### `get_workspace_docs(workspace_id, **params)`
Get all docs in a workspace.

**Parameters:**
- `workspace_id` (str): Workspace/team ID
- `**params`: Additional query parameters

**Returns:** Dict with 'docs' list

##### `create_doc(workspace_id, name, parent_id=None, **doc_data)`
Create a new doc.

**Parameters:**
- `workspace_id` (str): Workspace/team ID
- `name` (str): Doc name
- `parent_id` (str, optional): Parent doc ID for nested docs
- `**doc_data`: Additional doc fields

**Returns:** Doc data dict

##### `get_doc(workspace_id, doc_id)`
Get doc by ID.

**Parameters:**
- `workspace_id` (str): Workspace/team ID
- `doc_id` (str): Doc ID

**Returns:** Doc data dict

##### `get_doc_pages(workspace_id, doc_id, **params)`
Get all pages in a doc.

**Parameters:**
- `workspace_id` (str): Workspace/team ID
- `doc_id` (str): Doc ID
- `**params`: Additional query parameters

**Returns:** List of page dicts

##### `create_page(workspace_id, doc_id, name, content=None, **page_data)`
Create a page in a doc.

**Parameters:**
- `workspace_id` (str): Workspace/team ID
- `doc_id` (str): Doc ID
- `name` (str): Page name
- `content` (str, optional): Page content (markdown)
- `**page_data`: Additional page fields

**Returns:** Page data dict

##### `get_page(workspace_id, doc_id, page_id)`
Get page by ID.

**Parameters:**
- `workspace_id` (str): Workspace/team ID
- `doc_id` (str): Doc ID
- `page_id` (str): Page ID

**Returns:** Page data dict

##### `update_page(workspace_id, doc_id, page_id, name=None, content=None, **updates)`
Update a page.

**Parameters:**
- `workspace_id` (str): Workspace/team ID
- `doc_id` (str): Doc ID
- `page_id` (str): Page ID
- `name` (str, optional): New page name
- `content` (str, optional): New content (markdown)
- `**updates`: Additional fields to update

**Returns:** Updated page data dict

##### `create_doc_with_pages(workspace_id, doc_name, pages, **doc_data)`
Create a doc with multiple pages in one call.

**Parameters:**
- `workspace_id` (str): Workspace/team ID
- `doc_name` (str): Doc name
- `pages` (list): List of dicts with 'name' and 'content' keys
- `**doc_data`: Additional doc fields

**Returns:** Dict with 'doc' and 'pages' data

## Markdown Formatting

### Supported Elements

The Docs API supports most standard markdown elements:

```markdown
# Heading 1
## Heading 2
### Heading 3
#### Heading 4

**Bold text**
*Italic text*
~~Strikethrough~~
`inline code`

- Bulleted list item 1
- Bulleted list item 2

1. Numbered list item 1
2. Numbered list item 2

[Link text](https://example.com)

\`\`\`python
# Code block
def hello():
    print("Hello, world!")
\`\`\`

> Blockquote text

| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |

---
Horizontal divider
```

### Limitations

**Not supported:**
- Alignment (center, right)
- Toggle lists
- Checklists
- Banners
- Embeds (YouTube, Vimeo, etc.)
- Advanced blocks (columns, synced content)
- Text/background colors
- Badges

**Partially supported:**
- Code blocks (formatting may be lost)
- Tables (formatting may be lost)
- Attachments (sizing not retained)

### Best Practices

1. **Use standard markdown** - Stick to common markdown syntax
2. **Test formatting** - Preview content in ClickUp to verify rendering
3. **Keep it simple** - Avoid complex nested structures
4. **Use headings** - Organize content with clear heading hierarchy
5. **Code blocks** - Use language tags for syntax highlighting

## Examples

### Complete Documentation Generator

See `create_model_config_manager_tasks.py` for a complete example of:
- Creating a doc with multiple pages
- Using proper multiline markdown strings
- Organizing content hierarchically
- Generating task definitions

### Simple Documentation Script

```python
#!/usr/bin/env python3
"""Simple documentation generator"""

import sys
sys.path.insert(0, '/home/user')

from clickup_framework import ClickUpClient
from clickup_framework.resources import DocsAPI

# Configuration
WORKSPACE_ID = "90151898946"

def main():
    client = ClickUpClient()
    docs = DocsAPI(client)

    # Create doc with pages
    result = docs.create_doc_with_pages(
        workspace_id=WORKSPACE_ID,
        doc_name="My Project Documentation",
        pages=[
            {
                "name": "Overview",
                "content": "# Project Overview\n\nProject description..."
            },
            {
                "name": "Setup",
                "content": "# Setup Instructions\n\nInstallation steps..."
            },
            {
                "name": "Usage",
                "content": "# Usage Guide\n\nHow to use the project..."
            }
        ]
    )

    print(f"Created doc: {result['doc']['id']}")
    print(f"Created {len(result['pages'])} pages")

if __name__ == '__main__':
    main()
```

## Troubleshooting

### Common Issues

**404 Not Found errors:**
- Ensure workspace_id is correct
- Verify doc_id and page_id exist
- Check that v3 endpoints are being used

**Markdown not rendering:**
- Use proper multiline strings (not escaped `\n`)
- Avoid unsupported markdown features
- Test content in ClickUp UI

**Permission errors:**
- Verify API token has Docs permissions
- Check workspace access rights
- Ensure you're using correct workspace_id

## Additional Resources

- [ClickUp Docs API Reference](https://developer.clickup.com/reference/searchdocspublic)
- [ClickUp Framework README](/home/user/clickup_framework/README.md)
- [Example Script](./create_model_config_manager_tasks.py)
