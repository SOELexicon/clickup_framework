# Tree Formatting Rules for Hierarchy Display

## Overview
The tree formatter creates a hierarchical view of tasks using box-drawing characters. This document defines the exact rules for proper alignment and visual flow.

## Core Principles

### 1. **Consistent 4-Character Width**
All tree elements use exactly 4 characters for each indentation level:
- Branch indicators: `├── ` or `└── ` (4 chars: connector + 2 dashes + space)
- Continuation pipe: `│   ` (4 chars: pipe + 3 spaces)
- Empty space: `    ` (4 chars: 4 spaces)

### 2. **Tree Structure Lines (Task Names)**
- **Non-last item**: `├── ` (branch continues)
- **Last item**: `└── ` (branch ends)

### 3. **Detail Lines (Descriptions, Dates, etc.)**

Detail lines follow the task name and show metadata (descriptions, dates, tags, etc.).

#### Rule for Detail Line Prefixes:
```
if task has children:
    all detail lines use: child_prefix + "│   " (continuation)
else:
    first N-1 detail lines use: child_prefix + "│   " (continuation)
    last detail line uses: child_prefix + "└─  " (closure)
```

Where `child_prefix` is:
- `parent_prefix + "│   "` if task is NOT last in its level
- `parent_prefix + "    "` if task IS last in its level

## Visual Examples

### Task WITH Children
```
├── [task1] Task with children
│   │   📝 Description: This is a task with children
│   │   📅 Created: 2025-11-15
│   ├── [child1] First child
│   └── [child2] Second child
```
**Why**: Detail lines continue with `│` because children follow below.

### Task WITHOUT Children (Not Last)
```
├── [task2] Task without children (not last)
│   │   📝 Description: This is a task without children
│   └─  📅 Created: 2025-11-15
```
**Why**: Last detail line closes with `└─` because no children follow.

### Task WITHOUT Children (Last Item)
```
└── [task3] Task without children (last)
    │   📝 Description: This is a task without children
    └─  📅 Created: 2025-11-15
```
**Why**: Child prefix uses spaces instead of pipe (parent is last), but detail closure still uses `└─`.

## Multi-Level Example

```
└── [root] Root Task (0/2 complete)
    │   📝 Description: Root level task
    │   📅 Created: 2025-11-15
    ├── [child1] Child 1 (0/1 complete)
    │   │   📝 Description: First child
    │   │   📅 Created: 2025-11-15
    │   └── [grandchild1] Grandchild 1
    │       │   📝 Description: Grandchild with no children
    │       └─  📅 Created: 2025-11-15
    └── [child2] Child 2
        │   📝 Description: Second child (last item, no children)
        └─  📅 Created: 2025-11-15
```

## Prefix Calculation Algorithm

For each task at depth N:

1. **Calculate child_prefix for THIS task's details and children**:
   ```python
   if task is last item at its level:
       child_prefix = parent_prefix + "    "  # 4 spaces
   else:
       child_prefix = parent_prefix + "│   "  # pipe + 3 spaces
   ```

2. **Format detail lines**:
   ```python
   children = get_children(task)
   for i, detail_line in enumerate(detail_lines):
       if i == len(detail_lines) - 1 and not children:
           # Last detail line, no children: close with └─
           detail_prefix = child_prefix + "└─  "
       else:
           # Other detail lines, or has children: continue with │
           detail_prefix = child_prefix + "│   "
       output(detail_prefix + detail_line)
   ```

3. **Format children**:
   ```python
   for j, child in enumerate(children):
       if j == len(children) - 1:
           branch = "└── "
       else:
           branch = "├── "
       output(child_prefix + branch + child_name)
       # Recursively format child with child_prefix as its parent_prefix
   ```

## Character-by-Character Breakdown

Example task at level 3 (non-last, with children):
```
        ├── [abc123] Task Name
        │   │   📝 Description: Sample task
        │   │   📅 Created: 2025-11-15
        │   ├── [child1] Child task
```

Line 1: `        ├── [abc123] Task Name`
- Positions 0-7: 8 spaces (2 levels × 4 chars)
- Positions 8-11: `├── ` (branch indicator)
- Position 12+: task content

Line 2: `        │   │   📝 Description: Sample task`
- Positions 0-7: 8 spaces (2 levels × 4 chars)
- Positions 8-11: `│   ` (child_prefix continuation)
- Positions 12-15: `│   ` (detail continuation)
- Position 16+: detail content

Line 3: `        │   │   📅 Created: 2025-11-15`
- Same as line 2 (not last detail, or has children)

Line 4: `        │   ├── [child1] Child task`
- Positions 0-7: 8 spaces
- Positions 8-11: `│   ` (child_prefix)
- Positions 12-15: `├── ` (child branch)
- Position 16+: child content

## Implementation Files

- **tree.py:84-100**: Detail line formatting logic
- **task_formatter.py:348-485**: Detail content generation (no spacing added)
- **hierarchy.py:376-391**: Children filtering and tree building

## Testing Commands

```bash
# Test single task with children
cum h 86c6hvba2

# Test single task without children
cum h 86c6hvban

# Test full hierarchy
cum h 86c6hvba1

# Test deep nesting (7 levels)
cum h 86c6hvbae
```

## Common Mistakes to Avoid

1. ❌ Adding extra spacing in `task_formatter.py`
   - Detail lines should have NO prefix spacing
   - ALL spacing is handled by `tree.py`

2. ❌ Using `└─` for detail lines when task has children
   - Only close detail lines when `not children`

3. ❌ Inconsistent character widths
   - Always use 4-character units
   - `├── ` is 4 chars, `│   ` is 4 chars, `    ` is 4 chars

4. ❌ Forgetting to check `is_last_item` for child_prefix
   - Last items use `"    "` (spaces)
   - Non-last items use `│   ` (pipe)

## Quick Reference

```python
# Task line
prefix + branch + task_name
where branch = "└── " if is_last else "├── "

# Child prefix
child_prefix = prefix + ("    " if is_last else "│   ")

# Detail lines
for each detail_line:
    if is_last_detail and not has_children:
        detail_prefix = child_prefix + "└─  "
    else:
        detail_prefix = child_prefix + "│   "
    print(detail_prefix + detail_line)

# Children
for each child:
    print(child_prefix + child_branch + child_name)
    # Recurse with child_prefix as new prefix
```
