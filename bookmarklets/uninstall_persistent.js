// Uninstall Persistent Task Type Manager Service Worker
// Run this in the browser console to remove the auto-inject service worker

(async function() {
  'use strict';

  if (!('serviceWorker' in navigator)) {
    console.log('Service Workers not supported');
    return;
  }

  const registrations = await navigator.serviceWorker.getRegistrations();
  let unregistered = 0;

  for (const registration of registrations) {
    const scriptURL = registration.active?.scriptURL || registration.installing?.scriptURL || '';
    
    // Check if it's our service worker (blob URL or contains task-type-manager)
    if (scriptURL.includes('blob:') || scriptURL.includes('task-type-manager')) {
      await registration.unregister();
      unregistered++;
      console.log('🗑️ Unregistered service worker:', scriptURL);
    }
  }

  if (unregistered > 0) {
    console.log(`✅ Unregistered ${unregistered} service worker(s)`);
    console.log('🔄 Refresh the page to see changes');
  } else {
    console.log('ℹ️ No Task Type Manager service workers found');
  }
})();



