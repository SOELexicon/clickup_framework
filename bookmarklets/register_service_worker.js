// Registration script to install the Task Type Manager Service Worker
// Run this in the browser console on any ClickUp page

(async function() {
  'use strict';

  if (!('serviceWorker' in navigator)) {
    console.error('Service Workers are not supported in this browser');
    return;
  }

  // Load the service worker code
  const swCode = await fetch('https://your-domain.com/task_type_manager_service_worker.js')
    .catch(() => {
      // Fallback: inline service worker registration
      console.log('Could not fetch service worker from URL, using inline version');
      return null;
    });

  if (!swCode || !swCode.ok) {
    // Inline registration with embedded service worker
    const swUrl = URL.createObjectURL(
      new Blob([`
        // Embedded Service Worker
        const BOOKMARKLET_CACHE_NAME = 'task-type-manager-bookmarklet-v1';
        
        self.addEventListener('install', (event) => {
          console.log('[Task Type Manager SW] Installing...');
          event.waitUntil(self.skipWaiting());
        });
        
        self.addEventListener('activate', (event) => {
          console.log('[Task Type Manager SW] Activating...');
          event.waitUntil(self.clients.claim());
        });
        
        self.addEventListener('message', async (event) => {
          if (event.data && event.data.type === 'GET_BOOKMARKLET') {
            const channel = event.ports[0];
            // Return the bookmarklet code
            const bookmarkletCode = \`${getBookmarkletCode()}\`;
            channel.postMessage({ code: bookmarkletCode });
          }
        });
        
        self.addEventListener('fetch', (event) => {
          const url = new URL(event.request.url);
          if (
            url.hostname.includes('clickup.com') &&
            event.request.method === 'GET' &&
            event.request.headers.get('accept')?.includes('text/html')
          ) {
            event.respondWith(
              (async () => {
                const response = await fetch(event.request);
                const html = await response.clone().text();
                
                if (!html.includes('task-type-manager-injected')) {
                  const injectedHTML = html.replace(
                    '</head>',
                    \`<script>
                      (function() {
                        if (window.__TASK_TYPE_MANAGER_INJECTED) return;
                        window.__TASK_TYPE_MANAGER_INJECTED = true;
                        
                        if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
                          const channel = new MessageChannel();
                          channel.port1.onmessage = (e) => {
                            if (e.data.code) {
                              const script = document.createElement('script');
                              script.textContent = e.data.code;
                              document.head.appendChild(script);
                            }
                          };
                          navigator.serviceWorker.controller.postMessage(
                            { type: 'GET_BOOKMARKLET' },
                            [channel.port2]
                          );
                        }
                      })();
                    </script></head>\`
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
      `], { type: 'application/javascript' })
    );

    try {
      const registration = await navigator.serviceWorker.register(swUrl, {
        scope: '/'
      });
      console.log('✅ Task Type Manager Service Worker registered!', registration);
      console.log('The bookmarklet will now auto-inject on ClickUp pages.');
    } catch (error) {
      console.error('❌ Failed to register service worker:', error);
    }
  } else {
    // Register from URL
    try {
      const registration = await navigator.serviceWorker.register(
        'https://your-domain.com/task_type_manager_service_worker.js',
        { scope: '/' }
      );
      console.log('✅ Task Type Manager Service Worker registered!', registration);
    } catch (error) {
      console.error('❌ Failed to register service worker:', error);
    }
  }

  function getBookmarkletCode() {
    // This should return the full bookmarklet code
    // For now, return a placeholder - you'll need to paste the actual code
    return `
      // Paste task_type_manager_complete.js content here
      // Or fetch it dynamically
    `;
  }
})();



