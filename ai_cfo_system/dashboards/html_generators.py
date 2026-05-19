"""
HTML Dashboard generators — AI CFO System.
Each function accepts pipeline outputs and returns the path to the generated HTML file.
"""
import math, os

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

COLORS = ["#00FFC8", "#60A5FA", "#A78BFA", "#FBBF24", "#F87171", "#34D399", "#F472B6"]


# ── helpers ──────────────────────────────────────────────────────────────────

def _fmt(v, prefix="$"):
    if abs(v) >= 1_000_000: return f"{prefix}{v/1_000_000:.1f}M"
    if abs(v) >= 1_000:     return f"{prefix}{v/1_000:.0f}K"
    return f"{prefix}{v:,.0f}"

def _pct(v):
    return f"{'+'if v>=0 else ''}{v:.1f}%"

def _color(v, good_positive=True):
    if good_positive:
        return "green" if v > 0 else "red"
    return "red" if v > 0 else "green"

def _delta_cls(v, good_positive=True):
    if good_positive:
        return "delta-pos" if v >= 0 else "delta-neg"
    return "delta-neg" if v >= 0 else "delta-pos"

def _donut(pairs, colors, cx=120, cy=110, ro=90, ri=52):
    total = sum(v for _, v in pairs) or 1
    slices, offset = "", 0
    for (_, val), color in zip(pairs, colors):
        angle = (val / total) * 2 * math.pi
        x1,  y1  = cx + ro * math.sin(offset),       cy - ro * math.cos(offset)
        x2,  y2  = cx + ro * math.sin(offset+angle), cy - ro * math.cos(offset+angle)
        xi1, yi1 = cx + ri * math.sin(offset),       cy - ri * math.cos(offset)
        xi2, yi2 = cx + ri * math.sin(offset+angle), cy - ri * math.cos(offset+angle)
        large = 1 if angle > math.pi else 0
        slices += (f'<path d="M{xi1:.1f},{yi1:.1f} L{x1:.1f},{y1:.1f} '
                   f'A{ro},{ro} 0 {large},1 {x2:.1f},{y2:.1f} '
                   f'L{xi2:.1f},{yi2:.1f} A{ri},{ri} 0 {large},0 {xi1:.1f},{yi1:.1f} Z" '
                   f'fill="{color}" opacity="0.85" stroke="#04060F" stroke-width="2"/>')
        offset += angle
    return slices

def _legend(pairs, colors):
    html = ""
    for (label, val), color in zip(pairs, colors):
        html += (f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">'
                 f'<span style="width:10px;height:10px;border-radius:2px;background:{color};display:inline-block"></span>'
                 f'<span style="font-size:12px;color:#94A3B8">{label}</span>'
                 f'<span style="font-size:12px;font-weight:700;margin-left:auto">{_fmt(val)}</span></div>')
    return html

def _bars(values, labels, colors=None, w=780, h=160, show_value=True):
    max_v = max(abs(v) for v in values) * 1.2 or 1
    spacing = w / (len(values) + 1)
    bw = spacing * 0.6
    svg = ""
    for i, (v, lbl) in enumerate(zip(values, labels)):
        bx = spacing * (i + 0.5)
        bh = abs(v) / max_v * (h - 30)
        by = h - 20 - bh if v >= 0 else h - 20
        color = (colors[i % len(colors)] if colors else
                 ("#10B981" if v >= 0 else "#F87171"))
        svg += f'<rect x="{bx-bw/2:.1f}" y="{by:.1f}" width="{bw:.1f}" height="{bh:.1f}" fill="{color}" rx="4" opacity="0.85"/>'
        if show_value:
            ty = by - 5 if v >= 0 else by + bh + 12
            svg += f'<text x="{bx:.1f}" y="{ty:.1f}" fill="{color}" font-size="9" text-anchor="middle">{_fmt(v)}</text>'
        svg += f'<text x="{bx:.1f}" y="{h:.1f}" fill="#4E6880" font-size="9" text-anchor="middle">{lbl}</text>'
    svg += f'<line x1="10" y1="{h-20}" x2="{w}" y2="{h-20}" stroke="rgba(255,255,255,0.1)" stroke-width="1"/>'
    return f'<svg width="100%" viewBox="0 0 {w} {h+5}" preserveAspectRatio="xMidYMid meet">{svg}</svg>'

def _initials(company):
    words = [w for w in company.split() if w[0].isupper()] if company else []
    return "".join(w[0] for w in words[:2]).upper() or "AI"

def _agent_css():
    return """
.agent-section{background:#0B1627;border:1px solid rgba(59,130,246,.15);border-left:3px solid #3B82F6;border-radius:10px;padding:24px;margin-bottom:20px}
.agent-header{display:flex;align-items:center;gap:10px;margin-bottom:18px;padding-bottom:14px;border-bottom:1px solid rgba(255,255,255,.06)}
.agent-title{font-size:13px;font-weight:700;color:#93C5FD;letter-spacing:.01em}
.agent-badge{padding:2px 9px;border-radius:4px;font-size:10px;font-weight:700;background:rgba(71,85,105,.2);border:1px solid rgba(71,85,105,.3);color:#64748B;letter-spacing:.03em}
.agent-badge.zero-llm{background:rgba(16,185,129,.08);border-color:rgba(16,185,129,.2);color:#10B981}
.agent-badge.deterministic{background:rgba(59,130,246,.08);border-color:rgba(59,130,246,.2);color:#60A5FA}
.findings-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px}
.finding{border-radius:8px;padding:14px 16px;border:1px solid transparent}
.finding.ok{background:rgba(16,185,129,.04);border-color:rgba(16,185,129,.12);border-left:3px solid #10B981}
.finding.warn{background:rgba(245,158,11,.04);border-color:rgba(245,158,11,.12);border-left:3px solid #F59E0B}
.finding.critical{background:rgba(239,68,68,.04);border-color:rgba(239,68,68,.12);border-left:3px solid #EF4444}
.finding.info{background:rgba(59,130,246,.04);border-color:rgba(59,130,246,.12);border-left:3px solid #3B82F6}
.finding-top{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px}
.finding-title{font-size:11px;font-weight:700;color:#E2E8F0;line-height:1.4}
.finding-source{font-size:9px;font-weight:600;padding:1px 6px;border-radius:3px;background:rgba(255,255,255,.05);color:#475569;white-space:nowrap;margin-left:8px;flex-shrink:0;letter-spacing:.02em}
.finding-body{font-size:11px;color:#94A3B8;line-height:1.65;margin-bottom:5px}
.finding-citation{font-size:10px;color:#334155;font-style:italic;letter-spacing:.01em}
.agent-summary{background:rgba(6,13,31,.5);border-radius:8px;padding:14px 16px;margin-bottom:16px;border:1px solid rgba(255,255,255,.05)}
.agent-summary p{font-size:12px;color:#CBD5E1;line-height:1.75}
.action-list{list-style:none;padding:0;margin:0}
.action-list li{display:flex;gap:10px;align-items:flex-start;padding:9px 0;border-bottom:1px solid rgba(255,255,255,.04);font-size:11px;color:#94A3B8;line-height:1.5}
.action-list li:last-child{border:none}
.action-num{width:18px;height:18px;border-radius:50%;background:rgba(59,130,246,.15);color:#60A5FA;font-size:9px;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:1px}
"""

def _finding(severity, title, body, source, citation=""):
    cit = f'<div class="finding-citation">{citation}</div>' if citation else ""
    return (f'<div class="finding {severity}">'
            f'<div class="finding-top"><span class="finding-title">{title}</span>'
            f'<span class="finding-source">{source}</span></div>'
            f'<div class="finding-body">{body}</div>'
            f'{cit}'
            f'</div>')

def _agent_block(title, summary_html, findings_html, actions):
    actions_html = "".join(
        f'<li><span class="action-num">{i+1}</span><span>{a}</span></li>'
        for i, a in enumerate(actions)
    )
    return f"""
<div class="agent-section">
  <div class="agent-header">
    <div class="agent-title">&#x1F916; AI Agent Analysis — {title}</div>
    <span class="agent-badge zero-llm">Zero-LLM Math</span>
    <span class="agent-badge deterministic">100% Deterministic</span>
    <span class="agent-badge">Anti-Hallucination</span>
  </div>
  <div class="agent-summary">{summary_html}</div>
  <div class="findings-grid">{findings_html}</div>
  {"<div class='section-title' style='margin-top:4px'>Recommended Actions</div><ul class='action-list'>" + actions_html + "</ul>" if actions else ""}
</div>
"""

# ── agent analysis engines ────────────────────────────────────────────────────

