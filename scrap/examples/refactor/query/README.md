# Task Query Language (TQL)

The Task Query Language (TQL) provides a powerful way to filter and query tasks in the ClickUp JSON Manager. It offers a SQL-like syntax for expressing complex query conditions.

## Installation

The TQL module is part of the ClickUp JSON Manager project. No additional installation is required.

## Basic Usage

```python
from refactor.query import TQL

# Create a TQL instance
tql = TQL()

# Parse a query
query = tql.parse("status == 'to do' AND priority > 2")

# Evaluate a single task
matches = tql.evaluate(query, task)

# Filter a list of tasks
filtered_tasks = tql.filter_tasks(tasks, "status == 'to do' AND priority > 2")

# Get a human-readable explanation of a query
explanation = tql.explain("status == 'to do' AND priority > 2")
print(explanation)
```

### Using TQL with CLI Commands

The Task Query Language can be used with the ClickUp JSON Manager CLI:

```bash
# Filter tasks using a TQL query
./cujmrefactor.sh query 000_clickup_tasks_template.json "status == 'to do' AND priority > 2"

# Show tasks matching a complex condition
./cujmrefactor.sh query 000_clickup_tasks_template.json "tags in 'frontend' AND priority >= 3" | cat

# Save a frequently used query
./cujmrefactor.sh save-query 000_clickup_tasks_template.json "my-high-priority" "priority < 2 AND NOT status == 'complete'"

# Run a saved query
./cujmrefactor.sh run-query 000_clickup_tasks_template.json "my-high-priority" | cat
```

## TQL Syntax

TQL syntax supports field expressions, comparisons, logical operators, and parentheses for grouping.

### Field References

Reference task fields directly by name:
```
status
priority
name
tags
assignee
```

### Literals

- Strings: `'value'` or `"value"`
- Numbers: `123` or `45.67`
- Booleans: `true` or `false`
- Null: `null` or `none`
- Lists: Handled implicitly in comparisons like `'tag' in tags`

### Comparison Operators

- Equality: `==`, `!=`
- Ordering: `>`, `>=`, `<`, `<=`
- Membership: `in`, `not in`
- Text operations: `contains`, `starts_with`, `ends_with`
- Existence: `exists`
- Identity: `is`, `is not`

### Logical Operators

- AND: `AND` or `and`
- OR: `OR` or `or`
- NOT: `NOT` or `not`

### Parentheses

Use parentheses to group expressions and control the evaluation order.

## Query Examples

### Simple Queries

```
# Tasks with "to do" status
status == 'to do'

# High priority tasks
priority >= 3

# Tasks with a specific tag
'bug' in tags
# OR (both work equally well)
tags in 'bug'

# Tasks assigned to Alice
assignee == 'alice'

# Tasks containing a word in the name
name contains 'database'

# Tasks that exist in a specific list
list == 'Sprint 23'
```

### Complex Queries

```
# High priority to-do tasks
status == 'to do' AND priority >= 3

# Tasks that are either complete or low priority
status == 'complete' OR priority <= 1

# Tasks with specific tags that are not complete
'frontend' in tags AND NOT status == 'complete'

# Tasks in a specific folder with high priority
folder == 'Development' AND priority >= 3

# Tasks with a comment from a specific user that are due soon
author in 'alice' AND due_date < '2023-09-01'

# Tasks that need attention (high priority and not complete)
priority < 3 AND NOT status == 'complete'
```

### Using Parentheses

```
# Tasks that are either (high priority and to-do) or (any priority and in progress)
(priority >= 3 AND status == 'to do') OR (status == 'in progress')

# Tasks that are not (complete or low priority)
NOT (status == 'complete' OR priority <= 1)

# Complex nested conditions
(status == 'to do' AND (priority < 2 OR 'urgent' in tags)) OR (status == 'in progress' AND due_date < '2023-09-01')
```

## Available Fields

The following task fields can be referenced in TQL queries:

| Field Name    | Description                     | Example                     |
|---------------|---------------------------------|-----------------------------|
| status        | Task status                     | `status == 'to do'`         |
| type          | Task type                       | `type == 'bug'`             |
| priority      | Task priority                   | `priority >= 3`             |
| tag, tags     | Task tags                       | `'frontend' in tags`        |
| name          | Task name                       | `name contains 'database'`  |
| description   | Task description                | `description contains 'API'`|
| author        | Comment authors                 | `'alice' in author`         |
| id            | Task ID                         | `id == 'tsk_123'`           |
| parent        | Parent task ID                  | `parent == 'tsk_456'`       |
| list          | List name                       | `list == 'Sprint 23'`       |
| folder        | Folder name                     | `folder == 'Development'`   |
| space         | Space name                      | `space == 'Product'`        |
| assignee      | Task assignee                   | `assignee == 'alice'`       |
| created_at    | Creation date                   | `created_at > '2023-08-01'` |
| updated_at    | Last update date                | `updated_at > '2023-08-15'` |
| due_date      | Due date                        | `due_date < '2023-09-01'`   |

## Special Features

### Bidirectional "in" Operator

TQL supports bidirectional usage of the "in" operator, which works in both directions:

```
# These two queries are equivalent
'frontend' in tags
tags in 'frontend'

# These two queries are equivalent
'alice' in author
author in 'alice'
```

This flexibility allows for more intuitive queries, especially when checking if a field contains a value or if a value is in a field.

### Case Sensitivity

String comparisons are case-insensitive by default:

```
# These are equivalent
status == 'to do'
status == 'TO DO'
status == 'To Do'
```

### Numeric Comparison

String values that represent numbers can be compared numerically:

```
# String field with numeric content compared as number
priority == '3'  # Same as priority == 3
```

### Intelligent Text Comparisons

TQL supports intelligent text operations with the following operators:

```
# Find tasks containing specific text
name contains 'database'

# Find tasks starting with specific text
name starts_with 'Update'

# Find tasks ending with specific text
name ends_with 'migration'
```

## Error Handling

TQL provides detailed error messages for syntax errors and evaluation issues:

```python
try:
    filtered_tasks = tql.filter_tasks(tasks, "status = 'to do'")  # Syntax error - should be ==
except ValueError as e:
    print(f"Query error: {e}")
    # Output: Query error: Error parsing TQL query: Unexpected token in query: Token(FIELD, '=')
```

## Advanced Usage

### Working with Dates

Dates are compared as strings in lexicographic order:

```
# Tasks created after a specific date
created_at > '2023-08-01'

# Tasks due before a specific date
due_date < '2023-09-01'

# Tasks updated in a specific date range
updated_at > '2023-08-01' AND updated_at < '2023-09-01'
```

### Combining Multiple Conditions

Complex queries can combine multiple conditions:

```
# Find high-priority tasks assigned to Alice that are not complete
priority < 3 AND assignee == 'alice' AND NOT status == 'complete'

# Find tasks that need review or are blocking other tasks
status == 'in review' OR exists(blocks)
```

### Performance Tips

For better performance with large datasets:

1. Use specific field comparisons instead of text searches when possible
2. Put the most restrictive conditions first in AND expressions
3. Use parentheses to explicitly control evaluation order
4. Avoid unnecessary complex expressions that could be simplified

## Contributing

To contribute to the TQL module, see the CONTRIBUTING.md file in the main repository. 