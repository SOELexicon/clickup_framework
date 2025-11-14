/**
 * ClickUp Task Type Description Updater Bookmarklet
 * 
 * This bookmarklet updates all custom task types with comprehensive descriptions.
 * 
 * Usage:
 * 1. Navigate to ClickUp Settings > Task Types page
 * 2. Copy this entire script
 * 3. Create a bookmark with this as the URL (prefixed with javascript:)
 * 4. Click the bookmark while on the Task Types page
 * 
 * Or run directly in console:
 * 1. Open DevTools (F12)
 * 2. Go to Console tab
 * 3. Paste and run this script
 */

(function() {
    'use strict';
    
    // Configuration
    const CONFIG = {
        dryRun: false, // Set to true to preview changes without updating
        updateExisting: true, // Set to false to skip task types that already have descriptions
        updateIcons: true, // Set to false to preserve existing icons
    };
    
    // Comprehensive descriptions for common task types
    const TASK_TYPE_DESCRIPTIONS = {
        // Development & Coding
        'task': 'Standard development task for implementing features, fixing bugs, or making improvements. Use for general coding work that requires implementation, testing, and review.',
        'coding task': 'Complex development work requiring detailed technical specifications, architecture decisions, and implementation. Use for new features, system integrations, or significant code changes.',
        'normal task': 'Standard work item for tracking general tasks, assignments, and to-dos. Use for routine work that doesn\'t require specialized categorization.',
        'development': 'Active development work including coding, debugging, testing, and integration. Use for all software development activities.',
        'feature': 'New functionality or capability being added to the system. Use for user-facing features, API endpoints, or significant enhancements.',
        'bug': 'Software defect or unexpected behavior that needs to be fixed. Use for errors, crashes, incorrect behavior, or quality issues.',
        'bug fix': 'Addressing software defects with clear reproduction steps, root cause analysis, and verification. Use for fixing errors, crashes, or unexpected behavior.',
        'fix': 'Correcting issues, errors, or problems in existing functionality. Use for quick fixes, patches, or minor corrections.',
        
        // Architecture & Design
        'architecture': 'System design, architectural decisions, and structural changes. Use for designing new systems, refactoring architecture, or making significant design decisions.',
        'design': 'UI/UX design work, wireframes, mockups, and visual design. Use for user interface design, user experience improvements, or design system work.',
        'refactor': 'Code restructuring to improve quality, maintainability, or performance without changing functionality. Use for code cleanup, optimization, or restructuring.',
        
        // Documentation & Communication
        'documentation': 'Creating or updating technical documentation, user guides, API docs, or knowledge base articles. Use for writing, editing, or maintaining documentation.',
        'doc': 'Documentation work including writing, editing, or updating docs. Use for technical documentation, user guides, or knowledge base content.',
        'research': 'Exploratory work to answer questions, evaluate options, or investigate solutions. Use for feasibility studies, technology evaluation, or problem analysis.',
        'investigation': 'Investigating issues, analyzing problems, or researching solutions. Use for debugging complex issues, performance analysis, or root cause investigation.',
        
        // Testing & Quality
        'testing': 'Test creation, execution, and quality assurance work. Use for writing tests, running test suites, or QA activities.',
        'test': 'Testing activities including unit tests, integration tests, or manual testing. Use for test development, test execution, or quality verification.',
        'qa': 'Quality assurance activities including testing, validation, and verification. Use for QA work, test planning, or quality checks.',
        'code review': 'Systematic review of code changes for quality, security, and best practices. Use for reviewing pull requests, code audits, or peer reviews.',
        'review': 'Reviewing work including code reviews, design reviews, or document reviews. Use for peer review, quality checks, or approval processes.',
        
        // Infrastructure & DevOps
        'deployment': 'Releasing code to production or other environments. Use for deployments, releases, or environment updates.',
        'devops': 'Infrastructure, deployment, and operations work. Use for CI/CD, infrastructure changes, or operational tasks.',
        'infrastructure': 'Infrastructure setup, configuration, or changes. Use for server setup, cloud infrastructure, or system configuration.',
        'config': 'Configuration changes to systems, applications, or environments. Use for updating settings, environment variables, or configuration files.',
        'configuration': 'Modifying system configuration without code changes. Use for settings updates, environment configuration, or system tuning.',
        
        // Database & Data
        'database': 'Database-related work including schema changes, queries, or data migrations. Use for database design, optimization, or data management.',
        'migration': 'Database or data migrations between systems or versions. Use for schema migrations, data migrations, or system upgrades.',
        'data': 'Data-related work including data processing, analysis, or management. Use for data pipelines, data analysis, or data quality work.',
        
        // Security & Performance
        'security': 'Security-focused tasks including vulnerability fixes, security audits, or security improvements. Use for security patches, security reviews, or security enhancements.',
        'performance': 'Performance optimization work to improve speed, efficiency, or resource usage. Use for performance tuning, optimization, or efficiency improvements.',
        'optimization': 'Improving performance, efficiency, or resource usage. Use for code optimization, query optimization, or system tuning.',
        
        // Project Management
        'project': 'Project-level container for related work with multiple subtasks and milestones. Use for organizing large initiatives or project planning.',
        'epic': 'Large work item that spans multiple iterations or releases. Use for major features or initiatives broken into smaller tasks.',
        'milestone': 'Key project checkpoint or deliverable marking significant progress. Use for project milestones, releases, or major achievements.',
        'goal': 'Measurable objective with defined success criteria. Use for setting goals, objectives, or targets.',
        'story': 'User story or feature story describing functionality from a user perspective. Use for user-facing features or product requirements.',
        
        // Business & Operations
        'account': 'Manage client or customer account details and interactions. Use for account management, customer relations, or account-related work.',
        'client': 'Client-related work including communication, requirements, or deliverables. Use for client management, client communications, or client projects.',
        'customer': 'Customer-facing work including support, onboarding, or relationship management. Use for customer service, customer success, or customer engagement.',
        'support': 'Customer or user support work including troubleshooting, assistance, or issue resolution. Use for support tickets, help desk work, or user assistance.',
        
        // Maintenance & Operations
        'maintenance': 'Routine maintenance work to keep systems running smoothly. Use for regular upkeep, system maintenance, or operational tasks.',
        'chore': 'Routine maintenance tasks that don\'t add features but keep the codebase healthy. Use for dependency updates, cleanup, or maintenance work.',
        'cleanup': 'Cleaning up code, data, or systems. Use for removing unused code, cleaning up data, or system cleanup.',
        
        // Planning & Analysis
        'planning': 'Planning work including project planning, sprint planning, or roadmap planning. Use for planning activities, scheduling, or coordination.',
        'analysis': 'Analysis work including requirements analysis, data analysis, or system analysis. Use for analyzing requirements, data, or systems.',
        'specification': 'Creating specifications, requirements, or technical specifications. Use for writing specs, requirements documents, or technical designs.',
        
        // Communication & Collaboration
        'meeting': 'Meeting-related work including scheduling, preparation, or follow-up. Use for meeting organization, notes, or action items.',
        'communication': 'Communication work including emails, messages, or announcements. Use for team communication, stakeholder updates, or notifications.',
        
        // Learning & Training
        'training': 'Training or learning activities including workshops, courses, or knowledge sharing. Use for training sessions, learning activities, or knowledge transfer.',
        'learning': 'Learning new skills, technologies, or concepts. Use for skill development, research, or educational activities.',
    };
    
    // Font Awesome icon mappings for task types
    const TASK_TYPE_ICONS = {
        // Development & Coding
        'task': 'check-circle',
        'coding task': 'code',
        'normal task': 'list-check',
        'development': 'laptop-code',
        'feature': 'rocket',
        'bug': 'bug',
        'bug fix': 'bug',
        'fix': 'wrench',
        
        // Architecture & Design
        'architecture': 'sitemap',
        'design': 'palette',
        'refactor': 'sync-alt',
        
        // Documentation & Communication
        'documentation': 'book',
        'doc': 'file-alt',
        'research': 'search',
        'investigation': 'search',
        
        // Testing & Quality
        'testing': 'flask',
        'test': 'vial',
        'qa': 'check-double',
        'code review': 'eye',
        'review': 'clipboard-check',
        
        // Infrastructure & DevOps
        'deployment': 'cloud-upload-alt',
        'devops': 'server',
        'infrastructure': 'network-wired',
        'config': 'cog',
        'configuration': 'cogs',
        
        // Database & Data
        'database': 'database',
        'migration': 'exchange-alt',
        'data': 'chart-bar',
        
        // Security & Performance
        'security': 'shield-alt',
        'performance': 'tachometer-alt',
        'optimization': 'bolt',
        
        // Project Management
        'project': 'folder-open',
        'epic': 'layer-group',
        'milestone': 'flag-checkered',
        'goal': 'bullseye',
        'story': 'book-open',
        
        // Business & Operations
        'account': 'user-circle',
        'client': 'handshake',
        'customer': 'users',
        'support': 'headset',
        
        // Maintenance & Operations
        'maintenance': 'tools',
        'chore': 'broom',
        'cleanup': 'broom',
        
        // Planning & Analysis
        'planning': 'calendar-alt',
        'analysis': 'chart-line',
        'specification': 'file-contract',
        
        // Communication & Collaboration
        'meeting': 'comments',
        'communication': 'comment-dots',
        
        // Learning & Training
        'training': 'chalkboard-teacher',
        'learning': 'graduation-cap',
    };
    
    /**
     * Generate an appropriate Font Awesome icon for a task type based on its name
     */
    function generateIcon(taskTypeName) {
        const nameLower = taskTypeName.toLowerCase().trim();
        
        // Check for exact match first
        if (TASK_TYPE_ICONS[nameLower]) {
            return TASK_TYPE_ICONS[nameLower];
        }
        
        // Check for partial matches (task type name contains key or vice versa)
        for (const [key, icon] of Object.entries(TASK_TYPE_ICONS)) {
            if (nameLower.includes(key) || key.includes(nameLower)) {
                return icon;
            }
        }
        
        // Extended pattern matching for better coverage
        // Bug/Issue related
        if (nameLower.includes('bug') || nameLower.includes('issue') || nameLower.includes('defect') || 
            nameLower.includes('error') || nameLower.includes('fix') || nameLower.includes('crash')) {
            return 'bug';
        }
        
        // Feature/Enhancement related
        if (nameLower.includes('feature') || nameLower.includes('enhancement') || 
            nameLower.includes('improvement') || nameLower.includes('new')) {
            return 'rocket';
        }
        
        // Documentation related
        if (nameLower.includes('doc') || nameLower.includes('document') || 
            nameLower.includes('readme') || nameLower.includes('guide') || nameLower.includes('manual')) {
            return 'book';
        }
        
        // Testing related
        if (nameLower.includes('test') || nameLower.includes('qa') || nameLower.includes('quality') ||
            nameLower.includes('verify') || nameLower.includes('validation')) {
            return 'flask';
        }
        
        // Project/Epic related
        if (nameLower.includes('project') || nameLower.includes('initiative') || 
            nameLower.includes('epic') || nameLower.includes('program')) {
            return 'folder-open';
        }
        
        // Security related
        if (nameLower.includes('security') || nameLower.includes('vulnerability') || 
            nameLower.includes('audit') || nameLower.includes('compliance')) {
            return 'shield-alt';
        }
        
        // Database/Data related
        if (nameLower.includes('database') || nameLower.includes('data') || 
            nameLower.includes('sql') || nameLower.includes('db')) {
            return 'database';
        }
        
        // Deployment/Release related
        if (nameLower.includes('deploy') || nameLower.includes('release') || 
            nameLower.includes('publish') || nameLower.includes('ship')) {
            return 'cloud-upload-alt';
        }
        
        // Meeting/Communication related
        if (nameLower.includes('meeting') || nameLower.includes('communication') || 
            nameLower.includes('sync') || nameLower.includes('standup')) {
            return 'comments';
        }
        
        // Account/Client/Customer related
        if (nameLower.includes('account') || nameLower.includes('client') || 
            nameLower.includes('customer') || nameLower.includes('user')) {
            return 'user-circle';
        }
        
        // Support/Help related
        if (nameLower.includes('support') || nameLower.includes('help') || 
            nameLower.includes('ticket') || nameLower.includes('assistance')) {
            return 'headset';
        }
        
        // Maintenance/Cleanup related
        if (nameLower.includes('maintenance') || nameLower.includes('cleanup') || 
            nameLower.includes('chore') || nameLower.includes('housekeeping')) {
            return 'broom';
        }
        
        // Planning/Analysis related
        if (nameLower.includes('planning') || nameLower.includes('plan') || 
            nameLower.includes('roadmap') || nameLower.includes('strategy')) {
            return 'calendar-alt';
        }
        
        // Analysis/Research related
        if (nameLower.includes('analysis') || nameLower.includes('research') || 
            nameLower.includes('investigation') || nameLower.includes('study')) {
            return 'search';
        }
        
        // Design/UI related
        if (nameLower.includes('design') || nameLower.includes('ui') || 
            nameLower.includes('ux') || nameLower.includes('mockup') || nameLower.includes('wireframe')) {
            return 'palette';
        }
        
        // Architecture/Infrastructure related
        if (nameLower.includes('architecture') || nameLower.includes('infrastructure') || 
            nameLower.includes('system') || nameLower.includes('platform')) {
            return 'sitemap';
        }
        
        // Code/Development related
        if (nameLower.includes('code') || nameLower.includes('development') || 
            nameLower.includes('coding') || nameLower.includes('programming')) {
            return 'laptop-code';
        }
        
        // Review related
        if (nameLower.includes('review') || nameLower.includes('audit') || 
            nameLower.includes('inspection')) {
            return 'eye';
        }
        
        // Refactor related
        if (nameLower.includes('refactor') || nameLower.includes('restructure') || 
            nameLower.includes('reorganize')) {
            return 'sync-alt';
        }
        
        // Configuration/Settings related
        if (nameLower.includes('config') || nameLower.includes('setting') || 
            nameLower.includes('setup') || nameLower.includes('install')) {
            return 'cog';
        }
        
        // Migration related
        if (nameLower.includes('migration') || nameLower.includes('migrate') || 
            nameLower.includes('upgrade') || nameLower.includes('update')) {
            return 'exchange-alt';
        }
        
        // Performance/Optimization related
        if (nameLower.includes('performance') || nameLower.includes('optimization') || 
            nameLower.includes('optimize') || nameLower.includes('speed')) {
            return 'tachometer-alt';
        }
        
        // Milestone/Goal related
        if (nameLower.includes('milestone') || nameLower.includes('goal') || 
            nameLower.includes('objective') || nameLower.includes('target')) {
            return 'flag-checkered';
        }
        
        // Training/Learning related
        if (nameLower.includes('training') || nameLower.includes('learning') || 
            nameLower.includes('education') || nameLower.includes('tutorial')) {
            return 'graduation-cap';
        }
        
        // Warning/Alert related
        if (nameLower.includes('warning') || nameLower.includes('alert') || 
            nameLower.includes('caution') || nameLower.includes('notice')) {
            return 'triangle-exclamation';
        }
        
        // Task/Work related (generic)
        if (nameLower.includes('task') || nameLower.includes('work') || 
            nameLower.includes('todo') || nameLower.includes('item')) {
            return 'check-circle';
        }
        
        // Story/Requirement related
        if (nameLower.includes('story') || nameLower.includes('requirement') || 
            nameLower.includes('spec') || nameLower.includes('specification')) {
            return 'book-open';
        }
        
        // Default: use first letter or a generic icon based on name
        // Try to use a meaningful icon based on first letter
        const firstChar = nameLower.charAt(0);
        const iconMap = {
            'a': 'address-card',
            'b': 'book',
            'c': 'code',
            'd': 'database',
            'e': 'envelope',
            'f': 'folder',
            'g': 'gift',
            'h': 'home',
            'i': 'info-circle',
            'j': 'journal',
            'k': 'key',
            'l': 'list',
            'm': 'map',
            'n': 'newspaper',
            'o': 'object-group',
            'p': 'paper-plane',
            'q': 'question-circle',
            'r': 'rocket',
            's': 'star',
            't': 'tag',
            'u': 'user',
            'v': 'video',
            'w': 'wrench',
            'x': 'times-circle',
            'y': 'youtube',
            'z': 'zap'
        };
        
        if (iconMap[firstChar]) {
            return iconMap[firstChar];
        }
        
        // Last resort: use a generic but distinct icon
        return 'square';
    }
    
    /**
     * Generate a comprehensive description for a task type based on its name
     */
    function generateDescription(taskTypeName) {
        const nameLower = taskTypeName.toLowerCase().trim();
        
        // Check for exact match
        if (TASK_TYPE_DESCRIPTIONS[nameLower]) {
            return TASK_TYPE_DESCRIPTIONS[nameLower];
        }
        
        // Check for partial matches
        for (const [key, description] of Object.entries(TASK_TYPE_DESCRIPTIONS)) {
            if (nameLower.includes(key) || key.includes(nameLower)) {
                return description;
            }
        }
        
        // Generate a generic description based on common patterns
        if (nameLower.includes('task') || nameLower.includes('work')) {
            return `Standard ${taskTypeName} for tracking work items, assignments, and progress. Use for organizing and managing ${taskTypeName.toLowerCase()} work.`;
        }
        
        if (nameLower.includes('project') || nameLower.includes('initiative')) {
            return `${taskTypeName} container for organizing related work, tasks, and milestones. Use for managing ${taskTypeName.toLowerCase()} scope, timeline, and deliverables.`;
        }
        
        if (nameLower.includes('bug') || nameLower.includes('issue') || nameLower.includes('defect')) {
            return `${taskTypeName} for tracking and resolving issues, defects, or problems. Use for bug reports, issue tracking, or problem resolution.`;
        }
        
        if (nameLower.includes('feature') || nameLower.includes('enhancement')) {
            return `${taskTypeName} for new functionality, capabilities, or improvements. Use for feature development, enhancements, or product improvements.`;
        }
        
        if (nameLower.includes('doc') || nameLower.includes('document')) {
            return `${taskTypeName} for creating, updating, or maintaining documentation. Use for technical docs, user guides, or knowledge base content.`;
        }
        
        // Default generic description
        return `${taskTypeName} for organizing and tracking work. Use this task type to categorize and manage ${taskTypeName.toLowerCase()} work items.`;
    }
    
    /**
     * Get workspace ID from current page
     */
    function getWorkspaceId() {
        // Try to extract from URL (most reliable)
        const urlMatch = window.location.pathname.match(/\/(\d+)\//);
        if (urlMatch) {
            return urlMatch[1];
        }
        
        // Try to extract from URL query params
        const urlParams = new URLSearchParams(window.location.search);
        const wsId = urlParams.get('workspace_id') || urlParams.get('team_id');
        if (wsId) {
            return wsId;
        }
        
        // Try to extract from page data/React state
        const pageData = window.__INITIAL_STATE__ || window.__CLICKUP_DATA__ || window.__NEXT_DATA__;
        if (pageData) {
            if (pageData.workspaceId) return pageData.workspaceId;
            if (pageData.teamId) return pageData.teamId;
            if (pageData.props && pageData.props.pageProps) {
                const props = pageData.props.pageProps;
                if (props.workspaceId) return props.workspaceId;
                if (props.teamId) return props.teamId;
            }
        }
        
        // Try to extract from React component tree
        try {
            const reactRoot = document.querySelector('[data-reactroot]') || document.getElementById('root');
            if (reactRoot && reactRoot._reactInternalInstance) {
                // Try to find workspace ID in React fiber
                let fiber = reactRoot._reactInternalInstance;
                while (fiber) {
                    if (fiber.memoizedProps && fiber.memoizedProps.workspaceId) {
                        return fiber.memoizedProps.workspaceId;
                    }
                    fiber = fiber.return;
                }
            }
        } catch (e) {
            // React inspection failed, continue
        }
        
        // Try to extract from localStorage/sessionStorage
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && (key.includes('workspace') || key.includes('team'))) {
                const value = localStorage.getItem(key);
                if (value && /^\d+$/.test(value)) {
                    return value;
                }
            }
        }
        
        // Last resort: try to extract from any API calls in the page
        console.warn('⚠️ Could not auto-detect workspace ID. Please provide it manually.');
        console.log('💡 To find your workspace ID:');
        console.log('   1. Look at the URL: https://app.clickup.com/{WORKSPACE_ID}/...');
        console.log('   2. Or run: window.location.pathname.match(/(\\d+)/)[0]');
        
        // Use a safer method than prompt() - check if we can use it
        let workspaceId = null;
        try {
            if (typeof prompt !== 'undefined') {
                workspaceId = prompt('Please enter your ClickUp Workspace ID:');
            }
        } catch (e) {
            // prompt() blocked, use console input
        }
        
        if (workspaceId) {
            return workspaceId.trim();
        }
        
        // If we still don't have it, try to extract from the page URL one more time
        const pathParts = window.location.pathname.split('/').filter(p => p && /^\d+$/.test(p));
        if (pathParts.length > 0) {
            return pathParts[0];
        }
        
        throw new Error('Could not determine workspace ID. Please run this on the ClickUp Task Types settings page (URL should contain your workspace ID).');
    }
    
    /**
     * Get session token from cookies or localStorage
     */
    function getSessionToken() {
        // Try to get from cookies (most common location)
        const cookies = document.cookie.split(';');
        for (const cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name && value) {
                const nameLower = name.toLowerCase();
                if ((nameLower.includes('session') || nameLower.includes('token') || nameLower.includes('auth')) && 
                    nameLower.includes('clickup')) {
                    // Check if it's a JWT (starts with eyJ)
                    if (value.startsWith('eyJ')) {
                        return decodeURIComponent(value);
                    }
                }
            }
        }
        
        // Try to get from localStorage - check all keys for JWT tokens
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key) {
                const value = localStorage.getItem(key);
                // Check if it's a JWT (starts with eyJ)
                if (value && value.startsWith('eyJ')) {
                    return value;
                }
            }
        }
        
        // Try to get from sessionStorage - check all keys for JWT tokens
        for (let i = 0; i < sessionStorage.length; i++) {
            const key = sessionStorage.key(i);
            if (key) {
                const value = sessionStorage.getItem(key);
                // Check if it's a JWT (starts with eyJ)
                if (value && value.startsWith('eyJ')) {
                    return value;
                }
            }
        }
        
        // Try to intercept from fetch/XMLHttpRequest if available
        try {
            // Check if we can access the authorization header from recent requests
            // This is a fallback - we'll provide instructions instead
        } catch (e) {
            // Can't intercept, continue
        }
        
        // Try to intercept from fetch requests if we can
        // Check if there's a way to get it from the page's fetch interceptor
        try {
            // Look for token in window object or React state
            if (window.__CLICKUP_TOKEN || window.__CLICKUP_SESSION_TOKEN) {
                const token = (window.__CLICKUP_TOKEN || window.__CLICKUP_SESSION_TOKEN).replace(/^Bearer\s+/i, '');
                if (token.startsWith('eyJ')) {
                    return token;
                }
            }
        } catch (e) {
            // Continue
        }
        
        // Provide helpful instructions instead of using prompt()
        console.warn('⚠️ Could not auto-detect session token.');
        console.log('💡 To get your session token:');
        console.log('   1. Open DevTools (F12) > Network tab');
        console.log('   2. Refresh the page or perform any action');
        console.log('   3. Find any request to clickup.com');
        console.log('   4. Click on it > Headers > Request Headers');
        console.log('   5. Copy the "authorization" header value (JWT starting with "eyJ")');
        console.log('   6. Run: window.__CLICKUP_SESSION_TOKEN = "your-token-here"');
        console.log('   7. Then run this script again');
        
        // Try to get from a global variable (user can set it manually)
        if (window.__CLICKUP_SESSION_TOKEN) {
            return window.__CLICKUP_SESSION_TOKEN.replace(/^Bearer\s+/i, '');
        }
        
        // Last resort: try prompt() if available, but handle gracefully
        let token = null;
        try {
            if (typeof prompt !== 'undefined') {
                token = prompt('Could not find session token automatically. Please paste your session token (JWT):');
            }
        } catch (e) {
            // prompt() blocked
        }
        
        if (token) {
            return token.trim().replace(/^Bearer\s+/i, '');
        }
        
        throw new Error('Session token required. Please set window.__CLICKUP_SESSION_TOKEN = "your-token" and run again, or check console for instructions.');
    }
    
    /**
     * Fetch all custom task types using v1 API
     */
    async function fetchTaskTypes(workspaceId, sessionToken) {
        try {
            // Use v1 API endpoint (same as web interface)
            // Note: v1 uses /customItems (plural) for GET, /customItem (singular) for PUT
            const response = await fetch(`https://frontdoor-prod-eu-west-1-3.clickup.com/tasks/v1/${workspaceId}/customItems`, {
                method: 'GET',
                headers: {
                    'Authorization': sessionToken.startsWith('Bearer ') ? sessionToken : `Bearer ${sessionToken}`,
                    'Accept': 'application/json, text/plain, */*',
                    'x-workspace-id': workspaceId,
                    'Content-Type': 'application/json',
                },
                credentials: 'include', // Include cookies for session
            });
            
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Failed to fetch task types: ${response.status} ${response.statusText} - ${errorText}`);
            }
            
            const data = await response.json();
            // v1 API might return data in a different format
            return data.customItems || data.custom_items || data || [];
        } catch (error) {
            console.error('Error fetching task types:', error);
            throw error;
        }
    }
    
    /**
     * Update a task type description
     */
    async function updateTaskType(workspaceId, taskTypeId, taskTypeData, sessionToken) {
        // Generate icon if we want to update it, otherwise preserve existing
        let iconValue = taskTypeData.avatar_value || taskTypeData.icon || 'circle';
        if (CONFIG.updateIcons) {
            iconValue = generateIcon(taskTypeData.name);
        }
        
        const updateData = {
            name: taskTypeData.name,
            name_plural: taskTypeData.name_plural || taskTypeData.name + 's',
            description: generateDescription(taskTypeData.name),
            avatar_source: 'fas', // Font Awesome Solid
            avatar_value: iconValue,
        };
        
        if (CONFIG.dryRun) {
            console.log(`[DRY RUN] Would update ${taskTypeData.name}:`);
            console.log(`  Icon: ${updateData.avatar_value}`);
            console.log(`  Description: ${updateData.description.substring(0, 80)}...`);
            return { dryRun: true, ...updateData };
        }
        
        try {
            const response = await fetch(`https://frontdoor-prod-eu-west-1-3.clickup.com/tasks/v1/${workspaceId}/customItem/${taskTypeId}`, {
                method: 'PUT',
                headers: {
                    'Authorization': sessionToken.startsWith('Bearer ') ? sessionToken : `Bearer ${sessionToken}`,
                    'Content-Type': 'application/json',
                    'Accept': 'application/json, text/plain, */*',
                    'x-workspace-id': workspaceId,
                },
                credentials: 'include', // Include cookies for session
                body: JSON.stringify(updateData),
            });
            
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Failed to update task type: ${response.status} ${response.statusText} - ${errorText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error(`Error updating task type ${taskTypeData.name}:`, error);
            throw error;
        }
    }
    
    /**
     * Main execution function
     */
    async function main() {
        console.log('🚀 Starting Task Type Description Updater...\n');
        
        try {
            // Get workspace ID
            console.log('📋 Getting workspace ID...');
            const workspaceId = getWorkspaceId();
            console.log(`✓ Workspace ID: ${workspaceId}\n`);
            
            // Get session token
            console.log('🔑 Getting session token...');
            const sessionToken = getSessionToken();
            console.log(`✓ Session token obtained\n`);
            
            // Fetch task types
            console.log('📥 Fetching custom task types...');
            const taskTypes = await fetchTaskTypes(workspaceId, sessionToken);
            console.log(`✓ Found ${taskTypes.length} task type(s)\n`);
            
            if (taskTypes.length === 0) {
                console.log('ℹ️ No custom task types found.');
                return;
            }
            
            // Display task types
            console.log('📋 Current Task Types:');
            taskTypes.forEach((tt, index) => {
                const hasDesc = tt.description && tt.description.trim() !== '';
                console.log(`  ${index + 1}. ${tt.name} (ID: ${tt.id})${hasDesc ? ' - Has description' : ' - No description'}`);
            });
            console.log('');
            
            if (CONFIG.dryRun) {
                console.log('🔍 DRY RUN MODE - No changes will be made\n');
            }
            
            // Update each task type
            const results = [];
            for (const taskType of taskTypes) {
                const hasDescription = taskType.description && taskType.description.trim() !== '';
                
                if (!CONFIG.updateExisting && hasDescription) {
                    console.log(`⏭️  Skipping ${taskType.name} (already has description)`);
                    results.push({ taskType: taskType.name, status: 'skipped', reason: 'has description' });
                    continue;
                }
                
                try {
                    console.log(`🔄 Updating ${taskType.name}...`);
                    const result = await updateTaskType(workspaceId, taskType.id, taskType, sessionToken);
                    const newDescription = CONFIG.dryRun ? result.description : (result.custom_item?.description || result.description);
                    const newIcon = CONFIG.dryRun ? result.avatar_value : (result.custom_item?.avatar_value || result.avatar_value);
                    console.log(`✓ Updated ${taskType.name}`);
                    console.log(`  Icon: ${newIcon}`);
                    console.log(`  Description: ${newDescription.substring(0, 80)}...`);
                    results.push({ taskType: taskType.name, status: 'success', description: newDescription, icon: newIcon });
                    
                    // Small delay to avoid rate limiting
                    await new Promise(resolve => setTimeout(resolve, 500));
                } catch (error) {
                    console.error(`✗ Failed to update ${taskType.name}:`, error.message);
                    results.push({ taskType: taskType.name, status: 'error', error: error.message });
                }
            }
            
            // Summary
            console.log('\n📊 Summary:');
            const successful = results.filter(r => r.status === 'success').length;
            const skipped = results.filter(r => r.status === 'skipped').length;
            const errors = results.filter(r => r.status === 'error').length;
            
            console.log(`  ✓ Successfully updated: ${successful}`);
            console.log(`  ⏭️  Skipped: ${skipped}`);
            console.log(`  ✗ Errors: ${errors}`);
            
            if (CONFIG.dryRun) {
                console.log('\n💡 This was a dry run. Set CONFIG.dryRun = false to apply changes.');
            } else {
                console.log('\n✅ All task types updated! Refresh the page to see changes.');
            }
            
        } catch (error) {
            console.error('❌ Error:', error.message);
            console.error('Full error:', error);
            
            // Use a safer alert alternative
            try {
                if (typeof alert !== 'undefined') {
                    alert(`Error: ${error.message}\n\nCheck console for details.`);
                } else {
                    console.error('Alert not available. Error:', error.message);
                }
            } catch (e) {
                // alert() also blocked, just log to console
                console.error('Both prompt() and alert() are blocked. Please check console for error details.');
            }
        }
    }
    
    // Run the script
    main();
})();

