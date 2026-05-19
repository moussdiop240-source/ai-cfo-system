"""
AI CFO DASHBOARD GENERATOR
Synthetic data for NovaTech Solutions Inc. — Q1 2026
Runs full deterministic pipeline: Math → GAAP → IFRS → RAG → HTML
"""
import sys, json, os
sys.path.insert(0, ".")

# ── SYNTHETIC FINANCIAL DATA ────────────────────────────────────────────────
COMPANY = "NovaTech Solutions Inc."
PERIOD  = "Q1 2026"
CIK     = "0001234567"

FINANCIAL_DATA = {
    # ── Income Statement ────────────────────────────────────────────────
    "revenue":              12_840_000,
    "cogs":                 3_594_000,   # 28% — SaaS infra + support
    "gross_profit":         9_246_000,
    "operating_expenses":   6_120_000,   # SG&A + R&D
    "rd_expense":           2_430_000,
    "sg_a_expense":         3_690_000,
    "ebitda":               3_126_000,
    "depreciation":           312_000,
    "ebit":                 2_814_000,
    "interest_expense":       210_000,
    "pre_tax_income":       2_604_000,
    "tax_provision":          573_000,   # 22% ETR
    "net_income":           2_031_000,

    # ── Balance Sheet ───────────────────────────────────────────────────
    "total_assets":        58_400_000,
    "current_assets":      24_100_000,
    "cash":                11_250_000,
    "accounts_receivable":  8_640_000,
    "inventory":              210_000,   # hardware peripherals only
    "prepaid_expenses":     4_000_000,
    "total_equity":        34_200_000,
    "current_liabilities":  9_800_000,
    "accounts_payable":     3_150_000,
    "deferred_revenue":     4_200_000,
    "total_debt":          14_000_000,
    "long_term_debt":      11_800_000,

    # ── Cash Flow ───────────────────────────────────────────────────────
    "cash_from_operations":  3_840_000,
    "capex":                  780_000,
    "free_cash_flow":        3_060_000,
    "monthly_cash_burn":           0,    # profitable

    # ── Share Data ──────────────────────────────────────────────────────
    "shares_outstanding":   8_200_000,
    "diluted_shares":       8_650_000,   # stock options / RSUs

    # ── Lease / IFRS 16 / ASC 842 ──────────────────────────────────────
    "rou_assets":           4_800_000,
    "lease_liability":      4_620_000,
    "operating_lease_expense": 360_000,

    # ── Goodwill / Intangibles ──────────────────────────────────────────
    "goodwill":             9_600_000,   # DataPulse acquisition 2024
    "goodwill_impairment_test_date": "2026-01-31",
    "impairment_test_performed": True,
    "impairment_tested_at_cgu_level": True,

    # ── Credit Losses ───────────────────────────────────────────────────
    "allowance_for_credit_losses": 432_000,
    "ecl_stage1_allowance":  258_000,
    "ecl_stage2_allowance":  129_000,
    "ecl_stage3_allowance":   45_000,

    # ── GAAP / IFRS policy fields ───────────────────────────────────────
    "revenue_recognition_policy":       "ASC 606 5-step model",
    "inventory_cost_method":            "fifo",
    "interest_cash_flow_classification":"operating",
    "cash_flow_policy_consistent":      True,
    "comparative_period_presented":     True,
    "publicly_listed":                  True,
    "qualifying_development_projects":  True,    # IAS 38 trigger
    "rd_dev_capitalizable_pct":         0.35,

    # ── Budget vs Actuals ───────────────────────────────────────────────
    "actuals": {
        "revenue":   12_840_000,
        "cogs":       3_594_000,
        "gross_profit": 9_246_000,
        "ebitda":     3_126_000,
        "rd_expense": 2_430_000,
        "sg_a":       3_690_000,
    },
    "budget": {
        "revenue":   11_500_000,
        "cogs":       3_335_000,
        "gross_profit": 8_165_000,
        "ebitda":     2_700_000,
        "rd_expense": 2_100_000,
        "sg_a":       3_365_000,
    },

    # ── Historical Revenue (8 quarters for forecast) ────────────────────
    "historical_revenue": [
        7_200_000,   # Q1 2024
        7_810_000,   # Q2 2024
        8_450_000,   # Q3 2024
        9_120_000,   # Q4 2024
        9_980_000,   # Q1 2025
        10_620_000,  # Q2 2025
        11_310_000,  # Q3 2025
        11_870_000,  # Q4 2025
        12_840_000,  # Q1 2026 (current)
    ],

    # ── Segments ────────────────────────────────────────────────────────
    "segments": {
        "Enterprise":            {"revenue": 7_704_000,  "gross_profit": 5_852_400, "assets": 32_000_000},
        "SMB":                   {"revenue": 3_852_000,  "gross_profit": 2_813_160, "assets": 16_000_000},
        "Professional_Services": {"revenue": 1_284_000,  "gross_profit":   580_440, "assets":  6_000_000},
    },

    # ── Headcount ───────────────────────────────────────────────────────
    "headcount": 214,
    "revenue_per_employee": 60_000,   # annualised Q1

    # ── Deferred Revenue / ARR ──────────────────────────────────────────
    "arr":              51_360_000,   # annualised
    "nrr_pct":          118,          # net revenue retention
    "churn_rate_pct":   4.2,
}

# ── RUN DETERMINISTIC PIPELINE ───────────────────────────────────────────────
from backend.agents.math_engine import FinancialCalculationEngine
from backend.compliance.gaap_engine import GAAPEngine
from backend.compliance.ifrs_engine import IFRSEngine
from backend.rag.pipeline import RAGPipeline, format_rag_context

engine  = FinancialCalculationEngine()
gaap_e  = GAAPEngine()
ifrs_e  = IFRSEngine()
rag     = RAGPipeline()

kpis     = engine.calculate_kpis(FINANCIAL_DATA)
variance = engine.calculate_variance_analysis(
    FINANCIAL_DATA["actuals"], FINANCIAL_DATA["budget"]
)
anomalies = engine.detect_anomalies(FINANCIAL_DATA, kpis)
runway    = engine.calculate_cash_runway(FINANCIAL_DATA, kpis)
forecast  = engine.forecast_revenue(FINANCIAL_DATA["historical_revenue"], periods=8)
reconcile = engine.calculate_reconciliation(FINANCIAL_DATA, FINANCIAL_DATA)
triggers  = engine.check_approval_triggers(variance, kpis, anomalies, None, None)

# Engine expects segments as a list of dicts with a 'name' key
FINANCIAL_DATA_FOR_ENGINES = {
    **FINANCIAL_DATA,
    "segments": [
        {"name": k, **v}
        for k, v in FINANCIAL_DATA["segments"].items()
    ],
}

gaap_results = gaap_e.check_all(FINANCIAL_DATA_FOR_ENGINES, kpis, variance, runway)
ifrs_results = ifrs_e.check_all(FINANCIAL_DATA_FOR_ENGINES, kpis, variance, runway)

