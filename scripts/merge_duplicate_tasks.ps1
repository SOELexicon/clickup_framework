#!/usr/bin/env pwsh
# Script to merge duplicate tasks by keeping the one with the longest description
# Usage: ./scripts/merge_duplicate_tasks.ps1 <parent_task_id>

param(
    [Parameter(Mandatory=$true)]
    [string]$ParentTaskId
)

Write-Host "🔍 Analyzing subtasks of parent task: $ParentTaskId" -ForegroundColor Cyan

# Get all subtasks using detail command
$detailOutput = cum detail $ParentTaskId 2>&1 | Out-String
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error getting task details" -ForegroundColor Red
    exit 1
}

# Parse subtasks from detail output - look for subtasks section
$subtasks = @()
$lines = $detailOutput -split "`n"
$inSubtasks = $false

foreach ($line in $lines) {
    # Start of subtasks section
    if ($line -match "📂 Subtasks") {
        $inSubtasks = $true
        continue
    }
    
    # End of subtasks section (next major section)
    if ($inSubtasks -and ($line -match "^[^├└│\s]" -or $line -match "🌳 Task Relationships:")) {
        break
    }
    
    # Match subtask pattern: ├─ [task_id] 📝 Status Task Name
    # Format: ├─ [86c6jrfe6] 📝 ⬜ Migrate update_command.py to BaseCommand
    if ($inSubtasks -and $line -match '\[([a-z0-9]+)\]\s+.*?Migrate\s+(.+?)\s+to\s+BaseCommand') {
        $taskId = $matches[1]
        $taskName = "Migrate $($matches[2].Trim()) to BaseCommand"
        
        if ($taskName -and $taskName -notmatch '^Migrate All Commands') {
            $subtasks += @{
                Id = $taskId
                Name = $taskName
            }
        }
    }
}

Write-Host "📊 Found $($subtasks.Count) subtasks" -ForegroundColor Cyan

# Group by task name
$grouped = $subtasks | Group-Object -Property Name

# Find duplicates
$duplicates = $grouped | Where-Object { $_.Count -gt 1 }

if ($duplicates.Count -eq 0) {
    Write-Host "✅ No duplicate task names found!" -ForegroundColor Green
    exit 0
}

Write-Host "⚠️  Found $($duplicates.Count) groups of duplicate tasks" -ForegroundColor Yellow

$deletedCount = 0
$keptCount = 0

foreach ($group in $duplicates) {
    Write-Host "`n📋 Processing duplicates for: '$($group.Name)'" -ForegroundColor Cyan
    Write-Host "   Found $($group.Count) tasks with this name" -ForegroundColor Yellow
    
    # Get details for each task in the group
    $taskDetails = @()
    foreach ($task in $group.Group) {
        Write-Host "   Getting details for task $($task.Id)..." -ForegroundColor Gray
        $detailOutput = cum detail $task.Id 2>&1 | Out-String
        $detailLines = $detailOutput -split "`n"
        
        # Extract description
        $descStart = $false
        $description = ""
        foreach ($line in $detailLines) {
            if ($line -match "📝 Description:") {
                $descStart = $true
                continue
            }
            if ($descStart) {
                # Stop at task relationships section
                if ($line -match "🌳 Task Relationships:" -or $line -match "📊 Parent Chain:") {
                    break
                }
                # Add line to description
                $description += $line + "`n"
            }
        }
        
        $descLength = $description.Trim().Length
        
        $taskDetails += @{
            Id = $task.Id
            Name = $task.Name
            Description = $description.Trim()
            DescriptionLength = $descLength
        }
        
        Write-Host "      Description length: $descLength characters" -ForegroundColor Gray
    }
    
    # Sort by description length (longest first)
    $sorted = $taskDetails | Sort-Object -Property DescriptionLength -Descending
    
    # Keep the one with the longest description
    $keep = $sorted[0]
    $delete = $sorted[1..($sorted.Count - 1)]
    
    Write-Host "   ✅ Keeping task $($keep.Id) (description length: $($keep.DescriptionLength))" -ForegroundColor Green
    
    # Delete the others
    foreach ($taskToDelete in $delete) {
        Write-Host "   🗑️  Deleting task $($taskToDelete.Id) (description length: $($taskToDelete.DescriptionLength))" -ForegroundColor Red
        $deleteOutput = cum td $taskToDelete.Id --force 2>&1
        if ($LASTEXITCODE -eq 0) {
            $deletedCount++
            Write-Host "      ✓ Deleted successfully" -ForegroundColor Green
        } else {
            Write-Host "      ✗ Failed to delete: $deleteOutput" -ForegroundColor Red
        }
    }
    
    $keptCount++
}

Write-Host "`n📊 Summary:" -ForegroundColor Cyan
Write-Host "   ✅ Kept: $keptCount tasks" -ForegroundColor Green
Write-Host "   🗑️  Deleted: $deletedCount tasks" -ForegroundColor Yellow
Write-Host "`n✨ Done!" -ForegroundColor Green

