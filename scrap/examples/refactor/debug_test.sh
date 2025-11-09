#!/bin/bash

# Minimal debugging version to identify syntax issues

set -x  # Enable debug mode to show each command

# Create temporary files
tmp_dir="/tmp/test_debug"
mkdir -p "$tmp_dir"
results_file="$tmp_dir/test_results.txt"

# Initialize variables
total_tests=0
passed_tests=0
failed_tests=0
error_tests=0
skipped_tests=0

# Simple test function to isolate the issue
debug_test() {
    # Get test statistics
    module_total=0
    module_errors=0 
    module_failures=0
    module_skipped=0
    
    # Try to update counts - this should identify where the issue is
    echo "Updating counts..."
    
    # Check if values are properly set
    echo "module_total: $module_total"
    echo "module_errors: $module_errors"
    
    # This is where the issue likely occurs
    if [ "$module_total" -eq 0 ]; then
        echo "Total is zero"
    fi
    
    # Test arithmetic operations
    local module_passed=0
    if [ "$module_total" -gt 0 ]; then
        echo "Total greater than zero"
        module_passed=$((module_total - module_errors - module_failures - module_skipped))
    fi
    
    # Update statistics
    total_tests=$((total_tests + module_total))
    passed_tests=$((passed_tests + module_passed))
    
    # Print variables
    echo "Final counts:"
    echo "total_tests: $total_tests"
    echo "passed_tests: $passed_tests"
}

# Run the debug function
echo "Starting debug test..."
debug_test
echo "Debug test complete."

# Clean up
rm -rf "$tmp_dir" 