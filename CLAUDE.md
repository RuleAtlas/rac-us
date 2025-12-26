# cosilico-us

**THE home for US federal tax and benefit statute encodings.**

All US-specific .rac files belong here, NOT in cosilico-engine.

## Structure

Files organized under `statute/` by title and section:

```
cosilico-us/
├── statute/               # All enacted statutes
│   ├── 26/               # Title 26 (IRC)
│   │   ├── 24/          # § 24 - Child Tax Credit
│   │   ├── 32/          # § 32 - EITC
│   │   ├── 36B/         # § 36B - Premium Tax Credit
│   │   ├── 62/          # § 62 - AGI
│   │   └── 63/          # § 63 - Standard Deduction
│   │
│   └── 7/               # Title 7 (Agriculture)
│       └── 2017/        # § 2017 - SNAP
│
├── irs/                   # IRS guidance (Rev. Procs, etc.)
└── usda/fns/              # USDA Food & Nutrition Service guidance
```

## Filepath = Citation

The filepath IS the legal citation. No redundant reference fields.

```
statute/26/32/c/2/A.rac  →  26 USC § 32(c)(2)(A)
statute/7/2017/a.rac     →  7 USC § 2017(a)
```

## .rac File Format

Self-contained files with statute text, parameters, variables, and tests:

```yaml
# 26 USC Section 62(a)(7) - IRA Deduction

text: """
(7) Retirement savings.—The deduction allowed by section 219...
"""

imports:
  filing_status: statute/26/1/filing_status
  adjusted_gross_income: statute/26/62/a/adjusted_gross_income

parameters:
  contribution_limit:
    2024-01-01: 7000
  catch_up_amount:
    2024-01-01: 1000

input traditional_ira_contributions:
  entity Person
  period Year
  dtype Money
  default 0

variable ira_deduction:
  entity Person
  period Year
  dtype Money
  formula:
    return min(traditional_ira_contributions, contribution_limit)

examples:
  - name: "Full contribution"
    inputs:
      person:
        traditional_ira_contributions: 7000
    outputs:
      ira_deduction: 7000
```

## Schema Whitelist

Only these top-level attributes are allowed:

```
# REQUIRED for variables
entity    # Person, TaxUnit, Household, State, Family
period    # Year, Month, Week, Day, FederalFiscalYear
dtype     # Money, Rate, Boolean, Integer, Enum[...]

# OPTIONAL for variables
unit         # "USD", "months", "weeks", etc.
label        # Short human-readable name
description  # Longer explanation
formula      # Calculation block
default      # Default value
defined_for  # Filter condition block

# BLOCKS
imports      # Variable imports from other files
parameters   # Parameter values (inline or from .yaml)
exports      # Exported variable names
examples     # Test cases

# NAMED CONSTRUCTS (followed by identifier)
variable     # variable name:
input        # input name:
function     # function name(...):
enum         # enum name:
values       # values name:

# RAW STATUTE TEXT
text         # text: """ ... """
```

Anything not listed fails `scripts/validate_schema.py`.

## Formula Rules

**Allowed literals**: only -1, 0, 1, 2, 3

```python
# BAD - hardcoded values
if age >= 65: ...
threshold = income * 0.075

# GOOD - parameterized
if age >= elderly_age_threshold: ...
threshold = income * medical_expense_threshold_rate
```

**Allowed code keywords**: `if`, `else`, `return`, `for`, `break`, `and`, `or`, `not`, `in`

All policy values come from `parameters:` blocks.

## Validation

```bash
python scripts/validate_schema.py      # Whitelist enforcement
python scripts/validate_no_literals.py # No hardcoded values
```

## Related Repos

- **cosilico-lawarchive** - Source document archive (R2) + catalog
- **cosilico-validators** - Validation against external calculators
- **cosilico-engine** - DSL compiler and runtime
