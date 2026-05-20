"""
20-document fallback knowledge base.
Used when pgvector is unavailable — in-memory cosine similarity search.
"""
from typing import Any, Dict, List

KNOWLEDGE_BASE: List[Dict[str, Any]] = [
    # ── Finance Knowledge (4 docs) ──────────────────────────────────────────
    {
        "id": "kb001",
        "title": "EBITDA Standards and Non-GAAP Reconciliation",
        "category": "finance",
        "min_role": "analyst",
        "content": (
            "EBITDA (Earnings Before Interest, Taxes, Depreciation, and Amortization) is a non-GAAP "
            "metric widely used to assess operational performance. Under SEC guidance, public companies "
            "must reconcile EBITDA to the nearest GAAP measure (net income). EBITDA removes financing "
            "decisions (interest), tax strategies (taxes), and non-cash charges (D&A). "
            "EBITDA margin benchmarks by industry: SaaS 15-25%, Manufacturing 8-15%, Retail 3-8%, "
            "Healthcare 12-20%. IFRS 16 causes EBITDA to be higher vs GAAP ASC 842 because operating "
            "lease expenses are reclassified from SG&A (above EBITDA) to D&A + interest (below EBITDA). "
            "Non-GAAP reconciliation requires disclosure of all adjustments. "
            "Adjusted EBITDA commonly excludes: stock-based compensation, restructuring charges, "
            "acquisition costs, and non-recurring items."
        ),
    },
    {
        "id": "kb002",
        "title": "Working Capital Management — CCC, DSO, DPO, DIO",
        "category": "finance",
        "min_role": "analyst",
        "content": (
            "Cash Conversion Cycle (CCC) = DSO + DIO - DPO. "
            "DSO (Days Sales Outstanding) = AR / (Revenue/365). Target: industry-specific; SaaS <30 days, "
            "Manufacturing 45-60 days. DSO >90 days indicates collection risk. "
            "DIO (Days Inventory Outstanding) = Inventory / (COGS/365). Lower is better; measures inventory efficiency. "
            "DPO (Days Payable Outstanding) = AP / (COGS/365). Higher DPO preserves cash. "
            "Shorter CCC = faster cash generation. Negative CCC (e.g., Amazon, Costco) means collecting "
            "cash before paying suppliers — powerful cash flow advantage. "
            "Working Capital = Current Assets - Current Liabilities. Current ratio <1.0 = liquidity risk. "
            "Quick ratio = (Current Assets - Inventory) / Current Liabilities. Target >1.0. "
            "Working capital optimization levers: accelerate collections (e-invoicing, early payment discounts), "
            "extend payables (supply chain finance), reduce inventory (JIT, demand forecasting)."
        ),
    },
    {
        "id": "kb003",
        "title": "Variance Analysis Methodology and Board Commentary",
        "category": "finance",
        "min_role": "analyst",
        "content": (
            "Variance analysis compares actuals to budget (or prior year) to identify performance gaps. "
            "SAB 99 materiality threshold: 5% variance triggers qualitative + quantitative analysis. "
            "Variance decomposition: Price variance = (Actual Price - Budget Price) × Actual Volume. "
            "Volume variance = (Actual Volume - Budget Volume) × Budget Price. "
            "Mix variance applies when product/customer mix shifts. "
            "Board commentary structure: Lead with 'so what' before 'what'. "
            "Three-part structure: (1) What happened — the number; (2) Why — root cause; "
            "(3) What now — action and owner. "
            "Material variances must be explained: distinguish permanent vs one-time. "
            "FY outlook impact: annualize the variance, note whether it's expected to reverse. "
            "Common revenue variance drivers: pricing changes, volume shortfalls, product mix shift, "
            "deal timing slippage, currency impact. "
            "Common cost variance drivers: headcount vs plan, vendor rate changes, project timing, "
            "one-time charges, volume-driven costs."
        ),
    },
    {
        "id": "kb004",
        "title": "Board Report Standards — Pack Structure and Narrative Rules",
        "category": "finance",
        "min_role": "analyst",
        "content": (
            "Board-level financial report structure: "
            "1. Executive Summary (1 page max) — lead with EPS and 1-2 key metrics, then 3-5 bullets. "
            "2. P&L performance vs budget with variance explanations. "
            "3. Balance sheet and cash flow highlights. "
            "4. KPI dashboard — visual, benchmarked. "
            "5. Risks and opportunities (3-5 each, quantified). "
            "6. Action plan with owners and deadlines. "
            "7. Compliance and disclosure notes. "
            "Narrative rules: No jargon without definition. Every claim supported by a number. "
            "Distinguish actuals from estimates. Flag all assumptions. "
            "Audience calibration: Board members are not CFOs — explain accounting treatments briefly. "
            "Investor report: emphasize forward-looking guidance, growth metrics, competitive context. "
            "Audit report: emphasize compliance, internal controls, going concern assessment. "
            "Decimal precision: report in $K or $M consistently throughout document."
        ),
    },

    # ── US GAAP ASC Standards (8 docs) ──────────────────────────────────────
    {
        "id": "gaap01",
        "title": "ASC 606 — Revenue Recognition (5-Step Model)",
        "category": "gaap",
        "min_role": "analyst",
        "content": (
            "ASC 606 — Revenue from Contracts with Customers. Effective for public companies 2018. "
            "5-Step Model: "
            "Step 1: Identify the contract(s) with a customer — written, oral, or implied. "
            "Step 2: Identify the performance obligations — distinct goods or services. "
            "Step 3: Determine the transaction price — variable consideration, financing components. "
            "Step 4: Allocate the transaction price — standalone selling prices, SSP methods. "
            "Step 5: Recognize revenue when (or as) each performance obligation is satisfied. "
            "Contract assets arise when entity performs before customer pays. "
            "Contract liabilities (deferred revenue) arise when customer pays before entity performs. "
            "Variable consideration must be estimated and constrained (cumulative catch-up method). "
            "Principal vs agent: principal recognizes gross revenue; agent recognizes net (commission). "
            "Software: distinct licenses at a point in time; SaaS over the subscription period. "
            "Disclosure: disaggregation of revenue, remaining performance obligations, significant judgments."
        ),
    },
    {
        "id": "gaap02",
        "title": "ASC 842 — Leases (Dual Model)",
        "category": "gaap",
        "min_role": "analyst",
        "content": (
            "ASC 842 — Leases. Effective for public companies 2019. "
            "All leases >12 months must be recognized on balance sheet as ROU asset + lease liability. "
            "DUAL MODEL: Finance leases vs Operating leases. "
            "Finance lease criteria (any one): transfer of ownership, purchase option likely to exercise, "
            "lease term = major part of economic life (75% bright line), PV of payments = substantially all FV (90% bright line), "
            "specialized nature. "
            "Finance lease P&L: interest expense + depreciation (front-loaded). "
            "Operating lease P&L: straight-line lease cost (in SG&A). "
            "KEY DIFFERENCE from IFRS 16: GAAP shows operating lease cost in SG&A → EBITDA LOWER. "
            "IFRS 16 shows all lease cost as D&A + interest → EBITDA HIGHER. "
            "Discount rate: rate implicit in lease; if not determinable, incremental borrowing rate. "
            "Sale-leaseback: derecognize asset if control transfers; recognize gain/loss proportionally. "
            "Disclosure: maturity analysis, weighted-average discount rate, weighted-average remaining term."
        ),
    },
    {
        "id": "gaap03",
        "title": "ASC 205-40 — Going Concern",
        "category": "gaap",
        "min_role": "analyst",
        "content": (
            "ASC 205-40 — Presentation of Financial Statements: Going Concern. Effective 2016. "
            "Management must evaluate going concern for EACH REPORTING PERIOD. "
            "Evaluation window: 12 months from the date the financial statements are ISSUED. "
            "Substantial doubt exists if: conditions or events raise substantial doubt about the entity's "
            "ability to continue as a going concern within the 12-month period. "
            "Indicators: recurring net losses, negative cash flows, working capital deficiencies, "
            "negative equity, loan covenant violations, loss of key customer, legal proceedings. "
            "Mitigating factors: management's plans to address — refinancing, asset sales, cost reductions, "
            "equity issuance. Plans must be PROBABLE of implementation within the 12-month period. "
            "Disclosures required: conditions, management's plans, degree of uncertainty. "
            "If substantial doubt remains after plans: footnote + going concern opinion from auditor. "
            "Cash runway < 12 months is a strong indicator requiring evaluation."
        ),
    },
    {
        "id": "gaap04",
        "title": "ASC 230 — Statement of Cash Flows",
        "category": "gaap",
        "min_role": "analyst",
        "content": (
            "ASC 230 — Statement of Cash Flows. Three sections: Operating, Investing, Financing. "
            "GAAP MANDATES: Interest paid = Operating. Interest received = Operating. "
            "Income taxes paid = Operating (unless specifically identifiable with financing/investing). "
            "Dividends paid = Financing. Dividends received = Operating. "
            "Note: THIS IS DIFFERENT FROM IFRS — IAS 7 allows POLICY CHOICE for interest/dividends. "
            "Direct method: cash from customers, cash paid to suppliers (preferred by SEC). "
            "Indirect method: start with net income, adjust for non-cash items + working capital changes. "
            "Free Cash Flow = Cash from Operations + Cash from Investing (capital expenditures). "
            "Restricted cash: include in cash/equivalents; disclose restrictions. "
            "Non-cash investing/financing: disclosed separately (e.g., ROU asset + lease liability at inception)."
        ),
    },
    {
        "id": "gaap05",
        "title": "ASC 260 — Earnings Per Share",
        "category": "gaap",
        "min_role": "analyst",
        "content": (
            "ASC 260 — Earnings Per Share. Required for public companies. "
            "Basic EPS = Net Income attributable to common shareholders / Weighted-avg common shares. "
            "Diluted EPS = Adjusted net income / Diluted weighted-avg shares. "
            "Dilutive securities: stock options (treasury stock method), RSUs, convertible notes (if-converted). "
            "Treasury stock method: options are dilutive only if exercise price < avg market price. "
            "If-converted method: add back after-tax interest expense; add convert shares to denominator. "
            "Anti-dilutive securities (would increase EPS) are EXCLUDED from diluted calculation. "
            "Discontinued operations: report EPS from continuing and discontinued operations separately. "
            "Both basic and diluted EPS must appear on the FACE of the income statement. "
            "Interim periods: use YTD weighted-average shares."
        ),
    },
    {
        "id": "gaap06",
        "title": "ASC 350 — Goodwill Impairment",
        "category": "gaap",
        "min_role": "analyst",
        "content": (
            "ASC 350 — Intangibles — Goodwill and Other. "
            "Goodwill arises from business combinations: purchase price > fair value of net assets. "
            "NOT amortized under GAAP (unlike IFRS where optional amortization was introduced). "
            "Annual impairment test OR when triggering events occur. "
            "Two-step simplified: Step 1 — compare fair value of reporting unit to carrying value. "
            "If fair value < carrying value → goodwill is impaired; write down to fair value. "
            "KEY RULE: Goodwill impairment CANNOT BE REVERSED under GAAP ASC 350. "
            "CRITICAL DIFFERENCE: IFRS IAS 36 permits reversal of impairment at CGU level. "
            "Private company alternative: amortize over 10 years (straight-line). "
            "Reporting unit = operating segment or one level below. "
            "Triggers: significant adverse change in business climate, loss of key personnel, "
            "sustained market cap below book value."
        ),
    },
    {
        "id": "gaap07",
        "title": "ASC 740 — Income Tax Accounting",
        "category": "gaap",
        "min_role": "analyst",
        "content": (
            "ASC 740 — Income Taxes. Asset/liability method — temporary differences create deferred taxes. "
            "Deferred Tax Asset (DTA): future tax deduction; realize when taxable income expected. "
            "Deferred Tax Liability (DTL): future taxable amount; arises from accelerated depreciation. "
            "Valuation allowance: reduce DTA if 'MORE LIKELY THAN NOT' that some or all will not be realized. "
            "'More likely than not' = >50% probability standard. "
            "DIFFERENCE FROM IFRS: IAS 12 uses 'probable' standard (also >50%, but applied differently). "
            "Effective tax rate (ETR) = tax provision / pre-tax income. "
            "Rate reconciliation: disclose differences between statutory rate (21%) and ETR. "
            "Common reconciling items: state/local taxes, R&D credits, stock comp windfalls, "
            "uncertain tax positions (FIN 48 / ASC 740-10). "
            "Intraperiod allocation: tax effects allocated across continuing operations, discontinued, OCI. "
            "Uncertain tax positions (UTPs): recognize if 'more likely than not' to be sustained."
        ),
    },
    {
        "id": "gaap08",
        "title": "ASC 326 — CECL (Current Expected Credit Losses)",
        "category": "gaap",
        "min_role": "analyst",
        "content": (
            "ASC 326 — Financial Instruments — Credit Losses. CECL model. "
            "Effective for large public companies 2020. "
            "Requires recognition of LIFETIME expected credit losses at ORIGINATION — not just incurred losses. "
            "MAJOR CHANGE from prior incurred loss model (ASC 450). "
            "Applies to: trade receivables, loans, held-to-maturity securities, off-balance-sheet commitments. "
            "Methods: aging schedule, migration analysis, probability of default model, DCF. "
            "Must incorporate forward-looking information (macroeconomic forecasts). "
            "Allowance for Credit Losses (ACL) replaces Allowance for Doubtful Accounts. "
            "DIFFERENCE FROM IFRS 9: CECL recognizes lifetime ECL from day 1; "
            "IFRS 9 uses 3-stage model (12-month ECL at Stage 1, lifetime at Stage 2/3). "
            "Practical expedient for trade AR: aging schedule method acceptable. "
            "Disclosure: methods, assumptions, rollforward of allowance balance."
        ),
    },

    # ── IFRS Standards (8 docs) ──────────────────────────────────────────────
    {
        "id": "ifrs01",
        "title": "IFRS 15 — Revenue from Contracts with Customers",
        "category": "ifrs",
        "min_role": "analyst",
        "content": (
            "IFRS 15 — Revenue from Contracts with Customers. Largely CONVERGED with ASC 606. "
            "Same 5-step model as GAAP. Effective 2018. "
            "MINOR DIFFERENCES from ASC 606: "
            "1. Licenses: IFRS 15 treats IP licenses differently in certain circumstances. "
            "2. Variable consideration: IFRS uses 'highly probable' constraint; GAAP uses 'probable'. "
            "3. Collectability: IFRS 15 considers as contract validity threshold; GAAP as implied promise. "
            "Performance obligations: goods transferred at a point in time or services over time. "
            "Practical expedients: portfolio approach, significant financing component (<12 months), "
            "shipping and handling. "
            "Contract modifications: if distinct → new contract; if not distinct → modify existing. "
            "Presentation: contract assets (unbilled AR), contract liabilities (deferred revenue). "
            "Disclosure: disaggregation of revenue by type, geography, market. "
            "Remaining performance obligations >1 year: quantitative disclosure required."
        ),
    },
    {
        "id": "ifrs02",
        "title": "IFRS 16 — Leases (Single Model)",
        "category": "ifrs",
        "min_role": "analyst",
        "content": (
            "IFRS 16 — Leases. Effective 2019. SINGLE MODEL — all leases treated as finance leases. "
            "Lessee recognizes: ROU asset (debit) + lease liability (credit) at commencement. "
            "ALL leases on balance sheet EXCEPT: short-term (<12 months) and low-value assets (<USD 5,000). "
            "P&L impact: depreciation of ROU asset (D&A) + interest on lease liability. "
            "NO operating lease straight-line expense — EBITDA is HIGHER than under GAAP ASC 842. "
            "CRITICAL IMPACT: EBITDA uplift = former operating lease expense (now below EBITDA line). "
            "For leveraged analysis: IFRS 16 increases net debt by lease liability. "
            "Discount rate: rate implicit in lease; if not determinable, IBR. "
            "Subsequent measurement: lease liability = amortized cost; ROU asset = cost model or revaluation. "
            "Sale-leaseback under IFRS 16: recognize full gain if sale is a true sale. "
            "Disclosure: maturity analysis, interest expense on lease liabilities, additions to ROU assets."
        ),
    },
    {
        "id": "ifrs03",
        "title": "IAS 36 — Impairment of Assets",
        "category": "ifrs",
        "min_role": "analyst",
        "content": (
            "IAS 36 — Impairment of Assets. CRITICAL DIFFERENCE: impairment reversal PERMITTED. "
            "Annual test required for: goodwill, intangibles with indefinite life, intangibles not yet in use. "
            "Other assets: test only if impairment indicators exist (internal or external). "
            "Cash Generating Unit (CGU): smallest identifiable group of assets generating independent cash flows. "
            "Goodwill allocated to CGUs (or groups of CGUs). "
            "Recoverable amount = higher of: Fair Value Less Costs of Disposal (FVLCD) or Value in Use (VIU). "
            "VIU = PV of future cash flows from continuing use + disposal. "
            "Impairment loss: reduce to recoverable amount; recognize in P&L. "
            "REVERSAL: For assets other than goodwill — reversal PERMITTED up to original carrying amount. "
            "Goodwill impairment: CANNOT be reversed (same as GAAP ASC 350). "
            "KEY DIFFERENCE FROM GAAP: IAS 36 — asset reversals permitted; GAAP: NO reversal at all."
        ),
    },
    {
        "id": "ifrs04",
        "title": "IAS 37 — Provisions, Contingent Liabilities and Assets",
        "category": "ifrs",
        "min_role": "analyst",
        "content": (
            "IAS 37 — Provisions, Contingent Liabilities and Contingent Assets. "
            "Provision: present obligation + probable outflow + reliable estimate. "
            "PROBABLE = MORE LIKELY THAN NOT = >50%. "
            "CRITICAL DIFFERENCE from GAAP: ASC 450 uses ~75% probability threshold. "
            "IFRS recognizes provisions EARLIER than GAAP. "
            "Contingent liability: possible obligation (not probable) → disclose, do not accrue. "
            "Contingent asset: possible inflow → disclose if probable; recognize if virtually certain. "
            "Measurement: best estimate of expenditure; use expected value for large populations. "
            "Restructuring provision: recognize only when constructive obligation exists — "
            "formal plan + communicated to affected parties. Cannot accrue for future operating losses. "
            "Onerous contracts: recognize provision for unavoidable costs exceeding expected benefits. "
            "Discount: if material, discount at pre-tax risk-free rate. Unwinding = finance cost. "
            "Disclosure: description, expected timing, uncertainties, expected reimbursement."
        ),
    },
    {
        "id": "ifrs05",
        "title": "IAS 38 — Intangible Assets (Development Cost Capitalization)",
        "category": "ifrs",
        "min_role": "analyst",
        "content": (
            "IAS 38 — Intangible Assets. CRITICAL DIFFERENCE: development costs MUST be capitalized. "
            "Research phase: ALL costs expensed as incurred. "
            "Development phase: CAPITALIZE if ALL 6 criteria met: "
            "1. Technical feasibility of completing the asset. "
            "2. Intention to complete and use/sell. "
            "3. Ability to use or sell. "
            "4. Probable future economic benefits. "
            "5. Adequate technical, financial, other resources available. "
            "6. Ability to reliably measure expenditure. "
            "CRITICAL DIFFERENCE FROM GAAP: GAAP ASC 730 requires ALL R&D to be expensed immediately. "
            "IAS 38 capitalization: increases assets, reduces expenses, improves near-term net income. "
            "Amortization: over useful life (must be finite or indefinite). "
            "Indefinite life: no amortization; annual impairment test (IAS 36). "
            "Revaluation model: only if active market exists (rare for intangibles). "
            "Internally generated brands, customer lists: CANNOT be capitalized. "
            "Disclosure: classes of intangibles, amortization methods, carrying amounts."
        ),
    },
    {
        "id": "ifrs06",
        "title": "IAS 7 — Statement of Cash Flows (IFRS Policy Choice)",
        "category": "ifrs",
        "min_role": "analyst",
        "content": (
            "IAS 7 — Statement of Cash Flows. Three sections: Operating, Investing, Financing. "
            "CRITICAL DIFFERENCE FROM GAAP: interest and dividends — POLICY CHOICE under IFRS. "
            "Interest paid: Operating OR Financing (policy choice, must be consistent). "
            "Interest received: Operating OR Investing (policy choice, must be consistent). "
            "Dividends paid: Financing OR Operating (policy choice, must be consistent). "
            "Dividends received: Operating OR Investing (policy choice, must be consistent). "
            "GAAP ASC 230: Interest paid = Operating ONLY (no choice). "
            "Policy choice disclosure required. Consistency across periods required. "
            "Bank overdrafts: include in cash and cash equivalents if repayable on demand. "
            "Foreign currency: translate at rate at date of transaction; reconcile to balance sheet. "
            "Direct method (preferred): disclose major classes of gross operating receipts and payments. "
            "Indirect method: start with profit before tax (NOT net income). "
            "Tax paid: generally Operating unless specifically identifiable."
        ),
    },
    {
        "id": "ifrs07",
        "title": "IAS 2 — Inventories (LIFO Prohibited)",
        "category": "ifrs",
        "min_role": "analyst",
        "content": (
            "IAS 2 — Inventories. Measurement: lower of COST and NET REALIZABLE VALUE (NRV). "
            "CRITICAL RULE: LIFO method is STRICTLY PROHIBITED under IFRS. "
            "GAAP: LIFO is permitted (and used by ~30% of US public companies). "
            "Permitted methods: FIFO, Weighted Average Cost. "
            "Must use same method for all inventories of similar nature and use. "
            "Cost of inventories: purchase cost + conversion costs + other costs to bring to location/condition. "
            "Abnormal waste, idle capacity, storage (unless part of production), selling costs: EXCLUDE. "
            "NRV = estimated selling price less estimated costs of completion and selling. "
            "Write-down to NRV: recognize as expense. REVERSAL of write-down permitted if NRV increases. "
            "Disclosure: accounting policy (FIFO or weighted average), carrying amount by classification, "
            "amount of write-downs and reversals, inventories pledged as security. "
            "LIFO reserve disclosure: companies transitioning from GAAP must disclose LIFO reserve."
        ),
    },
    {
        "id": "ifrs08",
        "title": "IAS 16 — Property, Plant and Equipment (Revaluation Option)",
        "category": "ifrs",
        "min_role": "analyst",
        "content": (
            "IAS 16 — Property, Plant and Equipment. "
            "CRITICAL DIFFERENCE FROM GAAP: REVALUATION MODEL option available under IFRS. "
            "GAAP allows cost model ONLY. "
            "Two measurement models: "
            "Cost model: historical cost - accumulated depreciation - impairment losses. "
            "Revaluation model: fair value at revaluation date - subsequent depreciation - impairment. "
            "Must apply same model to entire class of PPE. "
            "Revaluation frequency: often enough so carrying amount does not differ materially from fair value. "
            "Revaluation gain → OCI (revaluation surplus in equity). "
            "Revaluation loss: first offset surplus in OCI; excess → P&L. "
            "Component approach: each significant component depreciated separately over its useful life. "
            "Depreciation: begins when available for use; ends when derecognized or classified as held for sale. "
            "Residual value and useful life: review at least annually. "
            "Disclosure: measurement model, depreciation methods, useful lives, carrying amounts, "
            "capital commitments, impairments."
        ),
    },
]


def keyword_search(query: str, top_k: int = 5, user_role: str = "analyst") -> List[Dict]:
    """Simple keyword overlap search — used when pgvector is unavailable."""
    query_words = set(query.lower().split())
    role_level = {"analyst": 1, "manager": 2, "vp": 3, "cfo": 4, "ceo": 5}
    user_level = role_level.get(user_role.lower(), 1)

    scored = []
    for doc in KNOWLEDGE_BASE:
        doc_level = role_level.get(doc.get("min_role", "analyst"), 1)
        if doc_level > user_level:
            continue

        doc_words = set((doc["title"] + " " + doc["content"]).lower().split())
        overlap = len(query_words & doc_words)
        if overlap > 0:
            scored.append({"doc": doc, "score": overlap / max(len(query_words), 1)})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return [
        {
            "id": s["doc"]["id"],
            "title": s["doc"]["title"],
            "content": s["doc"]["content"][:800],
            "score": round(s["score"], 3),
            "category": s["doc"]["category"],
        }
        for s in scored[:top_k]
    ]
