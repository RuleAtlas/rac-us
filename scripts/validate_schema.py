#!/usr/bin/env python3
"""Validate .rac files only use whitelisted attributes."""

import re
import sys
from pathlib import Path

# WHITELIST: Only these top-level attributes are allowed
ALLOWED_ATTRIBUTES = {
    # Required variable attributes
    "entity",
    "period",
    "dtype",
    # Optional variable attributes
    "unit",
    "label",
    "description",
    "formula",
    "default",
    "defined_for",
    # Block declarations
    "imports",
    "parameters",
    "exports",
    "examples",
    # Multi-variable file constructs
    "variable",
    "input",
    "enum",
    "values",
    # Helper functions
    "function",
}

# Keywords that can appear in formula/function bodies (not attributes)
CODE_KEYWORDS = {
    "if", "else", "return", "for", "break",
    "and", "or", "not", "in",
}

def validate_file(filepath: Path) -> list[str]:
    """Validate a single .rac file."""
    errors = []
    content = filepath.read_text()
    lines = content.split('\n')

    in_code_section = False  # Inside formula/function/defined_for

    for lineno, line in enumerate(lines, 1):
        # Skip empty lines
        if not line.strip():
            continue

        # Skip comment lines
        stripped = line.strip()
        if stripped.startswith('#'):
            continue

        # Calculate indentation
        indent = len(line) - len(line.lstrip())

        # Only check lines with no indentation (top-level declarations)
        if indent > 0:
            continue

        # Check for attribute pattern: word followed by space, colon, or end of line
        match = re.match(r'^([a-z_]+)(:|\s|$)', stripped)
        if not match:
            # Line doesn't start with a word - could be assignment inside code
            # e.g., "tax = tax + ..." - these should only appear in code sections
            if in_code_section:
                continue
            # Check if it's an assignment (variable = ...)
            if re.match(r'^[a-z_]+\s*=', stripped):
                if not in_code_section:
                    errors.append(f"{filepath}:{lineno}: assignment outside code block")
            continue

        attr = match.group(1)

        # Check if this is a code keyword (part of formula/function body)
        if attr in CODE_KEYWORDS:
            if not in_code_section:
                errors.append(f"{filepath}:{lineno}: code keyword '{attr}' outside code block")
            continue

        # Check if entering a code section
        if attr in {"formula", "function", "defined_for"}:
            in_code_section = True
            if attr not in ALLOWED_ATTRIBUTES:
                errors.append(f"{filepath}:{lineno}: forbidden attribute '{attr}'")
            continue

        # If we hit a known attribute, we're leaving any code section
        if attr in ALLOWED_ATTRIBUTES:
            in_code_section = False
            continue

        # Unknown attribute - check if we're in code section (might be a variable name)
        if in_code_section:
            # Inside code, unknown words are likely variable assignments
            continue

        # Not in code, not a known attribute - this is a violation
        errors.append(f"{filepath}:{lineno}: forbidden attribute '{attr}'")

    return errors

def main():
    statute_dir = Path(__file__).parent.parent / "statute"

    if not statute_dir.exists():
        print(f"Error: {statute_dir} not found")
        sys.exit(1)

    all_errors = []
    files_checked = 0

    for rac_file in statute_dir.rglob("*.rac"):
        files_checked += 1
        errors = validate_file(rac_file)
        all_errors.extend(errors)

    print(f"Checked {files_checked} .rac files")
    print(f"Allowed attributes: {sorted(ALLOWED_ATTRIBUTES)}")

    if all_errors:
        print(f"\n❌ Found {len(all_errors)} violations:\n")
        for error in sorted(all_errors):
            print(f"  {error}")
        sys.exit(1)
    else:
        print("\n✅ All files pass schema validation")
        sys.exit(0)

if __name__ == "__main__":
    main()
