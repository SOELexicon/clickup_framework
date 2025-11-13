#!/bin/bash
#
# setup_docs.sh
# Set up MkDocs with mkdocstrings for ClickUp Framework
#

set -e

echo "Setting up documentation system..."

# Install dependencies
echo "Installing MkDocs and plugins..."
pip install mkdocs mkdocs-material mkdocstrings[python]

# Create mkdocs.yml
echo "Creating mkdocs.yml configuration..."
cat > mkdocs.yml << 'EOF'
site_name: ClickUp Framework Documentation
site_description: Beautiful hierarchical task displays for ClickUp
site_author: ClickUp Framework Team
site_url: https://github.com/SOELexicon/clickup_framework

theme:
  name: material
  palette:
    - scheme: default
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode
    - scheme: slate
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-4
        name: Switch to light mode
  features:
    - navigation.tabs
    - navigation.sections
    - navigation.expand
    - navigation.top
    - toc.integrate
    - search.suggest
    - search.highlight
    - content.code.copy

plugins:
  - search
  - mkdocstrings:
      handlers:
        python:
          options:
            docstring_style: google
            show_source: true
            show_root_heading: true
            show_root_full_path: false
            show_signature_annotations: true
            separate_signature: true
            merge_init_into_class: true
            docstring_section_style: table

markdown_extensions:
  - pymdownx.highlight:
      anchor_linenums: true
  - pymdownx.superfences
  - pymdownx.inlinehilite
  - pymdownx.snippets
  - pymdownx.tabbed:
      alternate_style: true
  - admonition
  - pymdownx.details
  - pymdownx.emoji:
      emoji_index: !!python/name:material.extensions.emoji.twemoji
      emoji_generator: !!python/name:material.extensions.emoji.to_svg
  - tables
  - attr_list
  - md_in_html

nav:
  - Home: README.md
  - Getting Started:
      - Installation: docs/installation.md
      - Quick Start: docs/quickstart.md
  - CLI Reference:
      - Overview: docs/cli/INDEX.md
      - View Commands: docs/cli/VIEW_COMMANDS.md
      - Task Commands: docs/cli/TASK_COMMANDS.md
      - Comment Commands: docs/cli/COMMENT_COMMANDS.md
      - Docs Commands: docs/cli/DOC_COMMANDS.md
      - Context Commands: docs/cli/CONTEXT_COMMANDS.md
      - Config Commands: docs/cli/CONFIG_COMMANDS.md
      - Advanced Commands: docs/cli/ADVANCED_COMMANDS.md
  - API Reference:
      - Client: api/client.md
      - CLI: api/cli.md
      - Commands:
          - Overview: api/commands/index.md
          - Hierarchy: api/commands/hierarchy.md
          - Task Commands: api/commands/task_commands.md
          - Doc Commands: api/commands/doc_commands.md
      - Components:
          - Display: api/components/display.md
          - Hierarchy: api/components/hierarchy.md
          - Tree Formatter: api/components/tree.md
          - Task Formatter: api/components/task_formatter.md
  - Scripts:
      - Overview: scripts/README.md
      - Import CLI Docs: scripts/import_cli_docs.md
      - Test Failure Reporting: scripts/test_failures.md
  - Task Types: docs/task_types/README.md
EOF

# Create API reference pages
echo "Creating API reference pages..."
mkdir -p docs/api/commands docs/api/components

# Client API
cat > docs/api/client.md << 'EOF'
# ClickUp Client

The main ClickUpClient class for interacting with the ClickUp API.

::: clickup_framework.client.ClickUpClient
    options:
      show_root_heading: true
      show_source: true
EOF

# CLI
cat > docs/api/cli.md << 'EOF'
# CLI Module

Command-line interface entry point and argument parsing.

::: clickup_framework.cli
    options:
      show_root_heading: true
      show_source: true
EOF

# Commands
cat > docs/api/commands/index.md << 'EOF'
# Commands Overview

The commands module contains all CLI command implementations.

## Command Discovery

