#!/usr/bin/env python3
"""
RAC Quality Checker - Identifies common issues in .rac files
Issues checked:
1. Parameters missing `reference:` field
2. Variables missing entity/period/dtype
3. Files missing text: blocks (statute excerpt)
4. Units using old format (should be USD, /1, not currency-USD, rate)
"""

import os
import re
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List

@dataclass
class Issue:
    file: str
    issue_type: str
    details: str
    severity: str  # "error" or "warning"

def check_file(filepath: Path) -> List[Issue]:
    """Check a single RAC file for quality issues."""
    issues = []
    content = filepath.read_text()
    rel_path = str(filepath.relative_to(Path.cwd()))

    # 1. Check for parameters missing reference field
    param_pattern = re.compile(r'^parameter\s+(\w+):', re.MULTILINE)
    ref_pattern = re.compile(r'^\s+reference:', re.MULTILINE)

    for match in param_pattern.finditer(content):
        param_name = match.group(1)
        start = match.start()
        # Find the next parameter or variable or end
        next_block = re.search(r'^(parameter|variable|input)\s+\w+:', content[start+1:], re.MULTILINE)
        end = start + next_block.start() if next_block else len(content)
        block_content = content[start:end]

        if not re.search(r'^\s+reference:', block_content, re.MULTILINE):
            issues.append(Issue(
                file=rel_path,
                issue_type="missing_reference",
                details=f"Parameter '{param_name}' missing reference: field",
                severity="error"
            ))

    # 2. Check for text: block
    if not re.search(r'^text:', content, re.MULTILINE):
        issues.append(Issue(
            file=rel_path,
            issue_type="missing_text_block",
            details="File missing text: block with statute excerpt",
            severity="warning"
        ))

    # 3. Check for old unit formats
    old_units = [
        ('currency-USD', 'USD'),
        ('"rate"', '"/1"'),
        ('"percentage"', '"/1"'),
        ('unit: rate', 'unit: "/1"'),
        ('unit: percentage', 'unit: "/1"'),
    ]
    for old, new in old_units:
        if old in content:
            issues.append(Issue(
                file=rel_path,
                issue_type="old_unit_format",
                details=f"Uses '{old}', should be '{new}'",
                severity="warning"
            ))

    # 4. Check variables missing required fields
    var_pattern = re.compile(r'^variable\s+(\w+):', re.MULTILINE)
    for match in var_pattern.finditer(content):
        var_name = match.group(1)
        start = match.start()
        next_block = re.search(r'^(parameter|variable|input)\s+\w+:', content[start+1:], re.MULTILINE)
        end = start + next_block.start() if next_block else len(content)
        block_content = content[start:end]

        for field in ['entity:', 'period:', 'dtype:']:
            if field not in block_content:
                issues.append(Issue(
                    file=rel_path,
                    issue_type="missing_var_field",
                    details=f"Variable '{var_name}' missing {field}",
                    severity="error"
                ))

    # 5. Check for hardcoded numbers in formulas (excluding 0, 1, -1, 2, 3)
    formula_match = re.search(r'formula:\s*\|([^|]+?)(?=^\w+:|$)', content, re.MULTILINE | re.DOTALL)
    if formula_match:
        formula = formula_match.group(1)
        # Find numbers that aren't 0, 1, -1, 2, 3
        numbers = re.findall(r'(?<![a-zA-Z_])\d+\.?\d*(?![a-zA-Z_])', formula)
        bad_numbers = [n for n in numbers if n not in ['0', '1', '2', '3', '0.0', '1.0', '2.0', '3.0']]
        if bad_numbers:
            issues.append(Issue(
                file=rel_path,
                issue_type="hardcoded_values",
                details=f"Formula contains hardcoded values: {', '.join(bad_numbers[:5])}",
                severity="warning"
            ))

    return issues

def main():
    statute_dir = Path('/Users/maxghenis/CosilicoAI/cosilico-us/statute')
    if not statute_dir.exists():
        print(f"Directory not found: {statute_dir}")
        sys.exit(1)

    all_issues = []
    files_checked = 0

    for rac_file in statute_dir.rglob('*.rac'):
        files_checked += 1
        issues = check_file(rac_file)
        all_issues.extend(issues)

    # Group by issue type
    by_type = {}
    for issue in all_issues:
        by_type.setdefault(issue.issue_type, []).append(issue)

    print(f"\n{'='*60}")
    print(f"RAC Quality Check - {files_checked} files checked")
    print(f"{'='*60}\n")

    for issue_type, issues in sorted(by_type.items()):
        print(f"\n## {issue_type.upper()} ({len(issues)} files)")
        print("-" * 40)
        for issue in issues[:20]:  # Limit to first 20
            print(f"  {issue.file}: {issue.details}")
        if len(issues) > 20:
            print(f"  ... and {len(issues) - 20} more")

    print(f"\n{'='*60}")
    print(f"SUMMARY:")
    print(f"  Total files: {files_checked}")
    print(f"  Total issues: {len(all_issues)}")
    for issue_type, issues in sorted(by_type.items()):
        print(f"    {issue_type}: {len(issues)}")
    print(f"{'='*60}")

    # Return files needing fixes by issue type
    return by_type

if __name__ == '__main__':
    main()
