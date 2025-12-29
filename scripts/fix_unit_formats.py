#!/usr/bin/env python3
"""
Auto-fix old unit formats in RAC files.
Replacements:
- currency-USD -> USD
- "rate" -> "/1"
- "percentage" -> "/1"
- unit: rate -> unit: "/1"
- unit: percentage -> unit: "/1"
"""

import os
import re
from pathlib import Path

def fix_file(filepath: Path) -> bool:
    """Fix unit formats in a single file. Returns True if changes made."""
    content = filepath.read_text()
    original = content

    # Unit format fixes
    replacements = [
        (r'currency-USD', 'USD'),
        (r'unit:\s*rate\b', 'unit: "/1"'),
        (r'unit:\s*percentage\b', 'unit: "/1"'),
        (r'unit:\s+"rate"', 'unit: "/1"'),
        (r'unit:\s+"percentage"', 'unit: "/1"'),
    ]

    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)

    if content != original:
        filepath.write_text(content)
        return True
    return False

def main():
    statute_dir = Path('/Users/maxghenis/CosilicoAI/cosilico-us/statute')
    fixed_count = 0

    for rac_file in statute_dir.rglob('*.rac'):
        if fix_file(rac_file):
            rel_path = rac_file.relative_to(Path.cwd())
            print(f"Fixed: {rel_path}")
            fixed_count += 1

    print(f"\nTotal files fixed: {fixed_count}")

if __name__ == '__main__':
    main()
