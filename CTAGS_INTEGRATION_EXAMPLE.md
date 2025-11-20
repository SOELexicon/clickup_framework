# ctags Integration Example: Full Workflow

Complete working example integrating ctags with ClickUp automation, CI/CD, and your existing tools.

---

## Scenario: Document Multi-Language Codebase

You have a Python + C# + JavaScript project. Want to:
1. Generate live code maps
2. Track symbol changes in ClickUp
3. Automatically document complex modules
4. Create architecture diagrams from code structure

---

## Step 1: Initial Setup

### Install ctags Globally
```bash
# macOS
brew install libjansson universal-ctags

# Linux
sudo apt-get install libjansson-dev universal-ctags

# Verify
ctags --list-features | grep json
```

### Create Project Config

Create `.ctags.d/project.ctags`:

```
# Output configuration
--output-format=json
--fields=+l +e +S +n

# Standard exclusions
--exclude=.git
--exclude=node_modules
--exclude=__pycache__
--exclude=.pytest_cache
--exclude=.venv
--exclude=venv
--exclude=bin
--exclude=obj
--exclude=.vs

# Language configuration
--languages=Python,C#,JavaScript,TypeScript

# Extras
--extras=+p
```

---

## Step 2: Generate and Parse Tags

### Bash Automation Script

Create `scripts/generate_codemap.sh`:

```bash
#!/bin/bash
# generate_codemap.sh: Generate code maps and documentation

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TAGS_FILE="${PROJECT_ROOT}/.tags.json"
DOCS_DIR="${PROJECT_ROOT}/docs/codemap"

echo "🔍 Generating ctags..."
ctags --output-format=json -R . > "$TAGS_FILE"

# Create docs directory
mkdir -p "$DOCS_DIR"

echo "📊 Generating statistics..."
python3 << 'EOF'
import json
from pathlib import Path

tags_file = Path('.tags.json')
stats = {}

with open(tags_file) as f:
    for line in f:
        data = json.loads(line)
        if data.get('_type') != 'tag':
            continue
        
        lang = data.get('language', 'Unknown')
        kind = data.get('kind', 'other')
        
        if lang not in stats:
            stats[lang] = {}
        if kind not in stats[lang]:
            stats[lang][kind] = 0
        stats[lang][kind] += 1

# Print summary
print("\n📈 Code Structure Summary\n")
for lang in sorted(stats.keys()):
    print(f"  {lang}:")
    for kind in sorted(stats[lang].keys()):
        count = stats[lang][kind]
        print(f"    • {kind}: {count}")

# Export JSON
with open('docs/codemap/statistics.json', 'w') as f:
    json.dump(stats, f, indent=2)
EOF

echo "✅ Code maps generated in $DOCS_DIR"
```

Make executable:
```bash
chmod +x scripts/generate_codemap.sh
```

---

## Step 3: Integrate with ClickUp

### Python ClickUp Integration

Create `scripts/sync_to_clickup.py`:

```python
#!/usr/bin/env python3
"""
Sync code structure changes to ClickUp tasks
"""

import json
import os
from pathlib import Path
from ctags_parser import CtagsParser
from clickup_framework import ClickUpClient

def generate_code_documentation():
    """Generate structured documentation from code map"""
    
    parser = CtagsParser('.tags.json')
    stats = parser.statistics()
    
    # Group by language
    by_lang = {}
    for tag in parser.all_tags:
        if tag.language not in by_lang:
            by_lang[tag.language] = {
                'classes': [],
                'functions': [],
                'total': 0
            }
        by_lang[tag.language]['total'] += 1
        
        if tag.kind == 'class':
            by_lang[tag.language]['classes'].append(tag.name)
        elif tag.kind == 'function':
            by_lang[tag.language]['functions'].append(tag.name)
    
    return stats, by_lang

def sync_to_clickup(task_list_id, stats, by_lang):
    """Push documentation to ClickUp"""
    
    client = ClickUpClient(api_token=os.getenv('CLICKUP_API_TOKEN'))
    
    # Build description
    description = f"""
## Code Structure Update

**Generated:** {pd.Timestamp.now()}

### Summary
- Total symbols: {stats['total_tags']}
- Files analyzed: {stats['files']}
- Languages: {stats['languages']}

### Breakdown by Language

"""
    
    for lang in sorted(stats['by_language'].keys()):
        count = stats['by_language'][lang]
        description += f"\n**{lang}**: {count} symbols\n"
        
        if lang in by_lang and by_lang[lang]['classes']:
            description += f"  Classes: {', '.join(by_lang[lang]['classes'][:5])}"
            if len(by_lang[lang]['classes']) > 5:
                description += f" +{len(by_lang[lang]['classes']) - 5} more"
            description += "\n"
    
    # Create or update task
    try:
        task = client.create_task(
            list_id=task_list_id,
            name=f"Code Map - {stats['total_tags']} symbols",
            description=description,
            status='completed',
            custom_fields={
                'code_map_generated': True,
                'total_symbols': stats['total_tags'],
                'files_analyzed': stats['files']
            }
        )
        
        print(f"✅ ClickUp task created: {task['id']}")
        return task
        
    except Exception as e:
        print(f"⚠️ Failed to create ClickUp task: {e}")
        return None

if __name__ == '__main__':
    stats, by_lang = generate_code_documentation()
    sync_to_clickup(
        task_list_id=os.getenv('CLICKUP_LIST_ID'),
        stats=stats,
        by_lang=by_lang
    )
```

