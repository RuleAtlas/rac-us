#!/usr/bin/env python3
"""Migrate .rac files to unified syntax.

Transformations:
1. Strip keyword prefixes: `parameter name:` -> `name:`, `variable name:` -> `name:`, `input name:` -> `name:`
2. Convert values: blocks to from entries
3. Convert formula: | blocks to from entries
4. Convert text: blocks to docstrings
5. Extract tests: to .rac.test files
"""

import re
import os
import sys
from pathlib import Path


def find_earliest_date(content):
    """Find the earliest date in parameter values: blocks."""
    dates = re.findall(r'(\d{4}-\d{2}-\d{2}):', content)
    if dates:
        return sorted(dates)[0]
    return "2013-01-01"


def migrate_file(filepath):
    """Migrate a single .rac file. Returns (new_content, test_content_or_None)."""
    with open(filepath) as f:
        content = f.read()

    lines = content.split('\n')
    earliest_date = find_earliest_date(content)

    new_lines = []
    test_entries = []  # list of (variable_name, test_lines)

    i = 0
    while i < len(lines):
        line = lines[i]

        # Rule 4: Convert text: blocks to docstrings
        # Handle text: """  (triple-quote block)
        if re.match(r'^text:\s*"""', line):
            # Multi-line triple-quote text block
            # Check if it's on the same line closing
            rest = line[line.index('"""') + 3:]
            if '"""' in rest:
                # Single-line triple quote: text: """content"""
                inner = rest[:rest.index('"""')]
                new_lines.append('"""')
                new_lines.append(inner)
                new_lines.append('"""')
                i += 1
                continue
            # Multi-line: text: """
            new_lines.append('"""')
            i += 1
            while i < len(lines):
                if '"""' in lines[i]:
                    # End of triple-quote block
                    before_close = lines[i][:lines[i].index('"""')]
                    if before_close.strip():
                        new_lines.append(before_close.rstrip())
                    new_lines.append('"""')
                    i += 1
                    break
                else:
                    new_lines.append(lines[i])
                    i += 1
            continue

        # Handle text: | (pipe block)
        if re.match(r'^text:\s*\|', line):
            new_lines.append('"""')
            i += 1
            # Read indented block
            while i < len(lines) and (lines[i].startswith('  ') or lines[i].strip() == ''):
                if lines[i].strip() == '' and (i + 1 >= len(lines) or not lines[i + 1].startswith('  ')):
                    break
                # Remove exactly 2 spaces of indentation
                if lines[i].startswith('  '):
                    new_lines.append(lines[i][2:])
                else:
                    new_lines.append(lines[i])
                i += 1
            new_lines.append('"""')
            continue

        # Handle text: "single line"
        m = re.match(r'^text:\s*"([^"]*)"$', line)
        if m:
            new_lines.append('"""')
            new_lines.append(m.group(1))
            new_lines.append('"""')
            i += 1
            continue

        # Rule 1: Strip keyword prefixes for parameter, variable, input
        m_param = re.match(r'^parameter\s+(\w+):\s*$', line)
        m_var = re.match(r'^variable\s+(\w+):\s*$', line)
        m_input = re.match(r'^input\s+(\w+):\s*$', line)

        if m_param:
            name = m_param.group(1)
            new_lines.append(f'{name}:')
            i += 1
            # Process parameter body - look for values: block
            while i < len(lines):
                pline = lines[i]
                # Check if we're still in the parameter block (indented)
                if pline.strip() == '':
                    new_lines.append(pline)
                    i += 1
                    continue
                if not pline.startswith('  '):
                    break

                # Rule 2: Convert values: to from entries
                if re.match(r'^\s+values:\s*$', pline):
                    i += 1
                    # Read all date: value pairs
                    while i < len(lines) and re.match(r'^\s{4,}', lines[i]):
                        date_val = lines[i].strip()
                        m_dv = re.match(r'(\d{4}-\d{2}-\d{2}):\s*(.*)', date_val)
                        if m_dv:
                            new_lines.append(f'  from {m_dv.group(1)}: {m_dv.group(2)}')
                        else:
                            new_lines.append(lines[i])
                        i += 1
                    continue
                else:
                    new_lines.append(pline)
                    i += 1
            continue

        if m_var:
            name = m_var.group(1)
            new_lines.append(f'{name}:')
            i += 1
            # Process variable body - look for formula: and tests:
            while i < len(lines):
                vline = lines[i]
                if vline.strip() == '':
                    new_lines.append(vline)
                    i += 1
                    continue
                if not vline.startswith('  '):
                    break

                # Rule 3: Convert formula: | to from entry
                if re.match(r'^\s+formula:\s*\|', vline):
                    i += 1
                    formula_lines = []
                    while i < len(lines):
                        fline = lines[i]
                        # Formula block continues while indented by 4+ spaces
                        if fline.startswith('    ') or (fline.strip() == '' and i + 1 < len(lines) and lines[i + 1].startswith('    ')):
                            if fline.startswith('    '):
                                formula_lines.append(fline[4:])  # Remove 4-space indent
                            else:
                                formula_lines.append('')
                            i += 1
                        else:
                            break
                    # Write as from entry
                    new_lines.append(f'  from {earliest_date}:')
                    for fl in formula_lines:
                        new_lines.append(f'    {fl}' if fl else '')
                    continue

                # Rule 5: Extract tests:
                if re.match(r'^\s+tests:\s*$', vline):
                    i += 1
                    test_lines_raw = []
                    while i < len(lines) and (lines[i].startswith('    ') or lines[i].strip() == ''):
                        if lines[i].strip() == '' and (i + 1 >= len(lines) or not lines[i + 1].startswith('    ')):
                            break
                        test_lines_raw.append(lines[i])
                        i += 1
                    test_entries.append((name, test_lines_raw))
                    continue

                new_lines.append(vline)
                i += 1
            continue

        if m_input:
            name = m_input.group(1)
            new_lines.append(f'{name}:')
            i += 1
            # Process input body unchanged
            while i < len(lines):
                iline = lines[i]
                if iline.strip() == '':
                    new_lines.append(iline)
                    i += 1
                    continue
                if not iline.startswith('  '):
                    break
                new_lines.append(iline)
                i += 1
            continue

        # Default: pass through
        new_lines.append(line)
        i += 1

    # Build test file content
    test_content = None
    if test_entries:
        test_lines = []
        for var_name, raw_lines in test_entries:
            test_lines.append(f'{var_name}:')
            for tl in raw_lines:
                # Remove 2 spaces from indentation (was 4-space in variable body, make it 2-space at top level)
                if tl.startswith('    '):
                    test_lines.append(tl[2:])
                else:
                    test_lines.append(tl)
            test_lines.append('')
        test_content = '\n'.join(test_lines).rstrip() + '\n'

    new_content = '\n'.join(new_lines)
    # Clean up multiple blank lines
    new_content = re.sub(r'\n{3,}', '\n\n', new_content)
    # Ensure trailing newline
    if not new_content.endswith('\n'):
        new_content += '\n'

    return new_content, test_content


