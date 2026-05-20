"""
Reporting Agent — generates final board-ready report with ASC/IFRS citations.
Uses ONLY exact numbers from math engine. Never estimates.
"""
import os
from datetime import datetime
from typing import Dict

import anthropic

from .state import CFOAgentState

REPORT_SYSTEM = """You are a Chief Financial Officer generating a board-ready financial report.
Apply these rules without exception:

NUMBERS: Use ONLY the exact figures from the math engine output provided.
Never estimate, approximate, or recalculate any number.

STANDARDS: Cite specific ASC (GAAP) or IAS/IFRS standards for every financial
statement section. Example:
"Revenue of $X recognized per ASC 606 / IFRS 15 (5-step model)"
"Lease liability of $X recognized per ASC 842 / IFRS 16"

FORMAT: Board-appropriate language — authoritative, concise.
Every variance needs: Cause + FY outlook impact + Action + Owner + Deadline.

STRUCTURE:
1. EXECUTIVE SUMMARY (1 paragraph — lead with EPS and key metric)
2. REVENUE PERFORMANCE (cite ASC 606 / IFRS 15)
3. COST & MARGIN ANALYSIS (cite relevant standards)
4. US GAAP COMPLIANCE NOTES (cite all ASC standards with issues)
5. IFRS COMPLIANCE NOTES (cite IAS/IFRS standards, note key differences)
6. RISK ASSESSMENT (3-5 specific risks with quantification)
7. ACTION PLAN (3-5 items with owner, deadline, standard reference)"""


def _build_report_prompt(state: CFOAgentState) -> str:
    data     = state.get("validated_data") or {}
    kpis     = state.get("kpi_metrics") or {}
    variance = state.get("variance_table") or {}
    gaap     = state.get("gaap_results") or {}
    ifrs     = state.get("ifrs_results") or {}
    analysis = state.get("analysis_narrative") or ""
    forecast = state.get("forecast_outputs") or {}
    feedback = state.get("human_feedback") or "No CFO notes provided."
    sources  = ", ".join(state.get("rag_sources_cited") or []) or "Internal knowledge base"

    totals = variance.get("totals") or {}
    revenue = data.get("revenue", 0)
    budget  = totals.get("budget", 0)
    var_pct = totals.get("variance_pct", 0)

    def fmt_gaap(results: Dict) -> str:
        lines = []
        for std, r in results.items():
            icon = "✓" if r["status"] == "COMPLIANT" else ("⚠" if r["status"] == "DISCLOSURE_REQUIRED" else "✗")
            lines.append(f"  {icon} {r.get('standard', std)}: {r['status']} — {r.get('finding', '')[:120]}")
        return "\n".join(lines)

    return f"""Generate a {state.get('report_format', 'board')} report for {state.get('company_name', 'Company')} — {state.get('period', 'Period')}.

EXACT MATH ENGINE RESULTS:
Revenue: ${revenue:,.0f} vs Budget ${budget:,.0f} ({var_pct:+.1f}% variance)
Gross Margin: {kpis.get('gross_margin_pct', 0):.1f}% | EBITDA Margin: {kpis.get('ebitda_margin_pct', 0):.1f}% | Net Margin: {kpis.get('net_margin_pct', 0):.1f}%
Basic EPS: ${kpis.get('basic_eps', 0):.2f} | Diluted EPS: ${kpis.get('diluted_eps', 0):.2f}
Effective Tax Rate: {kpis.get('effective_tax_rate', 0):.1f}%
Current Ratio: {kpis.get('current_ratio', 0):.2f} | D/E: {kpis.get('debt_to_equity', 0):.2f}x
Net Debt: ${kpis.get('net_debt', 0):,.0f}
DSO: {kpis.get('dso_days', 0):.0f} days | CCC: {kpis.get('ccc_days', 0):.0f} days
ROU Assets: ${data.get('rou_assets', 0):,.0f} | Goodwill: ${data.get('goodwill', 0):,.0f}
Deferred Revenue: ${data.get('deferred_revenue', 0):,.0f}
Revenue Forecast R²: {forecast.get('r2', 'N/A')}

GAAP STATUS (12 ASC Standards):
{fmt_gaap(gaap)}

IFRS STATUS (12 IASB Standards):
{fmt_gaap(ifrs)}

AI ANALYSIS NARRATIVE:
{analysis}

CFO APPROVAL NOTES:
{feedback}

RAG SOURCES CITED: {sources}

Generate the complete {state.get('report_format', 'board')} report following the 7-section structure.
Cite ASC/IAS standard numbers for every financial treatment discussed.
Every action item must include: owner, deadline, and standard reference."""


def reporting_agent_node(state: CFOAgentState) -> CFOAgentState:
    """LangGraph node — generates final report using ONLY math engine numbers."""
    errors = list(state.get("errors", []))
    audit  = list(state.get("audit_log", []))

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        errors.append("reporting_agent: ANTHROPIC_API_KEY not set")
        return {**state, "errors": errors, "agent_statuses": {**state.get("agent_statuses", {}), "reporting_agent": "error"}}

    prompt = _build_report_prompt(state)

    try:
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4000,
            system=REPORT_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        report_text = msg.content[0].text
        tokens_used = msg.usage.input_tokens + msg.usage.output_tokens

        audit.append({
            "timestamp": datetime.utcnow().isoformat(),
            "agent": "reporting_agent",
            "action": "report_generated",
            "tokens": tokens_used,
            "report_length": len(report_text),
        })

        return {
            **state,
            "final_report": report_text,
            "total_tokens_used": state.get("total_tokens_used", 0) + tokens_used,
            "agent_statuses": {**state.get("agent_statuses", {}), "reporting_agent": "complete"},
            "audit_log": audit,
            "errors": errors,
        }

    except Exception as e:
        errors.append(f"reporting_agent failed: {e}")
        return {**state, "errors": errors, "agent_statuses": {**state.get("agent_statuses", {}), "reporting_agent": "error"}}