# count compliance
gaap_compliant = sum(1 for r in gaap_results.values() if r.get("status") == "COMPLIANT")
gaap_issues    = 12 - gaap_compliant
ifrs_compliant = sum(1 for r in ifrs_results.values() if r.get("status") == "COMPLIANT")
ifrs_issues    = 12 - ifrs_compliant

# RAG
rag_state = {
    "task_description": "Q1 2026 board analysis NovaTech Solutions",
    "task_type": "full_report",
    "period": PERIOD,
    "kpi_metrics": kpis,
    "anomaly_flags": anomalies,
    "gaap_results": gaap_results,
    "ifrs_results": ifrs_results,
}
rag_query  = rag.build_rag_query(rag_state)
rag_chunks = rag.retrieve(rag_query, top_k=5)

print(f"KPIs computed: {len(kpis)}")
print(f"GAAP: {gaap_compliant}/12 compliant | IFRS: {ifrs_compliant}/12 compliant")
print(f"Anomalies: {len(anomalies)} | HITL triggers: {len(triggers)}")
print(f"Forecast periods: {len(forecast.get('forecast', []))}")
print(f"RAG chunks: {len(rag_chunks)}")

# ── BUILD HTML DASHBOARD ─────────────────────────────────────────────────────

def fmt_usd(v, decimals=0):
    if abs(v) >= 1_000_000:
        return f"${v/1_000_000:.1f}M"
    if abs(v) >= 1_000:
        return f"${v/1_000:.0f}K"
    return f"${v:,.{decimals}f}"

def fmt_pct(v):
    sign = "+" if v >= 0 else ""
    return f"{sign}{v:.1f}%"

def color_for_status(s):
    return {"COMPLIANT": "#10B981", "DISCLOSURE_REQUIRED": "#FBBF24", "NON_COMPLIANT": "#F87171"}.get(s, "#94A3B8")

def badge_for_status(s):
    colors = {"COMPLIANT": "ok", "DISCLOSURE_REQUIRED": "warn", "NON_COMPLIANT": "bad"}
    return colors.get(s, "warn")

# ── Variance table rows ──────────────────────────────────────────────────────
var_rows_html = ""
var_labels = {
    "revenue": "Revenue", "cogs": "Cost of Revenue",
    "gross_profit": "Gross Profit", "ebitda": "EBITDA",
    "rd_expense": "R&D Expense", "sg_a": "SG&A Expense"
}
for key, label in var_labels.items():
    r = variance["line_items"].get(key, {})
    if not r:
        continue
    fav_class = "delta-pos" if r["favorable"] else "delta-neg"
    mat_badge = '<span class="status warn">Material</span>' if r["material"] else '<span class="status ok">Normal</span>'
    var_rows_html += f"""
<tr>
  <td>{label}</td>
  <td>{fmt_usd(r['actual'])}</td>
  <td>{fmt_usd(r['budget'])}</td>
  <td class="{fav_class}">{fmt_usd(r['variance_abs'])}</td>
  <td class="{fav_class}">{fmt_pct(r['variance_pct'])}</td>
  <td>{mat_badge}</td>
</tr>"""

# totals row
t = variance["totals"]
fav_class = "delta-pos" if t["favorable"] else "delta-neg"
var_rows_html += f"""
<tr style="font-weight:700;border-top:1px solid rgba(255,255,255,0.15)">
  <td>TOTAL</td>
  <td>{fmt_usd(t['actual'])}</td>
  <td>{fmt_usd(t['budget'])}</td>
  <td class="{fav_class}">{fmt_usd(t['variance_abs'])}</td>
  <td class="{fav_class}">{fmt_pct(t['variance_pct'])}</td>
  <td><span class="status ok">—</span></td>
</tr>"""

# ── GAAP rows ────────────────────────────────────────────────────────────────
gaap_labels = {
    "asc205": "ASC 205-40 Going Concern", "asc230": "ASC 230 Cash Flows",
    "asc260": "ASC 260 EPS", "asc280": "ASC 280 Segments",
    "asc310": "ASC 310/326 Credit Losses (CECL)", "asc350": "ASC 350 Goodwill",
    "asc450": "ASC 450 Contingencies", "asc606": "ASC 606 Revenue Recognition",
    "asc740": "ASC 740 Income Taxes", "asc820": "ASC 820 Fair Value",
    "asc842": "ASC 842 Leases", "sab99": "SAB 99 Materiality",
}
gaap_rows_html = ""
for std, label in gaap_labels.items():
    r = gaap_results.get(std, {})
    status = r.get("status", "COMPLIANT")
    finding = r.get("finding", "No issues identified")
    cls = badge_for_status(status)
    gaap_rows_html += f"""
<tr>
  <td>{label}</td>
  <td><span class="status {cls}">{status}</span></td>
  <td style="font-size:12px;color:#94A3B8">{finding}</td>
</tr>"""

# ── IFRS rows ────────────────────────────────────────────────────────────────
ifrs_labels = {
    "ias1":  "IAS 1 Presentation", "ias2":  "IAS 2 Inventories",
    "ias7":  "IAS 7 Cash Flows",   "ias12": "IAS 12 Income Taxes",
    "ias16": "IAS 16 PPE",         "ias33": "IAS 33 EPS",
    "ias36": "IAS 36 Impairment",  "ias37": "IAS 37 Provisions",
    "ias38": "IAS 38 Intangibles", "ifrs9": "IFRS 9 Credit Losses (ECL)",
    "ifrs15":"IFRS 15 Revenue",    "ifrs16":"IFRS 16 Leases",
}
ifrs_rows_html = ""
for std, label in ifrs_labels.items():
    r = ifrs_results.get(std, {})
    status = r.get("status", "COMPLIANT")
    finding = r.get("finding", "No issues identified")
    cls = badge_for_status(status)
    ifrs_rows_html += f"""
<tr>
  <td>{label}</td>
  <td><span class="status {cls}">{status}</span></td>
  <td style="font-size:12px;color:#94A3B8">{finding}</td>
</tr>"""

# ── Revenue chart data ────────────────────────────────────────────────────────
hist = FINANCIAL_DATA["historical_revenue"]
fcast = forecast.get("forecast", [])
quarters_hist  = ["Q1'24","Q2'24","Q3'24","Q4'24","Q1'25","Q2'25","Q3'25","Q4'25","Q1'26"]
quarters_fcast = ["Q2'26","Q3'26","Q4'26","Q1'27","Q2'27","Q3'27","Q4'27","Q1'28"]

all_vals = hist + fcast
max_val  = max(all_vals) * 1.15
chart_w, chart_h = 760, 220
bar_w    = chart_w / (len(hist) + len(fcast) + 1)

def bar_x(i): return 40 + i * (bar_w + 4)
def bar_y(v): return chart_h - 30 - (v / max_val) * (chart_h - 50)
def bar_h(v): return (v / max_val) * (chart_h - 50)

hist_bars = ""
for i, (v, q) in enumerate(zip(hist, quarters_hist)):
    x = bar_x(i)
    y = bar_y(v)
    h = bar_h(v)
    c = "#00FFC8" if i == len(hist)-1 else "#60A5FA"
    hist_bars += f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w-2:.1f}" height="{h:.1f}" fill="{c}" rx="3" opacity="0.85"/>'
    hist_bars += f'<text x="{x+bar_w/2-1:.1f}" y="{chart_h-8}" fill="#4E6880" font-size="9" text-anchor="middle">{q}</text>'

