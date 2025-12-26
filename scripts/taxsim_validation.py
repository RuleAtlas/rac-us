"""
TAXSIM 35 Validation Script

Compares PolicyEngine-US calculations against NBER TAXSIM 35 API.
Generates comparison dashboard to docs/TAXSIM_VALIDATION.md

TAXSIM API: https://taxsim.nber.org/taxsim35/
"""

import csv
import io
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import urllib.request
import urllib.error
import tempfile
import subprocess

# Add parent for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class TaxCase:
    """A test case for tax calculation comparison."""

    name: str
    year: int = 2023  # TAXSIM 35 only supports up to 2023 as of Dec 2024
    # Filing status: 1=single, 2=joint, 3=head of household
    mstat: int = 1
    # SOI state code (0=no state calc, helps isolate federal)
    state: int = 0
    # Primary taxpayer
    page: int = 35
    pwages: float = 0.0
    psemp: float = 0.0
    # Secondary taxpayer (spouse)
    sage: int = 0
    swages: float = 0.0
    ssemp: float = 0.0
    # Investment income
    dividends: float = 0.0
    intrec: float = 0.0  # Interest received
    stcg: float = 0.0  # Short-term capital gains
    ltcg: float = 0.0  # Long-term capital gains
    # Other income
    pensions: float = 0.0
    gssi: float = 0.0  # Social security benefits
    pui: float = 0.0  # Unemployment insurance
    # Dependents - use age1-age3 for specific ages (preferred by TAXSIM)
    depx: int = 0  # Number of dependents (total)
    age1: int = 0  # Age of first dependent (0 = not present)
    age2: int = 0  # Age of second dependent
    age3: int = 0  # Age of third dependent
    # Deductions
    proptax: float = 0.0
    mortgage: float = 0.0
    childcare: float = 0.0
    otheritem: float = 0.0


@dataclass
class TaxSimResult:
    """Results from TAXSIM API."""

    taxsim_id: int
    year: int
    state: int
    fiitax: float  # Federal income tax
    siitax: float  # State income tax
    fica: float  # FICA taxes
    frate: float  # Federal marginal rate
    srate: float  # State marginal rate
    ficar: float  # FICA marginal rate
    # Extended outputs (columns 10+)
    v10_agi: float = 0.0
    v11_ui_agi: float = 0.0
    v12_ss_agi: float = 0.0
    v13_zero_bracket: float = 0.0
    v14_exemptions: float = 0.0
    v15_exemption_phaseout: float = 0.0
    v16_deductions: float = 0.0
    v17_deduction_phaseout: float = 0.0
    v18_taxable_income: float = 0.0
    v19_tax_regular: float = 0.0
    v22_ctc: float = 0.0
    v23_ctc_refundable: float = 0.0
    v25_eitc: float = 0.0
    v26_amt: float = 0.0
    v27_fed_tax_before_credits: float = 0.0
    v28_fica: float = 0.0


@dataclass
class PolicyEngineResult:
    """Results from PolicyEngine-US."""

    adjusted_gross_income: float = 0.0
    taxable_income: float = 0.0
    income_tax_before_credits: float = 0.0
    income_tax: float = 0.0
    eitc: float = 0.0
    ctc: float = 0.0
    refundable_ctc: float = 0.0
    employee_social_security_tax: float = 0.0
    self_employment_tax: float = 0.0
    amt_income: float = 0.0  # Alternative Minimum Taxable Income
    amt: float = 0.0  # Alternative Minimum Tax


@dataclass
class ComparisonResult:
    """Comparison between TAXSIM and PolicyEngine."""

    case: TaxCase
    taxsim: Optional[TaxSimResult]
    policyengine: Optional[PolicyEngineResult]
    errors: List[str] = field(default_factory=list)