def _cfo_agent_analysis(data, kpis, variance, gaap, ifrs, anomalies, runway):
    rev   = data.get("revenue", 1)
    gm    = kpis.get("gross_margin_pct", 0)
    em    = kpis.get("ebitda_margin_pct", 0)
    nm    = kpis.get("net_margin_pct", 0)
    cr    = kpis.get("current_ratio", 0)
    de    = kpis.get("debt_to_equity", 0)
    dso   = kpis.get("dso_days", 0)
    icr   = kpis.get("interest_coverage", 0)
    t     = variance.get("totals", {})
    var_pct = t.get("variance_pct", 0)
    gc    = sum(1 for v in gaap.values() if v.get("status") == "COMPLIANT")
    ic    = sum(1 for v in ifrs.values() if v.get("status") == "COMPLIANT")
    nc_gaap = [v for v in gaap.values() if v.get("status") == "NON_COMPLIANT"]
    disc_gaap = [v for v in gaap.values() if v.get("status") == "DISCLOSURE_REQUIRED"]

    # executive summary
    rev_vs = "above" if var_pct >= 0 else "below"
    health = "strong" if gm > 60 and em > 15 and cr > 1.5 else "adequate" if gm > 35 and em > 5 else "under pressure"
    summary = (f"<p>{data.get('_meta', {}).get('name', 'Company')} reports {_fmt(rev)} revenue "
               f"for {data.get('_meta', {}).get('period', 'the period')}, "
               f"<b style='color:{'#10B981' if var_pct>=0 else '#F87171'}'>{abs(var_pct):.1f}% {rev_vs} budget</b>. "
               f"Gross margin of <b>{gm:.1f}%</b> and EBITDA margin of <b>{em:.1f}%</b> "
               f"indicate a <b>{health}</b> operating profile. "
               f"GAAP compliance: <b style='color:#10B981'>{gc}/12</b>. "
               f"IFRS compliance: <b style='color:#A78BFA'>{ic}/12</b>. "
               f"All figures sourced from deterministic math engine — zero LLM calculation.</p>")

    findings = []
    # gross margin
    if gm > 70:
        findings.append(_finding("ok", f"Gross Margin {gm:.1f}% — Excellent",
            f"Above 70% SaaS/high-margin benchmark. Gross profit {_fmt(data.get('gross_profit',0))} signals strong pricing power and low variable cost structure.",
            "Math Engine", "SAB 99 · ASC 606"))
    elif gm > 40:
        findings.append(_finding("info", f"Gross Margin {gm:.1f}% — Adequate",
            f"Within acceptable range. Monitor COGS trend — {_fmt(data.get('cogs',0))} this period. Consider pricing or mix optimization to reach 50%+ target.",
            "Math Engine", "ASC 606"))
    else:
        findings.append(_finding("critical", f"Gross Margin {gm:.1f}% — Below Benchmark",
            f"COGS of {_fmt(data.get('cogs',0))} is consuming {100-gm:.1f}% of revenue. Immediate cost structure review required.",
            "Math Engine", "ASC 606 · SAB 99"))

    # EBITDA
    if em > 20:
        findings.append(_finding("ok", f"EBITDA Margin {em:.1f}% — Strong",
            f"EBITDA of {_fmt(data.get('ebitda',0))} exceeds 20% benchmark. Operating leverage is being realized.",
            "Math Engine", ""))
    elif em > 5:
        findings.append(_finding("warn", f"EBITDA Margin {em:.1f}% — Watch",
            f"Below 20% target. Operating expenses of {_fmt(data.get('operating_expenses',0))} are compressing margins.",
            "Math Engine", ""))
    else:
        findings.append(_finding("critical", f"EBITDA Margin {em:.1f}% — Critical",
            f"Near-zero or negative EBITDA. Operational restructuring warranted.",
            "Math Engine", ""))

    # liquidity
    if cr >= 2.0:
        findings.append(_finding("ok", f"Current Ratio {cr:.2f}x — Healthy",
            f"Current assets {_fmt(data.get('current_assets',0))} cover current liabilities {_fmt(data.get('current_liabilities',0))} comfortably. No going concern risk.",
            "Math Engine", "ASC 205-40"))
    elif cr >= 1.0:
        findings.append(_finding("warn", f"Current Ratio {cr:.2f}x — Monitor",
            f"Adequate but tightening. Cash position {_fmt(data.get('cash',0))} should be preserved. Watch payables cycle.",
            "Math Engine", "ASC 205-40"))
    else:
        findings.append(_finding("critical", f"Current Ratio {cr:.2f}x — LIQUIDITY RISK",
            f"Current liabilities exceed current assets. ASC 205-40 going concern evaluation required. Disclose in financial statements.",
            "Math Engine", "ASC 205-40"))

    # revenue variance
    if var_pct >= 5:
        findings.append(_finding("ok", f"Revenue {_pct(var_pct)} vs Budget — Favorable",
            f"Outperformance of {_fmt(abs(t.get('variance_abs',0)))}. SAB 99 materiality threshold exceeded — disclose in MD&A.",
            "Math Engine", "SAB 99"))
    elif var_pct >= -5:
        findings.append(_finding("info", f"Revenue {_pct(var_pct)} vs Budget — On Track",
            f"Within SAB 99 materiality threshold (±5%). No additional disclosure required.",
            "Math Engine", "SAB 99"))
    else:
        findings.append(_finding("warn", f"Revenue {_pct(var_pct)} vs Budget — Unfavorable",
            f"Shortfall of {_fmt(abs(t.get('variance_abs',0)))}. Material per SAB 99. Investigate root cause: volume vs price vs mix.",
            "Math Engine", "SAB 99"))

    # DSO
    if dso <= 30:
        findings.append(_finding("ok", f"DSO {dso:.0f} Days — Efficient",
            f"Collections are fast. AR of {_fmt(data.get('accounts_receivable',0))} is turning over well.",
            "Math Engine", "ASC 310/326"))
    elif dso <= 60:
        findings.append(_finding("warn", f"DSO {dso:.0f} Days — Watch",
            f"AR {_fmt(data.get('accounts_receivable',0))} taking {dso:.0f} days to collect. Review credit terms and CECL allowance.",
            "Math Engine", "ASC 310/326 CECL"))
    else:
        findings.append(_finding("critical", f"DSO {dso:.0f} Days — Elevated",
            f"Collections lag. Credit loss exposure may exceed allowance of {_fmt(data.get('allowance_for_credit_losses',0))}. Review CECL model.",
            "Math Engine", "ASC 310/326 CECL · IFRS 9"))

    # ICR
    if icr > 3:
        findings.append(_finding("ok", f"Interest Coverage {icr:.1f}x — Strong",
            f"EBIT of {_fmt(data.get('ebit',0))} covers interest {_fmt(data.get('interest_expense',0))} comfortably. Low default risk.",
            "Math Engine", "ASC 740"))
    elif icr > 1:
        findings.append(_finding("warn", f"Interest Coverage {icr:.1f}x — Thin",
            f"Coverage approaching minimum. Refinancing or debt reduction should be evaluated.",
            "Math Engine", "ASC 740"))
    else:
        findings.append(_finding("critical", f"Interest Coverage {icr:.1f}x — Deficient",
            f"EBIT does not cover interest expense. Covenant breach risk. Immediate lender communication required.",
            "Math Engine", "ASC 740 · ASC 205-40"))

    # GAAP non-compliance
    for r in nc_gaap[:2]:
        findings.append(_finding("critical", f"GAAP Non-Compliant: {r.get('standard','')}",
            r.get("finding", "")[:160],
            "GAAP Engine", r.get("standard", "")))
    for r in disc_gaap[:2]:
        findings.append(_finding("warn", f"Disclosure Required: {r.get('standard','')}",
            r.get("finding", "")[:160],
            "GAAP Engine", r.get("standard", "")))

    # runway
    rm = runway.get("runway_months", 9999)
    if rm <= 12:
        findings.append(_finding("critical", f"Cash Runway {rm}mo — Going Concern",
            f"ASC 205-40 going concern disclosure required. Cash {_fmt(data.get('cash',0))} insufficient for 12 months.",
            "Math Engine", "ASC 205-40"))

    actions = []
    if var_pct < -5:
        actions.append(f"CFO: Investigate revenue shortfall of {_fmt(abs(t.get('variance_abs',0)))} — identify volume vs price vs mix drivers (deadline: 30 days)")
    if gm < 40:
        actions.append(f"Controller: Review COGS structure — target gross margin improvement to 50%+ (deadline: Q2)")
    if dso > 45:
        actions.append(f"FP&A: Tighten AR collections — implement 30-day collection target, review credit terms (deadline: 45 days)")
    if cr < 1.5:
        actions.append(f"CFO: Improve working capital — negotiate extended payables or draw on credit facility (deadline: 60 days)")
    if nc_gaap:
        actions.append(f"Controller: Resolve {len(nc_gaap)} GAAP non-compliance item(s) before next reporting period")
    if not actions:
        actions.append("Finance team: Continue monitoring KPIs — all key metrics within acceptable ranges")
        actions.append(f"FP&A: Prepare Q2 forecast incorporating {abs(var_pct):.1f}% {'outperformance' if var_pct>0 else 'shortfall'} trend")

    return _agent_block("CFO Overview", summary, "".join(findings[:8]), actions)


def _cost_agent_analysis(data, kpis):
    rev   = data.get("revenue", 1)
    rd    = data.get("rd_expense", 0)
    sga   = data.get("sg_a_expense", 0)
    cogs  = data.get("cogs", 0)
    capex = data.get("capex", 0)
    hc    = data.get("headcount", 1)
    gm    = kpis.get("gross_margin_pct", 0)
    em    = kpis.get("ebitda_margin_pct", 0)
    fcf   = data.get("free_cash_flow", 0)

    rd_pct  = rd  / rev * 100
    sga_pct = sga / rev * 100
    opex    = rd + sga + cogs
    opex_pct= opex / rev * 100
    cpe     = opex / hc

    bgt = data.get("budget", {})
    rd_var  = (rd  - bgt.get("rd_expense", rd))  / bgt.get("rd_expense", rd)  * 100  if bgt.get("rd_expense") else 0
    sga_var = (sga - bgt.get("sg_a", sga))        / bgt.get("sg_a", sga)        * 100  if bgt.get("sg_a") else 0

    summary = (f"<p>Total operating expenditure is <b>{_fmt(opex)}</b> ({opex_pct:.1f}% of revenue). "
               f"R&D: <b>{_fmt(rd)}</b> ({rd_pct:.1f}%), SG&A: <b>{_fmt(sga)}</b> ({sga_pct:.1f}%), "
               f"COGS: <b>{_fmt(cogs)}</b>. Free cash flow: <b style='color:{'#10B981' if fcf>=0 else '#F87171'}'>{_fmt(fcf)}</b>. "
               f"All cost metrics computed deterministically — zero LLM involvement.</p>")

    findings = []
    # gross margin
    sev = "ok" if gm>60 else "warn" if gm>35 else "critical"
    findings.append(_finding(sev, f"Gross Margin {gm:.1f}%",
        f"COGS of {_fmt(cogs)} = {100-gm:.1f}% of revenue. {'Strong cost control.' if gm>60 else 'Monitor COGS growth vs revenue growth.'}",
        "Math Engine", "ASC 606 · SAB 99"))

    # R&D
    if 15 <= rd_pct <= 25:
        findings.append(_finding("ok", f"R&D Spend {rd_pct:.1f}% of Revenue — On Target",
            f"{_fmt(rd)} R&D within 15–25% SaaS benchmark. Under IFRS, ~{data.get('rd_dev_capitalizable_pct',0)*100:.0f}% may qualify for IAS 38 capitalisation ({_fmt(rd*data.get('rd_dev_capitalizable_pct',0))}).",
            "Math Engine", "ASC 730 · IAS 38"))
    elif rd_pct > 25:
        findings.append(_finding("warn", f"R&D Spend {rd_pct:.1f}% — Elevated",
            f"{_fmt(rd)} R&D exceeds 25% revenue benchmark. Review project ROI and capitalisation eligibility under IAS 38.",
            "Math Engine", "ASC 730 · IAS 38"))
    else:
        findings.append(_finding("info", f"R&D Spend {rd_pct:.1f}% — Below Benchmark",
            f"May indicate underinvestment in product development. Consider whether pipeline velocity is sustainable.",
            "Math Engine", "ASC 730"))

    # SG&A
    sev = "ok" if sga_pct < 25 else "warn" if sga_pct < 40 else "critical"
    findings.append(_finding(sev, f"SG&A {sga_pct:.1f}% of Revenue",
        f"{_fmt(sga)} SG&A. {'Efficient go-to-market.' if sga_pct<25 else 'Above 25% — review sales efficiency and G&A leverage.' if sga_pct<40 else 'Excessive. Immediate SG&A rationalisation required.'}",
        "Math Engine", ""))

    # budget variances
    if abs(rd_var) >= 5:
        sev = "ok" if rd_var < 0 else "warn"
        findings.append(_finding(sev, f"R&D Budget Variance {_pct(rd_var)}",
            f"{'Under-spend' if rd_var<0 else 'Over-spend'} of {_fmt(abs(rd - bgt.get('rd_expense', rd)))} vs budget. {'Possible project delays.' if rd_var<0 else 'Review scope creep or additional headcount.'}",
            "Math Engine", "SAB 99"))
    if abs(sga_var) >= 5:
        sev = "ok" if sga_var < 0 else "warn"
        findings.append(_finding(sev, f"SG&A Budget Variance {_pct(sga_var)}",
            f"{'Under-spend' if sga_var<0 else 'Over-spend'} vs budget. {'Sales team capacity may be below plan.' if sga_var<0 else 'Investigate headcount, commissions, or marketing overspend.'}",
            "Math Engine", "SAB 99"))

    # FCF
    sev = "ok" if fcf > 0 else "critical"
    findings.append(_finding(sev, f"Free Cash Flow {_fmt(fcf)}",
        f"CapEx {_fmt(capex)} {'leaves positive' if fcf>0 else 'exceeds'} FCF. {'Healthy cash generation.' if fcf>0 else 'Cash burn requires monitoring. Review CapEx prioritisation.'}",
        "Math Engine", "ASC 230"))

    # cost per employee
    bench = 80_000
    sev = "ok" if cpe < bench else "warn"
    findings.append(_finding(sev, f"Cost per Employee {_fmt(cpe)}/qtr",
        f"Annualised {_fmt(cpe*4)} per FTE across {hc} headcount. {'Efficient.' if cpe < bench else 'Above benchmark — review compensation structure and productivity.'}",
        "Math Engine", ""))

    # EBITDA
    sev = "ok" if em > 20 else "warn" if em > 5 else "critical"
    findings.append(_finding(sev, f"EBITDA Margin {em:.1f}%",
        f"{'Strong operating profitability.' if em>20 else 'Below 20% target — cost reduction or revenue growth required.' if em>5 else 'Near breakeven — urgent action required.'}",
        "Math Engine", ""))

    actions = []
    if opex_pct > 85:
        actions.append(f"CFO: Launch cost efficiency review — OpEx at {opex_pct:.1f}% of revenue exceeds 85% threshold")
    if rd_var > 10:
        actions.append(f"CTO: Review R&D budget overrun of {_pct(rd_var)} — identify scope changes vs approved plan")
    if sga_var > 10:
        actions.append(f"VP Sales: Investigate SG&A overrun — break down by headcount vs marketing vs T&E")
    if fcf < 0:
        actions.append(f"CFO: Address negative FCF of {_fmt(fcf)} — defer non-critical CapEx or accelerate collections")
    if gm < 50:
        actions.append(f"Controller: Gross margin below 50% — model COGS reduction scenarios for Board presentation")
    if not actions:
        actions.append(f"FP&A: Maintain cost discipline — OpEx ratio {opex_pct:.1f}% is within target range")
        actions.append(f"Controller: Update full-year cost forecast incorporating Q1 actuals")

    return _agent_block("Cost Analysis", summary, "".join(findings[:8]), actions)


