# Mermaid Diagram Generation Tests

This folder contains tests for generating mermaid diagrams from markdown documents.

## Files

- `test_document.md` - Source markdown document with 6 different mermaid diagram types:
  - Flowchart
  - Sequence Diagram
  - Gantt Chart
  - Class Diagram
  - State Diagram
  - Pie Chart

- `test_document_processed.md` - Processed output with image placeholders ({{image:hash}})
- `test_document_with_images.md` - Alternative processed output
- `test_generation.py` - Test script using ContentProcessor
- `test_direct_generation.py` - Test script using MermaidParser directly

## Test Results

### Test 1: ContentProcessor Test
- **Status**: ✅ Success
- **Mermaid blocks detected**: 6
- **Image placeholders added**: 6
- **Images generated**: 0 (images not actually generated, only placeholders)

### Test 2: Direct MermaidParser Test
- **Status**: ✅ Success
- **Mermaid CLI available**: Yes
- **Image references found**: 6
- **Images in cache**: 0 (images not actually generated)

## Notes

The tests successfully:
1. ✅ Detect mermaid code blocks in markdown
2. ✅ Generate hash-based image references
3. ✅ Embed image placeholders above code blocks
4. ✅ Process multiple diagram types

However, the actual image generation appears to require additional configuration or the images are generated on-demand when needed (e.g., when uploading to ClickUp).

## Usage

Run the tests:
```bash
python mdmermaidtests/test_generation.py
python mdmermaidtests/test_direct_generation.py
```

## Next Steps

To actually generate PNG images, you may need to:
1. Ensure mermaid-cli is properly installed and configured
2. Check if images are generated on-demand during upload
3. Verify the cache directory permissions
4. Check if additional options are needed for image generation

