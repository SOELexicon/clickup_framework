# Bug Fix Implementation Workflow

You are implementing a fix for a bug in the ClickUp Framework. The investigation should already be complete with root cause identified.

## Prerequisites

Before starting, verify:
- [ ] Root cause analysis completed
- [ ] Investigation task has file locations
- [ ] Proposed solution documented
- [ ] Testing strategy defined

If not, run `/investigate-bug` first.

## Phase 1: Preparation

1. **Review Investigation Findings**
   ```bash
   # Read the investigation task
   cum detail <investigation-task-id>

   # Review root cause analysis
   # Note file locations
   # Review proposed solution
   ```

2. **Create Fix Branch**
   ```bash
   # Create branch following naming convention
   BRANCH="claude/fix-<issue-description>-<session-id>"
   git checkout -b $BRANCH

   # Verify clean working directory
   git status
   ```

3. **Read Relevant Files**
   - Read all files mentioned in investigation
   - Understand the current implementation
   - Identify exact lines to change

## Phase 2: Implementation

4. **Implement Minimal Fix**
   - Make the smallest change that solves the problem
   - Follow existing code style and patterns
   - Add comments explaining WHY (not just what)
   - Handle edge cases
   - Add error handling if appropriate

5. **Code Quality Checklist**
   - [ ] Fix addresses root cause (not just symptoms)
   - [ ] No unnecessary changes
   - [ ] Consistent with codebase style
   - [ ] Comments explain reasoning
   - [ ] Error handling added where needed
   - [ ] No hardcoded values
   - [ ] Type hints preserved/added
   - [ ] Docstrings updated if needed

## Phase 3: Testing

6. **Manual Testing**
   ```bash
   # Test the exact scenario from bug report
   cum <command> <original-failing-args>

   # Should now work correctly
   # Verify output matches expected behavior
   ```

7. **Edge Case Testing**
   ```bash
   # Test edge cases identified in investigation
   cum <command> <edge-case-1>
   cum <command> <edge-case-2>

   # Test with empty input
   cum <command> ""

   # Test with very long input
   cum <command> "<long-string>"

   # Test with special characters
   cum <command> "Test!@#$%^&*()"
   ```

8. **Regression Testing**
   ```bash
   # Run existing tests
   python -m pytest tests/test_<feature>.py -v

   # Run related command tests
   python -m pytest tests/ -k <feature> -v

   # All tests should pass
   ```

9. **Integration Testing**
   ```bash
   # Test the complete workflow
   # Example for docs:
   cum doc_create <workspace-id> "Test Doc" --pages "Page:Content"
   cum doc_get <workspace-id> <doc-id>
   cum page_list <workspace-id> <doc-id>

   # Verify entire flow works end-to-end
   ```

## Phase 4: Documentation

10. **Update Code Documentation**
    - Update docstrings if behavior changed
    - Add inline comments for complex logic
    - Document any workarounds or API limitations

11. **Update User Documentation**
    If the fix changes user-visible behavior:
    - Update README if needed
    - Update command help text
    - Note in CHANGELOG (if exists)

## Phase 5: Commit & Push

12. **Review Changes**
    ```bash
    git status
    git diff

    # Verify only intended changes included
    # Check for debugging code to remove
    # Ensure no sensitive data
    ```

13. **Commit with Descriptive Message**
    ```bash
    git add <files>
    git commit -m "$(cat <<'EOF'
    Fix: <concise summary of issue>

    Problem:
    <Description of the bug and its impact>

    Root Cause:
    <Brief explanation of underlying issue>

    Solution:
    <What was changed and why>

    Changes:
    - <Specific change 1>
    - <Specific change 2>
    - <Specific change 3>

    Testing:
    - Tested original failing scenario: ✓
    - Tested edge cases: ✓
    - Existing tests passing: ✓

    Files Modified:
    - <file1>: <what changed>
    - <file2>: <what changed>

    Fixes: <task-id>
    Related: <investigation-task-id>
    EOF
    )"
    ```

14. **Push with Retry Logic**
    ```bash
    MAX_RETRIES=4
    RETRY_COUNT=0
    DELAY=2

    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if git push -u origin $BRANCH; then
            echo "✓ Push successful"
            break
        else
            RETRY_COUNT=$((RETRY_COUNT + 1))
            if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
                echo "Push failed, retrying in ${DELAY}s..."
                sleep $DELAY
                DELAY=$((DELAY * 2))
            fi
        fi
    done
    ```

## Phase 6: Task Updates

