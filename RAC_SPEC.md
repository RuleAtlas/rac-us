# .rac File Specification v2

Self-contained rule encoding format for tax statutes, regulations, and guidance.

## Core Principle

**A .rac file encodes ONLY what appears in its source text - no more, no less.**

What IS encoded must be faithful to the text. What ISN'T encoded should be explicitly marked with a status.

This means:
- Values in the rule text → parameters in the .rac
- Values from IRS guidance, indexing, etc. → separate data layer (not in .rac)
- The `indexed_by:` field is a pointer, not a command to include indexed values

## File Status

Every .rac file has an implicit or explicit status:

```yaml
status: encoded | partial | draft | consolidated | deferred | boilerplate | entity_not_supported | obsolete

notes: "optional context"
```

| Status | Meaning | Has formula? |
|--------|---------|--------------|
| `encoded` | Fully implemented | Yes |
| `partial` | Some provisions in text encoded, others pending | Yes (incomplete) |
| `draft` | Work in progress | Partial |
| `stub` | Interface-only placeholder for import resolution | No |
| `consolidated` | Captured in parent/sibling file | No |
| `deferred` | Too complex, return later | No |
| `boilerplate` | Definitions, cross-refs, no computational content | No |
| `entity_not_supported` | Needs entity type not yet modeled (corps, trusts) | No |
| `obsolete` | Historical provision no longer in effect | No |

**Default**: Files without explicit `status:` are assumed `encoded`.

Examples:

```yaml
# 26 USC 1(g) - Kiddie Tax
status: deferred
notes: "Parent-child income linkage needed"
text: """..."""
```

```yaml
# 26 USC 1(a)(1) - MFJ definition clause
status: consolidated
notes: "Rate table in 26/1/a.rac"
text: """..."""
```

```yaml
# 26 USC 32(b)(1) - Credit percentage
status: partial
notes: "Credit percentage done; investment income disqualification pending"
text: """..."""
parameter credit_percentage: ...
variable eitc_credit_pct: ...
# investment_income_test not yet encoded
```

### Stub Format (STRICT)

**Stubs exist ONLY to resolve imports.** When encoding file A requires importing from file B that doesn't exist, create B as a minimal stub.

⚠️ **Stubs contain:**
- `status: stub`
- `text:` block with the rule text (for reviewer verification)
- Variable declarations with `stub_for:` field
- Entity, period, dtype, default

⚠️ **Stubs do NOT contain:**
- Parameters (no values researched)
- Formulas (no logic implemented)
- Tests (nothing to test)
- Analysis notes or complexity assessments

```yaml
# 26 USC Section 1(h) - Maximum Capital Gains Rate
# Stub for import resolution from 26/1

status: stub

text: """
(h) Maximum capital gains rate.—
(1) In general.— If a taxpayer has a net capital gain for any taxable year,
the tax imposed by this section for such taxable year shall not exceed the sum of—
...
"""

variable adjusted_net_capital_gain:
  stub_for: 26/1#income_tax
  entity: TaxUnit
  period: Year
  dtype: Money
  default: 0

variable capital_gains_tax:
  stub_for: 26/1#income_tax
  entity: TaxUnit
  period: Year
  dtype: Money
  default: 0
```

The `stub_for:` field indicates which importing variable triggered stub creation. Remove it when encoding the stub into a full implementation.

**Stub vs Deferred:**
- `stub`: Interface placeholder - text included for reviewer verification, but no implementation
- `deferred`: Reviewed and intentionally skipped - includes notes explaining why

## File Structure

```yaml
# path/to/section.rac - Title

text: """
Statute text here...
"""

parameter param_name:
  description: "..."
  unit: USD
  source: "..."
  values:
    2024-01-01: 100
    2023-01-01: 95

variable var_name:
  imports: [path#var, path#var2 as alias]
  entity: Household
  period: Month
  dtype: Money
  formula: |
    ...
  tests:
    - inputs: {...}
      expect: ...
```

## Top-Level Declarations

All declarations are named (no block-style grouping):

| Declaration | Syntax | Purpose |
|-------------|--------|---------|
| `text:` | `text: """..."""` | Statute text |
| `parameter` | `parameter name:` | Policy value |
| `variable` | `variable name:` | Computed value |
| `input` | `input name:` | User-provided input |
| `enum` | `enum name:` | Enumeration type |
| `function` | `function name:` | Helper function |