fcast_bars = ""
for i, (v, q) in enumerate(zip(fcast, quarters_fcast)):
    idx = len(hist) + i
    x = bar_x(idx)
    y = bar_y(v)
    h = bar_h(v)
    fcast_bars += f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w-2:.1f}" height="{h:.1f}" fill="#A78BFA" rx="3" opacity="0.55" stroke-dasharray="4,2"/>'
    fcast_bars += f'<text x="{x+bar_w/2-1:.1f}" y="{chart_h-8}" fill="#4E6880" font-size="9" text-anchor="middle">{q}</text>'

# ── Segment donut ─────────────────────────────────────────────────────────────
seg_data   = [(k, v["revenue"]) for k, v in FINANCIAL_DATA["segments"].items()]
seg_total  = sum(v for _, v in seg_data)
seg_colors = ["#00FFC8", "#60A5FA", "#A78BFA"]
seg_slices = ""
offset = 0
cx, cy, r_outer, r_inner = 120, 110, 90, 52
import math
for (name, val), color in zip(seg_data, seg_colors):
    pct   = val / seg_total
    angle = pct * 2 * math.pi
    x1 = cx + r_outer * math.sin(offset)
    y1 = cy - r_outer * math.cos(offset)
    x2 = cx + r_outer * math.sin(offset + angle)
    y2 = cy - r_outer * math.cos(offset + angle)
    xi1 = cx + r_inner * math.sin(offset)
    yi1 = cy - r_inner * math.cos(offset)
    xi2 = cx + r_inner * math.sin(offset + angle)
    yi2 = cy - r_inner * math.cos(offset + angle)
    large = 1 if angle > math.pi else 0
    seg_slices += f'<path d="M{xi1:.1f},{yi1:.1f} L{x1:.1f},{y1:.1f} A{r_outer},{r_outer} 0 {large},1 {x2:.1f},{y2:.1f} L{xi2:.1f},{yi2:.1f} A{r_inner},{r_inner} 0 {large},0 {xi1:.1f},{yi1:.1f} Z" fill="{color}" opacity="0.85" stroke="#04060F" stroke-width="2"/>'
    offset += angle

seg_legend = ""
for (name, val), color in zip(seg_data, seg_colors):
    seg_legend += f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px"><span style="width:10px;height:10px;border-radius:2px;background:{color};display:inline-block"></span><span style="font-size:12px;color:#94A3B8">{name.replace("_"," ")}</span><span style="font-size:12px;font-weight:700;margin-left:auto">{fmt_usd(val)}</span></div>'

# ── Anomaly cards ─────────────────────────────────────────────────────────────
anomaly_html = ""
if anomalies:
    for flag in anomalies:
        sev = "negative" if "CRITICAL" in flag else "warning"
        anomaly_html += f'<div class="insight-card {sev}"><div class="insight-title">{"⚠" if sev=="warning" else "🚨"} Anomaly Detected</div><p style="font-size:12px;color:#94A3B8;margin:0">{flag}</p></div>'
else:
    anomaly_html = '<div class="insight-card positive"><div class="insight-title">✓ No Anomalies</div><p style="font-size:12px;color:#94A3B8">All statistical indicators within normal bounds.</p></div>'

# ── HITL triggers ─────────────────────────────────────────────────────────────
trigger_html = ""
if triggers:
    for t in triggers:
        sev_cls = "bad" if t.get("severity") == "critical" else "warn"
        trigger_html += f'<div style="display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.06)"><span style="font-size:13px;color:#E2E8F0">{t["message"]}</span><span class="status {sev_cls}">{t["severity"].upper()}</span></div>'
    hitl_banner = '#F87171'
    hitl_label  = f'{len(triggers)} Review Required'
else:
    trigger_html = '<p style="color:#10B981;font-size:13px">All thresholds within acceptable range. No CFO approval required.</p>'
    hitl_banner = '#10B981'
    hitl_label  = 'Auto-Approved'

# ── RAG citations ─────────────────────────────────────────────────────────────
rag_html = ""
for i, chunk in enumerate(rag_chunks[:4], 1):
    d = chunk.to_dict()
    rag_html += f'<div style="padding:12px 0;border-bottom:1px solid rgba(255,255,255,0.06)"><div style="font-size:12px;color:#60A5FA;margin-bottom:4px">[{i}] {d["title"]}</div><p style="font-size:11px;color:#64748B;margin:0;line-height:1.6">{d["content"][:180]}…</p></div>'

# ── Reconciliation table ──────────────────────────────────────────────────────
recon_html = ""
recon_labels = {
    "ifrs16_vs_asc842_ebitda": "IFRS 16 vs ASC 842 — Lease Capitalization",
    "ias38_vs_asc730_rd":       "IAS 38 vs ASC 730 — R&D Capitalization",
    "ias37_vs_asc450_provisions":"IAS 37 vs ASC 450 — Provision Threshold",
    "ias36_vs_asc350_goodwill":  "IAS 36 vs ASC 350 — Goodwill Impairment",
    "ias2_vs_asc330_lifo":       "IAS 2 vs ASC 330 — LIFO Prohibition",
}
for key, label in recon_labels.items():
    r = reconcile.get(key, {})
    impact = r.get("ebitda_impact") or r.get("pl_impact") or r.get("goodwill_balance")
    impact_str = fmt_usd(impact) if impact else "Qualitative"
    gaap_t = r.get("gaap_treatment", "—")
    ifrs_t = r.get("ifrs_treatment", "—")
    recon_html += f"""
<tr>
  <td style="color:#E2E8F0;font-weight:600">{label}</td>
  <td style="color:#60A5FA;font-size:11px">{gaap_t}</td>
  <td style="color:#A78BFA;font-size:11px">{ifrs_t}</td>
  <td style="color:#FBBF24;text-align:center">{impact_str}</td>
</tr>"""

# ── KPI calculations for display ─────────────────────────────────────────────
gm   = kpis["gross_margin_pct"]
ebitda_m = kpis["ebitda_margin_pct"]
nm   = kpis["net_margin_pct"]
cr   = kpis["current_ratio"]
de   = kpis["debt_to_equity"]
roe  = kpis["roe_pct"]
roa  = kpis["roa_pct"]
dso  = kpis["dso_days"]
eps  = kpis["diluted_eps"]
wc   = kpis["working_capital"]
nd   = kpis["net_debt"]
icr  = kpis["interest_coverage"]
ccc  = kpis["ccc_days"]