---

## Step 4: GitHub Actions CI/CD

Create `.github/workflows/codemap.yml`:

```yaml
name: Generate Code Map

on:
  push:
    branches:
      - main
      - develop
  pull_request:
  schedule:
    - cron: '0 0 * * 0'  # Weekly

jobs:
  codemap:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0
      
      - name: Install dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y universal-ctags libjansson-dev
          pip install -r requirements.txt
      
      - name: Generate tags
        run: |
          ctags --output-format=json \
            --languages=Python,C#,JavaScript,TypeScript \
            --exclude=.git \
            --exclude=node_modules \
            --exclude=__pycache__ \
            -R . > .tags.json
      
      - name: Generate documentation
        run: |
          bash scripts/generate_codemap.sh
          python3 scripts/sync_to_clickup.py
        env:
          CLICKUP_API_TOKEN: ${{ secrets.CLICKUP_API_TOKEN }}
          CLICKUP_LIST_ID: ${{ secrets.CLICKUP_LIST_ID }}
      
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: code-maps
          path: |
            .tags.json
            docs/codemap/
      
      - name: Commit changes
        if: github.event_name == 'push'
        run: |
          git config --local user.email "codemap@example.com"
          git config --local user.name "CodeMap Bot"
          git add docs/codemap/
          git commit -m "chore: update code maps [skip ci]" || true
          git push
```

---

## Step 5: Local Development Hook

Create `.git/hooks/post-merge`:

```bash
#!/bin/bash
# .git/hooks/post-merge: Refresh code maps after merge

echo "🔄 Updating code maps..."

ctags --output-format=json \
  --languages=Python,C#,JavaScript,TypeScript \
  -R . > .tags.json 2>/dev/null

python3 << 'EOF'
from ctags_parser import CtagsParser

parser = CtagsParser('.tags.json')
stats = parser.statistics()

print(f"✅ Code map updated: {stats['total_tags']} symbols")
EOF

exit 0
```

Make executable:
```bash
chmod +x .git/hooks/post-merge
```

---

## Step 6: PowerShell Automation (Windows)

Create `scripts/Update-CodeMap.ps1`:

```powershell
<#
.SYNOPSIS
    Update code maps and documentation

.DESCRIPTION
    Generates ctags, parses structure, exports documentation
#>

param(
    [string]$TagsFile = '.tags.json',
    [string]$DocsDir = 'docs/codemap',
    [switch]$UpdateClickUp
)

# Import ctags module
Import-Module ./CtagsMapper.psm1

Write-Host "🔍 Generating ctags..." -ForegroundColor Cyan

# Generate tags
& ctags --output-format=json `
    --languages=Python,C#,JavaScript `
    --exclude=.git `
    --exclude=node_modules `
    -R . > $TagsFile

# Parse and document
$parser = New-CtagsParser $TagsFile
$stats = Get-TagsStatistics -Parser $parser

Write-Host "📊 Statistics:" -ForegroundColor Cyan
$stats | ConvertTo-Json | Write-Host

# Create docs directory
New-Item -ItemType Directory -Force -Path $DocsDir | Out-Null

# Generate markdown for each Python file
Get-ChildItem -Path src -Filter *.py -Recurse | ForEach-Object {
    $relPath = $_.FullName -replace [regex]::Escape((Get-Location)), ''
    Export-CodeMap -Parser $parser `
        -FilePath $relPath `
        -OutputFile "$DocsDir/$($_.BaseName).md"
    
    Write-Host "  ✓ $($_.Name)" -ForegroundColor Green
}

Write-Host "`n✅ Code maps updated in $DocsDir" -ForegroundColor Green

