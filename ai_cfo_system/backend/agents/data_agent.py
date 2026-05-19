"""
Data Agent — schema validation + Instructor-enforced extraction.
Uses Claude + Pydantic to extract structured financial data from raw input.
"""
import json
import os
from datetime import datetime
from typing import Any, Dict

import anthropic
try:
    import instructor
    INSTRUCTOR_AVAILABLE = True
except ImportError:
    INSTRUCTOR_AVAILABLE = False

from .state import CFOAgentState
from ..schemas.financial import FinancialDataSchema

DATA_EXTRACTION_SYSTEM = """You are a financial data extraction specialist. Extract structured
financial data from unstructured input and return ONLY valid JSON
matching the FinancialDataSchema exactly.

Required fields: company_name, period, currency, line_items[]
Optional: revenue, cogs, gross_profit, ebitda, net_income,
          total_assets, total_equity, current_assets, current_liabilities,
          cash, total_debt, accounts_receivable, inventory

Rules:
- All monetary values must be positive numbers (costs are positive; signs handled elsewhere)
- Period format: "Q1 2025", "FY 2024", "H1 2025", or "January 2025"
- Currency must be 3-letter ISO code: USD, EUR, GBP
- If a value cannot be determined, omit the field (do not guess)
- Return ONLY valid JSON, no explanation text"""


def data_agent_node(state: CFOAgentState) -> CFOAgentState:
    """LangGraph node — validates and extracts structured financial data."""
    errors  = list(state.get("errors", []))
    warnings = list(state.get("warnings", []))
    audit   = list(state.get("audit_log", []))

    raw = state.get("raw_financial_data")

    # If already a dict, try direct Pydantic validation
    if isinstance(raw, dict):
        try:
            schema = FinancialDataSchema(**raw)
            schema = schema.compute_derived()
            validated = schema.model_dump(exclude_none=True)

            audit.append({
                "timestamp": datetime.utcnow().isoformat(),
                "agent": "data_agent",
                "action": "direct_validation_success",
            })

            return {
                **state,
                "validated_data": validated,
                "schema_errors": [],
                "schema_version": "FinancialDataSchema_v1",
                "agent_statuses": {**state.get("agent_statuses", {}), "data_agent": "complete"},
                "audit_log": audit,
                "errors": errors,
                "warnings": warnings,
            }
        except Exception as ve:
            warnings.append(f"data_agent validation warning: {ve}")

    # Fall back to LLM extraction
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        errors.append("data_agent: ANTHROPIC_API_KEY not set — cannot extract unstructured data")
        return {
            **state,
            "errors": errors,
            "agent_statuses": {**state.get("agent_statuses", {}), "data_agent": "error"},
        }

    raw_str = json.dumps(raw) if isinstance(raw, dict) else str(raw)

    if INSTRUCTOR_AVAILABLE:
        validated = _extract_with_instructor(raw_str, errors, warnings)
    else:
        validated = _extract_with_raw_claude(raw_str, errors, warnings)

    if validated is None:
        return {
            **state,
            "errors": errors,
            "agent_statuses": {**state.get("agent_statuses", {}), "data_agent": "error"},
        }

    audit.append({
        "timestamp": datetime.utcnow().isoformat(),
        "agent": "data_agent",
        "action": "llm_extraction_success",
        "fields_extracted": len(validated),
    })

    return {
        **state,
        "validated_data": validated,
        "schema_errors": [],
        "schema_version": "FinancialDataSchema_v1",
        "agent_statuses": {**state.get("agent_statuses", {}), "data_agent": "complete"},
        "audit_log": audit,
        "errors": errors,
        "warnings": warnings,
    }


def _extract_with_instructor(raw_str: str, errors: list, warnings: list) -> Dict | None:
    try:
        client = instructor.from_anthropic(anthropic.Anthropic())
        result = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            response_model=FinancialDataSchema,
            system=DATA_EXTRACTION_SYSTEM,
            messages=[{"role": "user", "content": f"Extract financial data from:\n{raw_str}"}],
        )
        schema = result.compute_derived()
        return schema.model_dump(exclude_none=True)
    except Exception as e:
        errors.append(f"data_agent instructor extraction failed: {e}")
        return None


def _extract_with_raw_claude(raw_str: str, errors: list, warnings: list) -> Dict | None:
    try:
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            system=DATA_EXTRACTION_SYSTEM + "\nReturn ONLY the JSON object.",
            messages=[{"role": "user", "content": f"Extract financial data from:\n{raw_str}"}],
        )
        text = msg.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("```")[1].lstrip("json").strip()
        data = json.loads(text)
        schema = FinancialDataSchema(**data).compute_derived()
        return schema.model_dump(exclude_none=True)
    except Exception as e:
        errors.append(f"data_agent raw claude extraction failed: {e}")
        return None
