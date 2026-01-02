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
│   │   └── ...
│   └── 7/               # Title 7 (Agriculture)
│       ├── 2014/        # § 2014 - SNAP Eligibility
│       └── 2017/        # § 2017 - SNAP Allotment
├── RAC_SPEC.md           # Full .rac format specification
└── scripts/              # Validation and conversion tools
```

## Filepath = Citation (NEVER duplicate)

```
statute/26/32/c/2/A.rac  →  26 USC § 32(c)(2)(A)
statute/7/2017/a.rac     →  7 USC § 2017(a)
```

**⚠️ The filepath IS the citation. NEVER store citation separately.**
- ❌ `citation: "26 USC 1"` + `file: "statute/26/1.rac"` — REDUNDANT
- ✓ `file: "statute/26/1.rac"` — filepath encodes the citation

## .rac Format v2

See `RAC_SPEC.md` for full specification. Key features:

**Named declarations** (not blocks):
```yaml
parameter contribution_rate:
  values:
    1977-01-01: 0.30

variable snap_allotment:
  imports: [7/2014#household_size]
  entity: Household
  period: Month
  dtype: Money
  formula: ...
  tests:
    - inputs: {...}
      expect: 823
```

**Self-contained**: text, parameters, variables, tests in one file.

**Import syntax**: `path#variable` or `path#variable as alias`

**Scoping**:
- Parameters: in scope for all variables in file
- Same-file variables: in scope for later variables (dependency order)
- Imports: in scope for that variable's formula only

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

## Commands

```bash
# Validate schema
python scripts/test_new_schema.py

# Convert old format to new (WIP)
python scripts/convert_to_new_format.py --file path/to.rac --dry-run
```

## Exemplar Files

New format exemplars:
- `statute/7/2017/a/allotment_new.rac` - SNAP allotment

## Related Repos

- **cosilico-engine** - DSL compiler and runtime
- **cosilico-lawarchive** - Source document archive
- **cosilico-validators** - Validation against external calculators
