"""
Sample company financial datasets for testing the AI CFO System.
Three companies covering SaaS, Manufacturing, and Non-Profit sectors.
Import: from data.sample_companies import COMPANIES, get_company
"""

# ─────────────────────────────────────────────────────────────────────────────
#  COMPANY 1 — NovaTech Solutions Inc.  (SaaS / High Growth)
# ─────────────────────────────────────────────────────────────────────────────
NOVATECH = {
    "_meta": {
        "name":    "NovaTech Solutions Inc.",
        "ticker":  "NVTC",
        "cik":     "0001234567",
        "sector":  "SaaS / Cloud Software",
        "period":  "Q1 2026",
        "currency":"USD",
        "note":    "High-growth B2B SaaS — ARR $51M, NRR 118%",
    },

    # ── Income Statement ───────────────────────────────────────────────────
    "revenue":             12_840_000,
    "cogs":                 3_594_000,
    "gross_profit":         9_246_000,
    "operating_expenses":   6_120_000,
    "rd_expense":           2_430_000,
    "sg_a_expense":         3_690_000,
    "ebitda":               3_126_000,
    "depreciation":           312_000,
    "ebit":                 2_814_000,
    "interest_expense":       210_000,
    "pre_tax_income":       2_604_000,
    "tax_provision":          573_000,
    "net_income":           2_031_000,

    # ── Balance Sheet ──────────────────────────────────────────────────────
    "total_assets":        58_400_000,
    "current_assets":      24_100_000,
    "cash":                11_250_000,
    "accounts_receivable":  8_640_000,
    "inventory":              210_000,
    "prepaid_expenses":     4_000_000,
    "total_equity":        34_200_000,
    "current_liabilities":  9_800_000,
    "accounts_payable":     3_150_000,
    "deferred_revenue":     4_200_000,
    "total_debt":          14_000_000,
    "long_term_debt":      11_800_000,

    # ── Cash Flow ──────────────────────────────────────────────────────────
    "cash_from_operations":  3_840_000,
    "capex":                   780_000,
    "free_cash_flow":        3_060_000,
    "monthly_cash_burn":             0,

    # ── Share Data ─────────────────────────────────────────────────────────
    "shares_outstanding":   8_200_000,
    "diluted_shares":       8_650_000,

    # ── Lease / ASC 842 / IFRS 16 ─────────────────────────────────────────
    "rou_assets":           4_800_000,
    "lease_liability":      4_620_000,
    "operating_lease_expense": 360_000,

    # ── Goodwill / Intangibles ─────────────────────────────────────────────
    "goodwill":             9_600_000,
    "goodwill_impairment_test_date": "2026-01-31",
    "impairment_test_performed":     True,
    "impairment_tested_at_cgu_level":True,

    # ── Credit Losses (ASC 310/326 CECL / IFRS 9 ECL) ─────────────────────
    "allowance_for_credit_losses":  432_000,
    "ecl_stage1_allowance":         258_000,
    "ecl_stage2_allowance":         129_000,
    "ecl_stage3_allowance":          45_000,

    # ── GAAP / IFRS policy flags ───────────────────────────────────────────
    "revenue_recognition_policy":        "ASC 606 5-step model",
    "inventory_cost_method":             "fifo",
    "interest_cash_flow_classification": "operating",
    "cash_flow_policy_consistent":       True,
    "comparative_period_presented":      True,
    "publicly_listed":                   True,
    "qualifying_development_projects":   True,
    "rd_dev_capitalizable_pct":          0.35,

    # ── Budget vs Actuals ──────────────────────────────────────────────────
    "actuals": {
        "revenue":      12_840_000,
        "cogs":          3_594_000,
        "gross_profit":  9_246_000,
        "ebitda":        3_126_000,
        "rd_expense":    2_430_000,
        "sg_a":          3_690_000,
    },
    "budget": {
        "revenue":      11_500_000,
        "cogs":          3_335_000,
        "gross_profit":  8_165_000,
        "ebitda":        2_700_000,
        "rd_expense":    2_100_000,
        "sg_a":          3_365_000,
    },

    # ── Historical Revenue (9 quarters) ───────────────────────────────────
    "historical_revenue": [
        7_200_000,   # Q1 2024
        7_810_000,   # Q2 2024
        8_450_000,   # Q3 2024
        9_120_000,   # Q4 2024
        9_980_000,   # Q1 2025
       10_620_000,   # Q2 2025
       11_310_000,   # Q3 2025
       11_870_000,   # Q4 2025
       12_840_000,   # Q1 2026
    ],

    # ── Segments ───────────────────────────────────────────────────────────
    "segments": [
        {"name": "Enterprise",            "revenue": 7_704_000, "gross_profit": 5_852_400, "assets": 32_000_000},
        {"name": "SMB",                   "revenue": 3_852_000, "gross_profit": 2_813_160, "assets": 16_000_000},
        {"name": "Professional Services", "revenue": 1_284_000, "gross_profit":   580_440, "assets":  6_000_000},
    ],

    # ── SaaS Metrics ───────────────────────────────────────────────────────
    "arr":             51_360_000,
    "nrr_pct":         118,
    "churn_rate_pct":  4.2,
    "headcount":       214,
    "revenue_per_employee": 60_000,
}


