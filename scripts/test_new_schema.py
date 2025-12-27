#!/usr/bin/env python3
"""Tests for new .rac schema format."""

import pytest
import yaml
import re
from pathlib import Path
from typing import Any

# New schema: named declarations with inline params/tests
VALID_TOP_LEVEL = {"text", "parameter", "variable", "input", "enum", "function"}

# Parameter attributes
VALID_PARAM_ATTRS = {
    "description", "unit", "source", "values", "label", "reference",
    "thresholds", "amounts"  # for schedule-type params
}

# Variable attributes
VALID_VAR_ATTRS = {
    "imports", "entity", "period", "dtype", "unit", "label", "description",
    "formula", "default", "defined_for", "tests", "versions"
}

# Test/example attributes
VALID_TEST_ATTRS = {"name", "inputs", "expect", "outputs", "period", "notes"}


def parse_rac_file(content: str) -> dict:
    """Parse new .rac format into structured dict."""
    result = {
        "text": None,
        "parameters": {},
        "variables": {},
        "inputs": {},
    }

    lines = content.split('\n')
    current_block = None
    current_name = None
    current_content = []
    indent_level = 0

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip comments and empty lines at top level
        if not stripped or stripped.startswith('#'):
            i += 1
            continue

        # Check for text: block
        if stripped.startswith('text:'):
            if '"""' in stripped:
                # Multi-line text
                text_content = []
                if stripped.count('"""') == 2:
                    # Single line: text: """..."""
                    result["text"] = stripped.split('"""')[1]
                else:
                    # Multi-line starts
                    i += 1
                    while i < len(lines) and '"""' not in lines[i]:
                        text_content.append(lines[i])
                        i += 1
                    result["text"] = '\n'.join(text_content)
            i += 1
            continue

        # Check for parameter declaration
        param_match = re.match(r'^parameter\s+(\w+):', stripped)
        if param_match:
            current_block = "parameter"
            current_name = param_match.group(1)
            result["parameters"][current_name] = {}
            i += 1
            continue

        # Check for variable declaration
        var_match = re.match(r'^variable\s+(\w+):', stripped)
        if var_match:
            current_block = "variable"
            current_name = var_match.group(1)
            result["variables"][current_name] = {}
            i += 1
            continue

        # Check for input declaration
        input_match = re.match(r'^input\s+(\w+):', stripped)
        if input_match:
            current_block = "input"
            current_name = input_match.group(1)
            result["inputs"][current_name] = {}
            i += 1
            continue

        i += 1

    return result


def validate_new_format(content: str) -> list[str]:
    """Validate .rac file against new schema. Returns list of errors."""
    errors = []
    lines = content.split('\n')

    in_multiline_string = False
    in_formula = False
    seen_text = False

    for lineno, line in enumerate(lines, 1):
        # Track multiline strings
        if '"""' in line:
            count = line.count('"""')
            if count == 1:
                in_multiline_string = not in_multiline_string
            continue
        if in_multiline_string:
            continue

        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue

        # Check indentation
        indent = len(line) - len(line.lstrip())

        # Top-level declarations (no indent)
        if indent == 0:
            in_formula = False

            # text: block
            if stripped.startswith('text:'):
                if seen_text:
                    errors.append(f"Line {lineno}: duplicate text: block")
                seen_text = True
                continue

            # Named declarations
            decl_match = re.match(r'^(parameter|variable|input|enum|function)\s+(\w+):', stripped)
            if decl_match:
                continue

            # Unknown top-level
            word_match = re.match(r'^(\w+)', stripped)
            if word_match:
                word = word_match.group(1)
                if word not in {'parameter', 'variable', 'input', 'enum', 'function', 'text'}:
                    errors.append(f"Line {lineno}: unknown top-level declaration '{word}'")

        # Inside a block (indented)
        else:
            # Check for formula: which starts code block
            if stripped.startswith('formula:'):
                in_formula = True
                continue

            # Inside formula, anything goes
            if in_formula:
                continue

            # Attribute check - look for word:
            attr_match = re.match(r'^(\w+):', stripped)
            if attr_match:
                attr = attr_match.group(1)
                # These are known attributes across all block types
                known_attrs = VALID_PARAM_ATTRS | VALID_VAR_ATTRS | VALID_TEST_ATTRS
                # Also allow date-like keys for parameter values
                if not re.match(r'^\d{4}-\d{2}-\d{2}$', attr) and attr not in known_attrs:
                    # Could be a nested structure key, allow it for now
                    pass

    return errors


