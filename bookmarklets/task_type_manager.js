// ClickUp Task Type Manager - Standalone JavaScript
// Can be used as a bookmarklet or injected into ClickUp page

(function() {
    'use strict';

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
        'meeting': 'comments', 'support': 'headset', 'maintenance': 'tools'
    };

    // Initialize
    async function init() {
        // Get workspace ID from URL
        const urlMatch = window.location.pathname.match(/\/(\d+)\//);
        if (urlMatch) {
            CONFIG.workspaceId = urlMatch[1];
        }

        // Try to get session token
        CONFIG.sessionToken = await getSessionToken();

        if (!CONFIG.sessionToken && !document.getElementById('workspace-id-input')) {
            showSetupForm();
        }

        // Setup tabs
        const tabs = document.querySelectorAll('.tab');
        if (tabs.length > 0) {
            tabs.forEach(tab => {
                tab.addEventListener('click', () => {
                    const tabName = tab.dataset.tab;
                    switchTab(tabName);
                });
            });
        }

        // Setup forms
        const createForm = document.getElementById('create-form');
        if (createForm) {
            createForm.addEventListener('submit', handleCreate);
        }

        const csvBtn = document.getElementById('csv-import-btn');
        if (csvBtn) {
            csvBtn.addEventListener('click', handleCSVImport);
        }

        const iconInput = document.getElementById('create-icon');
        if (iconInput) {
            iconInput.addEventListener('input', updateIconPreview);
        }

        // Load task types if we have credentials
        if (CONFIG.workspaceId && CONFIG.sessionToken) {
            loadTaskTypes();
        }
    }

    function showSetupForm() {
        const container = document.getElementById('alert-container') || document.body;
        const setupDiv = document.createElement('div');
        setupDiv.className = 'alert alert-info';
        setupDiv.innerHTML = `
            <strong>Setup Required</strong><br>
            <div style="margin-top: 12px;">
                <label>Workspace ID: <input type="text" id="workspace-id-input" placeholder="From URL" style="margin-left: 8px; padding: 4px;"></label><br>
                <label style="margin-top: 8px; display: block;">Session Token: <input type="text" id="session-token-input" placeholder="JWT token" style="margin-left: 8px; padding: 4px; width: 400px;"></label><br>
                <button onclick="window.__TASK_MANAGER_SETUP()" class="btn btn-primary" style="margin-top: 8px;">Save & Load</button>
            </div>
        `;
        container.insertBefore(setupDiv, container.firstChild);
    }

    window.__TASK_MANAGER_SETUP = function() {
        const wsId = document.getElementById('workspace-id-input')?.value.trim();
        const token = document.getElementById('session-token-input')?.value.trim();
        if (wsId) CONFIG.workspaceId = wsId;
        if (token) {
            CONFIG.sessionToken = token.replace(/^Bearer\s+/i, '');
            window.__CLICKUP_SESSION_TOKEN = CONFIG.sessionToken;
        }
        if (CONFIG.workspaceId && CONFIG.sessionToken) {
            loadTaskTypes();
            document.querySelector('.alert-info')?.remove();
        }
    };

    function switchTab(tabName) {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        const tab = document.querySelector(`[data-tab="${tabName}"]`);
        const content = document.getElementById(`tab-${tabName}`);
        if (tab) tab.classList.add('active');
        if (content) content.classList.add('active');

        if (tabName === 'list') {
            loadTaskTypes();
        }
    }

    function showAlert(message, type = 'info') {
        const container = document.getElementById('alert-container');
        if (!container) return;

        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.textContent = message;
        container.appendChild(alert);
        setTimeout(() => alert.remove(), 5000);
    }

    async function getSessionToken() {
        // Check global variable first
        if (window.__CLICKUP_SESSION_TOKEN) {
            return window.__CLICKUP_SESSION_TOKEN.replace(/^Bearer\s+/i, '');
        }

        // Check cookies
        const cookies = document.cookie.split(';');
        for (const cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (value && value.startsWith('eyJ')) {
                return decodeURIComponent(value);
            }
        }

        // Check localStorage
        for (let i = 0; i < localStorage.length; i++) {
            const value = localStorage.getItem(localStorage.key(i));
            if (value && value.startsWith('eyJ')) {
                return value;
            }
        }

        return null;
    }

    async function loadTaskTypes() {
        const container = document.getElementById('task-types-container');
        if (!container) return;

        container.innerHTML = '<div class="loading">Loading task types...</div>';

        if (!CONFIG.workspaceId || !CONFIG.sessionToken) {
            container.innerHTML = '<div class="alert alert-error">Workspace ID and session token required</div>';
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

            if (!response.ok) {
                throw new Error(`Failed to fetch: ${response.status} ${response.statusText}`);
            }

            const data = await response.json();
            const taskTypes = data.customItems || data.custom_items || data || [];

            if (taskTypes.length === 0) {
                container.innerHTML = '<div class="alert alert-info">No custom task types found.</div>';
                return;
            }

            container.innerHTML = '<div class="task-types-list"></div>';
            const list = container.querySelector('.task-types-list');

            taskTypes.forEach(taskType => {
                const card = createTaskTypeCard(taskType);
                list.appendChild(card);
            });
        } catch (error) {
            container.innerHTML = `<div class="alert alert-error">Error: ${error.message}</div>`;
        }
    }

    function createTaskTypeCard(taskType) {
        const card = document.createElement('div');
        card.className = 'task-type-card';
        
        const icon = taskType.avatar_value || 'circle';
        const iconClass = `fas fa-${icon}`;

        card.innerHTML = `
            <div class="task-type-info">
                <div class="task-type-name">
                    <i class="${iconClass}"></i>
                    ${taskType.name}
                </div>
                <div class="task-type-description">
                    ${taskType.description || '<em>No description</em>'}
                </div>
            </div>
            <div class="task-type-actions">
                <button class="btn btn-sm btn-primary" onclick="window.__TASK_MANAGER_EDIT('${taskType.id}')">Edit</button>
            </div>
        `;

        return card;
    }

    window.__TASK_MANAGER_EDIT = async function(taskTypeId) {
        const name = prompt('Enter new name:');
        if (!name) return;
        const description = prompt('Enter description:');
        const icon = prompt('Enter icon name (Font Awesome):', 'circle');
        
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
                    description: description || '',
                    avatar_source: 'fas',
                    avatar_value: icon || 'circle'
                })
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Failed: ${response.status} - ${errorText}`);
            }

            showAlert('Task type updated!', 'success');
            loadTaskTypes();
        } catch (error) {
            showAlert(`Error: ${error.message}`, 'error');
        }
    };

    async function handleCreate(e) {
        e.preventDefault();
        
        if (!CONFIG.workspaceId || !CONFIG.sessionToken) {
            showAlert('Workspace ID and session token required', 'error');
            return;
        }

        const name = document.getElementById('create-name').value.trim();
        const namePlural = document.getElementById('create-name-plural').value.trim();
        const description = document.getElementById('create-description').value.trim();
        const icon = document.getElementById('create-icon').value.trim() || 'circle';
        const iconSource = document.getElementById('create-icon-source').value;

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
                    avatar_source: iconSource,
                    avatar_value: icon
                })
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Failed to create: ${response.status} - ${errorText}`);
            }

            showAlert(`Task type "${name}" created successfully!`, 'success');
            document.getElementById('create-form').reset();
            loadTaskTypes();
        } catch (error) {
            showAlert(`Error: ${error.message}`, 'error');
        }
    }

    function updateIconPreview() {
        const iconName = document.getElementById('create-icon')?.value.trim() || 'circle';
        const preview = document.getElementById('icon-preview');
        if (preview) {
            preview.className = `fas fa-${iconName}`;
        }
    }

    function parseCSV(csvText) {
        const lines = csvText.trim().split('\n');
        if (lines.length < 2) return [];

        const headers = lines[0].split(',').map(h => h.trim());
        const data = [];

        for (let i = 1; i < lines.length; i++) {
            const values = lines[i].split(',').map(v => v.trim());
            const row = {};
            headers.forEach((header, idx) => {
                row[header] = values[idx] || '';
            });
            data.push(row);
        }

        return data;
    }

    async function handleCSVImport() {
        if (!CONFIG.workspaceId || !CONFIG.sessionToken) {
            showAlert('Workspace ID and session token required', 'error');
            return;
        }

        const csvData = document.getElementById('csv-data')?.value.trim();
        const updateExisting = document.getElementById('csv-update-existing')?.checked;

        if (!csvData) {
            showAlert('Please paste CSV data', 'error');
            return;
        }

        try {
            const rows = parseCSV(csvData);
            if (rows.length === 0) {
                showAlert('No data found in CSV', 'error');
                return;
            }

            showAlert(`Processing ${rows.length} task type(s)...`, 'info');

            let success = 0;
            let errors = 0;

            for (const row of rows) {
                try {
                    const name = row.name || row.Name || '';
                    const namePlural = row.name_plural || row['name_plural'] || row.Name_Plural || name + 's';
                    const description = row.description || row.Description || '';
                    const icon = row.icon || row.Icon || 'circle';
                    const iconSource = row.icon_source || row['icon_source'] || row.Icon_Source || 'fas';

                    if (!name) {
                        errors++;
                        continue;
                    }

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
                            avatar_source: iconSource,
                            avatar_value: icon
                        })
                    });

                    if (response.ok) {
                        success++;
                    } else {
                        errors++;
                    }

                    await new Promise(resolve => setTimeout(resolve, 300));
                } catch (error) {
                    errors++;
                }
            }

            showAlert(`Import complete: ${success} created, ${errors} errors`, success > 0 ? 'success' : 'error');
            loadTaskTypes();
        } catch (error) {
            showAlert(`Error: ${error.message}`, 'error');
        }
    }

    // Initialize on load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();