# ─────────────────────────────────────────────────────────────────────────────
#  COMPANY 2 — Meridian Manufacturing Co.  (Industrial / Mid-Market)
# ─────────────────────────────────────────────────────────────────────────────
MERIDIAN = {
    "_meta": {
        "name":    "Meridian Manufacturing Co.",
        "ticker":  "MRDM",
        "cik":     "0007654321",
        "sector":  "Industrial Manufacturing",
        "period":  "Q1 2026",
        "currency":"USD",
        "note":    "Mid-market manufacturer — high COGS, LIFO prohibited under IFRS",
    },

    # ── Income Statement ───────────────────────────────────────────────────
    "revenue":             28_400_000,
    "cogs":                19_880_000,
    "gross_profit":         8_520_000,
    "operating_expenses":   5_110_000,
    "rd_expense":             840_000,
    "sg_a_expense":         4_270_000,
    "ebitda":               3_410_000,
    "depreciation":         1_250_000,
    "ebit":                 2_160_000,
    "interest_expense":       580_000,
    "pre_tax_income":       1_580_000,
    "tax_provision":          379_000,
    "net_income":           1_201_000,

    # ── Balance Sheet ──────────────────────────────────────────────────────
    "total_assets":        84_600_000,
    "current_assets":      31_200_000,
    "cash":                 4_750_000,
    "accounts_receivable": 14_320_000,
    "inventory":            9_840_000,
    "prepaid_expenses":     2_290_000,
    "total_equity":        38_100_000,
    "current_liabilities": 17_400_000,
    "accounts_payable":     8_960_000,
    "deferred_revenue":       420_000,
    "total_debt":          28_900_000,
    "long_term_debt":      22_300_000,

    # ── Cash Flow ──────────────────────────────────────────────────────────
    "cash_from_operations":  2_140_000,
    "capex":                 3_800_000,
    "free_cash_flow":       -1_660_000,
    "monthly_cash_burn":       553_000,

    # ── Share Data ─────────────────────────────────────────────────────────
    "shares_outstanding":   5_400_000,
    "diluted_shares":       5_520_000,

    # ── Lease / ASC 842 / IFRS 16 ─────────────────────────────────────────
    "rou_assets":           6_200_000,
    "lease_liability":      6_050_000,
    "operating_lease_expense": 480_000,

    # ── Goodwill ───────────────────────────────────────────────────────────
    "goodwill":             4_200_000,
    "goodwill_impairment_test_date": "2026-01-15",
    "impairment_test_performed":     True,
    "impairment_tested_at_cgu_level":True,

    # ── Credit Losses ─────────────────────────────────────────────────────
    "allowance_for_credit_losses":  716_000,
    "ecl_stage1_allowance":         430_000,
    "ecl_stage2_allowance":         215_000,
    "ecl_stage3_allowance":          71_000,

    # ── GAAP / IFRS policy flags ───────────────────────────────────────────
    "revenue_recognition_policy":        "ASC 606 — point-in-time delivery",
    "inventory_cost_method":             "fifo",
    "interest_cash_flow_classification": "operating",
    "cash_flow_policy_consistent":       True,
    "comparative_period_presented":      True,
    "publicly_listed":                   True,
    "qualifying_development_projects":   False,
    "rd_dev_capitalizable_pct":          0.0,

    # ── Budget vs Actuals ──────────────────────────────────────────────────
    "actuals": {
        "revenue":      28_400_000,
        "cogs":         19_880_000,
        "gross_profit":  8_520_000,
        "ebitda":        3_410_000,
        "rd_expense":      840_000,
        "sg_a":          4_270_000,
    },
    "budget": {
        "revenue":      30_000_000,
        "cogs":         20_700_000,
        "gross_profit":  9_300_000,
        "ebitda":        4_200_000,
        "rd_expense":      900_000,
        "sg_a":          4_100_000,
    },

    # ── Historical Revenue ─────────────────────────────────────────────────
    "historical_revenue": [
        22_100_000,  # Q1 2024
        24_800_000,  # Q2 2024
        26_400_000,  # Q3 2024
        25_900_000,  # Q4 2024
        27_200_000,  # Q1 2025
        29_100_000,  # Q2 2025
        30_800_000,  # Q3 2025
        29_600_000,  # Q4 2025
        28_400_000,  # Q1 2026
    ],

    # ── Segments ───────────────────────────────────────────────────────────
    "segments": [
        {"name": "Aerospace Components",  "revenue": 12_780_000, "gross_profit": 4_473_000, "assets": 38_000_000},
        {"name": "Industrial Equipment",  "revenue":  9_940_000, "gross_profit": 2_982_000, "assets": 28_000_000},
        {"name": "Defense Contracts",     "revenue":  5_680_000, "gross_profit": 1_704_000, "assets": 18_600_000},
    ],

    # ── Operational ────────────────────────────────────────────────────────
    "arr":             0,
    "nrr_pct":         0,
    "churn_rate_pct":  0,
    "headcount":       412,
    "revenue_per_employee": 69_000,
}


