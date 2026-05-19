"""
3-Round IFRS vs GAAP Agentic Debate.
Round 1: IFRS Advocate (IASB expert)
Round 2: GAAP Advocate (FASB/SEC expert)
Round 3: Independent Arbiter (Big-4 Chief Auditor)
"""
import os
import json
from datetime import datetime
from typing import Dict, Any

from .state import CFOAgentState
from ..llm.adapter import get_adapter, trim_for_local

IFRS_ADVOCATE_SYSTEM = """You are an IFRS advocate and Big-4 senior audit partner specializing
in IASB standards with 25 years of experience across EU, UK, and international listed companies.
Your role: ARGUE why this company SHOULD report under IFRS.

Structure your argument:
OPENING: Why IFRS suits this company's profile
COMPLIANCE: Current IFRS status by standard (cite IAS/IFRS numbers)
FAVORABLE TREATMENTS: Where IFRS benefits this company (IFRS 16 EBITDA uplift, IAS 38 dev cost)
CONCERNS: Honest assessment of disclosure gaps
VERDICT: Overall IFRS compliance assessment

Be specific to the company's actual data. Cite standard numbers for every finding."""

GAAP_ADVOCATE_SYSTEM = """You are a US GAAP expert and SEC-registered audit partner at a Big-4 firm
with 25 years of experience with NYSE/NASDAQ-listed companies and SEC filings.
Your role: ARGUE why this company SHOULD report under US GAAP.

Structure your argument:
OPENING: Why US GAAP is appropriate for this company
COMPLIANCE: Current GAAP status by standard (cite ASC codification references)
CONSERVATIVE PROTECTIONS: Where GAAP protects investors better
  (no impairment reversal, CECL lifetime losses, operating lease P&L visibility)
CONCERNS: Honest assessment of compliance gaps
VERDICT: Overall GAAP compliance assessment

Be specific to the company's actual data. Cite ASC numbers for every finding."""

ARBITER_SYSTEM = """You are an independent Chief Auditor who has served on both the IASB and FASB
advisory councils. You have NO bias toward either framework.
You have reviewed both advocates' arguments and the underlying data.

RENDER A DEFINITIVE VERDICT including:
1. MANDATORY FRAMEWORK: Which is legally required (jurisdiction + listing)
2. FINANCIAL IMPACT: Which framework produces more favorable/conservative results
3. TOP 5 RECONCILING ITEMS: Biggest GAAP↔IFRS differences, quantified where possible
4. KEY RISKS: What the company risks if non-compliant
5. RECOMMENDATION: Definitive guidance + priority compliance actions

Be decisive. Cite exact ASC and IAS/IFRS standard numbers. Reference specific company figures."""


def _build_advocate_prompt(state: CFOAgentState, framework: str) -> str:
    data   = state.get("validated_data") or {}
    kpis   = state.get("kpi_metrics") or {}
    gaap   = state.get("gaap_results") or {}
    ifrs   = state.get("ifrs_results") or {}

    revenue   = data.get("revenue", 0)
    gm_pct    = kpis.get("gross_margin_pct", 0)
    rou       = data.get("rou_assets", 0)
    goodwill  = data.get("goodwill", 0)
    rd_exp    = data.get("rd_expense", 0)
    op_lease  = data.get("operating_lease_expense", 0)

    jurisdiction = data.get("jurisdiction", "United States")
    listing      = data.get("listing_exchange", "NASDAQ")
    industry     = data.get("industry", "Technology")

    def fmt_results(results: Dict) -> str:
        lines = []
        for std, r in results.items():
            icon = "✓" if r["status"] == "COMPLIANT" else "⚠"
            lines.append(f"  {icon} {r.get('standard', std)}: {r['status']} — {r.get('finding', '')[:100]}")
        return "\n".join(lines) if lines else "  Not assessed"

    base = f"""Company: {state.get('company_name', 'Company')} | Period: {state.get('period', 'Period')}
Jurisdiction: {jurisdiction} | Listed: {listing} | Industry: {industry}
Revenue: ${revenue:,.0f} | Gross Margin: {gm_pct:.1f}% | ROU Assets: ${rou:,.0f}
Goodwill: ${goodwill:,.0f} | R&D: ${rd_exp:,.0f} | Operating Lease Expense: ${op_lease:,.0f}

Key IFRS vs GAAP differences for this company:
- IFRS 16 vs ASC 842: IFRS 16 single model → EBITDA higher by ~${op_lease:,.0f}
- IAS 38 vs ASC 730: R&D ${rd_exp:,.0f} — development phase capitalizable under IFRS
- IAS 37 vs ASC 450: Provisions at >50% vs ~75% — earlier recognition under IFRS
- IAS 36 vs ASC 350: Impairment reversal PERMITTED under IFRS; NOT under GAAP
- IAS 7 vs ASC 230: Interest paid — policy choice under IFRS; MUST be Operating under GAAP"""

    if framework == "ifrs":
        return base + f"\n\nIFRS compliance results:\n{fmt_results(ifrs)}"
    else:
        return base + f"\n\nGAAP compliance results:\n{fmt_results(gaap)}"


