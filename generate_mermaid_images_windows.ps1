# PowerShell Script to Pre-Generate Mermaid Images
# This script generates all Mermaid diagrams in mermaid_doc_content.md
# and caches them so they can be uploaded to ClickUp

param(
    [string]$ContentFile = "mermaid_doc_content.md",
    [string]$CacheDir = "$env:USERPROFILE\.clickup_framework\image_cache"
)

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host " Mermaid Image Generator for Windows" -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if mmdc is installed
Write-Host "Checking for Mermaid CLI (mmdc)..." -ForegroundColor Yellow
try {
    $mmdc_version = mmdc --version 2>$null
    Write-Host "✓ Mermaid CLI found: $mmdc_version" -ForegroundColor Green
} catch {
    Write-Host "✗ Mermaid CLI (mmdc) not found" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install it with:" -ForegroundColor Yellow
    Write-Host "  npm install -g @mermaid-js/mermaid-cli" -ForegroundColor White
    Write-Host ""
    exit 1
}

# Check if content file exists
if (-not (Test-Path $ContentFile)) {
    Write-Host "✗ Content file not found: $ContentFile" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Content file found: $ContentFile" -ForegroundColor Green
Write-Host ""

# Create cache directory
if (-not (Test-Path $CacheDir)) {
    New-Item -ItemType Directory -Path $CacheDir -Force | Out-Null
    Write-Host "✓ Created cache directory: $CacheDir" -ForegroundColor Green
} else {
    Write-Host "✓ Cache directory exists: $CacheDir" -ForegroundColor Green
}

Write-Host ""
Write-Host "Generating Mermaid images..." -ForegroundColor Yellow
Write-Host ""

# Run Python script to generate images
python -c @"
import sys
import os
import re
import hashlib
import tempfile
import subprocess
import json
from pathlib import Path

def compute_hash(content):
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def extract_mermaid_blocks(content):
    blocks = []
    lines = content.split('\n')
    in_block = False
    current_block = []

    for line in lines:
        if re.match(r'^\`\`\`mermaid\s*$', line.strip(), re.IGNORECASE):
            in_block = True
            current_block = []
            continue

        if in_block and re.match(r'^\`\`\`\s*$', line.strip()):
            if current_block:
                block_content = '\n'.join(current_block)
                if not block_content.strip().startswith('#ignore'):
                    blocks.append(block_content)
            in_block = False
            current_block = []
            continue

        if in_block:
            current_block.append(line)

    return blocks

# Read content file
content_file = r'$ContentFile'
cache_dir = r'$CacheDir'

with open(content_file, 'r', encoding='utf-8') as f:
    content = f.read()

blocks = extract_mermaid_blocks(content)
print(f'Found {len(blocks)} Mermaid diagram(s)\n')

# Generate each image
success_count = 0
error_count = 0
metadata = {}

for i, block in enumerate(blocks, 1):
    block_hash = compute_hash(block)
    output_file = os.path.join(cache_dir, f'{block_hash}.png')

    # Skip if already exists
    if os.path.exists(output_file):
        print(f'  [{i}/{len(blocks)}] Skipping (already cached): {block_hash[:8]}...')
        success_count += 1
        continue

    print(f'  [{i}/{len(blocks)}] Generating: {block_hash[:8]}...', end=' ')

    # Create temp file for mermaid code
    with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False, encoding='utf-8') as tmp:
        tmp.write(block)
        tmp_file = tmp.name

    try:
        # Run mmdc to generate image
        result = subprocess.run(
            ['mmdc', '-i', tmp_file, '-o', output_file, '-b', 'transparent', '-t', 'dark'],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0 and os.path.exists(output_file):
            size = os.path.getsize(output_file)
            print(f'✓ ({size:,} bytes)')
            success_count += 1

            # Add to metadata
            metadata[block_hash] = {
                'filename': f'mermaid_{block_hash[:8]}.png',
                'extension': '.png',
                'size': size,
                'cached_path': output_file,
                'uploaded': False,
                'upload_url': None,
                'source': 'mermaid'
            }
        else:
            print(f'✗ Failed')
            if result.stderr:
                print(f'      Error: {result.stderr[:100]}')
            error_count += 1
    except subprocess.TimeoutExpired:
        print(f'✗ Timeout')
        error_count += 1
    except Exception as e:
        print(f'✗ Error: {str(e)[:50]}')
        error_count += 1
    finally:
        try:
            os.unlink(tmp_file)
        except:
            pass

# Save metadata
metadata_file = os.path.join(cache_dir, 'metadata.json')
if os.path.exists(metadata_file):
    with open(metadata_file, 'r') as f:
        existing_metadata = json.load(f)
    existing_metadata.update(metadata)
    metadata = existing_metadata

with open(metadata_file, 'w') as f:
    json.dump(metadata, f, indent=2)

print('')
print('=' * 66)
print(f'Generation complete!')
print(f'  Success: {success_count}')
print(f'  Errors:  {error_count}')
print(f'  Cache:   {cache_dir}')
print('=' * 66)
print('')

if success_count > 0:
    print('✓ Images cached successfully!')
    print('')
    print('Now you can upload with:')
    print('  cum ca 86c6j3pkb --comment-file mermaid_doc_content.md --upload-images')
else:
    print('✗ No images were generated. Check errors above.')
    sys.exit(1)
"@

Write-Host ""
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host " Done!" -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan
