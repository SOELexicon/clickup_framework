// Quick Install Helper - Makes it easier to set up persistent installation
// Run this AFTER loading the bookmarklet once

(function() {
  'use strict';

  console.log('🔧 Quick Install Helper for Task Type Manager');
  console.log('');

  // Check if bookmarklet is loaded
  if (document.getElementById('clickup-task-manager-sidebar')) {
    console.log('✅ Bookmarklet is currently loaded');
  } else {
    console.log('⚠️ Bookmarklet is not currently loaded');
    console.log('   Please load task_type_manager_complete.js first');
  }

  // Check if code is stored
  if (window.__TASK_TYPE_MANAGER_CODE && window.__TASK_TYPE_MANAGER_CODE.length > 100) {
    console.log('✅ Bookmarklet code is stored in window.__TASK_TYPE_MANAGER_CODE');
  } else {
    console.log('⚠️ Bookmarklet code not found in window.__TASK_TYPE_MANAGER_CODE');
  }

  // Check localStorage
  try {
    const stored = localStorage.getItem('__TASK_TYPE_MANAGER_CODE');
    if (stored && stored.length > 100) {
      console.log('✅ Bookmarklet code is stored in localStorage');
    } else {
      console.log('⚠️ Bookmarklet code not found in localStorage');
    }
  } catch (e) {
    console.log('⚠️ Cannot access localStorage');
  }

  console.log('');
  console.log('📋 Next Steps:');
  console.log('');
  
  if (!window.__TASK_TYPE_MANAGER_CODE || window.__TASK_TYPE_MANAGER_CODE.length < 100) {
    console.log('1. Copy the entire contents of task_type_manager_complete.js');
    console.log('2. Run this in console:');
    console.log('   window.__TASK_TYPE_MANAGER_CODE = `...paste code here...`;');
    console.log('3. Then run install_persistent.js or install_persistent_localStorage.js');
  } else {
    console.log('✅ Code is ready! You can now run:');
    console.log('   - install_persistent.js (for service worker - may not work)');
    console.log('   - install_persistent_localStorage.js (recommended - simpler)');
  }

  // Helper function to load code from file (if user pastes it)
  window.__SET_TASK_TYPE_MANAGER_CODE = function(code) {
    if (!code || code.length < 100) {
      console.error('❌ Code too short. Please provide the full bookmarklet code.');
      return false;
    }
    window.__TASK_TYPE_MANAGER_CODE = code;
    try {
      localStorage.setItem('__TASK_TYPE_MANAGER_CODE', code);
      console.log('✅ Code stored successfully!');
      console.log('   You can now run install_persistent.js or install_persistent_localStorage.js');
      return true;
    } catch (e) {
      console.error('❌ Could not store in localStorage:', e);
      console.log('   Code stored in window.__TASK_TYPE_MANAGER_CODE only');
      return false;
    }
  };

  console.log('');
  console.log('💡 Tip: Use window.__SET_TASK_TYPE_MANAGER_CODE(code) to set the code programmatically');
})();