# ============================================================================
# TESTS
# ============================================================================

class TestNewFormatValidation:
    """Test validation of new .rac format."""

    def test_minimal_valid_file(self):
        """Minimal valid file with just a parameter and variable."""
        content = '''
text: """Section 2017(a) - Value of Allotment"""

parameter contribution_rate:
  description: "Household contribution rate"
  values:
    1977-01-01: 0.30

variable snap_allotment:
  entity: Household
  period: Month
  dtype: Money
  formula: income * contribution_rate
'''
        errors = validate_new_format(content)
        assert errors == [], f"Unexpected errors: {errors}"

    def test_parameter_with_metadata(self):
        """Parameter with full metadata."""
        content = '''
parameter max_allotment:
  description: "Maximum monthly SNAP allotment"
  unit: USD
  source: "USDA FNS"
  reference: "7 USC 2017(a)"
  values:
    2024-10-01: 292
    2023-10-01: 291
'''
        errors = validate_new_format(content)
        assert errors == []

    def test_variable_with_imports_and_tests(self):
        """Variable with imports and inline tests."""
        content = '''
variable snap_benefit:
  imports: [7/2014#household_size, 7/2014/e#snap_net_income]
  entity: Household
  period: Month
  dtype: Money
  formula: |
    if not snap_eligible:
      return 0
    return max_allotment - net_income * 0.3
  tests:
    - inputs: {household_size: 1, snap_net_income: 0}
      expect: 291
    - inputs: {household_size: 4, snap_net_income: 500}
      expect: 823
'''
        errors = validate_new_format(content)
        assert errors == []

    def test_rejects_old_format_block_style(self):
        """Old format with parameters: block should be rejected."""
        content = '''
parameters:
  contribution_rate:
    2023-10-01: 0.30

variable snap_allotment:
  entity: Household
  formula: income * contribution_rate
'''
        errors = validate_new_format(content)
        assert any("parameters" in e for e in errors), "Should reject 'parameters:' block"

    def test_rejects_old_format_variables_block(self):
        """Old format with variables: block should be rejected."""
        content = '''
variables:
  snap_allotment:
    entity: Household
    formula: income * 0.3
'''
        errors = validate_new_format(content)
        assert any("variables" in e for e in errors), "Should reject 'variables:' block"


class TestImportSyntax:
    """Test new import syntax: path#variable [as alias]."""

    def test_basic_import(self):
        """Basic import without alias."""
        content = '''
variable snap_benefit:
  imports: [7/2014#household_size]
  entity: Household
  formula: household_size * 100
'''
        errors = validate_new_format(content)
        assert errors == []

    def test_import_with_alias(self):
        """Import with alias."""
        content = '''
variable snap_benefit:
  imports:
    - 7/2014#household_size as hh_size
  entity: Household
  formula: hh_size * 100
'''
        errors = validate_new_format(content)
        assert errors == []

    def test_multiple_imports(self):
        """Multiple imports from different files."""
        content = '''
variable snap_allotment:
  imports:
    - 7/2014#household_size
    - 7/2014/e#snap_net_income
    - 7/2014/a#snap_eligible
  entity: Household
  formula: |
    if not snap_eligible:
      return 0
    return max_allotment[household_size] - snap_net_income * 0.3
'''
        errors = validate_new_format(content)
        assert errors == []


class TestInlineTests:
    """Test inline test syntax."""

    def test_simple_test(self):
        """Simple test with inputs/expect."""
        content = '''
variable doubled:
  entity: Person
  formula: value * 2
  tests:
    - inputs: {value: 5}
      expect: 10
'''
        errors = validate_new_format(content)
        assert errors == []

    def test_named_test(self):
        """Test with name."""
        content = '''
variable doubled:
  entity: Person
  formula: value * 2
  tests:
    - name: "Double five"
      inputs: {value: 5}
      expect: 10
'''
        errors = validate_new_format(content)
        assert errors == []

    def test_test_with_period(self):
        """Test specifying a period."""
        content = '''
variable benefit:
  entity: Household
  period: Month
  formula: max_benefit - income * 0.3
  tests:
    - name: "2024 calculation"
      period: 2024-01
      inputs: {income: 500}
      expect: 823
'''
        errors = validate_new_format(content)
        assert errors == []


