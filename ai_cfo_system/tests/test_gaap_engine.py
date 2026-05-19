"""Tests for the GAAP compliance engine (12 ASC standards)."""
import pytest
import sys
sys.path.insert(0, ".")

from backend.compliance.gaap_engine import GAAPEngine


@pytest.fixture
def gaap():
    return GAAPEngine()


@pytest.fixture
def healthy_data():
    return {
        "revenue": 12_500_000,
        "cogs": 5_225_000,
        "net_income": 1_890_000,
        "total_assets": 45_000_000,
        "cash": 6_200_000,
        "goodwill": 5_000_000,
        "goodwill_impairment_test_date": "2025-01-15",
        "rou_assets": 2_400_000,
        "lease_liability": 2_200_000,
        "accounts_receivable": 4_200_000,
        "allowance_for_credit_losses": 210_000,
        "revenue_recognition_policy": "5-step model per ASC 606",
        "deferred_revenue": 800_000,
        "interest_cash_flow_classification": "operating",
        "shares_outstanding": 4_500_000,
        "diluted_shares": 4_750_000,
    }


def healthy_kpis():
    return {
        "gross_margin_pct": 58.2,
        "current_ratio": 2.12,
        "basic_eps": 0.42,
        "diluted_eps": 0.40,
        "effective_tax_rate": 21.0,
        "dso_days": 49.0,
    }


def healthy_variance():
    return {"totals": {"variance_pct": 3.0}, "line_items": {}, "material_items": []}


def healthy_runway():
    return {"runway_months": 36.0, "status": "ADEQUATE"}


class TestASC20540GoingConcern:
    def test_adequate_runway_compliant(self, gaap, healthy_data):
        result = gaap.going_concern(healthy_data, healthy_kpis(), healthy_runway())
        assert result["status"] == "COMPLIANT"

    def test_short_runway_disclosure_required(self, gaap, healthy_data):
        runway = {"runway_months": 8.0}
        result = gaap.going_concern(healthy_data, {"current_ratio": 1.5, "net_income": 100}, runway)
        assert result["status"] in ("NON_COMPLIANT", "DISCLOSURE_REQUIRED")

    def test_negative_net_income_flagged(self, gaap, healthy_data):
        data = {**healthy_data, "net_income": -500_000}
        result = gaap.going_concern(data, healthy_kpis(), {"runway_months": 9})
        assert len(result["issues"]) > 0


class TestASC230CashFlows:
    def test_interest_as_operating_compliant(self, gaap, healthy_data):
        result = gaap.cash_flows(healthy_data)
        assert result["status"] == "COMPLIANT"

    def test_interest_as_financing_non_compliant(self, gaap, healthy_data):
        data = {**healthy_data, "interest_cash_flow_classification": "financing"}
        result = gaap.cash_flows(data)
        assert result["status"] == "NON_COMPLIANT"
        assert any("interest" in i.lower() for i in result["issues"])

    def test_key_rule_mentions_gaap_vs_ifrs_diff(self, gaap, healthy_data):
        result = gaap.cash_flows(healthy_data)
        assert "IFRS" in result.get("key_rule", "")


class TestASC350Goodwill:
    def test_impairment_reversal_non_compliant(self, gaap, healthy_data):
        data = {**healthy_data, "goodwill_impairment_reversal": 500_000}
        result = gaap.goodwill(data)
        assert result["status"] == "NON_COMPLIANT"
        assert any("reversal" in i.lower() for i in result["issues"])

    def test_missing_test_date_disclosure(self, gaap, healthy_data):
        data = {**healthy_data, "goodwill_impairment_test_date": None}
        result = gaap.goodwill(data)
        assert result["status"] in ("DISCLOSURE_REQUIRED", "NON_COMPLIANT")

    def test_no_goodwill_compliant(self, gaap):
        result = gaap.goodwill({"goodwill": 0})
        assert result["status"] == "COMPLIANT"


class TestASC606Revenue:
    def test_no_policy_disclosure_required(self, gaap):
        data = {"revenue": 5_000_000, "revenue_recognition_policy": ""}
        result = gaap.revenue_recognition(data)
        assert result["status"] == "DISCLOSURE_REQUIRED"

    def test_five_step_model_present(self, gaap, healthy_data):
        result = gaap.revenue_recognition(healthy_data)
        assert len(result["five_steps"]) == 5


class TestASC842Leases:
    def test_uncapitalized_operating_leases_non_compliant(self, gaap):
        data = {"operating_leases_not_capitalized": 500_000}
        result = gaap.leases(data)
        assert result["status"] == "NON_COMPLIANT"

    def test_rou_without_liability_disclosure(self, gaap):
        data = {"rou_assets": 2_000_000, "lease_liability": 0}
        result = gaap.leases(data)
        assert result["status"] in ("DISCLOSURE_REQUIRED", "NON_COMPLIANT")

    def test_dual_model_difference_mentioned(self, gaap, healthy_data):
        result = gaap.leases(healthy_data)
        assert "IFRS" in result.get("key_difference_from_ifrs", "")


class TestSAB99Materiality:
    def test_large_variance_disclosure(self, gaap, healthy_data):
        variance = {"totals": {"variance_pct": 12.0}, "line_items": {}, "material_items": ["revenue"]}
        result = gaap.materiality(healthy_data, variance)
        assert result["status"] == "DISCLOSURE_REQUIRED"

    def test_small_variance_compliant(self, gaap, healthy_data):
        variance = {"totals": {"variance_pct": 2.0}, "line_items": {}, "material_items": []}
        result = gaap.materiality(healthy_data, variance)
        assert result["status"] == "COMPLIANT"


class TestFullCheck:
    def test_all_12_standards_returned(self, gaap, healthy_data):
        results = gaap.check_all(healthy_data, healthy_kpis(), healthy_variance(), healthy_runway())
        expected_keys = ["asc205","asc230","asc260","asc280","asc310","asc350","asc450","asc606","asc740","asc820","asc842","sab99"]
        assert all(k in results for k in expected_keys)

    def test_all_have_status_field(self, gaap, healthy_data):
        results = gaap.check_all(healthy_data, healthy_kpis(), healthy_variance(), healthy_runway())
        for key, result in results.items():
            assert "status" in result, f"Missing status in {key}"
            assert result["status"] in ("COMPLIANT","DISCLOSURE_REQUIRED","NON_COMPLIANT"), f"Invalid status in {key}"