def _build_arbiter_prompt(state: CFOAgentState, ifrs_arg: str, gaap_arg: str) -> str:
    data  = state.get("validated_data") or {}
    kpis  = state.get("kpi_metrics") or {}
    goodwill  = data.get("goodwill", 0)
    rd_exp    = data.get("rd_expense", 0)
    op_lease  = data.get("operating_lease_expense", 0)
    dev_pct   = data.get("rd_dev_capitalizable_pct", 30)

    return f"""IFRS ADVOCATE'S ARGUMENT:
{ifrs_arg}

GAAP ADVOCATE'S ARGUMENT:
{gaap_arg}

COMPANY PROFILE:
{state.get('company_name', 'Company')} — {state.get('period', 'Period')}
Jurisdiction: {data.get('jurisdiction', 'United States')}
Exchange: {data.get('listing_exchange', 'NASDAQ')}

KEY QUANTIFIED FACTS:
- IFRS 16 EBITDA uplift: ~${op_lease:,.0f} (single vs dual model)
- IAS 38 dev costs: ${rd_exp:,.0f} in R&D — est. {dev_pct}% capitalizable
- Goodwill ${goodwill:,.0f}: annual impairment test both frameworks
- IAS 37 provisions recognized earlier (>50% vs ~75% threshold)

Render your definitive verdict."""


def debate_agent_node(
    state: CFOAgentState,
    backend: str | None = None,
    model:   str | None = None,
) -> CFOAgentState:
    """LangGraph node — 3-round IFRS vs GAAP debate.
    Works with Anthropic (ANTHROPIC_API_KEY) or Ollama (no key needed).
    """
    errors    = list(state.get("errors", []))
    audit     = list(state.get("audit_log", []))
    adapter   = get_adapter(backend=backend, model=model)
    is_ollama = adapter.active_backend == "ollama"
    # Local models: 500 tok/round keeps each under ~2 min; 3 rounds = ~6 min total
    adv_tok   = 500  if is_ollama else 1500
    arb_tok   = 600  if is_ollama else 2000
    trim      = lambda t: trim_for_local(t, max_chars=2000) if is_ollama else t

    # Round 1 — IFRS Advocate
    try:
        ifrs_argument = adapter.complete(
            IFRS_ADVOCATE_SYSTEM,
            trim(_build_advocate_prompt(state, "ifrs")),
            max_tokens=adv_tok,
        )
    except Exception as e:
        errors.append(f"debate round 1 (IFRS): {e}")
        ifrs_argument = f"Error: {e}"

    # Round 2 — GAAP Advocate
    try:
        gaap_argument = adapter.complete(
            GAAP_ADVOCATE_SYSTEM,
            trim(_build_advocate_prompt(state, "gaap")),
            max_tokens=adv_tok,
        )
    except Exception as e:
        errors.append(f"debate round 2 (GAAP): {e}")
        gaap_argument = f"Error: {e}"

    # Round 3 — Independent Arbiter
    try:
        arbiter_verdict = adapter.complete(
            ARBITER_SYSTEM,
            trim(_build_arbiter_prompt(state, ifrs_argument, gaap_argument)),
            max_tokens=arb_tok,
        )
    except Exception as e:
        errors.append(f"debate round 3 (arbiter): {e}")
        arbiter_verdict = f"Error: {e}"

    audit.append({
        "timestamp": datetime.utcnow().isoformat(),
        "agent": "debate_agent",
        "action": "3_round_debate_complete",
        "backend": adapter.active_backend,
        "model": adapter.active_model,
    })

    return {
        **state,
        "debate_ifrs_advocate": ifrs_argument,
        "debate_gaap_advocate": gaap_argument,
        "debate_arbiter": arbiter_verdict,
        "debate_complete": True,
        "agent_statuses": {**state.get("agent_statuses", {}), "debate_agent": "complete"},
        "audit_log": audit,
        "errors": errors,
    }
