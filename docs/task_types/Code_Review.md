# Code Review

## Overview

*   **Review Type:** \[Pull Request | Merge Request | Code Audit\]
*   **Repository:** \[Repo name\]
*   **Branch:** \[Branch name\]
*   **Pull Request:** \[#PR-NUMBER\]
*   **Author:** \[Developer name\]
*   **Reviewer:** \[Your name\]

## Review Scope

*   **Changed Files:** \[Number\]
*   **Lines Added:** \[Number\]
*   **Lines Removed:** \[Number\]

### Components Affected

*   \[Component 1\]
*   \[Component 2\]

## Review Objectives

### Focus Areas

*   Code correctness
*   Performance implications
*   Security vulnerabilities
*   Code style and standards
*   Test coverage
*   Documentation
*   Architecture alignment

## Review Checklist

### Functionality

- [ ] Code does what it's supposed to do
- [ ] Edge cases handled
- [ ] Error handling implemented
- [ ] Input validation present
- [ ] No obvious bugs

### Code Quality

- [ ] Code is readable and maintainable
- [ ] Functions/methods are appropriately sized
- [ ] Naming conventions followed
- [ ] Comments explain "why" not "what"
- [ ] No commented-out code left behind
- [ ] No debugging statements remaining
- [ ] No hardcoded values (use constants/config)

### Architecture & Design

- [ ] Follows established patterns
- [ ] No architectural violations
- [ ] Appropriate abstractions
- [ ] Separation of concerns maintained
- [ ] DRY principle followed (no duplication)
- [ ] SOLID principles considered

### Testing

- [ ] Unit tests added/updated
- [ ] Tests actually test what they claim to test
- [ ] Test coverage adequate
- [ ] Integration tests added (if needed)
- [ ] All tests pass
- [ ] Test names are descriptive

### Security

- [ ] No SQL injection vulnerabilities
- [ ] No XSS vulnerabilities
- [ ] Authentication/authorization checks
- [ ] Sensitive data handled properly
- [ ] Dependencies up to date
- [ ] No secrets in code

### Performance

- [ ] No unnecessary database queries
- [ ] Efficient algorithms used
- [ ] Proper indexing considered
- [ ] Caching strategy appropriate
- [ ] No memory leaks

### Documentation

- [ ] Public APIs documented
- [ ] Complex logic explained
- [ ] README updated (if needed)
- [ ] Changelog updated
- [ ] API docs updated (if needed)

## Findings

### Critical Issues (Must fix before merge)

**\[Issue description\]**

*   **Location:** \[file:line\]
*   **Problem:** \[Detailed explanation\]
*   **Suggested fix:** \[How to resolve\]

### Important Issues (Should fix before merge)

**\[Issue description\]**

*   \[Details\]

### Minor Issues (Nice to have)

**\[Issue description\]**

*   \[Details\]

### Questions

*   \[Question about approach/decision\]
*   \[Clarification needed\]

### Positive Feedback

*   \[Well-implemented aspect 1\]
*   \[Clever solution to problem\]

## Recommendations

### Immediate Actions

*   \[Fix critical issue 1\]
*   \[Fix critical issue 2\]

### Follow-up Tasks

*   \[Create task for refactoring\]
*   \[Schedule performance testing\]
*   \[Update documentation separately\]

## Review Decision

**Status:** \[Approve | Request Changes | Comment\]

### Summary

\[Overall assessment of the change\]

### Approval Conditions (if Request Changes)

*   \[Condition 1\]
*   \[Condition 2\]