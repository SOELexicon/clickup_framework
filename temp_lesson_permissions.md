**Lesson Learned: Task Access Permissions Issue in Coder-Workflow Mode**

**Date**: 2025-11-20
**Severity**: High
**Category**: Workflow, Permissions, Tooling

---

### 🔴 Problem Encountered

When attempting to fetch task details using cum task get 86c6mrdp4 in coder-workflow mode, received permission error:

`
Error: Exit code 1
It looks like you don't have access to that list.
`

This blocked the workflow despite the task being successfully created moments earlier.

---

### 🔍 Root Cause Analysis

**Primary Issue**: Permission/Access Control
- Task was created in list 901517404274 (Development Tasks)
- Immediately after creation, attempting to access the same task resulted in permission denial
- This suggests either:
  1. API token doesn't have read access to that list (only write)
  2. Token fallback mechanism not working correctly
  3. Context/session not properly refreshing after task creation
  4. Race condition where permissions haven't propagated yet

**Secondary Issues**:
- cum folder command failed with 'Namespace' object has no attribute 'func'
- cum space command failed with same error
- cum search command failed with "Required command not found: None" (missing grep dependency)

---

### ❌ What Went Wrong

1. **Workflow Assumption**: Assumed that creating a task would grant immediate read access
2. **No Fallback**: No alternative method to retrieve task details when permission denied
3. **CLI Tool Issues**: Multiple CLI commands are broken or have missing dependencies
4. **Context Management**: Token fallback mechanism may not be working as expected

---

### ✅ What Worked

- Task creation succeeded (all 9 tasks created successfully)
- Task detail view with cum d worked for parent task
- Checklist creation and item addition worked
- Tag addition worked
- Comment addition worked

---

### 💡 Solutions & Mitigations

**Immediate Workarounds**:
1. Use cum d <task_id> instead of cum task get <task_id> for fetching details
2. Set the problematic list as current: cum set list 901517404274
3. Check token permissions: Ensure API token has read access to all lists
4. Use parent task access path if subtask is blocked

**Long-term Fixes**:
1. **Fix Token Fallback**: Investigate context.py token fallback mechanism
2. **Fix Namespace Errors**: Debug folder/space commands that fail with attribute errors
3. **Add grep Dependency**: Install/configure grep for search functionality or use Python fallback
4. **Add Permission Checks**: Pre-validate token permissions before workflow operations
5. **Better Error Messages**: Provide actionable guidance when permission errors occur

---

### 📋 Prevention Checklist

For future workflows:
- [ ] Verify token has read/write access to target lists before starting
- [ ] Test CLI commands in target context before automation
- [ ] Add permission validation step at workflow start
- [ ] Use cum d instead of cum task get for reliability
- [ ] Set current list context before operations
- [ ] Have fallback API token configured
- [ ] Document which commands require external dependencies (grep)

---

### 🔧 Recommended Actions

**High Priority**:
1. Fix cum folder and cum space Namespace attribute errors
2. Investigate token permission scope for list 901517404274
3. Add grep dependency or Python fallback for search

**Medium Priority**:
4. Document token permission requirements in workflow guide
5. Add permission pre-check to coder-workflow mode
6. Create comprehensive CLI command health check

**Low Priority**:
7. Add retry logic with exponential backoff for permission errors
8. Cache task details after creation to avoid redundant fetches

---

### 📊 Impact Assessment

**Blocked Operations**:
- Automated coder-workflow task execution
- Task detail retrieval for newly created tasks
- Folder/space navigation in CLI

**Workaround Available**: Yes (use cum d and manual navigation)

**Workflow Disruption**: Medium - Can continue with manual intervention

---

### 🎓 Key Takeaways

1. **Never assume permissions**: Always validate access before operations
2. **Test in production context**: Development tokens may differ from production
3. **Build robust fallbacks**: Have alternative methods for critical operations
4. **Fix broken tools**: CLI commands with errors should be fixed before workflow automation
5. **Document dependencies**: External tools (grep) should be documented and checked

---

### 🔗 Related Issues

- Token fallback mechanism investigation needed
- CLI command error handling improvements needed
- Search functionality missing dependencies
- Namespace object attribute errors in multiple commands
