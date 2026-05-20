"""Integration tests for the agent pipeline (deterministic layers only)."""
import sys

import pytest

sys.path.insert(0, ".")

from backend.agents.gaap_agent import gaap_agent_node
from backend.agents.ifrs_agent import ifrs_agent_node
from backend.agents.math_engine import math_engine_node
from backend.agents.rag_agent import rag_agent_node
from backend.agents.supervisor import create_initial_state, route_from_supervisor

SAMPLE_FINANCIAL_DATA = {
    "revenue": 12_500_000,
    "cogs": 5_225_000,
    "gross_profit": 7_275_000,
    "ebitda": 2_800_000,
    "net_income": 1_890_000,
    "total_assets": 45_000_000,
    "total_equity": 28_000_000,
    "current_assets": 18_000_000,
    "current_liabilities": 8_500_000,
    "cash": 6_200_000,
    "total_debt": 12_000_000,
    "accounts_receivable": 4_200_000,
    "accounts_payable": 2_800_000,
    "inventory": 1_800_000,
    "shares_outstanding": 4_500_000,
    "diluted_shares": 4_750_000,
    "goodwill": 5_000_000,
    "goodwill_impairment_test_date": "2025-01-15",
    "rou_assets": 2_400_000,
    "lease_liability": 2_200_000,
    "operating_lease_expense": 180_000,
    "interest_cash_flow_classification": "operating",
    "revenue_recognition_policy": "ASC 606 5-step model",
    "inventory_cost_method": "fifo",
    "allowance_for_credit_losses": 210_000,
    "ecl_stage1_allowance": 100_000,
    "ecl_stage2_allowance": 50_000,
    "ecl_stage3_allowance": 20_000,
    "comparative_period_presented": True,
    "publicly_listed": True,
    "cash_flow_policy_consistent": True,
    "impairment_test_performed": True,
    "impairment_tested_at_cgu_level": True,
    "qualifying_development_projects": False,
    "actuals": {"revenue": 12_500_000, "cogs": 5_225_000, "ebitda": 2_800_000},
    "budget":  {"revenue": 11_000_000, "cogs": 5_000_000, "ebitda": 2_400_000},
    "historical_revenue": [9_800_000, 10_200_000, 10_800_000, 11_200_000, 11_800_000, 12_500_000],
}


@pytest.fixture
def initial_state():
    return create_initial_state(
        task_id="test-001",
        task_type="full_report",
        task_description="Q1 2025 board analysis",
        company_name="Acme Corp",
        period="Q1 2025",
        raw_financial_data=SAMPLE_FINANCIAL_DATA,
        submitted_by="test@company.com",
        report_format="board",
    )


class TestSupervisorRouting:
    def test_routes_to_data_agent_first(self, initial_state):
        route = route_from_supervisor(initial_state)
        assert route == "data_agent"

    def test_routes_to_math_after_data(self, initial_state):
        state = {
            **initial_state,
            "validated_data": SAMPLE_FINANCIAL_DATA,
            "agent_statuses": {"data_agent": "complete"},
        }
        route = route_from_supervisor(state)
        assert route == "math_engine"

    def test_routes_to_rag_after_math(self, initial_state):
        state = {
            **initial_state,
            "validated_data": SAMPLE_FINANCIAL_DATA,
            "kpi_metrics": {"gross_margin_pct": 58.2},
            "agent_statuses": {"data_agent": "complete", "math_engine": "complete"},
        }
        route = route_from_supervisor(state)
        assert route == "rag_agent"

    def test_ends_when_report_complete(self, initial_state):
        state = {
            **initial_state,
            "validated_data": SAMPLE_FINANCIAL_DATA,
            "kpi_metrics": {"gross_margin_pct": 58.2},
            "rag_chunks": [{"id": "kb001"}],
            "gaap_results": {"asc205": {"status": "COMPLIANT"}},
            "ifrs_results": {"ias1": {"status": "COMPLIANT"}},
            "analysis_narrative": "Strong Q1 performance…",
            "final_report": "Board Report: Q1 2025…",
            "requires_human_approval": False,
            "agent_statuses": {
                "data_agent": "complete", "math_engine": "complete",
                "rag_agent": "complete", "gaap_agent": "complete",
                "ifrs_agent": "complete", "analysis_agent": "complete",
                "reporting_agent": "complete",
            },
        }
        route = route_from_supervisor(state)
        assert route == "__end__"


