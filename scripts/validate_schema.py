#!/usr/bin/env python3
"""Validate .rac files only use whitelisted attributes and valid values."""

import re
import sys
from pathlib import Path

# Valid values for schema fields
VALID_ENTITIES = {
    # Core tax/benefit units
    "Person", "TaxUnit", "Household", "Family",
    # Benefit program units
    "TanfUnit", "SnapUnit", "SPMUnit",
    # Business/asset entities (for corporate/capital gains)
    "Corporation", "Business", "Asset",
}
VALID_PERIODS = {"Year", "Month", "Week", "Day"}
VALID_DTYPES = {"Money", "Rate", "Boolean", "Integer", "Count", "String", "Decimal"}  # Enum[...] handled specially

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
    # Multi-variable file constructs (followed by identifier)
    "variable",
    "input",
    "enum",
    "values",
    "parameter",
    # Helper functions (followed by identifier)
    "function",
    # Raw statute text
    "text",
    # Test definitions
    "tests",
}

# Keywords that can appear in formula/function bodies (not attributes)
CODE_KEYWORDS = {
    "if", "else", "return", "for", "break",
    "and", "or", "not", "in",
}

# Patterns for value extraction
# Entity and dtype appear in variable/input declarations
ENTITY_PATTERN = re.compile(r"^\s*entity:\s*(\w+)")
# Period type declarations only - exclude date-like values (2024-01, etc.)
PERIOD_PATTERN = re.compile(r"^\s*period:\s*(Year|Month|Week|Day|[A-Z][a-z]+)$")
DTYPE_PATTERN = re.compile(r"^\s*dtype:\s*(\w+)")
# Parameter declarations
PARAMETER_PATTERN = re.compile(r"^parameter\s+(\w+):")
# Legislation-specific naming anti-patterns (should be time-varying instead)
LEGISLATION_ANTIPATTERNS = [
    (r"pre_tcja|post_tcja|tcja_", "TCJA"),
    (r"pre_aca|post_aca|aca_", "ACA"),
    (r"pre_arpa|post_arpa|arpa_", "ARPA"),
    (r"pre_arra|post_arra|arra_", "ARRA"),
    (r"pre_tra|post_tra|tra97_|tra01_", "TRA"),
    (r"_2017_|_2018_|_2019_|_2020_|_2021_|_2022_|_2023_|_2024_", "year"),
]
FORMULA_START = re.compile(r"^\s*formula:\s*\|")
FORMULA_LINE = re.compile(r"^\s{4,}")  # Indented lines in formula

# Hardcoded literals - only -1, 0, 1, 2, 3 allowed in formulas
ALLOWED_INTEGERS = {-1, 0, 1, 2, 3}
LITERAL_PATTERN = re.compile(
    r"""
    (?<![a-zA-Z_\d])  # Not preceded by identifier char or digit
    (
        \d+\.\d+      # Float like 0.075
        |
        [4-9]         # Single digit 4-9
        |
        [1-9]\d+      # Multi-digit starting with 1-9 (10+)
    )
    (?![a-zA-Z_\d])   # Not followed by identifier char or digit
    """,
    re.VERBOSE,
)

def validate_file(filepath: Path) -> list[str]:
    """Validate a single .rac file."""
    errors = []
    content = filepath.read_text()
    lines = content.split('\n')

    in_code_section = False  # Inside formula/function/defined_for
    in_formula = False  # Inside formula block specifically
    in_multiline_string = False  # Inside """ block

    for lineno, line in enumerate(lines, 1):
        # Handle multiline strings (text: """ blocks)
        if '"""' in line:
            count = line.count('"""')
            if count == 1:
                in_multiline_string = not in_multiline_string
            # If count == 2, it opens and closes on same line
            continue
        if in_multiline_string:
            continue

        # Track formula blocks for literal checking
        if FORMULA_START.match(line):
            in_formula = True
            continue
        elif in_formula and not FORMULA_LINE.match(line) and line.strip():
            in_formula = False

        # Check for hardcoded literals in formulas
        if in_formula:
            # Strip comments and strings before checking
            code_line = re.sub(r"#.*$", "", line)  # Remove comments
            code_line = re.sub(r"['\"].*?['\"]", "", code_line)  # Remove strings

            for match in LITERAL_PATTERN.finditer(code_line):
                literal = match.group(1)
                # Check if it's an allowed value (integers -1,0,1,2,3 or their float equivalents)
                try:
                    val = float(literal)
                    if val in {-1.0, 0.0, 1.0, 2.0, 3.0}:
                        continue
                except ValueError:
                    pass
                errors.append(f"{filepath}:{lineno}: hardcoded literal '{literal}' - use a parameter instead")

        # Skip empty lines
        if not line.strip():
            continue

        # Skip comment lines
        stripped = line.strip()
        if stripped.startswith('#'):
            continue

        # Check parameter names for legislation-specific anti-patterns
        param_match = PARAMETER_PATTERN.match(stripped)
        if param_match:
            param_name = param_match.group(1)
            for pattern, legislation in LEGISLATION_ANTIPATTERNS:
                if re.search(pattern, param_name, re.IGNORECASE):
                    errors.append(
                        f"{filepath}:{lineno}: parameter '{param_name}' references {legislation} - "
                        f"use time-varying values instead (e.g., 2017-12-15: new_value)"
                    )

        # Validate entity values
        entity_match = ENTITY_PATTERN.match(line)
        if entity_match:
            entity = entity_match.group(1)
            if entity not in VALID_ENTITIES:
                errors.append(f"{filepath}:{lineno}: invalid entity '{entity}' (must be one of: {sorted(VALID_ENTITIES)})")

        # Validate period values
        period_match = PERIOD_PATTERN.match(line)
        if period_match:
            period = period_match.group(1)
            if period not in VALID_PERIODS:
                errors.append(f"{filepath}:{lineno}: invalid period '{period}' (must be one of: {sorted(VALID_PERIODS)})")

        # Validate dtype values
        dtype_match = DTYPE_PATTERN.match(line)
        if dtype_match:
            dtype = dtype_match.group(1)
            if dtype not in VALID_DTYPES and not dtype.startswith("Enum"):
                errors.append(f"{filepath}:{lineno}: invalid dtype '{dtype}' (must be one of: {sorted(VALID_DTYPES)} or Enum[...])")

        # Calculate indentation
        indent = len(line) - len(line.lstrip())

        # Only check lines with no indentation (top-level declarations)
        if indent > 0:
            continue

        # Check for named variable/input/function pattern: "variable name:" or "function name(...):"
        named_match = re.match(r'^(variable|input|function|enum)\s+([a-z_][a-z0-9_]*)', stripped)
        if named_match:
            attr = named_match.group(1)
            if attr == "function":
                in_code_section = True
            if attr not in ALLOWED_ATTRIBUTES:
                errors.append(f"{filepath}:{lineno}: forbidden attribute '{attr}'")
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
