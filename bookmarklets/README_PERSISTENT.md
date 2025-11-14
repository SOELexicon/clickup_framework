# Persistent Auto-Inject for Task Type Manager

Make the bookmarklet automatically load on every ClickUp page without clicking the bookmark each time.

## ⚠️ Important Limitation

**Service workers can only be registered from the same origin.** Since ClickUp controls `clickup.com`, you **cannot** register a service worker from a bookmarklet running on their domain.

## ✅ Working Solutions

### Option 1: localStorage Auto-Inject (Easiest - No Extension Needed)

This uses localStorage to store the bookmarklet code and auto-injects on page load.

**Installation:**

1. **Load the bookmarklet once** (to store the code):
   ```javascript
   // Paste task_type_manager_complete.js in console and run it
   ```

2. **Install auto-inject**:
   ```javascript
   // Paste install_persistent_localStorage.js in console and run it
   ```

3. **Refresh any ClickUp page** - The sidebar will auto-load!

**How it works:**
- Stores bookmarklet code in `localStorage`
- Injects a script that checks localStorage on every page load
- Works across browser sessions
- No service worker needed!

**Uninstall:**
```javascript
localStorage.removeItem('__TASK_TYPE_MANAGER_ENABLED');
localStorage.removeItem('__TASK_TYPE_MANAGER_CODE');
localStorage.removeItem('__TASK_TYPE_MANAGER_AUTO_INJECT');
```

### Option 2: Tampermonkey/Greasemonkey (Recommended)

**Best for persistent, reliable injection.**

1. Install [Tampermonkey](https://www.tampermonkey.net/) browser extension
2. Create new script
3. Paste the contents of `tampermonkey_script.user.js`
4. Update the `@match` URLs if needed
5. Update the fetch URL to point to your hosted bookmarklet (or inline it)

**Advantages:**
- ✅ Works reliably
- ✅ Persists across sessions
- ✅ No manual installation needed
- ✅ Works on all ClickUp pages automatically

### Option 3: Browser Extension (Most Professional)

Create a Chrome/Firefox extension that:
- Injects the bookmarklet on ClickUp pages
- Can be published to Chrome Web Store
- Most user-friendly

### Option 4: Service Worker (Advanced - Limited)

The `install_persistent.js` script attempts to register a service worker, but **this will fail** unless:
- You're running it from a browser extension
- You have control over the clickup.com domain
- You modify ClickUp's existing service worker (complex)

## Recommended: Use Option 1 (localStorage) or Option 2 (Tampermonkey)

Both work reliably without needing browser extensions or service workers!
