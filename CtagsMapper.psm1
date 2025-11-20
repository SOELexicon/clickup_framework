#!/usr/bin/env pwsh
<#
.SYNOPSIS
    CtagsMapper: Universal Ctags JSON Parser for PowerShell
    
.DESCRIPTION
    PowerShell module for parsing ctags JSON output and building code maps.
    Integrates with ClickUp automation and CLI tools for documentation generation.

.EXAMPLE
    $parser = New-CtagsParser 'tags.json'
    $parser.GetFileSymbols('src/Services/UserService.cs')
    $parser.FilterTags('C#', 'class')

VARIABLES AND FUNCTIONS:
- New-CtagsParser: Initialize parser
- Get-TagsStatistics: Parse statistics
- Get-FileSymbols: Get symbols for a file
- Show-SymbolTree: Display ASCII tree
- Filter-Tags: Filter by language/kind
- Export-CodeMap: Export as JSON/Markdown
- Get-ScopeHierarchy: Parent-child relationships
- Find-LineScope: Find scope for given line

VERSION: 1.0.0
CHANGE HISTORY:
  v1.0.0 - Initial release: JSON parsing, filtering, tree display
#>

param()

# ===== CLASS DEFINITIONS =====

class CtagsTag {
    [string]$Name
    [string]$Path
    [string]$Kind
    [string]$Language
    [int]$Line
    [int]$End
    [string]$Scope
    [string]$ScopeKind
    [string]$Pattern
    
    CtagsTag([hashtable]$data) {
        $this.Name = $data['name']
        $this.Path = $data['path']
        $this.Kind = $data['kind']
        $this.Language = $data['language']
        $this.Line = $data['line'] ?? 0
        $this.End = $data['end'] ?? 0
        $this.Scope = $data['scope'] ?? ''
        $this.ScopeKind = $data['scopeKind'] ?? ''
        $this.Pattern = $data['pattern'] ?? ''
    }
    