if ($UpdateClickUp) {
    Write-Host "📤 Syncing to ClickUp..." -ForegroundColor Cyan
    python3 scripts/sync_to_clickup.py
}
```

Run it:
```powershell
.\scripts\Update-CodeMap.ps1 -UpdateClickUp
```

---

## Step 7: Architecture Diagram Generation

Create `scripts/generate_architecture.py`:

```python
#!/usr/bin/env python3
"""
Generate architecture diagrams from code structure
"""

import json
from ctags_parser import CtagsParser
from pathlib import Path

def generate_mermaid_diagram(tags_file):
    """Generate Mermaid diagram of code structure"""
    
    parser = CtagsParser(tags_file)
    
    # Group by file and language
    by_lang = {}
    for tag in parser.all_tags:
        if tag.language not in by_lang:
            by_lang[tag.language] = []
        by_lang[tag.language].append(tag)
    
    diagram = ["graph TD"]
    
    for lang, tags in by_lang.items():
        # Create language node
        lang_node = lang.replace('#', '_').replace(' ', '_')
        diagram.append(f'  {lang_node}["{lang}"]')
        
        # Add main structures
        classes = set(t.name for t in tags if t.kind == 'class')
        for cls in sorted(classes)[:5]:  # Limit to 5
            cls_node = cls.replace('-', '_').replace(' ', '_')
            diagram.append(f'  {lang_node} --> {cls_node}["{cls}"]')
    
    return "\n".join(diagram)

if __name__ == '__main__':
    diagram = generate_mermaid_diagram('.tags.json')
    
    output_file = Path('docs/codemap/architecture.md')
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        f.write("# Code Architecture\n\n")
        f.write("```mermaid\n")
        f.write(diagram)
        f.write("\n```\n")
    
    print(f"✅ Architecture diagram: {output_file}")
```

---

## Step 8: Daily Summary Report

Create `scripts/daily_report.py`:

```python
#!/usr/bin/env python3
"""
Generate daily code metrics report
"""

import json
from datetime import datetime
from ctags_parser import CtagsParser

def generate_report(tags_file):
    """Generate daily metrics"""
    
    parser = CtagsParser(tags_file)
    stats = parser.statistics()
    
    report = f"""
# Daily Code Metrics - {datetime.now().strftime('%Y-%m-%d')}

## Overview
- **Total Symbols**: {stats['total_tags']}
- **Files Analyzed**: {stats['files']}
- **Languages**: {stats['languages']}

## By Language
"""
    
    for lang, count in sorted(stats['by_language'].items(), key=lambda x: x[1], reverse=True):
        report += f"- {lang}: {count}\n"
    
    report += "\n## By Kind\n"
    
    for kind, count in sorted(stats['by_kind'].items(), key=lambda x: x[1], reverse=True):
        report += f"- {kind}: {count}\n"
    
    return report

if __name__ == '__main__':
    report = generate_report('.tags.json')
    print(report)
    
    # Save report
    with open(f"docs/reports/metrics_{datetime.now().strftime('%Y%m%d')}.md", 'w') as f:
        f.write(report)
```

---

## Complete Workflow Example

```bash
# 1. Initial setup
brew install libjansson universal-ctags
cp ctags_parser.py scripts/
cp CtagsMapper.psm1 .

# 2. Generate code map
ctags --output-format=json -R . > .tags.json

# 3. View structure
python3 ctags_parser.py .tags.json show src/core/service.py

# 4. Generate documentation
python3 ctags_parser.py .tags.json markdown src/core/service.py > docs/service.md

# 5. Sync to ClickUp
CLICKUP_API_TOKEN=xxx python3 scripts/sync_to_clickup.py

# 6. Generate reports
python3 scripts/daily_report.py
```

---

## Integration with Your CLI Tools

### Using cum Tool

```bash
# Generate code map
cum tc "Code Structure" --description "$(python3 ctags_parser.py tags.json stats | jq .)"

# Document module
cum tc "Module: UserService" --description "$(python3 ctags_parser.py tags.json markdown src/services/user.py)"

# Update status
cum tss "code_audit" --status "in_progress"
```

---

## Benefits

✅ **Automatic Documentation** - Always in sync with code  
✅ **Architecture Tracking** - See structure evolution  
✅ **Team Communication** - Share code maps with ClickUp  
✅ **Quality Metrics** - Track complexity and growth  
✅ **Multi-Language** - Python, C#, JavaScript, etc.  
✅ **Zero Maintenance** - Runs in CI/CD automatically  

---

## Next Steps

1. Install ctags with jansson
2. Create `.ctags` config in project root
3. Run `ctags --output-format=json -R .` to test
4. Set up GitHub Actions workflow
5. Configure ClickUp task sync
6. Schedule daily reports