15. **Update Investigation Task**
    ```bash
    cum ca <investigation-task-id> "
    ✅ Fix Implemented

    ## Changes
    <Summary of what was changed>

    ## Files Modified
    - \`<file1>:<lines>\`: <description>
    - \`<file2>:<lines>\`: <description>

    ## Testing
    ✓ Original scenario: Fixed
    ✓ Edge cases: Passing
    ✓ Regression tests: Passing

    ## Commit
    Hash: $(git rev-parse --short HEAD)
    Branch: $BRANCH

    ## Verification
    Test with: \`cum <command> <args>\`
    Expected: <correct behavior>
    "

    # Mark as complete
    cum tss <investigation-task-id> "Complete"
    ```

16. **Update Sub-subtasks**
    ```bash
    # Mark implementation subtask complete
    cum tss <implement-task-id> "Complete"
    cum ca <implement-task-id> "Implemented in commit: $(git rev-parse --short HEAD)"

    # Mark test subtask complete
    cum tss <test-task-id> "Complete"
    cum ca <test-task-id> "All tests passing. Manual and regression tests verified."
    ```

17. **Update Parent Task**
    ```bash
    cum ca <parent-task-id> "
    ✅ Fixed: <issue summary>

    Investigation: <investigation-task-id>
    Commit: $(git rev-parse --short HEAD)
    Branch: $BRANCH

    Changes:
    - <change 1>
    - <change 2>

    Status: Ready for review
    "
    ```

## Phase 7: Verification

18. **Fresh Environment Test**
    ```bash
    # In a new terminal/environment
    cd /tmp
    git clone <repo-url>
    cd <repo>
    git checkout $BRANCH

    # Install and test
    pip install -e .
    cum <command> <test-args>

    # Verify fix works in clean environment
    ```

19. **Create Verification Checklist**
    Add to task comment:
    ```bash
    cum ca <parent-task-id> "
    ## Verification Checklist

    ### Functionality
    - [ ] Original bug scenario fixed
    - [ ] Edge cases handled
    - [ ] Error messages clear
    - [ ] No new bugs introduced

    ### Code Quality
    - [ ] Code follows style guide
    - [ ] Comments explain reasoning
    - [ ] No debugging code left
    - [ ] Type hints present

    ### Testing
    - [ ] Manual tests pass
    - [ ] Unit tests pass
    - [ ] Integration tests pass
    - [ ] Tested in clean environment

    ### Documentation
    - [ ] Docstrings updated
    - [ ] Code comments added
    - [ ] User docs updated (if needed)

    ### Git
    - [ ] Commit message descriptive
    - [ ] Branch pushed successfully
    - [ ] Task IDs referenced

    Ready for review: ✅
    "
    ```

## Common Fix Patterns

### Fix Pattern 1: Add Missing Field Check
```python
# Before (causes KeyError)
value = response['field']

# After (handles missing field)
value = response.get('field', default_value)
```

### Fix Pattern 2: Unescape Content
```python
# Before (shows \\n)
print(content)

# After (shows actual newlines)
content = content.replace('\\n', '\n')
print(content)
```

### Fix Pattern 3: Fix Endpoint Path
```python
# Before (404 error)
return self._request("GET", f"/v3/docs/{doc_id}/pages/list")

# After (correct path)
return self._request("GET", f"/v3/workspaces/{workspace_id}/docs/{doc_id}/pages")
```

### Fix Pattern 4: Filter Unwanted Items
```python
# Before (includes None items)
pages = result.get('pages', [])

# After (filters None)
pages = [p for p in result.get('pages', []) if p.get('name')]
```

### Fix Pattern 5: Build Hierarchy
```python
# Before (flat list)
return pages

# After (hierarchical tree)
def build_tree(pages):
    root = [p for p in pages if not p.get('parent_id')]
    for page in root:
        page['children'] = get_children(pages, page['id'])
    return root
```

## Implementation Checklist

Before marking fix complete:
- [ ] Root cause addressed (not just symptoms)
- [ ] Code follows project style
- [ ] Comments explain reasoning
- [ ] Original scenario tested ✓
- [ ] Edge cases tested ✓
- [ ] Regression tests passing ✓
- [ ] Integration tests passing ✓
- [ ] Documentation updated
- [ ] Commit message descriptive
- [ ] Changes pushed successfully
- [ ] All subtasks updated
- [ ] Parent task updated
- [ ] Verification checklist created

## Final Deliverables

At completion, you should have:
1. ✅ Working fix committed and pushed
2. ✅ All tests passing
3. ✅ Documentation updated
4. ✅ Task comments updated with results
5. ✅ Subtasks marked complete
6. ✅ Verification checklist in parent task

The fix is now ready for code review and merge!