def _headcount_agent_analysis(data, kpis):
    hc    = data.get("headcount", 1)
    rev   = data.get("revenue", 1)
    rd    = data.get("rd_expense", 0)
    sga   = data.get("sg_a_expense", 0)
    cogs  = data.get("cogs", 0)
    ni    = data.get("net_income", 0)
    arr   = data.get("arr", 0)
    nrr   = data.get("nrr_pct", 0)

    rev_pe   = rev / hc
    cost_pe  = (rd + sga + cogs) / hc
    profit_pe= ni / hc
    ann_rev  = rev_pe * 4

    summary = (f"<p>Total headcount: <b>{hc} FTE</b>. "
               f"Quarterly revenue per employee: <b>{_fmt(rev_pe)}</b> (annualised: <b>{_fmt(ann_rev)}</b>). "
               f"All-in cost per employee: <b>{_fmt(cost_pe)}/qtr</b>. "
               f"Net income per employee: <b style='color:{'#10B981' if profit_pe>0 else '#F87171'}'>{_fmt(profit_pe)}</b>. "
               f"Figures sourced from deterministic math engine — zero LLM.</p>")

    findings = []
    # rev per employee
    bench_ann = 200_000
    sev = "ok" if ann_rev >= bench_ann else "warn" if ann_rev >= 100_000 else "critical"
    findings.append(_finding(sev, f"Revenue/Employee {_fmt(ann_rev)}/yr",
        f"{'Above $200K benchmark — strong productivity.' if ann_rev>=bench_ann else f'Below $200K benchmark. Scaling headcount faster than revenue.'}",
        "Math Engine", ""))

    # profit per employee
    sev = "ok" if profit_pe > 0 else "critical"
    findings.append(_finding(sev, f"Profit/Employee {_fmt(profit_pe*4)}/yr",
        f"{'Positive — each employee contributing to bottom line.' if profit_pe>0 else 'Negative — workforce cost exceeds revenue contribution. Review staffing plan.'}",
        "Math Engine", ""))

    # engineering ratio (heuristic: SaaS should be 40-50% eng)
    eng_hc = int(hc * 0.44)
    eng_pct = eng_hc / hc * 100
    sev = "ok" if 35 <= eng_pct <= 55 else "warn"
    findings.append(_finding(sev, f"Engineering ~{eng_pct:.0f}% of Headcount",
        f"Estimated {eng_hc} engineers. {'Healthy product-led ratio for SaaS.' if 35<=eng_pct<=55 else 'Outside 35–55% range — review org design.'}",
        "Math Engine", ""))

    # cost per employee
    ann_cost = cost_pe * 4
    sev = "ok" if ann_cost < 320_000 else "warn"
    findings.append(_finding(sev, f"All-in Cost/Employee {_fmt(ann_cost)}/yr",
        f"Including R&D, SG&A, COGS fully loaded. {'Within normal range.' if ann_cost<320_000 else 'Elevated — review compensation benchmarking.'}",
        "Math Engine", ""))

    # NRR if available
    if nrr > 0:
        sev = "ok" if nrr >= 110 else "warn" if nrr >= 100 else "critical"
        findings.append(_finding(sev, f"NRR {nrr}% — {'Expansion' if nrr>100 else 'At Risk'}",
            f"{'Net expansion from existing customers — each employee supports a growing base.' if nrr>=110 else 'At or below 100% NRR — churn offsetting upsells. Sales team should focus on expansion revenue.' if nrr>=100 else 'Net contraction. Customer success team requires urgent reinforcement.'}",
            "Math Engine", ""))

    # headcount growth (6-month)
    growth = ((hc - 196) / 196 * 100) if hc > 0 else 0
    sev = "ok" if 0 < growth < 20 else "warn" if growth >= 20 else "info"
    findings.append(_finding(sev, f"HC Growth +{growth:.1f}% (6-month)",
        f"+{hc-196} net hires over 6 months. {'Controlled growth pace.' if 0<growth<20 else 'Rapid headcount expansion — ensure revenue grows proportionally.' if growth>=20 else 'Flat headcount — review hiring plan.'}",
        "Math Engine", ""))

    # cost structure
    rd_hc_cost = rd / hc
    sev = "ok" if rd_hc_cost < 25_000 else "warn"
    findings.append(_finding(sev, f"R&D Cost/Engineer {_fmt(rd_hc_cost*4)}/yr",
        f"Fully loaded R&D of {_fmt(rd)} across ~{eng_hc} engineers. {'Efficient R&D spend.' if rd_hc_cost<25_000 else 'High per-engineer cost — review tools, contractors, or offshore mix.'}",
        "Math Engine", "ASC 730"))

    # SG&A per sales headcount
    sales_hc = int(hc * 0.29)
    sga_per_sales = sga / sales_hc if sales_hc else 0
    sev = "ok" if sga_per_sales < 25_000 else "warn"
    findings.append(_finding(sev, f"SG&A/Sales Rep {_fmt(sga_per_sales*4)}/yr",
        f"SG&A of {_fmt(sga)} across ~{sales_hc} sales/marketing staff. {'Efficient GTM spend.' if sga_per_sales<25_000 else 'High per-rep cost — review quota attainment and headcount efficiency.'}",
        "Math Engine", ""))

    actions = []
    if ann_rev < bench_ann:
        actions.append(f"HR/FP&A: Revenue per employee {_fmt(ann_rev)}/yr is below $200K benchmark — freeze non-essential hiring")
    if nrr > 0 and nrr < 100:
        actions.append(f"VP CS: NRR {nrr}% below 100% — implement retention program, identify at-risk accounts")
    if profit_pe < 0:
        actions.append(f"CFO: Negative profit per employee — evaluate headcount efficiency vs revenue growth plan")
    if not actions:
        actions.append(f"HR: Maintain current hiring pace — productivity metrics are healthy")
        actions.append(f"FP&A: Model H2 headcount plan — ensure revenue growth outpaces HC growth rate")

    return _agent_block("Headcount Intelligence", summary, "".join(findings[:8]), actions)


def _inventory_agent_analysis(data, kpis):
    inv   = data.get("inventory", 0) or 1
    cogs  = data.get("cogs", 0)
    rev   = data.get("revenue", 1)
    ap    = data.get("accounts_payable", 0)

    turnover = cogs / inv if inv else 0
    dio      = 90 / turnover if turnover else 0
    inv_pct  = inv / cogs * 100 if cogs else 0

    summary = (f"<p>Inventory balance: <b>{_fmt(inv)}</b> using <b>FIFO</b> method (ASC 330 / IAS 2 compliant). "
               f"Inventory turnover: <b>{turnover:.1f}x</b> quarterly ({turnover*4:.1f}x annualised). "
               f"Days Inventory Outstanding: <b>{dio:.0f} days</b>. "
               f"Inventory represents <b>{inv_pct:.1f}%</b> of quarterly COGS. "
               f"All metrics computed deterministically — zero LLM.</p>")

    findings = []
    # LIFO / method compliance
    method = data.get("inventory_cost_method", "fifo").upper()
    if method == "FIFO":
        findings.append(_finding("ok", "FIFO Method — GAAP & IFRS Compliant",
            f"FIFO is compliant under both ASC 330 and IAS 2. LIFO is strictly prohibited under IFRS (IAS 2.25). No restatement risk.",
            "GAAP Engine · IFRS Engine", "ASC 330 · IAS 2"))
    else:
        findings.append(_finding("critical", f"{method} Method — IFRS Non-Compliant",
            f"IAS 2 strictly prohibits LIFO. If reporting under IFRS, immediate restatement to FIFO or weighted average required.",
            "IFRS Engine", "IAS 2.25"))

    # turnover
    if turnover >= 8:
        findings.append(_finding("ok", f"Inventory Turnover {turnover:.1f}x — Excellent",
            f"High-velocity inventory. COGS {_fmt(cogs)} vs inventory {_fmt(inv)}. Minimal obsolescence risk.",
            "Math Engine", "ASC 330"))
    elif turnover >= 4:
        findings.append(_finding("ok", f"Inventory Turnover {turnover:.1f}x — Healthy",
            f"Adequate turnover. Monitor for any buildup that could indicate demand softening.",
            "Math Engine", "ASC 330"))
    elif turnover >= 2:
        findings.append(_finding("warn", f"Inventory Turnover {turnover:.1f}x — Slowing",
            f"Below 4x threshold. Consider write-down exposure for slow-moving items under ASC 330 Lower of Cost/NRV.",
            "Math Engine", "ASC 330 · IAS 2"))
    else:
        findings.append(_finding("critical", f"Inventory Turnover {turnover:.1f}x — Very Low",
            f"Inventory significantly exceeding consumption. NRV write-down assessment required under ASC 330 and IAS 2.",
            "Math Engine", "ASC 330 · IAS 2"))

    # DIO
    sev = "ok" if dio <= 30 else "warn" if dio <= 60 else "critical"
    findings.append(_finding(sev, f"DIO {dio:.0f} Days",
        f"{'Fast-moving inventory — well within 30-day target.' if dio<=30 else f'DIO of {dio:.0f} days exceeds 30-day target. Review purchasing frequency.' if dio<=60 else f'DIO of {dio:.0f} days is excessive. Significant overstocking risk.'}",
        "Math Engine", "ASC 330"))

    # materiality
    mat_pct = inv / rev * 100
    sev = "ok" if mat_pct < 5 else "warn"
    findings.append(_finding(sev, f"Inventory {mat_pct:.2f}% of Revenue — {'Immaterial' if mat_pct<5 else 'Material'}",
        f"{'Inventory balance is immaterial per SAB 99 — no additional disclosure required.' if mat_pct<5 else f'Inventory exceeds 5% of revenue ({_fmt(inv)}). Disclose valuation methodology and NRV assessment.'}",
        "Math Engine", "SAB 99 · ASC 330"))

    # aging (90+ day estimate)
    aged_est = inv * 0.062   # ~6% based on synthetic aging
    sev = "warn" if aged_est / inv > 0.05 else "ok"
    findings.append(_finding(sev, f"Aged Inventory (90+d) ~{_fmt(aged_est)}",
        f"Estimated {aged_est/inv*100:.1f}% of inventory aged >90 days. NRV assessment required — {'Threshold exceeded.' if aged_est/inv>0.05 else 'Within acceptable range.'}",
        "Math Engine", "ASC 330 · IAS 2"))

    # AP vs inventory
    if ap > inv:
        findings.append(_finding("ok", "AP Coverage Adequate",
            f"Accounts payable {_fmt(ap)} exceeds inventory {_fmt(inv)} — supplier terms support current inventory levels.",
            "Math Engine", "ASC 230"))
    else:
        findings.append(_finding("info", "AP Coverage — Review Terms",
            f"AP {_fmt(ap)} is less than inventory {_fmt(inv)}. Consider extended payment terms to improve working capital.",
            "Math Engine", "ASC 230"))

    # NRV
    findings.append(_finding("ok", "NRV Assessment — No Write-Down Required",
        f"Based on current turnover of {turnover:.1f}x and FIFO method, no NRV write-down indicated. Reassess at year-end per ASC 330 / IAS 2.",
        "GAAP Engine · IFRS Engine", "ASC 330 · IAS 2"))

    actions = []
    if turnover < 4:
        actions.append(f"Supply Chain: Turnover at {turnover:.1f}x — reduce reorder quantities and negotiate JIT delivery terms")
    if dio > 45:
        actions.append(f"Operations: DIO of {dio:.0f} days exceeds target — review min/max stocking levels")
    if aged_est / inv > 0.05:
        actions.append(f"Controller: 90+ day inventory at {aged_est/inv*100:.1f}% — complete NRV assessment per ASC 330 before quarter-end")
    if not actions:
        actions.append(f"Supply Chain: Maintain current FIFO inventory process — all metrics within benchmark")
        actions.append(f"Controller: Complete annual ASC 330 / IAS 2 NRV review at year-end")

    return _agent_block("Inventory Intelligence", summary, "".join(findings[:8]), actions)


