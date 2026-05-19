"""
Analysis Agent — Claude interprets math outputs + RAG context.
NEVER calculates. Only interprets, explains, and synthesizes.
"""
import os
import json
from datetime import datetime
from typing import Dict, Any

from .state import CFOAgentState
from ..schemas.analysis import AnalysisOutput
from ..rag.pipeline import format_rag_context, RAGChunk
from ..llm.adapter import get_adapter, trim_for_local

ANALYSIS_SYSTEM = """You are a senior CFO analyst with 20 years of Big-4 and Fortune 500
experience. You receive two inputs:

1. EXACT CALCULATED RESULTS from a deterministic math engine.
   These numbers are ground truth. Trust them completely.
   DO NOT re-calculate, approximate, or question these values.

2. RETRIEVED CONTEXT from the company's knowledge base (RAG).
   Cite the source of any claim that comes from RAG context.

YOUR ROLE: Interpret, explain, and synthesize — not calculate.

For every variance or KPI:
- Explain the "so what" (not just the number)
- Identify root cause (price vs volume vs mix vs timing)
- Assess if permanent or one-time
- Quantify full-year outlook impact
- Recommend specific action with owner and deadline

For GAAP/IFRS findings:
- Cite the specific ASC or IAS standard number
- Explain the disclosure or compliance requirement
- Note key differences between frameworks where material

Output MUST follow AnalysisOutput schema (enforced by Instructor):
- executive_summary: min 50 chars, must contain $ figures
- key_variance_drivers: list[str], max 10
- identified_risks: list[str], min 1
- opportunities: list[str]
- action_items: list[str], max 5 (each must name an owner)
- confidence_score: float 0.0–1.0"""


def _format_gaap_summary(gaap_results: Dict) -> str:
    lines = []
    for std, r in gaap_results.items():
        status = r.get("status", "UNKNOWN")
        icon = "✓" if status == "COMPLIANT" else ("⚠" if status == "DISCLOSURE_REQUIRED" else "✗")
        lines.append(f"  {icon} {r.get('standard', std)}: {status} — {r.get('finding', '')[:100]}")
    return "\n".join(lines)


def _format_ifrs_summary(ifrs_results: Dict) -> str:
    lines = []
    for std, r in ifrs_results.items():
        status = r.get("status", "UNKNOWN")
        icon = "✓" if status == "COMPLIANT" else ("⚠" if status == "DISCLOSURE_REQUIRED" else "✗")
        lines.append(f"  {icon} {r.get('standard', std)}: {status} — {r.get('finding', '')[:100]}")
    return "\n".join(lines)


def _build_analysis_prompt(state: CFOAgentState) -> str:
    kpis     = state.get("kpi_metrics") or {}
    variance = state.get("variance_table") or {}
    gaap     = state.get("gaap_results") or {}
    ifrs     = state.get("ifrs_results") or {}
    anomalies = state.get("anomaly_flags") or []
    forecast  = state.get("forecast_outputs") or {}
    runway    = {}

    data = state.get("validated_data") or {}
    revenue  = data.get("revenue", 0)
    budget   = (variance.get("totals") or {}).get("budget", 0)
    var_pct  = (variance.get("totals") or {}).get("variance_pct", 0)

    rag_chunks_raw = state.get("rag_chunks") or []
    rag_chunks = [RAGChunk(**c) if isinstance(c, dict) else c for c in rag_chunks_raw]
    rag_context = format_rag_context(rag_chunks)

    material_vars = []
    for item, vals in (variance.get("line_items") or {}).items():
        if vals.get("material"):
            material_vars.append(
                f"  • {item}: actual ${vals['actual']:,.0f} vs budget ${vals['budget']:,.0f} "
                f"({vals['variance_pct']:+.1f}%) {'✓ FAV' if vals['favorable'] else '✗ UNF'}"
            )

    gaap_summary = _format_gaap_summary(gaap) if gaap else "  Not yet assessed"
    ifrs_summary = _format_ifrs_summary(ifrs) if ifrs else "  Not yet assessed"

    return f"""Analyze for {state.get('company_name', 'Company')} — {state.get('period', 'Period')}:

═══ MATH ENGINE OUTPUT (exact, deterministic) ═══
Revenue: ${revenue:,.0f} vs budget ${budget:,.0f} ({var_pct:+.1f}%)
Gross Margin: {kpis.get('gross_margin_pct', 0):.1f}% | EBITDA Margin: {kpis.get('ebitda_margin_pct', 0):.1f}%
Net Margin: {kpis.get('net_margin_pct', 0):.1f}% | Current Ratio: {kpis.get('current_ratio', 0):.2f}
Basic EPS: ${kpis.get('basic_eps', 0):.2f} | Diluted EPS: ${kpis.get('diluted_eps', 0):.2f}
Effective Tax Rate: {kpis.get('effective_tax_rate', 0):.1f}%
DSO: {kpis.get('dso_days', 0):.0f} days | CCC: {kpis.get('ccc_days', 0):.0f} days
Net Debt: ${kpis.get('net_debt', 0):,.0f} | D/E: {kpis.get('debt_to_equity', 0):.2f}x
Forecast R²: {forecast.get('r2', 'N/A')} | Anomaly flags: {len(anomalies)}

Material Variances:
{chr(10).join(material_vars) if material_vars else '  None — all variances within 5% SAB 99 threshold'}

Anomaly Flags:
{chr(10).join(f'  • {a}' for a in anomalies) if anomalies else '  None detected'}

US GAAP Status:
{gaap_summary}

IFRS Status:
{ifrs_summary}

═══ RAG CONTEXT (retrieved knowledge base) ═══
{rag_context}

Task: {state.get('task_description', 'Financial analysis')} in {state.get('report_format', 'board')} format.

Provide structured analysis. Reference specific ASC/IAS codes.
Cite which RAG sources informed each finding.
Every action item must include an owner and deadline."""


