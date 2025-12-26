# TaxSim 35 Parity Gap Analysis

*Last updated: 2025-12-25*

## TaxSim Output Variables vs Cosilico Coverage

### Federal Income Tax (Core) ✅ = Encoded, ❌ = Missing, ⚠️ = Partial, 🔄 = In Progress

| TaxSim Variable | Description | Cosilico Status |
|-----------------|-------------|-----------------|
| v10 - Federal AGI | Adjusted Gross Income | ✅ `adjusted_gross_income` |
| v11 - UI in AGI | Unemployment Insurance in AGI | ✅ `unemployment_in_agi` |
| v12 - Social Security in AGI | Taxable SS in AGI | ✅ `taxable_social_security` |
| v13 - Zero Bracket Amount | Standard deduction floor | ✅ `standard_deduction` |
| v14 - Personal Exemptions | Exemption amount | N/A (eliminated permanently by OBBBA) |
| v15 - Exemption Phaseout | Exemption phaseout | N/A (eliminated permanently by OBBBA) |
| v16 - Deduction Phaseout | Itemized deduction phaseout | N/A (Pease eliminated permanently by OBBBA) |
| v17 - Itemized Deductions | Total itemized | ✅ `itemized_deductions` |
| v18 - Taxable Income | AGI minus deductions | ✅ `taxable_income` |
| v19 - Tax on Taxable Income | Ordinary income tax | ✅ `income_tax` |
| v20 - Exemption Surtax | Historical surtax | N/A (not applicable post-2017) |
| v21 - General Tax Credit | Historical credit | N/A (not applicable) |
| v22 - Child Tax Credit | Nonrefundable CTC | ✅ `child_tax_credit` |
| v23 - Additional Child Tax Credit | Refundable ACTC | ✅ `refundable_credit` |
| v24 - Child Care Credit | CDCC | ✅ `child_dependent_care_credit` |
| v25 - Earned Income Credit | EITC | ✅ `earned_income_credit` |
| v26 - Income for AMT | AMTI | ✅ `alternative_minimum_taxable_income` |
| v27 - AMT Liability | Alternative minimum tax | ✅ `alternative_minimum_tax` |
| v28 - Tax Before Credits | Gross tax liability | ✅ `tax_liability_before_credits` |
| v29 - FICA | Social Security + Medicare | ✅ `employee_fica_tax` |
| fiitax - Total Federal Tax | Net federal liability | ✅ `total_federal_income_tax` |

### FICA/Payroll Taxes

| Component | Cosilico Status |
|-----------|-----------------|
| Employee Social Security (6.2%) | ✅ `employee_social_security_tax` |
| Employer Social Security (6.2%) | ✅ `employer_social_security_tax` |
| Employee Medicare (1.45%) | ✅ `medicare_tax` |
| Employer Medicare (1.45%) | ❌ Missing |
| Additional Medicare (0.9%) | ✅ `additional_medicare_tax` |
| Self-Employment Tax | ✅ `self_employment_tax` |
| NIIT (3.8%) | ✅ `net_investment_income_tax` |

### Credits

| Credit | Cosilico Status |
|--------|-----------------|
| Child Tax Credit | ✅ |
| Additional CTC (refundable) | ✅ |
| EITC | ✅ |
| Child & Dependent Care Credit | ✅ |
| American Opportunity Credit | ✅ `aoc` |
| Lifetime Learning Credit | ✅ `llc` |
| Saver's Credit | ✅ `savers_credit` |
| Foreign Tax Credit | ❌ Missing (not in TaxSim) |
| Adoption Credit | ❌ Missing (not in TaxSim) |
| Residential Energy Credit | N/A (not in TaxSim) |
| EV Credit | N/A (not in TaxSim) |
| Premium Tax Credit | ✅ `premium_tax_credit` |
| Recovery Rebate (COVID) | ❌ Missing (historical) |

### Deductions (Above-the-Line)

