#!/bin/bash

# Unit Test Runner with Statistics
# This script runs all unit tests in the project and provides detailed statistics

# Function to display help message
display_help() {
    echo "ClickUp JSON Manager Test Runner"
    echo ""
    echo "Usage: $0 [OPTIONS] [TEST_TARGET]"
    echo ""
    echo "Options:"
    echo "  --create-tasks          Create ClickUp tasks for test failures"
    echo "  --template FILE         Specify the ClickUp JSON template file"
    echo "                          Default: 000_clickup_tasks_template.json"
    echo "  --folder NAME           Specify the ClickUp folder name"
    echo "                          Default: Testing"
    echo "  --list NAME             Specify the ClickUp list name"
    echo "                          Default: Refactor Testing"
    echo "  --parent-task NAME      Specify a parent task for all test failure tasks"
    echo "  --pattern PATTERN       Specify test file pattern"
    echo "                          Default: test_*.py"
    echo "  --help                  Display this help message"
    echo ""
    echo "Examples:"
    echo "  $0                      Run all tests"
    echo "  $0 tests/unit           Run tests in the tests/unit directory"
    echo "  $0 tests/test_file.py   Run a specific test file"
    echo "  $0 --create-tasks       Run all tests and create tasks for failures"
    echo ""
    exit 0
}

# Parse command line arguments
CREATE_TASKS=false
TEMPLATE_FILE="000_clickup_tasks_template.json"
CLICKUP_FOLDER="Testing"
CLICKUP_LIST="Refactor Testing"
CLICKUP_PARENT_TASK=""
TEST_PATTERN="test_*.py"

# Process command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --help)
            display_help
            ;;
        --create-tasks)
            CREATE_TASKS=true
            ;;
        --template)
            TEMPLATE_FILE="$2"
            shift
            ;;
        --folder)
            CLICKUP_FOLDER="$2"
            shift
            ;;
        --list)
            CLICKUP_LIST="$2"
            shift
            ;;
        --parent-task)
            CLICKUP_PARENT_TASK="$2"
            shift
            ;;
        --pattern)
            TEST_PATTERN="$2"
            shift
            ;;
        *)
            # If it's a test file or directory, use it
            if [ -f "$1" ] || [ -d "$1" ]; then
                TEST_TARGET="$1"
            else
                echo "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
            fi
            ;;
    esac
    shift
done

# Colors for output formatting
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Show the command settings if creating tasks
if [ "$CREATE_TASKS" = true ]; then
    echo -e "${BOLD}${BLUE}Test Runner Configuration:${NC}"
    echo -e "${CYAN}Creating tasks for test failures: ${GREEN}Yes${NC}"
    echo -e "${CYAN}Template file: ${NC}${TEMPLATE_FILE}"
    echo -e "${CYAN}ClickUp folder: ${NC}${CLICKUP_FOLDER}"
    echo -e "${CYAN}ClickUp list: ${NC}${CLICKUP_LIST}"
    if [ -n "$CLICKUP_PARENT_TASK" ]; then
        echo -e "${CYAN}Parent task: ${NC}${CLICKUP_PARENT_TASK}"
    fi
    echo ""
fi

# Print header
echo -e "${BOLD}${BLUE}=========================================${NC}"
echo -e "${BOLD}${BLUE}       ClickUp JSON Manager Tests        ${NC}"
echo -e "${BOLD}${BLUE}=========================================${NC}"
echo ""

# Define variables for statistics
total_tests=0
passed_tests=0
failed_tests=0
skipped_tests=0
error_tests=0
total_time=0

# Create temporary directory for test results
tmp_dir=$(mktemp -d)
results_file="$tmp_dir/test_results.txt"
coverage_file="$tmp_dir/coverage.xml"
failed_tests_file="$tmp_dir/failed_tests.txt"

# Check if coverage is installed
if command -v coverage &> /dev/null; then
    has_coverage=true
else
    has_coverage=false
    echo -e "${YELLOW}Coverage module not found. Test coverage statistics will not be available.${NC}"
    echo -e "${YELLOW}Install with: pip install coverage${NC}"
    echo ""
fi

