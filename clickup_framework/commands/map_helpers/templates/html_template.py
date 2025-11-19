"""HTML template generator for interactive code map visualization with WebGL fire shader effects."""

import sys
import base64
from clickup_framework.utils.colors import colorize, TextColor
from .shader_loader import get_fire_shaders


def export_mermaid_to_html(mermaid_content: str, output_file: str, title: str = "Code Map", use_color: bool = False) -> bool:
    """
    Export mermaid diagram to interactive HTML with zoom, pan, and WebGL fire shader animations.

    Args:
        mermaid_content: Mermaid diagram code
        output_file: Output HTML file path
        title: Page title
        use_color: Whether to use colored output

    Returns:
        True if successful, False otherwise
    """
    # Load WebGL shaders from external files
    vertex_shader, fragment_shader = get_fire_shaders()
    html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{
            startOnLoad: false,  // We'll manually load content from base64 to avoid HTML parsing
            theme: 'dark',
            themeVariables: {{
                primaryColor: 'rgba(16, 185, 129, 0.15)',
                primaryTextColor: '#10b981',
                primaryBorderColor: '#10b981',
                lineColor: '#34d399',
                secondaryColor: 'rgba(139, 92, 246, 0.15)',
                tertiaryColor: 'rgba(168, 85, 247, 0.15)',
                background: '#000000',
                mainBkg: 'rgba(10, 10, 10, 0.3)',
                secondBkg: 'rgba(26, 26, 26, 0.3)',
                tertiaryBkg: 'rgba(42, 42, 42, 0.3)',
                border1: '#10b981',
                border2: '#8b5cf6',
                arrowheadColor: '#10b981',
                fontFamily: 'ui-monospace, monospace',
                clusterBkg: 'rgba(26, 26, 26, 0.2)',
                clusterBorder: '#10b981',
                edgeLabelBackground: 'rgba(10, 10, 10, 0.8)',
                nodeTextColor: '#10b981'
            }},
            flowchart: {{
                useMaxWidth: false,
                htmlLabels: true,
                curve: 'linear',
                nodeSpacing: 100,
                rankSpacing: 100,
                defaultRenderer: 'elk'
            }},
            elk: {{
                mergeEdges: true,
                nodePlacementStrategy: 'SIMPLE'
            }},
            sequence: {{
                useMaxWidth: false,
                wrap: true,
                height: 600
            }},
            class: {{
                useMaxWidth: false
            }},
            er: {{
                useMaxWidth: false
            }},
            securityLevel: 'loose',
            logLevel: 'error',
            arrowMarkerAbsolute: true
        }});
    </script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: ui-sans-serif, system-ui, -apple-system, sans-serif;
            background: linear-gradient(135deg, #000000 0%, #0a0a0a 50%, #1a1a1a 100%);
            color: #10b981;
            min-height: 100vh;
            overflow: hidden;
        }}
        .container {{
            display: flex;
            flex-direction: column;
            height: 100vh;
        }}
        .main-content {{
            display: flex;
            flex: 1;
            overflow: hidden;
        }}
        .sidebar {{
            width: 300px;
            background: rgba(10, 10, 10, 0.95);
            border-right: 2px solid #10b981;
            overflow-y: auto;
            padding: 1rem;
            box-shadow: 4px 0 6px -1px rgba(16, 185, 129, 0.3);
            transition: transform 0.3s ease;
        }}
        .sidebar.collapsed {{
            transform: translateX(-100%);
        }}
        .sidebar h2 {{
            color: #10b981;
            font-size: 1.125rem;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid rgba(16, 185, 129, 0.3);
            text-shadow: 0 0 10px rgba(16, 185, 129, 0.5);
        }}
        .sidebar-search {{
            width: 100%;
            background: rgba(0, 0, 0, 0.5);
            border: 1px solid #10b981;
            padding: 0.5rem;
            color: #10b981;
            border-radius: 0.25rem;
            margin-bottom: 1rem;
            font-family: ui-monospace, monospace;
        }}
        .sidebar-search:focus {{
            outline: none;
            border-color: #8b5cf6;
            box-shadow: 0 0 10px rgba(139, 92, 246, 0.5);
        }}
        .file-tree {{
            list-style: none;
            padding: 0;
        }}
        .tree-item {{
            padding: 0.375rem 0.5rem;
            margin: 0.25rem 0;
            cursor: pointer;
            border-radius: 0.25rem;
            transition: all 0.2s;
            font-size: 0.875rem;
            font-family: ui-monospace, monospace;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        .tree-item:hover {{
            background: rgba(16, 185, 129, 0.2);
            padding-left: 0.75rem;
            box-shadow: 0 0 10px rgba(16, 185, 129, 0.3);
        }}
        .tree-item.active {{
            background: rgba(139, 92, 246, 0.3);
            border-left: 3px solid #8b5cf6;
            padding-left: 0.75rem;
        }}
        .tree-item .icon {{
            flex-shrink: 0;
        }}
        .tree-folder {{
            font-weight: 600;
            color: #8b5cf6;
        }}
        .tree-file {{
            color: #10b981;
        }}
        .tree-function {{
            color: #06b6d4;
            padding-left: 1.5rem;
            font-size: 0.8125rem;
        }}
        .tree-children {{
            padding-left: 1rem;
            border-left: 1px solid rgba(16, 185, 129, 0.2);
            margin-left: 0.5rem;
        }}
        .toggle-sidebar {{
            position: absolute;
            left: 300px;
            top: 50%;
            transform: translateY(-50%);
            background: rgba(16, 185, 129, 0.9);
            border: none;
            color: #000;
            padding: 0.5rem;
            cursor: pointer;
            border-radius: 0 0.25rem 0.25rem 0;
            z-index: 1000;
            transition: all 0.3s;
        }}
        .toggle-sidebar:hover {{
            background: #8b5cf6;
            color: #fff;
        }}
        .sidebar.collapsed ~ .toggle-sidebar {{
            left: 0;
        }}
        /* Right sidebar for node details */
        .node-details {{
            position: fixed;
            right: 0;
            top: 0;
            bottom: 0;
            width: 350px;
            background: rgba(10, 10, 10, 0.98);
            border-left: 2px solid #8b5cf6;
            padding: 2rem 1.5rem;
            overflow-y: auto;
            transform: translateX(100%);
            transition: transform 0.3s ease;
            box-shadow: -4px 0 6px -1px rgba(139, 92, 246, 0.3);
            z-index: 1001;
        }}
        .node-details.visible {{
            transform: translateX(0);
        }}
        .node-details h2 {{
            color: #8b5cf6;
            font-size: 1.25rem;
            margin-bottom: 1.5rem;
            padding-bottom: 0.75rem;
            border-bottom: 2px solid rgba(139, 92, 246, 0.4);
            text-shadow: 0 0 15px rgba(139, 92, 246, 0.8);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .node-details .close-btn {{
            background: transparent;
            border: none;
            color: #8b5cf6;
            font-size: 1.5rem;
            cursor: pointer;
            padding: 0.25rem 0.5rem;
            border-radius: 0.25rem;
            transition: all 0.2s;
        }}
        .node-details .close-btn:hover {{
            background: rgba(139, 92, 246, 0.2);
            color: #a78bfa;
        }}
        .node-details .detail-section {{
            margin-bottom: 1.5rem;
        }}
        .node-details .detail-label {{
            color: #10b981;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
            font-weight: 600;
        }}
        .node-details .detail-value {{
            color: #e2e8f0;
            font-size: 0.9375rem;
            font-family: ui-monospace, monospace;
            background: rgba(0, 0, 0, 0.5);
            padding: 0.75rem;
            border-radius: 0.375rem;
            border: 1px solid rgba(139, 92, 246, 0.3);
            word-break: break-word;
        }}
        .node-details .detail-value.multiline {{
            white-space: pre-wrap;
        }}
        .node-details .tag {{
            display: inline-block;
            background: rgba(16, 185, 129, 0.2);
            color: #10b981;
            padding: 0.25rem 0.75rem;
            border-radius: 0.25rem;
            font-size: 0.8125rem;
            margin-right: 0.5rem;
            margin-bottom: 0.5rem;
            border: 1px solid rgba(16, 185, 129, 0.4);
        }}
        .node-details .node-icon {{
            font-size: 2rem;
            margin-bottom: 1rem;
            text-align: center;
        }}
        .header {{
            background: rgba(0, 0, 0, 0.9);
            backdrop-filter: blur(10px);
            padding: 1rem 2rem;
            border-bottom: 2px solid #10b981;
            box-shadow: 0 4px 6px -1px rgba(16, 185, 129, 0.3);
            z-index: 100;
        }}
        .header h1 {{
            font-size: 1.5rem;
            font-weight: 700;
            color: #10b981;
            text-shadow: 0 0 20px rgba(16, 185, 129, 0.8);
        }}
        .controls {{
            margin-top: 0.5rem;
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
            align-items: center;
        }}
        .btn {{
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: #000;
            border: 1px solid #10b981;
            padding: 0.5rem 1rem;
            border-radius: 0.375rem;
            cursor: pointer;
            font-weight: 600;
            font-size: 0.875rem;
            transition: all 0.2s;
            box-shadow: 0 0 10px rgba(16, 185, 129, 0.3);
        }}
        .btn:hover {{
            transform: translateY(-1px);
            box-shadow: 0 0 20px rgba(16, 185, 129, 0.6);
            background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
            color: #fff;
            border-color: #8b5cf6;
        }}
        .btn:active {{
            transform: translateY(0);
        }}
        .zoom-info {{
            font-size: 0.875rem;
            color: #94a3b8;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        .spacing-control {{
            font-size: 0.875rem;
            color: #94a3b8;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-left: 1rem;
        }}
        .spacing-slider {{
            width: 150px;
            height: 4px;
            border-radius: 2px;
            background: #1e293b;
            outline: none;
            -webkit-appearance: none;
            appearance: none;
        }}
        .spacing-slider::-webkit-slider-thumb {{
            -webkit-appearance: none;
            appearance: none;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background: #10b981;
            cursor: pointer;
            box-shadow: 0 0 8px rgba(16, 185, 129, 0.5);
        }}
        .spacing-slider::-moz-range-thumb {{
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background: #10b981;
            cursor: pointer;
            border: none;
            box-shadow: 0 0 8px rgba(16, 185, 129, 0.5);
        }}
        .spacing-slider::-webkit-slider-thumb:hover {{
            background: #34d399;
            box-shadow: 0 0 12px rgba(16, 185, 129, 0.8);
        }}
        .spacing-slider::-moz-range-thumb:hover {{
            background: #34d399;
            box-shadow: 0 0 12px rgba(16, 185, 129, 0.8);
        }}
        .diagram-wrapper {{
            flex: 1;
            position: relative;
            overflow: hidden;
            background: radial-gradient(circle at 50% 50%, #0a0a0a 0%, #000000 100%);
        }}
        .diagram-container {{
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem;
            transform-origin: center center;
            cursor: grab;
            will-change: transform;
            user-select: none;
            -webkit-user-select: none;
            -moz-user-select: none;
            -ms-user-select: none;
        }}
        .diagram-container:active {{
            cursor: grabbing;
        }}
        .diagram-container.zoomed {{
            cursor: move;
        }}
        #mermaid-diagram {{
            display: inline-block;
            background: rgba(10, 10, 10, 0.95);
            padding: 2rem;
            border-radius: 1rem;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5),
                        0 0 50px rgba(16, 185, 129, 0.3),
                        inset 0 0 50px rgba(139, 92, 246, 0.15);
            backdrop-filter: blur(10px);
            border: 2px solid rgba(16, 185, 129, 0.4);
        }}
        /* Ensure SVG elements are visible */
        #mermaid-diagram svg {{
            filter: drop-shadow(0 0 1px rgba(52, 211, 153, 0.3));
        }}
        /* Node highlight animation */
        .node.highlighted rect,
        .node.highlighted polygon {{
            stroke: #8b5cf6 !important;
            stroke-width: 4px !important;
            filter: drop-shadow(0 0 20px rgba(139, 92, 246, 1));
            animation: pulse-highlight 1s ease-in-out;
        }}
        @keyframes pulse-highlight {{
            0%, 100% {{
                stroke-width: 4px;
            }}
            50% {{
                stroke-width: 6px;
            }}
        }}
        /* Mermaid node animations */
        @keyframes fadeInUp {{
            from {{
                opacity: 0;
                transform: translateY(20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        .node, .cluster, .edgePath {{
            animation: fadeInUp 0.5s ease-out backwards;
        }}
        .node:nth-child(1) {{ animation-delay: 0.05s; }}
        .node:nth-child(2) {{ animation-delay: 0.1s; }}
        .node:nth-child(3) {{ animation-delay: 0.15s; }}
        .node:nth-child(4) {{ animation-delay: 0.2s; }}
        .node:nth-child(5) {{ animation-delay: 0.25s; }}
        /* Hover effects - avoid transform conflicts */
        .node {{
            transition: filter 0.2s ease, opacity 0.2s ease;
            cursor: pointer;
        }}
        .node:hover {{
            filter: brightness(1.5) drop-shadow(0 0 20px rgba(139, 92, 246, 1)) drop-shadow(0 0 40px rgba(16, 185, 129, 0.6));
        }}
        .node rect, .node circle, .node polygon, .node path {{
            transition: all 0.2s ease;
        }}
        .node:hover rect,
        .node:hover circle,
        .node:hover polygon,
        .node:hover path {{
            stroke-width: 3px !important;
        }}
        /* Enhanced edge/arrow visibility - Circuit board style */
        .edgePath path {{
            stroke: #000000 !important;
            stroke-width: 4px !important;
            stroke-linecap: square !important;
            filter: drop-shadow(0 0 2px rgba(16, 185, 129, 0.8));
            transition: all 0.2s ease;
        }}
        /* Subtle pulse effect */
        .edgePath {{
            animation: edge-pulse 4s ease-in-out infinite;
        }}
        @keyframes edge-pulse {{
            0%, 100% {{
                opacity: 0.9;
            }}
            50% {{
                opacity: 1;
            }}
        }}
        .edgePath:hover path {{
            stroke-width: 5px !important;
            filter: drop-shadow(0 0 3px rgba(139, 92, 246, 0.9));
        }}
        .edgePath marker path {{
            fill: #10b981 !important;
            filter: drop-shadow(0 0 2px rgba(16, 185, 129, 0.8));
        }}
        .edgePath:hover marker path {{
            fill: #8b5cf6 !important;
            filter: drop-shadow(0 0 3px rgba(139, 92, 246, 0.9));
        }}
        /* Loading animation */
        .loading {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
        }}
        .spinner {{
            border: 4px solid #334155;
            border-top: 4px solid #60a5fa;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 1rem;
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        .fullscreen {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            z-index: 9999;
        }}
        .fullscreen .diagram-container {{
            padding: 1rem;
        }}
    </style>
</head>
<body>
    <div class="container" id="container">
        <div class="header">
            <h1>🗺️ {title}</h1>
            <div class="controls">
                <button class="btn" onclick="zoomIn()">🔍 Zoom In</button>
                <button class="btn" onclick="zoomOut()">🔍 Zoom Out</button>
                <button class="btn" onclick="resetZoom()">↺ Reset</button>
                <button class="btn" onclick="toggleFullscreen()">⛶ Fullscreen</button>
                <button class="btn" onclick="toggleSidebar()">📁 Files</button>
                <button class="btn" onclick="downloadSVG()">💾 Download SVG</button>
                <span class="zoom-info">
                    <span>Zoom:</span>
                    <strong id="zoom-level">100%</strong>
                    <span style="margin-left: 1rem">💡 Scroll to zoom, drag to pan</span>
                </span>
                <span class="spacing-control">
                    <span>Spacing:</span>
                    <input type="range" class="spacing-slider" id="spacing-slider"
                           min="50" max="300" value="100" step="10"
                           oninput="updateSpacing(this.value)">
                    <strong id="spacing-value">100px</strong>
                </span>
            </div>
        </div>
        <div class="main-content">
            <div class="sidebar" id="sidebar">
                <h2>📁 File Explorer</h2>
                <input type="text" class="sidebar-search" id="sidebar-search" placeholder="Search files..." />
                <div id="file-tree"></div>
            </div>
            <div class="diagram-wrapper">
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>Rendering diagram...</p>
            </div>
            <div class="diagram-container" id="diagram-container">
                <div class="mermaid" id="mermaid-diagram" data-mermaid-code-b64="{mermaid_code_b64}">
                    <!-- Mermaid code will be loaded from base64 attribute by JavaScript to avoid HTML parsing issues -->
                </div>
            </div>
        </div>
        </div>
    </div>

    <!-- Node details sidebar -->
    <div class="node-details" id="node-details">
        <h2>
            <span id="node-details-title">Node Details</span>
            <button class="close-btn" onclick="closeNodeDetails()">&times;</button>
        </h2>
        <div class="node-icon" id="node-icon"></div>
        <div id="node-details-content">
            <p style="color: #64748b; text-align: center; margin-top: 2rem;">Click a node to view details</p>
        </div>
    </div>

    <script type="module">
        // Re-import mermaid for this script module (ES modules cache imports efficiently)
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';

        let scale = 1;
        let translateX = 0;
        let translateY = 0;
        let isDragging = false;
        let startX = 0;
        let startY = 0;

        const container = document.getElementById('diagram-container');
        const zoomLevelEl = document.getElementById('zoom-level');

        // Hide loading when mermaid is ready
        window.addEventListener('load', () => {{
            setTimeout(() => {{
                document.getElementById('loading').style.display = 'none';

                // Add click handlers to nodes
                document.querySelectorAll('.node').forEach(node => {{
                    node.addEventListener('click', (e) => {{
                        const label = node.querySelector('text')?.textContent;
                        if (label) {{
                            alert('Node: ' + label);
                        }}
                    }});
                }});
            }}, 500);
        }});

        function updateTransform() {{
            // Use translate3d for better performance and to avoid conflicts
            container.style.transform = `translate3d(${{translateX}}px, ${{translateY}}px, 0) scale(${{scale}})`;
            zoomLevelEl.textContent = Math.round(scale * 100) + '%';
            container.classList.toggle('zoomed', scale !== 1);
        }}

        function zoomIn() {{
            scale = Math.min(scale * 1.2, 5);
            updateTransform();
        }}

        function zoomOut() {{
            scale = Math.max(scale / 1.2, 0.1);
            updateTransform();
        }}

        function resetZoom() {{
            scale = 1;
            translateX = 0;
            translateY = 0;
            updateTransform();
        }}

        function updateSpacing(value) {{
            const spacingValue = parseInt(value);
            document.getElementById('spacing-value').textContent = spacingValue + 'px';

            // Update mermaid configuration with new spacing
            mermaid.initialize({{
                startOnLoad: false,
                theme: 'dark',
                themeVariables: {{
                    primaryColor: '#10b981',
                    primaryTextColor: '#10b981',
                    primaryBorderColor: '#10b981',
                    lineColor: '#10b981',
                    secondaryColor: '#8b5cf6',
                    tertiaryColor: '#ec4899',
                    background: '#0a0a0a',
                    mainBkg: '#0d1f1a',
                    secondBkg: '#1a1625',
                    tertiaryBkg: '#1f0a1a',
                    clusterBkg: 'rgba(16, 185, 129, 0.05)',
                    clusterBorder: '#10b981',
                    edgeLabelBackground: 'rgba(10, 10, 10, 0.8)',
                    nodeTextColor: '#10b981'
                }},
                flowchart: {{
                    useMaxWidth: false,
                    htmlLabels: true,
                    curve: 'linear',
                    nodeSpacing: spacingValue,
                    rankSpacing: spacingValue,
                    defaultRenderer: 'elk'
                }},
                elk: {{
                    mergeEdges: true,
                    nodePlacementStrategy: 'SIMPLE'
                }},
                sequence: {{
                    useMaxWidth: false,
                    wrap: true,
                    height: 600
                }},
                class: {{
                    useMaxWidth: false
                }},
                er: {{
                    useMaxWidth: false
                }},
                securityLevel: 'loose',
                logLevel: 'error',
                arrowMarkerAbsolute: true
            }});

            // Re-render the diagram with proper cleanup
            const diagramDiv = document.getElementById('mermaid-diagram');
            const mermaidCodeB64 = diagramDiv.getAttribute('data-mermaid-code-b64');

            if (mermaidCodeB64) {{
                try {{
                    // Decode base64 mermaid code
                    const mermaidCode = atob(mermaidCodeB64);

                    // Clear old diagram completely (remove SVG and all children)
                    diagramDiv.innerHTML = '';

                    // Reset to mermaid class and insert raw mermaid code
                    diagramDiv.className = 'mermaid';
                    diagramDiv.removeAttribute('data-processed');
                    diagramDiv.textContent = mermaidCode;

                    // Reset zoom/pan for new diagram
                    scale = 1;
                    translateX = 0;
                    translateY = 0;
                    updateTransform();

                    // Re-render on next tick to ensure DOM is ready
                    setTimeout(async () => {{
                        try {{
                            await mermaid.run({{
                                querySelector: '.mermaid'
                            }});
                            // Reinitialize WebGL animations after render completes
                            setTimeout(createWebGLGlows, 500);
                        }} catch (err) {{
                            console.error('Failed to re-render diagram:', err);
                        }}
                    }}, 0);
                }} catch (error) {{
                    console.error('Failed to update spacing:', error);
                }}
            }}
        }}

        // Mouse wheel zoom - zoom towards cursor
        container.addEventListener('wheel', (e) => {{
            e.preventDefault();

            // Get mouse position relative to container
            const rect = container.getBoundingClientRect();
            const mouseX = e.clientX - rect.left;
            const mouseY = e.clientY - rect.top;

            // With transform "translate(tx,ty) scale(s)", screen coords = (diagram + translate) * scale
            // So: diagram = screen / scale - translate
            // Calculate the point in diagram space that's currently under cursor
            const pointX = mouseX / scale - translateX;
            const pointY = mouseY / scale - translateY;

            // Calculate new scale
            const delta = e.deltaY > 0 ? 0.9 : 1.1;
            const newScale = Math.max(0.1, Math.min(5, scale * delta));

            // Calculate new translation to keep same diagram point under cursor
            // We want: mouseX = (pointX + new_translateX) * newScale
            // So: new_translateX = mouseX / newScale - pointX
            translateX = mouseX / newScale - pointX;
            translateY = mouseY / newScale - pointY;
            scale = newScale;

            updateTransform();
        }});

        // Drag to pan - avoid dragging when clicking nodes
        container.addEventListener('mousedown', (e) => {{
            // Don't start dragging if clicking on a node
            if (e.target.closest('.node')) {{
                return;
            }}
            isDragging = true;
            startX = e.clientX - translateX;
            startY = e.clientY - translateY;
        }});

        document.addEventListener('mousemove', (e) => {{
            if (!isDragging) return;
            translateX = e.clientX - startX;
            translateY = e.clientY - startY;
            updateTransform();
        }});

        document.addEventListener('mouseup', () => {{
            isDragging = false;
        }});

        // Fullscreen
        function toggleFullscreen() {{
            const elem = document.getElementById('container');
            if (!document.fullscreenElement) {{
                elem.requestFullscreen().catch(err => {{
                    console.log('Fullscreen error:', err);
                }});
            }} else {{
                document.exitFullscreen();
            }}
        }}

        // Download SVG
        function downloadSVG() {{
            const svg = document.querySelector('#mermaid-diagram svg');
            if (svg) {{
                const svgData = new XMLSerializer().serializeToString(svg);
                const blob = new Blob([svgData], {{ type: 'image/svg+xml' }});
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'diagram.svg';
                a.click();
                URL.revokeObjectURL(url);
            }}
        }}

        // Sidebar functionality
        function toggleSidebar() {{
            const sidebar = document.getElementById('sidebar');
            sidebar.classList.toggle('collapsed');
        }}

        // Parse mermaid content and build file tree
        function buildFileTree() {{
            try {{
                // Get mermaid content from base64 attribute to avoid template string issues
                const diagramDiv = document.getElementById('mermaid-diagram');
                const mermaidCodeB64 = diagramDiv.getAttribute('data-mermaid-code-b64');

                console.log('Base64 attribute found:', !!mermaidCodeB64);
                console.log('Base64 length:', mermaidCodeB64 ? mermaidCodeB64.length : 0);

                if (!mermaidCodeB64) {{
                    console.error('No base64 data found on mermaid-diagram element');
                    document.getElementById('file-tree').innerHTML = '<div style="color:#f59e0b;">Error: No diagram data found</div>';
                    return;
                }}

                const mermaidContent = atob(mermaidCodeB64);
                console.log('Decoded mermaid content length:', mermaidContent.length);
                console.log('Sample content:', mermaidContent.substring(0, 500));

                const nodes = new Map(); // nodeId -> {{ name, file, line }}
                const fileStructure = {{}};

                // Extract nodes from mermaid content
                // Format: N0["function()<br/>🔧 class<br/>📄 file.py<br/>📍 L10-20"]
                // Use more flexible regex that doesn't rely on emoji matching
                const nodePattern = /N(\\d+)\\["([^(]+)\\(\\)<br\\/>[^<]*<br\\/>.*?\\s+([^<]+)<br\\/>[^<]*L(\\d+)-(\\d+)"\\]/g;
                let match;
                let matchCount = 0;

                while ((match = nodePattern.exec(mermaidContent)) !== null) {{
                    matchCount++;
                    if (matchCount <= 3) {{
                        console.log(`Match ${{matchCount}}:`, match[0]);
                    }}
                    const [, nodeId, funcName, fileName, lineStart, lineEnd] = match;
                const node = {{
                    id: 'N' + nodeId,
                    name: funcName.trim(),
                    file: fileName.trim(),
                    lineStart: parseInt(lineStart),
                    lineEnd: parseInt(lineEnd)
                }};
                nodes.set(node.id, node);

                // Build file structure
                if (!fileStructure[node.file]) {{
                    fileStructure[node.file] = [];
                }}
                fileStructure[node.file].push(node);
            }}

            console.log('buildFileTree: Found', matchCount, 'nodes');
            console.log('buildFileTree: Files found:', Object.keys(fileStructure).length);

            // Build HTML tree
            const treeHTML = [];
            const sortedFiles = Object.keys(fileStructure).sort();

            if (sortedFiles.length === 0) {{
                treeHTML.push('<div class="tree-item" style="color: #f59e0b;">No files found. Check console for regex match issues.</div>');
                console.warn('No files matched. Sample mermaid content:', mermaidContent.substring(0, 500));
            }} else {{
                for (const fileName of sortedFiles) {{
                    const funcs = fileStructure[fileName];
                    treeHTML.push(`
                        <div class="tree-item tree-file" onclick="highlightFile('${{fileName}}')">
                            <span class="icon">📄</span>
                            <span>${{fileName}}</span>
                        </div>
                        <div class="tree-children">
                    `);

                    for (const func of funcs) {{
                        treeHTML.push(`
                            <div class="tree-item tree-function" data-node-id="${{func.id}}" onclick="navigateToNode('${{func.id}}')">
                                <span class="icon">⚡</span>
                                <span>${{func.name}}() :${{func.lineStart}}</span>
                            </div>
                        `);
                    }}

                    treeHTML.push('</div>');
                }}
            }}

            document.getElementById('file-tree').innerHTML = treeHTML.join('');
            }} catch (error) {{
                console.error('Error in buildFileTree:', error);
                document.getElementById('file-tree').innerHTML = '<div style="color:#ef4444;">Error building file tree. Check console for details.</div>';
            }}
        }}

        // Navigate to a specific node in the diagram
        function navigateToNode(nodeId) {{
            // Find the node in the SVG
            const svg = document.querySelector('#mermaid-diagram svg');
            if (!svg) return;

            // Mermaid v10 with ELK renderer uses IDs like "flowchart-N0-123" instead of just "N0"
            // Try exact match first, then partial match
            let nodeElement = svg.querySelector(`#${{nodeId}}`);
            if (!nodeElement) {{
                // Try finding node by partial ID match (contains our nodeId)
                nodeElement = svg.querySelector(`g.node[id*="${{nodeId}}"]`);
            }}
            if (!nodeElement) {{
                console.warn('Node not found:', nodeId);
                console.log('Available node IDs:', Array.from(svg.querySelectorAll('g.node')).map(n => n.id));
                return;
            }}

            // Get the bounding box of the node in SVG coordinate space
            const nodeBBox = nodeElement.getBBox();
            const containerRect = container.getBoundingClientRect();

            // Calculate the center of the node in SVG coordinates
            const nodeCenterX = nodeBBox.x + nodeBBox.width / 2;
            const nodeCenterY = nodeBBox.y + nodeBBox.height / 2;

            // Set scale to 1.5 for better visibility
            scale = 1.5;

            // Center the node in the viewport
            // With transform "translate(tx,ty) scale(s)": screen = (svg + translate) * scale
            // We want: viewportCenter = (nodeCenter + translate) * scale
            // So: translate = viewportCenter / scale - nodeCenter
            const viewportCenterX = containerRect.width / 2;
            const viewportCenterY = containerRect.height / 2;

            translateX = viewportCenterX / scale - nodeCenterX;
            translateY = viewportCenterY / scale - nodeCenterY;

            updateTransform();

            // Highlight the node temporarily
            nodeElement.classList.add('highlighted');
            setTimeout(() => nodeElement.classList.remove('highlighted'), 2000);

            // Update active state in sidebar
            document.querySelectorAll('.tree-item').forEach(el => el.classList.remove('active'));
            const sidebarItem = document.querySelector(`[data-node-id="${{nodeId}}"]`);
            if (sidebarItem) sidebarItem.classList.add('active');
        }}

        function highlightFile(fileName) {{
            // Highlight all nodes from this file
            const items = document.querySelectorAll(`[data-node-id]`);
            const svg = document.querySelector('#mermaid-diagram svg');

            items.forEach(item => {{
                const nodeId = item.getAttribute('data-node-id');
                // Try exact match first, then partial match
                let nodeElement = svg.querySelector(`#${{nodeId}}`);
                if (!nodeElement) {{
                    nodeElement = svg.querySelector(`g.node[id*="${{nodeId}}"]`);
                }}
                if (nodeElement && item.textContent.includes(fileName)) {{
                    nodeElement.classList.add('highlighted');
                    setTimeout(() => nodeElement.classList.remove('highlighted'), 2000);
                }}
            }});
        }}

        // Search functionality
        document.getElementById('sidebar-search').addEventListener('input', (e) => {{
            const searchTerm = e.target.value.toLowerCase();
            const treeItems = document.querySelectorAll('.tree-item');

            treeItems.forEach(item => {{
                const text = item.textContent.toLowerCase();
                if (text.includes(searchTerm)) {{
                    item.style.display = 'flex';
                }} else {{
                    item.style.display = 'none';
                }}
            }});
        }});

        // Enhanced pulse effects with fading trails
        function createPulseEffects() {{
            const svg = document.querySelector('#mermaid-diagram svg');
            if (!svg) return;

            // Create a defs section for gradients
            let defs = svg.querySelector('defs');
            if (!defs) {{
                defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
                svg.insertBefore(defs, svg.firstChild);
            }}

            // Add larger radial gradient for pulse
            const gradient = document.createElementNS('http://www.w3.org/2000/svg', 'radialGradient');
            gradient.setAttribute('id', 'pulse-gradient');
            gradient.innerHTML = `
                <stop offset="0%" style="stop-color:#10b981;stop-opacity:1" />
                <stop offset="50%" style="stop-color:#10b981;stop-opacity:0.6" />
                <stop offset="100%" style="stop-color:#10b981;stop-opacity:0" />
            `;
            defs.appendChild(gradient);

            // Only animate selected edges for performance
            const edgePaths = svg.querySelectorAll('.edgePath path');
            const maxPulses = Math.min(10, Math.floor(edgePaths.length / 5));

            for (let i = 0; i < maxPulses; i++) {{
                const index = i * Math.floor(edgePaths.length / maxPulses);
                const path = edgePaths[index];
                if (!path) continue;

                const pathLength = path.getTotalLength();
                const trailLength = 8; // Number of trail segments
                const trail = [];

                // Create trail segments
                for (let j = 0; j < trailLength; j++) {{
                    const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                    const opacity = 1 - (j / trailLength); // Fade out progressively
                    const radius = 6 - (j * 0.5); // Get smaller progressively

                    circle.setAttribute('r', radius);
                    circle.setAttribute('fill', 'url(#pulse-gradient)');
                    circle.setAttribute('opacity', opacity);
                    circle.style.filter = 'blur(1px)';

                    path.parentNode.appendChild(circle);
                    trail.push(circle);
                }}

                let distance = (i * 150) % pathLength;
                let lastTime = performance.now();

                function animatePulse(currentTime) {{
                    const deltaTime = currentTime - lastTime;

                    // 60fps cap
                    if (deltaTime < 16) {{
                        requestAnimationFrame(animatePulse);
                        return;
                    }}

                    lastTime = currentTime;
                    distance += 3; // Moderate speed

                    if (distance > pathLength) {{
                        distance = 0;
                    }}

                    // Update each trail segment
                    for (let j = 0; j < trailLength; j++) {{
                        const segmentDistance = distance - (j * 15); // Space segments out
                        let actualDistance = segmentDistance;

                        if (actualDistance < 0) {{
                            actualDistance = pathLength + actualDistance;
                        }}

                        const point = path.getPointAtLength(actualDistance % pathLength);
                        trail[j].setAttribute('cx', point.x);
                        trail[j].setAttribute('cy', point.y);
                    }}

                    requestAnimationFrame(animatePulse);
                }}

                requestAnimationFrame(animatePulse);
            }}
        }}

        // WebGL-accelerated glow particles for high-performance rendering
        function createWebGLGlows() {{
            const svg = document.querySelector('#mermaid-diagram svg');
            if (!svg) {{
                console.warn('SVG not found, retrying WebGL initialization...');
                setTimeout(createWebGLGlows, 200);
                return;
            }}

            // Wait for paths to be fully rendered - check multiple times
            const edgePathCount = svg.querySelectorAll('.edgePath path').length;

            // Store last count to detect when rendering stabilizes
            if (!createWebGLGlows.lastPathCount) {{
                createWebGLGlows.lastPathCount = 0;
                createWebGLGlows.retryCount = 0;
            }}

            createWebGLGlows.retryCount++;

            // Wait longer if paths are still being added
            // Need to see same count at least 3 times before considering it stable
            if (!createWebGLGlows.stableCount) createWebGLGlows.stableCount = 0;

            if (edgePathCount !== createWebGLGlows.lastPathCount) {{
                console.log('WebGL: Found', edgePathCount, 'paths (was', createWebGLGlows.lastPathCount, '), waiting for rendering to stabilize...');
                createWebGLGlows.lastPathCount = edgePathCount;
                createWebGLGlows.stableCount = 0; // Reset stability counter
                setTimeout(createWebGLGlows, 500);
                return;
            }} else {{
                createWebGLGlows.stableCount++;
                if (createWebGLGlows.stableCount < 3 && createWebGLGlows.retryCount < 30) {{
                    console.log('WebGL: Path count stable at', edgePathCount, '(check', createWebGLGlows.stableCount, 'of 3)');
                    setTimeout(createWebGLGlows, 500);
                    return;
                }}
            }}

            console.log('WebGL: Initializing with', edgePathCount, 'edge paths after', createWebGLGlows.retryCount, 'checks');

            // Create canvas overlay - position it relative to SVG, not container
            const canvas = document.createElement('canvas');
            canvas.style.position = 'absolute';
            canvas.style.top = '0';
            canvas.style.left = '0';
            canvas.style.width = '100%';
            canvas.style.height = '100%';
            canvas.style.pointerEvents = 'none';
            canvas.style.zIndex = '100';  // Higher z-index to ensure visibility

            // Append canvas as sibling to SVG inside mermaid-diagram div
            // This way canvas and SVG are both transformed together
            const mermaidDiagram = document.getElementById('mermaid-diagram');
            mermaidDiagram.appendChild(canvas);
            console.log('WebGL canvas created');

            // Setup WebGL context
            const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
            if (!gl) {{
                console.warn('WebGL not supported, falling back to SVG animations');
                return;
            }}

            // Vertex shader - loaded from external file
            const vertexShaderSource = `{vertex_shader}`;

            // Fragment shader - loaded from external file
            const fragmentShaderSource = `{fragment_shader}`;

            // Compile shaders
            function compileShader(source, type) {{
                const shader = gl.createShader(type);
                gl.shaderSource(shader, source);
                gl.compileShader(shader);
                if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {{
                    console.error('Shader compile error:', gl.getShaderInfoLog(shader));
                    return null;
                }}
                return shader;
            }}

            const vertexShader = compileShader(vertexShaderSource, gl.VERTEX_SHADER);
            const fragmentShader = compileShader(fragmentShaderSource, gl.FRAGMENT_SHADER);

            // Create program
            const program = gl.createProgram();
            gl.attachShader(program, vertexShader);
            gl.attachShader(program, fragmentShader);
            gl.linkProgram(program);

            if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {{
                console.error('Program link error:', gl.getProgramInfoLog(program));
                return;
            }}

            gl.useProgram(program);

            // Get attribute/uniform locations
            const positionLoc = gl.getAttribLocation(program, 'a_position');
            const texCoordLoc = gl.getAttribLocation(program, 'a_texCoord');
            const perpCoordLoc = gl.getAttribLocation(program, 'a_perpCoord');
            const normalLoc = gl.getAttribLocation(program, 'a_normal');
            const resolutionLoc = gl.getUniformLocation(program, 'u_resolution');
            const transformLoc = gl.getUniformLocation(program, 'u_transform');
            const timeLoc = gl.getUniformLocation(program, 'u_time');
            const lineWidthLoc = gl.getUniformLocation(program, 'u_lineWidth');

            // Extract path data from SVG
            const edgePaths = svg.querySelectorAll('.edgePath path');
            const pathData = [];

            console.log('WebGL: Found', edgePaths.length, 'edge paths');

            edgePaths.forEach((path, idx) => {{
                // With WebGL we can animate ALL paths without performance issues
                const length = path.getTotalLength();
                const points = [];
                const step = Math.max(1, Math.floor(length / 50)); // Sample ~50 points

                for (let i = 0; i <= length; i += step) {{
                    const pt = path.getPointAtLength(i);
                    // Use raw points - they're already in SVG coordinate space
                    points.push([pt.x, pt.y]);
                }}

                // Debug first path
                if (idx === 0) {{
                    console.log('WebGL: First path points (first 3):', points.slice(0, 3));
                }}

                pathData.push({{
                    points,
                    length,
                    progress: Math.random() // Start at random position
                }});
            }});

            console.log('WebGL: Created', pathData.length, 'animated paths');

            // Debug: Calculate bounding box of ALL path points
            let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
            pathData.forEach(path => {{
                path.points.forEach(([x, y]) => {{
                    minX = Math.min(minX, x);
                    minY = Math.min(minY, y);
                    maxX = Math.max(maxX, x);
                    maxY = Math.max(maxY, y);
                }});
            }});
            console.log('WebGL: Path points bounding box:', {{
                min: [minX, minY],
                max: [maxX, maxY],
                width: maxX - minX,
                height: maxY - minY
            }});
            console.log('WebGL: SVG viewBox:', {{
                x: svg.viewBox.baseVal.x,
                y: svg.viewBox.baseVal.y,
                width: svg.viewBox.baseVal.width,
                height: svg.viewBox.baseVal.height
            }});

            // Build vertex data for thick lines using triangle strips
            const lineVertices = [];
            const lineTexCoords = [];
            const linePerpCoords = [];
            const lineNormals = [];
            const lineSegments = []; // Track where each path starts/ends

            pathData.forEach(path => {{
                const points = path.points;
                const startIdx = lineVertices.length / 2;

                // For each segment in the path
                for (let i = 0; i < points.length; i++) {{
                    const curr = points[i];
                    const texCoord = i / (points.length - 1);

                    // Calculate normal direction (perpendicular to line direction)
                    let normal = [0, 0];
                    if (i < points.length - 1) {{
                        // Forward direction
                        const next = points[i + 1];
                        const dx = next[0] - curr[0];
                        const dy = next[1] - curr[1];
                        const len = Math.sqrt(dx * dx + dy * dy);
                        if (len > 0) {{
                            // Perpendicular: rotate by 90° (swap and negate one component)
                            normal = [-dy / len, dx / len];
                        }}
                    }} else if (i > 0) {{
                        // Use previous segment's direction for last point
                        const prev = points[i - 1];
                        const dx = curr[0] - prev[0];
                        const dy = curr[1] - prev[1];
                        const len = Math.sqrt(dx * dx + dy * dy);
                        if (len > 0) {{
                            normal = [-dy / len, dx / len];
                        }}
                    }}

                    // Create two vertices for this point (top and bottom of line)
                    // Triangle strip order: alternate between -1 and +1 perp coords
                    // Vertex 1: perpCoord = -1 (one side)
                    lineVertices.push(curr[0], curr[1]);
                    lineTexCoords.push(texCoord);
                    linePerpCoords.push(-1.0);
                    lineNormals.push(normal[0], normal[1]);

                    // Vertex 2: perpCoord = +1 (other side)
                    lineVertices.push(curr[0], curr[1]);
                    lineTexCoords.push(texCoord);
                    linePerpCoords.push(1.0);
                    lineNormals.push(normal[0], normal[1]);
                }}

                const endIdx = lineVertices.length / 2;
                lineSegments.push({{ start: startIdx, count: endIdx - startIdx }});
            }});

            const positions = new Float32Array(lineVertices);
            const texCoords = new Float32Array(lineTexCoords);
            const perpCoords = new Float32Array(linePerpCoords);
            const normals = new Float32Array(lineNormals);

            // Create buffers
            const positionBuffer = gl.createBuffer();
            const texCoordBuffer = gl.createBuffer();
            const perpCoordBuffer = gl.createBuffer();
            const normalBuffer = gl.createBuffer();

            // Upload static geometry to GPU
            gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);
            gl.bufferData(gl.ARRAY_BUFFER, positions, gl.STATIC_DRAW);

            gl.bindBuffer(gl.ARRAY_BUFFER, texCoordBuffer);
            gl.bufferData(gl.ARRAY_BUFFER, texCoords, gl.STATIC_DRAW);

            gl.bindBuffer(gl.ARRAY_BUFFER, perpCoordBuffer);
            gl.bufferData(gl.ARRAY_BUFFER, perpCoords, gl.STATIC_DRAW);

            gl.bindBuffer(gl.ARRAY_BUFFER, normalBuffer);
            gl.bufferData(gl.ARRAY_BUFFER, normals, gl.STATIC_DRAW);

            // Resize canvas to match SVG dimensions (not CSS-transformed container)
            function resizeCanvas() {{
                // Use SVG's actual dimensions, not the CSS-transformed container size
                const viewBox = svg.viewBox.baseVal;
                const svgWidth = viewBox.width || svg.width.baseVal.value;
                const svgHeight = viewBox.height || svg.height.baseVal.value;

                // Set canvas to reasonable size based on SVG aspect ratio
                // Use fixed width and calculate height to maintain aspect ratio
                const targetWidth = 2000; // Fixed reference width
                const aspectRatio = svgHeight / svgWidth;
                canvas.width = targetWidth;
                canvas.height = Math.round(targetWidth * aspectRatio);

                gl.viewport(0, 0, canvas.width, canvas.height);
            }}
            resizeCanvas();
            window.addEventListener('resize', resizeCanvas);

            console.log('WebGL: Starting fire channel animation with', lineSegments.length, 'paths');
            console.log('WebGL: Total vertices:', positions.length / 2);
            console.log('WebGL: Triangle strip vertices (2 per point)');

            let frameCount = 0;
            // Animation loop
            function animate() {{
                resizeCanvas();
                frameCount++;
                // Clear with transparent background
                gl.clearColor(0, 0, 0, 0);
                gl.clear(gl.COLOR_BUFFER_BIT);
                gl.enable(gl.BLEND);
                gl.blendFunc(gl.SRC_ALPHA, gl.ONE);  // Additive blending for fire glow

                // Bind all vertex attributes
                gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);
                gl.enableVertexAttribArray(positionLoc);
                gl.vertexAttribPointer(positionLoc, 2, gl.FLOAT, false, 0, 0);

                gl.bindBuffer(gl.ARRAY_BUFFER, texCoordBuffer);
                gl.enableVertexAttribArray(texCoordLoc);
                gl.vertexAttribPointer(texCoordLoc, 1, gl.FLOAT, false, 0, 0);

                gl.bindBuffer(gl.ARRAY_BUFFER, perpCoordBuffer);
                gl.enableVertexAttribArray(perpCoordLoc);
                gl.vertexAttribPointer(perpCoordLoc, 1, gl.FLOAT, false, 0, 0);

                gl.bindBuffer(gl.ARRAY_BUFFER, normalBuffer);
                gl.enableVertexAttribArray(normalLoc);
                gl.vertexAttribPointer(normalLoc, 2, gl.FLOAT, false, 0, 0);

                // Set uniforms
                gl.uniform2f(resolutionLoc, canvas.width, canvas.height);
                gl.uniform1f(timeLoc, performance.now() * 0.001); // Time in seconds
                gl.uniform1f(lineWidthLoc, 5.0); // Line width in pixels

                // Get SVG viewBox for proper coordinate transformation
                const viewBox = svg.viewBox.baseVal;
                const svgWidth = viewBox.width || svg.width.baseVal.value;
                const svgHeight = viewBox.height || svg.height.baseVal.value;
                const svgX = viewBox.x || 0;  // ViewBox X offset
                const svgY = viewBox.y || 0;  // ViewBox Y offset

                // Calculate transform from SVG coordinates to canvas pixels
                // Only convert coordinate systems - CSS transform handles pan/zoom
                const scaleX = canvas.width / svgWidth;
                const scaleY = canvas.height / svgHeight;

                // Transform matrix: translate by viewBox offset, then scale
                // (CSS transform on canvas element handles pan/zoom to avoid double transformation)
                const transform = [
                    scaleX, 0, 0,
                    0, scaleY, 0,
                    -svgX * scaleX, -svgY * scaleY, 1
                ];
                gl.uniformMatrix3fv(transformLoc, false, transform);

                // Debug logging on first frame
                if (frameCount === 1) {{
                    console.log('WebGL: First frame rendering fire channels');
                    console.log('WebGL: Canvas size:', canvas.width, 'x', canvas.height);
                    console.log('WebGL: SVG viewBox:', svgX, svgY, svgWidth, 'x', svgHeight);
                    console.log('WebGL: Transform scale:', scaleX, 'x', scaleY);
                    console.log('WebGL: Transform matrix:', transform);
                    console.log('WebGL: Rendering', lineSegments.length, 'fire channels');
                }}

                // Draw each path as a TRIANGLE_STRIP with flowing fire texture
                lineSegments.forEach(segment => {{
                    gl.drawArrays(gl.TRIANGLE_STRIP, segment.start, segment.count);
                }});

                // Check for WebGL errors on first frame
                if (frameCount === 1) {{
                    const err = gl.getError();
                    if (err !== gl.NO_ERROR) {{
                        console.error('WebGL error after first draw:', err);
                    }} else {{
                        console.log('WebGL: First draw completed without errors');
                    }}
                }}

                requestAnimationFrame(animate);
            }}

            animate();
        }}

        // Auto-fit diagram to viewport on load
        function autoFitDiagram() {{
            const svg = document.querySelector('#mermaid-diagram svg');
            if (!svg) {{
                setTimeout(autoFitDiagram, 100);
                return;
            }}

            const svgBBox = svg.getBBox();
            const containerRect = container.getBoundingClientRect();

            // Add padding to container size
            const paddingPercent = 0.05; // 5% padding
            const availableWidth = containerRect.width * (1 - paddingPercent * 2);
            const availableHeight = containerRect.height * (1 - paddingPercent * 2);

            // Calculate scale to fit entire diagram
            const scaleX = availableWidth / svgBBox.width;
            const scaleY = availableHeight / svgBBox.height;
            scale = Math.min(scaleX, scaleY, 1);

            // Center the diagram accounting for bounding box offset
            const scaledWidth = svgBBox.width * scale;
            const scaledHeight = svgBBox.height * scale;

            // Calculate centering: center of viewport - center of scaled content
            translateX = (containerRect.width - scaledWidth) / 2 / scale - svgBBox.x;
            translateY = (containerRect.height - scaledHeight) / 2 / scale - svgBBox.y;

            updateTransform();
        }}

        // Load mermaid content from base64 to avoid HTML parsing issues
        function loadMermaidContent() {{
            const diagramDiv = document.getElementById('mermaid-diagram');
            const mermaidCodeB64 = diagramDiv.getAttribute('data-mermaid-code-b64');

            if (!mermaidCodeB64) {{
                console.error('No base64 mermaid content found');
                return false;
            }}

            try {{
                // Decode base64 to bytes, then UTF-8 decode for proper emoji support
                const base64Bytes = atob(mermaidCodeB64);
                // Convert binary string to UTF-8 using TextDecoder
                const bytes = new Uint8Array(base64Bytes.length);
                for (let i = 0; i < base64Bytes.length; i++) {{
                    bytes[i] = base64Bytes.charCodeAt(i);
                }}
                const mermaidCode = new TextDecoder('utf-8').decode(bytes);
                diagramDiv.textContent = mermaidCode;
                console.log('Loaded mermaid content:', mermaidCode.length, 'characters');
                return true;
            }} catch (error) {{
                console.error('Failed to decode mermaid content:', error);
                return false;
            }}
        }}

        // Initialize when DOM is ready
        document.addEventListener('DOMContentLoaded', async () => {{
            console.log('DOM ready, initializing diagram...');

            // Load content and render diagram
            if (loadMermaidContent()) {{
                try {{
                    // Use mermaid.run() for v10 API - it finds and renders all .mermaid elements
                    await mermaid.run({{
                        querySelector: '.mermaid'
                    }});
                    console.log('Mermaid diagram rendered successfully');

                    // Build tree and effects after diagram is rendered
                    setTimeout(() => {{
                        buildFileTree();
                        createWebGLGlows(); // GPU-accelerated particle effects
                        // Don't auto-fit - it causes off-screen positioning
                        // User can press Reset (0 key) to fit if needed
                    }}, 500);
                }} catch (error) {{
                    console.error('Failed to render mermaid diagram:', error);
                    // Try fallback rendering
                    setTimeout(() => {{
                        buildFileTree();
                        createWebGLGlows(); // GPU-accelerated fallback
                    }}, 1000);
                }}
            }} else {{
                console.error('Failed to load mermaid content');
            }}
        }});

        // Global function to refresh WebGL particles (callable from console or keyboard)
        window.refreshWebGLParticles = function() {{
            console.log('Refreshing WebGL particles...');
            // Remove existing canvas
            const existingCanvas = document.querySelector('#mermaid-diagram canvas');
            if (existingCanvas) {{
                existingCanvas.remove();
            }}
            // Reset retry counters
            createWebGLGlows.lastPathCount = 0;
            createWebGLGlows.retryCount = 0;
            createWebGLGlows.stableCount = 0;
            // Reinitialize
            createWebGLGlows();
        }};

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {{
            if (e.key === '+' || e.key === '=') zoomIn();
            if (e.key === '-' || e.key === '_') zoomOut();
            if (e.key === '0') resetZoom();
            if (e.key === 'f' || e.key === 'F') toggleFullscreen();
            if (e.key === 'r' || e.key === 'R') window.refreshWebGLParticles(); // R to refresh particles
            if (e.key === 'b' || e.key === 'B') toggleSidebar();
        }});

        // Node details sidebar functions
        function showNodeDetails(nodeElement) {{
            const detailsPanel = document.getElementById('node-details');
            const contentDiv = document.getElementById('node-details-content');
            const iconDiv = document.getElementById('node-icon');
            const titleSpan = document.getElementById('node-details-title');

            // Extract node information from the Mermaid node
            const nodeText = nodeElement.querySelector('.nodeLabel')?.textContent || '';
            const nodeId = nodeElement.id || '';

            // Parse node text (format: "FunctionName()<br/>📦 module<br/>📄 file.py<br/>📍 L123-456")
            const lines = nodeText.split('\\n').map(l => l.trim()).filter(l => l);

            let nodeName = lines[0] || 'Unknown';
            let module = '';
            let file = '';
            let lineRange = '';
            let icon = '📦';

            // Parse each line
            lines.forEach(line => {{
                if (line.includes('📦')) module = line.replace('📦', '').trim();
                if (line.includes('📄')) file = line.replace('📄', '').trim();
                if (line.includes('📍')) lineRange = line.replace('📍', '').trim();
                if (line.includes('()')) icon = '🔧'; // Function
                if (line.includes('class ')) icon = '🏛️'; // Class
            }});

            // Update sidebar content
            titleSpan.textContent = 'Node Details';
            iconDiv.textContent = icon;

            contentDiv.innerHTML = `
                <div class="detail-section">
                    <div class="detail-label">Name</div>
                    <div class="detail-value">${{nodeName}}</div>
                </div>
                ${{module ? `
                <div class="detail-section">
                    <div class="detail-label">Module</div>
                    <div class="detail-value">${{module}}</div>
                </div>
                ` : ''}}
                ${{file ? `
                <div class="detail-section">
                    <div class="detail-label">File</div>
                    <div class="detail-value">${{file}}</div>
                </div>
                ` : ''}}
                ${{lineRange ? `
                <div class="detail-section">
                    <div class="detail-label">Lines</div>
                    <div class="detail-value">${{lineRange}}</div>
                </div>
                ` : ''}}
                <div class="detail-section">
                    <div class="detail-label">Node ID</div>
                    <div class="detail-value">${{nodeId}}</div>
                </div>
            `;

            // Show the panel
            detailsPanel.classList.add('visible');
        }}

        function closeNodeDetails() {{
            const detailsPanel = document.getElementById('node-details');
            detailsPanel.classList.remove('visible');
        }}

        function setupNodeClickHandlers() {{
            // Wait for diagram to be fully rendered
            setTimeout(() => {{
                const nodes = document.querySelectorAll('.node');
                nodes.forEach(node => {{
                    node.style.cursor = 'pointer';
                    node.addEventListener('click', (e) => {{
                        e.stopPropagation();
                        showNodeDetails(node);
                    }});
                }});
                console.log('Node click handlers set up for', nodes.length, 'nodes');
            }}, 1000);
        }}

        // Call setup after diagram is rendered
        setupNodeClickHandlers();

        // Make functions globally accessible for inline onclick handlers
        window.navigateToNode = navigateToNode;
        window.highlightFile = highlightFile;
        window.toggleSidebar = toggleSidebar;
        window.toggleFullscreen = toggleFullscreen;
        window.zoomIn = zoomIn;
        window.zoomOut = zoomOut;
        window.resetZoom = resetZoom;
        window.updateSpacing = updateSpacing;
        window.closeNodeDetails = closeNodeDetails;
        window.downloadSVG = downloadSVG;
    </script>
</body>
</html>'''

    try:
        # Encode mermaid code in base64 to avoid HTML escaping issues
        mermaid_code_b64 = base64.b64encode(mermaid_content.encode('utf-8')).decode('ascii')
        html_content = html_template.format(
            title=title,
            mermaid_code_b64=mermaid_code_b64
        )

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        if use_color:
            print(colorize(f"[SUCCESS] Interactive HTML: {output_file}", TextColor.GREEN))
        else:
            print(f"[SUCCESS] Interactive HTML: {output_file}")

        return True

    except Exception as e:
        if use_color:
            print(colorize(f"[ERROR] Failed to generate HTML: {e}", TextColor.RED), file=sys.stderr)
        else:
            print(f"[ERROR] Failed to generate HTML: {e}", file=sys.stderr)
        return False
