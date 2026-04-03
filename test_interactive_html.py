"""Test script for interactive HTML export functionality."""

from clickup_framework.commands.map_helpers.mermaid_export import export_mermaid_to_interactive_html

# Test with a simple flowchart
test_diagram = """graph TD
    A[Start] --> B{Decision}
    B -->|Yes| C[Process 1]
    B -->|No| D[Process 2]
    C --> E[End]
    D --> E

    style A fill:#4CAF50,stroke:#2E7D32,color:#fff
    style E fill:#F44336,stroke:#C62828,color:#fff
    style B fill:#FF9800,stroke:#E65100,color:#fff
"""

print("Testing interactive HTML export...")
print("-" * 50)

# Test 1: Dark theme
result1 = export_mermaid_to_interactive_html(
    mermaid_content=test_diagram,
    output_file="test_interactive_dark.html",
    title="Test Flowchart (Dark)",
    theme="dark",
    use_color=True
)

if result1:
    print("[PASS] Test 1: Dark theme HTML created")
else:
    print("[FAIL] Test 1 failed")

# Test 2: Light theme
result2 = export_mermaid_to_interactive_html(
    mermaid_content=test_diagram,
    output_file="test_interactive_light.html",
    title="Test Flowchart (Light)",
    theme="light",
    use_color=True
)

if result2:
    print("[PASS] Test 2: Light theme HTML created")
else:
    print("[FAIL] Test 2 failed")

print("-" * 50)
print("\nTest complete! Open the HTML files in a browser to verify:")
print("  - test_interactive_dark.html")
print("  - test_interactive_light.html")
print("\nFeatures to test:")
print("  - Pan: Click and drag the diagram")
print("  - Zoom: Mouse wheel or +/- buttons")
print("  - Search: Type in search box (e.g., 'Process')")
print("  - Theme: Click 'Toggle Theme' button")
print("  - Fit: Click fit button to fit diagram to screen")
print("  - Keyboard: Ctrl+/-, Ctrl+0, Ctrl+F, Esc")
