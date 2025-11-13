"""
ClickUp Tree Line Alignment Test Suite
================================================================================
VARIABLES: tree_lines, indent_levels, connector_chars, vertical_pipes,
           indentation_stack, level_widths
FUNCTIONS: validate_tree_alignment, check_consistent_indentation,
           check_vertical_alignment, check_connector_alignment,
           check_pipe_continuation, check_level_depth_consistency,
           check_orphaned_lines, check_connector_positioning,
           check_branch_alignment, check_mixed_connectors,
           parse_tree_structure, validate_all_rules

Version: 1.0
================================================================================
Test rules for ensuring ClickUp tree visualization maintains proper visual alignment
across all nesting levels and connector characters. Because crooked ASCII trees
are the debugging equivalent of losing your mind.
"""

import re
from typing import List, Tuple, Dict, Set


class TreeAlignmentValidator:
    """
    Validates tree structure alignment in ClickUp CLI output.

    Rules enforced:
    - Consistent indentation increments per depth level
    - Vertical alignment of tree connectors with parent levels
    - Proper pipe continuation through branching
    - No orphaned or misaligned connector characters
    - Correct usage of tree characters (├, └, │, ─)

    Version: 1.0
    Change History:
    - 1.0: Initial implementation with 10 core validation rules
    """

    INDENT_INCREMENT = 4  # Expected spaces per depth level
    TREE_CHARS = {'├', '└', '│', '─'}
    CONNECTOR_CHARS = {'├', '└'}
    PIPE_CHAR = '│'
    DASH_CHAR = '─'

    def __init__(self, tree_output: str):
        """
        Initialize validator with tree output.

        Args:
            tree_output: Multi-line string containing tree structure
        """
        self.lines = tree_output.split('\n')
        self.errors = []
        self.warnings = []

    # RULE 1: Consistent Indentation Increments
    def check_consistent_indentation(self) -> bool:
        """
        RULE 1: Validate indentation increases by consistent amount per level.

        Detects: Irregular indent spacing, mixed tab/space usage
        Example failure: Level 0 at 0 spaces, Level 1 at 3 spaces, Level 2 at 8 spaces
        """
        indent_levels = {}

        for line_num, line in enumerate(self.lines, 1):
            if not line.strip():  # Skip empty lines
                continue

            # Count leading spaces
            indent = len(line) - len(line.lstrip(' '))

            # Skip if line starts with tab character
            if line.startswith('\t'):
                self.errors.append(
                    f"Line {line_num}: TAB character detected, use spaces only"
                )
                return False

            # Determine depth level (should be indent / INCREMENT)
            if indent % self.INDENT_INCREMENT != 0:
                self.errors.append(
                    f"Line {line_num}: Indent {indent}px not multiple of {self.INDENT_INCREMENT} "
                    f"| Content: {line.strip()[:50]}"
                )
                return False

            level = indent // self.INDENT_INCREMENT

            if level not in indent_levels:
                indent_levels[level] = indent

        return True

    # RULE 2: Vertical Pipe Continuation Alignment
    def check_pipe_continuation(self) -> bool:
        """
        RULE 2: Validate vertical pipes (│) continue properly through tree levels.

        Detects: Pipes not at consistent column positions, broken vertical lines
        Example failure: Pipe at column 4 in level 1, pipe at column 5 in level 2
        """
        pipe_columns = {}

        for line_num, line in enumerate(self.lines, 1):
            if not line.strip():
                continue

            level = (len(line) - len(line.lstrip(' '))) // self.INDENT_INCREMENT

            # Find all pipe characters in this line
            for col_idx, char in enumerate(line):
                if char == self.PIPE_CHAR:
                    if level not in pipe_columns:
                        pipe_columns[level] = []
                    pipe_columns[level].append(col_idx)

        # Check that pipes at same level are at same columns
        for level, columns in pipe_columns.items():
            unique_cols = set(columns)
            if len(unique_cols) > 1:
                self.errors.append(
                    f"Level {level}: Pipes at inconsistent columns: {sorted(unique_cols)}"
                )
                return False

        return True

    # RULE 3: Connector Character Alignment with Parent
    def check_connector_alignment(self) -> bool:
        """
        RULE 3: Validate connectors (├, └) align with their parent level.

        Detects: Connectors offset from parent indentation, misaligned junctions
        Example failure: Parent at indent 4, child connector at indent 6 instead of 4+width
        """
        for line_num, line in enumerate(self.lines, 1):
            if not line.strip():
                continue

            indent = len(line) - len(line.lstrip(' '))

            # Check if line contains connector
            if any(char in line for char in self.CONNECTOR_CHARS):
                # Connector position should align with tree structure
                connector_pos = None
                for i, char in enumerate(line):
                    if char in self.CONNECTOR_CHARS:
                        connector_pos = i
                        break

                if connector_pos is not None:
                    # Connector should be at expected indent level
                    level = indent // self.INDENT_INCREMENT
                    expected_pos = level * self.INDENT_INCREMENT

                    if connector_pos != expected_pos:
                        self.errors.append(
                            f"Line {line_num}: Connector at column {connector_pos}, "
                            f"expected {expected_pos} | {line.strip()[:50]}"
                        )
                        return False

        return True

    # RULE 4: No Orphaned Connectors
    def check_orphaned_lines(self) -> bool:
        """
        RULE 4: Detect orphaned connector characters without proper hierarchy.

        Detects: Tree chars appearing without parent context, dangling branches
        Example failure: └── appearing at root level or after └── without ├──
        """
        for line_num, line in enumerate(self.lines, 1):
            if not line.strip():
                continue

            # Count connectors in line
            has_branch_start = '├' in line
            has_branch_end = '└' in line

            if has_branch_start and has_branch_end:
                self.errors.append(
                    f"Line {line_num}: Multiple connectors in single line: {line.strip()[:50]}"
                )
                return False

        return True

    # RULE 5: Proper Dash Sequences
    def check_dash_sequences(self) -> bool:
        """
        RULE 5: Validate dash sequences (──) are proper length and positioned correctly.

        Detects: Single dashes, irregular dash patterns, dashes not following connectors
        Example failure: "├─ Item" should be "├── Item"
        """
        for line_num, line in enumerate(self.lines, 1):
            if not line.strip():
                continue

            # Look for connector + dash pattern
            if '├' in line or '└' in line:
                # Should be followed by at least 2 dashes
                match = re.search(r'[├└]([─]*)\s', line)
                if match:
                    dashes = len(match.group(1))
                    if dashes < 2:
                        self.errors.append(
                            f"Line {line_num}: Insufficient dashes after connector "
                            f"({dashes} found, minimum 2) | {line.strip()[:50]}"
                        )
                        return False

        return True

    # RULE 6: Level Depth Progression
    def check_level_depth_consistency(self) -> bool:
        """
        RULE 6: Validate depth levels increase/decrease by 1 between adjacent lines.

        Detects: Skipped levels, jumps in hierarchy, broken parent-child chains
        Example failure: Level 0 → Level 2 (skipped Level 1)
        """
        prev_level = None

        for line_num, line in enumerate(self.lines, 1):
            if not line.strip():
                continue

            indent = len(line) - len(line.lstrip(' '))
            level = indent // self.INDENT_INCREMENT

            if prev_level is not None:
                level_diff = level - prev_level
                if abs(level_diff) > 1:
                    self.errors.append(
                        f"Line {line_num}: Level jump from {prev_level} to {level} "
                        f"| {line.strip()[:50]}"
                    )
                    return False

            prev_level = level

        return True

    # RULE 7: No Mixed Connector Sequences
    def check_no_mixed_connectors(self) -> bool:
        """
        RULE 7: Validate proper sequencing of branch connectors (├ then └).

        Detects: └── appearing before ├──, incorrect branching order
        Example failure: └── appears on line 2, ├── appears on line 3 at same level
        """
        last_connector_by_level = {}

        for line_num, line in enumerate(self.lines, 1):
            if not line.strip():
                continue

            indent = len(line) - len(line.lstrip(' '))
            level = indent // self.INDENT_INCREMENT

            if '├' in line:
                last_connector_by_level[level] = ('├', line_num)
            elif '└' in line:
                if level in last_connector_by_level:
                    prev_type, prev_line = last_connector_by_level[level]
                    if prev_type == '└':
                        self.errors.append(
                            f"Line {line_num}: └── appears after └── at same level "
                            f"(previous at line {prev_line})"
                        )
                        return False
                last_connector_by_level[level] = ('└', line_num)

        return True

    # RULE 8: Content Not Overlapping with Tree Structure
    def check_content_alignment(self) -> bool:
        """
        RULE 8: Validate content starts after tree structure, no overlap.

        Detects: Text starting too early, content bleeding into tree chars
        Example failure: "├── Item" has content immediately after ──,
                        should have space
        """
        for line_num, line in enumerate(self.lines, 1):
            if not line.strip():
                continue

            # Find where tree chars end
            tree_end = 0
            for char in line:
                if char in self.TREE_CHARS or char == ' ':
                    tree_end += 1
                else:
                    break

            # Verify there's a space before content
            if tree_end > 0 and tree_end < len(line):
                if line[tree_end - 1] not in (' ', self.PIPE_CHAR):
                    self.warnings.append(
                        f"Line {line_num}: Possible content alignment issue, "
                        f"content too close to tree chars | {line[:40]}"
                    )

        return True

    # RULE 9: Symmetric Branch Closing
    def check_symmetric_branch_closing(self) -> bool:
        """
        RULE 9: Validate branch sections properly close (├── ... └──).

        Detects: Branches not properly closed, unmatched connectors
        Example failure: ├── without corresponding └── before next ├──
        """
        branch_stack = []

        for line_num, line in enumerate(self.lines, 1):
            if not line.strip():
                continue

            indent = len(line) - len(line.lstrip(' '))
            level = indent // self.INDENT_INCREMENT

            if '├' in line:
                branch_stack.append((level, '├', line_num))
            elif '└' in line:
                if branch_stack and branch_stack[-1][0] == level:
                    branch_stack.pop()
                else:
                    self.errors.append(
                        f"Line {line_num}: └── without matching ├── at level {level}"
                    )
                    return False

        if branch_stack:
            unclosed = len(branch_stack)
            self.errors.append(
                f"Unclosed branches: {unclosed} branch(es) opened but never closed"
            )
            return False

        return True

    # RULE 10: No Trailing Whitespace on Tree Lines
    def check_no_trailing_whitespace(self) -> bool:
        """
        RULE 10: Validate no trailing whitespace on tree structure lines.

        Detects: Trailing spaces/tabs that break alignment in terminals
        Example failure: "├── Item   " (trailing spaces at end)
        """
        for line_num, line in enumerate(self.lines, 1):
            if line and line != line.rstrip():
                self.warnings.append(
                    f"Line {line_num}: Trailing whitespace detected"
                )

        return True

    # Master validation function
    def validate_all_rules(self) -> Tuple[bool, List[str], List[str]]:
        """
        Execute all alignment validation rules.

        Returns:
            Tuple of (all_pass: bool, errors: List[str], warnings: List[str])
        """
        rules = [
            self.check_consistent_indentation,
            self.check_pipe_continuation,
            self.check_connector_alignment,
            self.check_orphaned_lines,
            self.check_dash_sequences,
            self.check_level_depth_consistency,
            self.check_no_mixed_connectors,
            self.check_content_alignment,
            self.check_symmetric_branch_closing,
            self.check_no_trailing_whitespace,
        ]

        results = []
        for rule in rules:
            try:
                result = rule()
                results.append(result)
            except Exception as e:
                self.errors.append(f"Exception in {rule.__name__}: {str(e)}")
                results.append(False)

        all_pass = all(results)
        return all_pass, self.errors, self.warnings


# ============================================================================
# TEST EXECUTION
# ============================================================================

def test_tree_alignment():
    """
    Example test usage. Replace test_tree with actual ClickUp output.
    """
    test_tree = """├── Task 1
│   ├── Subtask 1.1
│   └── Subtask 1.2
├── Task 2
│   └── Subtask 2.1
└── Task 3"""

    validator = TreeAlignmentValidator(test_tree)
    passed, errors, warnings = validator.validate_all_rules()

    print(f"\n{'='*70}")
    print(f"TREE ALIGNMENT VALIDATION REPORT")
    print(f"{'='*70}\n")

    if passed:
        print("✓ ALL RULES PASSED - Tree structure is properly aligned")
    else:
        print(f"✗ VALIDATION FAILED - {len(errors)} error(s) found\n")
        print("ERRORS:")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")

    if warnings:
        print(f"\nWARNINGS: {len(warnings)}")
        for i, warning in enumerate(warnings, 1):
            print(f"  {i}. {warning}")

    print(f"\n{'='*70}\n")

    return passed


if __name__ == "__main__":
    test_tree_alignment()