::: clickup_framework.commands
    options:
      show_root_heading: true
      members:
        - discover_commands
        - register_all_commands
EOF

cat > docs/api/commands/hierarchy.md << 'EOF'
# Hierarchy Command

Display tasks in hierarchical parent-child tree view.

::: clickup_framework.commands.hierarchy
    options:
      show_root_heading: true
      show_source: true
EOF

cat > docs/api/commands/task_commands.md << 'EOF'
# Task Commands

Commands for creating, updating, and managing tasks.

::: clickup_framework.commands.task_commands
    options:
      show_root_heading: true
      show_source: true
      members:
        - register_command
EOF

cat > docs/api/commands/doc_commands.md << 'EOF'
# Doc Commands

Commands for managing ClickUp Docs and pages.

::: clickup_framework.commands.doc_commands
    options:
      show_root_heading: true
      show_source: true
EOF

# Components
cat > docs/api/components/display.md << 'EOF'
# Display Manager

Main display management and formatting.

::: clickup_framework.components.display.DisplayManager
    options:
      show_root_heading: true
      show_source: true
EOF

cat > docs/api/components/hierarchy.md << 'EOF'
# Task Hierarchy

Task hierarchy organization and formatting.

::: clickup_framework.components.hierarchy.TaskHierarchyFormatter
    options:
      show_root_heading: true
      show_source: true
EOF

cat > docs/api/components/tree.md << 'EOF'
# Tree Formatter

Tree structure rendering with box-drawing characters.

::: clickup_framework.components.tree.TreeFormatter
    options:
      show_root_heading: true
      show_source: true
EOF

cat > docs/api/components/task_formatter.md << 'EOF'
# Task Formatter

Rich task formatting with colors and emojis.

::: clickup_framework.components.task_formatter.RichTaskFormatter
    options:
      show_root_heading: true
      show_source: true
EOF

# Create stub docs if missing
mkdir -p docs
if [ ! -f docs/installation.md ]; then
  cat > docs/installation.md << 'EOF'
# Installation

## From PyPI (Coming Soon)

```bash
pip install clickup-framework
```

## From Source

```bash
git clone https://github.com/SOELexicon/clickup_framework.git
cd clickup_framework
pip install -e .
```

## Configuration

Set your ClickUp API token:

```bash
export CLICKUP_API_TOKEN="your_token_here"
```

Or use the CLI:

```bash
cum set token "your_token_here"
```
EOF
fi

if [ ! -f docs/quickstart.md ]; then
  cat > docs/quickstart.md << 'EOF'
# Quick Start

## Basic Usage

### View Your Tasks

```bash
# Set context
cum set workspace YOUR_WORKSPACE_ID
cum set list YOUR_LIST_ID

# View tasks
cum hierarchy current
```

### Create a Task

```bash
cum task_create "New Task" --list current --priority high
```

### View Command Help

```bash
cum --help
cum hierarchy --help
```

## Common Workflows

See the [CLI Reference](cli/INDEX.md) for detailed command documentation.
EOF
fi

# Create helper script for API doc pages
cat > scripts/import_cli_docs.md << 'EOF'
# Import CLI Docs Script

See [scripts/README.md](../README.md#documentation-import) for full documentation.
EOF

cat > scripts/test_failures.md << 'EOF'
# Test Failure Reporting

See [scripts/README.md](../README.md#test-failure-reporting) for full documentation.
EOF

echo ""
echo "✓ Documentation system set up successfully!"
echo ""
echo "Next steps:"
echo "  1. Review and customize mkdocs.yml"
echo "  2. Run 'mkdocs serve' to preview locally at http://localhost:8000"
echo "  3. Run 'mkdocs build' to generate static site in site/"
echo "  4. Deploy with 'mkdocs gh-deploy' to GitHub Pages"
echo ""
echo "Quick commands:"
echo "  mkdocs serve    # Start development server"
echo "  mkdocs build    # Build static site"
echo "  mkdocs gh-deploy # Deploy to GitHub Pages"
echo ""
