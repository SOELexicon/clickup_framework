// ClickUp Task Type Manager - Complete Single File
// Copy this entire file and run it in the ClickUp page console, or use as bookmarklet
// To use as bookmarklet, prefix with: javascript:

(function(){
    'use strict';
    
    // Remove existing sidebar if present
    if (document.getElementById('clickup-task-manager-sidebar')) {
        document.getElementById('clickup-task-manager-sidebar').remove();
        return;
    }

    // Configuration
    const CONFIG = {
        workspaceId: null,
        sessionToken: null,
        apiBase: 'https://frontdoor-prod-eu-west-1-3.clickup.com/tasks/v1'
    };

    // Icon mappings for auto-suggestion
    const ICON_MAPPINGS = {
        'bug': 'bug', 'feature': 'rocket', 'documentation': 'book', 'test': 'flask',
        'project': 'folder-open', 'account': 'user-circle', 'security': 'shield-alt',
        'warning': 'triangle-exclamation', 'error': 'exclamation-triangle',
        'deployment': 'cloud-upload-alt', 'database': 'database', 'api': 'plug',
        'meeting': 'comments', 'support': 'headset', 'maintenance': 'tools',
        'task': 'check-circle', 'fix': 'wrench', 'refactor': 'sync-alt',
        'design': 'palette', 'architecture': 'sitemap', 'research': 'search',
        'planning': 'calendar-alt', 'analysis': 'chart-line', 'review': 'eye',
        'milestone': 'flag-checkered', 'goal': 'bullseye', 'objective': 'target',
        'user story': 'book-open', 'requirement': 'file-contract', 'request': 'hand-paper',
        'resource': 'box', 'content': 'file-alt', 'form_response': 'file-signature',
        'meeting_note': 'sticky-note', 'test result': 'clipboard-check',
        'pull request': 'code-branch', 'actions run': 'play-circle', 'commit': 'code-commit',
        'command': 'terminal', 'branch': 'code-branch', 'lesson learned': 'lightbulb',
        'project file': 'folder', 'actions_run': 'play-circle', 'pull_request': 'code-branch',
        'test_result': 'clipboard-check', 'lesson_learned': 'lightbulb', 'project_file': 'folder',
        'form response': 'file-signature', 'meeting note': 'sticky-note'
    };

    // Get workspace ID from URL
    const urlMatch = window.location.pathname.match(/\/(\d+)\//);
    if (urlMatch) {
        CONFIG.workspaceId = urlMatch[1];
    }

    // Get session token (synchronous check first, then async)
    function getSessionTokenSync() {
        if (window.__CLICKUP_SESSION_TOKEN) {
            return window.__CLICKUP_SESSION_TOKEN.replace(/^Bearer\s+/i, '');
        }
        const cookies = document.cookie.split(';');
        for (const cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (value && value.startsWith('eyJ')) {
                return decodeURIComponent(value);
            }
        }
        for (let i = 0; i < localStorage.length; i++) {
            const value = localStorage.getItem(localStorage.key(i));
            if (value && value.startsWith('eyJ')) {
                return value;
            }
        }
        return null;
    }

    async function getSessionToken() {
        return getSessionTokenSync();
    }

    // Initialize session token
    CONFIG.sessionToken = getSessionTokenSync();

    // Helper: Generate icon from name
    function generateIcon(name) {
        const nameLower = name.toLowerCase().trim();
        if (ICON_MAPPINGS[nameLower]) return ICON_MAPPINGS[nameLower];
        for (const [key, icon] of Object.entries(ICON_MAPPINGS)) {
            if (nameLower.includes(key) || key.includes(nameLower)) return icon;
        }
        if (nameLower.includes('bug') || nameLower.includes('issue') || nameLower.includes('error') || nameLower.includes('defect')) return 'bug';
        if (nameLower.includes('feature') || nameLower.includes('enhancement') || nameLower.includes('request')) return 'rocket';
        if (nameLower.includes('doc') || nameLower.includes('document') || nameLower.includes('content')) return 'book';
        if (nameLower.includes('test') && nameLower.includes('result')) return 'clipboard-check';
        if (nameLower.includes('test')) return 'flask';
        if (nameLower.includes('project') && nameLower.includes('file')) return 'folder';
        if (nameLower.includes('project')) return 'folder-open';
        if (nameLower.includes('security')) return 'shield-alt';
        if (nameLower.includes('warning') || nameLower.includes('alert')) return 'triangle-exclamation';
        if (nameLower.includes('account') || nameLower.includes('user')) return 'user-circle';
        if (nameLower.includes('milestone')) return 'flag-checkered';
        if (nameLower.includes('meeting') && nameLower.includes('note')) return 'sticky-note';
        if (nameLower.includes('meeting')) return 'comments';
        if (nameLower.includes('form') && nameLower.includes('response')) return 'file-signature';
        if (nameLower.includes('form')) return 'file-alt';
        if (nameLower.includes('response')) return 'file-signature';
        if (nameLower.includes('pull') && nameLower.includes('request')) return 'code-branch';
        if (nameLower.includes('pr') || nameLower.includes('merge')) return 'code-branch';
        if (nameLower.includes('commit')) return 'code-commit';
        if (nameLower.includes('branch')) return 'code-branch';
        if (nameLower.includes('action') && nameLower.includes('run')) return 'play-circle';
        if (nameLower.includes('command')) return 'terminal';
        if (nameLower.includes('lesson') && nameLower.includes('learned')) return 'lightbulb';
        if (nameLower.includes('resource')) return 'box';
        if (nameLower.includes('requirement')) return 'file-contract';
        if (nameLower.includes('story')) return 'book-open';
        if (nameLower.includes('request')) return 'hand-paper';
        if (nameLower.includes('goal')) return 'bullseye';
        if (nameLower.includes('objective')) return 'target';
        return 'circle';
    }

    // Helper: Generate description from name
    function generateDescription(name) {
        const nameLower = name.toLowerCase().trim();
        const descriptions = {
            'bug': 'Software defect or unexpected behavior that needs to be fixed. Use for errors, crashes, incorrect behavior, or quality issues.',
            'feature': 'New functionality or capability being added to the system. Use for user-facing features, API endpoints, or significant enhancements.',
            'documentation': 'Creating or updating technical documentation, user guides, API docs, or knowledge base articles. Use for writing, editing, or maintaining documentation.',
            'test': 'Testing activities including unit tests, integration tests, or manual testing. Use for test development, test execution, or quality verification.',
            'project': 'Project-level container for related work with multiple subtasks and milestones. Use for organizing large initiatives or project planning.',
            'account': 'Manage client or customer account details and interactions. Use for account management, customer relations, or account-related work.',
            'warning': 'Warning or alert tasks that require attention. Use for warnings, alerts, cautions, or notices that need to be addressed.',
            'error': 'Error or issue tasks that need immediate attention. Use for errors, failures, or critical issues.',
        };
        if (descriptions[nameLower]) return descriptions[nameLower];
        for (const [key, desc] of Object.entries(descriptions)) {
            if (nameLower.includes(key)) return desc;
        }
        return `${name} for organizing and tracking work. Use this task type to categorize and manage ${nameLower} work items.`;
    }

    // Create sidebar HTML
    function createSidebarHTML() {
        return `
            <div id="clickup-task-manager-sidebar" style="position:fixed;top:0;right:0;width:450px;height:100vh;background:#1e1e1e;z-index:999999;box-shadow:-2px 0 12px rgba(0,0,0,0.5);overflow-y:auto;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;display:flex;flex-direction:column;color:#e0e0e0;">
                <div style="padding:16px 20px;background:#2d2d2d;color:#e0e0e0;display:flex;justify-content:space-between;align-items:center;position:sticky;top:0;z-index:10;border-bottom:1px solid #404040;">
                    <h2 style="margin:0;font-size:18px;font-weight:600;">🎯 Task Type Manager</h2>
                    <button id="close-sidebar" style="background:none;border:none;color:#e0e0e0;font-size:24px;cursor:pointer;padding:0;width:30px;height:30px;line-height:30px;">×</button>
                </div>
                <div id="manager-content" style="flex:1;padding:20px;overflow-y:auto;background:#1e1e1e;">
                    <div style="display:flex;border-bottom:2px solid #404040;margin:0 -20px 20px -20px;padding:0 20px;">
                        <button class="manager-tab active" data-tab="list" style="padding:12px 16px;border:none;background:none;cursor:pointer;border-bottom:2px solid #7b68ee;color:#7b68ee;font-weight:500;">List</button>
                        <button class="manager-tab" data-tab="create" style="padding:12px 16px;border:none;background:none;cursor:pointer;border-bottom:2px solid transparent;color:#999;font-weight:500;">Create</button>
                        <button class="manager-tab" data-tab="bulk" style="padding:12px 16px;border:none;background:none;cursor:pointer;border-bottom:2px solid transparent;color:#999;font-weight:500;">Bulk Add</button>
                        <button class="manager-tab" data-tab="csv" style="padding:12px 16px;border:none;background:none;cursor:pointer;border-bottom:2px solid transparent;color:#999;font-weight:500;">CSV</button>
                    </div>
                    <div id="manager-alerts"></div>
                    <div id="tab-list-content" class="tab-content" style="display:block;">
                        <div style="margin-bottom:12px;display:flex;gap:8px;">
                            <button id="export-json-btn" style="padding:8px 16px;background:#28a745;color:white;border:none;border-radius:4px;cursor:pointer;font-size:13px;">Export JSON</button>
                            <button id="export-csv-btn" style="padding:8px 16px;background:#17a2b8;color:white;border:none;border-radius:4px;cursor:pointer;font-size:13px;">Export CSV</button>
                        </div>
                        <div class="loading" style="color:#999;">Loading...</div>
                    </div>
                    <div id="tab-create-content" class="tab-content" style="display:none;">
                        <form id="create-task-form">
                            <div style="margin-bottom:16px;">
                                <label style="display:block;margin-bottom:6px;font-weight:500;font-size:14px;color:#e0e0e0;">Name (Singular) *</label>
                                <input type="text" id="create-name" required style="width:100%;padding:10px;border:1px solid #404040;border-radius:4px;font-size:14px;background:#2d2d2d;color:#e0e0e0;">
                            </div>
                            <div style="margin-bottom:16px;">
                                <label style="display:block;margin-bottom:6px;font-weight:500;font-size:14px;color:#e0e0e0;">Name (Plural) *</label>
                                <input type="text" id="create-name-plural" required style="width:100%;padding:10px;border:1px solid #404040;border-radius:4px;font-size:14px;background:#2d2d2d;color:#e0e0e0;">
                            </div>
                            <div style="margin-bottom:16px;">
                                <label style="display:block;margin-bottom:6px;font-weight:500;font-size:14px;color:#e0e0e0;">Description</label>
                                <textarea id="create-description" style="width:100%;padding:10px;border:1px solid #404040;border-radius:4px;font-size:14px;min-height:80px;resize:vertical;background:#2d2d2d;color:#e0e0e0;"></textarea>
                            </div>
                            <div style="margin-bottom:16px;">
                                <label style="display:block;margin-bottom:6px;font-weight:500;font-size:14px;color:#e0e0e0;">Icon</label>
                                <div style="display:flex;gap:8px;align-items:center;">
                                    <input type="text" id="create-icon" value="circle" placeholder="Font Awesome icon name" style="flex:1;padding:10px;border:1px solid #404040;border-radius:4px;font-size:14px;background:#2d2d2d;color:#e0e0e0;">
                                    <button type="button" id="open-icon-picker" style="padding:10px 16px;background:#6c757d;color:white;border:none;border-radius:4px;cursor:pointer;font-size:14px;">Pick Icon</button>
                                </div>
                                <small style="color:#999;font-size:12px;display:block;margin-top:4px;">Preview: <span id="icon-preview">○</span> | Selected: <span id="icon-selected">circle</span></small>
                            </div>
                            <button type="submit" style="padding:10px 20px;background:#7b68ee;color:white;border:none;border-radius:4px;cursor:pointer;font-weight:500;">Create</button>
                        </form>
                    </div>
                    <div id="tab-bulk-content" class="tab-content" style="display:none;">
                        <div style="margin-bottom:20px;">
                            <div style="display:flex;gap:8px;margin-bottom:12px;">
                                <button id="bulk-mode-lines" class="bulk-mode-btn active" style="flex:1;padding:10px;background:#7b68ee;color:white;border:none;border-radius:4px;cursor:pointer;font-weight:500;">Paste Lines</button>
                                <button id="bulk-mode-form" class="bulk-mode-btn" style="flex:1;padding:10px;background:#6c757d;color:white;border:none;border-radius:4px;cursor:pointer;font-weight:500;">Form Entry</button>
                            </div>
                            <div id="bulk-lines-mode" style="display:block;">
                                <label style="display:block;margin-bottom:6px;font-weight:500;font-size:14px;color:#e0e0e0;">Paste task types (one per line)</label>
                                <textarea id="bulk-lines-data" placeholder="Bug&#10;Feature&#10;Documentation&#10;Warning" style="width:100%;padding:10px;border:1px solid #404040;border-radius:4px;font-size:14px;min-height:200px;font-family:monospace;resize:vertical;background:#2d2d2d;color:#e0e0e0;"></textarea>
                                <div style="margin-top:8px;padding:12px;background:#2d2d2d;border-radius:4px;font-size:12px;color:#999;border:1px solid #404040;">One task type name per line. Icons and descriptions will be auto-generated.</div>
                            </div>
                            <div id="bulk-form-mode" style="display:none;">
                                <div id="bulk-form-entries" style="max-height:400px;overflow-y:auto;">
                                    <div class="bulk-form-entry" style="padding:16px;border:1px solid #404040;border-radius:4px;margin-bottom:12px;background:#2d2d2d;">
                                        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px;">
                                            <div>
                                                <label style="display:block;margin-bottom:4px;font-weight:500;font-size:13px;color:#e0e0e0;">Name (Singular) *</label>
                                                <input type="text" class="bulk-name" required style="width:100%;padding:8px;border:1px solid #404040;border-radius:4px;font-size:14px;background:#1e1e1e;color:#e0e0e0;">
                                            </div>
                                            <div>
                                                <label style="display:block;margin-bottom:4px;font-weight:500;font-size:13px;color:#e0e0e0;">Name (Plural) *</label>
                                                <input type="text" class="bulk-name-plural" required style="width:100%;padding:8px;border:1px solid #404040;border-radius:4px;font-size:14px;background:#1e1e1e;color:#e0e0e0;">
                                            </div>
                                        </div>
                                        <div style="margin-bottom:12px;">
                                            <label style="display:block;margin-bottom:4px;font-weight:500;font-size:13px;color:#e0e0e0;">Description</label>
                                            <textarea class="bulk-description" style="width:100%;padding:8px;border:1px solid #404040;border-radius:4px;font-size:14px;min-height:60px;resize:vertical;background:#1e1e1e;color:#e0e0e0;"></textarea>
                                        </div>
                                        <div style="display:flex;gap:8px;align-items:center;">
                                            <div style="flex:1;">
                                                <label style="display:block;margin-bottom:4px;font-weight:500;font-size:13px;color:#e0e0e0;">Icon</label>
                                                <input type="text" class="bulk-icon" placeholder="Font Awesome name" style="width:100%;padding:8px;border:1px solid #404040;border-radius:4px;font-size:14px;background:#1e1e1e;color:#e0e0e0;">
                                            </div>
                                            <button type="button" class="bulk-icon-picker-btn" style="padding:8px 12px;background:#6c757d;color:white;border:none;border-radius:4px;cursor:pointer;font-size:13px;margin-top:20px;">Pick</button>
                                        </div>
                                        <button type="button" class="bulk-remove-entry" style="margin-top:8px;padding:6px 12px;background:#dc3545;color:white;border:none;border-radius:4px;cursor:pointer;font-size:12px;">Remove</button>
                                    </div>
                                </div>
                                <button type="button" id="bulk-add-entry" style="width:100%;padding:10px;background:#28a745;color:white;border:none;border-radius:4px;cursor:pointer;font-weight:500;margin-bottom:12px;">+ Add Another</button>
                            </div>
                        </div>
                        <button id="bulk-import-btn" style="width:100%;padding:10px 20px;background:#7b68ee;color:white;border:none;border-radius:4px;cursor:pointer;font-weight:500;">Create All</button>
                    </div>
                    <div id="tab-csv-content" class="tab-content" style="display:none;">
                        <div style="margin-bottom:16px;">
                            <label style="display:block;margin-bottom:6px;font-weight:500;font-size:14px;color:#e0e0e0;">CSV Data</label>
                            <textarea id="csv-data" style="width:100%;padding:10px;border:1px solid #404040;border-radius:4px;font-size:14px;min-height:200px;font-family:monospace;resize:vertical;background:#2d2d2d;color:#e0e0e0;"></textarea>
                            <div style="margin-top:8px;padding:12px;background:#2d2d2d;border-radius:4px;font-size:12px;font-family:monospace;white-space:pre-wrap;color:#999;border:1px solid #404040;">Example:
name,name_plural,description,icon
Bug,Bugs,Software defects,bug
Feature,Features,New features,rocket
Warning,Warnings,Warning tasks,triangle-exclamation</div>
                        </div>
                        <div style="margin-bottom:16px;">
                            <label style="display:flex;align-items:center;gap:8px;color:#e0e0e0;">
                                <input type="checkbox" id="csv-update-existing" checked style="accent-color:#7b68ee;">
                                <span>Update existing if name matches</span>
                            </label>
                        </div>
                        <button id="csv-import-btn" style="padding:10px 20px;background:#7b68ee;color:white;border:none;border-radius:4px;cursor:pointer;font-weight:500;">Import CSV</button>
                    </div>
                </div>
            </div>
        `;
    }

    // Inject Font Awesome if not present
    // Use inline style or check if already loaded to avoid CSP violations
    if (!document.querySelector('link[href*="font-awesome"]') && !document.querySelector('link[href*="fontawesome"]') && !document.querySelector('style[data-font-awesome]')) {
        // Try to use an allowed CDN or inline minimal FA styles
        // Since ClickUp's CSP blocks cdnjs, we'll use minimal inline styles for common icons
        const faStyle = document.createElement('style');
        faStyle.setAttribute('data-font-awesome', 'true');
        faStyle.textContent = `
            /* Minimal Font Awesome icon styles - using Unicode fallbacks */
            .fa, .fas { font-family: "Font Awesome 6 Free", "Font Awesome 6 Pro", sans-serif; font-weight: 900; }
            .fa-bug::before { content: "🐛"; }
            .fa-rocket::before { content: "🚀"; }
            .fa-book::before { content: "📖"; }
            .fa-flask::before { content: "🧪"; }
            .fa-folder-open::before { content: "📂"; }
            .fa-user-circle::before { content: "👤"; }
            .fa-shield-alt::before { content: "🛡️"; }
            .fa-triangle-exclamation::before { content: "⚠️"; }
            .fa-exclamation-triangle::before { content: "⚠️"; }
            .fa-cloud-upload-alt::before { content: "☁️"; }
            .fa-database::before { content: "💾"; }
            .fa-plug::before { content: "🔌"; }
            .fa-comments::before { content: "💬"; }
            .fa-headset::before { content: "🎧"; }
            .fa-tools::before { content: "🔧"; }
            .fa-check-circle::before { content: "✅"; }
            .fa-wrench::before { content: "🔧"; }
            .fa-sync-alt::before { content: "🔄"; }
            .fa-palette::before { content: "🎨"; }
            .fa-sitemap::before { content: "🗺️"; }
            .fa-search::before { content: "🔍"; }
            .fa-calendar-alt::before { content: "📅"; }
            .fa-chart-line::before { content: "📈"; }
            .fa-eye::before { content: "👁️"; }
            .fa-code::before { content: "💻"; }
            .fa-laptop-code::before { content: "💻"; }
            .fa-file-alt::before { content: "📄"; }
            .fa-vial::before { content: "🧪"; }
            .fa-check-double::before { content: "✅"; }
            .fa-clipboard-check::before { content: "📋"; }
            .fa-server::before { content: "🖥️"; }
            .fa-network-wired::before { content: "🌐"; }
            .fa-cog::before { content: "⚙️"; }
            .fa-cogs::before { content: "⚙️"; }
            .fa-exchange-alt::before { content: "🔄"; }
            .fa-chart-bar::before { content: "📊"; }
            .fa-tachometer-alt::before { content: "📊"; }
            .fa-bolt::before { content: "⚡"; }
            .fa-layer-group::before { content: "📚"; }
            .fa-flag-checkered::before { content: "🏁"; }
            .fa-bullseye::before { content: "🎯"; }
            .fa-book-open::before { content: "📖"; }
            .fa-handshake::before { content: "🤝"; }
            .fa-users::before { content: "👥"; }
            .fa-broom::before { content: "🧹"; }
            .fa-file-contract::before { content: "📝"; }
            .fa-circle::before { content: "○"; }
            .fa-code-branch::before { content: "🌿"; }
            .fa-code-commit::before { content: "💾"; }
            .fa-play-circle::before { content: "▶️"; }
            .fa-lightbulb::before { content: "💡"; }
            .fa-folder::before { content: "📁"; }
            .fa-file-signature::before { content: "✍️"; }
            .fa-sticky-note::before { content: "📝"; }
            .fa-box::before { content: "📦"; }
            .fa-hand-paper::before { content: "✋"; }
            .fa-target::before { content: "🎯"; }
            .fa-terminal::before { content: "💻"; }
        `;
        document.head.appendChild(faStyle);
    }

    // Inject sidebar
    const sidebarHTML = createSidebarHTML();
    document.body.insertAdjacentHTML('beforeend', sidebarHTML);
    const sidebar = document.getElementById('clickup-task-manager-sidebar');

    // Functions
    function showAlert(msg, type = 'info') {
        const alert = document.createElement('div');
        alert.style.cssText = `
            padding: 12px;
            margin-bottom: 12px;
            border-radius: 4px;
            background: ${type === 'error' ? '#4a1f1f' : type === 'success' ? '#1f4a1f' : '#1f3a4a'};
            color: ${type === 'error' ? '#ff6b6b' : type === 'success' ? '#51cf66' : '#74c0fc'};
            font-size: 14px;
            border: 1px solid ${type === 'error' ? '#6b2b2b' : type === 'success' ? '#2b6b2b' : '#2b4a6b'};
        `;
        alert.textContent = msg;
        document.getElementById('manager-alerts').appendChild(alert);
        setTimeout(() => alert.remove(), 5000);
    }

    function switchTab(tabName) {
        document.querySelectorAll('.manager-tab').forEach(t => {
            t.style.borderBottomColor = 'transparent';
            t.style.color = '#999';
        });
        document.querySelectorAll('.tab-content').forEach(c => c.style.display = 'none');
        
        const activeTab = document.querySelector(`[data-tab="${tabName}"]`);
        if (activeTab) {
            activeTab.style.borderBottomColor = '#7b68ee';
            activeTab.style.color = '#7b68ee';
        }
        
        const activeContent = document.getElementById(`tab-${tabName}-content`);
        if (activeContent) {
            activeContent.style.display = 'block';
        }

        if (tabName === 'list') {
            loadTaskTypes();
        }
    }

    async function loadTaskTypes() {
        const container = document.getElementById('tab-list-content');
        container.innerHTML = '<div class="loading">Loading...</div>';

        // Ensure we have token
        if (!CONFIG.sessionToken) {
            CONFIG.sessionToken = await getSessionToken();
        }

        if (!CONFIG.workspaceId) {
            container.innerHTML = '<div style="padding:20px;color:#ff6b6b;">Error: Could not detect workspace ID. Please run this on a ClickUp page with workspace ID in URL.</div>';
            return;
        }

        if (!CONFIG.sessionToken) {
            container.innerHTML = '<div style="padding:20px;color:#ff6b6b;">Error: Session token missing. Set window.__CLICKUP_SESSION_TOKEN = "your-token" and refresh.</div>';
            return;
        }

        try {
            const response = await fetch(`${CONFIG.apiBase}/${CONFIG.workspaceId}/customItems`, {
                headers: {
                    'Authorization': `Bearer ${CONFIG.sessionToken}`,
                    'Accept': 'application/json, text/plain, */*',
                    'x-workspace-id': CONFIG.workspaceId,
                },
                credentials: 'include'
            });

            if (!response.ok) throw new Error(`Failed: ${response.status}`);

            const data = await response.json();
            const taskTypes = data.customItems || data.custom_items || data || [];

            if (taskTypes.length === 0) {
                container.innerHTML = '<div style="padding:20px;text-align:center;color:#999;">No task types found</div>';
                return;
            }

            // Store task types globally for export (with normalized icon field)
            window.__CURRENT_TASK_TYPES = taskTypes.map(tt => {
                // Normalize icon field - check multiple possible field names
                const icon = tt.avatar_value || tt.avatarValue || tt.icon || tt.avatar?.value || 'circle';
                const iconSource = tt.avatar_source || tt.avatarSource || tt.icon_source || tt.avatar?.source || 'fas';
                return {
                    ...tt,
                    avatar_value: icon,
                    avatar_source: iconSource,
                    // Also store normalized for export
                    _export_icon: icon,
                    _export_icon_source: iconSource
                };
            });
            
            // Create container for task types list
            const listContainer = document.createElement('div');
            listContainer.id = 'task-types-list-container';
            
            window.__CURRENT_TASK_TYPES.forEach(tt => {
                const icon = tt._export_icon || tt.avatar_value || 'circle';
                const card = document.createElement('div');
                card.style.cssText = 'padding:12px;margin-bottom:8px;border:1px solid #404040;border-radius:4px;background:#2d2d2d;';
                card.innerHTML = `
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div>
                            <strong style="color:#e0e0e0;">${tt.name}</strong> <span style="color:#999;font-size:12px;">(${icon})</span>
                            <div style="color:#999;font-size:12px;margin-top:4px;">${tt.description || 'No description'}</div>
                        </div>
                        <button onclick="window.__UPDATE_TASK_TYPE('${tt.id}')" style="padding:6px 12px;background:#7b68ee;color:white;border:none;border-radius:4px;cursor:pointer;font-size:12px;">Update</button>
                    </div>
                `;
                listContainer.appendChild(card);
            });
            
            // Clear and rebuild container with export buttons
            container.innerHTML = '';
            const exportButtons = document.createElement('div');
            exportButtons.style.cssText = 'margin-bottom:12px;display:flex;gap:8px;';
            exportButtons.innerHTML = `
                <button id="export-json-btn" style="padding:8px 16px;background:#28a745;color:white;border:none;border-radius:4px;cursor:pointer;font-size:13px;">Export JSON</button>
                <button id="export-csv-btn" style="padding:8px 16px;background:#17a2b8;color:white;border:none;border-radius:4px;cursor:pointer;font-size:13px;">Export CSV</button>
            `;
            container.appendChild(exportButtons);
            container.appendChild(listContainer);
            
            // Re-attach export handlers
            document.getElementById('export-json-btn').addEventListener('click', exportToJSON);
            document.getElementById('export-csv-btn').addEventListener('click', exportToCSV);
        } catch (error) {
            container.innerHTML = `<div style="padding:20px;color:#ff6b6b;">Error: ${error.message}</div>`;
        }
    }

    window.__UPDATE_TASK_TYPE = async function(taskTypeId) {
        if (!CONFIG.sessionToken) {
            CONFIG.sessionToken = await getSessionToken();
            if (!CONFIG.sessionToken) {
                alert('Session token required. Set window.__CLICKUP_SESSION_TOKEN');
                return;
            }
        }

        const name = prompt('Enter new name:');
        if (!name) return;
        const description = prompt('Enter description (or leave empty for auto-generated):');
        const icon = prompt('Enter icon name (or leave empty for auto-generated):', '');
        
        const finalDescription = description || generateDescription(name);
        const finalIcon = icon || generateIcon(name);
        
        try {
            const response = await fetch(`${CONFIG.apiBase}/${CONFIG.workspaceId}/customItem/${taskTypeId}`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${CONFIG.sessionToken}`,
                    'Content-Type': 'application/json',
                    'Accept': 'application/json, text/plain, */*',
                    'x-workspace-id': CONFIG.workspaceId,
                },
                credentials: 'include',
                body: JSON.stringify({
                    name: name,
                    name_plural: name + 's',
                    description: finalDescription,
                    avatar_source: 'fas',
                    avatar_value: finalIcon
                })
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Failed: ${response.status} - ${errorText}`);
            }
            showAlert('Updated!', 'success');
            loadTaskTypes();
        } catch (error) {
            showAlert(`Error: ${error.message}`, 'error');
        }
    };

    // Event listeners
    document.getElementById('close-sidebar').addEventListener('click', () => sidebar.remove());
    
    document.querySelectorAll('.manager-tab').forEach(tab => {
        tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    });

    document.getElementById('create-task-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        if (!CONFIG.sessionToken) {
            CONFIG.sessionToken = await getSessionToken();
        }

        if (!CONFIG.workspaceId || !CONFIG.sessionToken) {
            showAlert('Workspace ID or session token missing. Set window.__CLICKUP_SESSION_TOKEN', 'error');
            return;
        }

        const name = document.getElementById('create-name').value.trim();
        const namePlural = document.getElementById('create-name-plural').value.trim();
        let description = document.getElementById('create-description').value.trim();
        let icon = document.getElementById('create-icon').value.trim();

        // Auto-generate if empty
        if (!description) description = generateDescription(name);
        if (!icon || icon === 'circle') icon = generateIcon(name);

        try {
            const response = await fetch(`${CONFIG.apiBase}/${CONFIG.workspaceId}/customItem`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${CONFIG.sessionToken}`,
                    'Content-Type': 'application/json',
                    'Accept': 'application/json, text/plain, */*',
                    'x-workspace-id': CONFIG.workspaceId,
                },
                credentials: 'include',
                body: JSON.stringify({
                    name: name,
                    name_plural: namePlural,
                    description: description,
                    avatar_source: 'fas',
                    avatar_value: icon
                })
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Failed: ${response.status} - ${errorText}`);
            }
            showAlert('Created!', 'success');
            document.getElementById('create-task-form').reset();
            document.getElementById('create-icon').value = 'circle';
            document.getElementById('icon-preview').textContent = '○';
            loadTaskTypes();
        } catch (error) {
            showAlert(`Error: ${error.message}`, 'error');
        }
    });

    document.getElementById('csv-import-btn').addEventListener('click', async () => {
        if (!CONFIG.sessionToken) {
            CONFIG.sessionToken = await getSessionToken();
        }

        if (!CONFIG.workspaceId || !CONFIG.sessionToken) {
            showAlert('Workspace ID or session token missing. Set window.__CLICKUP_SESSION_TOKEN', 'error');
            return;
        }

        const csvData = document.getElementById('csv-data').value.trim();
        if (!csvData) {
            showAlert('Please paste CSV data', 'error');
            return;
        }

        const lines = csvData.trim().split('\n');
        if (lines.length < 2) {
            showAlert('CSV must have at least a header and one data row', 'error');
            return;
        }

        const headers = lines[0].split(',').map(h => h.trim());
        const rows = [];

        for (let i = 1; i < lines.length; i++) {
            const values = lines[i].split(',').map(v => v.trim());
            const row = {};
            headers.forEach((h, idx) => row[h] = values[idx] || '');
            rows.push(row);
        }

        showAlert(`Processing ${rows.length} task type(s)...`, 'info');

        let success = 0;
        let errors = 0;

        for (const row of rows) {
            try {
                const name = row.name || row.Name || '';
                if (!name) {
                    errors++;
                    continue;
                }

                const namePlural = row.name_plural || row['name_plural'] || row.Name_Plural || name + 's';
                let description = row.description || row.Description || '';
                let icon = row.icon || row.Icon || '';

                // Auto-generate if empty
                if (!description) description = generateDescription(name);
                if (!icon) icon = generateIcon(name);

                const response = await fetch(`${CONFIG.apiBase}/${CONFIG.workspaceId}/customItem`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${CONFIG.sessionToken}`,
                        'Content-Type': 'application/json',
                        'Accept': 'application/json, text/plain, */*',
                        'x-workspace-id': CONFIG.workspaceId,
                    },
                    credentials: 'include',
                    body: JSON.stringify({
                        name: name,
                        name_plural: namePlural,
                        description: description,
                        avatar_source: 'fas',
                        avatar_value: icon
                    })
                });

                if (response.ok) {
                    success++;
                } else {
                    errors++;
                }
                await new Promise(r => setTimeout(r, 300));
            } catch (e) {
                errors++;
            }
        }

        showAlert(`Import complete: ${success} created, ${errors} errors`, success > 0 ? 'success' : 'error');
        loadTaskTypes();
    });

    document.getElementById('create-icon').addEventListener('input', (e) => {
        const icon = e.target.value.trim() || 'circle';
        document.getElementById('icon-preview').textContent = icon === 'circle' ? '○' : icon;
        document.getElementById('icon-selected').textContent = icon;
    });

    // Icon picker integration
    function openClickUpIconPicker(callback) {
        // Try to find ClickUp's icon picker component
        const clickUpIconPicker = document.querySelector('cu3-icon-picker, [cu3-icon-picker], icon-picker');
        
        if (clickUpIconPicker) {
            // If we find the component, try to trigger it
            const event = new CustomEvent('openIconPicker', { detail: { callback } });
            clickUpIconPicker.dispatchEvent(event);
            return true;
        }

        // Fallback: Create our own icon picker modal
        const modal = document.createElement('div');
        modal.id = 'icon-picker-modal';
        modal.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.7);z-index:1000000;display:flex;align-items:center;justify-content:center;';
        
        const modalContent = document.createElement('div');
        modalContent.style.cssText = 'background:#1e1e1e;border-radius:8px;padding:24px;max-width:600px;max-height:80vh;overflow-y:auto;border:1px solid #404040;';
        modalContent.innerHTML = `
            <h3 style="margin:0 0 16px 0;font-size:18px;color:#e0e0e0;">Select Icon</h3>
            <div style="display:grid;grid-template-columns:repeat(8,1fr);gap:8px;margin-bottom:16px;">
                ${['bug','rocket','book','flask','folder-open','user-circle','shield-alt','triangle-exclamation','exclamation-triangle','cloud-upload-alt','database','plug','comments','headset','tools','check-circle','wrench','sync-alt','palette','sitemap','search','calendar-alt','chart-line','eye','code','laptop-code','file-alt','vial','check-double','clipboard-check','server','network-wired','cog','cogs','exchange-alt','chart-bar','tachometer-alt','bolt','layer-group','flag-checkered','bullseye','book-open','handshake','users','broom','file-contract','circle'].map(icon => 
                    `<button class="icon-option" data-icon="${icon}" style="padding:12px;border:1px solid #404040;border-radius:4px;cursor:pointer;background:#2d2d2d;font-size:20px;color:#e0e0e0;transition:all 0.2s;" onmouseover="this.style.background='#404040';this.style.borderColor='#7b68ee';" onmouseout="this.style.background='#2d2d2d';this.style.borderColor='#404040';" title="${icon}">
                        <i class="fas fa-${icon}"></i>
                    </button>`
                ).join('')}
            </div>
            <div style="display:flex;gap:8px;">
                <input type="text" id="icon-search" placeholder="Search icon name..." style="flex:1;padding:8px;border:1px solid #404040;border-radius:4px;background:#2d2d2d;color:#e0e0e0;">
                <button id="icon-picker-close" style="padding:8px 16px;background:#6c757d;color:white;border:none;border-radius:4px;cursor:pointer;">Cancel</button>
            </div>
        `;
        
        modal.appendChild(modalContent);
        document.body.appendChild(modal);

        // Icon selection
        modalContent.querySelectorAll('.icon-option').forEach(btn => {
            btn.addEventListener('click', () => {
                const icon = btn.dataset.icon;
                callback(icon);
                modal.remove();
            });
        });

        // Search
        const searchInput = modalContent.querySelector('#icon-search');
        searchInput.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase();
            modalContent.querySelectorAll('.icon-option').forEach(btn => {
                const icon = btn.dataset.icon;
                if (icon.includes(term) || term === '') {
                    btn.style.display = 'block';
                } else {
                    btn.style.display = 'none';
                }
            });
        });

        // Close
        modalContent.querySelector('#icon-picker-close').addEventListener('click', () => modal.remove());
        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.remove();
        });
    }

    // Open icon picker for create form
    document.getElementById('open-icon-picker').addEventListener('click', () => {
        openClickUpIconPicker((icon) => {
            document.getElementById('create-icon').value = icon;
            document.getElementById('icon-preview').textContent = icon === 'circle' ? '○' : icon;
            document.getElementById('icon-selected').textContent = icon;
        });
    });

    // Bulk add functionality
    let bulkMode = 'lines';
    document.getElementById('bulk-mode-lines').addEventListener('click', () => {
        bulkMode = 'lines';
        document.getElementById('bulk-lines-mode').style.display = 'block';
        document.getElementById('bulk-form-mode').style.display = 'none';
        document.getElementById('bulk-mode-lines').style.background = '#7b68ee';
        document.getElementById('bulk-mode-form').style.background = '#6c757d';
    });

    document.getElementById('bulk-mode-form').addEventListener('click', () => {
        bulkMode = 'form';
        document.getElementById('bulk-lines-mode').style.display = 'none';
        document.getElementById('bulk-form-mode').style.display = 'block';
        document.getElementById('bulk-mode-lines').style.background = '#6c757d';
        document.getElementById('bulk-mode-form').style.background = '#7b68ee';
    });

    // Add new form entry
    document.getElementById('bulk-add-entry').addEventListener('click', () => {
        const container = document.getElementById('bulk-form-entries');
        const newEntry = document.createElement('div');
        newEntry.className = 'bulk-form-entry';
        newEntry.style.cssText = 'padding:16px;border:1px solid #404040;border-radius:4px;margin-bottom:12px;background:#2d2d2d;';
        newEntry.innerHTML = `
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px;">
                <div>
                    <label style="display:block;margin-bottom:4px;font-weight:500;font-size:13px;color:#e0e0e0;">Name (Singular) *</label>
                    <input type="text" class="bulk-name" required style="width:100%;padding:8px;border:1px solid #404040;border-radius:4px;font-size:14px;background:#1e1e1e;color:#e0e0e0;">
                </div>
                <div>
                    <label style="display:block;margin-bottom:4px;font-weight:500;font-size:13px;color:#e0e0e0;">Name (Plural) *</label>
                    <input type="text" class="bulk-name-plural" required style="width:100%;padding:8px;border:1px solid #404040;border-radius:4px;font-size:14px;background:#1e1e1e;color:#e0e0e0;">
                </div>
            </div>
            <div style="margin-bottom:12px;">
                <label style="display:block;margin-bottom:4px;font-weight:500;font-size:13px;color:#e0e0e0;">Description</label>
                <textarea class="bulk-description" style="width:100%;padding:8px;border:1px solid #404040;border-radius:4px;font-size:14px;min-height:60px;resize:vertical;background:#1e1e1e;color:#e0e0e0;"></textarea>
            </div>
            <div style="display:flex;gap:8px;align-items:center;">
                <div style="flex:1;">
                    <label style="display:block;margin-bottom:4px;font-weight:500;font-size:13px;color:#e0e0e0;">Icon</label>
                    <input type="text" class="bulk-icon" placeholder="Font Awesome name" style="width:100%;padding:8px;border:1px solid #404040;border-radius:4px;font-size:14px;background:#1e1e1e;color:#e0e0e0;">
                </div>
                <button type="button" class="bulk-icon-picker-btn" style="padding:8px 12px;background:#6c757d;color:white;border:none;border-radius:4px;cursor:pointer;font-size:13px;margin-top:20px;">Pick</button>
            </div>
            <button type="button" class="bulk-remove-entry" style="margin-top:8px;padding:6px 12px;background:#dc3545;color:white;border:none;border-radius:4px;cursor:pointer;font-size:12px;">Remove</button>
        `;
        container.appendChild(newEntry);
        
        // Add event listeners
        newEntry.querySelector('.bulk-remove-entry').addEventListener('click', () => newEntry.remove());
        newEntry.querySelector('.bulk-icon-picker-btn').addEventListener('click', () => {
            openClickUpIconPicker((icon) => {
                newEntry.querySelector('.bulk-icon').value = icon;
            });
        });
    });

    // Remove entry handler (for initial entry)
    document.querySelector('.bulk-remove-entry')?.addEventListener('click', function() {
        if (document.querySelectorAll('.bulk-form-entry').length > 1) {
            this.closest('.bulk-form-entry').remove();
        }
    });

    // Icon picker for initial entry
    document.querySelector('.bulk-icon-picker-btn')?.addEventListener('click', function() {
        openClickUpIconPicker((icon) => {
            this.closest('.bulk-form-entry').querySelector('.bulk-icon').value = icon;
        });
    });

    // Bulk import handler
    document.getElementById('bulk-import-btn').addEventListener('click', async () => {
        if (!CONFIG.sessionToken) {
            CONFIG.sessionToken = await getSessionToken();
        }

        if (!CONFIG.workspaceId || !CONFIG.sessionToken) {
            showAlert('Workspace ID or session token missing', 'error');
            return;
        }

        const entries = [];
        
        if (bulkMode === 'lines') {
            const lines = document.getElementById('bulk-lines-data').value.trim().split('\n').filter(l => l.trim());
            if (lines.length === 0) {
                showAlert('Please enter at least one task type name', 'error');
                return;
            }
            lines.forEach(name => {
                entries.push({
                    name: name.trim(),
                    name_plural: name.trim() + 's',
                    description: generateDescription(name.trim()),
                    icon: generateIcon(name.trim())
                });
            });
        } else {
            const formEntries = document.querySelectorAll('.bulk-form-entry');
            if (formEntries.length === 0) {
                showAlert('Please add at least one entry', 'error');
                return;
            }
            formEntries.forEach(entry => {
                const name = entry.querySelector('.bulk-name').value.trim();
                const namePlural = entry.querySelector('.bulk-name-plural').value.trim();
                if (!name || !namePlural) {
                    return; // Skip invalid entries
                }
                let description = entry.querySelector('.bulk-description').value.trim();
                let icon = entry.querySelector('.bulk-icon').value.trim();
                if (!description) description = generateDescription(name);
                if (!icon) icon = generateIcon(name);
                entries.push({ name, name_plural: namePlural, description, icon });
            });
        }

        if (entries.length === 0) {
            showAlert('No valid entries to create', 'error');
            return;
        }

        showAlert(`Creating ${entries.length} task type(s)...`, 'info');

        let success = 0;
        let errors = 0;

        for (const entry of entries) {
            try {
                const response = await fetch(`${CONFIG.apiBase}/${CONFIG.workspaceId}/customItem`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${CONFIG.sessionToken}`,
                        'Content-Type': 'application/json',
                        'Accept': 'application/json, text/plain, */*',
                        'x-workspace-id': CONFIG.workspaceId,
                    },
                    credentials: 'include',
                    body: JSON.stringify({
                        name: entry.name,
                        name_plural: entry.name_plural,
                        description: entry.description,
                        avatar_source: 'fas',
                        avatar_value: entry.icon
                    })
                });

                if (response.ok) {
                    success++;
                } else {
                    errors++;
                }
                await new Promise(r => setTimeout(r, 300));
            } catch (e) {
                errors++;
            }
        }

        showAlert(`Created ${success} of ${entries.length} task type(s)`, success > 0 ? 'success' : 'error');
        if (bulkMode === 'lines') {
            document.getElementById('bulk-lines-data').value = '';
        }
        loadTaskTypes();
    });

    // Export functions
    function exportToJSON() {
        const taskTypes = window.__CURRENT_TASK_TYPES || [];
        if (taskTypes.length === 0) {
            showAlert('No task types to export. Please load task types first.', 'error');
            return;
        }
        
        const exportData = taskTypes.map(tt => {
            // Get icon from normalized field or try to generate from name
            let icon = tt._export_icon || tt.avatar_value || tt.avatarValue || tt.icon || tt.avatar?.value;
            // If still no icon or it's 'circle', try to generate from name
            if (!icon || icon === 'circle') {
                icon = generateIcon(tt.name);
            }
            
            return {
                id: tt.id,
                name: tt.name,
                name_plural: tt.name_plural || tt.namePlural || tt.name + 's',
                description: tt.description || '',
                icon: icon,
                icon_source: tt._export_icon_source || tt.avatar_source || tt.avatarSource || tt.icon_source || tt.avatar?.source || 'fas'
            };
        });
        
        const jsonStr = JSON.stringify(exportData, null, 2);
        const blob = new Blob([jsonStr], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `clickup_task_types_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        showAlert(`Exported ${taskTypes.length} task type(s) to JSON`, 'success');
    }

    function exportToCSV() {
        const taskTypes = window.__CURRENT_TASK_TYPES || [];
        if (taskTypes.length === 0) {
            showAlert('No task types to export. Please load task types first.', 'error');
            return;
        }
        
        const headers = ['id', 'name', 'name_plural', 'description', 'icon', 'icon_source'];
        const csvRows = [headers.join(',')];
        
        taskTypes.forEach(tt => {
            // Get icon from normalized field or try to generate from name
            let icon = tt._export_icon || tt.avatar_value || tt.avatarValue || tt.icon || tt.avatar?.value;
            // If still no icon or it's 'circle', try to generate from name
            if (!icon || icon === 'circle') {
                icon = generateIcon(tt.name);
            }
            
            const row = [
                tt.id || '',
                `"${(tt.name || '').replace(/"/g, '""')}"`,
                `"${((tt.name_plural || tt.namePlural || tt.name + 's') || '').replace(/"/g, '""')}"`,
                `"${((tt.description || '') || '').replace(/"/g, '""')}"`,
                icon,
                tt._export_icon_source || tt.avatar_source || tt.avatarSource || tt.icon_source || tt.avatar?.source || 'fas'
            ];
            csvRows.push(row.join(','));
        });
        
        const csvStr = csvRows.join('\n');
        const blob = new Blob([csvStr], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `clickup_task_types_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        showAlert(`Exported ${taskTypes.length} task type(s) to CSV`, 'success');
    }

    // Store code for persistent installation
    // Try to store the bookmarklet code so it can be used by installers
    if (typeof window !== 'undefined') {
        try {
            // Method 1: Try to get it from the script tag that contains this code
            const scripts = document.getElementsByTagName('script');
            for (let script of scripts) {
                if (script.textContent && 
                    script.textContent.includes('clickup-task-manager-sidebar') && 
                    script.textContent.includes('Task Type Manager') &&
                    script.textContent.length > 1000) {
                    // Store the full code
                    window.__TASK_TYPE_MANAGER_CODE = script.textContent;
                    // Also store in localStorage for persistence
                    try {
                        localStorage.setItem('__TASK_TYPE_MANAGER_CODE', script.textContent);
                        console.log('✅ Bookmarklet code stored for persistent installation');
                    } catch (e) {
                        console.log('⚠️ Could not store in localStorage (may be disabled)');
                    }
                    break;
                }
            }
            
            // Method 2: If we're running from console/eval, try to get from the source
            // This won't work in strict mode, but we can try
            if (!window.__TASK_TYPE_MANAGER_CODE) {
                // Mark that the bookmarklet is loaded
                window.__TASK_TYPE_MANAGER_AVAILABLE = true;
                console.log('ℹ️ Bookmarklet loaded. To enable persistent installation:');
                console.log('  1. Copy the entire task_type_manager_complete.js file');
                console.log('  2. Set: window.__TASK_TYPE_MANAGER_CODE = `...paste code...`');
                console.log('  3. Then run install_persistent.js');
            }
        } catch (e) {
            // Fallback: Just mark as available
            window.__TASK_TYPE_MANAGER_AVAILABLE = true;
        }
    }

    // Initial load
    loadTaskTypes();
})();