def generate_test_cases() -> List[TaxCase]:
    """Generate comprehensive test scenarios."""
    cases = []

    # 1. Single filers at various income levels
    for income in [15000, 25000, 40000, 60000, 80000, 120000, 200000, 400000]:
        cases.append(
            TaxCase(
                name=f"Single ${income:,}",
                mstat=1,
                page=35,
                pwages=income,
            )
        )

    # 2. Married filing jointly at various income levels
    for income in [40000, 80000, 120000, 200000, 400000]:
        cases.append(
            TaxCase(
                name=f"MFJ ${income:,}",
                mstat=2,
                page=40,
                pwages=int(income * 0.6),
                sage=38,
                swages=int(income * 0.4),
            )
        )

    # 3. EITC-eligible scenarios (Head of Household with children)
    # Use age1-age3 for specific dependent ages (TAXSIM preferred method)
    for income in [15000, 20000, 30000, 40000, 50000]:
        for n_kids in [1, 2, 3]:
            case = TaxCase(
                name=f"HoH ${income:,} + {n_kids} kids",
                mstat=3,  # Head of household
                page=32,
                pwages=income,
                depx=n_kids,
            )
            # Add child ages (8, 10, 12 for EITC/CTC eligibility)
            if n_kids >= 1:
                case.age1 = 8
            if n_kids >= 2:
                case.age2 = 10
            if n_kids >= 3:
                case.age3 = 12
            cases.append(case)

    # 4. MFJ with children (CTC scenarios)
    for income in [50000, 75000, 100000, 150000, 200000, 400000, 500000]:
        for n_kids in [1, 2, 3]:
            case = TaxCase(
                name=f"MFJ ${income:,} + {n_kids} kids",
                mstat=2,
                page=35,
                pwages=int(income * 0.6),
                sage=33,
                swages=int(income * 0.4),
                depx=n_kids,
            )
            if n_kids >= 1:
                case.age1 = 6
            if n_kids >= 2:
                case.age2 = 9
            if n_kids >= 3:
                case.age3 = 14
            cases.append(case)

    # 5. Self-employment income
    for income in [30000, 60000, 100000, 150000, 200000]:
        cases.append(
            TaxCase(
                name=f"Self-employed ${income:,}",
                mstat=1,
                page=45,
                psemp=income,
            )
        )

    # 6. Mixed wages + self-employment
    for wage_income in [40000, 80000]:
        for se_income in [20000, 50000]:
            cases.append(
                TaxCase(
                    name=f"Wages ${wage_income:,} + SE ${se_income:,}",
                    mstat=1,
                    page=40,
                    pwages=wage_income,
                    psemp=se_income,
                )
            )

    # 7. Investment income scenarios
    for wage_income in [50000, 100000]:
        for dividend_income in [5000, 20000, 50000]:
            cases.append(
                TaxCase(
                    name=f"Wages ${wage_income:,} + Div ${dividend_income:,}",
                    mstat=1,
                    page=45,
                    pwages=wage_income,
                    dividends=dividend_income,
                )
            )

    # 8. Capital gains scenarios
    for wage_income in [60000, 120000]:
        for ltcg in [10000, 50000, 100000]:
            cases.append(
                TaxCase(
                    name=f"Wages ${wage_income:,} + LTCG ${ltcg:,}",
                    mstat=1,
                    page=50,
                    pwages=wage_income,
                    ltcg=ltcg,
                )
            )

    # 9. High income with itemized deductions
    for income in [200000, 400000]:
        cases.append(
            TaxCase(
                name=f"MFJ ${income:,} itemized",
                mstat=2,
                page=45,
                pwages=int(income * 0.6),
                sage=43,
                swages=int(income * 0.4),
                proptax=15000,
                mortgage=20000,
            )
        )

    # 10. Social Security recipients
    for ss_income in [20000, 35000, 50000]:
        for other_income in [0, 15000, 30000]:
            cases.append(
                TaxCase(
                    name=f"SS ${ss_income:,} + Other ${other_income:,}",
                    mstat=1,
                    page=68,
                    gssi=ss_income,
                    pwages=other_income,
                )
            )

    # 11. AMT-triggering scenarios (high income with large itemized deductions)
    # AMT is triggered when tentative minimum tax > regular tax
    # Key triggers: high SALT (added back for AMT), large ISO exercise
    # Note: Post-TCJA, AMT exemption is much higher ($133,300 joint, $85,700 single for 2024)
    # so fewer taxpayers are subject to AMT

    # High-income with large SALT (capped at $10k for regular tax, but fully added back for AMT)
    for income in [500000, 750000, 1000000]:
        cases.append(
            TaxCase(
                name=f"AMT - High income ${income:,}",
                mstat=2,  # Joint
                page=50,
                pwages=int(income * 0.6),
                sage=48,
                swages=int(income * 0.4),
                proptax=50000,  # High SALT
                mortgage=30000,
            )
        )

    # Single high earner - more likely to trigger AMT
    for income in [400000, 600000, 800000]:
        cases.append(
            TaxCase(
                name=f"AMT - Single high ${income:,}",
                mstat=1,
                page=45,
                pwages=income,
                proptax=30000,
                mortgage=20000,
            )
        )

    # Exemption phaseout range scenarios
    # Joint phaseout starts at $1,218,700 for 2024, Single at $609,350
    for income in [1200000, 1500000, 2000000]:
        cases.append(
            TaxCase(
                name=f"AMT phaseout - Joint ${income:,}",
                mstat=2,
                page=55,
                pwages=int(income * 0.6),
                sage=53,
                swages=int(income * 0.4),
                proptax=40000,
            )
        )

    return cases