# Function to run tests in a module
run_module_tests() {
    local module=$1
    local module_name=$(basename "$module")
    
    echo -e "${CYAN}Running tests in ${module_name}...${NC}"
    
    # Measure execution time
    start_time=$(date +%s.%N)
    
    # Set PYTHONPATH to include current directory
    export PYTHONPATH=$(pwd)
    
    if [ "$has_coverage" = true ]; then
        # Run tests with coverage
        coverage run --source=refactor -m unittest discover -s "$module" -p "$TEST_PATTERN" > "$results_file" 2>&1
    else
        # Run tests without coverage
        python3 -m unittest discover -s "$module" -p "$TEST_PATTERN" > "$results_file" 2>&1
    fi
    
    exit_code=$?
    end_time=$(date +%s.%N)
    
    # Calculate execution time
    module_time=$(echo "$end_time - $start_time" | bc)
    total_time=$(echo "$total_time + $module_time" | bc)
    
    # Get test result statistics
    local module_total=0
    module_total=$(grep -c "test_" "$results_file" || true)
    if [ -z "$module_total" ]; then
        module_total=0
    fi
    
    local module_errors=0
    module_errors=$(grep -c "ERROR:" "$results_file" || true)
    if [ -z "$module_errors" ]; then
        module_errors=0
    fi
    
    local module_failures=0
    module_failures=$(grep -c "FAIL:" "$results_file" || true)
    if [ -z "$module_failures" ]; then
        module_failures=0
    fi
    
    local module_skipped=0
    module_skipped=$(grep -c "skipped=" "$results_file" || true)
    if [ -z "$module_skipped" ]; then
        module_skipped=0
    fi
    
    # If no tests were found, try another approach
    if [ "$module_total" -eq 0 ]; then
        local alternate_count
        alternate_count=$(python3 -m unittest discover -s "$module" -p "$TEST_PATTERN" -v 2>&1 | grep -c "test_" || true)
        if [ -n "$alternate_count" ] && [ "$alternate_count" -gt 0 ]; then
            module_total=$alternate_count
        fi
    fi
    
    # Calculate module_passed
    local module_passed=0
    if [ "$module_total" -gt 0 ]; then
        module_passed=$((module_total - module_errors - module_failures - module_skipped))
        if [ "$module_passed" -lt 0 ]; then
            module_passed=0
        fi
    fi
    
    # Update global statistics
    total_tests=$((total_tests + module_total))
    passed_tests=$((passed_tests + module_passed))
    failed_tests=$((failed_tests + module_failures))
    error_tests=$((error_tests + module_errors))
    skipped_tests=$((skipped_tests + module_skipped))
    
    # Display module results
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✓ All tests passed in ${module_name} (${module_total} tests, $(printf "%.2f" $module_time)s)${NC}"
    else
        echo -e "${RED}✗ Tests failed in ${module_name} (${module_passed}/${module_total} passed, $(printf "%.2f" $module_time)s)${NC}"
        # Save failed tests for later reporting
        grep -A 1 "FAIL:\|ERROR:" "$results_file" >> "$failed_tests_file"
    fi
    
    # Generate coverage report if available
    if [ "$has_coverage" = true ]; then
        coverage xml -o "$coverage_file" > /dev/null 2>&1
    fi
}