def _parse_raw_analysis(text: str) -> Dict:
    """Best-effort structured parse of a raw LLM text response."""
    import re
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]

    def extract_list(keyword: str) -> list:
        result, capture = [], False
        for line in lines:
            low = line.lower()
            if keyword in low:
                capture = True
                continue
            if capture:
                if line.startswith(("-", "*", "•", "1", "2", "3", "4", "5")):
                    result.append(re.sub(r"^[-*•\d.]+\s*", "", line))
                elif any(k in low for k in ("risk", "action", "opportunity", "driver", "summary", "finding")):
                    break
        return result or []

    summary_lines = []
    for line in lines[:8]:
        if re.search(r"\$[\d,]+|[\d.]+%|\d+[MKB]", line):
            summary_lines.append(line)
    summary = " ".join(summary_lines) or lines[0] if lines else text[:300]

    return {
        "executive_summary":    summary[:600],
        "key_variance_drivers": extract_list("variance") or extract_list("driver"),
        "identified_risks":     extract_list("risk"),
        "opportunities":        extract_list("opportunit"),
        "action_items":         extract_list("action"),
        "confidence_score":     0.6,
        "rag_sources_cited":    [],
        "gaap_citations":       [],
        "ifrs_citations":       [],
        "_raw_text":            text,
    }


def analysis_agent_node(
    state: CFOAgentState,
    backend: str | None = None,
    model: str | None = None,
) -> CFOAgentState:
    """LangGraph node — LLM interprets math + RAG. NEVER calculates.
    Works with Anthropic (ANTHROPIC_API_KEY) or Ollama (no key needed).
    """
    errors  = list(state.get("errors", []))
    audit   = list(state.get("audit_log", []))

    adapter    = get_adapter(backend=backend, model=model)
    is_ollama  = adapter.active_backend == "ollama"
    # Shorter output + trimmed prompt for local models to stay within ~5 min
    max_tok    = 800 if is_ollama else 2000
    prompt_raw = _build_analysis_prompt(state)
    prompt     = trim_for_local(prompt_raw, max_chars=3000) if is_ollama else prompt_raw

    keys = [
        "executive_summary", "key_variance_drivers", "identified_risks",
        "opportunities", "action_items", "confidence_score",
        "rag_sources_cited", "gaap_citations", "ifrs_citations",
    ]

    result = None

    if is_ollama:
        # Ollama: skip JSON mode — it causes slow, unreliable output.
        # Use raw text completion; parse what we can from the response.
        try:
            text = adapter.complete(ANALYSIS_SYSTEM, prompt, max_tokens=max_tok)
            result = _parse_raw_analysis(text)
        except Exception as e:
            errors.append(f"analysis_agent ollama: {e}")
    else:
        # Anthropic path: try Instructor → JSON → raw fallback
        try:
            import instructor, anthropic as _ant
            client = instructor.from_anthropic(_ant.Anthropic())
            out = client.messages.create(
                model=adapter.active_model,
                max_tokens=max_tok,
                response_model=AnalysisOutput,
                system=ANALYSIS_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
            )
            result = out.model_dump()
        except Exception as e:
            errors.append(f"analysis_agent instructor: {e}")

        if result is None:
            try:
                raw = adapter.complete_json(ANALYSIS_SYSTEM, prompt, keys=keys, max_tokens=max_tok)
                result = raw
            except Exception as e:
                errors.append(f"analysis_agent json: {e}")

        if result is None:
            try:
                text = adapter.complete(ANALYSIS_SYSTEM, prompt, max_tokens=max_tok)
                result = _parse_raw_analysis(text)
            except Exception as e:
                errors.append(f"analysis_agent fallback: {e}")

    if result is None:
        return {
            **state,
            "errors": errors,
            "agent_statuses": {**state.get("agent_statuses", {}), "analysis_agent": "error"},
        }

    audit.append({
        "timestamp": datetime.utcnow().isoformat(),
        "agent": "analysis_agent",
        "action": "analysis_complete",
        "backend": adapter.active_backend,
        "model": adapter.active_model,
        "confidence": result.get("confidence_score"),
    })

    return {
        **state,
        "analysis_narrative": result.get("executive_summary", ""),
        "identified_risks": result.get("identified_risks", []),
        "opportunities": result.get("opportunities", []),
        "action_items": result.get("action_items", []),
        "ai_confidence_score": result.get("confidence_score", 0.0),
        "structured_output": result,
        "agent_statuses": {**state.get("agent_statuses", {}), "analysis_agent": "complete"},
        "audit_log": audit,
        "errors": errors,
    }