class TestFullFileExample:
    """Test complete file examples."""

    def test_snap_allotment_new_format(self):
        """Full SNAP allotment file in new format."""
        content = '''
# 7/2017/a.rac - SNAP Allotment

text: """
(a) Value of allotment
The value of the allotment shall be equal to the cost of the
thrifty food plan reduced by 30 percent of household income.
"""

parameter max_allotment_schedule:
  description: "Maximum monthly SNAP allotment by household size"
  unit: USD
  source: "USDA FNS annual memo"
  values:
    2024-10-01: [292, 536, 768, 975, 1158, 1390, 1536, 1756]
    2023-10-01: [291, 535, 766, 973, 1155, 1386, 1532, 1751]

parameter contribution_rate:
  description: "Household contribution as share of net income"
  source: "7 USC 2017(a)"
  values:
    1977-01-01: 0.30

parameter minimum_benefit:
  description: "Minimum benefit for 1-2 person households"
  unit: USD
  values:
    2024-10-01: 23
    2023-10-01: 23

variable snap_max_allotment:
  imports: [7/2014#household_size]
  entity: Household
  period: Month
  dtype: Money
  formula: max_allotment_schedule[household_size - 1]
  tests:
    - inputs: {household_size: 1}
      expect: 291
    - inputs: {household_size: 4}
      expect: 973

variable snap_expected_contribution:
  imports: [7/2014/e#snap_net_income]
  entity: Household
  period: Month
  dtype: Money
  formula: snap_net_income * contribution_rate
  tests:
    - inputs: {snap_net_income: 500}
      expect: 150

variable snap_allotment:
  imports: [7/2014/a#snap_eligible]
  entity: Household
  period: Month
  dtype: Money
  formula: |
    if not snap_eligible:
      return 0
    calculated = snap_max_allotment - snap_expected_contribution
    return max(calculated, minimum_benefit)
  tests:
    - name: "Family of 4, $500 income"
      inputs: {household_size: 4, snap_net_income: 500, snap_eligible: true}
      expect: 823
    - name: "Not eligible"
      inputs: {snap_eligible: false}
      expect: 0
'''
        errors = validate_new_format(content)
        assert errors == [], f"Errors: {errors}"


class TestTopLevelImportsFormat:
    """Test old format with top-level imports (no variable keyword)."""

    def test_parse_top_level_imports(self):
        """Parse file with top-level imports: block."""
        from scripts.convert_to_new_format import parse_old_rac

        content = '''
# 20 USC 1070a - Expected Family Contribution

imports:
  pell_grant_formula: statute/20/1070a/formula_type
  head_contribution: statute/20/1070a/head_contribution

entity Person
period Year
dtype Money
label "Expected Family Contribution"

formula:
  return head_contribution

default 0
'''
        result = parse_old_rac(content)
        # Should create an anonymous variable with the imports
        assert len(result["variables"]) == 1
        var = result["variables"][0]
        assert var["attributes"]["entity"] == "Person"
        assert len(var["imports"]) == 2

    def test_convert_top_level_imports_file(self):
        """Convert file with top-level imports to new format."""
        from scripts.convert_to_new_format import convert_to_new_format

        old_content = '''
# 20 USC 1070a - EFC

imports:
  head_contribution: statute/20/1070a/head_contribution
  agi: statute/26/62/a/adjusted_gross_income

entity Person
period Year
dtype Money
unit "USD"
label "Expected Family Contribution"

formula:
  return max(0, head_contribution)

default 0
'''
        new_content = convert_to_new_format(old_content, {})
        # Should have variable with imports in new format
        assert "variable" in new_content
        assert "imports:" in new_content
        assert "entity: Person" in new_content

    def test_anonymous_var_gets_filename(self):
        """Anonymous variables should get name from filename."""
        from scripts.convert_to_new_format import convert_to_new_format

        old_content = '''
# Test file

entity Person
period Year
dtype Money

formula:
  return 100
'''
        # Pass filename hint to converter
        new_content = convert_to_new_format(old_content, {}, filename="efc")
        assert "variable efc:" in new_content


class TestParamDataEdgeCases:
    """Test edge cases in parameter data structures."""

    def test_amounts_as_list(self):
        """Parameters with amounts as list (not dict) should be handled."""
        from scripts.convert_to_new_format import convert_to_new_format

        old_content = '''
variable test_var:
  entity TaxUnit
  period Year

  parameters:
    rate: parameters#gov.foo.rate

  formula:
    return rate
'''
        # Amounts is a list instead of dict
        params_lookup = {
            "gov.foo.rate": {
                "description": "Some rate",
                "amounts": [0.5, 0.6, 0.7]  # List, not dict
            }
        }
        new_content = convert_to_new_format(old_content, params_lookup)
        # Should handle list gracefully
        assert "parameter rate:" in new_content
        assert "values:" in new_content