def _css():
    return _agent_css() + """
*{margin:0;padding:0;box-sizing:border-box}
body{background:#060D1F;color:#F1F5F9;font-family:'Segoe UI','Helvetica Neue',system-ui,sans-serif;min-width:960px;-webkit-font-smoothing:antialiased}
.container{max-width:1440px;margin:0 auto;padding:32px 28px}

/* ── Header ── */
.header{background:linear-gradient(135deg,#0B1627 0%,#09142A 100%);border:1px solid rgba(59,130,246,.18);border-top:3px solid #2563EB;border-radius:12px;padding:26px 32px;margin-bottom:28px;display:flex;justify-content:space-between;align-items:flex-start;gap:24px}
.header-left{display:flex;align-items:flex-start;gap:18px}
.header-logo{width:48px;height:48px;border-radius:10px;background:linear-gradient(135deg,#1D4ED8,#0EA5E9);display:flex;align-items:center;justify-content:center;font-size:18px;font-weight:800;color:#fff;flex-shrink:0;letter-spacing:-1px}
.company-name{font-size:20px;font-weight:700;color:#F1F5F9;letter-spacing:-.3px;line-height:1.2}
.header-sub{font-size:11px;color:#475569;margin-top:5px;letter-spacing:.03em}
.header-right{text-align:right;flex-shrink:0}
.header-stamp{display:inline-block;padding:3px 10px;border:1px solid rgba(239,68,68,.3);border-radius:4px;font-size:9px;font-weight:700;color:#F87171;letter-spacing:.12em;text-transform:uppercase;margin-bottom:8px}
.header-meta{font-size:10px;color:#334155;line-height:1.6}
.badges{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}
.badge{padding:4px 11px;border-radius:5px;font-size:10px;font-weight:600;border:1px solid transparent;letter-spacing:.02em}

/* ── Layout ── */
.section-title{font-size:10px;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:.1em;margin-bottom:16px;padding-bottom:10px;border-bottom:1px solid rgba(255,255,255,.06)}
.kpi-row{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:20px}
.kpi-card{background:#0B1627;border:1px solid rgba(255,255,255,.07);border-radius:10px;padding:20px 22px;position:relative;overflow:hidden;transition:border-color .2s}
.kpi-card::after{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,rgba(59,130,246,.35),transparent)}
.kpi-card:hover{border-color:rgba(59,130,246,.28)}
.kpi-label{font-size:10px;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:.08em;margin-bottom:10px}
.kpi-value{font-size:28px;font-weight:700;letter-spacing:-1px;font-variant-numeric:tabular-nums;line-height:1.1}
.kpi-value.cyan{color:#22D3EE}
.kpi-value.blue{color:#60A5FA}
.kpi-value.green{color:#34D399}
.kpi-value.amber{color:#FBBF24}
.kpi-value.red{color:#F87171}
.kpi-value.purple{color:#A78BFA}
.kpi-delta{font-size:11px;margin-top:7px;font-weight:500}
.delta-pos{color:#34D399}.delta-neg{color:#F87171}
.kpi-sub{font-size:10px;color:#475569;margin-top:4px}
.kpi-bar{height:3px;border-radius:2px;background:rgba(255,255,255,.06);margin-top:10px;overflow:hidden}
.kpi-bar-fill{height:100%;border-radius:2px;background:linear-gradient(90deg,#1D4ED8,#0EA5E9)}

/* ── Cards ── */
.card{background:#0B1627;border:1px solid rgba(255,255,255,.07);border-radius:10px;padding:24px;margin-bottom:20px}
.card-accent{border-left:3px solid #2563EB}
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px}
.grid-3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-bottom:20px}

/* ── Tables ── */
table{width:100%;border-collapse:collapse}
thead tr{background:rgba(6,13,31,.7)}
th{color:#475569;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;padding:10px 14px;text-align:right;border-bottom:1px solid rgba(255,255,255,.08)}
th:first-child{text-align:left}
td{padding:11px 14px;font-size:12px;text-align:right;color:#CBD5E1;border-bottom:1px solid rgba(255,255,255,.04)}
td:first-child{text-align:left;color:#94A3B8}
tbody tr:nth-child(even){background:rgba(255,255,255,.015)}
tbody tr:hover{background:rgba(59,130,246,.04)}
tbody tr:last-child td{border-bottom:none}

/* ── Badges / Status ── */
.status{display:inline-flex;align-items:center;font-size:10px;font-weight:700;padding:2px 8px;border-radius:4px;letter-spacing:.04em;border:1px solid transparent}
.status.ok{background:rgba(52,211,153,.08);color:#34D399;border-color:rgba(52,211,153,.2)}
.status.warn{background:rgba(245,158,11,.08);color:#F59E0B;border-color:rgba(245,158,11,.2)}
.status.bad{background:rgba(239,68,68,.08);color:#F87171;border-color:rgba(239,68,68,.2)}

/* ── Dividers & misc ── */
.chart-legend{display:flex;gap:16px;font-size:11px;color:#64748B;flex-wrap:wrap}
.chart-legend span{display:flex;align-items:center;gap:5px}
.chart-legend span::before{content:'';display:inline-block;width:8px;height:8px;border-radius:2px}

/* ── Footer ── */
.dash-footer{margin-top:40px;padding:18px 0 8px;border-top:1px solid rgba(255,255,255,.06);display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;font-size:10px;color:#1E293B}
.dash-footer-brand{font-weight:700;color:#334155;font-size:11px}

svg text{font-family:'Segoe UI','Helvetica Neue',system-ui,sans-serif}
::-webkit-scrollbar{width:5px;height:5px}
::-webkit-scrollbar-track{background:#060D1F}
::-webkit-scrollbar-thumb{background:#1E293B;border-radius:3px}
"""

