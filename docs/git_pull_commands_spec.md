# Git Pull Commands Specification

## Overview
Add two new CLI commands to the ClickUp Framework for Git repository management:
1. `cum pull` - Execute `git pull --rebase` in the current repository
2. `cum suck` - Execute `git pull --rebase` recursively on all Git repositories found within the project folder

## Command 1: `cum pull`

### Purpose
Execute `git pull --rebase` in the current working directory's Git repository.

### Behavior
- Checks if current directory is a Git repository (has `.git` folder)
- If not a Git repo, displays error and exits
- Executes `git pull --rebase`
- Displays output to user
- Returns appropriate exit code based on Git command result

### Usage
```bash
cum pull
```

### Implementation Details
- **File**: `clickup_framework/commands/git_pull_command.py`
- **Function**: `pull_command(args)`
- **Registration**: `register_command(subparsers)`

### Error Handling
- If not in a Git repository: Display clear error message
- If Git command fails: Display Git error output and exit with non-zero code
- Handle network errors gracefully

### Output
- Show Git command output in real-time
- Display success/failure status
- Use consistent formatting with other CLI commands

---

## Command 2: `cum suck`

### Purpose
Recursively find all Git repositories within the current project folder and execute `git pull --rebase` on each one.

### Behavior
1. Start from current working directory
2. Recursively search for all `.git` folders (or directories containing `.git`)
3. For each Git repository found:
   - Display repository path/name
   - Execute `git pull --rebase` in that directory
   - Display results
4. Provide summary of all operations

### Usage
```bash
cum suck
```

### Implementation Details
- **File**: `clickup_framework/commands/git_suck_command.py`
- **Function**: `suck_command(args)`
- **Registration**: `register_command(subparsers)`

### Repository Discovery
- Use `pathlib.Path` to walk directory tree
- Look for `.git` directories (not files)
- Skip common directories that shouldn't be searched:
  - `node_modules/`
  - `.venv/`, `venv/`, `env/`
  - `__pycache__/`
  - `.git/` (don't search inside other repos)
- Optionally respect `.gitignore` patterns

### Error Handling
- If no Git repositories found: Display informative message
- If a repository pull fails: Continue with other repositories
- Collect and display summary of successes/failures
- Handle permission errors gracefully

### Output Format
```
🔍 Searching for Git repositories...
📁 Found 3 repositories:

1. /path/to/repo1
   ✅ Pull successful

2. /path/to/repo2
   ⚠️  Pull failed: [error message]

3. /path/to/repo3
   ✅ Pull successful

Summary: 2 successful, 1 failed
```

### Options (Future Enhancement)
- `--dry-run`: Show what would be pulled without executing
- `--exclude <pattern>`: Exclude repositories matching pattern
- `--max-depth <n>`: Limit search depth

---

## Technical Implementation

### Common Patterns
Both commands should:
- Use `subprocess.run()` for Git commands (consistent with existing codebase)
- Follow the command registration pattern from `commands/__init__.py`
- Use consistent error handling and output formatting
- Support Windows and Unix paths
- Handle encoding issues (UTF-8)

### Dependencies
- `subprocess` (standard library)
- `pathlib` (standard library)
- `os` (standard library)

### Testing Requirements
1. Test `cum pull` in a Git repository
2. Test `cum pull` outside a Git repository (error case)
3. Test `cum pull` with network failure simulation
4. Test `cum suck` with multiple repositories
5. Test `cum suck` with no repositories found
6. Test `cum suck` with nested repositories
7. Test `cum suck` skipping common directories

### Code Structure

#### `git_pull_command.py`
```python
"""Git pull command - Execute git pull --rebase in current repository."""

import subprocess
import sys
from pathlib import Path


def pull_command(args):
    """Execute git pull --rebase in current directory."""
    # Check if in Git repo
    # Execute git pull --rebase
    # Display results
    pass


def register_command(subparsers):
    """Register the pull command."""
    parser = subparsers.add_parser(
        'pull',
        help='Execute git pull --rebase',
        description='Pull latest changes with rebase in current Git repository'
    )
    parser.set_defaults(func=pull_command)
```

#### `git_suck_command.py`
```python
"""Git suck command - Pull all repositories in project folder."""

import subprocess
import sys
from pathlib import Path


def find_git_repositories(root_path):
    """Recursively find all Git repositories."""
    # Walk directory tree
    # Find .git directories
    # Return list of repository paths
    pass


def suck_command(args):
    """Pull all Git repositories in project folder."""
    # Find all repos
    # Execute pull on each
    # Display summary
    pass


def register_command(subparsers):
    """Register the suck command."""
    parser = subparsers.add_parser(
        'suck',
        help='Pull all Git repositories in project folder',
        description='Recursively find and pull all Git repositories'
    )
    parser.set_defaults(func=suck_command)
```

---

## Integration Points

### Command Discovery
- Commands will be auto-discovered by `commands/__init__.py`
- No manual registration needed in `cli.py`

### Help System
- Commands will appear in `cum --help`
- Will be categorized appropriately in command tree

### Error Codes
- Return 0 on success
- Return 1 on failure
- Use `sys.exit()` for proper exit codes

---

## Future Enhancements

### Phase 2 Features
- `--verbose` flag for detailed output
- `--quiet` flag for minimal output
- `--parallel` flag for `cum suck` to pull repos in parallel
- Configuration file for excluded directories
- Progress indicators for long operations

### Phase 3 Features
- Integration with ClickUp tasks (track which repos are updated)
- Git status reporting before pull
- Conflict detection and reporting
- Branch tracking and switching

---

## Documentation Updates

### CLI Reference
- Add commands to `CLI_COMMAND_REFERENCE.md`
- Add to `.claude/commands/cum.md`
- Update help text in command tree

### User Documentation
- Add usage examples to main README
- Document in workflow documentation
- Add to quick reference guide

---

## Acceptance Criteria

- [ ] `cum pull` executes `git pull --rebase` successfully
- [ ] `cum pull` shows appropriate error when not in Git repo
- [ ] `cum suck` finds all Git repositories recursively
- [ ] `cum suck` executes pull on each repository
- [ ] `cum suck` provides clear summary of results
- [ ] Both commands handle errors gracefully
- [ ] Both commands follow existing code style
- [ ] Tests pass for all scenarios
- [ ] Documentation updated
- [ ] Commands appear in help system

