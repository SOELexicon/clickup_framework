// ==UserScript==
// @name         ClickUp Task Type Manager Auto-Load
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  Automatically load Task Type Manager bookmarklet on ClickUp pages
// @author       You
// @match        https://app.clickup.com/*
// @match        https://*.clickup.com/*
// @grant        none
// @run-at       document-start
// ==/UserScript==

(function() {
    'use strict';
    
    // Check if already loaded
    if (window.__TASK_TYPE_MANAGER_TAMPERMONKEY_LOADED) return;
    window.__TASK_TYPE_MANAGER_TAMPERMONKEY_LOADED = true;
    
    // Wait for DOM
    function injectBookmarklet() {
        if (document.getElementById('clickup-task-manager-sidebar')) return;
        
        // Option 1: Fetch from URL (update this)
        fetch('https://raw.githubusercontent.com/your-repo/task_type_manager_complete.js')
            .then(response => response.text())
            .then(code => {
                const script = document.createElement('script');
                script.textContent = code;
                (document.head || document.documentElement).appendChild(script);
            })
            .catch(error => {
                console.error('[Task Type Manager] Failed to load:', error);
                console.log('Please update the fetch URL in the userscript');
            });
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', injectBookmarklet);
    } else {
        setTimeout(injectBookmarklet, 100);
    }
    
    // Watch for SPA navigation
    let lastUrl = location.href;
    new MutationObserver(() => {
        const url = location.href;
        if (url !== lastUrl) {
            lastUrl = url;
            setTimeout(injectBookmarklet, 500);
        }
    }).observe(document, { subtree: true, childList: true });
})();



