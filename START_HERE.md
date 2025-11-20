# ctags Code Mapping Toolkit - Start Here

Welcome! You have a complete toolkit for mapping source code variables, functions, and structure across **Python, C#, JavaScript, and 40+ other languages**.

## Your Situation

You're getting notices like this from ctags:

```
ctags.exe: Notice: ignoring null tag in ./.venv/Lib/site-packages/...
```

**This is normal.** Third-party libraries have minified code ctags can't fully parse. The solution is simple—exclude those directories (which you should do anyway).

## Quick Fix (2 Minutes)

### 1. Copy Configuration File

Copy the provided `.ctags` file to your project root.

### 2. Run ctags

```powershell
ctags --output-format=json -R .
```

That's it. The `.ctags` config includes `--quiet` to suppress those notices.

## What You Now Have

### 📄 Documentation Files

| File | Purpose |
|------|---------|
| **README.md** | Overview and quick start |
| **CTAGS_WINDOWS_SETUP.md** | Windows-specific setup & troubleshooting (for you!) |
| **CTAGS_QUICK_REFERENCE.md** | Command examples and patterns |
| **CTAGS_SETUP.md** | Complete installation guide |
| **CTAGS_INTEGRATION_EXAMPLE.md** | ClickUp, GitHub Actions, full automation |

### 🛠 Tools

| File | Purpose |
|------|---------|
| **ctags_parser.py** | Python CLI for analyzing tags |
| **CtagsMapper.psm1** | PowerShell module for Windows/.NET |
| **generate_codemap.bat** | Windows batch automation script |
| **.ctags** | Project configuration (copy to root) |

---

## Recommended Reading Order

