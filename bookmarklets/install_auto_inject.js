// Install Auto-Inject Service Worker for Task Type Manager
// Paste this entire script into the browser console on any ClickUp page

(function() {
  'use strict';

  // Read the bookmarklet code
  async function getBookmarkletCode() {
    // Try to fetch from a URL first (if you host it)
    try {
      const response = await fetch('https://your-domain.com/task_type_manager_complete.js');
      if (response.ok) {
        return await response.text();
      }
    } catch (e) {
      console.log('Could not fetch bookmarklet from URL, will use inline version');
    }

    // Fallback: You'll need to paste the bookmarklet code here
    // Or we can fetch it from the current page if it's already loaded
    return window.__TASK_TYPE_MANAGER_CODE || '// Bookmarklet code not found';
  }

  async function installServiceWorker() {
    if (!('serviceWorker' in navigator)) {
      console.error('❌ Service Workers are not supported in this browser');
      return;
    }

    // Get bookmarklet code
    const bookmarkletCode = await getBookmarkletCode();
    
    // Escape the code for embedding in service worker
    const escapedCode = bookmarkletCode
      .replace(/\\/g, '\\\\')
      .replace(/`/g, '\\`')
      .replace(/\${/g, '\\${');

    // Create service worker code
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

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  
  // Only intercept ClickUp HTML pages
  if (
    url.hostname.includes('clickup.com') &&
    event.request.method === 'GET' &&
    event.request.headers.get('accept')?.includes('text/html')
  ) {
    event.respondWith(
      (async () => {
        try {
          const response = await fetch(event.request);
          const html = await response.clone().text();
          
          // Check if already injected
          if (html.includes('task-type-manager-auto-injected')) {
            return response;
          }
          
          // Inject the bookmarklet
          const injectedHTML = html.replace(
            '</head>',
            \`<script>
              (function() {
                if (window.__TASK_TYPE_MANAGER_LOADED) return;
                window.__TASK_TYPE_MANAGER_LOADED = true;
                const script = document.createElement('script');
                script.textContent = \` + BOOKMARKLET_CODE + \`;
                (document.head || document.documentElement).appendChild(script);
              })();
            </script>
            <meta name="task-type-manager-auto-injected" content="true"></head>\`
          );
          
          return new Response(injectedHTML, {
            headers: response.headers,
            status: response.status,
            statusText: response.statusText
          });
        } catch (error) {
          console.error('[Task Type Manager] Injection error:', error);
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
      // Unregister any existing service worker first
      const existingRegistrations = await navigator.serviceWorker.getRegistrations();
      for (const registration of existingRegistrations) {
        if (registration.scope.includes('clickup.com') || registration.active?.scriptURL.includes('task-type-manager')) {
          await registration.unregister();
          console.log('Unregistered existing service worker');
        }
      }

      // Register new service worker
      const registration = await navigator.serviceWorker.register(swUrl, {
        scope: '/'
      });

      console.log('✅ Task Type Manager Service Worker registered!');
      console.log('📌 The bookmarklet will now automatically load on all ClickUp pages.');
      console.log('🔄 Refresh the page to see it in action.');

      // Clean up blob URL
      setTimeout(() => URL.revokeObjectURL(swUrl), 1000);

      return registration;
    } catch (error) {
      console.error('❌ Failed to register service worker:', error);
      URL.revokeObjectURL(swUrl);
    }
  }

  // Run installation
  installServiceWorker();
})();