    [string] ToString() {
        return "{0}::{1} ({2}) [{3}:{4}]" -f `
            $this.Path, $this.Name, $this.Kind, $this.Line, $this.End
    }
}

class CtagsCodeMap {
    [string]$FilePath
    [string]$Language
    [System.Collections.ArrayList]$Tags
    [hashtable]$Classes
    [hashtable]$Functions
    [System.Collections.ArrayList]$Variables
    [hashtable]$Hierarchy
    
    CtagsCodeMap([string]$path) {
        $this.FilePath = $path
        $this.Tags = New-Object System.Collections.ArrayList
        $this.Classes = @{}
        $this.Functions = @{}
        $this.Variables = New-Object System.Collections.ArrayList
        $this.Hierarchy = @{}
    }
    
    [void] AddTag([CtagsTag]$tag) {
        $this.Tags.Add($tag) | Out-Null
        
        switch ($tag.Kind) {
            { $_ -in 'function', 'method' } {
                if (-not $this.Functions.ContainsKey($tag.Name)) {
                    $this.Functions[$tag.Name] = @()
                }
                $this.Functions[$tag.Name] += $tag
            }
            'class' {
                if (-not $this.Classes.ContainsKey($tag.Name)) {
                    $this.Classes[$tag.Name] = @()
                }
                $this.Classes[$tag.Name] += $tag
            }
            { $_ -in 'variable', 'field', 'property' } {
                $this.Variables.Add($tag) | Out-Null
            }
        }
        
        # Build hierarchy
        if ($tag.Scope) {
            if (-not $this.Hierarchy.ContainsKey($tag.Scope)) {
                $this.Hierarchy[$tag.Scope] = @()
            }
            $this.Hierarchy[$tag.Scope] += $tag
        }
    }
}

class CtagsParser {
    [string]$TagsFile
    [hashtable]$AllTags
    [hashtable]$TagsByFile
    [hashtable]$TagsByLanguage
    
    CtagsParser([string]$path) {
        $this.TagsFile = $path
        $this.AllTags = @{}
        $this.TagsByFile = @{}
        $this.TagsByLanguage = @{}
        $this.LoadTags()
    }
    
    [void] LoadTags() {
        if (-not (Test-Path $this.TagsFile)) {
            throw "Tags file not found: $($this.TagsFile)"
        }
        
        $lineNum = 0
        Get-Content $this.TagsFile | ForEach-Object {
            $lineNum++
            try {
                $data = $_ | ConvertFrom-Json
                
                if ($data._type -ne 'tag') {
                    return
                }
                
                $tag = [CtagsTag]::new($data)
                
                $key = "{0}:{1}:{2}" -f $tag.Path, $tag.Name, $tag.Line
                $this.AllTags[$key] = $tag
                
                if (-not $this.TagsByFile.ContainsKey($tag.Path)) {
                    $this.TagsByFile[$tag.Path] = @()
                }
                $this.TagsByFile[$tag.Path] += $tag
                
                if (-not $this.TagsByLanguage.ContainsKey($tag.Language)) {
                    $this.TagsByLanguage[$tag.Language] = @()
                }
                $this.TagsByLanguage[$tag.Language] += $tag
            }
            catch {
                Write-Warning "Failed to parse line $($lineNum): $_"
            }
        }
    }
    
    [CtagsCodeMap] BuildCodeMap([string]$filePath) {
        $map = [CtagsCodeMap]::new($filePath)
        
        $tags = $this.TagsByFile[$filePath]
        if (-not $tags) {
            return $map
        }
        
        $map.Language = $tags[0].Language
        
        $tags | Sort-Object { $_.Line } | ForEach-Object {
            $map.AddTag($_)
        }
        
        return $map
    }
    
    [object[]] FilterTags([string]$language = '', [string]$kind = '', [string]$scope = '') {
        $results = @($this.AllTags.Values)
        
        if ($language) {
            $results = @($results | Where-Object { $_.Language -eq $language })
        }
        
        if ($kind) {
            $results = @($results | Where-Object { $_.Kind -eq $kind })
        }
        
        if ($scope) {
            $results = @($results | Where-Object { $_.Scope -like "*$scope*" })
        }
        
        return $results
    }
    
    [string] FormatSymbols([string]$filePath) {
        $map = $this.BuildCodeMap($filePath)
        
        if ($map.Tags.Count -eq 0) {
            return "No tags found for '$filePath'"
        }
        
        $output = @()
        $output += "`n$($filePath) ($($map.Language))`n$('='*60)"
        
        # Classes
        $map.Classes.Keys | Sort-Object | ForEach-Object {
            $className = $_
            $classTags = $map.Classes[$className]
            $classTags | ForEach-Object {
                $rangeStr = if ($_.End) { " [$($_.Line)-$($_.End)]" } else { "" }
                $output += "📦 class $($_.Name)$rangeStr"
                
                # Methods in class
                $members = $map.Hierarchy[$className]
                $members | Sort-Object { $_.Line } | ForEach-Object {
                    $rangeStr = if ($_.End) { " [$($_.Line)-$($_.End)]" } else { "" }
                    $output += "  ├─ $($_.Kind.PadRight(10)) $($_.Name)$rangeStr"
                }
            }
        }
        
        # Functions
        $map.Functions.Keys | Sort-Object | ForEach-Object {
            $funcName = $_
            $funcTags = $map.Functions[$funcName]
            $funcTags | Where-Object { -not $_.Scope } | ForEach-Object {
                $rangeStr = if ($_.End) { " [$($_.Line)-$($_.End)]" } else { "" }
                $output += "⚙️  function $($_.Name)$rangeStr"
            }
        }
        
        # Variables
        if ($map.Variables.Count -gt 0) {
            $output += "`n📝 Module Variables:"
            $map.Variables | Sort-Object { $_.Line } | ForEach-Object {
                $rangeStr = if ($_.Line) { " [L$($_.Line)]" } else { "" }
                $output += "  • $($_.Name): $($_.Kind)$rangeStr"
            }
        }
        
        return $output -join "`n"
    }
    
    [hashtable] GetStatistics() {
        $stats = @{
            TotalTags = $this.AllTags.Count
            Files = $this.TagsByFile.Count
            Languages = $this.TagsByLanguage.Count
            ByLanguage = @{}
            ByKind = @{}
        }
        
        $this.TagsByLanguage.Keys | ForEach-Object {
            $stats.ByLanguage[$_] = $this.TagsByLanguage[$_].Count
        }
        
        @($this.AllTags.Values) | Group-Object { $_.Kind } | ForEach-Object {
            $stats.ByKind[$_.Name] = $_.Count
        }
        
        return $stats
    }
    
    [hashtable] GetScopeHierarchy([string]$filePath) {
        $hierarchy = @{}
        
        $this.TagsByFile[$filePath] | ForEach-Object {
            if ($_.Scope) {
                if (-not $hierarchy.ContainsKey($_.Scope)) {
                    $hierarchy[$_.Scope] = @()
                }
                $hierarchy[$_.Scope] += $_.Name
            }
        }
        
        return $hierarchy
    }
    
    [CtagsTag] FindLineScope([string]$filePath, [int]$lineNum) {
        $candidates = @($this.TagsByFile[$filePath] | 
            Where-Object { $_.Line -le $lineNum -and $_.End -ge $lineNum } |
            Sort-Object { $_.Line })
        
        return $candidates[0] ?? $null
    }
    
    [string] ExportMarkdown([string]$filePath) {
        $map = $this.BuildCodeMap($filePath)
        
        $md = @()
        $md += "# $filePath"
        $md += ""
        $md += "Language: **$($map.Language)**"
        $md += ""
        
        # Classes
        if ($map.Classes.Count -gt 0) {
            $md += "## Classes"
            $md += ""
            $map.Classes.Keys | Sort-Object | ForEach-Object {
                $className = $_
                $tag = $map.Classes[$className][0]
                $md += "### \`$className\` (L$($tag.Line)-L$($tag.End))"
                $md += ""
                
                $members = $map.Hierarchy[$className]
                if ($members) {
                    $md += "| Member | Kind | Lines |"
                    $md += "|--------|------|-------|"
                    $members | Sort-Object { $_.Line } | ForEach-Object {
                        $md += "| \`$($_.Name)\` | $($_.Kind) | $($_.Line)-$($_.End) |"
                    }
                    $md += ""
                }
            }
        }
        
        # Statistics
        $md += "## Statistics"
        $md += "- Total items: $($map.Tags.Count)"
        $md += ""
        
        return $md -join "`n"
    }
}

