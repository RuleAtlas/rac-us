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
│   │   │   ├── a/credit.rac
│   │   │   ├── b/2/phaseout.rac
│   │   │   └── d/1/B/refundable_credit.rac
│   │   ├── 32/          # § 32 - EITC
│   │   │   ├── a/1/earned_income_credit.rac
│   │   │   └── c/2/A/earned_income.rac
│   │   ├── 62/          # § 62 - AGI
│   │   │   └── a/adjusted_gross_income.rac
│   │   └── 63/          # § 63 - Standard Deduction
│   │       └── c/standard_deduction.rac
│   │
│   └── 7/               # Title 7 (Agriculture)
│       └── 2017/a/      # § 2017(a) - SNAP Allotment
│           └── allotment.rac
│
├── irs/                   # IRS guidance (Rev. Procs, etc.)
│   └── rev-proc-2023-34/
│       └── parameters.yaml
│
└── usda/fns/              # USDA Food & Nutrition Service guidance
    └── snap-fy2024-cola/
        └── parameters.yaml
```

## .rac Variable Schema

Variables in .rac files use ONLY these attributes:

```
# REQUIRED
entity    # Person, TaxUnit, Household, State, Family
period    # Year, Month, Week, Day, FederalFiscalYear
dtype     # Money, Rate, Boolean, Integer, Enum[...]

# OPTIONAL
unit         # "USD", "months", "weeks", etc.
label        # Short human-readable name
description  # Longer explanation
formula      # Calculation block
default      # Default value (not default_value)
defined_for  # Filter condition block

# BLOCKS (for cross-file dependencies)
imports      # Variable imports from other files
parameters   # Parameter imports from .yaml files
```

**NOT ALLOWED** (redundant with filepath):
- `module` - filepath IS the module path
- `version` - not needed
- `jurisdiction` - implied by repo (cosilico-us)
- `reference` - filepath IS the statute reference

Filepath `statute/26/32/a/1/earned_income_credit.rac` implies:
- Module: `statute.26.32.a.1`
- Reference: 26 USC § 32(a)(1)

## Formula Rules

**No numeric literals in formulas** (except 0, 1, -1):
```python
# BAD - hardcoded values
if age >= 65: ...
threshold = income * 0.075

# GOOD - parameterized
if age >= elderly_age_threshold: ...
threshold = income * medical_expense_threshold_rate
```

All policy values come from `parameters.yaml` files with legal citations.

## File Types

- `.rac` - Executable formulas (compile to Python/JS/WASM)
- `parameters.yaml` - Time-varying values (rates, thresholds, brackets)
- `tests.yaml` - Validation test cases

## Related Repos

- **cosilico-lawarchive** - Source document archive (R2) + catalog
- **cosilico-validators** - Validation against external calculators
- **cosilico-engine** - DSL compiler and runtime