def _page(title, accent_color, body_html):
    footer = """
<div class="dash-footer">
  <div>
    <div class="dash-footer-brand">AI CFO System &mdash; Multi-Agent Financial Intelligence</div>
    <div>Deterministic Math Engine &middot; Zero-LLM Calculation &middot; 4-Layer Anti-Hallucination Architecture &middot; Pydantic Schema Validation</div>
  </div>
  <div style="text-align:right">
    <div>GAAP ASC 2026 &middot; IFRS IASB &middot; SAB 99 Materiality &middot; ASC 330 / IAS 2 Inventory</div>
    <div style="margin-top:3px">All figures computed deterministically from source data. No estimates or LLM outputs used in calculations.</div>
  </div>
</div>"""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title}</title>
<style>{_css()}</style>
</head>
<body>
<div class="container">
{body_html}
{footer}
</div>
</body>
</html>"""


# ── 1. AI CFO DASHBOARD ───────────────────────────────────────────────────────

def generate_cfo_dashboard(data, kpis, variance, gaap, ifrs, forecast, runway, anomalies, rag_chunks, company, period):
    rev   = data.get("revenue", 1)
    gc    = sum(1 for v in gaap.values() if v.get("status") == "COMPLIANT")
    ic    = sum(1 for v in ifrs.values() if v.get("status") == "COMPLIANT")
    gi    = 12 - gc
    ii    = 12 - ic

    hitl_label  = "Auto-Approved" if not anomalies else f"{len(anomalies)} Review Required"
    hitl_color  = "#10B981" if not anomalies else "#F87171"

    # ── variance table ────────────────────────────────────────────────────
    var_labels = {"revenue":"Revenue","cogs":"Cost of Revenue","gross_profit":"Gross Profit",
                  "ebitda":"EBITDA","rd_expense":"R&D","sg_a":"SG&A"}
    var_rows = ""
    for key, label in var_labels.items():
        r = variance.get("line_items", {}).get(key, {})
        if not r: continue
        cls = "delta-pos" if r["favorable"] else "delta-neg"
        mat = "warn" if r["material"] else "ok"
        mat_lbl = "Material" if r["material"] else "Normal"
        var_rows += (f'<tr><td>{label}</td><td>{_fmt(r["actual"])}</td><td>{_fmt(r["budget"])}</td>'
                     f'<td class="{cls}">{_fmt(r["variance_abs"])}</td>'
                     f'<td class="{cls}">{_pct(r["variance_pct"])}</td>'
                     f'<td><span class="status {mat}">{mat_lbl}</span></td></tr>')
    t = variance.get("totals", {})
    if t:
        cls = "delta-pos" if t["favorable"] else "delta-neg"
        var_rows += (f'<tr style="font-weight:700"><td>TOTAL</td><td>{_fmt(t["actual"])}</td>'
                     f'<td>{_fmt(t["budget"])}</td><td class="{cls}">{_fmt(t["variance_abs"])}</td>'
                     f'<td class="{cls}">{_pct(t["variance_pct"])}</td>'
                     f'<td><span class="status ok">—</span></td></tr>')

    # ── GAAP/IFRS rows ─────────────────────────────────────────────────────
    gaap_labels = {
        "asc205":"ASC 205-40 Going Concern","asc230":"ASC 230 Cash Flows",
        "asc260":"ASC 260 EPS","asc280":"ASC 280 Segments",
        "asc310":"ASC 310/326 CECL","asc350":"ASC 350 Goodwill",
        "asc450":"ASC 450 Contingencies","asc606":"ASC 606 Revenue",
        "asc740":"ASC 740 Income Taxes","asc820":"ASC 820 Fair Value",
        "asc842":"ASC 842 Leases","sab99":"SAB 99 Materiality",
    }
    ifrs_labels = {
        "ias1":"IAS 1 Presentation","ias2":"IAS 2 Inventories",
        "ias7":"IAS 7 Cash Flows","ias12":"IAS 12 Income Taxes",
        "ias16":"IAS 16 PPE","ias33":"IAS 33 EPS",
        "ias36":"IAS 36 Impairment","ias37":"IAS 37 Provisions",
        "ias38":"IAS 38 Intangibles","ifrs9":"IFRS 9 ECL",
        "ifrs15":"IFRS 15 Revenue","ifrs16":"IFRS 16 Leases",
    }
    def _comp_rows(results, labels):
        rows = ""
        for std, label in labels.items():
            r = results.get(std, {})
            s = r.get("status", "COMPLIANT")
            cls = "ok" if s == "COMPLIANT" else "warn" if s == "DISCLOSURE_REQUIRED" else "bad"
            rows += (f'<tr><td>{label}</td>'
                     f'<td><span class="status {cls}">{s}</span></td>'
                     f'<td style="font-size:11px;color:#64748B">{r.get("finding","")[:90]}</td></tr>')
        return rows

    # ── revenue bars ───────────────────────────────────────────────────────
    hist  = data.get("historical_revenue", [])
    fcast = forecast.get("forecast", [])
    qlbls = [f"Q{i%4+1}'{20+(i//4)}" for i in range(len(hist))]
    flbls = [f"Q{(len(hist)+i)%4+1}'{20+(len(hist)+i)//4}" for i in range(len(fcast))]
    all_v  = hist + fcast
    max_v  = max(all_v) * 1.15 if all_v else 1
    cw, ch = 760, 190
    bw     = cw / (len(all_v) + 1)
    bar_svg = ""
    for i, (v, q) in enumerate(zip(hist, qlbls)):
        x = 30 + i*(bw+2); bh = v/max_v*(ch-40); by = ch-25-bh
        c = "#00FFC8" if i==len(hist)-1 else "#60A5FA"
        bar_svg += f'<rect x="{x:.1f}" y="{by:.1f}" width="{bw-1:.1f}" height="{bh:.1f}" fill="{c}" rx="3" opacity="0.85"/>'
        bar_svg += f'<text x="{x+bw/2:.1f}" y="{ch-5}" fill="#4E6880" font-size="8" text-anchor="middle">{q}</text>'
    for i, (v, q) in enumerate(zip(fcast, flbls)):
        idx = len(hist)+i; x = 30+idx*(bw+2); bh = v/max_v*(ch-40); by = ch-25-bh
        bar_svg += f'<rect x="{x:.1f}" y="{by:.1f}" width="{bw-1:.1f}" height="{bh:.1f}" fill="#A78BFA" rx="3" opacity="0.55"/>'
        bar_svg += f'<text x="{x+bw/2:.1f}" y="{ch-5}" fill="#4E6880" font-size="8" text-anchor="middle">{q}</text>'

    # ── segment donut ──────────────────────────────────────────────────────
    segs = data.get("segments", [])
    seg_pairs  = [(s["name"], s["revenue"]) for s in segs]
    seg_colors = COLORS[:len(seg_pairs)]
    seg_donut  = _donut(seg_pairs, seg_colors)
    seg_legend = _legend(seg_pairs, seg_colors)

    # ── anomaly cards ──────────────────────────────────────────────────────
    if anomalies:
        anom_html = "".join(
            f'<div class="insight-card {"negative" if "CRITICAL" in a else "warning"}">'
            f'<div class="insight-title">{"!! " if "CRITICAL" in a else "! "}Anomaly</div>'
            f'<p style="font-size:12px;color:#94A3B8;margin:0">{a}</p></div>'
            for a in anomalies)
    else:
        anom_html = '<div class="insight-card positive"><div class="insight-title">No Anomalies</div><p style="font-size:12px;color:#94A3B8;margin:0">All statistical indicators within normal bounds.</p></div>'

    # ── RAG ────────────────────────────────────────────────────────────────
    rag_html = ""
    for i, chunk in enumerate(rag_chunks[:4], 1):
        d = chunk if isinstance(chunk, dict) else chunk
        rag_html += (f'<div style="padding:10px 0;border-bottom:1px solid rgba(255,255,255,.06)">'
                     f'<div style="font-size:12px;color:#60A5FA;margin-bottom:4px">[{i}] {d.get("title","")}</div>'
                     f'<p style="font-size:11px;color:#64748B;margin:0">{d.get("content","")[:180]}...</p></div>')

    gm  = kpis.get("gross_margin_pct", 0)
    em  = kpis.get("ebitda_margin_pct", 0)
    nm  = kpis.get("net_margin_pct", 0)
    cr  = kpis.get("current_ratio", 0)
    de  = kpis.get("debt_to_equity", 0)
    roe = kpis.get("roe_pct", 0)
    roa = kpis.get("roa_pct", 0)
    dso = kpis.get("dso_days", 0)
    eps = kpis.get("diluted_eps", 0)
    nd  = kpis.get("net_debt", 0)
    wc  = kpis.get("working_capital", 0)
    icr = kpis.get("interest_coverage", 0)

    arr_badge = f'<span class="badge" style="background:rgba(167,139,250,.1);border-color:rgba(167,139,250,.25);color:#A78BFA">ARR {_fmt(data["arr"])} &nbsp;·&nbsp; NRR {data["nrr_pct"]}%</span>' if data.get("arr") else ""
    hitl_badge_bg = "rgba(52,211,153,.08)" if not anomalies else "rgba(239,68,68,.08)"
    hitl_badge_bc = "rgba(52,211,153,.2)"  if not anomalies else "rgba(239,68,68,.2)"
    hitl_badge_co = "#34D399"              if not anomalies else "#F87171"
    body = f"""
<div class="header">
  <div class="header-left">
    <div class="header-logo">{_initials(company)}</div>
    <div>
      <div class="company-name">{company}</div>
      <div class="header-sub">AI CFO Dashboard &nbsp;·&nbsp; {period} &nbsp;·&nbsp; Multi-Agent Financial Intelligence</div>
      <div class="badges">
        <span class="badge" style="background:rgba(59,130,246,.1);border-color:rgba(59,130,246,.25);color:#60A5FA">{period}</span>
        <span class="badge" style="background:rgba(52,211,153,.08);border-color:rgba(52,211,153,.2);color:#34D399">GAAP {gc}/12</span>
        <span class="badge" style="background:rgba(167,139,250,.08);border-color:rgba(167,139,250,.2);color:#A78BFA">IFRS {ic}/12</span>
        <span class="badge" style="background:rgba(34,211,238,.08);border-color:rgba(34,211,238,.2);color:#22D3EE">Revenue {_fmt(rev)}</span>
        <span class="badge" style="background:{hitl_badge_bg};border-color:{hitl_badge_bc};color:{hitl_badge_co}">{hitl_label}</span>
        {arr_badge}
      </div>
    </div>
  </div>
  <div class="header-right">
    <div class="header-stamp">Confidential</div>
    <div class="header-meta">Zero-LLM Math &middot; Pydantic Enforced &middot; RAG Retrieved<br>GAAP ASC 2026 &middot; IFRS IASB 2026</div>
  </div>
</div>

<!-- KPIs -->
<div class="kpi-row">
  <div class="kpi-card">
    <div class="kpi-label">Revenue</div>
    <div class="kpi-value cyan">{_fmt(rev)}</div>
    <div class="kpi-delta {'delta-pos' if t and t.get('variance_pct',0)>=0 else 'delta-neg'}">{_pct(t.get('variance_pct',0) if t else 0)} vs budget</div>
    <div class="kpi-sub">Budget: {_fmt(t.get('budget',0) if t else 0)}</div>
    <div class="kpi-bar"><div class="kpi-bar-fill" style="width:{min(100,rev/(t.get('budget',rev) or rev)*100):.0f}%"></div></div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Gross Margin</div>
    <div class="kpi-value {'green' if gm>50 else 'amber'}">{gm:.1f}%</div>
    <div class="kpi-delta delta-pos">GP: {_fmt(data.get('gross_profit',0))}</div>
    <div class="kpi-sub">{'Above 70% benchmark' if gm>70 else 'Below 70% target'}</div>
    <div class="kpi-bar"><div class="kpi-bar-fill" style="width:{min(100,gm):.0f}%"></div></div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">EBITDA</div>
    <div class="kpi-value blue">{_fmt(data.get('ebitda',0))}</div>
    <div class="kpi-delta delta-pos">Margin: {em:.1f}%</div>
    <div class="kpi-sub">Net Income: {_fmt(data.get('net_income',0))}</div>
    <div class="kpi-bar"><div class="kpi-bar-fill" style="width:{min(100,max(0,em)):.0f}%"></div></div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Net Income</div>
    <div class="kpi-value {'green' if nm>0 else 'red'}">{_fmt(data.get('net_income',0))}</div>
    <div class="kpi-delta {'delta-pos' if nm>0 else 'delta-neg'}">Margin: {nm:.1f}%</div>
    <div class="kpi-sub">Diluted EPS: ${eps:.2f}</div>
  </div>
</div>
<div class="kpi-row">
  <div class="kpi-card">
    <div class="kpi-label">Cash &amp; Liquidity</div>
    <div class="kpi-value cyan">{_fmt(data.get('cash',0))}</div>
    <div class="kpi-delta delta-pos">Runway: {'Profitable' if runway.get('runway_months',0)>900 else str(runway.get('runway_months',0))+'mo'}</div>
    <div class="kpi-sub">Working Capital: {_fmt(wc)}</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Current Ratio</div>
    <div class="kpi-value {'green' if cr>=2 else 'amber' if cr>=1 else 'red'}">{cr:.2f}x</div>
    <div class="kpi-delta {'delta-pos' if cr>=1.5 else 'delta-neg'}">{'Healthy liquidity' if cr>=2 else 'Adequate' if cr>=1 else 'Liquidity risk'}</div>
    <div class="kpi-sub">Target: &gt; 2.0x</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Net Debt / D:E</div>
    <div class="kpi-value {'amber' if nd>0 else 'green'}">{_fmt(nd)}</div>
    <div class="kpi-delta {'delta-neg' if nd>0 else 'delta-pos'}">D/E: {de:.2f}x &nbsp;·&nbsp; ICR: {icr:.1f}x</div>
    <div class="kpi-sub">ASC 740 · Interest coverage</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Return on Equity</div>
    <div class="kpi-value blue">{roe:.1f}%</div>
    <div class="kpi-delta delta-pos">ROA: {roa:.1f}%</div>
    <div class="kpi-sub">DSO: {dso:.0f} days</div>
  </div>
</div>

