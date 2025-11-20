// Auto-Inject Bookmarklet via Service Worker
// This is a simpler approach: inject the bookmarklet code directly into the service worker

// Step 1: Register this service worker
// Step 2: The service worker will inject the bookmarklet on every ClickUp page load

const SW_CODE = `
const BOOKMARKLET_CODE = \`${getBookmarkletCode()}\`;

self.addEventListener('install', (event) => {
  console.log('[Task Type Manager] Service Worker installing...');
  event.waitUntil(self.skipWaiting());
});

self.addEventListener('activate', (event) => {
  console.log('[Task Type Manager] Service Worker activating...');
  event.waitUntil(self.clients.claim());
});

// Inject bookmarklet on page navigation
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
          
          // Inject the bookmarklet loader
          const injectedHTML = html.replace(
            '</head>',
            \`<script>
              (function() {
                if (window.__TASK_TYPE_MANAGER_LOADED) return;
                window.__TASK_TYPE_MANAGER_LOADED = true;
                
                // Execute bookmarklet code
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

function getBookmarkletCode() {
  // Return the full bookmarklet code as a string
  // This will be replaced with actual code during build
  return \`// Bookmarklet code here\`;
}
`;

// Registration function
async function registerAutoInjectSW() {
  if (!('serviceWorker' in navigator)) {
    console.error('Service Workers not supported');
    return;
  }

  try {
    // Create a blob URL for the service worker
    const swBlob = new Blob([SW_CODE], { type: 'application/javascript' });
    const swUrl = URL.createObjectURL(swBlob);
    
    const registration = await navigator.serviceWorker.register(swUrl, {
      scope: '/'
    });
    
    console.log('✅ Task Type Manager Auto-Inject Service Worker registered!');
    console.log('The bookmarklet will now automatically load on all ClickUp pages.');
    
    // Clean up the blob URL after registration
    setTimeout(() => URL.revokeObjectURL(swUrl), 1000);
    
    return registration;
  } catch (error) {
    console.error('❌ Failed to register service worker:', error);
  }
}

// Auto-register if run directly
if (typeof window !== 'undefined') {
  registerAutoInjectSW();
}



