#!/usr/bin/env python3
"""
Auto-fix missing reference: fields in RAC file parameters.
Derives reference from filepath (e.g., statute/26/32.rac -> "26 USC 32")
"""

import os
import re
from pathlib import Path

def derive_reference(filepath: Path) -> str:
    """Derive statute reference from filepath."""
    # Get relative path from statute dir
    parts = filepath.parts
    try:
        statute_idx = parts.index('statute')
        relevant = parts[statute_idx + 1:]  # Skip 'statute'
    except ValueError:
        return ""

    if not relevant:
        return ""

    title = relevant[0]  # e.g., "26", "7", "42"

    # Build section reference
    section_parts = []
    for part in relevant[1:]:
        # Remove .rac extension
        part = part.replace('.rac', '')
        section_parts.append(part)

    if not section_parts:
        return f"{title} USC"

    # Format as "26 USC 32(a)(1)" style
    section = section_parts[0]
    subsections = section_parts[1:]

    ref = f"{title} USC {section}"
    if subsections:
        ref += f"({')('.join(subsections)})"

    return ref

def add_reference_to_params(filepath: Path) -> bool:
    """Add reference: field to parameters missing it. Returns True if changes made."""
    content = filepath.read_text()
    original = content
    reference = derive_reference(filepath)

    if not reference:
        return False

    # Find all parameter blocks that don't have reference:
    param_pattern = re.compile(
        r'^(parameter\s+(\w+):\s*\n)'
        r'((?:[ \t]+(?!reference:)[^\n]*\n)*)',
        re.MULTILINE
    )

    def add_ref(match):
        param_decl = match.group(1)  # "parameter name:\n"
        param_name = match.group(2)
        body = match.group(3)

        # Check if reference already exists in body
        if 'reference:' in body:
            return match.group(0)

        # Find indentation from first line of body
        indent = '  '  # Default 2 spaces
        first_line = body.lstrip('\n').split('\n')[0] if body.strip() else ''
        if first_line:
            indent_match = re.match(r'^(\s+)', first_line)
            if indent_match:
                indent = indent_match.group(1)

        # Insert reference after description if exists, else at start
        if 'description:' in body:
            # Find where description line ends
            desc_match = re.search(r'(description:[^\n]*\n)', body)
            if desc_match:
                insert_pos = desc_match.end()
                new_body = body[:insert_pos] + f'{indent}reference: "{reference}"\n' + body[insert_pos:]
                return param_decl + new_body

        # Insert at start of body
        return param_decl + f'{indent}reference: "{reference}"\n' + body

    content = param_pattern.sub(add_ref, content)

    if content != original:
        filepath.write_text(content)
        return True
    return False

def main():
    statute_dir = Path('/Users/maxghenis/CosilicoAI/cosilico-us/statute')
    fixed_count = 0
    files_fixed = []

    for rac_file in statute_dir.rglob('*.rac'):
        if add_reference_to_params(rac_file):
            rel_path = rac_file.relative_to(Path.cwd())
            files_fixed.append(str(rel_path))
            fixed_count += 1

    print(f"Files with references added ({fixed_count}):")
    for f in sorted(files_fixed)[:50]:
        print(f"  {f}")
    if fixed_count > 50:
        print(f"  ... and {fixed_count - 50} more")

    print(f"\nTotal files fixed: {fixed_count}")

if __name__ == '__main__':
    main()
