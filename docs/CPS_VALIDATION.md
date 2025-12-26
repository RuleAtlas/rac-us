# CPS Validation Dashboard

*Last updated: 2025-12-26 13:15*

## Summary Statistics

| Variable | N | Mean | Median | Min | Max | Nonzero % |
|----------|---|------|--------|-----|-----|-----------|
| adjusted_gross_income | 28 | $91,819 | $55,000 | $15,000 | $400,000 | 100.0% |
| taxable_income | 28 | $70,207 | $36,750 | $0 | $385,400 | 89.3% |
| income_tax_before_credits | 28 | $12,689 | $4,128 | $0 | $105,265 | 89.3% |
| income_tax | 28 | $9,925 | $1,988 | $-10,455 | $105,265 | 100.0% |
| eitc | 28 | $1,230 | $0 | $0 | $7,830 | 32.1% |
| ctc | 28 | $1,714 | $0 | $0 | $6,000 | 42.9% |
| employee_social_security_tax | 28 | $3,653 | $3,038 | $0 | $10,453 | 89.3% |
| self_employment_tax | 28 | $1,362 | $0 | $0 | $21,194 | 10.7% |

## Sample Scenarios

| Scenario | AGI | Taxable | Tax | EITC | CTC |
|----------|-----|---------|-----|------|-----|
| Single $15,000 | $15,000 | $400 | $-235 | $275 | $0 |
| Single $25,000 | $25,000 | $10,400 | $1,040 | $0 | $0 |
| Single $40,000 | $40,000 | $25,400 | $2,816 | $0 | $0 |
| Single $60,000 | $60,000 | $45,400 | $5,216 | $0 | $0 |
| Single $80,000 | $80,000 | $65,400 | $9,441 | $0 | $0 |
| Single $120,000 | $120,000 | $105,400 | $18,338 | $0 | $0 |
| Single $200,000 | $200,000 | $185,400 | $37,538 | $0 | $0 |
| Single $400,000 | $400,000 | $385,400 | $105,265 | $0 | $0 |
| MFJ $40,000 | $40,000 | $10,800 | $1,080 | $0 | $0 |
| MFJ $80,000 | $80,000 | $50,800 | $5,632 | $0 | $0 |
| MFJ $120,000 | $120,000 | $90,800 | $10,432 | $0 | $0 |
| MFJ $200,000 | $200,000 | $170,800 | $27,682 | $0 | $0 |
| MFJ $400,000 | $400,000 | $370,800 | $75,077 | $0 | $0 |
| HoH $20,000 + 1 kids | $20,000 | $0 | $-5,913 | $4,213 | $2,000 |
| HoH $20,000 + 2 kids | $20,000 | $0 | $-9,585 | $6,960 | $4,000 |
| HoH $20,000 + 3 kids | $20,000 | $0 | $-10,455 | $7,830 | $6,000 |
| HoH $35,000 + 1 kids | $35,000 | $13,100 | $-2,941 | $2,251 | $2,000 |
| HoH $35,000 + 2 kids | $35,000 | $13,100 | $-7,064 | $4,374 | $4,000 |
| HoH $35,000 + 3 kids | $35,000 | $13,100 | $-9,934 | $5,244 | $6,000 |
| HoH $50,000 + 1 kids | $50,000 | $28,100 | $1,041 | $0 | $2,000 |

## Validation Notes

- All calculations use PolicyEngine-US for 2024 tax year
- State set to TX (no state income tax) to isolate federal calculations
- Self-employment tax computed from self_employment_income
- EITC/CTC computed based on earned income and qualifying children

## Next Steps

1. Compare against TaxSim API responses
2. Add weighted CPS microdata sample
3. Track accuracy metrics over time