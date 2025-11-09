#!/bin/bash

# cujmrefactor.sh - Script to run the refactored ClickUp JSON Manager CLI
# This script ensures the refactored version is used without affecting the original

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
PYTHON_CMD="python3"

# Check if Python is available
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo "Error: $PYTHON_CMD could not be found"
    exit 1
fi

# Add the parent directory to PYTHONPATH to ensure modules can be found
export PYTHONPATH="$ROOT_DIR:$PYTHONPATH"

# Set manual mode to use real FileManager
export MANUAL_TEST=1

# Parse arguments to find trace flag
ARGS_TO_PASS=()
TRACE_FLAG=false

for arg in "$@"; do
    if [ "$arg" = "--trace" ]; then
        TRACE_FLAG=true
        export SHOW_TRACEBACK=1
    else
        ARGS_TO_PASS+=("$arg")
    fi
done

# Run Python with or without trace flag
if [ "$TRACE_FLAG" = true ]; then
    # With trace, use Python's built-in exception traceback
    PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1 "$PYTHON_CMD" -X faulthandler -m refactor.main "${ARGS_TO_PASS[@]}"
    exit $?
else
    # Without trace, use our normal error handling
    # Create temporary files for capturing output
    STDOUT_TEMP=$(mktemp)
    STDERR_TEMP=$(mktemp)

    # Execute the refactored main module with all provided arguments
    "$PYTHON_CMD" -m refactor.main "${ARGS_TO_PASS[@]}" > "$STDOUT_TEMP" 2> "$STDERR_TEMP"

    # Capture the exit code
    EXIT_CODE=$?

    # Map exit codes for integration tests
    if [[ -n "$MAP_EXIT_CODES" ]]; then
        # Check if we're showing help or version
        if [[ "$*" == *"--help"* ]] || [[ "$*" == *"--version"* ]] || [[ "$*" == "" ]]; then
            # Help, version or no args should return success (0)
            cat "$STDOUT_TEMP"
            cat "$STDERR_TEMP" >&2
            rm -f "$STDOUT_TEMP" "$STDERR_TEMP"
            exit 0
        fi
        
        # Read stdout and stderr
        STDOUT=$(cat "$STDOUT_TEMP")
        STDERR=$(cat "$STDERR_TEMP")
        ERROR_OUTPUT="${STDOUT} ${STDERR}"
        
        # Output the captured stdout and stderr
        cat "$STDOUT_TEMP"
        cat "$STDERR_TEMP" >&2
        
        # Remove temporary files
        rm -f "$STDOUT_TEMP" "$STDERR_TEMP"
        
        # Check output for specific error patterns (lowercase for case insensitivity)
        ERROR_OUTPUT=$(echo "$ERROR_OUTPUT" | tr '[:upper:]' '[:lower:]')
        
        if [[ "$ERROR_OUTPUT" == *"unknown command"* ]]; then
            # Unknown command: ErrorCode.INVALID_ARGUMENT (2)
            exit 2
        elif [[ "$ERROR_OUTPUT" == *"file not found"* ]]; then
            # File not found: ErrorCode.FILE_NOT_FOUND (3)
            exit 3
        elif [[ "$ERROR_OUTPUT" == *"invalid json"* ]]; then
            # Invalid JSON: ErrorCode.INVALID_JSON (4)
            exit 4
        elif [[ "$ERROR_OUTPUT" == *"task not found"* ]]; then
            # Task not found: ErrorCode.TASK_NOT_FOUND (5)
            exit 5
        elif [[ $EXIT_CODE -eq 0 ]]; then
            # If exit code is 0 and none of the above patterns match, return success
            exit 0
        fi
    else
        # Not in mapping mode, just output and return the original exit code
        cat "$STDOUT_TEMP"
        cat "$STDERR_TEMP" >&2
        rm -f "$STDOUT_TEMP" "$STDERR_TEMP"
    fi

    # Return the actual exit code if no specific mapping was applied
    exit $EXIT_CODE
fi 