def cases_to_taxsim_csv(cases: List[TaxCase]) -> str:
    """Convert test cases to TAXSIM CSV format."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Header row - using age1-age3 for dependent ages (TAXSIM preferred)
    headers = [
        "taxsimid",
        "year",
        "state",
        "mstat",
        "page",
        "sage",
        "depx",
        "age1",
        "age2",
        "age3",
        "pwages",
        "swages",
        "psemp",
        "ssemp",
        "dividends",
        "intrec",
        "stcg",
        "ltcg",
        "pensions",
        "gssi",
        "pui",
        "proptax",
        "mortgage",
        "childcare",
        "otheritem",
        "idtl",  # Request full output (2 = full)
    ]
    writer.writerow(headers)

    for i, case in enumerate(cases, start=1):
        row = [
            i,  # taxsimid
            case.year,
            case.state,
            case.mstat,
            case.page,
            case.sage,
            case.depx,
            case.age1,
            case.age2,
            case.age3,
            case.pwages,
            case.swages,
            case.psemp,
            case.ssemp,
            case.dividends,
            case.intrec,
            case.stcg,
            case.ltcg,
            case.pensions,
            case.gssi,
            case.pui,
            case.proptax,
            case.mortgage,
            case.childcare,
            case.otheritem,
            2,  # Full output
        ]
        writer.writerow(row)

    return output.getvalue()


def query_taxsim(csv_data: str, max_retries: int = 3) -> List[TaxSimResult]:
    """Send CSV data to TAXSIM API and parse results.

    Uses curl for multipart form upload per TAXSIM documentation:
    https://taxsim.nber.org/taxsim35/low-level-remote.html
    """
    url = "https://taxsim.nber.org/taxsim35/redirect.cgi"

    for attempt in range(max_retries):
        try:
            # Write CSV to temp file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".csv", delete=False
            ) as f:
                f.write(csv_data)
                temp_path = f.name

            try:
                # Use curl for multipart form upload
                result = subprocess.run(
                    [
                        "curl",
                        "-s",  # Silent
                        "-F",
                        f"txpydata.csv=@{temp_path}",
                        url,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=120,
                )

                if result.returncode != 0:
                    print(f"curl error: {result.stderr}")
                    continue

                result_text = result.stdout

            finally:
                # Clean up temp file
                Path(temp_path).unlink(missing_ok=True)

            # Parse CSV response
            results = []

            # TAXSIM returns space-separated or comma-separated values
            # First, try to detect the format
            lines = result_text.strip().split("\n")
            if not lines:
                print("Empty response from TAXSIM")
                continue

            # Check if it's an error response
            if "error" in lines[0].lower() or "<html" in lines[0].lower():
                print(f"TAXSIM error response: {lines[0][:200]}")
                continue

            # Parse the response - TAXSIM may return space or comma separated
            reader = csv.DictReader(io.StringIO(result_text))

            for row in reader:
                try:
                    result = TaxSimResult(
                        taxsim_id=int(float(row.get("taxsimid", 0))),
                        year=int(float(row.get("year", 0))),
                        state=int(float(row.get("state", 0))),
                        fiitax=float(row.get("fiitax", 0)),
                        siitax=float(row.get("siitax", 0)),
                        fica=float(row.get("fica", 0)),
                        frate=float(row.get("frate", 0)),
                        srate=float(row.get("srate", 0)),
                        ficar=float(row.get("ficar", 0)),
                        v10_agi=float(row.get("v10", 0)),
                        v11_ui_agi=float(row.get("v11", 0)),
                        v12_ss_agi=float(row.get("v12", 0)),
                        v13_zero_bracket=float(row.get("v13", 0)),
                        v14_exemptions=float(row.get("v14", 0)),
                        v15_exemption_phaseout=float(row.get("v15", 0)),
                        v16_deductions=float(row.get("v16", 0)),
                        v17_deduction_phaseout=float(row.get("v17", 0)),
                        v18_taxable_income=float(row.get("v18", 0)),
                        v19_tax_regular=float(row.get("v19", 0)),
                        v22_ctc=float(row.get("v22", 0)),
                        v23_ctc_refundable=float(row.get("v23", 0)),
                        v25_eitc=float(row.get("v25", 0)),
                        v26_amt=float(row.get("v26", 0)),
                        v27_fed_tax_before_credits=float(row.get("v27", 0)),
                        v28_fica=float(row.get("v28", 0)),
                    )
                    results.append(result)
                except (ValueError, KeyError) as e:
                    print(f"Error parsing TAXSIM row: {e}")
                    continue

            return results

        except subprocess.TimeoutExpired:
            print(f"TAXSIM request timeout (attempt {attempt + 1})")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            continue
        except Exception as e:
            print(f"TAXSIM API error (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            continue

    return []


def run_policyengine(case: TaxCase) -> PolicyEngineResult:
    """Run PolicyEngine-US calculation for a test case."""
    try:
        from policyengine_us import Simulation
    except ImportError:
        print("PolicyEngine-US not installed. Install with: pip install policyengine-us")
        return PolicyEngineResult()

    # Build situation
    people = {}
    tax_unit_members = []

    # Primary taxpayer
    primary_data = {
        "age": {case.year: case.page},
        "employment_income": {case.year: case.pwages},
        "self_employment_income": {case.year: case.psemp},
        "dividend_income": {case.year: case.dividends},
        "interest_income": {case.year: case.intrec},
        "short_term_capital_gains": {case.year: case.stcg},
        "long_term_capital_gains": {case.year: case.ltcg},
        "taxable_pension_income": {case.year: case.pensions},
        "social_security": {case.year: case.gssi},
        "unemployment_compensation": {case.year: case.pui},
    }

    # Add itemized deductions to primary taxpayer (person-level variables)
    if case.proptax > 0:
        primary_data["real_estate_taxes"] = {case.year: case.proptax}
    if case.mortgage > 0:
        primary_data["mortgage_interest"] = {case.year: case.mortgage}
    if case.otheritem > 0:
        primary_data["charitable_cash_donations"] = {case.year: case.otheritem}

    people["primary"] = primary_data
    tax_unit_members.append("primary")

    # Spouse (if MFJ)
    if case.mstat == 2 and case.sage > 0:
        people["spouse"] = {
            "age": {case.year: case.sage},
            "employment_income": {case.year: case.swages},
            "self_employment_income": {case.year: case.ssemp},
        }
        tax_unit_members.append("spouse")

    # Children - use specific ages from age1, age2, age3
    child_ages = [a for a in [case.age1, case.age2, case.age3] if a > 0]
    for i, age in enumerate(child_ages):
        child_id = f"child_{i}"
        people[child_id] = {
            "age": {case.year: age},
        }
        tax_unit_members.append(child_id)

    # Filing status mapping
    filing_status_map = {
        1: "SINGLE",
        2: "JOINT",
        3: "HEAD_OF_HOUSEHOLD",
        6: "SEPARATE",
    }
    filing_status = filing_status_map.get(case.mstat, "SINGLE")

    # Build tax unit
    tax_unit = {
        "members": tax_unit_members,
        "filing_status": {case.year: filing_status},
    }

    situation = {
        "people": people,
        "tax_units": {"tax_unit": tax_unit},
        "households": {
            "household": {
                "members": tax_unit_members,
                "state_code": {case.year: "TX"},  # No state income tax
            }
        },
    }

    try:
        sim = Simulation(situation=situation)

        result = PolicyEngineResult(
            adjusted_gross_income=float(
                sim.calculate("adjusted_gross_income", case.year)[0]
            ),
            taxable_income=float(sim.calculate("taxable_income", case.year)[0]),
            income_tax_before_credits=float(
                sim.calculate("income_tax_before_credits", case.year)[0]
            ),
            income_tax=float(sim.calculate("income_tax", case.year)[0]),
            eitc=float(sim.calculate("eitc", case.year)[0]),
            ctc=float(sim.calculate("ctc", case.year)[0]),
            refundable_ctc=float(sim.calculate("refundable_ctc", case.year)[0]),
            employee_social_security_tax=float(
                sim.calculate("employee_social_security_tax", case.year)[0]
            ),
            self_employment_tax=float(
                sim.calculate("self_employment_tax", case.year)[0]
            ),
        )

        # Try to get AMT variables (may not exist in all PE versions)
        try:
            result.amt_income = float(
                sim.calculate("alternative_minimum_taxable_income", case.year)[0]
            )
            result.amt = float(
                sim.calculate("alternative_minimum_tax", case.year)[0]
            )
        except Exception:
            # AMT variables may not be implemented in PolicyEngine-US yet
            pass

        return result

    except Exception as e:
        print(f"PolicyEngine error for {case.name}: {e}")
        return PolicyEngineResult()


def run_comparisons(cases: List[TaxCase]) -> List[ComparisonResult]:
    """Run all comparisons between TAXSIM and PolicyEngine."""
    print(f"Running {len(cases)} test cases...")

    # Query TAXSIM for all cases at once
    print("Querying TAXSIM API...")
    csv_data = cases_to_taxsim_csv(cases)
    taxsim_results = query_taxsim(csv_data)

    # Index TAXSIM results by ID
    taxsim_by_id = {r.taxsim_id: r for r in taxsim_results}

    # Run PolicyEngine for each case
    print("Running PolicyEngine calculations...")
    comparisons = []

    for i, case in enumerate(cases, start=1):
        taxsim_result = taxsim_by_id.get(i)
        pe_result = run_policyengine(case)

        comparison = ComparisonResult(
            case=case,
            taxsim=taxsim_result,
            policyengine=pe_result,
        )

        if taxsim_result is None:
            comparison.errors.append("TAXSIM result missing")

        comparisons.append(comparison)

        if i % 10 == 0:
            print(f"  Processed {i}/{len(cases)} cases...")

    return comparisons


def compute_comparison_stats(comparisons: List[ComparisonResult]) -> Dict:
    """Compute comparison statistics."""
    import numpy as np

    stats = {
        "agi": {"diffs": [], "pe": [], "ts": []},
        "taxable_income": {"diffs": [], "pe": [], "ts": []},
        "federal_tax": {"diffs": [], "pe": [], "ts": []},
        "eitc": {"diffs": [], "pe": [], "ts": []},
        "ctc": {"diffs": [], "pe": [], "ts": []},
        "fica": {"diffs": [], "pe": [], "ts": []},
        "amti": {"diffs": [], "pe": [], "ts": []},
    }

    for c in comparisons:
        if c.taxsim is None or c.policyengine is None:
            continue

        # AGI comparison
        stats["agi"]["pe"].append(c.policyengine.adjusted_gross_income)
        stats["agi"]["ts"].append(c.taxsim.v10_agi)
        stats["agi"]["diffs"].append(
            c.policyengine.adjusted_gross_income - c.taxsim.v10_agi
        )

        # Taxable income
        stats["taxable_income"]["pe"].append(c.policyengine.taxable_income)
        stats["taxable_income"]["ts"].append(c.taxsim.v18_taxable_income)
        stats["taxable_income"]["diffs"].append(
            c.policyengine.taxable_income - c.taxsim.v18_taxable_income
        )

        # Federal tax
        stats["federal_tax"]["pe"].append(c.policyengine.income_tax)
        stats["federal_tax"]["ts"].append(c.taxsim.fiitax)
        stats["federal_tax"]["diffs"].append(
            c.policyengine.income_tax - c.taxsim.fiitax
        )

        # EITC
        stats["eitc"]["pe"].append(c.policyengine.eitc)
        stats["eitc"]["ts"].append(c.taxsim.v25_eitc)
        stats["eitc"]["diffs"].append(c.policyengine.eitc - c.taxsim.v25_eitc)

        # CTC
        stats["ctc"]["pe"].append(c.policyengine.ctc)
        stats["ctc"]["ts"].append(c.taxsim.v22_ctc + c.taxsim.v23_ctc_refundable)
        stats["ctc"]["diffs"].append(
            c.policyengine.ctc - (c.taxsim.v22_ctc + c.taxsim.v23_ctc_refundable)
        )

        # FICA
        pe_fica = (
            c.policyengine.employee_social_security_tax
            + c.policyengine.self_employment_tax
        )
        stats["fica"]["pe"].append(pe_fica)
        stats["fica"]["ts"].append(c.taxsim.fica)
        stats["fica"]["diffs"].append(pe_fica - c.taxsim.fica)

        # AMTI (only if PolicyEngine has AMT values)
        if c.policyengine.amt_income > 0 or c.taxsim.v26_amt > 0:
            stats["amti"]["pe"].append(c.policyengine.amt_income)
            stats["amti"]["ts"].append(c.taxsim.v26_amt)
            stats["amti"]["diffs"].append(
                c.policyengine.amt_income - c.taxsim.v26_amt
            )

    # Compute summary stats for each variable
    summary = {}
    for var, data in stats.items():
        if not data["diffs"]:
            continue

        diffs = np.array(data["diffs"])
        pe_vals = np.array(data["pe"])
        ts_vals = np.array(data["ts"])

        # Compute various metrics
        summary[var] = {
            "n": len(diffs),
            "mean_diff": float(np.mean(diffs)),
            "median_diff": float(np.median(diffs)),
            "std_diff": float(np.std(diffs)),
            "mae": float(np.mean(np.abs(diffs))),
            "max_abs_diff": float(np.max(np.abs(diffs))),
            "pe_mean": float(np.mean(pe_vals)),
            "ts_mean": float(np.mean(ts_vals)),
            "correlation": float(np.corrcoef(pe_vals, ts_vals)[0, 1])
            if len(pe_vals) > 1
            else 0.0,
            "pct_exact": float(np.mean(np.abs(diffs) < 1) * 100),
            "pct_within_10": float(np.mean(np.abs(diffs) < 10) * 100),
            "pct_within_100": float(np.mean(np.abs(diffs) < 100) * 100),
        }

    return summary


def generate_dashboard(
    comparisons: List[ComparisonResult], stats: Dict, cases: List[TaxCase]
) -> str:
    """Generate markdown dashboard."""
    lines = [
        "# TAXSIM Validation Dashboard",
        "",
        f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        "",
        "Comparison of PolicyEngine-US against NBER TAXSIM 35 API.",
        "",
        "## Summary",
        "",
        f"- **Total test cases:** {len(cases)}",
        f"- **Successful comparisons:** {sum(1 for c in comparisons if c.taxsim is not None)}",
        f"- **Tax year:** 2023 (TAXSIM 35 max supported year)",
        "",
        "## Accuracy Metrics",
        "",
        "| Variable | N | Mean Diff | MAE | Max Abs Diff | Correlation | % Exact | % Within $10 | % Within $100 |",
        "|----------|---|-----------|-----|--------------|-------------|---------|--------------|---------------|",
    ]

    var_names = {
        "agi": "AGI",
        "taxable_income": "Taxable Income",
        "federal_tax": "Federal Tax",
        "eitc": "EITC",
        "ctc": "CTC",
        "fica": "FICA",
        "amti": "AMTI",
    }

    for var, s in stats.items():
        display_name = var_names.get(var, var)
        lines.append(
            f"| {display_name} | {s['n']} | ${s['mean_diff']:,.0f} | "
            f"${s['mae']:,.0f} | ${s['max_abs_diff']:,.0f} | "
            f"{s['correlation']:.3f} | {s['pct_exact']:.1f}% | "
            f"{s['pct_within_10']:.1f}% | {s['pct_within_100']:.1f}% |"
        )

    lines.extend(
        [
            "",
            "## Detailed Comparison",
            "",
            "### Sample Scenarios",
            "",
            "| Scenario | PE Tax | TS Tax | Diff | PE EITC | TS EITC | PE CTC | TS CTC |",
            "|----------|--------|--------|------|---------|---------|--------|--------|",
        ]
    )

    # Show first 30 comparisons
    for c in comparisons[:30]:
        if c.taxsim is None or c.policyengine is None:
            continue

        diff = c.policyengine.income_tax - c.taxsim.fiitax
        ts_ctc = c.taxsim.v22_ctc + c.taxsim.v23_ctc_refundable

        lines.append(
            f"| {c.case.name} | ${c.policyengine.income_tax:,.0f} | "
            f"${c.taxsim.fiitax:,.0f} | ${diff:,.0f} | "
            f"${c.policyengine.eitc:,.0f} | ${c.taxsim.v25_eitc:,.0f} | "
            f"${c.policyengine.ctc:,.0f} | ${ts_ctc:,.0f} |"
        )

    # Identify largest discrepancies
    lines.extend(
        [
            "",
            "### Largest Discrepancies (Federal Tax)",
            "",
            "| Scenario | PE Tax | TS Tax | Diff | PE AGI | TS AGI |",
            "|----------|--------|--------|------|--------|--------|",
        ]
    )

    # Sort by absolute difference
    sorted_comps = sorted(
        [c for c in comparisons if c.taxsim is not None and c.policyengine is not None],
        key=lambda c: abs(c.policyengine.income_tax - c.taxsim.fiitax),
        reverse=True,
    )

    for c in sorted_comps[:10]:
        diff = c.policyengine.income_tax - c.taxsim.fiitax
        lines.append(
            f"| {c.case.name} | ${c.policyengine.income_tax:,.0f} | "
            f"${c.taxsim.fiitax:,.0f} | ${diff:,.0f} | "
            f"${c.policyengine.adjusted_gross_income:,.0f} | "
            f"${c.taxsim.v10_agi:,.0f} |"
        )

    # EITC-specific analysis
    lines.extend(
        [
            "",
            "### EITC Discrepancies",
            "",
            "| Scenario | PE EITC | TS EITC | Diff | Wages | # Kids |",
            "|----------|---------|---------|------|-------|--------|",
        ]
    )

    eitc_cases = [
        c
        for c in comparisons
        if c.taxsim is not None
        and c.policyengine is not None
        and (c.taxsim.v25_eitc > 0 or c.policyengine.eitc > 0)
    ]
    eitc_cases_sorted = sorted(
        eitc_cases,
        key=lambda c: abs(c.policyengine.eitc - c.taxsim.v25_eitc),
        reverse=True,
    )

    for c in eitc_cases_sorted[:15]:
        diff = c.policyengine.eitc - c.taxsim.v25_eitc
        lines.append(
            f"| {c.case.name} | ${c.policyengine.eitc:,.0f} | "
            f"${c.taxsim.v25_eitc:,.0f} | ${diff:,.0f} | "
            f"${c.case.pwages:,.0f} | {c.case.depx} |"
        )

    # CTC-specific analysis
    lines.extend(
        [
            "",
            "### CTC Discrepancies",
            "",
            "| Scenario | PE CTC | TS CTC | TS Refund | Diff | # Kids |",
            "|----------|--------|--------|-----------|------|--------|",
        ]
    )

    ctc_cases = [
        c
        for c in comparisons
        if c.taxsim is not None
        and c.policyengine is not None
        and (c.taxsim.v22_ctc + c.taxsim.v23_ctc_refundable > 0 or c.policyengine.ctc > 0)
    ]
    ctc_cases_sorted = sorted(
        ctc_cases,
        key=lambda c: abs(
            c.policyengine.ctc - (c.taxsim.v22_ctc + c.taxsim.v23_ctc_refundable)
        ),
        reverse=True,
    )

    for c in ctc_cases_sorted[:15]:
        ts_ctc_total = c.taxsim.v22_ctc + c.taxsim.v23_ctc_refundable
        diff = c.policyengine.ctc - ts_ctc_total
        lines.append(
            f"| {c.case.name} | ${c.policyengine.ctc:,.0f} | "
            f"${c.taxsim.v22_ctc:,.0f} | ${c.taxsim.v23_ctc_refundable:,.0f} | "
            f"${diff:,.0f} | {c.case.depx} |"
        )

    lines.extend(
        [
            "",
            "## Test Scenario Categories",
            "",
            "1. **Single filers** - Income levels $15K to $400K",
            "2. **Married filing jointly** - Income levels $40K to $400K",
            "3. **Head of Household with children** - EITC eligibility scenarios",
            "4. **MFJ with children** - CTC eligibility scenarios",
            "5. **Self-employment income** - SE tax calculations",
            "6. **Mixed wages + self-employment** - Combined income",
            "7. **Investment income** - Dividends and interest",
            "8. **Capital gains** - Long-term capital gains",
            "9. **High income itemized** - Mortgage and property tax deductions",
            "10. **Social Security recipients** - Benefit taxation",
            "",
            "## Known Differences",
            "",
            "### TAXSIM vs PolicyEngine",
            "",
            "- **Dependent handling**: TAXSIM uses `depx` count and `age1-age3` for ages; "
            "PolicyEngine models individual dependents with specific attributes",
            "- **Head of Household**: Filing status determination may differ",
            "- **EITC phase-out**: Minor differences in earned income calculation",
            "- **CTC refundability**: ACTC (refundable portion) calculation differs",
            "- **Self-employment tax**: TAXSIM may use different SE income calculation",
            "",
            "## Methodology",
            "",
            "1. Generate standardized test cases covering key scenarios",
            "2. Submit batch to TAXSIM 35 API (https://taxsim.nber.org/taxsim35/)",
            "3. Run equivalent calculations in PolicyEngine-US",
            "4. Compare key outputs: AGI, taxable income, tax liability, credits",
            "5. Track discrepancies and investigate systematic differences",
            "",
            "## References",
            "",
            "- [TAXSIM 35 Documentation](https://taxsim.nber.org/taxsim35/)",
            "- [PolicyEngine-US Documentation](https://policyengine.org/us/research)",
            "- [Cosilico US Encodings](https://github.com/CosilicoAI/cosilico-us)",
        ]
    )

    return "\n".join(lines)


def main():
    print("TAXSIM Validation Script")
    print("=" * 50)

    # Generate test cases
    cases = generate_test_cases()
    print(f"Generated {len(cases)} test cases")

    # Run comparisons
    comparisons = run_comparisons(cases)

    # Compute statistics
    stats = compute_comparison_stats(comparisons)

    # Generate dashboard
    dashboard = generate_dashboard(comparisons, stats, cases)

    # Write to docs
    output_path = Path(__file__).parent.parent / "docs" / "TAXSIM_VALIDATION.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(dashboard)

    print(f"\nDashboard written to {output_path}")
    print("\nSummary:")
    for var, s in stats.items():
        print(f"  {var}: MAE=${s['mae']:,.0f}, correlation={s['correlation']:.3f}")


if __name__ == "__main__":
    main()
