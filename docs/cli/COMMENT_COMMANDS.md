# Comment Management Commands

Commands for adding and managing comments on tasks.

**[← Back to Index](INDEX.md)**

---

## Commands Overview

| Command | Shortcode | Description |
|---------|-----------|-------------|
| [`comment_add`](#comment_add) | `ca` | Add a comment to a task |
| [`comment_list`](#comment_list) | `cl` | List comments on a task |
| [`comment_update`](#comment_update) | `cu` | Update an existing comment |
| [`comment_delete`](#comment_delete) | `cd` | Delete a comment |

---

## comment_add

**Shortcode:** `ca`

Add a comment to a task.

### Usage

```bash
cum comment_add <task_id> <text>
cum comment_add <task_id> --comment-file <path>
cum ca <task_id> <text>
cum ca <task_id> --comment-file <path>
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `task_id` | Yes | Task ID or `current` |
| `text` | Conditional | Comment text (required unless --comment-file is used) |

### Options

| Option | Description |
|--------|-------------|
| `--comment-file PATH` | Read comment text from file |

**Note:** `text` argument and `--comment-file` option are mutually exclusive.

### Examples

```bash
# Add comment with text
cum ca 86c6xyz "Great work on this!"

# Add comment from file
cum comment_add 86c6xyz --comment-file notes.txt

# Add to current task
cum ca current "Initial thoughts"

# Multi-line comment from file
echo "Line 1
Line 2
Line 3" > comment.txt
cum ca current --comment-file comment.txt

# Add markdown comment
cum ca 86c6xyz "## Status Update

- Completed API integration
- Updated tests
- Ready for review"
```

**Tip:** Use `--comment-file` for longer comments or when working with formatted text.

[→ Full comment_add command details](commands/comment_add.md)

---

## comment_list

**Shortcode:** `cl`

List all comments on a task.

### Usage

```bash
cum comment_list <task_id> [options]
cum cl <task_id> [options]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `task_id` | Yes | Task ID or `current` |

### Options

| Option | Description |
|--------|-------------|
| `--limit N` | Limit to N most recent comments |

### Output Format

Each comment displays:
- Comment ID
- Author name
- Timestamp (created/updated)
- Comment text

### Examples

```bash
# List all comments
cum cl 86c6xyz

# List comments on current task
cum comment_list current

# Limit to 5 most recent
cum cl 86c6xyz --limit 5

# List for review
cum cl current | less
```

**Tip:** Use `--limit` to reduce output when tasks have many comments.

[→ Full comment_list command details](commands/comment_list.md)

---

## comment_update

**Shortcode:** `cu`

Update an existing comment.

### Usage

```bash
cum comment_update <comment_id> <text>
cum comment_update <comment_id> --comment-file <path>
cum cu <comment_id> <text>
cum cu <comment_id> --comment-file <path>
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `comment_id` | Yes | Comment ID (get from `comment_list`) |
| `text` | Conditional | New comment text (required unless --comment-file is used) |

### Options

| Option | Description |
|--------|-------------|
| `--comment-file PATH` | Read new comment text from file |

**Note:** `text` argument and `--comment-file` option are mutually exclusive.

### Examples

```bash
# Update comment with text
cum cu 123456789 "Updated comment text"

# Update from file
cum comment_update 123456789 --comment-file updated_notes.txt

# Fix typo in comment
cum cu 123456789 "Corrected spelling and grammar"
```

**Note:** You need the comment ID from `comment_list` to update a comment.

[→ Full comment_update command details](commands/comment_update.md)

---

## comment_delete

**Shortcode:** `cd`

Delete a comment.

### Usage

```bash
cum comment_delete <comment_id> [options]
cum cd <comment_id> [options]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `comment_id` | Yes | Comment ID (get from `comment_list`) |

### Options

| Option | Description |
|--------|-------------|
| `--force` | Skip confirmation prompt |

### Examples

```bash
# Delete with confirmation
cum cd 123456789

# Delete without confirmation
cum comment_delete 123456789 --force

# Workflow: list, then delete
cum cl 86c6xyz
cum cd 123456789
```

**Warning:** Deletion is permanent and cannot be undone!

[→ Full comment_delete command details](commands/comment_delete.md)

---

## Common Workflows

### Add Status Update Comments

```bash
# Quick status update
cum ca current "Status: In progress. ETA: tomorrow"

# Detailed status from file
cat > status.txt << EOF
## Status Update - $(date +%Y-%m-%d)

### Completed:
- API integration
- Unit tests

### In Progress:
- Integration tests
- Documentation

### Blockers:
- Waiting on API key from DevOps
EOF

cum ca current --comment-file status.txt
```

### Review and Clean Up Comments

```bash
# List comments
cum cl 86c6xyz

# Output:
# [1] 123456789 - John Doe (2024-01-15): "Old comment"
# [2] 123456790 - Jane Doe (2024-01-16): "Keep this"

# Delete old comment
cum cd 123456789 --force
```

### Update Comment After Review

```bash
# Original comment
cum ca 86c6xyz "Initial analysis shows performance issue"

# List to get comment ID
cum cl 86c6xyz
# Get ID: 123456789

# Update after investigation
cum cu 123456789 "Root cause identified: N+1 query in user endpoint. Fix PR #123"
```

### Batch Comment on Multiple Tasks

```bash
# Add same comment to multiple tasks
for task in 86c6xyz 86c6abc 86c6def; do
  cum ca $task "Sprint review: approved for deployment"
done
```

---

## Tips

1. **Use files for long comments:** `--comment-file` is better for detailed updates
2. **Get comment IDs:** Use `cum cl <task_id>` to see comment IDs before updating/deleting
3. **Markdown support:** Comments support markdown formatting
4. **Status updates:** Use comments for status updates that don't warrant task field changes
5. **Context workflow:** Set current task, then use `cum ca current "..."`

---

## Comment vs Task Updates

**Use comments for:**
- Status updates and progress notes
- Discussion and collaboration
- Temporary information
- Review feedback
- Investigation notes

**Use task updates for:**
- Changing task status, priority, or assignees
- Updating task description
- Modifying core task properties

---

**Navigation:**
- [← Back to Index](INDEX.md)
- [← Task Commands](TASK_COMMANDS.md)
- [Docs Commands →](DOC_COMMANDS.md)