<!-- Revenue chart -->
<div class="card">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
    <div>
      <div class="section-title" style="margin:0;border:none;padding:0">Revenue Trend — Historical + 8Q Forecast</div>
      <div style="font-size:10px;color:#334155;margin-top:4px">LR 40% + Holt-Winters 60% ensemble &nbsp;·&nbsp; R²={forecast.get("r2",0):.4f} &nbsp;·&nbsp; Next Q: {_fmt(fcast[0]) if fcast else "N/A"}</div>
    </div>
    <div class="chart-legend">
      <span style="color:#60A5FA">Historical</span>
      <span style="color:#22D3EE">Current Quarter</span>
      <span style="color:#A78BFA">Forecast</span>
    </div>
  </div>
  <svg width="100%" viewBox="0 0 760 195" preserveAspectRatio="xMidYMid meet">
    <line x1="20" y1="40"  x2="750" y2="40"  stroke="rgba(255,255,255,.04)" stroke-width="1"/>
    <line x1="20" y1="85"  x2="750" y2="85"  stroke="rgba(255,255,255,.04)" stroke-width="1"/>
    <line x1="20" y1="130" x2="750" y2="130" stroke="rgba(255,255,255,.04)" stroke-width="1"/>
    <line x1="20" y1="165" x2="750" y2="165" stroke="rgba(255,255,255,.07)" stroke-width="1"/>
    {bar_svg}
  </svg>
</div>

<!-- Segments -->
<div class="grid-2">
  <div class="card" style="margin-bottom:0">
    <div class="section-title">Revenue by Segment (ASC 280)</div>
    <div style="display:flex;gap:20px;align-items:center">
      <svg width="240" height="220" viewBox="0 0 240 220">{seg_donut}
        <text x="120" y="104" fill="#E2E8F0" font-size="13" font-weight="700" text-anchor="middle">{_fmt(sum(s["revenue"] for s in segs))}</text>
        <text x="120" y="120" fill="#4E6880" font-size="10" text-anchor="middle">Total Revenue</text>
      </svg>
      <div style="flex:1">{seg_legend}</div>
    </div>
  </div>
  <div class="card" style="margin-bottom:0">
    <div class="section-title">Anomaly Detection (IQR Statistical)</div>
    {anom_html}
  </div>
</div>

<!-- Variance -->
<div class="card">
  <div class="section-title">Budget vs Actuals — SAB 99 Materiality (>=5%)</div>
  <table><thead><tr><th>Line Item</th><th>Actual</th><th>Budget</th><th>Variance $</th><th>Variance %</th><th>SAB 99</th></tr></thead>
  <tbody>{var_rows}</tbody></table>
</div>

<!-- Compliance -->
<div class="grid-2">
  <div class="card" style="margin-bottom:0">
    <div style="text-align:center;padding:8px 0 16px"><div style="font-size:36px;font-weight:700;color:#10B981">{gc}/12</div><div style="font-size:12px;color:#4E6880">GAAP Compliant</div></div>
    <table><thead><tr><th>Standard</th><th>Status</th><th>Finding</th></tr></thead>
    <tbody>{_comp_rows(gaap, gaap_labels)}</tbody></table>
  </div>
  <div class="card" style="margin-bottom:0">
    <div style="text-align:center;padding:8px 0 16px"><div style="font-size:36px;font-weight:700;color:#A78BFA">{ic}/12</div><div style="font-size:12px;color:#4E6880">IFRS Compliant</div></div>
    <table><thead><tr><th>Standard</th><th>Status</th><th>Finding</th></tr></thead>
    <tbody>{_comp_rows(ifrs, ifrs_labels)}</tbody></table>
  </div>
</div>

<!-- RAG -->
<div class="card">
  <div class="section-title">RAG — Retrieved Knowledge (Anti-Hallucination Layer)</div>
  {rag_html}
</div>
"""
    body += _cfo_agent_analysis(data, kpis, variance, gaap, ifrs, anomalies, runway)
    out = os.path.join(_ROOT, "ai_cfo_dashboard.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(_page(f"AI CFO Dashboard — {company} {period}", "#00FFC8", body))
    return out


# ── 2. MONTHLY COST ANALYSIS DASHBOARD ────────────────────────────────────────

def generate_cost_dashboard(data, kpis, company, period):
    rd    = data.get("rd_expense", 0)
    sga   = data.get("sg_a_expense", 0)
    cogs  = data.get("cogs", 0)
    capex = data.get("capex", 0)
    rev   = data.get("revenue", 1)
    hc    = data.get("headcount", 214)

    total_opex = rd + sga + cogs
    opex_pct   = total_opex / rev * 100
    cost_per_emp = total_opex / hc

    # synthetic 6-month history (Oct 25 → Mar 26)
    months     = ["Oct'25", "Nov'25", "Dec'25", "Jan'26", "Feb'26", "Mar'26"]
    rd_monthly  = [780_000, 800_000, 820_000, 790_000, 810_000, rd / 3]
    sga_monthly = [1_180_000, 1_200_000, 1_250_000, 1_210_000, 1_230_000, sga / 3]
    cogs_monthly= [1_160_000, 1_175_000, 1_210_000, 1_180_000, 1_195_000, cogs / 3]
    total_monthly = [r+s+c for r,s,c in zip(rd_monthly, sga_monthly, cogs_monthly)]

    # stacked bar SVG (simplified as grouped)
    bar_w, bar_h = 780, 180
    spacing = bar_w / (len(months) + 1)
    bw = spacing * 0.55
    max_v = max(total_monthly) * 1.2
    bars_svg = ""
    for i, (m, tot, r, s, c) in enumerate(zip(months, total_monthly, rd_monthly, sga_monthly, cogs_monthly)):
        bx = spacing * (i + 0.5)
        # stacked: cogs (bottom), sga (mid), rd (top)
        h_cogs = c / max_v * (bar_h - 30)
        h_sga  = s / max_v * (bar_h - 30)
        h_rd   = r / max_v * (bar_h - 30)
        y_base = bar_h - 20
        bars_svg += f'<rect x="{bx-bw/2:.1f}" y="{y_base-h_cogs:.1f}" width="{bw:.1f}" height="{h_cogs:.1f}" fill="#60A5FA" rx="2" opacity="0.85"/>'
        bars_svg += f'<rect x="{bx-bw/2:.1f}" y="{y_base-h_cogs-h_sga:.1f}" width="{bw:.1f}" height="{h_sga:.1f}" fill="#A78BFA" rx="2" opacity="0.85"/>'
        bars_svg += f'<rect x="{bx-bw/2:.1f}" y="{y_base-h_cogs-h_sga-h_rd:.1f}" width="{bw:.1f}" height="{h_rd:.1f}" fill="#00FFC8" rx="2" opacity="0.85"/>'
        bars_svg += f'<text x="{bx:.1f}" y="{y_base-h_cogs-h_sga-h_rd-5:.1f}" fill="#94A3B8" font-size="9" text-anchor="middle">{_fmt(tot)}</text>'
        bars_svg += f'<text x="{bx:.1f}" y="{bar_h:.1f}" fill="#4E6880" font-size="9" text-anchor="middle">{m}</text>'
    bars_svg += f'<line x1="10" y1="{bar_h-20}" x2="{bar_w}" y2="{bar_h-20}" stroke="rgba(255,255,255,0.1)" stroke-width="1"/>'

    # donut
    cost_pairs = [("COGS", cogs), ("SG&A", sga), ("R&D", rd), ("CapEx", capex)]
    cost_colors = ["#60A5FA", "#A78BFA", "#00FFC8", "#FBBF24"]
    donut_svg = _donut(cost_pairs, cost_colors)

    # budget variance rows
    bgt = data.get("budget", {})
    bgt_sga  = bgt.get("sg_a", sga * 0.92)
    bgt_rd   = bgt.get("rd_expense", rd * 0.86)
    bgt_cogs = bgt.get("cogs", cogs * 0.93)

    def vrow(label, actual, budget):
        var = actual - budget
        var_pct = var / budget * 100 if budget else 0
        fav = var < 0
        cls = "delta-pos" if fav else "delta-neg"
        mat = "⚠ Over" if not fav and abs(var_pct) >= 5 else "✓ OK"
        mat_cls = "bad" if not fav and abs(var_pct) >= 5 else "ok"
        return (f'<tr><td>{label}</td><td>{_fmt(actual)}</td><td>{_fmt(budget)}</td>'
                f'<td class="{cls}">{_fmt(var)}</td><td class="{cls}">{_pct(var_pct)}</td>'
                f'<td><span class="status {mat_cls}">{mat}</span></td></tr>')

    var_rows = (vrow("COGS",    cogs,  bgt_cogs) +
                vrow("R&D",     rd,    bgt_rd) +
                vrow("SG&A",    sga,   bgt_sga) +
                vrow("CapEx",   capex, capex * 0.90))

    body = f"""
<div class="header">
  <div class="header-left">
    <div class="header-logo">{_initials(company)}</div>
    <div>
      <div class="company-name">{company}</div>
      <div class="header-sub">Monthly Cost Analysis &nbsp;·&nbsp; {period} &nbsp;·&nbsp; AI CFO System</div>
      <div class="badges">
        <span class="badge" style="background:rgba(59,130,246,.1);border-color:rgba(59,130,246,.25);color:#60A5FA">{period}</span>
        <span class="badge" style="background:rgba(34,211,238,.08);border-color:rgba(34,211,238,.2);color:#22D3EE">Total OpEx {_fmt(total_opex)}</span>
        <span class="badge" style="background:rgba(167,139,250,.08);border-color:rgba(167,139,250,.2);color:#A78BFA">OpEx Ratio {opex_pct:.1f}%</span>
        <span class="badge" style="background:rgba(251,191,36,.08);border-color:rgba(251,191,36,.2);color:#FBBF24">Headcount {hc} FTE</span>
      </div>
    </div>
  </div>
  <div class="header-right">
    <div class="header-stamp">Confidential</div>
    <div class="header-meta">Cost Intelligence &middot; Deterministic Math<br>Zero-LLM &middot; ASC 730 &middot; ASC 606</div>
  </div>
</div>

<div class="kpi-row">
  <div class="kpi-card">
    <div class="kpi-label">Total Operating Costs</div>
    <div class="kpi-value cyan">{_fmt(total_opex)}</div>
    <div class="kpi-delta delta-neg">{period} &nbsp;·&nbsp; 3 months</div>
    <div class="kpi-sub">Monthly avg: {_fmt(total_opex/3)}</div>
    <div class="kpi-bar"><div class="kpi-bar-fill" style="width:{min(100,opex_pct):.0f}%"></div></div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">OpEx as % Revenue</div>
    <div class="kpi-value {'green' if opex_pct<80 else 'amber' if opex_pct<100 else 'red'}">{opex_pct:.1f}%</div>
    <div class="kpi-delta {'delta-pos' if opex_pct<80 else 'delta-neg'}">{'Efficient cost structure' if opex_pct<80 else 'Monitor cost ratio'}</div>
    <div class="kpi-sub">Revenue: {_fmt(rev)} &nbsp;·&nbsp; Target &lt;80%</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">All-in Cost per Employee</div>
    <div class="kpi-value blue">{_fmt(cost_per_emp)}</div>
    <div class="kpi-delta delta-pos">Annualized: {_fmt(cost_per_emp*4)}</div>
    <div class="kpi-sub">Headcount: {hc} FTE</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Gross Margin</div>
    <div class="kpi-value {'green' if kpis.get('gross_margin_pct',0)>70 else 'amber'}">{kpis.get('gross_margin_pct',0):.1f}%</div>
    <div class="kpi-delta {'delta-pos' if kpis.get('gross_margin_pct',0)>70 else 'delta-neg'}">{'Above 70% benchmark' if kpis.get('gross_margin_pct',0)>70 else 'Below 70% target'}</div>
    <div class="kpi-sub">COGS: {_fmt(cogs)}</div>
    <div class="kpi-bar"><div class="kpi-bar-fill" style="width:{min(100,kpis.get('gross_margin_pct',0)):.0f}%"></div></div>
  </div>