# Function to run individual test file
run_test_file() {
    local test_file=$1
    local file_name=$(basename "$test_file")
    
    echo -e "${CYAN}Running test file ${file_name}...${NC}"
    
    # Measure execution time
    start_time=$(date +%s.%N)
    
    # Set PYTHONPATH to include current directory
    export PYTHONPATH=$(pwd)
    
    if [ "$has_coverage" = true ]; then
        # Run tests with coverage
        coverage run --source=refactor -m unittest "$test_file" > "$results_file" 2>&1
    else
        # Run tests without coverage
        python3 -m unittest "$test_file" > "$results_file" 2>&1
    fi
    
    exit_code=$?
    end_time=$(date +%s.%N)
    
    # Calculate execution time
    module_time=$(echo "$end_time - $start_time" | bc)
    total_time=$(echo "$total_time + $module_time" | bc)
    
    # Get test result statistics by counting patterns in the output
    local module_total=0
    module_total=$(grep -c "test_" "$results_file" || true)
    if [ -z "$module_total" ]; then
        module_total=0
    fi
    
    local module_errors=0
    module_errors=$(grep -c "ERROR:" "$results_file" || true)
    if [ -z "$module_errors" ]; then
        module_errors=0
    fi
    
    local module_failures=0
    module_failures=$(grep -c "FAIL:" "$results_file" || true)
    if [ -z "$module_failures" ]; then
        module_failures=0
    fi
    
    local module_skipped=0
    module_skipped=$(grep -c "skipped=" "$results_file" || true)
    if [ -z "$module_skipped" ]; then
        module_skipped=0
    fi
    
    # If no tests were found, try running with -v for more verbose output
    if [ "$module_total" -eq 0 ]; then
        local alternate_count
        alternate_count=$(python3 -m unittest "$test_file" -v 2>&1 | grep -c "test_" || true)
        if [ -n "$alternate_count" ] && [ "$alternate_count" -gt 0 ]; then
            module_total=$alternate_count
        fi
    fi
    
    # Calculate module_passed
    local module_passed=0
    if [ "$module_total" -gt 0 ]; then
        module_passed=$((module_total - module_errors - module_failures - module_skipped))
        if [ "$module_passed" -lt 0 ]; then
            module_passed=0
        fi
    fi
    
    # Update global statistics
    total_tests=$((total_tests + module_total))
    passed_tests=$((passed_tests + module_passed))
    failed_tests=$((failed_tests + module_failures))
    error_tests=$((error_tests + module_errors))
    skipped_tests=$((skipped_tests + module_skipped))
    
    # Display module results
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✓ All tests passed in ${file_name} (${module_total} tests, $(printf "%.2f" $module_time)s)${NC}"
    else
        echo -e "${RED}✗ Tests failed in ${file_name} (${module_passed}/${module_total} passed, $(printf "%.2f" $module_time)s)${NC}"
        # Save failed tests for later reporting
        grep -A 1 "FAIL:\|ERROR:" "$results_file" >> "$failed_tests_file"
    fi
}

# Find all test directories
echo -e "${BLUE}Discovering test modules...${NC}"

# If a specific test target is provided
if [ -n "$TEST_TARGET" ]; then
    if [ -f "$TEST_TARGET" ]; then
        # Run a specific test file
        run_test_file "$TEST_TARGET"
    elif [ -d "$TEST_TARGET" ]; then
        # Run tests in a specific directory
        run_module_tests "$TEST_TARGET"
    else
        echo -e "${RED}Invalid test target: $TEST_TARGET${NC}"
        exit 1
    fi
else
    # Find all test directories
    test_dirs=$(find . -type d -path "*/tests*" | grep -v "__pycache__" | sort)

    if [ -z "$test_dirs" ]; then
        echo -e "${YELLOW}No test directories found.${NC}"
        echo -e "${YELLOW}Looking for individual test files...${NC}"
        test_files=$(find . -name "$TEST_PATTERN" | grep -v "__pycache__" | sort)
        
        if [ -z "$test_files" ]; then
            echo -e "${RED}No test files found. Exiting.${NC}"
            exit 1
        else
            # Run each test file individually
            for test_file in $test_files; do
                run_test_file "$test_file"
            done
        fi
    else
        # First check for individual test files
        test_files=$(find . -name "$TEST_PATTERN" | grep -v "__pycache__" | sort)
        
        if [ -n "$test_files" ]; then
            echo -e "${BLUE}Running individual test files...${NC}"
            for test_file in $test_files; do
                run_test_file "$test_file"
            done
        fi
        
        # Then run directory-based tests
        echo -e "${BLUE}Running directory-based tests...${NC}"
        for dir in $test_dirs; do
            if [ -d "$dir" ]; then
                run_module_tests "$dir"
            fi
        done
    fi
fi

echo ""
echo -e "${BOLD}${BLUE}=========================================${NC}"
echo -e "${BOLD}${BLUE}            Test Summary                 ${NC}"
echo -e "${BOLD}${BLUE}=========================================${NC}"
echo ""

# Calculate percentages
pass_percent=0.0
fail_percent=0.0
error_percent=0.0
skip_percent=0.0

if [ "$total_tests" -gt 0 ]; then
    pass_percent=$(echo "scale=1; $passed_tests * 100 / $total_tests" | bc)
    fail_percent=$(echo "scale=1; $failed_tests * 100 / $total_tests" | bc)
    error_percent=$(echo "scale=1; $error_tests * 100 / $total_tests" | bc)
    skip_percent=$(echo "scale=1; $skipped_tests * 100 / $total_tests" | bc)
fi

# Print test summary
echo "Test Results:"
echo "  Total tests:  $total_tests"
echo "  Passed:       $passed_tests ($pass_percent%)"
echo "  Failed:       $failed_tests ($fail_percent%)"
echo "  Errors:       $error_tests ($error_percent%)"
echo "  Skipped:      $skipped_tests ($skip_percent%)"
echo ""

