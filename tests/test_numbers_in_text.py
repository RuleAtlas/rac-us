"""
Validate that every numeric parameter value in a .rac file appears
in the source statute text block (the triple-quoted \"\"\" section).

Numbers like 1000 can appear as "1,000" or "$1,000" in the text.
Small allowed literals (-1, 0, 1, 2, 3) are excluded.
Dates (YYYY-MM-DD) in `from:` lines are excluded.
"""

import glob
import os
import re
import pytest

RAC_ROOT = os.path.join(os.path.dirname(__file__), "..", "statute")

# Numbers that are allowed as DSL literals (not from statute)
ALLOWED_LITERALS = {"-1", "0", "1", "2", "3"}


def extract_text_block(content: str) -> str:
    """Extract the triple-quoted statute text block."""
    match = re.search(r'"""(.*?)"""', content, re.DOTALL)
    return match.group(1) if match else ""


def extract_parameter_numbers(content: str) -> list[tuple[str, int, str]]:
    """
    Extract numeric values from parameter `from YYYY-MM-DD: <value>` lines.

    Returns list of (number_str, line_number, line_text).
    Skips formula lines (containing operators, function calls, variables).
    """
    results = []
    in_text_block = False

    for i, line in enumerate(content.splitlines(), 1):
        stripped = line.strip()

        # Track text block boundaries
        if '"""' in stripped:
            in_text_block = not in_text_block
            continue
        if in_text_block:
            continue

        # Skip comments
        if stripped.startswith("#"):
            continue

        # Match parameter value lines: "from YYYY-MM-DD: <value>"
        param_match = re.match(r"from\s+\d{4}-\d{2}-\d{2}:\s*(.+)", stripped)
        if not param_match:
            continue

        value_part = param_match.group(1).strip()

        # Skip if it's a formula (contains variables, operators, function calls)
        if any(
            kw in value_part
            for kw in [
                "return",
                "if ",
                "else",
                "min(",
                "max(",
                "=",
                "+",
                "-",
                "*",
                "/",
                "not ",
                "and ",
                "or ",
            ]
        ):
            continue

        # Extract pure numeric value (possibly negative, possibly decimal)
        num_match = re.match(r"^(-?\d+\.?\d*)\s*(?:#.*)?$", value_part)
        if num_match:
            num_str = num_match.group(1)
            if num_str not in ALLOWED_LITERALS:
                results.append((num_str, i, stripped))

    return results


def number_in_text(num_str: str, text: str) -> bool:
    """
    Check if a number appears in the text, handling common formatting.

    1000 matches: "1,000", "$1,000", "1000"
    0.075 matches: "0.075", ".075", "7.5 percent", "7.5%"
    1.33 matches: "133 percent", "133%"
    0.5 matches: "1/2"
    """
    # Direct match
    if num_str in text:
        return True

    try:
        num = float(num_str)
    except ValueError:
        return False

    # Try with comma formatting (e.g. 1000 → 1,000)
    if num == int(num):
        formatted = f"{int(num):,}"
        if formatted in text:
            return True

    # Try as percentage substring (0.075 → "7.5" anywhere in text)
    if 0 < abs(num) < 1:
        pct = num * 100
        pct_str = f"{pct:g}"  # Remove trailing zeros
        if pct_str in text:
            return True

    # Try "X percent" or "X%" patterns (handles 1.33 → "133 percent")
    pct = num * 100
    pct_str = f"{pct:g}"
    if re.search(rf"\b{re.escape(pct_str)}\s*(?:percent|%)", text):
        return True
    # Also check "X.0 percent" patterns (e.g. "150.0 percent")
    pct_str_1d = f"{pct:.1f}"
    if re.search(rf"\b{re.escape(pct_str_1d)}\s*(?:percent|%)", text):
        return True

    # Try matching common fractions in text (e.g. "1/2" → 0.5)
    common_fractions = {
        0.5: r"\b1/2\b", 0.25: r"\b1/4\b", 0.75: r"\b3/4\b",
        0.333: r"\b1/3\b", 0.667: r"\b2/3\b",
    }
    for frac_val, frac_pattern in common_fractions.items():
        if abs(num - frac_val) < 0.01 and re.search(frac_pattern, text):
            return True

    # Fraction words (e.g. "one-half" → 0.5, "two-thirds" → 0.667)
    fraction_words = {
        0.5: [r"\bhalf\b", r"\bone-half\b"],
        0.333: [r"\bone-third\b"],
        0.667: [r"\btwo-thirds\b"],
        0.25: [r"\bone-fourth\b", r"\bone-quarter\b"],
        0.75: [r"\bthree-fourths\b", r"\bthree-quarters\b"],
    }
    for frac_val, patterns in fraction_words.items():
        if abs(num - frac_val) < 0.01:
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return True

    # Number words (e.g. "six" → 6, "twenty-five" → 25)
    number_words = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
        "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
        "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
        "nineteen": 19, "twenty": 20, "twenty-five": 25, "thirty": 30,
        "forty": 40, "fifty": 50, "sixty": 60, "sixty-five": 65,
        "seventy": 70, "eighty": 80, "ninety": 90, "one hundred": 100,
    }
    if num == int(num):
        int_num = int(num)
        for word, val in number_words.items():
            if val == int_num and re.search(rf"\b{word}\b", text, re.IGNORECASE):
                return True

    return False


def find_rac_files() -> list[str]:
    """Find all .rac files under statute/."""
    return sorted(glob.glob(os.path.join(RAC_ROOT, "**/*.rac"), recursive=True))


def check_file(filepath: str) -> list[str]:
    """Check a single .rac file. Returns list of error messages."""
    with open(filepath) as f:
        content = f.read()

    text = extract_text_block(content)
    if not text:
        return []  # No text block — skip (some files may not have one)

    numbers = extract_parameter_numbers(content)
    errors = []

    for num_str, line_num, line_text in numbers:
        if not number_in_text(num_str, text):
            rel_path = os.path.relpath(filepath, os.path.join(RAC_ROOT, ".."))
            errors.append(
                f"{rel_path}:{line_num}: parameter value {num_str} "
                f"not found in statute text"
            )

    return errors


class TestNumbersInText:
    """Every numeric parameter value must appear in the source statute text."""

    def test_all_parameter_numbers_appear_in_text(self):
        files = find_rac_files()
        assert files, "No .rac files found"

        all_errors = []
        for f in files:
            all_errors.extend(check_file(f))

        if all_errors:
            msg = f"\n\n{len(all_errors)} parameter values not found in statute text:\n"
            for e in all_errors:
                msg += f"  {e}\n"
            pytest.fail(msg)