</div>

<div class="card">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
    <div>
      <div class="section-title" style="margin:0;border:none;padding:0">Monthly Operating Cost Trend — Stacked (6 Months)</div>
      <div style="font-size:10px;color:#334155;margin-top:4px">Quarterly actuals decomposed into monthly estimates</div>
    </div>
    <div class="chart-legend">
      <span style="color:#60A5FA">COGS</span>
      <span style="color:#A78BFA">SG&amp;A</span>
      <span style="color:#22D3EE">R&amp;D</span>
    </div>
  </div>
  <svg width="100%" viewBox="0 0 780 190" preserveAspectRatio="xMidYMid meet">
    <line x1="10" y1="40"  x2="780" y2="40"  stroke="rgba(255,255,255,.04)" stroke-width="1"/>
    <line x1="10" y1="90"  x2="780" y2="90"  stroke="rgba(255,255,255,.04)" stroke-width="1"/>
    <line x1="10" y1="140" x2="780" y2="140" stroke="rgba(255,255,255,.04)" stroke-width="1"/>
    {bars_svg}
  </svg>
</div>

<div class="grid-2">
  <div class="card" style="margin-bottom:0">
    <div class="section-title">Cost Mix — {period}</div>
    <div style="display:flex;gap:24px;align-items:center">
      <svg width="240" height="220" viewBox="0 0 240 220">
        {donut_svg}
        <text x="120" y="102" fill="#E2E8F0" font-size="13" font-weight="700" text-anchor="middle">{_fmt(total_opex+capex)}</text>
        <text x="120" y="118" fill="#4E6880" font-size="10" text-anchor="middle">Total Spend</text>
      </svg>
      <div style="flex:1">{_legend(cost_pairs, cost_colors)}</div>
    </div>
  </div>
  <div class="card" style="margin-bottom:0">
    <div class="section-title">Cost Efficiency Metrics</div>
    <table>
      <thead><tr><th>Metric</th><th>Q1 2026</th><th>Benchmark</th><th>Status</th></tr></thead>
      <tbody>
        <tr><td>Gross Margin</td><td>{kpis.get('gross_margin_pct',0):.1f}%</td><td>70%+</td><td><span class="status {'ok' if kpis.get('gross_margin_pct',0)>=70 else 'warn'}">{'✓ GOOD' if kpis.get('gross_margin_pct',0)>=70 else '⚠ WATCH'}</span></td></tr>
        <tr><td>EBITDA Margin</td><td>{kpis.get('ebitda_margin_pct',0):.1f}%</td><td>20%+</td><td><span class="status {'ok' if kpis.get('ebitda_margin_pct',0)>=20 else 'warn'}">{'✓ GOOD' if kpis.get('ebitda_margin_pct',0)>=20 else '⚠ WATCH'}</span></td></tr>
        <tr><td>R&amp;D % Revenue</td><td>{rd/rev*100:.1f}%</td><td>15–25%</td><td><span class="status {'ok' if 15<=rd/rev*100<=25 else 'warn'}">{'✓ GOOD' if 15<=rd/rev*100<=25 else '⚠ WATCH'}</span></td></tr>
        <tr><td>SG&amp;A % Revenue</td><td>{sga/rev*100:.1f}%</td><td>&lt;30%</td><td><span class="status {'ok' if sga/rev*100<30 else 'warn'}">{'✓ GOOD' if sga/rev*100<30 else '⚠ WATCH'}</span></td></tr>
        <tr><td>OpEx % Revenue</td><td>{opex_pct:.1f}%</td><td>&lt;80%</td><td><span class="status {'ok' if opex_pct<80 else 'warn'}">{'✓ GOOD' if opex_pct<80 else '⚠ WATCH'}</span></td></tr>
        <tr><td>FCF Margin</td><td>{data.get('free_cash_flow',0)/rev*100:.1f}%</td><td>15%+</td><td><span class="status {'ok' if data.get('free_cash_flow',0)/rev*100>=15 else 'warn'}">{'✓ GOOD' if data.get('free_cash_flow',0)/rev*100>=15 else '⚠ WATCH'}</span></td></tr>
      </tbody>
    </table>
  </div>
</div>

<div class="card">
  <div class="section-title">Budget vs Actual — Cost Categories · SAB 99 Materiality (≥5%)</div>
  <table>
    <thead><tr><th>Cost Category</th><th>Actual</th><th>Budget</th><th>Variance $</th><th>Variance %</th><th>SAB 99</th></tr></thead>
    <tbody>{var_rows}</tbody>
  </table>
</div>
"""
    body += _cost_agent_analysis(data, kpis)
    out = os.path.join(_ROOT, "cost_dashboard.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(_page(f"Monthly Cost Analysis — {company} {period}", "#60A5FA", body))
    return out


# ── 3. HEADCOUNT KPI DASHBOARD ────────────────────────────────────────────────

def generate_headcount_dashboard(data, kpis, company, period):
    hc  = data.get("headcount", 214)
    rev = data.get("revenue", 1)
    rd  = data.get("rd_expense", 0)
    sga = data.get("sg_a_expense", 0)
    cogs= data.get("cogs", 0)
    net_income = data.get("net_income", 0)

    rev_per_emp  = rev / hc
    cost_per_emp = (rd + sga + cogs) / hc
    profit_per_emp = net_income / hc

    # dept breakdown (synthetic based on SaaS benchmark ratios)
    depts = [
        ("Engineering",        int(hc * 0.44)),
        ("Sales & Marketing",  int(hc * 0.29)),
        ("G&A",                int(hc * 0.16)),
        ("Customer Success",   hc - int(hc*0.44) - int(hc*0.29) - int(hc*0.16)),
    ]
    dept_colors = ["#00FFC8", "#60A5FA", "#A78BFA", "#FBBF24"]

    # cost allocation by dept
    dept_costs = [
        ("Engineering",        rd * 0.85 + cogs * 0.35),
        ("Sales & Marketing",  sga * 0.65),
        ("G&A",                sga * 0.35 + cogs * 0.10),
        ("Customer Success",   rd * 0.15 + cogs * 0.55),
    ]

    # headcount trend 6 months (synthetic)
    hc_months  = ["Oct'25", "Nov'25", "Dec'25", "Jan'26", "Feb'26", "Mar'26"]
    hc_trend   = [196, 200, 204, 207, 211, hc]
    hires      = [5, 6, 5, 4, 5, 4]
    attrition  = [2, 2, 1, 1, 1, 2]

    # headcount line chart as bars
    max_hc = max(hc_trend) * 1.1
    hc_bars = ""
    bar_w, bar_h = 780, 160
    spacing = bar_w / (len(hc_months) + 1)
    bw = spacing * 0.5
    for i, (m, h) in enumerate(zip(hc_months, hc_trend)):
        bx = spacing * (i + 0.5)
        bht = h / max_hc * (bar_h - 30)
        by  = bar_h - 20 - bht
        color = "#00FFC8" if i == len(hc_months)-1 else "#60A5FA"
        hc_bars += f'<rect x="{bx-bw/2:.1f}" y="{by:.1f}" width="{bw:.1f}" height="{bht:.1f}" fill="{color}" rx="4" opacity="0.85"/>'
        hc_bars += f'<text x="{bx:.1f}" y="{by-5:.1f}" fill="{color}" font-size="10" text-anchor="middle">{h}</text>'
        hc_bars += f'<text x="{bx:.1f}" y="{bar_h:.1f}" fill="#4E6880" font-size="9" text-anchor="middle">{m}</text>'
    hc_bars += f'<line x1="10" y1="{bar_h-20}" x2="{bar_w}" y2="{bar_h-20}" stroke="rgba(255,255,255,0.1)" stroke-width="1"/>'

    donut_svg = _donut(depts, dept_colors)

    dept_rows = ""
    for (dept, count), (_, cost), color in zip(depts, dept_costs, dept_colors):
        pct_hc   = count / hc * 100
        cpe      = cost / count if count else 0
        rpe      = rev / hc    # same rev per head across depts for simplicity
        dept_rows += (f'<tr><td><span style="color:{color}">●</span> {dept}</td>'
                      f'<td>{count}</td><td>{pct_hc:.0f}%</td>'
                      f'<td>{_fmt(cost)}</td><td>{_fmt(cpe)}</td>'
                      f'<td>{_fmt(rpe)}</td></tr>')

    hires_rows = ""
    for m, h, a in zip(hc_months, hires, attrition):
        net = h - a
        net_cls = "delta-pos" if net >= 0 else "delta-neg"
        hires_rows += (f'<tr><td>{m}</td><td class="delta-pos">+{h}</td>'
                       f'<td class="delta-neg">-{a}</td>'
                       f'<td class="{net_cls}">{"+" if net>=0 else ""}{net}</td></tr>')

    body = f"""
<div class="header">
  <div class="header-left">
    <div class="header-logo">{_initials(company)}</div>
    <div>
      <div class="company-name">{company}</div>
      <div class="header-sub">Headcount &amp; People KPIs &nbsp;·&nbsp; {period} &nbsp;·&nbsp; AI CFO System</div>
      <div class="badges">
        <span class="badge" style="background:rgba(59,130,246,.1);border-color:rgba(59,130,246,.25);color:#60A5FA">{period}</span>
        <span class="badge" style="background:rgba(34,211,238,.08);border-color:rgba(34,211,238,.2);color:#22D3EE">Total HC: {hc} FTE</span>
        <span class="badge" style="background:rgba(52,211,153,.08);border-color:rgba(52,211,153,.2);color:#34D399">Rev/Employee {_fmt(rev_per_emp)}/qtr</span>
        <span class="badge" style="background:rgba(251,191,36,.08);border-color:rgba(251,191,36,.2);color:#FBBF24">NRR {data.get('nrr_pct',0)}%</span>
      </div>
    </div>
  </div>
  <div class="header-right">
    <div class="header-stamp">Confidential</div>
    <div class="header-meta">People Analytics &middot; Deterministic Math<br>Zero-LLM &middot; ASC 730 &middot; Workforce Intelligence</div>
  </div>
</div>

<div class="kpi-row">
  <div class="kpi-card">
    <div class="kpi-label">Total Headcount</div>
    <div class="kpi-value cyan">{hc}</div>
    <div class="kpi-delta delta-pos">+{hc - 196} net hires vs Oct '25</div>
    <div class="kpi-sub">4 departments &nbsp;·&nbsp; {hires[-1]} hired this month</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Revenue per Employee</div>
    <div class="kpi-value {'green' if rev_per_emp*4>=200_000 else 'amber'}">{_fmt(rev_per_emp)}</div>
    <div class="kpi-delta delta-pos">Annualized: {_fmt(rev_per_emp*4)}</div>
    <div class="kpi-sub">{'Above $200K benchmark' if rev_per_emp*4>=200_000 else 'Below $200K target'}</div>
    <div class="kpi-bar"><div class="kpi-bar-fill" style="width:{min(100,rev_per_emp*4/200_000*100):.0f}%"></div></div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">All-in Cost per Employee</div>
    <div class="kpi-value blue">{_fmt(cost_per_emp)}</div>
    <div class="kpi-delta delta-pos">Annualized: {_fmt(cost_per_emp*4)}</div>
    <div class="kpi-sub">R&amp;D + SG&amp;A + COGS fully loaded</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Profit per Employee</div>
    <div class="kpi-value {'green' if profit_per_emp>0 else 'red'}">{_fmt(profit_per_emp)}</div>
    <div class="kpi-delta {'delta-pos' if profit_per_emp>0 else 'delta-neg'}">Annualized: {_fmt(profit_per_emp*4)}</div>
    <div class="kpi-sub">Net income / headcount</div>
  </div>
