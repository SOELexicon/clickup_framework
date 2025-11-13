# Documentation Guide

This guide explains how to generate and maintain documentation for the ClickUp Framework.

## Overview

The project uses **MkDocs + mkdocstrings** to combine hand-written markdown documentation with auto-generated API documentation from Python docstrings.

## Quick Start

### 1. Install Documentation Dependencies

```bash
pip install -r requirements-docs.txt
```

### 2. Run Setup Script (First Time Only)

```bash
./scripts/setup_docs.sh
```

This creates:
- `mkdocs.yml` configuration file
- API reference pages in `docs/api/`
- Stub documentation if missing

### 3. Preview Documentation Locally

```bash
mkdocs serve
```

Open http://localhost:8000 in your browser.

### 4. Build Static Site

```bash
mkdocs build
```

Output will be in `site/` directory.

## Documentation Tools Comparison

### MkDocs + mkdocstrings (Current Choice)

**Pros:**
- ✅ Combines existing markdown with auto-generated API docs
- ✅ Beautiful Material Design theme
- ✅ Built-in search
- ✅ Easy to customize
- ✅ Live reload during development
- ✅ Markdown-based (easy to write)

**Install:**
```bash
pip install mkdocs mkdocs-material mkdocstrings[python]
```

**Usage:**
```bash
mkdocs serve  # Development server
mkdocs build  # Build static site
mkdocs gh-deploy  # Deploy to GitHub Pages
```

---

### pdoc (Alternative - Simplest)

**Pros:**
- ✅ Zero configuration
- ✅ Works immediately with existing docstrings
- ✅ Very lightweight

**Cons:**
- ❌ Limited customization
- ❌ No integration with existing markdown
- ❌ No search functionality

**Install:**
```bash
pip install pdoc
```

**Usage:**
```bash
pdoc clickup_framework --html --output-dir docs/api
pdoc clickup_framework --http :8080  # Live server
```

---

### Sphinx + autodoc (Alternative - Most Powerful)

**Pros:**
- ✅ Industry standard (Python, Django use it)
- ✅ Most powerful and feature-rich
- ✅ Multiple output formats (HTML, PDF, ePub)
- ✅ Extensive extension ecosystem

**Cons:**
- ❌ Steeper learning curve
- ❌ Uses reStructuredText (not Markdown)
- ❌ More complex configuration

**Install:**
```bash
pip install sphinx sphinx-rtd-theme sphinx-autodoc-typehints
```

**Usage:**
```bash
sphinx-quickstart docs/sphinx
sphinx-apidoc -o docs/sphinx/source clickup_framework
cd docs/sphinx && make html
```

---

## Documentation Structure

```
docs/
├── cli/                    # CLI command reference (manual)
│   ├── INDEX.md
│   ├── VIEW_COMMANDS.md
│   ├── TASK_COMMANDS.md
│   └── ...
├── api/                    # API reference (auto-generated)
│   ├── client.md
│   ├── cli.md
│   ├── commands/
│   └── components/
├── task_types/             # Task type templates
├── installation.md         # Installation guide
└── quickstart.md           # Quick start guide
```

## Writing Documentation

### Docstring Style

Use **Google-style docstrings** for consistency:

```python
def example_function(param1: str, param2: int) -> bool:
    """
    Brief description of what the function does.

    Detailed explanation of the function's behavior, including
    any important notes or caveats.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When something goes wrong

    Examples:
        >>> example_function("test", 42)
        True

    Changelog:
        2025-11-13: Added error handling for edge cases
                   - Prior attempt didn't handle None values
                   Issue: NoneType errors when param1 was None
                   Fix: Added None check at start
    """
    if param1 is None:
        raise ValueError("param1 cannot be None")
    return len(param1) > param2
```

### Markdown Documentation

Write clear, concise markdown with:
- Code examples
- Usage patterns
- Common workflows
- Tips and best practices

## Adding New API Documentation

### For a New Command

1. Create `docs/api/commands/your_command.md`:

```markdown
# Your Command

Brief description of the command.

::: clickup_framework.commands.your_command
    options:
      show_root_heading: true
      show_source: true
```

2. Add to `mkdocs.yml` navigation:

```yaml
nav:
  - API Reference:
      - Commands:
          - Your Command: api/commands/your_command.md
```

### For a New Component

1. Create `docs/api/components/your_component.md`:

```markdown
# Your Component

Brief description.

::: clickup_framework.components.your_component.YourClass
    options:
      show_root_heading: true
      show_source: true
```

2. Add to navigation in `mkdocs.yml`

## Deploying Documentation

### GitHub Pages

```bash
# Deploy to gh-pages branch
mkdocs gh-deploy

# With custom commit message
mkdocs gh-deploy -m "Update documentation"
```

Your docs will be available at: `https://yourusername.github.io/clickup_framework/`

### Other Hosting

Build static site and deploy anywhere:

```bash
mkdocs build
# Upload site/ directory to your hosting
```

## Customization

### Changing Theme Colors

Edit `mkdocs.yml`:

```yaml
theme:
  palette:
    primary: blue  # Change to your color
    accent: blue
```

### Adding Extensions

Add to `mkdocs.yml`:

```yaml
markdown_extensions:
  - your_extension
```

### Custom CSS

1. Create `docs/stylesheets/extra.css`
2. Add to `mkdocs.yml`:

```yaml
extra_css:
  - stylesheets/extra.css
```

## Maintenance

### Keeping Docs Updated

1. **Update docstrings** when changing code
2. **Run `mkdocs serve`** to preview changes
3. **Test links** and code examples
4. **Update changelog sections** in docstrings

### Documentation Checklist

When adding new features:

- [ ] Write/update docstrings in code
- [ ] Add examples to docstrings
- [ ] Update or create markdown guide
- [ ] Add to CLI reference if applicable
- [ ] Test documentation locally
- [ ] Deploy to GitHub Pages

## Troubleshooting

### Import Errors

If mkdocstrings can't import your module:

```bash
# Ensure package is installed in development mode
pip install -e .
```

### Missing Dependencies

```bash
# Reinstall docs requirements
pip install -r requirements-docs.txt --force-reinstall
```

### Build Warnings

Check for:
- Missing docstrings
- Broken internal links
- Invalid markdown syntax

Run with warnings as errors:

```bash
mkdocs build --strict
```

## Additional Resources

- [MkDocs Documentation](https://www.mkdocs.org/)
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
- [mkdocstrings Documentation](https://mkdocstrings.github.io/)
- [Google Style Python Docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)

## Alternative Tools Reference

If you want to try other tools:

### pdoc
```bash
pip install pdoc
pdoc clickup_framework --html --output-dir docs/api
```

### pydoc-markdown
```bash
pip install pydoc-markdown
pydoc-markdown -m clickup_framework > docs/api.md
```

### Sphinx
```bash
pip install sphinx sphinx-rtd-theme
sphinx-quickstart docs/sphinx
sphinx-apidoc -o docs/sphinx/source clickup_framework
cd docs/sphinx && make html
```
