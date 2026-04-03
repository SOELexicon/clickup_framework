"""Test HTML export integration with generator classes."""

from clickup_framework.commands.map_helpers.mermaid.generators import PieChartGenerator

# Sample stats for testing
test_stats = {
    'total_symbols': 150,
    'files_analyzed': 10,
    'by_language': {
        'Python': {'function': 50, 'class': 20},
        'JavaScript': {'function': 40, 'class': 15},
        'TypeScript': {'function': 25, 'class': 10}
    }
}

print("Testing BaseGenerator HTML export integration...")
print("-" * 50)

# Test 1: Generate markdown and export to HTML
print("\nTest 1: PieChartGenerator with HTML export")
generator = PieChartGenerator(test_stats, 'test_pie_generator.md', theme='dark')

# Generate markdown
print("  - Generating markdown diagram...")
result = generator.generate()
print(f"  - Markdown created: {result}")

# Export to HTML
print("  - Exporting to interactive HTML...")
html_result = generator.export_html(use_color=True)

if html_result:
    print("  [PASS] HTML export successful")
else:
    print("  [FAIL] HTML export failed")

# Test 2: Export with custom filename
print("\nTest 2: Custom HTML filename")
html_result2 = generator.export_html('custom_pie_chart.html', use_color=True)

if html_result2:
    print("  [PASS] Custom HTML export successful")
else:
    print("  [FAIL] Custom HTML export failed")

print("\n" + "-" * 50)
print("\nTest complete! Check the following files:")
print("  - test_pie_generator.md (markdown)")
print("  - test_pie_generator.html (default HTML export)")
print("  - custom_pie_chart.html (custom HTML export)")
