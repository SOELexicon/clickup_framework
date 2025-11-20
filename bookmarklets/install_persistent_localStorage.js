// Persistent Auto-Inject via localStorage (No Service Worker Needed!)
// This works by storing the bookmarklet code and auto-injecting on page load
// Run this ONCE in the browser console on any ClickUp page

(function() {
  'use strict';

  // Step 1: Get the bookmarklet code
  async function getBookmarkletCode() {
    // Check if already stored
    const stored = localStorage.getItem('__TASK_TYPE_MANAGER_CODE');
    if (stored) {
      console.log('✅ Found stored bookmarklet code');
      return stored;
    }

    // Check if it's in a global variable (from manual load)
    if (window.__TASK_TYPE_MANAGER_CODE) {
      localStorage.setItem('__TASK_TYPE_MANAGER_CODE', window.__TASK_TYPE_MANAGER_CODE);
      return window.__TASK_TYPE_MANAGER_CODE;
    }

    // Try to fetch from URL
    try {
      const response = await fetch('https://raw.githubusercontent.com/your-repo/task_type_manager_complete.js');
      if (response.ok) {
        const code = await response.text();
        localStorage.setItem('__TASK_TYPE_MANAGER_CODE', code);
        return code;
      }
    } catch (e) {
      console.log('Could not fetch from URL');
    }

    // Prompt user
    console.warn('⚠️ Bookmarklet code not found. Please:');
    console.warn('1. Load the bookmarklet once manually, OR');
    console.warn('2. Paste the code: localStorage.setItem("__TASK_TYPE_MANAGER_CODE", "...code...")');
    return null;
  }

  // Step 2: Create auto-inject script
  async function installAutoInject() {
    const code = await getBookmarkletCode();
    
    if (!code) {
      alert('Please load the bookmarklet once first, then run this installer again.');
      return;
    }

    // Create the auto-inject script
    const autoInjectScript = `
(function() {
  'use strict';
  
  // Check if already injected
  if (window.__TASK_TYPE_MANAGER_AUTO_INJECTED) return;
  window.__TASK_TYPE_MANAGER_AUTO_INJECTED = true;
  
  // Get stored bookmarklet code
  const bookmarkletCode = localStorage.getItem('__TASK_TYPE_MANAGER_CODE');
  if (!bookmarkletCode) return;
  
  // Wait for DOM to be ready
  function inject() {
    if (document.getElementById('clickup-task-manager-sidebar')) return;
    
    const script = document.createElement('script');
    script.textContent = bookmarkletCode;
    (document.head || document.documentElement).appendChild(script);
  }
  
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', inject);
  } else {
    setTimeout(inject, 100);
  }
})();
    `;

    // Store the auto-inject script
    localStorage.setItem('__TASK_TYPE_MANAGER_AUTO_INJECT', autoInjectScript);
    localStorage.setItem('__TASK_TYPE_MANAGER_ENABLED', 'true');

    // Inject it now
    const script = document.createElement('script');
    script.textContent = autoInjectScript;
    document.head.appendChild(script);

    // Also inject it into the page for future loads
    // We'll use a MutationObserver to inject on navigation
    const observerScript = `
(function() {
  if (window.__TASK_TYPE_MANAGER_OBSERVER_SETUP) return;
  window.__TASK_TYPE_MANAGER_OBSERVER_SETUP = true;
  
  // Inject on current page
  const autoInject = localStorage.getItem('__TASK_TYPE_MANAGER_AUTO_INJECT');
  if (autoInject && localStorage.getItem('__TASK_TYPE_MANAGER_ENABLED') === 'true') {
    if (!document.getElementById('clickup-task-manager-sidebar')) {
      const script = document.createElement('script');
      script.textContent = autoInject;
      document.head.appendChild(script);
    }
  }
  
  // Watch for navigation (SPA)
  let lastUrl = location.href;
  new MutationObserver(() => {
    const url = location.href;
    if (url !== lastUrl) {
      lastUrl = url;
      setTimeout(() => {
        const autoInject = localStorage.getItem('__TASK_TYPE_MANAGER_AUTO_INJECT');
        if (autoInject && localStorage.getItem('__TASK_TYPE_MANAGER_ENABLED') === 'true') {
          if (!document.getElementById('clickup-task-manager-sidebar')) {
            const script = document.createElement('script');
            script.textContent = autoInject;
            document.head.appendChild(script);
          }
        }
      }, 500);
    }
  }).observe(document, { subtree: true, childList: true });
})();
    `;

    const observerScriptEl = document.createElement('script');
    observerScriptEl.textContent = observerScript;
    document.head.appendChild(observerScriptEl);

    console.log('✅ Persistent auto-inject installed!');
    console.log('📌 The bookmarklet will now auto-load on every ClickUp page.');
    console.log('💾 Code stored in localStorage.');
    console.log('');
    console.log('To disable: localStorage.removeItem("__TASK_TYPE_MANAGER_ENABLED")');
    console.log('To uninstall: localStorage.removeItem("__TASK_TYPE_MANAGER_CODE") && localStorage.removeItem("__TASK_TYPE_MANAGER_AUTO_INJECT")');
  }

  installAutoInject();
})();