class TestMathEngineNode:
    def test_node_populates_kpis(self, initial_state):
        state = {**initial_state, "validated_data": SAMPLE_FINANCIAL_DATA, "agent_statuses": {}}
        result = math_engine_node(state)
        assert result["kpi_metrics"] is not None
        assert "gross_margin_pct" in result["kpi_metrics"]

    def test_kpi_values_are_reasonable(self, initial_state):
        state = {**initial_state, "validated_data": SAMPLE_FINANCIAL_DATA, "agent_statuses": {}}
        result = math_engine_node(state)
        kpis = result["kpi_metrics"]
        assert 50 < kpis["gross_margin_pct"] < 70  # 58.2% expected
        assert kpis["current_ratio"] > 1.0

    def test_variance_table_populated(self, initial_state):
        state = {**initial_state, "validated_data": SAMPLE_FINANCIAL_DATA, "agent_statuses": {}}
        result = math_engine_node(state)
        assert result["variance_table"] is not None
        assert "totals" in result["variance_table"]

    def test_status_set_to_complete(self, initial_state):
        state = {**initial_state, "validated_data": SAMPLE_FINANCIAL_DATA, "agent_statuses": {}}
        result = math_engine_node(state)
        assert result["agent_statuses"]["math_engine"] == "complete"

    def test_no_errors_on_valid_data(self, initial_state):
        state = {**initial_state, "validated_data": SAMPLE_FINANCIAL_DATA, "agent_statuses": {}}
        result = math_engine_node(state)
        assert len(result["errors"]) == 0


class TestGAAPAgentNode:
    def test_returns_12_standards(self, initial_state):
        state_with_math = {
            **initial_state,
            "validated_data": SAMPLE_FINANCIAL_DATA,
            "kpi_metrics": {"gross_margin_pct": 58.2, "current_ratio": 2.12, "dso_days": 49, "basic_eps": 0.42, "diluted_eps": 0.40, "effective_tax_rate": 21.0},
            "variance_table": {"totals": {"variance_pct": 3.0}, "line_items": {}, "material_items": []},
            "agent_statuses": {},
        }
        result = gaap_agent_node(state_with_math)
        assert len(result["gaap_results"]) == 12
        assert result["agent_statuses"]["gaap_agent"] == "complete"

    def test_counts_are_non_negative(self, initial_state):
        state = {
            **initial_state,
            "validated_data": SAMPLE_FINANCIAL_DATA,
            "kpi_metrics": {"gross_margin_pct": 58.2, "current_ratio": 2.12, "dso_days": 49, "basic_eps": 0.42, "diluted_eps": 0.40, "effective_tax_rate": 21.0},
            "variance_table": {"totals": {"variance_pct": 3.0}, "line_items": {}, "material_items": []},
            "agent_statuses": {},
        }
        result = gaap_agent_node(state)
        assert result["gaap_compliant_count"] >= 0
        assert result["gaap_issues_count"] >= 0
        total = result["gaap_compliant_count"] + result["gaap_issues_count"]
        assert total == 12


class TestIFRSAgentNode:
    def test_returns_12_standards(self, initial_state):
        state = {
            **initial_state,
            "validated_data": SAMPLE_FINANCIAL_DATA,
            "kpi_metrics": {"gross_margin_pct": 58.2, "current_ratio": 2.12, "dso_days": 49, "basic_eps": 0.42, "diluted_eps": 0.40, "effective_tax_rate": 21.0},
            "variance_table": {"totals": {"variance_pct": 3.0}, "line_items": {}, "material_items": []},
            "agent_statuses": {},
        }
        result = ifrs_agent_node(state)
        assert len(result["ifrs_results"]) == 12
        assert result["agent_statuses"]["ifrs_agent"] == "complete"


class TestRAGAgentNode:
    def test_retrieves_chunks(self, initial_state):
        state = {
            **initial_state,
            "kpi_metrics": {"gross_margin_pct": 58.2},
            "anomaly_flags": [],
            "gaap_results": {},
            "ifrs_results": {},
            "agent_statuses": {},
        }
        result = rag_agent_node(state)
        assert result["rag_chunks"] is not None
        assert len(result["rag_chunks"]) > 0
        assert result["rag_query_used"] is not None
