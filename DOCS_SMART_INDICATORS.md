# Smart Task Indicators

The hierarchy command (`cum h`) now displays smart indicators for task relationships, assignments, due dates, and time tracking.

## Indicator Reference

### 🔗 Dependencies & Blockers

**Dependencies (⏳ or D:N)**
- Shows tasks this task is **waiting on** (depends on)
- **With colors**: ⏳2 (yellow hourglass + count)
- **Without colors**: D:2
- Example: This task depends on 2 other tasks to be completed first

**Blockers (🚫 or B:N)**
- Shows tasks this task is **blocking**
- **With colors**: 🚫3 (red no-entry + count)
- **Without colors**: B:3
- Example: This task is blocking 3 other tasks

### 🔗 Linked Tasks (🔗 or L:N)

Shows count of related/linked tasks:
- **With colors**: 🔗5 (cyan link + count)
- **Without colors**: L:5
- Example: This task is linked to 5 other tasks

### 👤 Assignees

**Single Assignee (👤XX)**
- Shows user initials when one person assigned
- **With colors**: 👤JD (blue person + initials)
- **Without colors**: A:1
- Example: Assigned to John Doe

**Multiple Assignees (👥N)**
- Shows count when multiple people assigned
- **With colors**: 👥3 (blue people + count)
- **Without colors**: A:3
- Example: Assigned to 3 people

### 📅 Due Date Warnings

**Overdue (🔴 or OVERDUE:Nd)**
- Shows in **bold red** when past due
- **With colors**: 🔴5d (red circle + days overdue, bold)
- **Without colors**: OVERDUE:5d
- Example: 5 days overdue

**Due Today (📅 or DUE:TODAY)**
- Shows in **bold yellow** when due today
- **With colors**: 📅TODAY (calendar emoji, yellow, bold)
- **Without colors**: DUE:TODAY

**Due Soon (⚠️ or DUE:Nd)**
- Shows in **yellow** when due within 3 days
- **With colors**: ⚠️2d (warning + days until due)
- **Without colors**: DUE:2d
- Example: Due in 2 days

### ⏱️ Time Tracking

**Estimate + Spent (⏱️X.X/Y.Yh)**
- Shows tracked time vs estimate
- **Over budget**: Red color when spent > estimate
- **Under budget**: Green color when spent ≤ estimate
- **With colors**: ⏱️5.5/4.0h (red - over budget)
- **Without colors**: T:5.5/4.0h

**Estimate Only (⏱️X.Xh)**
- Shows only the time estimate
- **With colors**: ⏱️8.0h (cyan)
- **Without colors**: T:8.0h

**Spent Only (⏱️X.Xh)**
- Shows only tracked time (no estimate)
- **With colors**: ⏱️3.5h (yellow)
- **Without colors**: T:3.5h

## Example Hierarchy Views

### With All Indicators (Colored)

```
Tasks in My Project
│
└─Workspace (workspace)
  └─Development (folder)
    └─Sprint 42 (list)
      ├─[abc123] ⏳2 🚫1 🔗3 👤JD ⚠️2d ⏱️4.5/8.0h 📝 ⚙️ Implement user authentication
      │ └─[def456] 👤MS ⏱️2.0h 📝 ✓ Create login form
      ├─[ghi789] 🚫3 👥2 🔴5d ⏱️12.0/8.0h 📝 ⚙️ Fix critical bug
      └─[jkl012] 🔗1 👤AB 📅TODAY 📝 ⬜ Write documentation
```

### Without Colors (Terminal-safe)

```
Tasks in My Project
│
└─Workspace (workspace)
  └─Development (folder)
    └─Sprint 42 (list)
      ├─[abc123] D:2 B:1 L:3 A:1 DUE:2d T:4.5/8.0h [DOC] [DEV] Implement user authentication
      │ └─[def456] A:1 T:2.0h [DOC] [DON] Create login form
      ├─[ghi789] B:3 A:2 OVERDUE:5d T:12.0/8.0h [DOC] [DEV] Fix critical bug
      └─[jkl012] L:1 A:1 DUE:TODAY [DOC] [OPN] Write documentation
```

## Indicator Placement

Indicators appear in this order (after task ID):

1. **Dependencies** (⏳ or D:N)
2. **Blockers** (🚫 or B:N)
3. **Linked tasks** (🔗 or L:N)
4. **Assignees** (👤XX or 👥N or A:N)
5. **Due date warnings** (🔴, 📅, ⚠️ or OVERDUE/DUE)
6. **Time tracking** (⏱️ or T:)
7. **Task type emoji** (📝, 🐛, etc.)
8. **Status icon** (⚙️, ⬜, ✓, etc.)
9. **Task name**
10. **Priority** ((P1), (P2), etc.)
11. **Subtask count** ((0/5 complete))