echo "Timing:"
echo "  Total execution time: ${total_time}s"

# Print average time if tests were executed
if [ "$total_tests" -gt 0 ]; then
    avg_time=$(echo "scale=3; $total_time / $total_tests" | bc)
    echo "  Average time per test: ${avg_time}s"
else
    echo "  No tests found to calculate average time."
fi

echo ""

# Show appropriate message based on test results
if [ "$total_tests" -eq 0 ]; then
    echo "No tests were found or executed!"
elif [ "$failed_tests" -eq 0 ] && [ "$error_tests" -eq 0 ]; then
    echo "All tests passed successfully!"
else
    echo "Some tests failed or had errors. Check the output above for details."
fi

# Display coverage information if available
if [ "$has_coverage" = true ]; then
    echo ""
    echo -e "${BOLD}Coverage:${NC}"
    
    if [ -f "$coverage_file" ]; then
        coverage_percent=$(grep "line-rate=" "$coverage_file" | head -1 | grep -oP 'line-rate="\K[^"]+')
        if [ -n "$coverage_percent" ]; then
            # Convert decimal to percentage
            coverage_percent=$(echo "scale=1; ${coverage_percent}*100" | bc)
            echo -e "  Line coverage: ${coverage_percent}%"
            
            # Print coverage by module
            echo -e "  ${BOLD}Coverage by module:${NC}"
            grep "class filename" "$coverage_file" | grep -oP 'filename="\K[^"]+' | while read -r file; do
                module_coverage=$(grep -A1 "filename=\"$file\"" "$coverage_file" | grep -oP 'line-rate="\K[^"]+' | head -1)
                if [ -n "$module_coverage" ]; then
                    module_coverage=$(echo "scale=1; ${module_coverage}*100" | bc)
                    echo -e "    $(basename "$file"): ${module_coverage}%"
                fi
            done
        else
            echo -e "  ${YELLOW}Unable to parse coverage data${NC}"
        fi
    else
        echo -e "  ${YELLOW}No coverage data available${NC}"
    fi
fi

# Display failed tests in detail
if [ -f "$failed_tests_file" ] && [ -s "$failed_tests_file" ]; then
    echo ""
    echo -e "${BOLD}${RED}Failed Tests:${NC}"
    cat "$failed_tests_file" | sed 's/^/  /'
    
    # Create ClickUp tasks for failures if requested
    if [ "$CREATE_TASKS" = true ] && [ "$failed_tests" -gt 0 -o "$error_tests" -gt 0 ]; then
        echo ""
        echo -e "${BOLD}${BLUE}Creating ClickUp Tasks for Test Failures...${NC}"
        
        FAILURE_TASK_CREATOR="$(dirname "$0")/tools/test_failure_tasks.py"
        
        if [ ! -f "$FAILURE_TASK_CREATOR" ]; then
            echo -e "${RED}Error: Test failure task creator script not found at $FAILURE_TASK_CREATOR${NC}"
            echo -e "${YELLOW}Make sure the script exists and is executable${NC}"
        else
            # Build the command
            CMD="python3 $FAILURE_TASK_CREATOR $failed_tests_file --template $TEMPLATE_FILE --folder \"$CLICKUP_FOLDER\" --list \"$CLICKUP_LIST\""
            
            # Add parent task if provided
            if [ -n "$CLICKUP_PARENT_TASK" ]; then
                CMD="$CMD --parent \"$CLICKUP_PARENT_TASK\""
            fi
            
            # Execute the command
            echo -e "${CYAN}Executing: $CMD${NC}"
            eval "$CMD"
            
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}Task creation completed successfully${NC}"
            else
                echo -e "${RED}Task creation failed${NC}"
            fi
        fi
    fi
fi

# Clean up temporary directory
rm -rf "$tmp_dir"

# Exit with appropriate status code
if [ "$failed_tests" -gt 0 ] || [ "$error_tests" -gt 0 ]; then
    echo ""
    echo -e "${RED}Tests completed with failures or errors.${NC}"
    exit 1
else
    echo ""
    if [ "$total_tests" -eq 0 ]; then
        echo -e "${YELLOW}No tests were found or executed!${NC}"
        exit 0
    else
        echo -e "${GREEN}All tests passed successfully!${NC}"
        exit 0
    fi
fi 