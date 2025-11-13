# Configuration Commands

Commands for configuring CLI behavior and settings.

**[← Back to Index](INDEX.md)**

---

## Commands Overview

| Command | Shortcode | Description |
|---------|-----------|-------------|
| [`ansi`](#ansi) | - | Enable/disable ANSI color output |
| [`update`](#update) | - | Update cum tool or bump version |

---

## ansi

Configure ANSI color output.

### Usage

```bash
cum ansi <action>
```

### Actions

| Action | Description |
|--------|-------------|
| `enable` | Enable ANSI color output |
| `disable` | Disable ANSI color output |
| `status` | Show current ANSI setting |

### Configuration Storage

Setting is stored in `~/.clickup_context.json`:
```json
{
  "ansi_enabled": true
}
```

### Examples

```bash
# Enable colors
cum ansi enable

# Disable colors
cum ansi disable

# Check status
cum ansi status

# Sample output:
# ANSI color output is: enabled
```

### When to Use

**Enable colors when:**
- Using modern terminal (iTerm2, Terminal.app, Windows Terminal)
- Terminal supports 256 colors
- Want visual distinction between statuses/priorities

**Disable colors when:**
- Piping output to files or other commands
- Using basic terminals without color support
- Terminal color rendering issues
- Accessibility requirements

### Override with Command Options

Even with ANSI disabled in config, you can force colors per-command:

```bash
# ANSI disabled globally
cum ansi disable

# Force colorize for one command
cum hierarchy current --colorize

# Force disable for one command
cum ansi enable
cum hierarchy current --no-colorize
```

### Examples

```bash
# Enable for interactive use
cum ansi enable
cum h current

# Disable for scripting
cum ansi disable
cum h current > tasks.txt

# Check status before piping
cum ansi status
cum h current | grep "TODO"
```

[→ Full ansi command details](commands/ansi.md)

---

## update

Update cum tool components or bump version.

### Usage

```bash
cum update <subcommand> [options]
```

### Subcommands

#### 1. update cum

Update cum tool from git and reinstall.

```bash
cum update cum
```

**What it does:**
1. Fetches latest changes from git repository
2. Pulls latest code
3. Reinstalls package with pip

**Example:**
```bash
# Update to latest version
cum update cum

# Typical output:
# Fetching latest changes...
# Already up to date.
# Reinstalling cum tool...
# Successfully installed clickup-framework-1.2.3
```

**Requirements:**
- Must be in a git repository
- Must have write access to installation directory
- Pip must be available

---

#### 2. update version

Bump project version and create git tag.

```bash
cum update version [--major|--minor|--patch] [VERSION]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--major` | Bump major version (1.0.0 → 2.0.0) |
| `--minor` | Bump minor version (1.0.0 → 1.1.0) |
| `--patch` | Bump patch version (1.0.0 → 1.0.1) |
| `VERSION` | Set specific version (e.g., "2.0.0") |

**What it does:**
1. Updates version in `setup.py` or `pyproject.toml`
2. Creates git commit with version change
3. Creates git tag with version number
4. Optionally pushes to remote

**Examples:**

```bash
# Bump patch version (1.0.0 → 1.0.1)
cum update version --patch

# Bump minor version (1.0.0 → 1.1.0)
cum update version --minor

# Bump major version (1.0.0 → 2.0.0)
cum update version --major

# Set specific version
cum update version 2.5.3

# Check current version first
cum --version
# Output: cum 1.2.3

# Bump and verify
cum update version --minor
cum --version
# Output: cum 1.3.0
```

**Semantic Versioning:**

Follow semantic versioning (semver) guidelines:

- **Major (X.0.0):** Breaking changes, incompatible API changes
- **Minor (x.Y.0):** New features, backwards-compatible
- **Patch (x.y.Z):** Bug fixes, backwards-compatible

**Git workflow:**

```bash
# Make changes
git add .
git commit -m "feat: new feature"

# Bump version
cum update version --minor

# Push with tags
git push origin main --tags
```

[→ Full update command details](commands/update.md)

---

## Common Workflows

### Initial Configuration

```bash
# Enable ANSI colors
cum ansi enable

# Set API token
cum set token "pk_your_token"

# Set workspace and defaults
cum set workspace 90151898946
cum set list 901517404278
cum set assignee 68483025

# Verify configuration
cum show
cum ansi status
```

### Development Workflow

```bash
# Check current version
cum --version

# Make changes to code
# ... coding ...

# Test changes
cum demo

# Commit changes
git add .
git commit -m "feat: add new feature"

# Bump version
cum update version --minor

# Push with tags
git push origin main --tags

# Update installation
cum update cum
```

### Updating Cum Tool

```bash
# Check current version
cum --version
# Output: cum 1.2.3

# Update to latest
cum update cum

# Verify new version
cum --version
# Output: cum 1.3.0

# Test updated features
cum h current
```

### Release Workflow

```bash
# Complete feature
git add .
git commit -m "feat: major feature"

# Create release
cum update version --minor

# Tag created: v1.3.0

# Push release
git push origin main
git push origin v1.3.0

# Or push all tags
git push origin main --tags
```

### Color Configuration by Environment

```bash
# .bashrc or .zshrc

# Enable colors for interactive shells
if [ -t 1 ]; then
  cum ansi enable
fi

# Disable colors for pipes/redirects
# (automatically handled by --colorize flags)
```

---

## Configuration Files

### Context File

**Location:** `~/.clickup_context.json`

**Contents:**
```json
{
  "workspace_id": "90151898946",
  "list_id": "901517404278",
  "task_id": null,
  "assignee_id": "68483025",
  "api_token": "pk_...",
  "space_id": null,
  "folder_id": null,
  "ansi_enabled": true,
  "last_updated": "2024-01-15T10:30:45.123456"
}
```

**Permissions:**
```bash
chmod 600 ~/.clickup_context.json
```

---

### Version File

**Location:** `setup.py` or `pyproject.toml`

**setup.py example:**
```python
setup(
    name="clickup-framework",
    version="1.2.3",
    ...
)
```

**pyproject.toml example:**
```toml
[project]
name = "clickup-framework"
version = "1.2.3"
```

---

## Tips

1. **Enable colors:** Better visual experience for interactive use
2. **Disable for scripts:** Cleaner output when piping to files
3. **Update regularly:** Keep cum tool up to date with `cum update cum`
4. **Semantic versioning:** Follow semver for version bumps
5. **Tag releases:** Use `cum update version` to create version tags
6. **Check version:** Run `cum --version` to see current version
7. **Test after update:** Run `cum demo` to verify installation

---

## Troubleshooting

### Colors not showing

```bash
# Check ANSI status
cum ansi status

# Enable if disabled
cum ansi enable

# Force colorize for command
cum h current --colorize

# Check terminal support
echo $TERM
# Should show: xterm-256color or similar
```

### Update fails

```bash
# Ensure in git repo
git status

# Check remote
git remote -v

# Manual update
git pull origin main
pip install -e . --force-reinstall
```

### Version bump fails

```bash
# Check git status
git status

# Ensure clean working directory
git add .
git commit -m "commit message"

# Try version bump again
cum update version --minor
```

---

## Environment Variables

### CLICKUP_API_TOKEN

```bash
# Set in shell
export CLICKUP_API_TOKEN="pk_your_token"

# Add to .bashrc or .zshrc
echo 'export CLICKUP_API_TOKEN="pk_your_token"' >> ~/.bashrc

# Precedence
# 1. Environment variable
# 2. Context file (~/.clickup_context.json)
# 3. Prompt for token
```

### NO_COLOR

Standard environment variable to disable colors:

```bash
# Disable colors globally
export NO_COLOR=1

# Run command
cum h current
# Colors automatically disabled
```

---

**Navigation:**
- [← Back to Index](INDEX.md)
- [← Context Commands](CONTEXT_COMMANDS.md)
- [Advanced Commands →](ADVANCED_COMMANDS.md)
