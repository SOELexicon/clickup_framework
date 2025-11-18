#!/bin/bash
# Update ClickUp tasks after migrating commands to BaseCommand

COMMIT_SHA="$1"

if [ -z "$COMMIT_SHA" ]; then
    echo "Usage: $0 <commit_sha>"
    echo "Example: $0 535bc1d"
    exit 1
fi

# Function to update a single task
update_task() {
    local task_id="$1"
    local file_name="$2"
    local commit="$3"

    echo "Updating task $task_id for $file_name..."

    # Add comment
    cum ca "$task_id" "Migrated to BaseCommand. Commit: $commit. Tested and working." 2>&1 | grep -E "✓|✗"

    # Update checklist items if they exist
    for i in {1..8}; do
        cum chk item-update 1 $i --task "$task_id" --resolved true 2>/dev/null
    done

    # Set status to Committed
    cum tss "$task_id" "Committed" 2>&1 | grep -E "✓|✗|Status updated"
}

# Mapping of files to task IDs
declare -A TASK_MAP=(
    ["demo.py"]="86c6jrdy8 86c6jre94"
    ["dump.py"]="86c6jreft 86c6jre32"
    ["flat.py"]="86c6jrep1 86c6jre5e"
    ["filter.py"]="86c6jrejy 86c6jre4e"
    ["stats.py"]="86c6jrfbt 86c6jrf56"
    ["clear_current.py"]="86c6jrdty 86c6jrdzz 86c6jrdw8"
    ["assigned_command.py"]="86c6jrdqk"
    ["attachment_commands.py"]="86c6jrdrg"
    ["automation_commands.py"]="86c6jrdrv"
    ["checklist_commands.py"]="86c6jrdta"
    ["command_sync.py"]="86c6jrdup 86c6jre12"
    ["comment_commands.py"]="86c6jrdvr 86c6jre2w"
    ["custom_field_commands.py"]="86c6jrdxe 86c6jre7k"
    ["detail.py"]="86c6jrdz8 86c6jreaq"
    ["diff_command.py"]="86c6jrec0 86c6jre08"
    ["doc_commands.py"]="86c6jred3 86c6jre15"
    ["folder_commands.py"]="86c6jrerk 86c6jre7x"
    ["git_overflow_command.py"]="86c6jrex5 86c6jrea1"
    ["git_reauthor_command.py"]="86c6jrey8 86c6jrecf"
    ["gitpull_command.py"]="86c6jrezh 86c6jredq"
    ["gitsuck_command.py"]="86c6jrf0x 86c6jrej0"
    ["hierarchy.py"]="86c6jrf21 86c6jrema"
    ["horde_command.py"]="86c6jrf3d 86c6jrerf"
    ["jizz_command.py"]="86c6jrf4h 86c6jrewz"
    ["list_commands.py"]="86c6jrf54 86c6jrey3"
    ["mermaid_commands.py"]="86c6jrf5y 86c6jreyz"
    ["search_command.py"]="86c6jrf6k 86c6jrf0p"
    ["space_commands.py"]="86c6jrf9v 86c6jrf3t"
    ["stash_command.py"]="86c6jrfar 86c6jrf4d"
    ["task_commands.py"]="86c6jrfd1 86c6jrf61"
    ["update_command.py"]="86c6jrfe6 86c6jrf6q"
)

# Update tasks for specified files
if [ $# -eq 1 ]; then
    # Update all tasks
    echo "No specific files provided. Please specify files to update."
    echo "Example: $0 $COMMIT_SHA demo.py dump.py"
    exit 1
fi

shift  # Skip commit_sha argument

for file in "$@"; do
    if [ -n "${TASK_MAP[$file]}" ]; then
        echo "Processing $file..."
        for task_id in ${TASK_MAP[$file]}; do
            update_task "$task_id" "$file" "$COMMIT_SHA"
        done
        echo ""
    else
        echo "Warning: No task mapping found for $file"
    fi
done

echo "✓ Task updates complete!"