## Parameter Attributes

```yaml
parameter contribution_rate:
  description: "Household contribution as share of net income"
  unit: USD           # Optional: USD, rate, years, months, persons
  source: "USDA FNS"  # Optional: data source
  reference: "7 USC 2017(a)"  # Optional: legal citation
  values:
    2024-01-01: 0.30
    2023-01-01: 0.30
```

Parameters are in scope for all variables in the file.

## Variable Attributes

```yaml
variable snap_allotment:
  imports: [7/2014#household_size, 7/2014/a#snap_eligible]
  entity: Household       # Required: Person, TaxUnit, Household, Family
  period: Month           # Required: Year, Month, Day
  dtype: Money            # Required: Money, Rate, Boolean, Integer, Enum[...]
  unit: "USD"             # Optional
  label: "SNAP Benefit"   # Optional
  description: "..."      # Optional
  default: 0              # Optional
  formula: |
    if not snap_eligible:
      return 0
    return max_allotment - net_income * contribution_rate
  tests:
    - name: "Basic case"  # Optional
      inputs: {household_size: 4, snap_net_income: 500}
      expect: 823
```

## Import Syntax

```yaml
imports:
  - 7/2014#household_size           # Import as-is
  - 7/2014/e#snap_net_income        # From nested path
  - 26/32#earned_income as ei       # With alias
```

Path format: `title/section/subsection#variable_name`

## Scoping Rules

| Source | In Scope For |
|--------|--------------|
| Same-file parameter | All variables in file |
| Same-file variable | Later variables (dependency order) |
| Imported variable | That variable's formula only |

## Formula Syntax

Python-like with restrictions:
- Keywords: `if`, `else`, `return`, `for`, `break`, `and`, `or`, `not`, `in`
- Built-ins: `max`, `min`, `abs`, `round`, `sum`, `len`
- **No numeric literals** except -1, 0, 1, 2, 3 (use parameters)

```yaml
formula: |
  if household_size <= minimum_benefit_max_size:
    return minimum_benefit
  return 0
```

## Validation Rules

These rules are enforced by CI (automated pytest checks):

| Rule | Description |
|------|-------------|
| No magic numbers | Only -1, 0, 1, 2, 3 allowed in formulas |
| Param values in text | Every parameter value must appear in the `text:` field |
| Imports resolve | All `imports:` paths must reference existing files/variables |
| Large number separators | Numbers ≥1000 must use `_` separator (e.g., `10_000`) |

**Param values in text** catches:
- Hallucinated values (LLM made it up)
- Copy-paste from other statutes
- Rev Proc values when encoding statute-only

Allowed exceptions: 0 and 1 (common defaults), percentage conversions (0.075 ↔ "7.5%")

## ⚠️ Pattern Library (MUST USE)

When you see these statutory patterns, use the corresponding RAC construct.
**Do NOT implement these manually - use the built-in functions.**

### Progressive Tax Brackets → `marginal_agg()`

When rule has a rate table like:
```
If taxable income is:          The tax is:
Not over $X                    A% of taxable income
Over $X but not over $Y        $Z, plus B% of excess over $X
```

**MUST use:**
```yaml
parameter brackets:
  values:
    2018-01-01:
      thresholds: [0, 19050, 77400, 165000, 315000, 400000, 600000]
      rates: [0.10, 0.12, 0.22, 0.24, 0.32, 0.35, 0.37]

variable income_tax:
  formula: |
    return marginal_agg(taxable_income, brackets)
```

**NEVER write manual bracket loops:**
```yaml
# ❌ WRONG - 80 lines of manual computation
formula: |
  if taxable_income <= threshold_1:
    return taxable_income * rate_1
  elif taxable_income <= threshold_2:
    return threshold_1 * rate_1 + (taxable_income - threshold_1) * rate_2
  # ... 6 more brackets
```

### Filing Status Variations → Threshold by Category

When brackets differ by filing status (single, joint, HoH, MFS):

```yaml
parameter brackets:
  values:
    2018-01-01:
      thresholds:
        single: [0, 9525, 38700, 82500, 157500, 200000, 500000]
        joint: [0, 19050, 77400, 165000, 315000, 400000, 600000]
        hoh: [0, 13600, 51800, 82500, 157500, 200000, 500000]
        mfs: [0, 9525, 38700, 82500, 157500, 200000, 300000]
      rates: [0.10, 0.12, 0.22, 0.24, 0.32, 0.35, 0.37]

variable income_tax:
  imports: [26/1#filing_status]
  formula: |
    return marginal_agg(taxable_income, brackets, threshold_by=filing_status)
```