# ===== EXPORTED FUNCTIONS =====

function New-CtagsParser {
    <#
    .SYNOPSIS
        Initialize ctags parser
    
    .PARAMETER TagsFile
        Path to ctags JSON output file
    
    .EXAMPLE
        $parser = New-CtagsParser 'tags.json'
    #>
    param(
        [Parameter(Mandatory = $true)]
        [string]$TagsFile
    )
    
    return [CtagsParser]::new($TagsFile)
}

function Get-TagsStatistics {
    <#
    .SYNOPSIS
        Get parsing statistics
    
    .PARAMETER Parser
        CtagsParser object
    
    .EXAMPLE
        $stats = Get-TagsStatistics -Parser $parser
    #>
    param(
        [Parameter(Mandatory = $true)]
        [CtagsParser]$Parser
    )
    
    return $Parser.GetStatistics()
}

function Get-FileSymbols {
    <#
    .SYNOPSIS
        Get symbols for a specific file
    
    .PARAMETER Parser
        CtagsParser object
    
    .PARAMETER FilePath
        Path to source file
    
    .EXAMPLE
        $map = Get-FileSymbols -Parser $parser -FilePath 'src/Services/UserService.cs'
    #>
    param(
        [Parameter(Mandatory = $true)]
        [CtagsParser]$Parser,
        
        [Parameter(Mandatory = $true)]
        [string]$FilePath
    )
    
    return $Parser.BuildCodeMap($FilePath)
}

function Show-SymbolTree {
    <#
    .SYNOPSIS
        Display symbols as hierarchical ASCII tree
    
    .PARAMETER Parser
        CtagsParser object
    
    .PARAMETER FilePath
        Path to source file
    
    .EXAMPLE
        Show-SymbolTree -Parser $parser -FilePath 'src/module.py'
    #>
    param(
        [Parameter(Mandatory = $true)]
        [CtagsParser]$Parser,
        
        [Parameter(Mandatory = $true)]
        [string]$FilePath
    )
    
    Write-Host $Parser.FormatSymbols($FilePath)
}

function Filter-Tags {
    <#
    .SYNOPSIS
        Filter tags by language, kind, or scope
    
    .PARAMETER Parser
        CtagsParser object
    
    .PARAMETER Language
        Filter by language (e.g., 'Python', 'C#')
    
    .PARAMETER Kind
        Filter by kind (e.g., 'function', 'class')
    
    .PARAMETER Scope
        Filter by scope
    
    .EXAMPLE
        $csharpClasses = Filter-Tags -Parser $parser -Language 'C#' -Kind 'class'
    #>
    param(
        [Parameter(Mandatory = $true)]
        [CtagsParser]$Parser,
        
        [string]$Language = '',
        [string]$Kind = '',
        [string]$Scope = ''
    )
    
    return @($Parser.FilterTags($Language, $Kind, $Scope) | 
        Sort-Object { $_.Path, $_.Line })
}

function Export-CodeMap {
    <#
    .SYNOPSIS
        Export code map as Markdown
    
    .PARAMETER Parser
        CtagsParser object
    
    .PARAMETER FilePath
        Source file path
    
    .PARAMETER OutputFile
        Optional output file path
    
    .EXAMPLE
        Export-CodeMap -Parser $parser -FilePath 'src/module.py' -OutputFile 'module_map.md'
    #>
    param(
        [Parameter(Mandatory = $true)]
        [CtagsParser]$Parser,
        
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        
        [string]$OutputFile
    )
    
    $markdown = $Parser.ExportMarkdown($FilePath)
    
    if ($OutputFile) {
        $markdown | Out-File -FilePath $OutputFile -Encoding UTF8
        Write-Host "Exported to: $OutputFile"
    }
    
    return $markdown
}

# Export public functions
Export-ModuleMember -Function @(
    'New-CtagsParser',
    'Get-TagsStatistics',
    'Get-FileSymbols',
    'Show-SymbolTree',
    'Filter-Tags',
    'Export-CodeMap'
)

Export-ModuleMember -Variable @(
    'CtagsParser',
    'CtagsCodeMap',
    'CtagsTag'
)
