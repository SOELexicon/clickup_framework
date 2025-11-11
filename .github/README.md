# GitHub Configuration Files

This directory contains configuration and guidance files for GitHub integrations.

## Files

### `copilot-instructions.md` - Comprehensive Copilot Guide
Full custom instructions for GitHub Copilot when working on this project. This file contains:

- Complete project architecture overview
- Coding standards and conventions
- API interaction patterns (pagination, error handling)
- Testing requirements and examples
- Documentation standards (docstrings, comments)
- Display and formatting guidelines
- Common utilities and patterns
- MCP server patterns
- Git workflow conventions
- Code review checklist
- Quick reference with code snippets

**Use this file** when you need detailed guidance on any aspect of the codebase.

### `copilot-settings.md` - Short Version for GitHub Settings
Condensed version optimized for GitHub Copilot's custom instructions field (which has character limits).

**How to use:**
1. Go to your GitHub account settings
2. Navigate to Copilot settings
3. Find "Custom instructions" section
4. Copy the content from `copilot-settings.md`
5. Paste into the custom instructions field

This gives Copilot essential context about:
- Critical patterns (pagination, error handling)
- Command structure
- Testing requirements
- Code standards
- Quick reference snippets

### Setting Up GitHub Copilot

#### Option 1: Repository-Level (Recommended)
GitHub Copilot automatically reads `.github/copilot-instructions.md` if it exists in the repository. Just keep this file in place and Copilot will use it when working in this repo.

#### Option 2: Personal Settings
For additional context or if working across multiple repos, add the content from `copilot-settings.md` to your personal GitHub Copilot settings:

1. GitHub.com → Settings → Copilot
2. Scroll to "Custom instructions"
3. Paste the content from `copilot-settings.md`

#### Option 3: VS Code
If using VS Code with GitHub Copilot extension:

1. Open VS Code settings (Cmd/Ctrl + ,)
2. Search for "Copilot"
3. Look for "GitHub Copilot: Instructions" or similar
4. Add content from `copilot-settings.md`

### Tips for Best Results

1. **Reference the full instructions**: When working on complex features, review `copilot-instructions.md` first to understand patterns.

2. **Update as needed**: If you introduce new patterns or conventions, update both files to keep Copilot informed.

3. **Use comments**: Add comments in your code referencing specific patterns:
   ```python
   # Using pagination pattern from copilot-instructions.md
   tasks = _fetch_all_pages(...)
   ```

4. **Test suggestions**: Always review and test Copilot's suggestions - it's a helpful assistant, not a replacement for code review.

5. **Share knowledge**: If Copilot suggests something better than our current pattern, consider updating the codebase and these instructions.

### Maintaining These Files

When updating:
- **Full guide** (`copilot-instructions.md`): Add detailed explanations, more examples, comprehensive patterns
- **Short version** (`copilot-settings.md`): Keep concise, update only critical changes
- **Keep in sync**: Ensure both files have consistent information (just different detail levels)

### Why Two Files?

- **Long form**: Complete reference, better for Copilot when it has access to repository context
- **Short form**: Fits in GitHub's character-limited settings, portable across repos

---

## Other GitHub Files (Future)

This directory can also contain:
- GitHub Actions workflows (`.github/workflows/`)
- Issue templates (`.github/ISSUE_TEMPLATE/`)
- Pull request templates (`.github/pull_request_template.md`)
- Contributing guidelines (`.github/CONTRIBUTING.md`)
- Code of conduct (`.github/CODE_OF_CONDUCT.md`)
- Security policy (`.github/SECURITY.md`)
