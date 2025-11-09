# task_set_status - Set Task Status with Validation

## Description

Set task status with automatic subtask validation. Prevents setting a parent task's status unless all subtasks have the same status. Supports updating multiple tasks simultaneously.

## Command Signature

```bash
clickup task_set_status <task_id> [task_id ...] <status>
```

## Arguments

### Required
- `task_ids` - One or more task IDs to update (or "current")
- `status` - The new status (must be valid for the task's list)

## Features

### Subtask Validation
- Automatically checks if task has subtasks
- Prevents status change if subtasks have different status
- Shows formatted list of mismatched subtasks
- Provides clear guidance on which subtasks need updating

### Multi-Task Support
- Update multiple tasks in a single command
- Continues processing remaining tasks if one fails
- Provides summary of successes/failures

## Examples

### Single Task Update
```bash
clickup task_set_status 86c6e0xyz "in development"
```

### Multiple Tasks
```bash
clickup task_set_status 86c6e0a 86c6e0b 86c6e0c "Closed"
```

### With Validation Failure
```bash
$ clickup task_set_status 86c6e0q0a "Closed"

⚠ Cannot set status to 'Closed' - 3 subtask(s) have different status

Task: Task Management Commands
Target status: Closed

Subtasks requiring status update:

  1. [86c6e0q0b] task create - Create new tasks
     Current status: Open

  2. [86c6e0q0d] task update - Update existing tasks
     Current status: Open

  3. [86c6e0q0f] task delete - Delete tasks
     Current status: in development

Update these subtasks first, then retry.
```

### After Updating Subtasks
```bash
# Update subtasks first
clickup task_set_status 86c6e0q0b 86c6e0q0d 86c6e0q0f "Closed"

# Now parent can be updated
clickup task_set_status 86c6e0q0a "Closed"
```

## Output

### Success (Single Task)
```
✓ Status updated

Task: API Development [86c6e0xyz]
New status: in development
Subtasks: 5 subtask(s) also have status 'in development'
```

### Success (Multiple Tasks)
```
✓ Status updated

Task: task create [86c6e0q0b]
New status: Closed

✓ Status updated

Task: task update [86c6e0q0d]
New status: Closed

✓ Status updated

Task: task delete [86c6e0q0f]
New status: Closed

Summary:
  Updated: 3/3 tasks
```

### Validation Failure
Shows formatted list of subtasks that need updating (see example above)

## Implementation Status

✅ **Implemented** - Available in CLI with full validation

## Related Commands

- `task_update` - General task updates without validation
- `hierarchy` - View task hierarchy
- `detail` - View task details including subtasks

## API Endpoint

`PUT /task/{task_id}`

## Validation Rules

1. **Subtask Check**
   - If task has subtasks, fetch all subtasks
   - Compare each subtask's status with target status (case-insensitive)
   - If any mismatch, abort with formatted error message

2. **Multiple Tasks**
   - Validate each task independently
   - Skip tasks that fail validation
   - Continue with remaining tasks
   - Report summary at end

## Notes

- Status comparison is case-insensitive
- Subtask validation fetches all tasks in the list (may be slow for large lists)
- For tasks without subtasks, behaves like `task_update --status`
- Validation can be bypassed by using `task_update --status` instead
- Status must exist in the task's list workflow

## Use Cases

### ✅ Good For
- Marking parent tasks as complete
- Ensuring task hierarchy consistency
- Bulk status updates with validation
- Workflow compliance

### ⚠️ Not Ideal For
- Updating tasks without subtasks (use `task_update` for speed)
- Bypassing validation (use `task_update` instead)
- Very large task hierarchies (validation may be slow)

## Error Handling

- Invalid status → API error
- Task not found → API error
- Subtask mismatch → Validation error with details
- Multiple tasks → Continues on error, reports at end
