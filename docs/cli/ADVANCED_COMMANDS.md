# Advanced Commands

Advanced functionality including checklists, custom fields, automation, and workflows.

**[← Back to Index](INDEX.md)**

---

## Features Overview

| Feature | Commands | Description |
|---------|----------|-------------|
| [Checklist Management](#checklist-management) | `checklist` (`chk`) | Manage checklists on tasks |
| [Custom Fields](#custom-fields) | `custom-field` (`cf`) | Manage custom fields on tasks |
| [Parent Auto-Update](#parent-auto-update) | `parent_auto_update` (`pau`) | Auto-update parent task automation |
| [Git Overflow](#git-overflow) | `overflow` | Automated Git + ClickUp workflow |
| [Space Management](#space-management) | `space` (`sp`, `spc`) | Create, update, delete spaces |
| [Folder Management](#folder-management) | `folder` (`fld`, `fd`) | Create, update, delete folders |
| [List Management](#list-management) | `list-mgmt` (`lm`) | Create, update, delete lists |

---

## Checklist Management

**Command:** `checklist` **Shortcode:** `chk`

Manage checklists on tasks including templates and cloning.

### Subcommands

#### checklist create

Create a checklist on a task.

```bash
cum checklist create --task-id <task_id> --name <name> [options]
cum chk create --task-id <task_id> --name <name> [options]
```

**Options:**
- `--task-id TASK_ID` - Task ID or `current`
- `--name NAME` - Checklist name
- `--verbose` - Verbose output

**Example:**
```bash
cum chk create --task-id current --name "Pre-deployment Checklist"
```

---

#### checklist delete

Delete a checklist.

```bash
cum checklist delete --checklist-id <checklist_id> [options]
cum chk delete --checklist-id <checklist_id> [options]
cum chk rm --checklist-id <checklist_id> [options]
```

**Options:**
- `--checklist-id ID` - Checklist ID
- `--force` - Skip confirmation

**Example:**
```bash
cum chk rm --checklist-id 123456 --force
```

---

#### checklist update

Update checklist properties.

```bash
cum checklist update --checklist-id <id> [options]
cum chk update --checklist-id <id> [options]
```

**Options:**
- `--checklist-id ID` - Checklist ID
- `--name NAME` - New name
- `--position N` - New position

**Example:**
```bash
cum chk update --checklist-id 123456 --name "Updated Checklist"
```

---

#### checklist item-add

Add item to checklist.

```bash
cum checklist item-add --checklist-id <id> --name <name>
cum chk add --checklist-id <id> --name <name>
```

**Example:**
```bash
cum chk add --checklist-id 123456 --name "Run tests"
```

---

#### checklist item-update

Update checklist item.

```bash
cum checklist item-update --item-id <id> [options]
cum chk update-item --item-id <id> [options]
```

**Example:**
```bash
cum chk update-item --item-id 789 --name "Updated item"
```

---

#### checklist item-delete

Delete checklist item.

```bash
cum checklist item-delete --item-id <id>
cum chk delete-item --item-id <id>
cum chk rm-item --item-id <id>
```

**Example:**
```bash
cum chk rm-item --item-id 789
```

---

### Checklist Templates

**Feature:** Save and reuse checklists across tasks.

**Usage in task creation:**
```bash
# Apply template when creating task
cum tc current "Deploy to production" --checklist-template "deployment"

# Clone from existing task
cum tc current "Similar task" --clone-checklists-from 86c6xyz
```

**Template storage:** Templates are stored locally in `~/.clickup_checklist_templates.json`

**Example workflow:**
```bash
# Create task with checklist template
cum tc current "Deploy v1.2.3" --checklist-template "deployment-checklist"

# Task is created with pre-filled checklist:
# ☐ Run tests
# ☐ Update version
# ☐ Build artifacts
# ☐ Deploy to staging
# ☐ Run smoke tests
# ☐ Deploy to production
# ☐ Verify deployment
# ☐ Update documentation
```

[→ Full checklist documentation](commands/checklist.md)

---

## Custom Fields

**Command:** `custom-field` **Shortcode:** `cf`

Manage custom fields on tasks.

### Subcommands

#### custom_field get

Get custom field value from a task.

```bash
cum custom-field get <task_id> <field_name>
cum cf get <task_id> <field_name>
```

**Example:**
```bash
cum cf get 86c6xyz "Story Points"
```

---

#### custom_field set

Set custom field value on a task.

```bash
cum custom-field set <task_id> <field_name> <value>
cum cf set <task_id> <field_name> <value>
```

**Example:**
```bash
cum cf set 86c6xyz "Story Points" 5
cum cf set current "Priority Score" 8
cum cf set 86c6xyz "Environment" "production"
```

---

#### custom_field delete

Delete/clear custom field value.

```bash
cum custom-field delete <task_id> <field_name>
cum cf delete <task_id> <field_name>
cum cf rm <task_id> <field_name>
```

**Example:**
```bash
cum cf rm 86c6xyz "Story Points"
```

---

### Custom Field Types

ClickUp supports various custom field types:
- **Text:** Free-form text
- **Number:** Numeric values
- **Dropdown:** Pre-defined options
- **Date:** Date values
- **Checkbox:** Boolean values
- **URL:** Link values
- **Email:** Email addresses
- **Phone:** Phone numbers
- **Currency:** Monetary values
- **Progress:** Percentage values

**Example usage:**
```bash
# Number field
cum cf set current "Story Points" 5

# Dropdown field
cum cf set current "Priority" "High"

# Date field
cum cf set current "Due Date" "2024-01-31"

# Checkbox field
cum cf set current "Approved" true

# URL field
cum cf set current "Documentation" "https://docs.example.com"
```

[→ Full custom field documentation](commands/custom_field.md)

---

## Parent Auto-Update

**Command:** `parent_auto_update` **Shortcode:** `pau`

Automate parent task status updates based on subtask completion.

### Subcommands

#### parent_auto_update status

Show automation configuration.

```bash
cum parent_auto_update status
cum pau status
```

**Output:**
- Enabled/disabled status
- Configured triggers
- Update rules

---

#### parent_auto_update enable

Enable automation.

```bash
cum parent_auto_update enable
cum pau enable
```

---

#### parent_auto_update disable

Disable automation.

```bash
cum parent_auto_update disable
cum pau disable
```

---

#### parent_auto_update config

Update configuration.

```bash
cum parent_auto_update config --key <key> --value <value>
cum pau config --key <key> --value <value>
```

**Example:**
```bash
cum pau config --key "auto_close" --value "true"
```

---

#### parent_auto_update add-trigger

Add status trigger.

```bash
cum parent_auto_update add-trigger <status>
cum pau add-trigger <status>
```

**Example:**
```bash
cum pau add-trigger "done"
cum pau add-trigger "closed"
```

---

#### parent_auto_update remove-trigger

Remove status trigger.

```bash
cum parent_auto_update remove-trigger <status>
cum pau remove-trigger <status>
```

---

### How It Works

When enabled, the automation:
1. Monitors subtask status changes
2. Checks if trigger conditions are met
3. Automatically updates parent task status
4. Logs the automation action

**Use case:**
- Automatically close parent task when all subtasks are done
- Update parent status when critical subtasks complete
- Cascade status changes up the hierarchy

**Example workflow:**
```bash
# Enable automation
cum pau enable

# Add triggers
cum pau add-trigger "done"
cum pau add-trigger "closed"

# Create parent with subtasks
cum tc current "Feature Implementation"
# Returns: 86c6parent

cum tc "Backend API" --parent 86c6parent
cum tc "Frontend UI" --parent 86c6parent
cum tc "Tests" --parent 86c6parent

# As subtasks complete, parent updates automatically
cum tss 86c6sub1 "done"  # 1/3 complete
cum tss 86c6sub2 "done"  # 2/3 complete
cum tss 86c6sub3 "done"  # 3/3 complete → parent auto-closes!
```

[→ Full parent auto-update documentation](PARENT_AUTO_UPDATE.md)

---

## Git Overflow

**Command:** `overflow`

Automated Git + ClickUp workflow integration.

### Usage

```bash
cum overflow <message> [options]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `message` | Yes | Commit message |

### Options

| Option | Description |
|--------|-------------|
| `--task TASK_ID` | Task ID (defaults to `current`) |
| `--type TYPE` | Workflow type (see below) |
| `--no-push` | Don't push to remote |
| `--no-clickup` | Don't update ClickUp |
| `--status STATUS` | Update task status |
| `--priority PRIORITY` | Update task priority |
| `--tags TAG [TAG...]` | Update task tags |
| `--dry-run` | Test without making changes |

### Workflow Types

| Type | Description |
|------|-------------|
| `direct` | Direct commit and push (default) |
| `pr` | Create pull request branch |
| `wip` | Work in progress (no push) |
| `hotfix` | Hotfix branch workflow |
| `merge` | Merge workflow |

### Examples

```bash
# Simple commit and push
cum overflow "Implement feature X"

# With task update
cum overflow "Fix bug" --task 86c6xyz --status "done"

# Create PR branch
cum overflow "New feature" --type pr --task current

# Work in progress
cum overflow "WIP: testing" --type wip --no-push

# Hotfix workflow
cum overflow "Critical fix" --type hotfix --status "done" --priority urgent

# Dry run to test
cum overflow "Test message" --dry-run
```

### Workflow Details

**Direct workflow:**
1. Stage all changes (`git add .`)
2. Commit with message
3. Push to remote
4. Update ClickUp task (if --task provided)
5. Add comment to task with commit SHA

**PR workflow:**
1. Create feature branch
2. Stage and commit changes
3. Push to remote
4. Create pull request (if GitHub CLI available)
5. Update ClickUp task with PR link

**Hotfix workflow:**
1. Create hotfix branch from main
2. Stage and commit changes
3. Push to remote
4. Update ClickUp task with urgent priority

### Integration with ClickUp

When `--task` is provided:
- Adds commit SHA as comment
- Updates task status (if `--status` provided)
- Updates task priority (if `--priority` provided)
- Adds tags (if `--tags` provided)
- Links commit to task

**Example workflow:**
```bash
# Set current task
cum set task 86c6xyz

# Work on code
vim src/feature.py

# Commit and update task
cum overflow "Implement feature X" \
  --status "in review" \
  --tags "needs-review" "backend"

# Result:
# ✓ Changes committed
# ✓ Pushed to remote
# ✓ Task status updated to "in review"
# ✓ Tags added: needs-review, backend
# ✓ Comment added with commit SHA
```

[→ Full git overflow documentation](git_overflow_action_plan.md)

---

## Space Management

**Command:** `space` **Shortcodes:** `sp` `spc`

Create, update, delete, and list spaces.

### Usage

```bash
cum space <subcommand> [options]
cum sp <subcommand> [options]
cum spc <subcommand> [options]
```

### Subcommands

- `create` - Create new space
- `update` - Update space properties
- `delete` - Delete space
- `list` - List all spaces

### Examples

```bash
# List spaces
cum sp list

# Create space
cum space create --name "Project X" --workspace current

# Update space
cum sp update <space_id> --name "Updated Name"

# Delete space
cum space delete <space_id> --force
```

[→ Full space management documentation](commands/space.md)

---

## Folder Management

**Command:** `folder` **Shortcodes:** `fld` `fd`

Create, update, delete, and list folders.

### Usage

```bash
cum folder <subcommand> [options]
cum fld <subcommand> [options]
cum fd <subcommand> [options]
```

### Subcommands

- `create` - Create new folder
- `update` - Update folder properties
- `delete` - Delete folder
- `list` - List folders

### Examples

```bash
# List folders in space
cum fld list <space_id>

# Create folder
cum folder create --space <space_id> --name "Backend"

# Update folder
cum fd update <folder_id> --name "Updated Name"

# Delete folder
cum folder delete <folder_id> --force
```

[→ Full folder management documentation](commands/folder.md)

---

## List Management

**Command:** `list-mgmt` **Shortcodes:** `lm` `list_mgmt`

Create, update, delete, and list Lists.

### Usage

```bash
cum list-mgmt <subcommand> [options]
cum lm <subcommand> [options]
cum list_mgmt <subcommand> [options]
```

### Subcommands

- `create` - Create new list
- `update` - Update list properties
- `delete` - Delete list
- `list` - List all lists

### Examples

```bash
# List all lists in folder
cum lm list <folder_id>

# Create list
cum list-mgmt create --folder <folder_id> --name "Sprint 5"

# Update list
cum lm update <list_id> --name "Updated Sprint 5"

# Delete list
cum list-mgmt delete <list_id> --force
```

[→ Full list management documentation](commands/list_mgmt.md)

---

## Common Workflows

### Project Setup Workflow

```bash
# Set workspace
cum set workspace 90151898946

# Create space
cum sp create --name "Project X"
# Returns: space_id

# Create folders
cum fld create --space <space_id> --name "Backend"
cum fld create --space <space_id> --name "Frontend"
cum fld create --space <space_id> --name "DevOps"

# Create lists in backend folder
cum lm create --folder <backend_folder_id> --name "Sprint 1"
cum lm create --folder <backend_folder_id> --name "Sprint 2"
cum lm create --folder <backend_folder_id> --name "Backlog"

# Set current list
cum set list <sprint1_list_id>

# Create tasks with checklist template
cum tc "Setup API" --checklist-template "api-setup"
cum tc "Database schema" --checklist-template "database"
```

### Development Workflow with Git Overflow

```bash
# Set current task
cum set task 86c6xyz

# View task details
cum d current

# Work on feature
vim src/feature.py

# Commit and update task
cum overflow "Implement feature" --status "in progress"

# Continue working
vim tests/test_feature.py

# Commit tests
cum overflow "Add tests" --status "in review" --tags "needs-review"

# After review, complete
cum overflow "Address review comments" --status "done"
```

### Custom Field Tracking

```bash
# Set story points on tasks
cum cf set 86c6xyz "Story Points" 5
cum cf set 86c6abc "Story Points" 3
cum cf set 86c6def "Story Points" 8

# Set priority scores
cum cf set 86c6xyz "Priority Score" 9
cum cf set 86c6abc "Priority Score" 7

# Track environments
cum cf set 86c6xyz "Environment" "production"
cum cf set 86c6abc "Environment" "staging"

# View task with custom fields
cum d 86c6xyz
```

### Automation Setup

```bash
# Enable parent auto-update
cum pau enable

# Configure triggers
cum pau add-trigger "done"
cum pau add-trigger "closed"

# Check configuration
cum pau status

# Create hierarchical task structure
cum tc current "Q1 Goals"  # Parent
cum tc "Goal 1" --parent <parent_id>
cum tc "Goal 2" --parent <parent_id>
cum tc "Goal 3" --parent <parent_id>

# As goals complete, parent auto-updates
cum tss <goal1_id> "done"
cum tss <goal2_id> "done"
cum tss <goal3_id> "done"  # Parent auto-completes!
```

---

## Tips

1. **Use templates:** Save time with checklist templates for recurring tasks
2. **Custom fields:** Track additional metadata beyond standard fields
3. **Automation:** Enable parent auto-update for hierarchical task management
4. **Git integration:** Use overflow for seamless Git + ClickUp workflow
5. **Organize with hierarchy:** Use Spaces → Folders → Lists for structure
6. **Bulk operations:** Script list/folder creation for consistent project structure
7. **Dry run:** Test overflow commands with `--dry-run` first

---

## Advanced Configuration Files

### Checklist Templates

**File:** `~/.clickup_checklist_templates.json`

```json
{
  "deployment": {
    "name": "Deployment Checklist",
    "items": [
      "Run tests",
      "Update version",
      "Build artifacts",
      "Deploy to staging",
      "Run smoke tests",
      "Deploy to production",
      "Verify deployment",
      "Update documentation"
    ]
  },
  "code-review": {
    "name": "Code Review Checklist",
    "items": [
      "Code follows style guide",
      "Tests are comprehensive",
      "Documentation is updated",
      "No security vulnerabilities",
      "Performance is acceptable"
    ]
  }
}
```

### Parent Auto-Update Config

**File:** `~/.clickup_parent_auto_update.json`

```json
{
  "enabled": true,
  "triggers": ["done", "closed"],
  "auto_close": true,
  "update_progress": true
}
```

---

**Navigation:**
- [← Back to Index](INDEX.md)
- [← Config Commands](CONFIG_COMMANDS.md)
