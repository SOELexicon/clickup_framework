# ClickUp Task Type Manager

Interactive sidebar component for managing ClickUp custom task types - create, update, and bulk import from CSV.

## Features

- ✅ **View all task types** - See all custom task types with their icons and descriptions
- ✅ **Create new task types** - Form-based creation with icon preview
- ✅ **Update existing** - Edit task type names, descriptions, and icons
- ✅ **CSV Import** - Bulk import task types from CSV data
- ✅ **Auto-detection** - Automatically detects workspace ID and session token
- ✅ **Icon support** - Full Font Awesome icon support (fas, far, fab)

## Usage

### Method 1: Standalone HTML Page

1. Open `task_type_manager_standalone.html` in your browser
2. Enter your workspace ID and session token when prompted
3. Use the interface to manage task types

### Method 2: Bookmarklet (Inject into ClickUp)

1. Copy the contents of `task_type_manager.bookmarklet.js`
2. Create a bookmark with that as the URL
3. Navigate to ClickUp Settings > Task Types page
4. Click the bookmark to inject the sidebar

### Method 3: Console Injection

1. Navigate to ClickUp Settings > Task Types page
2. Open DevTools (F12) > Console
3. Paste the contents of `task_type_manager.js`
4. The sidebar will appear

## CSV Import Format

```csv
name,name_plural,description,icon
Bug,Bugs,Software defects that need fixing,bug
Feature,Features,New functionality being added,rocket
Documentation,Docs,Documentation and guides,book
Warning,Warnings,Warning tasks,triangle-exclamation
```

### CSV Columns

- `name` (required) - Singular name of the task type
- `name_plural` (optional) - Plural name (defaults to name + "s")
- `description` (optional) - Description text
- `icon` (optional) - Font Awesome icon name (defaults to "circle")
- `icon_source` (optional) - "fas", "far", or "fab" (defaults to "fas")

## API Endpoints Used

- **GET** `/tasks/v1/{workspace_id}/customItems` - List all task types
- **POST** `/tasks/v1/{workspace_id}/customItem` - Create new task type
- **PUT** `/tasks/v1/{workspace_id}/customItem/{id}` - Update task type

## Session Token Setup

If auto-detection fails, set it manually:

```javascript
window.__CLICKUP_SESSION_TOKEN = "your-jwt-token-here";
```

To get your session token:
1. Open DevTools (F12) > Network tab
2. Refresh the page
3. Find any request to clickup.com
4. Copy the "authorization" header value (JWT starting with "eyJ")

## Icon Reference

Common Font Awesome icons:
- `bug` - Bug icon
- `rocket` - Feature/launch
- `book` - Documentation
- `flask` - Testing
- `shield-alt` - Security
- `triangle-exclamation` - Warning
- `user-circle` - Account/User
- `folder-open` - Project
- And 100+ more...

See [Font Awesome Icons](https://fontawesome.com/icons) for the full list.