### For Quick Start (15 minutes)
1. Read this file (you're reading it!)
2. Copy `.ctags` to your project
3. Run `.\generate_codemap.bat`
4. Look at `CTAGS_QUICK_REFERENCE.md` for examples

### For Full Understanding (1 hour)
1. **CTAGS_WINDOWS_SETUP.md** - Your platform-specific guide
2. **CTAGS_QUICK_REFERENCE.md** - See what ctags can do
3. **README.md** - Understand the overall toolkit
4. Try examples in PowerShell and Python

### For Integration & Automation (2 hours)
1. **CTAGS_INTEGRATION_EXAMPLE.md** - Full workflow with ClickUp
2. Setup GitHub Actions or your CI/CD
3. Integrate with your existing tools

---

## The Problem It Solves

**Mapping Code Structure** - Know:
- Where every function, class, variable is located
- Line numbers (start and end)
- Scope hierarchy (methods in classes, nested functions)
- What language each symbol is in
- Cross-references between symbols

**Example:**
```json
{
  "name": "authenticate",
  "path": "src/auth/service.py",
  "kind": "function",
  "line": 42,
  "end": 67,
  "scope": "AuthService",
  "language": "Python"
}
```

Now you can:
- Auto-generate documentation
- Track code changes
- Create architecture diagrams
- Build refactoring tools
- Integrate with ClickUp tasks
- Enable smart IDE features

---

## Hands-On: Try It Now

### Step 1: Copy Config File

```powershell
# Copy the .ctags file to your project root
Copy-Item .ctags .
```

### Step 2: Generate Tags

```powershell
# Use the batch script (easiest)
.\generate_codemap.bat

# Or directly
ctags --output-format=json -R . > tags.json
```

### Step 3: Explore Results

```powershell
# View with PowerShell
Import-Module .\CtagsMapper.psm1
$parser = New-CtagsParser 'tags.json'
Show-SymbolTree -Parser $parser -FilePath 'src/Services/UserService.cs'

# Or Python
python3 ctags_parser.py tags.json show src/services/user_service.py
```

### Step 4: Get Statistics

```powershell
# View statistics
.\generate_codemap.bat --stats
```

---

## Your Files Explained

### .ctags (Configuration)
Place in project root. Contains:
- Exclusions (`.venv`, `node_modules`, `bin`, `obj`, etc.)
- Output format (JSON)
- Language configuration
- `--quiet` flag (silences those notices you saw)

### generate_codemap.bat (Windows Script)
Easy automation with options:
```powershell
.\generate_codemap.bat              # Full scan
.\generate_codemap.bat --python     # Python only
.\generate_codemap.bat --csharp     # C# only
.\generate_codemap.bat --stats      # Show statistics
```

### ctags_parser.py (Python Tool)
Analyze tags from command line:
```bash
python3 ctags_parser.py tags.json show src/module.py
python3 ctags_parser.py tags.json filter Python class
python3 ctags_parser.py tags.json stats
```

### CtagsMapper.psm1 (PowerShell Module)
Programmatic access from PowerShell:
```powershell
Import-Module CtagsMapper.psm1
$parser = New-CtagsParser 'tags.json'
Get-FileSymbols -Parser $parser -FilePath 'src/module.py'
```

---

## Language Support

Works with:
- **Python** ✅
- **C#** ✅
- **JavaScript/TypeScript** ✅
- **Java, Go, Rust** ✅
- **40+ others** - Kotlin, Swift, Objective-C, PHP, Ruby, Lua, Bash, etc.

```powershell
# See all supported
ctags --list-languages
```

---

## Integration Ideas

### 1. Auto-Docs on Commit
```powershell
# .git/hooks/post-commit
ctags --output-format=json -R . > .tags.json
python3 ctags_parser.py .tags.json markdown src/core.py > docs/core.md
git add docs/
```

### 2. ClickUp Task Updates
```powershell
# Sync code structure to ClickUp
python3 scripts/sync_to_clickup.py
```

### 3. GitHub Actions
```yaml
# Every push: generate code map
- name: Generate code map
  run: ctags --output-format=json -R . > tags.json
```

### 4. Team Documentation
```powershell
# Generate markdown for each module
python3 ctags_parser.py tags.json markdown src/services/UserService.cs
```

---

## Troubleshooting

### Still seeing "ignoring null tag" notices?

Make sure you're using the configuration:

```powershell
# Check if .ctags exists
Test-Path .ctags

# Copy if missing
Copy-Item .ctags .

# Run (will now use config)
ctags --output-format=json -R . > tags.json
```

### ctags not found?

```powershell
# Install via Chocolatey (easiest)
choco install universal-ctags

# Or download from
# https://github.com/universal-ctags/ctags-win32/releases
```

### JSON support missing?

```powershell
# Verify
ctags --list-features | Select-String json

# If missing, install newer build or rebuild with jansson
choco install universal-ctags  # Latest should have it
```

See **CTAGS_WINDOWS_SETUP.md** for complete troubleshooting.

---

## Next: Level Up

Once basic usage works:

1. **CTAGS_INTEGRATION_EXAMPLE.md** - Automate with ClickUp + CI/CD
2. **CTAGS_QUICK_REFERENCE.md** - Advanced commands and patterns
3. **Automate your workflow** - Git hooks, scheduled tasks, etc.

---

## File Overview

```
📁 Your Toolkit
├── 📖 Documentation
│   ├── START_HERE.md (you are here)
│   ├── README.md
│   ├── CTAGS_WINDOWS_SETUP.md ⭐ (your platform)
│   ├── CTAGS_QUICK_REFERENCE.md
│   ├── CTAGS_SETUP.md
│   └── CTAGS_INTEGRATION_EXAMPLE.md
│
├── 🛠 Tools
│   ├── .ctags (copy to project root)
│   ├── generate_codemap.bat (Windows automation)
│   ├── ctags_parser.py (Python CLI)
│   └── CtagsMapper.psm1 (PowerShell module)
│
└── 📋 Notes
    └── This file!
```

---

## Summary

✅ **You have everything needed** to map code structure  
✅ **Windows-optimized** with batch script and PowerShell module  
✅ **40+ language support** including your Python/C# stack  
✅ **Easy integration** with ClickUp and automation  
✅ **Ready to use** - copy `.ctags`, run `generate_codemap.bat`  

---

## Start Now

1. **Copy `.ctags` to project root**
2. **Run `.\generate_codemap.bat`**
3. **Read `CTAGS_WINDOWS_SETUP.md`** for your platform
4. **Explore with `CtagsMapper.psm1`** PowerShell module

You're ready to go! 🚀

---

**Questions?** See the relevant documentation file above. Most answers are in **CTAGS_WINDOWS_SETUP.md** (your platform) or **CTAGS_QUICK_REFERENCE.md** (examples).
