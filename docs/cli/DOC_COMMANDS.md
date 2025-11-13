# Docs Management Commands

Commands for working with ClickUp Docs and pages.

**[← Back to Index](INDEX.md)**

---

## Commands Overview

| Command | Shortcode | Description |
|---------|-----------|-------------|
| [`dlist`](#dlist) | `dl` `doc_list` | List all docs in a workspace |
| [`doc_get`](#doc_get) | `dg` | Get and display a doc with pages |
| [`doc_create`](#doc_create) | `dc` | Create new doc with optional pages |
| [`doc_update`](#doc_update) | `du` | Update a page in a doc |
| [`doc_export`](#doc_export) | `de` | Export docs to markdown files |
| [`doc_import`](#doc_import) | `di` | Import markdown files to create docs |
| [`page_list`](#page_list) | `pl` | List all pages in a doc |
| [`page_create`](#page_create) | `pc` | Create a new page in a doc |
| [`page_update`](#page_update) | `pu` | Update a page in a doc |

---

## dlist

**Shortcodes:** `dl` `doc_list`

List all docs in a workspace.

### Usage

```bash
cum dlist <workspace_id>
cum dl <workspace_id>
cum doc_list <workspace_id>
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `workspace_id` | Yes | Workspace ID or `current` |

### Examples

```bash
# List all docs
cum dl 90151898946

# List docs in current workspace
cum dlist current

# Save list to file
cum dl current > docs_list.txt
```

[→ Full dlist command details](commands/dlist.md)

---

## doc_get

**Shortcode:** `dg`

Get a doc and display its pages.

### Usage

```bash
cum doc_get <workspace_id> <doc_id> [options]
cum dg <workspace_id> <doc_id> [options]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `workspace_id` | Yes | Workspace ID or `current` |
| `doc_id` | Yes | Doc ID |

### Options

| Option | Description |
|--------|-------------|
| `--preview` | Show preview mode |

### Examples

```bash
# Get doc details
cum dg 90151898946 abc123

# Get with preview
cum doc_get current abc123 --preview

# Pipe to pager
cum dg current abc123 | less
```

[→ Full doc_get command details](commands/doc_get.md)

---

## doc_create

**Shortcode:** `dc`

Create a new doc with optional pages.

### Usage

```bash
cum doc_create <workspace_id> <name> [options]
cum dc <workspace_id> <name> [options]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `workspace_id` | Yes | Workspace ID or `current` |
| `name` | Yes | Doc name |

### Options

| Option | Description |
|--------|-------------|
| `--pages "name:content" [...]` | Initial pages (format: "name:content") |

### Examples

```bash
# Create empty doc
cum dc current "API Documentation"

# Create doc with pages
cum dc current "Project Plan" \
  --pages "Overview:Project overview content" \
          "Timeline:Timeline content"

# Create from template
cum dc 90151898946 "Meeting Notes - $(date +%Y-%m-%d)"
```

[→ Full doc_create command details](commands/doc_create.md)

---

## doc_update

**Shortcode:** `du`

Update a page in a doc.

### Usage

```bash
cum doc_update <workspace_id> <doc_id> <page_id> [options]
cum du <workspace_id> <doc_id> <page_id> [options]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `workspace_id` | Yes | Workspace ID or `current` |
| `doc_id` | Yes | Doc ID |
| `page_id` | Yes | Page ID to update |

### Options

Format options available (see common options).

### Examples

```bash
# Update page
cum du current abc123 page456

# With custom options
cum doc_update current abc123 page456 --colorize
```

[→ Full doc_update command details](commands/doc_update.md)

---

## doc_export

**Shortcode:** `de`

Export docs to markdown files.

### Usage

```bash
cum doc_export <workspace_id> [options]
cum de <workspace_id> [options]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `workspace_id` | Yes | Workspace ID or `current` |

### Options

| Option | Description |
|--------|-------------|
| `--doc-id DOC_ID` | Export specific doc (omit to export all) |
| `--output-dir DIR` | Output directory (default: `./clickup_docs_export`) |
| `--nested` | Use nested directory structure |

### Examples

```bash
# Export all docs
cum de current --output-dir ./docs

# Export specific doc
cum doc_export current --doc-id abc123 --output-dir ./api_docs

# Export with nested structure
cum de 90151898946 --output-dir ./exports --nested

# Export to timestamped directory
cum de current --output-dir "./exports/$(date +%Y%m%d_%H%M%S)"
```

**Output structure:**
```
output-dir/
├── doc-name-1/
│   ├── page-1.md
│   ├── page-2.md
│   └── page-3.md
└── doc-name-2/
    ├── overview.md
    └── details.md
```

[→ Full doc_export command details](commands/doc_export.md)

---

## doc_import

**Shortcode:** `di`

Import markdown files to create docs.

### Usage

```bash
cum doc_import <workspace_id> <input_dir> [options]
cum di <workspace_id> <input_dir> [options]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `workspace_id` | Yes | Workspace ID or `current` |
| `input_dir` | Yes | Input directory with markdown files |

### Options

| Option | Description |
|--------|-------------|
| `--doc-name NAME` | Doc name (default: directory name) |
| `--nested` | Handle nested directory structure |

### Input Structure

```
input_dir/
├── page1.md
├── page2.md
└── page3.md
```

Or with `--nested`:
```
input_dir/
├── section1/
│   ├── page1.md
│   └── page2.md
└── section2/
    └── page3.md
```

### Examples

```bash
# Import markdown files
cum di current ./markdown_docs

# Import with custom doc name
cum doc_import current ./docs --doc-name "API Reference"

# Import nested structure
cum di 90151898946 ./nested_docs --nested

# Workflow: export, edit, re-import
cum de current --output-dir ./export
# Edit files...
cum di current ./export
```

[→ Full doc_import command details](commands/doc_import.md)

---

## page_list

**Shortcode:** `pl`

List all pages in a doc.

### Usage

```bash
cum page_list <workspace_id> <doc_id>
cum pl <workspace_id> <doc_id>
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `workspace_id` | Yes | Workspace ID or `current` |
| `doc_id` | Yes | Doc ID |

### Examples

```bash
# List pages
cum pl current abc123

# List and save
cum page_list 90151898946 abc123 > pages.txt
```

[→ Full page_list command details](commands/page_list.md)

---

## page_create

**Shortcode:** `pc`

Create a new page in a doc.

### Usage

```bash
cum page_create <workspace_id> <doc_id> --name <name> [options]
cum pc <workspace_id> <doc_id> --name <name> [options]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `workspace_id` | Yes | Workspace ID or `current` |
| `doc_id` | Yes | Doc ID |

### Options

| Option | Required | Description |
|--------|----------|-------------|
| `--name NAME` | Yes | Page name |
| `--content TEXT` | No | Page content |

### Examples

```bash
# Create empty page
cum pc current abc123 --name "New Page"

# Create page with content
cum page_create current abc123 \
  --name "Overview" \
  --content "# Overview

This document provides an overview of the project."

# Create multiple pages
for page in "Introduction" "Setup" "Usage" "FAQ"; do
  cum pc current abc123 --name "$page"
done
```

[→ Full page_create command details](commands/page_create.md)

---

## page_update

**Shortcode:** `pu`

Update a page in a doc.

### Usage

```bash
cum page_update <workspace_id> <doc_id> <page_id> [options]
cum pu <workspace_id> <doc_id> <page_id> [options]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `workspace_id` | Yes | Workspace ID or `current` |
| `doc_id` | Yes | Doc ID |
| `page_id` | Yes | Page ID |

### Options

| Option | Description |
|--------|-------------|
| `--name NAME` | New page name |
| `--content TEXT` | New page content |

### Examples

```bash
# Update page name
cum pu current abc123 page456 --name "Updated Title"

# Update page content
cum page_update current abc123 page456 \
  --content "# Updated Content

New content here."

# Update both
cum pu current abc123 page456 \
  --name "New Title" \
  --content "New content"
```

[→ Full page_update command details](commands/page_update.md)

---

## Common Workflows

### Create Documentation Set

```bash
# Set workspace context
cum set workspace 90151898946

# Create main doc
cum dc current "API Documentation"
# Returns doc ID: abc123

# Create pages
cum pc current abc123 --name "Overview"
cum pc current abc123 --name "Authentication"
cum pc current abc123 --name "Endpoints"
cum pc current abc123 --name "Examples"
cum pc current abc123 --name "FAQ"

# List pages to verify
cum pl current abc123
```

### Export, Edit, Re-import

```bash
# Export docs
cum de current --output-dir ./export

# Edit markdown files locally
vim ./export/api-docs/overview.md

# Re-import (creates new doc)
cum di current ./export
```

### Backup Workspace Docs

```bash
# Create timestamped backup
BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
cum de current --output-dir "$BACKUP_DIR" --nested

echo "Docs backed up to: $BACKUP_DIR"
```

### Migrate Docs Between Workspaces

```bash
# Export from source workspace
cum de 90151898946 --output-dir ./migration

# Import to target workspace
cum di 90151898947 ./migration --nested
```

### Create Meeting Notes Template

```bash
# Create template function
create_meeting_notes() {
  local date=$(date +%Y-%m-%d)
  local doc_name="Meeting Notes - $date"

  cum dc current "$doc_name" \
    --pages "Agenda:## Agenda
- Item 1
- Item 2" \
            "Notes:## Discussion Notes
" \
            "Action Items:## Action Items
- [ ] Item 1
- [ ] Item 2"
}

# Use it
create_meeting_notes
```

---

## Tips

1. **Export regularly:** Use `doc_export` for backups and version control
2. **Edit locally:** Export docs, edit in your favorite editor, re-import
3. **Nested structure:** Use `--nested` for complex documentation hierarchies
4. **Markdown support:** Full markdown formatting in page content
5. **Workspace context:** Set workspace once, use `current` everywhere
6. **Batch operations:** Use shell loops for bulk page creation

---

## Doc Management Best Practices

1. **Organize docs by project:** One doc per project or feature area
2. **Use consistent naming:** Follow a naming convention for docs and pages
3. **Regular exports:** Schedule automatic exports for backup
4. **Version control:** Store exported docs in git for history tracking
5. **Templates:** Create reusable templates with `doc_create --pages`

---

**Navigation:**
- [← Back to Index](INDEX.md)
- [← Comment Commands](COMMENT_COMMANDS.md)
- [Context Commands →](CONTEXT_COMMANDS.md)
