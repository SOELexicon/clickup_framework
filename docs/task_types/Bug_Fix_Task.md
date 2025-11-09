# Bug Fix Task

## Overview

*   **Bug ID:** \[BUG-XXX\]
*   **Severity:** \[Critical | High | Medium | Low\]
*   **Affected Component:** \[Component/Module name\]
*   **Environment:** \[Production | Staging | Development\]
*   **Reported Date:** \[Date\]
*   **Reporter:** \[Name/Role\]

## Bug Description

### Summary

\[One-sentence description of the bug\]

### Detailed Description

\[Comprehensive description of incorrect behavior\]

### Steps to Reproduce

1. \[First step\]
2. \[Second step\]
3. \[Third step\]

**Expected Behavior:** \[What should happen\]

**Actual Behavior:** \[What actually happens\]

## Impact Analysis

### User Impact

*   **Affected Users:** \[Number/percentage\]
*   **Severity:** \[Blocker | Major inconvenience | Minor issue\]
*   **Workaround Available:** \[Yes/No\]

### System Impact

*   **Performance degradation:** \[Yes/No\]
*   **Data integrity issues:** \[Yes/No\]
*   **Security implications:** \[Yes/No\]

## Technical Details

### Error Messages

\[Paste relevant error messages and stack traces\]

### Environment Details

*   **OS:** \[Operating system\]
*   **Browser:** \[Browser + version\]
*   **Framework Version:** \[Version\]
*   **Database Version:** \[Version\]

### Affected Code

*   **File:** \[path/to/file\]
*   **Function/Method:** \[FunctionName\]
*   **Line Number(s):** \[Lines\]

## Root Cause Analysis

### Investigation Findings

\[Detailed explanation of what's causing the bug\]

### Contributing Factors

*   \[Factor 1\]
*   \[Factor 2\]

### Why This Wasn't Caught Earlier

\[Analysis of why existing tests/reviews didn't catch this\]

## Proposed Solution

### Fix Approach

\[Detailed description of how to fix the bug\]

### Code Changes Required

**\[File/Component\]:**

*   \[Change description\]
*   Impact: \[What this changes\]

### Alternative Solutions Considered

*   **\[Alternative 1\]:** \[Why not chosen\]
*   **\[Alternative 2\]:** \[Why not chosen\]

## Testing Strategy

### Verification Steps

*   \[Step to verify fix\]
*   \[Additional verification\]

### Regression Testing

- [ ] Test original reproduction steps
- [ ] Test related functionality
- [ ] Run full test suite
- [ ] Check edge cases

### Test Cases to Add

*   \[New test case 1\]
*   \[New test case 2\]

## Acceptance Criteria

- [ ] Bug no longer reproducible
- [ ] No new bugs introduced
- [ ] Tests added to prevent regression
- [ ] Code reviewed
- [ ] Documentation updated (if needed)
- [ ] Root cause documented
- [ ] Deployed to staging and verified
- [ ] Performance impact measured (if applicable)

## Deployment Considerations

**Risk Assessment:** \[Low | Medium | High\]

### Rollback Plan

\[How to rollback if fix causes issues\]

### Monitoring

*   **Metrics to watch:** \[Specific metrics\]
*   **Alert thresholds:** \[What indicates failure\]