## Color Meanings

### Emoji/Color Indicators
- 🟢 **Green**: Under time budget, on track
- 🔴 **Red**: Overdue, over budget, blocking
- 🟡 **Yellow**: Due soon, in progress, waiting on dependencies
- 🔵 **Blue**: Assigned users
- 🔵 **Cyan**: Links, estimates
- ⚫ **Black/Gray**: Task IDs

### Status Colors
- **Red**: Overdue tasks
- **Yellow**: Due today or soon
- **Green**: Completed tasks
- **Blue**: In progress
- **Gray**: Not started

## Use Cases

### Finding Blockers
```bash
# Find tasks blocking others
cum h --all | grep "🚫"
```

### Finding Overdue Tasks
```bash
# Find overdue tasks
cum h --all | grep "🔴"
```

### Finding Unassigned Tasks
```bash
# Find tasks without assignees (no 👤 or 👥 indicator)
cum h --all | grep -v "👤\|👥"
```

### Finding Tasks with Dependencies
```bash
# Find tasks waiting on dependencies
cum h --all | grep "⏳"
```

## Toggling Indicators

Currently, all indicators are shown by default when data is available.

Future options (planned):
- `--no-deps`: Hide dependency/blocker indicators
- `--no-assign`: Hide assignee indicators
- `--no-due`: Hide due date warnings
- `--no-time`: Hide time tracking

## API Data Requirements

For indicators to appear, tasks must have the corresponding data:

- **Dependencies**: `dependencies` field with `type: "waiting_on"` or `type: "blocking"`
- **Linked tasks**: `linked_tasks` array
- **Assignees**: `assignees` array with user objects
- **Due dates**: `due_date` timestamp (milliseconds)
- **Time tracking**: `time_estimate` and/or `time_spent` (milliseconds)

## Setting Dependencies via CLI

### Add dependency (this task waits for another)
```bash
# Task abc123 depends on xyz789
cum task abc123 add-dependency --depends-on xyz789
```

### Add blocker (this task blocks another)
```bash
# Task abc123 blocks xyz789
cum task abc123 add-dependency --blocks xyz789
```

### Add linked task
```bash
# Link task abc123 to xyz789
cum task abc123 add-link xyz789
```

## Performance Note

All indicators are calculated from existing task data in the API response. No additional API calls are made, so there is no performance impact on hierarchy view rendering.

## Examples with Real Data

### Sprint Planning View
```
└─Sprint Tasks
  ├─[abc] 👤JD ⚠️1d ⏱️0.0/8.0h 📝 ⚙️ API endpoints (0/3 complete)
  │ ├─[def] 👤JD ⏱️2.0/3.0h 📝 ⚙️ GET /users
  │ ├─[ghi] 👤MS 📝 ⬜ POST /users
  │ └─[jkl] ⏳2 📝 ⬜ Integration tests
  └─[mno] 🚫1 👤AB 🔴2d ⏱️15.0/8.0h 📝 ⚙️ Database migration
```

**What this tells us:**
- Task `abc`: Assigned to JD, due tomorrow, 8h estimated, in development, has 3 subtasks
- Task `def`: Assigned to JD, 2h spent of 3h estimated (under budget), in development
- Task `ghi`: Assigned to MS, not started
- Task `jkl`: Waiting on 2 other tasks before it can start
- Task `mno`: Blocking 1 other task, assigned to AB, 2 days overdue, 15h spent on 8h estimate (over budget)

### Bug Triage View
```
└─Bugs
  ├─[bug1] 🔗2 👥3 🔴7d 📝 ⚙️ Critical: Data loss on save
  ├─[bug2] 👤JD ⚠️3d 📝 ⚙️ Memory leak in worker
  └─[bug3] 👤MS 📝 ⬜ UI flickers on scroll
```

**What this tells us:**
- `bug1`: Linked to 2 tasks, assigned to 3 people, 7 days overdue - needs attention!
- `bug2`: Assigned to JD, due in 3 days
- `bug3`: Assigned to MS, not started yet

## Future Enhancements

Planned additions:
- **Watchers**: 👁️N (show number of watchers)
- **Comments**: 💬N (show comment count)
- **Checklists**: ☑️N (show checklist progress)
- **Custom fields**: Show important custom field values
- **Tags**: #tag (show task tags inline)
- **Recurrence**: 🔄 (show if task is recurring)

## Feedback

These indicators help you quickly understand task relationships and status at a glance without needing to open each task individually.
