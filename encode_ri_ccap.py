"""Stress-test: encode RI CCAP (218-RICR-20-00-4) with pre-fetched regulation text."""

import asyncio
from pathlib import Path
from autorac.harness.orchestrator import Orchestrator

CITATION = "RI RICR 218-20-00-4"
OUTPUT_PATH = Path.cwd() / "statute" / "ri" / "218-RICR-20-00-4"

# Full regulation text fetched from https://rules.sos.ri.gov/Regulations/part/218-20-00-4
STATUTE_TEXT = """
218-RICR-20-00-4: Child Care Assistance Program Rules and Regulations
Title 218 - Rhode Island Department of Human Services

Authority: R.I. Gen. Laws § 42-12-23

4.1 General Provisions

4.1.1 Introduction
The Rhode Island Department of Human Services recognizes affordable child care access as critical for families transitioning from economic assistance to self-sufficiency. The Starting RIght Child Care Assistance Program (CCAP), adopted in 1998, ensures access to developmentally appropriate early childhood education and support services.

4.1.2 Authority and Purpose
Authority derives from R.I. Gen. Laws § 42-12-23, designating DHS as the principal state agency responsible for planning, coordination, and child care subsidy programs for Rhode Island Works Program (RIW) recipients and low to moderate-income eligible working families.

4.2 Definitions

"Allowable child care expense" - Total cost of CCAP authorized services paid by DHS to approved providers, minus family share.

"Applicant child(ren)" - Dependent children in the financial unit for whom CCAP services are requested.

"Authorized child care services" - Child care approved for a child based on assessed family need, categorized as full-time (FT), three-quarter time (3QT), half-time (HT), or quarter-time (QT).

"Categorically eligible" - Eligibility conferred by state law or DHS policy based on receipt of/participation in particular public benefit.

"Certification period" - Actual period eligible children obtain CCAP services, minimum twelve (12) months.

"Child Care Assistance Program (CCAP)" - DHS-administered program consolidating subsidy programs for RIW recipients, income-eligible working families, families with parents in approved education/training, and youth services participants.

"Dependent child" - Child under thirteen (13) years, or turning thirteen during the twelve-month certification period, or under nineteen if disabled with acceptable degree of relationship.

"DHS authorized payment rate for providers" - Rate DHS pays approved providers: either actual provider rate reported in APRR or DHS CCAP Established Payment Rate, whichever is lower.

"DHS CCAP established payment rate" - Maximum rate DHS pays providers per rate category, established from biennial Market Rate Survey.

"Eligible child" - Dependent child meeting requirements to receive authorized CCAP services (excludes foster children eligible through DCYF).

"Excluded income" - Certain money/goods/services not counted for eligibility determination:
- USDA donated foods value
- Relocation assistance under Title II
- Educational grants/loans for undergraduates
- Per capita Indian tribe payments
- Title VII nutrition benefits
- Volunteer service reimbursements
- Child nutrition act benefits
- Foster care payments (child not in assistance unit)
- Food assistance value
- Government rent/housing subsidies
- Home energy assistance
- College work study income
- Dependent child earned income
- Workforce Investment Act/WIOA stipends
- Earned Income Tax Credit (EITC) refunds
- Educational loans/scholarships
- Federal PASS/IRWE program funds
- Parent income (teen parent cases)
- Section 8 utility payments
- Veterans benefits
- AmeriCorps/VISTA volunteer payments
- Rhode Island Works cash assistance

"Family child care home" - Provider's home-based program for four (4) to eight (8) unrelated children, requiring DCYF licensure.

"Family share" - Amount families contribute as co-payments toward child care cost.

"Financial unit" - Dependent children (applicant and non-applicant), parent(s), and legal spouse(s) living in same household; determines family size for income purposes.

"Homeless individuals" - Individuals lacking fixed/regular/adequate nighttime residence.

"Income" - Money, goods, or services available to the financial unit for CCAP eligibility calculation, including:
- Wages, salary, commissions, work-based fees, stipends, tips, bonuses
- Self-employment adjusted gross income
- Social Security Benefits (RSDI)
- Supplemental Security Income (SSI)
- Dividends/interest
- Estate/trust income
- Rental income
- Public assistance payments
- Unemployment compensation
- Temporary Disability Insurance (TDI)
- Workers' compensation
- Government/military retirement
- Private pensions/annuities
- Alimony
- Child support payments
- Regular household contributions
- Foster care payments (child in assistance unit)

"Income eligible" - CCAP eligibility determined on income basis for non-RIW recipients within state law limits.

"Infant" - Child from one (1) week to eighteen (18) months old.
"Toddler" - Child over eighteen (18) months, up to three (3) years old.
"Pre-school age child" - Child age three (3) through first-grade entry.
"School-age child" - Child through age twelve, or turning thirteen during eligibility period, enrolled in at least first grade.

"Rhode Island Works Program (RIW)" - State program per R.I. Gen. Laws Chapter 40-5.1 providing cash assistance; beneficiaries categorically eligible for fully-subsidized CCAP.

"Temporary change in status" - Temporary parent status change including:
- Time-limited absence from work (family care, illness)
- Seasonal worker interruption between industry seasons
- Student holiday/break participation
- Work/training/education hour reduction while still participating
- Cessation not exceeding three (3) months

4.3 Eligibility and Authorization of Services

4.3.1 General Eligibility Requirements

Families with incomes at or below one hundred eighty percent (180%) of Federal Poverty Level (FPL) meeting CCAP requirements qualify for full or partial child care expense payment through two avenues:

1. Categorical Eligibility - RIW cash assistance recipients (including Youth Services participants) meeting need for services per § 4.5
2. Income Eligibility - Working families and those with parents in approved education/training programs meeting requirements per § 4.6
3. Temporary Higher Education Eligibility - October 1, 2021 through June 30, 2022, families where parent needs child care for enrollment in Rhode Island public institution of higher education, subject to available funding up to $200,000.

General Requirements (all applicants):

1. Age of applicant child(ren) - Child must be over one (1) week old, below thirteen (13) years, unless:
   - Child is thirteen (13) to eighteen (18) with documented physical/mental disability making self-care impossible; or
   - Child turns thirteen (13) during certification period, remaining eligible until redetermination

2. Relationship - Applicant child must live in parent's home.

3. Residency - Parent(s) and applicant children must be Rhode Island residents.

4. Citizenship - Applicant child must be U.S. citizen or qualified immigrant (no five-year waiting period for qualified immigrants).

5. Need for Services:
   - RIW/Youth Services parents: Must be in approved education/training activity or work plan activity per § 4.5
   - Income-eligible: Parents must be employed or participating in approved education/training program per § 4.6

6. Cooperation with Office of Child Support Services - All families with absent parent(s) are referred to OCSS. Parent must cooperate in establishing paternity and child support orders, unless good cause exists.

4.3.9 Limitations and Exclusions of Eligibility

1. One CCAP Household per Applicant Child - CCAP services authorized for one household per applicant child during certification period.

2. Self-Employment as Child Care Provider - Parent deriving sole self-employment income as child care provider ineligible for CCAP services.

4.4 Applying for Child Care Assistance

4.4.1 Application
Application period: Thirty (30) days from application date.
Homeless applicants have up to ninety (90) days providing required documentation.

4.4.3 Reporting Requirements
Families must report:
- Income changes during twelve (12)-month certification period exceeding eighty-five percent (85%) State Median Income (SMI)
- Non-temporary work/training/education cessation
- Address changes

4.4.4 Redetermination
CCAP eligibility period: No less than twelve (12) months.

4.5 Criteria for Categorical Eligibility

4.5.1 General Requirements and Criteria

RIW recipients fulfilling general § 4.3 requirements meet CCAP criteria by:

1. RIW-eligible acceptable need includes:
   a. Employment plan requirement: Parent(s) must have approved, signed, current employment plan on file.
   b. RIW component activities: Must meet Rhode Island Works Program Rules § 2.11 employment plan component activity requirements.
   c. Two-parent home requirement: Both parents must have signed, approved, current employment plans.

2. Youth Services (YS) participants:
   a. YS parents under twenty (20) years without high school diploma/equivalency, actively working with Youth Services Home Visiting Program, participating in approved education activity.

4.5.2 Limitations
Child care services not authorized for otherwise categorically eligible families when:
1. One-parent home: Parent failed completing RIW employment plan
2. Two-parent home: One parent lacks approved employment plan
3. Two-parent home: One parent statutorily barred from RIW and not working
4. Parent self-employed as child care provider requesting payment during employment hours
5. Eligible child parent providing child care
6. Same legal residence person providing child care
7. Full family sanction in place per RIW Rules Part 2

4.5.4 Co-payments
1. RIW recipients: Zero ($0.00) co-payment.
2. Loco-parentis applicants: Assessed co-payment based on Family Cost Sharing Requirement.
3. Homeless families: Zero ($0.00) co-payment.

4.6 Criteria for Income Eligibility

4.6.1 General Requirements and Criteria

1. Financial Determination:
   a. Income limits: Financial unit countable income at or below one hundred eighty percent (180%) Federal Poverty Level (FPL) based on family size.

   Transitional Child Care: Families currently child-care-eligible may continue receiving care after income exceeds 180% FPL, as long as income remains below two hundred twenty-five percent (225%) FPL.
   - Above 225% FPL: No longer eligible
   - New applicants exceeding 180% FPL ineligible for Transitional Child Care

   b. Self-employment income calculation: Per RIW Rules § 2.15.4

   c. Prospective budgeting: Weekly income converted to monthly using 4.3333 weeks/month conversion.

B. Treatment of Resources
   Liquid resources limit: one million dollars ($1,000,000.00). Exceeding this limit results in application denial.

   Liquid resources include: Cash, bank accounts, certificates of deposit, stocks, bonds, mutual funds.
   Excludes: Educational savings accounts, retirement accounts, joint accounts with non-household adult (documented).

C. Family Cost Sharing Requirement

1. Cost sharing: Eligible families with countable income above one hundred percent (100%) FPL pay service expense share.

   Effective through December 31, 2021:
   Level 0: ≤100% FPL - No Family Share
   Level 1: >100% to ≤125% FPL - 2% of Countable Gross Income
   Level 2: >125% to ≤150% FPL - 5% of Countable Gross Income
   Level 3: >150% to ≤180% FPL - 8% of Countable Gross Income
   Level 4: >180% to ≤200% FPL - 10% of Countable Gross Income
   Level 5: >200% to ≤225% FPL - 14% of Countable Gross Income

   Effective January 1, 2022:
   Level 0: ≤100% FPL - No Family Share
   Level 1: >100% to ≤125% FPL - 2% of Countable Gross Income
   Level 2: >125% to ≤150% FPL - 5% of Countable Gross Income
   Level 3: >150% to ≤225% FPL - 7% of Countable Gross Income

   2021 Income Thresholds (through December 31, 2021):
   Family Size 2: Level 0 <$17,420, Level 1 $21,775, Level 2 $26,130, Level 3 $31,356, Level 4 $34,840, Level 5 $39,195
   Family Size 3: Level 0 <$21,960, Level 1 $27,450, Level 2 $32,940, Level 3 $39,528, Level 4 $43,920, Level 5 $49,410
   Family Size 4: Level 0 <$26,500, Level 1 $33,125, Level 2 $39,750, Level 3 $47,700, Level 4 $53,000, Level 5 $59,625
   Family Size 5: Level 0 <$31,040, Level 1 $38,800, Level 2 $46,560, Level 3 $55,872, Level 4 $62,080, Level 5 $69,840
   Family Size 6: Level 0 <$35,580, Level 1 $44,475, Level 2 $53,370, Level 3 $64,044, Level 4 $71,160, Level 5 $80,055
   Family Size 7: Level 0 <$40,120, Level 1 $50,150, Level 2 $60,180, Level 3 $72,216, Level 4 $80,240, Level 5 $90,270
   Family Size 8: Level 0 <$44,660, Level 1 $55,825, Level 2 $66,990, Level 3 $80,388, Level 4 $89,320, Level 5 $100,485

   2022 Income Thresholds (effective January 1, 2022):
   Family Size 2: Level 0 <$17,420, Level 1 $21,775, Level 2 $26,130, Level 3 $39,195
   Family Size 3: Level 0 <$21,960, Level 1 $27,450, Level 2 $32,940, Level 3 $49,410
   Family Size 4: Level 0 <$26,500, Level 1 $33,125, Level 2 $39,750, Level 3 $59,625
   Family Size 5: Level 0 <$31,040, Level 1 $38,800, Level 2 $46,560, Level 3 $69,840
   Family Size 6: Level 0 <$35,580, Level 1 $44,475, Level 2 $53,370, Level 3 $80,055
   Family Size 7: Level 0 <$40,120, Level 1 $50,150, Level 2 $60,180, Level 3 $90,270
   Family Size 8: Level 0 <$44,660, Level 1 $55,825, Level 2 $66,990, Level 3 $100,485

2. Family share distribution:
   a. Determined without regard to eligible children enrollment number
   b. Assigned to first (youngest) eligible child enrolled receiving highest-rate authorized services
   c. Only distributed among providers when total family share exceeds first/youngest child rate

4.6.2 Need for Services

1. General Criteria - Income Eligible:
   a. Two-parent home: Each parent minimum average twenty (20) hours/week per month employment. Each parent earns hourly average of greater of State or Federal minimum wage.
   b. One-parent home: Parent minimum average twenty (20) hours/week per month employment, hourly average of greater of State or Federal minimum wage.

2. Program-Specific Criteria - Non-RIW YS Participants:
   a. YS parent under twenty (20) years, without high school degree/equivalent. Employed, attending school, or combination minimum twenty (20) hours/week. Authorization up to twelve (12) months.

3. Program-Specific Criteria - Child Care for Training:
   Beginning October 1, 2013, DHS provides child care to income-eligible families below 180% FPL in approved training programs.
   a. Parent participating minimum twenty (20) hours/week average monthly. Authorization no less than twelve (12) months.

4. Program-Specific Criteria - Child Care College:
   Beginning October 1, 2021, for families below 180% FPL enrolled in RI public institution of higher education.
   a. Parent enrolled minimum seven (7) credit hours per semester.
   b. Seven-credit-hour student: twenty-one (21) school-activity hours, meeting minimum twenty (20) hours/week.

4.6.3 Limitations
CCAP not authorized for otherwise income-eligible children when:
1. Parent self-employed as child care provider
2. Parent providing child care
3. Household-resident person providing child care
4. Applicant parent's sole income from rental/room-board
5. Applicant parent's need based wholly on volunteer work (unpaid work doesn't count toward minimum hours)

4.6.4 Exceptions
1. Parents with disabilities: May be exempt from minimum work hours/minimum wage requirements.
2. Temporary Change in Status: Temporary changes not adversely affecting CCAP authorization.
3. Non-Temporary Change in Status: Continue CCAP three (3) months for work-resumption or approved program attendance.

4.7 Short Term Special Approval

4.7.1 Criteria
SSACC approved when documented serious health condition evidence indicates child or parent special need.
- Child-based SSACC: Based on CEDARR finding
- Parent-based SSACC: Health condition prohibits employment and routine child care

4.7.2 Limitations
1. Not authorized exceeding full-time in any 24-hour period
2. Authorized up to three (3) months initially, additional three (3) months in any twelve (12)-month period

4.8 Authorization of Child Care Services

4.8.1 Authorization Levels
Services authorized as:
- Full-time (FT): 30+ hours per week
- Three-quarter time (3QT): 20-29 hours per week
- Half-time (HT): 10-19 hours per week
- Quarter-time (QT): Under 10 hours per week
"""


async def main():
    orchestrator = Orchestrator(backend="cli")
    run = await orchestrator.encode(
        citation=CITATION,
        output_path=OUTPUT_PATH,
        statute_text=STATUTE_TEXT,
    )
    print(f"\n{'='*60}")
    print(f"Session: {run.session_id}")
    print(f"Files created: {len(list(OUTPUT_PATH.rglob('*.rac')))}")
    print(f"Agent runs: {len(run.agent_runs)}")
    for ar in run.agent_runs:
        print(f"  - {ar.agent_key} ({ar.phase}): {ar.duration_ms/1000:.1f}s")


if __name__ == "__main__":
    asyncio.run(main())
