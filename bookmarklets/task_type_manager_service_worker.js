// Service Worker to Auto-Inject Task Type Manager Bookmarklet
// Register this service worker to automatically inject the bookmarklet on ClickUp pages

const SW_VERSION = '1.0.0';
const BOOKMARKLET_CACHE_NAME = 'task-type-manager-bookmarklet-v1';

// Install event - cache the bookmarklet code
self.addEventListener('install', (event) => {
  console.log('[Task Type Manager SW] Installing...');
  event.waitUntil(
    (async () => {
      // Store the bookmarklet code in cache
      const bookmarkletCode = await fetchBookmarkletCode();
      const cache = await caches.open(BOOKMARKLET_CACHE_NAME);
      await cache.put(
        new Request('/task-type-manager-bookmarklet.js'),
        new Response(bookmarkletCode, {
          headers: { 'Content-Type': 'application/javascript' }
        })
      );
      await self.skipWaiting();
    })()
  );
});

// Activate event
self.addEventListener('activate', (event) => {
  console.log('[Task Type Manager SW] Activating...');
  event.waitUntil(
    (async () => {
      await self.clients.claim();
      // Clean up old caches
      const cacheNames = await caches.keys();
      await Promise.all(
        cacheNames
          .filter(name => name.startsWith('task-type-manager') && name !== BOOKMARKLET_CACHE_NAME)
          .map(name => caches.delete(name))
      );
    })()
  );
});

// Fetch the bookmarklet code (you'll need to host this or inline it)
async function fetchBookmarkletCode() {
  // Option 1: Fetch from a URL (if you host the bookmarklet)
  try {
    const response = await fetch('https://your-domain.com/task_type_manager_complete.js');
    if (response.ok) {
      return await response.text();
    }
  } catch (e) {
    console.warn('[Task Type Manager SW] Could not fetch bookmarklet from URL, using inline version');
  }

  // Option 2: Return inline bookmarklet code
  // This is the full bookmarklet code - you'll need to paste it here
  return `
    // Task Type Manager Bookmarklet Code
    // This will be injected into ClickUp pages
    (function(){
      'use strict';
      // ... [paste full bookmarklet code here] ...
    })();
  `;
}

// Listen for messages from pages
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'GET_BOOKMARKLET') {
    event.waitUntil(
      (async () => {
        const cache = await caches.open(BOOKMARKLET_CACHE_NAME);
        const response = await cache.match('/task-type-manager-bookmarklet.js');
        if (response) {
          const code = await response.text();
          event.ports[0].postMessage({ code });
        } else {
          event.ports[0].postMessage({ error: 'Bookmarklet not found in cache' });
        }
      })()
    );
  } else if (event.data && event.data.type === 'INJECT_BOOKMARKLET') {
    // Inject bookmarklet into all clients
    event.waitUntil(
      (async () => {
        const clients = await self.clients.matchAll();
        clients.forEach(client => {
          client.postMessage({
            type: 'INJECT_BOOKMARKLET',
            source: 'service-worker'
          });
        });
      })()
    );
  }
});

// Intercept HTML responses to inject a script loader
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  
  // Only intercept ClickUp pages
  if (
    url.hostname.includes('clickup.com') &&
    event.request.method === 'GET' &&
    event.request.headers.get('accept')?.includes('text/html')
  ) {
    event.respondWith(
      (async () => {
        const response = await fetch(event.request);
        
        // Clone the response so we can read it
        const responseClone = response.clone();
        const html = await responseClone.text();
        
        // Check if we should inject (e.g., settings page or any page)
        const shouldInject = url.pathname.includes('/settings') || 
                            url.pathname.includes('/task-types') ||
                            true; // Inject on all pages
        
        if (shouldInject && !html.includes('task-type-manager-injected')) {
          // Inject script loader
          const injectedHTML = html.replace(
            '</head>',
            `<script>
              // Auto-inject Task Type Manager
              (function() {
                if (window.__TASK_TYPE_MANAGER_INJECTED) return;
                window.__TASK_TYPE_MANAGER_INJECTED = true;
                
                // Request bookmarklet code from service worker
                if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
                  const channel = new MessageChannel();
                  channel.port1.onmessage = (event) => {
                    if (event.data.code) {
                      // Execute the bookmarklet code
                      const script = document.createElement('script');
                      script.textContent = event.data.code;
                      document.head.appendChild(script);
                    }
                  };
                  navigator.serviceWorker.controller.postMessage(
                    { type: 'GET_BOOKMARKLET' },
                    [channel.port2]
                  );
                } else {
                  // Fallback: Load from cache or inline
                  console.log('[Task Type Manager] Service worker not available, using fallback');
                }
              })();
            </script>
            <meta name="task-type-manager-injected" content="true"></head>`
          );
          
          return new Response(injectedHTML, {
            headers: response.headers,
            status: response.status,
            statusText: response.statusText
          });
        }
        
        return response;
      })()
    );
  }
});



