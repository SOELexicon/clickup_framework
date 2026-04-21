# Auto-Inject Task Type Manager via Service Worker

This allows the Task Type Manager bookmarklet to automatically load on all ClickUp pages without needing to click a bookmark each time.

## Quick Install

1. **Load the bookmarklet code first** (so it's available):
   - Open any ClickUp page
   - Open DevTools Console (F12)
   - Paste the contents of `task_type_manager_complete.js` and run it once
   - This stores the code in `window.__TASK_TYPE_MANAGER_CODE`

2. **Install the service worker**:
   - In the same console, paste and run the contents of `install_auto_inject.js`
   - The service worker will be registered

3. **Refresh the page** - The bookmarklet should now auto-load!

## How It Works

The service worker:
1. Intercepts all HTML requests to `clickup.com`
2. Injects a script tag into the `<head>` that loads the bookmarklet
3. The bookmarklet runs automatically on every page load

## Manual Installation

If you want to host the service worker yourself:

1. Host `task_type_manager_complete.js` on a server
2. Update `install_auto_inject.js` to point to your hosted URL
3. Run the installation script

## Uninstall

To remove the service worker:

```javascript
navigator.serviceWorker.getRegistrations().then(registrations => {
  registrations.forEach(reg => {
    if (reg.scope.includes('clickup.com') || reg.active?.scriptURL.includes('task-type-manager')) {
      reg.unregister();
      console.log('Service worker unregistered');
    }
  });
});
```

## Limitations

- Service workers only work on HTTPS (or localhost)
- The service worker must be registered from the same origin (clickup.com)
- You may need to register it from a browser extension or use a different approach

## Alternative: Browser Extension

For a more persistent solution, consider creating a browser extension that:
1. Injects the bookmarklet on ClickUp pages
2. Persists across browser sessions
3. Can be installed from Chrome Web Store

## Alternative: User Script Manager

You can also use Tampermonkey/Greasemonkey to auto-inject:

```javascript
// ==UserScript==
// @name         ClickUp Task Type Manager
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  Auto-inject Task Type Manager
// @author       You
// @match        https://app.clickup.com/*
// @grant        none
// ==/UserScript==

(function() {
    'use strict';
    // Paste bookmarklet code here
})();
```