| Deduction | Cosilico Status |
|-----------|-----------------|
| Student Loan Interest | ✅ |
| IRA Deduction | ✅ |
| HSA Deduction | ✅ |
| Self-Employment Tax Deduction | ✅ |
| Self-Employed Health Insurance | ✅ |
| Educator Expense | ✅ |
| Tip Income Deduction (OBBBA 2025-2028) | 🔄 In Progress |
| Overtime Deduction (OBBBA 2025-2028) | 🔄 In Progress |
| Moving Expenses (military) | ❌ Missing |
| Alimony (pre-2019) | ❌ Missing (historical) |

### Deductions (Itemized)

| Deduction | Cosilico Status |
|-----------|-----------------|
| SALT (capped at $10k) | ✅ `salt_deduction` |
| Mortgage Interest | ✅ `qualified_residence_interest` |
| Charitable Contributions | ✅ `charitable_deduction` |
| Medical Expenses (>7.5% AGI) | ✅ `medical_expense_deduction` |
| Casualty Losses | ❌ Missing (limited post-TCJA) |
| Investment Interest | ✅ `investment_interest` |

### Income Types

| Income | Cosilico Status |
|--------|-----------------|
| Wages/Salaries | ✅ |
| Self-Employment | ✅ |
| Interest | ✅ |
| Dividends (ordinary) | ✅ |
| Dividends (qualified) | ✅ `qualified_dividend_income` |
| Capital Gains (short-term) | ✅ |
| Capital Gains (long-term) | ✅ |
| Social Security Benefits | ✅ |
| Unemployment Insurance | ✅ `unemployment_compensation` |
| Rental Income | ⚠️ Partial |
| Partnership/S-Corp | ⚠️ Partial (QBI exists) |
| Pension/Annuity | ❌ Missing |
| IRA Distributions | ❌ Missing |

## OBBBA (One Big Beautiful Bill Act) Changes

Signed July 4, 2025 - made TCJA permanent with additions:

### Made Permanent
- Personal exemptions remain at $0 (no return of PEP)
- Pease limitation eliminated (replaced with 37%→35% cap for top bracket)
- Standard deduction amounts preserved
- Tax bracket structure preserved

### New Provisions (2025-2028)
| Provision | Cap | Phaseout Start | Status |
|-----------|-----|----------------|--------|
| Tip Income Deduction | $25,000 | $150k/$300k | 🔄 In Progress |
| Overtime Deduction | $12,500/$25,000 | $150k/$300k | 🔄 In Progress |

## Priority Gaps for TaxSim Parity

### P1 - Critical ✅ COMPLETE
All P1 items have been encoded:
- ~~Employee FICA (SS + Medicare)~~ ✅
- ~~Total Federal Tax Liability~~ ✅
- ~~Unemployment Insurance in AGI~~ ✅

### P2 - Important (common scenarios)
| Item | Status |
|------|--------|
| ~~Saver's Credit~~ | ✅ Encoded |
| ~~Qualified Dividends~~ | ✅ Encoded |
| Foreign Tax Credit | ❌ (simplified) - Note: Not in TaxSim |
| Pension/IRA Distributions | ❌ §402/408 |

### P3 - Nice to Have
| Item | Status |
|------|--------|
| Recovery Rebate Credits | ❌ (COVID-era, historical) |
| Energy Credits | N/A (not in TaxSim) |
| Adoption Credit | ❌ (not in TaxSim) |

## Validation Infrastructure

| Component | Status |
|-----------|--------|
| TaxSim API Client | 🔄 In Progress |
| Variable Mapping | 🔄 In Progress |
| Test Case Suite | 🔄 In Progress |
| Comparison Reports | 🔄 In Progress |

## Next Steps

1. Complete tip/overtime deduction encoding
2. Finish TaxSim validation infrastructure
3. Update all parameters for 2025/2026
4. Add pension/IRA distribution handling
5. Run validation suite against TaxSim