### Step Function Lookup → `cut()`

When rule says "if X is at least Y, the amount is Z":

```yaml
parameter benefit_schedule:
  values:
    2024-01-01:
      thresholds: [0, 100, 130]
      amounts:
        1: [291, 200, 0]  # household size 1
        2: [535, 391, 0]  # household size 2

variable snap_max_benefit:
  formula: |
    return cut(net_income_pct, benefit_schedule, amount_by=household_size)
```

### Phase-Out (AGI-based) → Linear Reduction

```yaml
parameter phase_out:
  values:
    2024-01-01:
      start: 200000
      end: 240000
      rate: 0.05  # 5% reduction per $1000 over start

variable credit_after_phaseout:
  formula: |
    reduction = max(0, (agi - phase_out.start) * phase_out.rate)
    return max(0, base_credit - reduction)
```

### Pattern Recognition Checklist

Before encoding, identify which pattern applies:

| Statutory Language | Pattern | RAC Construct |
|-------------------|---------|---------------|
| "rate table", "if income is..." | Progressive brackets | `marginal_agg()` |
| "by filing status" | Category variation | `threshold_by=` |
| "maximum benefit of $X" | Step function | `cut()` |
| "reduced by $Y for each $Z" | Phase-out | Linear formula |
| "shall not exceed" | Cap/limit | `min()` |
| "the greater of" | Floor | `max()`|

## Test Syntax

```yaml
tests:
  - name: "Family of 4"           # Optional name
    period: 2024-01               # Optional: defaults to current
    inputs:
      household_size: 4
      snap_net_income: 500
      snap_eligible: true
    expect: 823                   # Expected output value
```

## Versioning (Temporal)

For rules with formula changes over time:

```yaml
variable additional_ctc:
  entity: TaxUnit
  period: Year
  dtype: Money

  versions:
    2018-01-01:
      parameters:
        threshold: 2500
        cap: 1400
      formula: |
        ...TCJA formula...

    2026-01-01:
      reverts_to: 2001-01-01
```

Effective dates should come from rule text conditions (e.g., "for taxable years beginning after December 31, 2017"). P.L. references are tracked separately in arch, not required in .rac files.

## Uncertainty Metadata

Use `_uncertain` to flag fields that need verification. This enables encoding to proceed without blocking on missing research.

```yaml
parameter brackets:
  values:
    2018-01-01:
      # Date from statute: "after December 31, 2017"
      thresholds: [0, 19050, 77400, 165000, 315000, 400000, 600000]
      rates: [0.10, 0.12, 0.22, 0.24, 0.32, 0.35, 0.37]

    2017-01-01:
      _uncertain: [effective_date]
      _notes:
        effective_date: "Pre-TCJA, actual date from P.L. amendment history"
      thresholds: [0, 36900, 89150, 140000, 250000]
      rates: [0.15, 0.28, 0.31, 0.36, 0.396]

    1980-01-01:
      _uncertain: [effective_date, thresholds]
      _notes:
        effective_date: "Approximate, needs P.L. research"
        thresholds: "Values from secondary source"
      thresholds: [0, 20000, 40000]
      rates: [0.14, 0.16, 0.18]
```

### `_uncertain` Syntax

| Value | Meaning |
|-------|---------|
| `_uncertain: [field1, field2]` | Listed fields need verification |
| `_uncertain: all` | Entire entry needs verification |
| `_notes: {field: "reason"}` | Why field is uncertain |

Works at any level:
- Parameter values (as shown above)
- Variable attributes
- File-level metadata

To find all uncertainties: `grep -r "_uncertain" statute/`

## File Naming

Filepath = legal citation:
```
statute/7/2017/a.rac      → 7 USC § 2017(a)
statute/26/24/d/1/B.rac   → 26 USC § 24(d)(1)(B)
```

## Migration from v1

Old format (separate files):
- `variable.rac` + `parameters.yaml` + `tests.yaml`

New format (self-contained):
- Single `.rac` with `parameter`, `variable`, `tests:` inline

Use `scripts/convert_to_new_format.py` for automated migration.
