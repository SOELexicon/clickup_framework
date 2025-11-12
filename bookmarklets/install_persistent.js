// Persistent Auto-Inject Installation for Task Type Manager
// Run this ONCE in the browser console on any ClickUp page
// It will create a service worker that auto-injects the bookmarklet on every page load

(function() {
  'use strict';

  if (!('serviceWorker' in navigator)) {
    console.error('❌ Service Workers are not supported in this browser');
    return;
  }

  // Step 1: Load the bookmarklet code
  async function loadBookmarkletCode() {
    // Try to get it from a global variable first (if already loaded)
    if (window.__TASK_TYPE_MANAGER_CODE && window.__TASK_TYPE_MANAGER_CODE.length > 100) {
      console.log('✅ Found bookmarklet code in window.__TASK_TYPE_MANAGER_CODE');
      return window.__TASK_TYPE_MANAGER_CODE;
    }

    // Try to read from localStorage (if stored by the bookmarklet)
    try {
      const stored = localStorage.getItem('__TASK_TYPE_MANAGER_CODE');
      if (stored && stored.length > 100) {
        console.log('✅ Found bookmarklet code in localStorage');
        window.__TASK_TYPE_MANAGER_CODE = stored;
        return stored;
      }
    } catch (e) {
      console.log('Could not read from localStorage');
    }

    // Try to find it in script tags on the page
    try {
      const scripts = document.getElementsByTagName('script');
      for (let script of scripts) {
        if (script.textContent && 
            script.textContent.includes('clickup-task-manager-sidebar') && 
            script.textContent.includes('Task Type Manager') &&
            script.textContent.length > 1000) {
          console.log('✅ Found bookmarklet code in script tag');
          const code = script.textContent;
          // Store it for future use
          window.__TASK_TYPE_MANAGER_CODE = code;
          try {
            localStorage.setItem('__TASK_TYPE_MANAGER_CODE', code);
          } catch (e) {}
          return code;
        }
      }
    } catch (e) {
      console.log('Could not search script tags');
    }

    // Try to fetch from a hosted URL (update this to your hosted bookmarklet)
    try {
      const response = await fetch('https://raw.githubusercontent.com/your-repo/task_type_manager_complete.js');
      if (response.ok) {
        const code = await response.text();
        console.log('✅ Fetched bookmarklet code from URL');
        // Store it
        window.__TASK_TYPE_MANAGER_CODE = code;
        try {
          localStorage.setItem('__TASK_TYPE_MANAGER_CODE', code);
        } catch (e) {}
        return code;
      }
    } catch (e) {
      console.log('Could not fetch bookmarklet from URL');
    }

    // Fallback: Provide clear instructions
    console.warn('');
    console.warn('⚠️ Bookmarklet code not found. Please follow these steps:');
    console.warn('');
    console.warn('Option 1: Load bookmarklet first (Recommended)');
    console.warn('  1. Copy the entire contents of task_type_manager_complete.js');
    console.warn('  2. Paste it in this console and press Enter');
    console.warn('  3. The bookmarklet will run and store its code automatically');
    console.warn('  4. Then run this installer again');
    console.warn('');
    console.warn('Option 2: Manually set the code');
    console.warn('  1. Copy the entire contents of task_type_manager_complete.js');
    console.warn('  2. Run this command:');
    console.warn('     window.__TASK_TYPE_MANAGER_CODE = `...paste code here...`;');
    console.warn('  3. Then run this installer again');
    console.warn('');
    console.warn('Option 3: Use simpler localStorage installer');
    console.warn('  Use install_persistent_localStorage.js instead (no service worker needed)');
    console.warn('');
    
    // Try to open a prompt for manual entry
    const userCode = prompt(
      'Paste the bookmarklet code here (or click Cancel):\n\n' +
      'You can find the code in: bookmarklets/task_type_manager_complete.js\n\n' +
      'Or click Cancel and follow the instructions in the console.'
    );
    
    if (userCode && userCode.trim().length > 100) {
      window.__TASK_TYPE_MANAGER_CODE = userCode.trim();
      try {
        localStorage.setItem('__TASK_TYPE_MANAGER_CODE', userCode.trim());
        console.log('✅ Code stored! Continuing installation...');
        return userCode.trim();
      } catch (e) {
        console.log('⚠️ Could not store in localStorage, but code is set');
        return userCode.trim();
      }
    }
    
    return null;
  }

  // Step 2: Create and register service worker
  async function installServiceWorker() {
    const bookmarkletCode = await loadBookmarkletCode();
    
    if (!bookmarkletCode) {
      alert('Please load the bookmarklet once first, then run this installer again.');
      return;
    }

    // Escape the code for embedding
    const escapedCode = bookmarkletCode
      .replace(/\\/g, '\\\\')
      .replace(/`/g, '\\`')
      .replace(/\${/g, '\\${');

    // Create service worker that injects the bookmarklet
    const swCode = `
const BOOKMARKLET_CODE = \`${escapedCode}\`;

self.addEventListener('install', (event) => {
  console.log('[Task Type Manager] Service Worker installing...');
  event.waitUntil(self.skipWaiting());
});

self.addEventListener('activate', (event) => {
  console.log('[Task Type Manager] Service Worker activating...');
  event.waitUntil(self.clients.claim());
});

// Inject bookmarklet into all ClickUp pages
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  
  // Only intercept ClickUp HTML pages
  if (
    (url.hostname.includes('clickup.com') || url.hostname.includes('clickup-stg.com')) &&
    event.request.method === 'GET' &&
    event.request.headers.get('accept')?.includes('text/html') &&
    !url.searchParams.has('sw-bypass')
  ) {
    event.respondWith(
      (async () => {
        try {
          const response = await fetch(event.request);
          const html = await response.clone().text();
          
          // Skip if already injected
          if (html.includes('task-type-manager-persistent-injected')) {
            return response;
          }
          
          // Inject the bookmarklet loader script
          const injectionScript = \`
            (function() {
              if (window.__TASK_TYPE_MANAGER_PERSISTENT_LOADED) return;
              window.__TASK_TYPE_MANAGER_PERSISTENT_LOADED = true;
              
              // Small delay to ensure DOM is ready
              if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', injectBookmarklet);
              } else {
                setTimeout(injectBookmarklet, 100);
              }
              
              function injectBookmarklet() {
                const script = document.createElement('script');
                script.textContent = \` + BOOKMARKLET_CODE + \`;
                (document.head || document.documentElement).appendChild(script);
              }
            })();
          \`;
          
          const injectedHTML = html.replace(
            '</head>',
            '<script>' + injectionScript + '</script><meta name="task-type-manager-persistent-injected" content="true"></head>'
          );
          
          return new Response(injectedHTML, {
            headers: response.headers,
            status: response.status,
            statusText: response.statusText
          });
        } catch (error) {
          console.error('[Task Type Manager SW] Injection error:', error);
          return fetch(event.request);
        }
      })()
    );
  }
});
    `;

    // Create blob URL for service worker
    const swBlob = new Blob([swCode], { type: 'application/javascript' });
    const swUrl = URL.createObjectURL(swBlob);

    try {
      // Unregister any existing task type manager service workers
      const existingRegistrations = await navigator.serviceWorker.getRegistrations();
      for (const registration of existingRegistrations) {
        const scriptURL = registration.active?.scriptURL || registration.installing?.scriptURL || '';
        if (scriptURL.includes('task-type-manager') || scriptURL.includes('blob:')) {
          await registration.unregister();
          console.log('🗑️ Unregistered existing service worker');
        }
      }

      // Register new service worker with a unique scope
      // Note: Service workers must be registered from the same origin
      // This will only work if run from clickup.com domain
      const registration = await navigator.serviceWorker.register(swUrl, {
        scope: window.location.origin + '/'
      });

      console.log('✅ Task Type Manager Service Worker registered successfully!');
      console.log('📌 The bookmarklet will now automatically load on all ClickUp pages.');
      console.log('🔄 Refresh any ClickUp page to see it in action.');
      console.log('');
      console.log('To uninstall, run:');
      console.log('navigator.serviceWorker.getRegistrations().then(regs => regs.forEach(r => r.unregister()))');

      // Clean up blob URL after a delay
      setTimeout(() => URL.revokeObjectURL(swUrl), 2000);

      // Wait for activation
      if (registration.installing) {
        registration.installing.addEventListener('statechange', function() {
          if (this.state === 'activated') {
            console.log('✅ Service Worker activated!');
          }
        });
      }

      return registration;
    } catch (error) {
      console.error('❌ Failed to register service worker:', error);
      URL.revokeObjectURL(swUrl);
      throw error;
    }
  }

  // Run installation
  installServiceWorker().catch(console.error);
})();