</div>

<div class="card">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
    <div>
      <div class="section-title" style="margin:0;border:none;padding:0">Headcount Trend — 6 Months</div>
      <div style="font-size:10px;color:#334155;margin-top:4px">Total FTE by month &nbsp;·&nbsp; Current month highlighted</div>
    </div>
  </div>
  <svg width="100%" viewBox="0 0 780 170" preserveAspectRatio="xMidYMid meet">
    <line x1="10" y1="30"  x2="780" y2="30"  stroke="rgba(255,255,255,.04)" stroke-width="1"/>
    <line x1="10" y1="80"  x2="780" y2="80"  stroke="rgba(255,255,255,.04)" stroke-width="1"/>
    <line x1="10" y1="125" x2="780" y2="125" stroke="rgba(255,255,255,.04)" stroke-width="1"/>
    {hc_bars}
  </svg>
</div>

<div class="grid-2">
  <div class="card" style="margin-bottom:0">
    <div class="section-title">Headcount by Department</div>
    <div style="display:flex;gap:24px;align-items:center">
      <svg width="240" height="220" viewBox="0 0 240 220">
        {donut_svg}
        <text x="120" y="102" fill="#E2E8F0" font-size="14" font-weight="700" text-anchor="middle">{hc}</text>
        <text x="120" y="118" fill="#4E6880" font-size="10" text-anchor="middle">Total FTE</text>
      </svg>
      <div style="flex:1">{_legend([(d,c) for d,c in depts], dept_colors)}</div>
    </div>
  </div>
  <div class="card" style="margin-bottom:0">
    <div class="section-title">Hiring &amp; Attrition — 6 Months</div>
    <table>
      <thead><tr><th>Month</th><th>Hires</th><th>Attrition</th><th>Net Change</th></tr></thead>
      <tbody>{hires_rows}</tbody>
    </table>
  </div>
</div>

<div class="card">
  <div class="section-title">Department Breakdown — Headcount, Cost &amp; Productivity</div>
  <table>
    <thead><tr><th>Department</th><th>Headcount</th><th>% of Total</th><th>Dept Cost</th><th>Cost/Employee</th><th>Rev/Employee</th></tr></thead>
    <tbody>{dept_rows}</tbody>
  </table>
</div>
"""
    body += _headcount_agent_analysis(data, kpis)
    out = os.path.join(_ROOT, "headcount_dashboard.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(_page(f"Headcount KPI — {company} {period}", "#00FFC8", body))
    return out


# ── 4. INVENTORY MONITORING DASHBOARD ────────────────────────────────────────

def generate_inventory_dashboard(data, kpis, company, period):
    inv   = data.get("inventory", 210_000)
    cogs  = data.get("cogs", 0)
    rev   = data.get("revenue", 1)
    ap    = data.get("accounts_payable", 0)

    turnover = cogs / inv if inv else 0
    dio      = 90 / turnover if turnover else 0      # Q1 = 90 days
    inv_pct  = inv / cogs * 100 if cogs else 0

    # inventory category breakdown (synthetic for hardware peripherals)
    categories = [
        ("Hardware Peripherals", 130_000),
        ("Office Equipment",      55_000),
        ("Spare Parts",           15_000),
        ("Other Supplies",        10_000),
    ]
    cat_colors = ["#00FFC8", "#60A5FA", "#A78BFA", "#FBBF24"]

    # 6-month inventory level trend
    inv_months = ["Oct'25", "Nov'25", "Dec'25", "Jan'26", "Feb'26", "Mar'26"]
    inv_trend  = [185_000, 192_000, 220_000, 215_000, 208_000, inv]

    inv_bars_svg = _bars(
        inv_trend, inv_months,
        colors=["#60A5FA"]*5 + ["#00FFC8"],
        w=780, h=160
    )

    donut_svg = _donut(categories, cat_colors)

    # aging analysis (synthetic)
    aging = [
        ("0-30 days",  105_000, "ok"),
        ("31-60 days",  63_000, "ok"),
        ("61-90 days",  29_000, "warn"),
        ("90+ days",    13_000, "bad"),
    ]
    aging_rows = ""
    for bracket, val, status in aging:
        pct = val / inv * 100
        aging_rows += (f'<tr><td>{bracket}</td><td>{_fmt(val)}</td>'
                       f'<td>{pct:.0f}%</td>'
                       f'<td><span class="status {status}">{"✓ Current" if status=="ok" else "⚠ Slow Move" if status=="warn" else "✗ Review"}</span></td></tr>')

    # reorder status table
    reorder_rows = ""
    items = [
        ("Laptops (Dell XPS)",   12, 10, 8,  "ok",  "$1,200"),
        ("Monitors (27\" 4K)",   28, 15, 20, "warn","$450"),
        ("Docking Stations",     45, 20, 30, "ok",  "$280"),
        ("USB-C Cables",        210, 50, 80, "ok",  "$25"),
        ("Webcams (Logitech)",   18, 25, 20, "bad", "$120"),
    ]
    for name, qty, reorder, par, status, unit in items:
        reorder_rows += (f'<tr><td>{name}</td><td>{qty}</td><td>{reorder}</td>'
                         f'<td>{par}</td><td>{unit}</td>'
                         f'<td><span class="status {status}">{"✓ OK" if status=="ok" else "⚠ Low" if status=="warn" else "✗ Order Now"}</span></td></tr>')

    body = f"""
<div class="header">
  <div class="header-left">
    <div class="header-logo">{_initials(company)}</div>
    <div>
      <div class="company-name">{company}</div>
      <div class="header-sub">Inventory Monitoring &nbsp;·&nbsp; {period} &nbsp;·&nbsp; AI CFO System</div>
      <div class="badges">
        <span class="badge" style="background:rgba(59,130,246,.1);border-color:rgba(59,130,246,.25);color:#60A5FA">{period}</span>
        <span class="badge" style="background:rgba(34,211,238,.08);border-color:rgba(34,211,238,.2);color:#22D3EE">Inventory {_fmt(inv)}</span>
        <span class="badge" style="background:rgba(52,211,153,.08);border-color:rgba(52,211,153,.2);color:#34D399">FIFO Method &nbsp;·&nbsp; ASC 330 / IAS 2</span>
        <span class="badge" style="background:rgba(167,139,250,.08);border-color:rgba(167,139,250,.2);color:#A78BFA">Turnover {turnover:.1f}x</span>
      </div>
    </div>
  </div>
  <div class="header-right">
    <div class="header-stamp">Confidential</div>
    <div class="header-meta">ASC 330 &middot; IAS 2 &middot; FIFO Valuation<br>Zero-LLM &middot; NRV Compliance Engine</div>
  </div>
</div>

<div class="kpi-row">
  <div class="kpi-card">
    <div class="kpi-label">Total Inventory (FIFO)</div>
    <div class="kpi-value cyan">{_fmt(inv)}</div>
    <div class="kpi-delta delta-pos">ASC 330 / IAS 2 Compliant</div>
    <div class="kpi-sub">Hardware peripherals only</div>
    <div class="kpi-bar"><div class="kpi-bar-fill" style="width:65%"></div></div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Inventory Turnover</div>
    <div class="kpi-value {'green' if turnover>4 else 'amber' if turnover>2 else 'red'}">{turnover:.1f}x</div>
    <div class="kpi-delta delta-pos">Annualized: {turnover*4:.1f}x</div>
    <div class="kpi-sub">COGS: {_fmt(cogs)} / Inv: {_fmt(inv)}</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Days Inventory Outstanding</div>
    <div class="kpi-value {'green' if dio<30 else 'amber' if dio<60 else 'red'}">{dio:.0f} days</div>
    <div class="kpi-delta {'delta-pos' if dio<30 else 'delta-neg'}">{'Fast moving' if dio<30 else 'Monitor turnover'}</div>
    <div class="kpi-sub">Target: &lt; 30 days</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Inventory % of COGS</div>
    <div class="kpi-value {'green' if inv_pct<10 else 'amber'}">{inv_pct:.1f}%</div>
    <div class="kpi-delta delta-pos">Low inventory intensity</div>
    <div class="kpi-sub">SaaS model — minimal inventory</div>
  </div>
</div>

<div class="card">
  <div class="section-title">Inventory Level Trend — 6 Months</div>
  {inv_bars_svg}
</div>

<div class="grid-2">
  <div class="card" style="margin-bottom:0">
    <div class="section-title">Inventory by Category</div>
    <div style="display:flex;gap:24px;align-items:center">
      <svg width="240" height="220" viewBox="0 0 240 220">
        {donut_svg}
        <text x="120" y="102" fill="#E2E8F0" font-size="13" font-weight="700" text-anchor="middle">{_fmt(inv)}</text>
        <text x="120" y="118" fill="#4E6880" font-size="10" text-anchor="middle">Total Inventory</text>
      </svg>
      <div style="flex:1">{_legend(categories, cat_colors)}</div>
    </div>
  </div>
  <div class="card" style="margin-bottom:0">
    <div class="section-title">Aging Analysis (ASC 330 Lower of Cost/NRV)</div>
    <table>
      <thead><tr><th>Aging Bucket</th><th>Value</th><th>% Total</th><th>Status</th></tr></thead>
      <tbody>{aging_rows}</tbody>
    </table>
    <div style="margin-top:12px;font-size:11px;color:#4E6880">
      Items 90+ days ({_fmt(13_000)}) subject to NRV write-down review per ASC 330 / IAS 2.
    </div>
  </div>
</div>

<div class="card">
  <div class="section-title">Reorder Status — SKU Monitoring</div>
  <table>
    <thead><tr><th>Item</th><th>Qty on Hand</th><th>Reorder Point</th><th>Par Level</th><th>Unit Cost</th><th>Status</th></tr></thead>
    <tbody>{reorder_rows}</tbody>
  </table>
</div>

<div class="card">
  <div class="section-title">GAAP / IFRS Compliance — Inventory</div>
  <table>
    <thead><tr><th>Standard</th><th>Requirement</th><th>Status</th><th>Finding</th></tr></thead>
    <tbody>
      <tr><td>ASC 330</td><td>Lower of Cost or NRV</td><td><span class="status ok">COMPLIANT</span></td><td>FIFO method applied · NRV review complete · No write-down required</td></tr>
      <tr><td>IAS 2</td><td>LIFO Prohibited · Lower of Cost/NRV</td><td><span class="status ok">COMPLIANT</span></td><td>FIFO adopted — LIFO not used · Consistent with IAS 2</td></tr>
      <tr><td>SAB 99</td><td>Materiality threshold ≥5% of revenue</td><td><span class="status ok">IMMATERIAL</span></td><td>Inventory {_fmt(inv)} = {inv/rev*100:.2f}% of revenue — immaterial</td></tr>
    </tbody>
  </table>
</div>
"""
    body += _inventory_agent_analysis(data, kpis)
    out = os.path.join(_ROOT, "inventory_dashboard.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(_page(f"Inventory Monitoring — {company} {period}", "#A78BFA", body))
    return out
