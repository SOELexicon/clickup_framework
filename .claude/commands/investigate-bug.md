# Bug Investigation Workflow

You are helping investigate and fix a bug in the ClickUp Framework. Follow this systematic workflow:

## Phase 1: Reproduction & Documentation

1. **Reproduce the Issue**
   - Run the failing command/code
   - Capture exact error messages and output
   - Document steps to reproduce consistently
   - Note any patterns or conditions that trigger the bug

2. **Gather Context**
   - Check the task description for issue details
   - Look for related tasks or previous fixes
   - Review recent commits that might be related
   - Check if this worked before (regression vs new bug)

## Phase 2: Code Investigation

3. **Locate Relevant Code**
   ```bash
   # Find files related to the feature
   grep -r "function_name" clickup_framework/
   find . -name "*feature*.py"

   # Check command implementations
   ls clickup_framework/commands/

   # Check API clients
   ls clickup_framework/resources/
   ```

4. **Read Implementation**
   - Use Read tool to examine relevant source files
   - Trace the code path from CLI command to API call
   - Look for data transformations, validations, error handling
   - Check for edge cases or missing logic

5. **Test API Directly**
   ```python
   from clickup_framework import ClickUpClient
   import json

   client = ClickUpClient()

   # Test the exact API call
   result = client.<method>(<params>)

   # Examine response structure
   print(json.dumps(result, indent=2))
   print("Keys:", result.keys())

   # Check for missing/unexpected fields
   ```

## Phase 3: Root Cause Analysis

6. **Compare Expected vs Actual**
   - What should happen?
   - What actually happens?
   - Where does behavior diverge?
   - Is this a display issue, logic issue, or API issue?

7. **Identify Root Cause**
   Common patterns to check:
   - Missing field in API response
   - Incorrect data transformation/parsing
   - Wrong endpoint or parameters
   - Escaped/unescaped data (newlines, quotes)
   - Missing error handling
   - Logic errors in conditionals
   - Type mismatches

8. **Document Findings**
   Add comprehensive comment to task:
   ```bash
   cum ca <task_id> "
   ## Root Cause Analysis

   ### Issue Summary
   <Brief description>

   ### Reproduction Steps
   1. <Step 1>
   2. <Step 2>
   3. <Step 3>

   ### Expected Behavior
   <What should happen>

   ### Actual Behavior
   <What actually happens>

   ### Root Cause
   <Detailed explanation of the underlying issue>

   ### Evidence
   \`\`\`
   <Code snippet, API response, or error message>
   \`\`\`

   ### File Locations
   - Primary: \`path/to/file.py:line_number\`
   - Related: \`path/to/related.py:line_number\`

   ### Proposed Solutions
   1. **Option 1**: <Description>
      - Pros: <advantages>
      - Cons: <disadvantages>
      - Complexity: Low/Medium/High

   2. **Option 2**: <Description>
      - Pros: <advantages>
      - Cons: <disadvantages>
      - Complexity: Low/Medium/High

   ### Recommended Solution
   Option <N> because <reasoning>

   ### Implementation Plan
   1. <Step 1>
   2. <Step 2>
   3. <Step 3>

   ### Testing Strategy
   - Unit test: <description>
   - Integration test: <description>
   - Manual verification: <command to test>
   "
   ```

## Phase 4: Implementation

9. **Create Fix Branch**
   ```bash
   git checkout -b claude/fix-<issue-description>-<session-id>
   ```

10. **Implement Fix**
    - Make minimal, focused changes
    - Follow existing code style
    - Add comments explaining the fix
    - Handle edge cases
    - Add error handling if needed

11. **Test Thoroughly**
    ```bash
    # Test the specific fix
    cum <command> <args>

    # Test edge cases
    cum <command> <edge-case-args>

    # Run related tests
    python -m pytest tests/test_<feature>.py -v
    ```

## Phase 5: Documentation & Completion

12. **Update Documentation**
    - Update docstrings if behavior changed
    - Add code comments explaining the fix
    - Update user-facing docs if needed

13. **Commit Changes**
    ```bash
    git add <files>
    git commit -m "Fix: <issue description>

    Problem: <what was wrong>
    Solution: <what was changed>
    Testing: <how it was verified>

    Fixes: <task-id>
    "
    ```

14. **Update Task Status**
    ```bash
    # Mark investigation subtask complete
    cum tss <investigation-task-id> "Complete"

    # Add completion comment
    cum ca <investigation-task-id> "
    ✓ Investigation complete
    ✓ Root cause identified: <brief summary>
    ✓ Fix implemented in commit: <commit-hash>
    ✓ Tests passing

    Branch: <branch-name>
    Files changed: <list>
    "

    # Update parent task
    cum ca <parent-task-id> "Fix implemented for <issue>. See <investigation-task-id> for details."
    ```

## Common Bug Patterns & Solutions

### Pattern 1: Escaped Newlines
**Symptom**: Content shows `\n` instead of line breaks
**Location**: Display/formatting code
**Fix**: Unescape or decode newlines before display

### Pattern 2: Missing API Fields
**Symptom**: KeyError or None values
**Location**: API response parsing
**Fix**: Add field validation, use `.get()` with defaults

### Pattern 3: Wrong Endpoint
**Symptom**: 404 or unexpected response
**Location**: Client API methods
**Fix**: Verify endpoint path against ClickUp API docs

### Pattern 4: Extra Objects Created
**Symptom**: Unexpected items in lists
**Location**: Creation logic
**Fix**: Check for automatic default object creation

### Pattern 5: Missing Hierarchy
**Symptom**: Only root items shown
**Location**: Data fetching or display logic
**Fix**: Implement recursive fetching or tree building

## Investigation Checklist

Before completing investigation:
- [ ] Issue reproduced consistently
- [ ] Error messages/output captured
- [ ] Relevant code located and read
- [ ] API tested directly
- [ ] Root cause identified with evidence
- [ ] File locations documented
- [ ] Solutions proposed with pros/cons
- [ ] Implementation plan created
- [ ] Testing strategy defined

## Deliverables

At end of investigation, you should have:
1. ✅ Comprehensive root cause analysis in task comment
2. ✅ Clear reproduction steps
3. ✅ File locations with line numbers
4. ✅ Proposed solutions with recommendation
5. ✅ Implementation plan
6. ✅ Testing strategy

Now proceed with the investigation, following these steps systematically.
