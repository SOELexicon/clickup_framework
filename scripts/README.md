# ClickUp Framework Scripts

Command-line utilities for managing ClickUp tasks using the Token-Efficient ClickUp Framework.

## Available Scripts

### update_tasks.py

Bulk update ClickUp tasks with status changes and comments using JSON configuration.

**Features:**
- Update task statuses
- Add comments to tasks
- Add tags to tasks
- Dry-run mode for preview
- No Python coding needed - just edit JSON

**Usage:**

```bash
# From repository root
python clickup_framework/scripts/update_tasks.py --dry-run config.json
python clickup_framework/scripts/update_tasks.py config.json

# If framework is installed
python -m clickup_framework.scripts.update_tasks config.json
```

**JSON Configuration Format:**

```json
{
  "description": "Batch update description",
  "tasks": [
    {
      "id": "task_id",
      "name": "Task Name (for reference)",
      "status": "comitted",
      "comment": "Comment text",
      "add_tags": ["tag1", "tag2"]
    }
  ]
}
```

See `task_updates_example.json` for a complete example.

---

### analyze_task_dependencies.py

Analyze task dependencies to show blockers, dependents, and execution order.

**Features:**
- Show what blocks each task (dependencies)
- Show what each task blocks (dependents)
- Sort tasks in completion order (topological sort)
- Identify critical path
- Calculate project completion percentage

**Usage:**

```bash
# Analyze single task
python clickup_framework/scripts/analyze_task_dependencies.py 86c6chc8q

# Analyze multiple specific tasks
python clickup_framework/scripts/analyze_task_dependencies.py \
  --tasks task_id_1 task_id_2 task_id_3

# Analyze all tasks in a list
python clickup_framework/scripts/analyze_task_dependencies.py --all list_id

# Analyze project tasks
python clickup_framework/scripts/analyze_task_dependencies.py --project project_task_id
```

**Output:**

For single task:
- Lists all blocking tasks (what this task waits for)
- Lists all dependent tasks (what waits for this task)
- Shows task status for each relationship

For multiple tasks:
- Execution order (what must be completed first)
- Tasks grouped by dependency level (parallelization opportunities)
- Critical path (longest dependency chain)
- Summary statistics

**Example Output:**

```
EXECUTION ORDER (What Must Be Completed First)

Level 1 - Can start in parallel:
  [✓] 86c6chcfe: Space Management Endpoints [comitted]
  [✓] 86c6chcfg: Custom Fields Endpoints [comitted]
  [ ] 86c6chcfj: Checklist Endpoints [Open]

Level 2 - Can start in parallel:
  [✓] 86c6chc8q: List Formatter [comitted]
  [ ] 86c6chc90: Workspace Formatter [Open]

CRITICAL PATH (Longest Dependency Chain)

Length: 5 tasks

1. [✓] 86c6chcfe: Space Management [comitted]  ↓
2. [✓] 86c6chc8q: List Formatter [comitted]  ↓
3. [ ] 86c6chcd6: ListAPI Resource [Open]  ↓
4. [ ] 86c6chchr: Migration Docs [Open]  ↓
5. [ ] 86c6chctb: README Update [Open]

SUMMARY
Total tasks: 17
Completed: 9 (52.9%)
Remaining: 8
Critical path length: 5 tasks
Parallel opportunities: 3 tasks can start now
```

---

## Requirements

Both scripts require:
- Python 3.9+
- ClickUp Framework installed (`pip install -e /path/to/clickup_framework`)
- `CLICKUP_API_TOKEN` environment variable set

## Installation

```bash
# Install framework in development mode
pip install -e /path/to/clickup_framework

# Or install from package
pip install clickup-framework
```

## Common Workflows

### 1. Update Task Status After Completion

```bash
# Create config file
cat > my_updates.json << 'EOF'
{
  "tasks": [
    {
      "id": "86c6chcfe",
      "status": "comitted",
      "comment": "Implementation complete. Added 5 new endpoints."
    }
  ]
}
EOF

# Preview changes
python clickup_framework/scripts/update_tasks.py --dry-run my_updates.json

# Apply updates
python clickup_framework/scripts/update_tasks.py my_updates.json
```

### 2. Analyze Project Dependencies

```bash
# Get list of task IDs from your project
TASK_IDS="86c6chcfe 86c6chcfg 86c6chcfj 86c6chc8q"

# Analyze dependencies
python clickup_framework/scripts/analyze_task_dependencies.py --tasks $TASK_IDS
```

### 3. Find Next Tasks to Work On

```bash
# Analyze all tasks to see execution order
python clickup_framework/scripts/analyze_task_dependencies.py --all <list_id>

# Look for "Level N - Can start in parallel" with uncompleted tasks
# These are the next tasks you can work on
```

## Tips

### Task Updates

- Always use `--dry-run` first to preview changes
- Keep JSON configs in version control for audit trail
- Use descriptive comment text to document what was done
- Prefer `comitted` status over `Closed` for completed work

### Dependency Analysis

- Run analysis regularly to track progress
- Use critical path to identify bottlenecks
- Look for parallel opportunities to speed up work
- Check blockers before starting new tasks

## Troubleshooting

**Import errors:**
```bash
# Ensure framework is installed
pip install -e /path/to/clickup_framework

# Or add to PYTHONPATH
export PYTHONPATH="/path/to/repository:$PYTHONPATH"
```

**API errors:**
```bash
# Check API token is set
echo $CLICKUP_API_TOKEN

# Set if missing
export CLICKUP_API_TOKEN="your_token_here"
```

**Task not found errors:**
- Verify task ID is correct
- Check you have access to the task
- Ensure task exists in ClickUp

## Examples

See `task_updates_example.json` for a complete update configuration example.

---

**Related Documentation:**
- [ClickUp Framework README](../README.md)
- [API Reference](../../docs/api_reference.md)
- [Quickstart Guide](../../docs/quickstart.md)