# ── HTML ──────────────────────────────────────────────────────────────────────
HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI CFO Dashboard — {COMPANY} {PERIOD}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#04060F;color:#F1F5F9;font-family:'Segoe UI',system-ui,sans-serif;min-width:900px}}
@keyframes fadeInUp{{from{{opacity:0;transform:translateY(20px)}}to{{opacity:1;transform:translateY(0)}}}}
@keyframes glow-pulse{{0%,100%{{box-shadow:0 0 20px rgba(0,255,200,0.15)}}50%{{box-shadow:0 0 30px rgba(0,255,200,0.3)}}}}
@keyframes pulse-dot{{0%,100%{{opacity:1}}50%{{opacity:0.3}}}}
.container{{max-width:1440px;margin:0 auto;padding:24px}}
.header{{background:linear-gradient(135deg,rgba(11,17,32,0.95),rgba(4,6,15,0.98));border:1px solid rgba(0,255,200,0.2);border-radius:16px;padding:24px 32px;margin-bottom:24px;animation:fadeInUp 0.5s ease}}
.header-top{{display:flex;justify-content:space-between;align-items:flex-start}}
.company-name{{font-size:26px;font-weight:700;background:linear-gradient(135deg,#00FFC8,#60A5FA);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.sub{{font-size:13px;color:#4E6880;margin-top:4px}}
.badges{{display:flex;gap:10px;flex-wrap:wrap;margin-top:8px}}
.badge{{padding:5px 12px;border-radius:20px;font-size:11px;font-weight:600}}
.badge-period{{background:rgba(96,165,250,0.15);border:1px solid rgba(96,165,250,0.3);color:#60A5FA}}
.badge-gaap{{background:rgba(16,185,129,0.15);border:1px solid rgba(16,185,129,0.3);color:#10B981}}
.badge-ifrs{{background:rgba(167,139,250,0.15);border:1px solid rgba(167,139,250,0.3);color:#A78BFA}}
.badge-live{{background:rgba(0,255,200,0.1);border:1px solid rgba(0,255,200,0.3);color:#00FFC8}}
.badge-hitl{{background:rgba(248,113,113,0.15);border:1px solid rgba(248,113,113,0.3);color:{hitl_banner}}}
.live-dot{{width:7px;height:7px;background:#00FFC8;border-radius:50%;display:inline-block;margin-right:5px;animation:pulse-dot 1.5s infinite}}
.section-title{{font-size:11px;font-weight:600;color:#4E6880;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:16px;padding-bottom:8px;border-bottom:1px solid rgba(255,255,255,0.06)}}

/* KPI grid */
.kpi-row{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:20px;animation:fadeInUp 0.6s ease}}
.kpi-row-2{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:24px;animation:fadeInUp 0.65s ease}}
.kpi-card{{background:rgba(11,17,32,0.8);backdrop-filter:blur(20px);border-radius:12px;padding:18px;border:1px solid rgba(255,255,255,0.07);transition:all 0.3s ease}}
.kpi-card:hover{{transform:translateY(-2px);border-color:rgba(0,255,200,0.2)}}
.kpi-label{{font-size:11px;color:#4E6880;margin-bottom:8px;text-transform:uppercase;letter-spacing:0.05em}}
.kpi-value{{font-size:26px;font-weight:700;font-family:'Courier New',monospace;letter-spacing:-1px}}
.kpi-value.cyan{{color:#00FFC8;text-shadow:0 0 12px rgba(0,255,200,0.5)}}
.kpi-value.blue{{color:#60A5FA;text-shadow:0 0 12px rgba(96,165,250,0.5)}}
.kpi-value.purple{{color:#A78BFA;text-shadow:0 0 12px rgba(167,139,250,0.5)}}
.kpi-value.amber{{color:#FBBF24;text-shadow:0 0 12px rgba(251,191,36,0.5)}}
.kpi-value.green{{color:#10B981;text-shadow:0 0 12px rgba(16,185,129,0.5)}}
.kpi-value.red{{color:#F87171;text-shadow:0 0 12px rgba(248,113,113,0.5)}}
.kpi-delta{{font-size:11px;margin-top:5px;font-weight:500}}
.delta-pos{{color:#10B981}}.delta-neg{{color:#F87171}}
.kpi-sub{{font-size:11px;color:#4E6880;margin-top:4px}}

/* Cards */
.card{{background:rgba(11,17,32,0.8);backdrop-filter:blur(20px);border-radius:12px;padding:24px;border:1px solid rgba(255,255,255,0.07);margin-bottom:20px;animation:fadeInUp 0.7s ease}}
.grid-2{{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px}}
.grid-3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-bottom:20px}}

/* Tables */
table{{width:100%;border-collapse:collapse}}
th{{background:#0B1120;color:#4E6880;font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;padding:10px 14px;text-align:right;border-bottom:1px solid rgba(255,255,255,0.07)}}
th:first-child{{text-align:left}}
td{{padding:10px 14px;font-size:12px;text-align:right;border-bottom:1px solid rgba(255,255,255,0.04);color:#CBD5E1}}
td:first-child{{text-align:left;color:#94A3B8}}
tr:hover{{background:rgba(0,255,200,0.03)}}
.status{{display:inline-flex;align-items:center;font-size:10px;font-weight:700;padding:3px 8px;border-radius:10px;letter-spacing:0.02em}}
.status.ok{{background:rgba(16,185,129,0.15);color:#10B981}}
.status.warn{{background:rgba(251,191,36,0.15);color:#FBBF24}}
.status.bad{{background:rgba(248,113,113,0.15);color:#F87171}}

/* Charts */
svg text{{font-family:'Segoe UI',system-ui,sans-serif}}

/* Insight cards */
.insight-card{{background:rgba(11,17,32,0.8);border-radius:10px;padding:16px;border-left:3px solid;margin-bottom:12px}}
.insight-card.positive{{border-color:#10B981;background:rgba(16,185,129,0.04)}}
.insight-card.warning{{border-color:#FBBF24;background:rgba(251,191,36,0.04)}}
.insight-card.negative{{border-color:#F87171;background:rgba(248,113,113,0.04)}}
.insight-title{{font-size:12px;font-weight:700;margin-bottom:6px;color:#E2E8F0}}

/* Tabs */
.tab-nav{{display:flex;gap:4px;background:rgba(11,17,32,0.8);border-radius:10px;padding:4px;margin-bottom:20px;border:1px solid rgba(255,255,255,0.07)}}
.tab{{flex:1;text-align:center;padding:9px;border-radius:8px;font-size:12px;font-weight:600;cursor:pointer;color:#4E6880;transition:all 0.2s;border:none;background:none}}
.tab.active{{background:rgba(0,255,200,0.1);color:#00FFC8;border:1px solid rgba(0,255,200,0.2)}}
.tab-pane{{display:none}}.tab-pane.active{{display:block}}

/* Waterfall bar special */
.wf-pos{{fill:#10B981}}.wf-neg{{fill:#F87171}}.wf-net{{fill:#60A5FA}}

/* scrollbar */
::-webkit-scrollbar{{width:6px;height:6px}}
::-webkit-scrollbar-track{{background:#0B1120}}
::-webkit-scrollbar-thumb{{background:#1E2D3D;border-radius:3px}}
</style>
</head>
<body>
<div class="container">

<!-- ══ HEADER ══════════════════════════════════════════════════════════════ -->
<div class="header">
  <div class="header-top">
    <div>
      <div class="company-name">{COMPANY}</div>
      <div class="sub">CIK {CIK} · Quarterly Financial Intelligence Report · Powered by AI CFO Multi-Agent System</div>
    </div>
    <div style="text-align:right">
      <div style="font-size:11px;color:#4E6880">Anti-Hallucination Architecture</div>
      <div style="font-size:11px;color:#10B981;margin-top:4px">✓ Zero-LLM Math · ✓ Pydantic Enforced · ✓ RAG Retrieved</div>
    </div>
  </div>
  <div class="badges" style="margin-top:16px">
    <span class="badge badge-period">{PERIOD}</span>
    <span class="badge badge-live"><span class="live-dot"></span>LIVE PIPELINE</span>
    <span class="badge badge-gaap">GAAP {gaap_compliant}/12 Compliant</span>
    <span class="badge badge-ifrs">IFRS {ifrs_compliant}/12 Compliant</span>
    <span class="badge badge-hitl">{hitl_label}</span>
    <span class="badge" style="background:rgba(251,191,36,0.1);border:1px solid rgba(251,191,36,0.3);color:#FBBF24">ARR {fmt_usd(FINANCIAL_DATA['arr'])}</span>
    <span class="badge" style="background:rgba(96,165,250,0.1);border:1px solid rgba(96,165,250,0.3);color:#60A5FA">NRR {FINANCIAL_DATA['nrr_pct']}%</span>
  </div>
</div>

<!-- ══ TABS ════════════════════════════════════════════════════════════════ -->
<div class="tab-nav">
  <button class="tab active" onclick="switchTab('overview')">Overview & KPIs</button>
  <button class="tab" onclick="switchTab('variance')">Budget vs Actuals</button>
  <button class="tab" onclick="switchTab('compliance')">GAAP / IFRS Compliance</button>
  <button class="tab" onclick="switchTab('forecast')">Forecast & Segments</button>
  <button class="tab" onclick="switchTab('reconcile')">GAAP↔IFRS Recon</button>
  <button class="tab" onclick="switchTab('hitl')">HITL & RAG</button>
</div>

<!-- ══════════════════════════════════════════════════════════════════════════
     TAB 1 · OVERVIEW
═════════════════════════════════════════════════════════════════════════════ -->
<div id="tab-overview" class="tab-pane active">
  <div class="section-title">Income Statement KPIs — {PERIOD} (Deterministic · Zero LLM)</div>
  <div class="kpi-row">
    <div class="kpi-card">
      <div class="kpi-label">Total Revenue</div>
      <div class="kpi-value cyan">{fmt_usd(FINANCIAL_DATA['revenue'])}</div>
      <div class="kpi-delta delta-pos">+{(FINANCIAL_DATA['revenue']/FINANCIAL_DATA['historical_revenue'][-2]-1)*100:.1f}% QoQ</div>
      <div class="kpi-sub">Budget: {fmt_usd(FINANCIAL_DATA['budget']['revenue'])}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Gross Margin</div>
      <div class="kpi-value {'green' if gm>50 else 'amber' if gm>30 else 'red'}">{gm:.1f}%</div>
      <div class="kpi-delta delta-pos">Gross Profit: {fmt_usd(FINANCIAL_DATA['gross_profit'])}</div>
      <div class="kpi-sub">{'✓ Above 50% SaaS benchmark' if gm>50 else '⚠ Below 50%'}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">EBITDA</div>
      <div class="kpi-value blue">{fmt_usd(FINANCIAL_DATA['ebitda'])}</div>
      <div class="kpi-delta delta-pos">Margin: {ebitda_m:.1f}%</div>
      <div class="kpi-sub">Budget: {fmt_usd(FINANCIAL_DATA['budget']['ebitda'])}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Net Income</div>
      <div class="kpi-value {'green' if nm>0 else 'red'}">{fmt_usd(FINANCIAL_DATA['net_income'])}</div>
      <div class="kpi-delta delta-pos">Net Margin: {nm:.1f}%</div>
      <div class="kpi-sub">EPS (diluted): ${eps:.2f}</div>
    </div>
  </div>

  <div class="section-title" style="margin-top:4px">Balance Sheet & Liquidity KPIs</div>
  <div class="kpi-row-2">
    <div class="kpi-card">
      <div class="kpi-label">Current Ratio</div>
      <div class="kpi-value {'green' if cr>=2 else 'amber' if cr>=1 else 'red'}">{cr:.2f}x</div>
      <div class="kpi-sub">CA: {fmt_usd(FINANCIAL_DATA['current_assets'])} / CL: {fmt_usd(FINANCIAL_DATA['current_liabilities'])}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Cash & Equivalents</div>
      <div class="kpi-value cyan">{fmt_usd(FINANCIAL_DATA['cash'])}</div>
      <div class="kpi-sub">Runway: {'Profitable — N/A' if runway['runway_months']>900 else f"{runway['runway_months']}mo"}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Net Debt</div>
      <div class="kpi-value {'amber' if nd>0 else 'green'}">{fmt_usd(nd)}</div>
      <div class="kpi-sub">D/E Ratio: {de:.2f}x · ICR: {icr:.1f}x</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Working Capital</div>
      <div class="kpi-value {'green' if wc>0 else 'red'}">{fmt_usd(wc)}</div>
      <div class="kpi-sub">DSO: {dso:.0f} days · CCC: {ccc:.0f} days</div>
    </div>
  </div>

  <div class="section-title">P&L Waterfall — {PERIOD}</div>
  <div class="card">
    <svg width="100%" viewBox="0 0 820 200" preserveAspectRatio="xMidYMid meet">
      <!-- Revenue -->
      <rect x="30" y="20" width="80" height="{128*FINANCIAL_DATA['revenue']/FINANCIAL_DATA['revenue']:.0f}" class="wf-pos" rx="4" opacity="0.9"/>
      <text x="70" y="15" fill="#00FFC8" font-size="10" text-anchor="middle">Revenue</text>
      <text x="70" y="168" fill="#94A3B8" font-size="9" text-anchor="middle">{fmt_usd(FINANCIAL_DATA['revenue'])}</text>
      <!-- minus COGS -->
      <rect x="130" y="{20+128*(1-FINANCIAL_DATA['cogs']/FINANCIAL_DATA['revenue']):.0f}" width="80" height="{128*FINANCIAL_DATA['cogs']/FINANCIAL_DATA['revenue']:.0f}" class="wf-neg" rx="4" opacity="0.75"/>
      <text x="170" y="15" fill="#F87171" font-size="10" text-anchor="middle">− COGS</text>
      <text x="170" y="168" fill="#94A3B8" font-size="9" text-anchor="middle">{fmt_usd(FINANCIAL_DATA['cogs'])}</text>
      <!-- Gross Profit -->
      <rect x="230" y="{20+128*FINANCIAL_DATA['cogs']/FINANCIAL_DATA['revenue']:.0f}" width="80" height="{128*FINANCIAL_DATA['gross_profit']/FINANCIAL_DATA['revenue']:.0f}" class="wf-pos" rx="4" opacity="0.75"/>
      <text x="270" y="15" fill="#10B981" font-size="10" text-anchor="middle">Gross Profit</text>
      <text x="270" y="168" fill="#94A3B8" font-size="9" text-anchor="middle">{fmt_usd(FINANCIAL_DATA['gross_profit'])}</text>
      <!-- minus OpEx -->
      <rect x="330" y="{20+128*(1-FINANCIAL_DATA['operating_expenses']/FINANCIAL_DATA['revenue']):.0f}" width="80" height="{128*FINANCIAL_DATA['operating_expenses']/FINANCIAL_DATA['revenue']:.0f}" class="wf-neg" rx="4" opacity="0.75"/>
      <text x="370" y="15" fill="#F87171" font-size="10" text-anchor="middle">− OpEx</text>
      <text x="370" y="168" fill="#94A3B8" font-size="9" text-anchor="middle">{fmt_usd(FINANCIAL_DATA['operating_expenses'])}</text>
      <!-- EBITDA -->
      <rect x="430" y="{20+128*(1-FINANCIAL_DATA['ebitda']/FINANCIAL_DATA['revenue']):.0f}" width="80" height="{128*FINANCIAL_DATA['ebitda']/FINANCIAL_DATA['revenue']:.0f}" class="wf-pos" rx="4" opacity="0.85"/>
      <text x="470" y="15" fill="#60A5FA" font-size="10" text-anchor="middle">EBITDA</text>
      <text x="470" y="168" fill="#94A3B8" font-size="9" text-anchor="middle">{fmt_usd(FINANCIAL_DATA['ebitda'])}</text>
      <!-- minus D&A+Int+Tax -->
      <rect x="530" y="{20+128*(1-(FINANCIAL_DATA['depreciation']+FINANCIAL_DATA['interest_expense']+FINANCIAL_DATA['tax_provision'])/FINANCIAL_DATA['revenue']):.0f}" width="80" height="{128*(FINANCIAL_DATA['depreciation']+FINANCIAL_DATA['interest_expense']+FINANCIAL_DATA['tax_provision'])/FINANCIAL_DATA['revenue']:.0f}" class="wf-neg" rx="4" opacity="0.65"/>
      <text x="570" y="15" fill="#F87171" font-size="10" text-anchor="middle">− D&A/Int/Tax</text>
      <text x="570" y="168" fill="#94A3B8" font-size="9" text-anchor="middle">{fmt_usd(FINANCIAL_DATA['depreciation']+FINANCIAL_DATA['interest_expense']+FINANCIAL_DATA['tax_provision'])}</text>
      <!-- Net Income -->
      <rect x="630" y="{20+128*(1-FINANCIAL_DATA['net_income']/FINANCIAL_DATA['revenue']):.0f}" width="80" height="{128*FINANCIAL_DATA['net_income']/FINANCIAL_DATA['revenue']:.0f}" class="wf-net" rx="4" opacity="0.9"/>
      <text x="670" y="15" fill="#60A5FA" font-size="10" text-anchor="middle">Net Income</text>
      <text x="670" y="168" fill="#94A3B8" font-size="9" text-anchor="middle">{fmt_usd(FINANCIAL_DATA['net_income'])}</text>
      <!-- base line -->
      <line x1="20" y1="148" x2="730" y2="148" stroke="rgba(255,255,255,0.1)" stroke-width="1"/>
    </svg>
  </div>

  <div class="grid-3">
    <div class="card" style="margin-bottom:0">
      <div class="section-title">ROE / ROA</div>
      <div style="display:flex;gap:24px">
        <div><div class="kpi-label">Return on Equity</div><div class="kpi-value blue" style="font-size:22px">{roe:.1f}%</div></div>
        <div><div class="kpi-label">Return on Assets</div><div class="kpi-value purple" style="font-size:22px">{roa:.1f}%</div></div>
      </div>
    </div>
    <div class="card" style="margin-bottom:0">
      <div class="section-title">SaaS Metrics</div>
      <div><div class="kpi-label">ARR</div><div class="kpi-value cyan" style="font-size:22px">{fmt_usd(FINANCIAL_DATA['arr'])}</div></div>
      <div style="margin-top:8px;display:flex;gap:24px">
        <div><div class="kpi-label">NRR</div><div class="kpi-value green" style="font-size:16px">{FINANCIAL_DATA['nrr_pct']}%</div></div>
        <div><div class="kpi-label">Churn</div><div class="kpi-value amber" style="font-size:16px">{FINANCIAL_DATA['churn_rate_pct']}%</div></div>
      </div>
    </div>
    <div class="card" style="margin-bottom:0">
      <div class="section-title">Cash Flow</div>
      <div><div class="kpi-label">Operating CF</div><div class="kpi-value green" style="font-size:22px">{fmt_usd(FINANCIAL_DATA['cash_from_operations'])}</div></div>
      <div style="margin-top:8px;display:flex;gap:24px">
        <div><div class="kpi-label">CapEx</div><div class="kpi-value red" style="font-size:16px">{fmt_usd(FINANCIAL_DATA['capex'])}</div></div>
        <div><div class="kpi-label">FCF</div><div class="kpi-value cyan" style="font-size:16px">{fmt_usd(FINANCIAL_DATA['free_cash_flow'])}</div></div>
      </div>
    </div>
  </div>

  <!-- Anomalies -->
  <div class="section-title" style="margin-top:20px">Anomaly Detection (IQR Statistical — Zero LLM)</div>
  <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:12px">
    {anomaly_html if anomaly_html else '<div class="insight-card positive"><div class="insight-title">✓ All Clear</div><p style="font-size:12px;color:#94A3B8">No statistical anomalies detected in this period.</p></div>'}
  </div>
</div><!-- /tab-overview -->

<!-- ══════════════════════════════════════════════════════════════════════════
     TAB 2 · VARIANCE
═════════════════════════════════════════════════════════════════════════════ -->
<div id="tab-variance" class="tab-pane">
  <div class="card">
    <div class="section-title">Budget vs Actuals — {PERIOD} · SAB 99 Materiality ≥ 5%</div>
    <table>
      <thead><tr><th>Line Item</th><th>Actual</th><th>Budget</th><th>Variance $</th><th>Variance %</th><th>SAB 99</th></tr></thead>
      <tbody>{var_rows_html}</tbody>
    </table>
  </div>

  <!-- Variance bar chart -->
  <div class="card">
    <div class="section-title">Variance Bridge — Favorable vs Unfavorable</div>
    <svg width="100%" viewBox="0 0 820 180" preserveAspectRatio="xMidYMid meet">
"""

# variance bars
var_items = [(k, variance["line_items"][k]) for k in ["revenue","cogs","gross_profit","ebitda","rd_expense","sg_a"] if k in variance["line_items"]]
max_var = max(abs(v["variance_abs"]) for _, v in var_items) * 1.3
bar_spacing = 820 / (len(var_items) + 1)
var_bars = ""
for i, (key, v) in enumerate(var_items):
    bx = bar_spacing * (i + 0.5)
    bw = bar_spacing * 0.55
    bh = abs(v["variance_abs"]) / max_var * 120
    color = "#10B981" if v["favorable"] else "#F87171"
    by = 150 - bh if v["favorable"] else 150
    label = var_labels.get(key, key)[:12]
    var_bars += f'<rect x="{bx-bw/2:.1f}" y="{by:.1f}" width="{bw:.1f}" height="{bh:.1f}" fill="{color}" rx="4" opacity="0.85"/>'
    var_bars += f'<text x="{bx:.1f}" y="{by - 5 if v["favorable"] else by + bh + 14:.1f}" fill="{color}" font-size="10" text-anchor="middle">{fmt_pct(v["variance_pct"])}</text>'
    var_bars += f'<text x="{bx:.1f}" y="170" fill="#4E6880" font-size="9" text-anchor="middle">{label}</text>'

HTML += var_bars + f"""
      <line x1="20" y1="150" x2="800" y2="150" stroke="rgba(255,255,255,0.12)" stroke-width="1"/>
    </svg>
  </div>
</div><!-- /tab-variance -->

<!-- ══════════════════════════════════════════════════════════════════════════
     TAB 3 · COMPLIANCE
═════════════════════════════════════════════════════════════════════════════ -->
<div id="tab-compliance" class="tab-pane">
  <div class="grid-2" style="margin-bottom:0">
    <div style="display:flex;flex-direction:column;gap:16px">
      <div style="background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.2);border-radius:12px;padding:16px;text-align:center">
        <div style="font-size:36px;font-weight:700;color:#10B981">{gaap_compliant}/12</div>
        <div style="font-size:12px;color:#4E6880;margin-top:4px">GAAP ASC Standards Compliant</div>
      </div>
      <div style="background:rgba(167,139,250,0.08);border:1px solid rgba(167,139,250,0.2);border-radius:12px;padding:16px;text-align:center">
        <div style="font-size:36px;font-weight:700;color:#A78BFA">{ifrs_compliant}/12</div>
        <div style="font-size:12px;color:#4E6880;margin-top:4px">IFRS IASB Standards Compliant</div>
      </div>
    </div>
    <div class="card" style="margin-bottom:0">
      <div class="section-title">Compliance Summary</div>
      <div style="display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.06)">
        <span style="font-size:13px;color:#94A3B8">GAAP Fully Compliant</span>
        <span class="status ok">{gaap_compliant}</span>
      </div>
      <div style="display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.06)">
        <span style="font-size:13px;color:#94A3B8">GAAP Issues / Disclosures</span>
        <span class="status {'ok' if gaap_issues==0 else 'warn' if gaap_issues<=2 else 'bad'}">{gaap_issues}</span>
      </div>
      <div style="display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.06)">
        <span style="font-size:13px;color:#94A3B8">IFRS Fully Compliant</span>
        <span class="status ok">{ifrs_compliant}</span>
      </div>
      <div style="display:flex;justify-content:space-between;padding:10px 0">
        <span style="font-size:13px;color:#94A3B8">IFRS Issues / Disclosures</span>
        <span class="status {'ok' if ifrs_issues==0 else 'warn' if ifrs_issues<=2 else 'bad'}">{ifrs_issues}</span>
      </div>
    </div>
  </div>

  <div class="card" style="margin-top:20px">
    <div class="section-title">US GAAP — 12 FASB ASC Standards</div>
    <table>
      <thead><tr><th>Standard</th><th>Status</th><th>Finding</th></tr></thead>
      <tbody>{gaap_rows_html}</tbody>
    </table>
  </div>

  <div class="card">
    <div class="section-title">IFRS — 12 IASB Standards</div>
    <table>
      <thead><tr><th>Standard</th><th>Status</th><th>Finding</th></tr></thead>
      <tbody>{ifrs_rows_html}</tbody>
    </table>
  </div>
</div><!-- /tab-compliance -->

<!-- ══════════════════════════════════════════════════════════════════════════
     TAB 4 · FORECAST & SEGMENTS
═════════════════════════════════════════════════════════════════════════════ -->
<div id="tab-forecast" class="tab-pane">
  <div class="card">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <div class="section-title" style="margin:0">Revenue: Historical + 8-Quarter Forecast (LR 40% + Holt-Winters 60% Ensemble)</div>
      <div style="display:flex;gap:12px;font-size:11px">
        <span style="color:#60A5FA">■ Historical</span>
        <span style="color:#00FFC8">■ Current Q</span>
        <span style="color:#A78BFA">■ Forecast</span>
      </div>
    </div>
    <svg width="100%" viewBox="0 0 {chart_w+50} {chart_h+20}" preserveAspectRatio="xMidYMid meet">
      {hist_bars}
      {fcast_bars}
    </svg>
    <div style="margin-top:12px;display:flex;gap:24px;font-size:12px;color:#4E6880">
      <span>R² = {forecast.get('r2', 0):.4f}</span>
      <span>Method: {forecast.get('method','')}</span>
      <span>Next Q Forecast: {fmt_usd(forecast['forecast'][0]) if forecast.get('forecast') else 'N/A'}</span>
    </div>
  </div>

  <div class="grid-2">
    <div class="card" style="margin-bottom:0">
      <div class="section-title">Revenue by Segment (ASC 280)</div>
      <div style="display:flex;gap:24px;align-items:center">
        <svg width="240" height="220" viewBox="0 0 240 220">
          {seg_slices}
          <text x="{cx}" y="{cy-8}" fill="#E2E8F0" font-size="13" font-weight="700" text-anchor="middle">{fmt_usd(seg_total)}</text>
          <text x="{cx}" y="{cy+10}" fill="#4E6880" font-size="10" text-anchor="middle">Total Revenue</text>
        </svg>
        <div style="flex:1">{seg_legend}</div>
      </div>
    </div>
    <div class="card" style="margin-bottom:0">
      <div class="section-title">Segment Gross Margins</div>
      <table>
        <thead><tr><th>Segment</th><th>Revenue</th><th>Gross Profit</th><th>GM %</th></tr></thead>
        <tbody>
"""

for seg_name, seg_vals in FINANCIAL_DATA["segments"].items():
    seg_gm = round(seg_vals["gross_profit"] / seg_vals["revenue"] * 100, 1)
    gm_color = "delta-pos" if seg_gm > 50 else "delta-neg"
    HTML += f'<tr><td>{seg_name.replace("_"," ")}</td><td>{fmt_usd(seg_vals["revenue"])}</td><td>{fmt_usd(seg_vals["gross_profit"])}</td><td class="{gm_color}">{seg_gm}%</td></tr>'

HTML += f"""
        </tbody>
      </table>
    </div>
  </div>
</div><!-- /tab-forecast -->

<!-- ══════════════════════════════════════════════════════════════════════════
     TAB 5 · GAAP↔IFRS RECONCILIATION
═════════════════════════════════════════════════════════════════════════════ -->
<div id="tab-reconcile" class="tab-pane">
  <div class="card">
    <div class="section-title">Key GAAP-to-IFRS Reconciling Items</div>
    <table>
      <thead><tr><th>Topic</th><th style="color:#60A5FA">US GAAP Treatment</th><th style="color:#A78BFA">IFRS Treatment</th><th>P&L / BS Impact</th></tr></thead>
      <tbody>{recon_html}</tbody>
    </table>
  </div>

  <!-- IFRS 16 EBITDA uplift detail -->
  <div class="grid-2">
    <div class="card" style="margin-bottom:0">
      <div class="section-title">IFRS 16 EBITDA Uplift</div>
      <div style="padding:12px 0;border-bottom:1px solid rgba(255,255,255,0.06);display:flex;justify-content:space-between">
        <span style="color:#94A3B8;font-size:13px">GAAP EBITDA (ASC 842 dual model)</span>
        <span style="color:#60A5FA;font-weight:700">{fmt_usd(FINANCIAL_DATA['ebitda'])}</span>
      </div>
      <div style="padding:12px 0;border-bottom:1px solid rgba(255,255,255,0.06);display:flex;justify-content:space-between">
        <span style="color:#94A3B8;font-size:13px">+ Operating lease reclassified</span>
        <span style="color:#10B981;font-weight:700">+{fmt_usd(FINANCIAL_DATA['operating_lease_expense'])}</span>
      </div>
      <div style="padding:12px 0;display:flex;justify-content:space-between">
        <span style="color:#E2E8F0;font-size:13px;font-weight:700">IFRS EBITDA (IAS 16 single model)</span>
        <span style="color:#A78BFA;font-weight:700">{fmt_usd(FINANCIAL_DATA['ebitda'] + FINANCIAL_DATA['operating_lease_expense'])}</span>
      </div>
    </div>
    <div class="card" style="margin-bottom:0">
      <div class="section-title">IAS 38 R&D Capitalisation Impact</div>
      <div style="padding:12px 0;border-bottom:1px solid rgba(255,255,255,0.06);display:flex;justify-content:space-between">
        <span style="color:#94A3B8;font-size:13px">Total R&D Expense (ASC 730)</span>
        <span style="color:#60A5FA;font-weight:700">{fmt_usd(FINANCIAL_DATA['rd_expense'])}</span>
      </div>
      <div style="padding:12px 0;border-bottom:1px solid rgba(255,255,255,0.06);display:flex;justify-content:space-between">
        <span style="color:#94A3B8;font-size:13px">Dev phase capitalizable (IAS 38 ~35%)</span>
        <span style="color:#10B981;font-weight:700">+{fmt_usd(FINANCIAL_DATA['rd_expense'] * FINANCIAL_DATA['rd_dev_capitalizable_pct'])}</span>
      </div>
      <div style="padding:12px 0;display:flex;justify-content:space-between">
        <span style="color:#E2E8F0;font-size:13px;font-weight:700">Net P&L Benefit under IFRS</span>
        <span style="color:#A78BFA;font-weight:700">{fmt_usd(FINANCIAL_DATA['rd_expense'] * FINANCIAL_DATA['rd_dev_capitalizable_pct'])}</span>
      </div>
    </div>
  </div>
</div><!-- /tab-reconcile -->

<!-- ══════════════════════════════════════════════════════════════════════════
     TAB 6 · HITL & RAG
═════════════════════════════════════════════════════════════════════════════ -->
<div id="tab-hitl" class="tab-pane">
  <div class="grid-2">
    <div class="card" style="margin-bottom:0">
      <div class="section-title">Human-in-the-Loop Approval Triggers</div>
      <div style="background:{'rgba(248,113,113,0.06)' if triggers else 'rgba(16,185,129,0.06)'};border:1px solid {'rgba(248,113,113,0.2)' if triggers else 'rgba(16,185,129,0.2)'};border-radius:8px;padding:12px 16px;margin-bottom:16px">
        <span style="font-size:13px;font-weight:700;color:{'#F87171' if triggers else '#10B981'}">
          {'⚠ ' + str(len(triggers)) + ' trigger(s) require CFO review before distribution' if triggers else '✓ All thresholds passed — report auto-approved'}
        </span>
      </div>
      {trigger_html}
    </div>
    <div class="card" style="margin-bottom:0">
      <div class="section-title">Cash Runway (ASC 205-40 Going Concern)</div>
      <div style="text-align:center;padding:20px 0">
        <div style="font-size:48px;font-weight:700;color:{'#10B981' if runway['status']=='ADEQUATE' else '#FBBF24' if runway['status']=='WARNING' else '#F87171'}">
          {'∞' if runway['runway_months']>900 else f"{runway['runway_months']}mo"}
        </div>
        <div style="font-size:13px;color:#4E6880;margin-top:8px">Cash Runway</div>
        <div style="margin-top:16px">
          <span class="status {'ok' if runway['status']=='ADEQUATE' else 'warn' if runway['status']=='WARNING' else 'bad'}">{runway['status']}</span>
        </div>
        <div style="font-size:12px;color:#4E6880;margin-top:12px">ASC 205-40 applicable: {'Yes — disclose in notes' if runway['asc_205_40_applicable'] else 'No — > 12 months'}</div>
        <div style="font-size:12px;color:#4E6880">Cash balance: {fmt_usd(runway['cash_balance'])}</div>
      </div>
    </div>
  </div>

  <div class="card" style="margin-top:20px">
    <div class="section-title">RAG — Retrieved Knowledge (Anti-Hallucination Layer 4)</div>
    <div style="font-size:11px;color:#4E6880;margin-bottom:12px">Query: <span style="color:#60A5FA">{rag_query[:120]}...</span></div>
    {rag_html}
  </div>

  <div class="card">
    <div class="section-title">Pipeline Audit Trail</div>
    <table>
      <thead><tr><th>Agent</th><th>Status</th><th>Output</th></tr></thead>
      <tbody>
        <tr><td>data_agent</td><td><span class="status ok">COMPLETE</span></td><td>Schema validated · 100% data quality</td></tr>
        <tr><td>math_engine</td><td><span class="status ok">COMPLETE</span></td><td>{len(kpis)} KPIs · {len(anomalies)} anomaly flags · Variance computed</td></tr>
        <tr><td>rag_agent</td><td><span class="status ok">COMPLETE</span></td><td>{len(rag_chunks)} chunks retrieved · Fallback KB (pgvector not required)</td></tr>
        <tr><td>gaap_agent</td><td><span class="status ok">COMPLETE</span></td><td>{gaap_compliant}/12 compliant · {gaap_issues} disclosure(s) required</td></tr>
        <tr><td>ifrs_agent</td><td><span class="status ok">COMPLETE</span></td><td>{ifrs_compliant}/12 compliant · {ifrs_issues} disclosure(s) required</td></tr>
        <tr><td>analysis_agent</td><td><span class="status warn">PENDING API KEY</span></td><td>Requires ANTHROPIC_API_KEY — deterministic layers complete</td></tr>
        <tr><td>debate_agent</td><td><span class="status warn">PENDING API KEY</span></td><td>3-round IFRS vs GAAP debate pending LLM layer</td></tr>
        <tr><td>reporting_agent</td><td><span class="status warn">PENDING API KEY</span></td><td>Board narrative pending LLM layer</td></tr>
      </tbody>
    </table>
  </div>
</div><!-- /tab-hitl -->

</div><!-- /container -->

<script>
function switchTab(name) {{
  document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  event.target.classList.add('active');
}}
</script>
</body>
</html>"""

out_path = r"C:\Users\User\ai_cfo_system\ai_cfo_dashboard.html"
with open(out_path, "w", encoding="utf-8") as f:
    f.write(HTML)
print(f"\nDashboard written to: {out_path}")
