# Lessons Learned - ClickUp Framework CLI

## Session: 2025-11-12 - Bugfix Task 86c6g88be

### Lesson 1: Always Use Correct CLI Command Names

**Mistake Made:**
Attempted to use `cum create` command which doesn't exist:
```bash
cum create 86c6g88be "Fix: Pipe alignment breaks..." --description "..."
```

**Error Received:**
```
cum: error: argument command: invalid choice: 'create'
```

**Root Cause:**
- Assumed there was a generic `create` command
- Did not verify the actual command name before using it
- Should have checked available commands first

**Correct Solution:**
Use `cum tc` (task_create) for creating tasks:
```bash
cum tc --parent 86c6g88be "Fix: Pipe alignment breaks..." --description "..."
```

**Prevention Strategy:**
1. **Always reference the command list** before using a command
   - Run `cum --help` or `/cum` to see available commands
   - Check documentation for exact command names

2. **Use command aliases when known:**
   - `tc` = task_create
   - `tu` = task_update
   - `tss` = task_set_status
   - `ca` = comment_add
   - etc.

3. **If unsure, check help first:**
   ```bash
   cum --help | grep -i create
   # Shows: task_create, tc, doc_create, dc, page_create, pc
   ```

4. **Learn from error messages:**
   - The error message lists ALL valid commands
   - Read the list to find the correct one
   - In this case, the list included `task_create, tc` which is what we needed

**Impact:**
- Minor: Required one extra command to correct
- Lost ~30 seconds retrying with correct command
- No data corruption or permanent issues

**Key Takeaway:**
> "When working with CLI tools, verify command names before execution. Use --help or documentation rather than assuming command names based on patterns from other tools."

---

## Best Practices Reinforced

### CLI Command Discovery
1. Use `/cum` slash command to see full command reference
2. Use `cum --help` for quick command list
3. Use `cum <command> --help` for command-specific options
4. Check CLICKUP_CLI_COMMANDS.md for detailed documentation

### Error Recovery
1. Read error messages carefully - they often list valid options
2. Use error output to quickly identify the correct command
3. Document the mistake to avoid repetition

### Command Naming Patterns
- **Task operations:** `task_<action>` or `t<initials>`
  - create: `task_create` / `tc`
  - update: `task_update` / `tu`
  - delete: `task_delete` / `td`

- **Doc operations:** `doc_<action>` or `d<initials>`
  - create: `doc_create` / `dc`
  - get: `doc_get` / `dg`

- **Page operations:** `page_<action>` or `p<initials>`
  - create: `page_create` / `pc`
  - update: `page_update` / `pu`

- **No generic** `create`, `update`, `delete` commands - always prefixed with resource type

---

## Verification Checklist

Before executing a CLI command:
- [ ] Verified command exists in help output
- [ ] Checked command syntax/parameters
- [ ] Understood what the command will do
- [ ] Have proper error handling/recovery plan

This prevents:
- Invalid command errors
- Incorrect parameter usage
- Unintended side effects
- Time wasted on trial-and-error