# ─────────────────────────────────────────────────────────────────────────────
#  COMPANY 3 — Horizon Community Foundation  (Non-Profit / 501(c)(3))
# ─────────────────────────────────────────────────────────────────────────────
HORIZON = {
    "_meta": {
        "name":    "Horizon Community Foundation",
        "ticker":  "N/A",
        "cik":     "0009988776",
        "sector":  "Non-Profit / 501(c)(3)",
        "period":  "FY 2025",
        "currency":"USD",
        "note":    "Non-profit — ASC 958; no EPS; restricted vs unrestricted net assets",
    },

    # ── Statement of Activities (P&L equivalent) ───────────────────────────
    "revenue":              6_240_000,    # total support & revenue
    "cogs":                 1_248_000,    # program direct costs
    "gross_profit":         4_992_000,    # program gross surplus
    "operating_expenses":   3_744_000,    # program + support services
    "rd_expense":             312_000,    # research grants
    "sg_a_expense":         1_560_000,    # management & general + fundraising
    "ebitda":               1_248_000,
    "depreciation":           187_000,
    "ebit":                 1_061_000,
    "interest_expense":        42_000,
    "pre_tax_income":       1_019_000,    # change in net assets
    "tax_provision":                0,    # tax-exempt
    "net_income":           1_019_000,    # change in net assets

    # ── Balance Sheet (Statement of Financial Position) ────────────────────
    "total_assets":        18_400_000,
    "current_assets":       4_200_000,
    "cash":                 2_860_000,
    "accounts_receivable":    840_000,
    "inventory":               45_000,    # program supplies
    "prepaid_expenses":       455_000,
    "total_equity":        14_100_000,    # net assets
    "current_liabilities":  1_960_000,
    "accounts_payable":       380_000,
    "deferred_revenue":       920_000,    # deferred grant revenue
    "total_debt":           2_340_000,
    "long_term_debt":       2_100_000,

    # ── Cash Flow ──────────────────────────────────────────────────────────
    "cash_from_operations":   980_000,
    "capex":                  220_000,
    "free_cash_flow":         760_000,
    "monthly_cash_burn":            0,

    # ── Share Data (N/A — non-profit) ─────────────────────────────────────
    "shares_outstanding":           0,
    "diluted_shares":               0,

    # ── Lease ─────────────────────────────────────────────────────────────
    "rou_assets":             840_000,
    "lease_liability":        820_000,
    "operating_lease_expense": 96_000,

    # ── Goodwill ───────────────────────────────────────────────────────────
    "goodwill":                     0,
    "goodwill_impairment_test_date": "N/A",
    "impairment_test_performed":    False,
    "impairment_tested_at_cgu_level":False,

    # ── Credit Losses ─────────────────────────────────────────────────────
    "allowance_for_credit_losses":  42_000,
    "ecl_stage1_allowance":         30_000,
    "ecl_stage2_allowance":          9_000,
    "ecl_stage3_allowance":          3_000,

    # ── GAAP / IFRS policy flags ───────────────────────────────────────────
    "revenue_recognition_policy":        "ASC 958 / ASC 606 — conditional grants",
    "inventory_cost_method":             "fifo",
    "interest_cash_flow_classification": "operating",
    "cash_flow_policy_consistent":       True,
    "comparative_period_presented":      True,
    "publicly_listed":                   False,
    "qualifying_development_projects":   False,
    "rd_dev_capitalizable_pct":          0.0,

    # ── Budget vs Actuals ──────────────────────────────────────────────────
    "actuals": {
        "revenue":     6_240_000,
        "cogs":        1_248_000,
        "gross_profit":4_992_000,
        "ebitda":      1_248_000,
        "rd_expense":    312_000,
        "sg_a":        1_560_000,
    },
    "budget": {
        "revenue":     5_800_000,
        "cogs":        1_160_000,
        "gross_profit":4_640_000,
        "ebitda":      1_100_000,
        "rd_expense":    290_000,
        "sg_a":        1_500_000,
    },

    # ── Historical Revenue ─────────────────────────────────────────────────
    "historical_revenue": [
        4_100_000,   # FY 2018
        4_480_000,   # FY 2019
        3_920_000,   # FY 2020  (COVID impact)
        4_200_000,   # FY 2021
        4_850_000,   # FY 2022
        5_310_000,   # FY 2023
        5_780_000,   # FY 2024
        6_240_000,   # FY 2025
    ],

    # ── Segments (Programs) ────────────────────────────────────────────────
    "segments": [
        {"name": "Education Grants",      "revenue": 2_808_000, "gross_profit": 2_246_400, "assets":  8_280_000},
        {"name": "Community Health",      "revenue": 2_184_000, "gross_profit": 1_747_200, "assets":  6_440_000},
        {"name": "Workforce Development", "revenue": 1_248_000, "gross_profit":   998_400, "assets":  3_680_000},
    ],

    # ── Non-Profit Specific ────────────────────────────────────────────────
    "arr":             0,
    "nrr_pct":         0,
    "churn_rate_pct":  0,
    "headcount":       68,
    "revenue_per_employee": 91_765,

    # ── Non-profit net asset classification (ASC 958) ──────────────────────
    "net_assets_without_restrictions":  8_460_000,
    "net_assets_with_restrictions":     5_640_000,
    "total_net_assets":                14_100_000,
    "restricted_grants_receivable":     1_240_000,
    "endowment_fund_balance":           4_200_000,
    "program_efficiency_pct":           80.2,    # program costs / total expenses
}


# ─────────────────────────────────────────────────────────────────────────────
#  REGISTRY
# ─────────────────────────────────────────────────────────────────────────────

COMPANIES = {
    "novatech": NOVATECH,
    "meridian":  MERIDIAN,
    "horizon":   HORIZON,
}


def get_company(key: str) -> dict:
    """Return company data dict by key ('novatech', 'meridian', 'horizon')."""
    if key not in COMPANIES:
        raise KeyError(f"Unknown company '{key}'. Available: {list(COMPANIES)}")
    return COMPANIES[key]


def list_companies() -> list:
    """Return list of (key, name, sector, period) tuples."""
    return [
        (k, v["_meta"]["name"], v["_meta"]["sector"], v["_meta"]["period"])
        for k, v in COMPANIES.items()
    ]