def process_inputs_file(filepath):
    """Process input files that use a different format (no block structure, flat fields)."""
    with open(filepath) as f:
        content = f.read()

    # These input files don't use `input name:` pattern - they use flat format
    # Check if they have the standard `input name:` pattern
    if re.search(r'^input\s+\w+:', content, re.MULTILINE):
        return migrate_file(filepath)

    # Otherwise return as-is (different format)
    return content, None


def main():
    base_dir = Path('/Users/maxghenis/RulesFoundation/rac-us')

    # Find all .rac files
    rac_files = sorted(base_dir.glob('**/*.rac'))

    migrated = 0
    tests_created = 0
    skipped = 0

    for filepath in rac_files:
        # Skip .rac.test files
        if '.rac.test' in str(filepath):
            continue

        print(f"Processing: {filepath.relative_to(base_dir)}")

        try:
            new_content, test_content = migrate_file(filepath)

            # Write migrated file
            with open(filepath, 'w') as f:
                f.write(new_content)
            migrated += 1

            # Write test file if needed
            if test_content:
                test_path = str(filepath) + '.test'
                with open(test_path, 'w') as f:
                    f.write(test_content)
                tests_created += 1
                print(f"  -> Created test file: {Path(test_path).relative_to(base_dir)}")
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()
            skipped += 1

    print(f"\nDone! Migrated: {migrated}, Tests created: {tests_created}, Skipped: {skipped}")


if __name__ == '__main__':
    main()
