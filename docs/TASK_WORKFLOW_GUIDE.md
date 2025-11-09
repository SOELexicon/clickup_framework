# ClickUp Task Workflow Guide

A comprehensive guide for managing ClickUp tasks from start to finish using the ClickUp Framework CLI.

---

## Table of Contents

1. [Starting a Task](#1-starting-a-task)
2. [Working on a Task (In Progress)](#2-working-on-a-task-in-progress)
3. [Completing a Task](#3-completing-a-task)
4. [Handling Subtasks](#4-handling-subtasks)
5. [Status Management](#5-status-management)
6. [When to Leave Comments](#6-when-to-leave-comments)
7. [Quick Reference](#7-quick-reference)

---

## 1. Starting a Task

### When You're Ready to Begin Work

**Step 1: Set the task as current** (for easy reference)
```bash
cum set_current task <task_id>
```

**Step 2: View the task details**
```bash
cum detail current
```
Review:
- Task description and requirements
- Existing subtasks
- Current status
- Assigned priority
- Due dates
- Any existing comments from stakeholders

**Step 3: Update status to "in progress"**
```bash
cum set_status current "in progress"
```

**Step 4: Leave a start comment** (recommended)
```bash
cum comment current "Starting work on this task. Initial review complete."
```

**When to leave a start comment:**
- ✅ Complex tasks requiring multiple days
- ✅ Tasks with multiple stakeholders
- ✅ Tasks where you need to document your approach
- ✅ Tasks assigned to you by someone else
- ❌ Small, routine tasks with obvious implementation
- ❌ Tasks you created yourself with clear scope

**Optional: Set yourself as assignee** (if not already assigned)
```bash
cum assign current --user-id <your_user_id>
```

---

## 2. Working on a Task (In Progress)

### Making Progress Updates

**Update frequency depends on:**
- **Task duration**: Daily updates for week-long tasks, milestone updates for longer tasks
- **Team expectations**: Match your team's communication norms
- **Complexity**: More updates for complex/risky work
- **Blockers**: Immediate updates when blocked

### When to Leave Progress Comments

**✅ DO leave comments when:**

1. **You hit a significant milestone**
   ```bash
   cum comment current "Completed database schema design. Moving to API implementation."
   ```

2. **You're blocked or need help**
   ```bash
   cum comment current "Blocked: Need design approval before proceeding with frontend. @designer"
   ```

3. **Scope changes or new discoveries**
   ```bash
   cum comment current "Discovered additional edge case: users with expired subscriptions. Will need extra validation."
   ```

4. **Taking a break from long-running tasks**
   ```bash
   cum comment current "Pausing work on this for priority issue #12345. Will resume next week."
   ```

5. **Important technical decisions**
   ```bash
   cum comment current "Decision: Using Redis for caching instead of memcached due to persistence requirements."
   ```

6. **Completing subtasks** (if they represent significant work)
   ```bash
   cum comment current "✓ Completed API endpoint implementation. 3/5 subtasks done."
   ```

**❌ DON'T leave comments for:**

- Trivial updates ("still working on it")
- Every single commit or minor change
- Information better suited for commit messages
- Redundant status updates (status field handles this)

### Updating Subtasks

**As you complete subtasks:**
```bash
# Mark subtask as complete
cum set_status <subtask_id> "complete"

# Or if it's your current task
cum set_current task <subtask_id>
cum set_status current "complete"
```

**View subtask progress:**
```bash
cum hierarchy current  # Shows parent task with all subtasks
```

---

## 3. Completing a Task

### Checklist Before Marking Complete

**✅ Verify all completion criteria:**

1. **Check subtasks**
   ```bash
   cum hierarchy current
   ```
   - Are all critical subtasks completed?
   - Are any remaining subtasks acceptable to leave undone?
   - Should incomplete subtasks be converted to separate tasks?

2. **Review task requirements**
   ```bash
   cum detail current
   ```
   - Does the work meet all acceptance criteria?
   - Have you tested the implementation?
   - Is documentation updated (if required)?

3. **Handle incomplete subtasks** (see Section 4)

### Marking Task Complete

**If all subtasks are complete:**
```bash
cum set_status current "complete"
cum comment current "Task completed. All subtasks finished and tested successfully."
```

**If some subtasks remain:**

**Option A: Move incomplete subtasks to new parent task**
```bash
# Create a follow-up task
cum create <list_id> "Follow-up: Remaining items from #<original_task_id>"

# Update the incomplete subtasks to point to new parent
# (This would need manual API work or waiting for future CLI support)

# Mark original task complete
cum set_status <original_task_id> "complete"
cum comment <original_task_id> "Core work complete. Moved remaining items to #<new_task_id>."
```

**Option B: Mark them as "won't do" or update status**
```bash
cum set_status <incomplete_subtask_id> "won't do"
cum comment current "Marked subtask 'X' as won't do - no longer relevant after implementation."
cum set_status current "complete"
```

**Option C: Leave for future (if using custom statuses)**
```bash
# Some teams have "Complete with Open Items" or similar
cum set_status current "complete - pending followup"
cum comment current "Main work complete. Remaining subtasks documented in description."
```

### When Task is Complete

**Leave a completion comment if:**
- ✅ Task took multiple days/weeks
- ✅ Multiple people were involved
- ✅ Deployment or special actions required
- ✅ Results worth documenting (performance gains, bug fixes, etc.)
- ✅ Follow-up tasks were created

**Example completion comments:**
```bash
cum comment current "Completed and deployed to production. Performance improved by 40%. Monitoring in place."

cum comment current "Fixed bug #123. Root cause was race condition in payment processing. Added tests to prevent regression."

cum comment current "Feature complete and merged to main. Documentation updated in Wiki. Created follow-up task #456 for mobile support."
```

---

## 4. Handling Subtasks

### Scenarios and Recommended Actions

#### Scenario 1: All Subtasks Complete ✅
**Action:** Mark parent task complete
```bash
cum set_status <parent_task_id> "complete"
```

#### Scenario 2: Some Subtasks No Longer Needed 🚫
**Action:** Mark unnecessary subtasks as "won't do" or delete them
```bash
cum set_status <subtask_id> "won't do"
cum comment <subtask_id> "No longer needed - requirement changed."

# Then mark parent complete
cum set_status <parent_task_id> "complete"
```

#### Scenario 3: Subtasks Are Follow-up Work (Nice to Have) 📋
**Action:** Convert to separate tasks or keep as future work
```bash
# Create new task for follow-up work
cum create <list_id> "Enhancement: <description>" --priority low

# Reference it in parent task
cum comment <parent_task_id> "Core complete. Created #<new_task_id> for future enhancements."

# Mark parent complete
cum set_status <parent_task_id> "complete"
```

#### Scenario 4: Subtasks Are Blocked ⛔
**Action:** Don't mark parent complete; update status and add comment
```bash
cum set_status <parent_task_id> "blocked"
cum comment <parent_task_id> "Blocked on subtask #<id>: waiting for API access from infrastructure team."
```

#### Scenario 5: Subtasks Were Planning Items (Already Done) ✓
**Action:** Mark them complete retroactively
```bash
# If they were completed but not marked
cum set_status <subtask_id> "complete"

# Then complete parent
cum set_status <parent_task_id> "complete"
```

---

## 5. Status Management

### Common Status Flow

```
TO DO → IN PROGRESS → IN REVIEW → COMPLETE
                ↓
            BLOCKED (temporary)
```

### Status Guidelines

| Status | When to Use | Next Steps |
|--------|------------|------------|
| **To Do** | Task is defined but not started | Set to "in progress" when starting work |
| **In Progress** | Actively working on task | Update to "in review" when code is ready for review |
| **In Review** | Code/work submitted for review | Update to "complete" when approved, back to "in progress" if changes needed |
| **Blocked** | Cannot proceed due to external dependency | Leave comment explaining blocker. Return to "in progress" when unblocked |
| **Complete** | All acceptance criteria met, all critical subtasks done | Task is done! Archive or close per team process |
| **Won't Do** | Task cancelled or no longer relevant | Add comment explaining why |

### Custom Statuses

**Your ClickUp workspace may have custom statuses.** View available statuses:
```bash
cum hierarchy <list_id>  # Shows status options in output
```

Common custom statuses:
- "Ready for QA" / "In QA"
- "Pending Deployment"
- "In Code Review"
- "Waiting for Feedback"
- "On Hold"

**Match your team's workflow!** Ask your team lead if unsure about status meanings.

---

## 6. When to Leave Comments

### Comment Guidelines

#### ✅ DO Comment When:

1. **Starting complex/assigned work**
   - "Starting investigation into the database performance issues"

2. **Hitting blockers**
   - "Blocked: Need staging environment access"
   - "Waiting on design feedback from @designer"

3. **Making important decisions**
   - "Chose approach A over B due to better scalability"

4. **Discovering scope changes**
   - "Found 3 additional edge cases that need handling"

5. **Completing milestones in long tasks**
   - "Phase 1 complete: Database migration successful"

6. **Requesting review or feedback**
   - "Ready for review: PR #123"
   - "Need architecture review before proceeding"

7. **Completing the task**
   - "Deployed to production. All tests passing."

8. **Providing context for status changes**
   - "Setting to blocked while waiting for API key"

9. **@Mentioning stakeholders**
   - "@manager Design approved, proceeding with implementation"

10. **Linking related work**
    - "Related to issue #456. Fixed similar issue."

#### ❌ DON'T Comment For:

1. **Obvious status changes**
   - ❌ "Setting to in progress" (the status field shows this)

2. **Micro-updates**
   - ❌ "Fixed typo"
   - ❌ "Still working on it"

3. **Information better in commits**
   - ❌ "Changed variable name from x to y"

4. **Internal monologue**
   - ❌ "Hmm, wondering if this approach will work"

5. **Test messages**
   - ❌ "Testing the comment feature"

### Comment Best Practices

**Good Comments Are:**
- **Actionable**: "Need approval on design before proceeding"
- **Informative**: "Discovered root cause: race condition in payment processor"
- **Concise**: Get to the point quickly
- **Timely**: Leave when information is relevant

**Comment Formatting Tips:**
```bash
# Short updates
cum comment current "Completed API integration. Moving to frontend work."

# Multi-line comments with details
cum comment current "Major milestone reached:
- User authentication complete
- Database schema migrated
- API endpoints tested

Next: Frontend integration"

# @Mention for visibility
cum comment current "@manager Ready for review: completed all requirements"

# Link to external resources
cum comment current "PR ready for review: https://github.com/org/repo/pull/123"
```

---

## 7. Quick Reference

### Starting Work
```bash
cum set_current task <task_id>
cum detail current
cum set_status current "in progress"
cum comment current "Starting work on this task"  # If appropriate
```

### During Work
```bash
# Complete subtasks as you go
cum set_status <subtask_id> "complete"

# Leave milestone comments
cum comment current "Milestone: Backend API complete"

# Update if blocked
cum set_status current "blocked"
cum comment current "Blocked: waiting for X"
```

### Completing Work

**Simple task (no subtasks):**
```bash
cum set_status current "complete"
```

**Task with subtasks (all complete):**
```bash
cum hierarchy current  # Verify all subtasks complete
cum set_status current "complete"
cum comment current "All work complete. <summary of outcome>"
```

**Task with incomplete subtasks:**
```bash
# Option 1: Mark unneeded subtasks as "won't do"
cum set_status <subtask_id> "won't do"
cum set_status <parent_task_id> "complete"

# Option 2: Create follow-up task
cum create <list_id> "Follow-up: <remaining work>"
cum comment <original_task_id> "Core complete. Created #<new_id> for remaining items"
cum set_status <original_task_id> "complete"
```

### View Task Hierarchy
```bash
cum hierarchy current              # Current task and subtasks
cum hierarchy <list_id>            # All tasks in list
cum hierarchy current --detailed   # With full descriptions
```

### Common Workflows

**Daily standup update:**
```bash
cum hierarchy <list_id> --status "in progress"  # Your active tasks
cum comment <task_id> "Daily update: completed X, working on Y, blocked on Z"
```

**End of day:**
```bash
# Mark completed subtasks
cum set_status <subtask_1> "complete"
cum set_status <subtask_2> "complete"

# Leave progress update if appropriate
cum comment current "EOD: 3/5 subtasks complete. On track for Friday delivery."
```

**Code review ready:**
```bash
cum set_status current "in review"
cum comment current "@reviewer Ready for review: PR https://github.com/org/repo/pull/123"
```

---

## Best Practices Summary

### Status Updates
- ✅ Update status promptly when starting, blocking, or completing
- ✅ Use status field for current state
- ✅ Match your team's status workflow
- ❌ Don't leave tasks in "in progress" for weeks without updates

### Comments
- ✅ Add value and context
- ✅ Focus on decisions, blockers, and milestones
- ✅ @Mention people who need to know
- ❌ Don't spam with trivial updates
- ❌ Don't duplicate what's obvious from status

### Subtasks
- ✅ Mark complete as you finish them
- ✅ Handle incomplete subtasks before completing parent
- ✅ Convert future work to separate tasks
- ❌ Don't leave parent task "complete" with critical subtasks undone

### General
- ✅ Set task as "current" for easy CLI access
- ✅ Review task details before starting
- ✅ Keep stakeholders informed on complex work
- ✅ Be consistent with team norms
- ❌ Don't over-communicate on simple tasks
- ❌ Don't forget to update status when done

---

## Integration with Development Workflow

### Git + ClickUp Workflow Example

```bash
# 1. Start ClickUp task
cum set_current task <task_id>
cum set_status current "in progress"

# 2. Create git branch
git checkout -b feature/task-<task_id>-description

# 3. Do work, commit with task reference
git commit -m "feat: implement feature (#<task_id>)"

# 4. Update ClickUp at milestones
cum comment current "Completed backend implementation. Starting frontend."

# 5. Create PR
gh pr create --title "Feature: description (#<task_id>)"

# 6. Update ClickUp to in review
cum set_status current "in review"
cum comment current "Ready for review: <PR link>"

# 7. After PR approval and merge
cum set_status current "complete"
cum comment current "Merged and deployed to staging. Monitoring for issues."
```

---

## Getting Help

**View task details:**
```bash
cum detail <task_id>
cum hierarchy <task_id>
```

**View available commands:**
```bash
cum --help
```

**Check status options for your list:**
```bash
cum hierarchy <list_id>  # Status options shown in output
```

---

*This guide assumes you have the ClickUp Framework CLI installed and configured with your API token. For setup instructions, see the main README.md.*
