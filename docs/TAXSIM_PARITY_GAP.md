# TaxSim 35 Parity Gap Analysis

## TaxSim Output Variables vs Cosilico Coverage

### Federal Income Tax (Core) ✅ = Encoded, ❌ = Missing, ⚠️ = Partial

| TaxSim Variable | Description | Cosilico Status |
|-----------------|-------------|-----------------|
| v10 - Federal AGI | Adjusted Gross Income | ✅ `adjusted_gross_income` |
| v11 - UI in AGI | Unemployment Insurance in AGI | ❌ Missing |
| v12 - Social Security in AGI | Taxable SS in AGI | ✅ `taxable_social_security` |
| v13 - Zero Bracket Amount | Standard deduction floor | ✅ `standard_deduction` |
| v14 - Personal Exemptions | Exemption amount | ❌ Missing (suspended under TCJA) |
| v15 - Exemption Phaseout | Exemption phaseout | ❌ Missing (suspended under TCJA) |
| v16 - Deduction Phaseout | Itemized deduction phaseout | ❌ Missing (Pease limitation suspended) |
| v17 - Itemized Deductions | Total itemized | ✅ `itemized_deductions` |
| v18 - Taxable Income | AGI minus deductions | ✅ `taxable_income` |
| v19 - Tax on Taxable Income | Ordinary income tax | ✅ `income_tax` |
| v20 - Exemption Surtax | Historical surtax | ❌ Not applicable post-2017 |
| v21 - General Tax Credit | Historical credit | ❌ Not applicable |
| v22 - Child Tax Credit | Nonrefundable CTC | ✅ `child_tax_credit` |
| v23 - Additional Child Tax Credit | Refundable ACTC | ✅ `refundable_credit` |
| v24 - Child Care Credit | CDCC | ✅ `child_dependent_care_credit` |
| v25 - Earned Income Credit | EITC | ✅ `earned_income_credit` |
| v26 - Income for AMT | AMTI | ✅ `amti` |
| v27 - AMT Liability | Alternative minimum tax | ✅ `amt` |
| v28 - Tax Before Credits | Gross tax liability | ✅ `tax_liability_before_credits` |
| v29 - FICA | Social Security + Medicare | ⚠️ Partial (`self_employment_tax`, `medicare_tax`) |
| fiitax - Total Federal Tax | Net federal liability | ❌ Need to sum components |

### FICA/Payroll Taxes

| Component | Cosilico Status |
|-----------|-----------------|
| Employee Social Security (6.2%) | ❌ Missing |
| Employer Social Security (6.2%) | ❌ Missing |
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
| Saver's Credit | ❌ Missing |
| Foreign Tax Credit | ❌ Missing |
| Adoption Credit | ❌ Missing |
| Residential Energy Credit | ❌ Missing |
| EV Credit | ❌ Missing |
| Premium Tax Credit | ✅ `premium_tax_credit` |
| Recovery Rebate (COVID) | ❌ Missing |

### Deductions (Above-the-Line)

| Deduction | Cosilico Status |
|-----------|-----------------|
| Student Loan Interest | ✅ |
| IRA Deduction | ✅ |
| HSA Deduction | ✅ |
| Self-Employment Tax Deduction | ✅ |
| Self-Employed Health Insurance | ✅ |
| Educator Expense | ✅ |
| Moving Expenses (military) | ❌ Missing |
| Alimony (pre-2019) | ❌ Missing |

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
| Dividends (qualified) | ⚠️ Need to separate |
| Capital Gains (short-term) | ✅ |
| Capital Gains (long-term) | ✅ |
| Social Security Benefits | ✅ |
| Unemployment Insurance | ❌ Missing |
| Rental Income | ⚠️ Partial |
| Partnership/S-Corp | ⚠️ Partial (QBI exists) |
| Pension/Annuity | ❌ Missing |
| IRA Distributions | ❌ Missing |

## Priority Gaps for TaxSim Parity

### P1 - Critical (blocks core tax calculation)
1. **Employee FICA (SS + Medicare)** - §3101/3111
2. **Total Federal Tax Liability** - Sum all components
3. **Unemployment Insurance in AGI** - §85

### P2 - Important (common scenarios)
4. **Saver's Credit** - §25B
5. **Foreign Tax Credit** - §901 (simplified)
6. **Qualified Dividends Separation** - §1(h)(11)
7. **Pension/IRA Distributions** - §402/408

### P3 - Nice to Have
8. **Recovery Rebate Credits** - COVID-era
9. **Energy Credits** - §25C, §30D
10. **Adoption Credit** - §23