class TestConverterParsing:
    """Test parsing of old format files."""

    def test_parse_old_format_with_variable_keyword(self):
        """Parse old format that uses 'variable name:' syntax."""
        from scripts.convert_to_new_format import parse_old_rac

        content = '''
# Comment
variable snap_allotment:
  entity Household
  period Month
  dtype Money

  imports:
    household_size: statute/7/2014#household_size

  parameters:
    rate: parameters#gov.usda.fns.snap.rate

  formula:
    return household_size * rate

  default 0
'''
        result = parse_old_rac(content)
        assert len(result["variables"]) == 1
        assert result["variables"][0]["name"] == "snap_allotment"
        assert result["variables"][0]["attributes"]["entity"] == "Household"

    def test_parse_old_format_multi_variable_no_keyword(self):
        """Parse old format with multiple variables without 'variable' keyword."""
        from scripts.convert_to_new_format import parse_old_rac

        content = '''
# CTC file with multiple variables
imports:
  earned_income: statute/26/32#earned_income

# First variable
entity TaxUnit
period Year
dtype Money
label "First Var"

formula:
  return earned_income * 0.15

# Second variable
entity TaxUnit
period Year
dtype Money
label "Second Var"

formula:
  return first_var * 2
'''
        # This format is trickier - variables aren't named explicitly
        # The converter should detect this pattern
        result = parse_old_rac(content)
        # For now, this may not parse correctly - that's the test


class TestConverterTransform:
    """Test conversion from old to new format."""

    def test_convert_simple_variable(self):
        """Convert a simple variable with parameters."""
        from scripts.convert_to_new_format import convert_to_new_format

        old_content = '''
# 7 USC 2017(a) - Test
variable snap_rate:
  entity Household
  period Month
  dtype Money
  description "Test variable"

  parameters:
    rate: parameters#gov.usda.fns.snap.rate

  formula:
    return income * rate

  default 0
'''
        params_lookup = {
            "gov.usda.fns.snap.rate": {
                "description": "SNAP rate",
                "values": {"2024-01-01": 0.30}
            }
        }

        new_content = convert_to_new_format(old_content, params_lookup)

        # Should have parameter declaration
        assert "parameter rate:" in new_content
        assert "2024-01-01: 0.3" in new_content

        # Should have variable
        assert "variable snap_rate:" in new_content
        assert "entity: Household" in new_content

    def test_convert_preserves_imports(self):
        """Imports should be converted to new syntax."""
        from scripts.convert_to_new_format import convert_to_new_format

        old_content = '''
variable test_var:
  entity Person
  period Year
  dtype Money

  imports:
    foo: statute/26/32#foo
    bar: statute/7/2014/e#bar

  formula:
    return foo + bar
'''
        new_content = convert_to_new_format(old_content, {})

        # Should have new import syntax
        assert "imports:" in new_content
        # The exact format may vary, but should reference the paths


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_file(self):
        """Empty file should produce minimal valid output."""
        errors = validate_new_format("")
        # Empty file is technically valid (no violations)
        assert errors == []

    def test_file_with_only_comments(self):
        """File with only comments should be valid."""
        content = '''
# This is a comment
# Another comment
'''
        errors = validate_new_format(content)
        assert errors == []

    def test_multiline_formula(self):
        """Multi-line formula with complex logic."""
        content = '''
variable complex_calc:
  entity: TaxUnit
  period: Year
  dtype: Money
  formula: |
    if income > threshold:
      rate = high_rate
    else:
      rate = low_rate

    base = income * rate

    for deduction in deductions:
      base = base - deduction

    return max(0, base)
'''
        errors = validate_new_format(content)
        assert errors == []

    def test_versioned_variable(self):
        """Variable with temporal versions."""
        content = '''
variable ctc_refundable:
  entity: TaxUnit
  period: Year
  dtype: Money

  versions:
    2018-01-01:
      enacted_by: "P.L. 115-97"
      parameters:
        threshold: 2500
      formula: |
        return (earned_income - threshold) * 0.15

    2026-01-01:
      reverts_to: 2001-01-01
'''
        errors = validate_new_format(content)
        assert errors == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
