"""Tests for the IFRS compliance engine (12 IASB standards)."""
import sys

import pytest

sys.path.insert(0, ".")

from backend.compliance.ifrs_engine import IFRSEngine


@pytest.fixture
def ifrs():
    return IFRSEngine()


@pytest.fixture
def healthy_data():
    return {
        "revenue": 12_500_000,
        "cogs": 5_225_000,
        "net_income": 1_890_000,
        "inventory": 1_800_000,
        "inventory_cost_method": "fifo",
        "net_realizable_value": 1_900_000,
        "goodwill": 5_000_000,
        "impairment_test_performed": True,
        "impairment_tested_at_cgu_level": True,
        "rou_assets": 2_400_000,
        "lease_liability": 2_200_000,
        "operating_lease_expense": 180_000,
        "interest_cash_flow_classification": "operating",
        "cash_flow_policy_consistent": True,
        "revenue_recognition_policy": "5-step model per IFRS 15",
        "deferred_revenue": 800_000,
        "accounts_receivable": 4_200_000,
        "ecl_stage1_allowance": 100_000,
        "ecl_stage2_allowance": 50_000,
        "ecl_stage3_allowance": 20_000,
        "comparative_period_presented": True,
        "shares_outstanding": 4_500_000,
        "diluted_shares": 4_750_000,
        "publicly_listed": True,
        "rd_expense": 1_300_000,
        "qualifying_development_projects": False,
    }


def healthy_kpis():
    return {
        "gross_margin_pct": 58.2,
        "current_ratio": 2.12,
        "basic_eps": 0.42,
        "diluted_eps": 0.40,
        "dso_days": 49.0,
        "effective_tax_rate": 21.0,
    }


def healthy_variance():
    return {"totals": {"variance_pct": 3.0}, "line_items": {}, "material_items": []}


def healthy_runway():
    return {"runway_months": 36.0}


class TestIAS2Inventories:
    def test_lifo_non_compliant(self, ifrs, healthy_data):
        data = {**healthy_data, "inventory_cost_method": "lifo"}
        result = ifrs.inventories(data)
        assert result["status"] == "NON_COMPLIANT"
        assert any("lifo" in i.lower() for i in result["issues"])

    def test_fifo_compliant(self, ifrs, healthy_data):
        result = ifrs.inventories(healthy_data)
        assert result["status"] == "COMPLIANT"

    def test_nrv_below_cost_requires_writedown(self, ifrs, healthy_data):
        data = {**healthy_data, "inventory": 2_000_000, "net_realizable_value": 1_700_000}
        result = ifrs.inventories(data)
        assert len(result["issues"]) > 0
        assert any("write" in i.lower() for i in result["issues"])

    def test_key_diff_mentions_gaap(self, ifrs, healthy_data):
        result = ifrs.inventories(healthy_data)
        assert "GAAP" in result.get("key_difference_from_gaap", "")


class TestIAS7CashFlows:
    def test_policy_choice_mentioned(self, ifrs, healthy_data):
        result = ifrs.cash_flows(healthy_data)
        assert "IFRS" in result.get("key_difference_from_gaap", "")

    def test_missing_policy_disclosure_required(self, ifrs):
        result = ifrs.cash_flows({"interest_cash_flow_classification": "", "cash_flow_policy_consistent": True})
        assert result["status"] == "DISCLOSURE_REQUIRED"


class TestIAS16PPE:
    def test_revaluation_model_requires_date(self, ifrs, healthy_data):
        data = {**healthy_data, "ppe_measurement_model": "revaluation", "last_revaluation_date": None}
        result = ifrs.ppe(data)
        assert result["status"] == "DISCLOSURE_REQUIRED"

    def test_cost_model_compliant(self, ifrs, healthy_data):
        data = {**healthy_data, "ppe_measurement_model": "cost", "depreciation_method": "straight-line", "ppe_net": 8_000_000}
        result = ifrs.ppe(data)
        assert result["status"] == "COMPLIANT"

    def test_key_diff_mentions_gaap_cost_only(self, ifrs, healthy_data):
        result = ifrs.ppe({**healthy_data, "ppe_net": 5_000_000})
        assert "GAAP" in result.get("key_difference_from_gaap", "")


class TestIAS38Intangibles:
    def test_dev_costs_not_capitalized_when_qualifying(self, ifrs, healthy_data):
        data = {**healthy_data, "qualifying_development_projects": True, "development_costs_capitalized": 0}
        result = ifrs.intangibles(data)
        assert result["status"] == "DISCLOSURE_REQUIRED"
        assert any("capitaliz" in i.lower() for i in result["issues"])

    def test_no_qualifying_projects_compliant(self, ifrs, healthy_data):
        result = ifrs.intangibles(healthy_data)
        assert result["status"] == "COMPLIANT"

    def test_key_diff_mentions_gaap(self, ifrs, healthy_data):
        result = ifrs.intangibles(healthy_data)
        assert "GAAP" in result.get("key_difference_from_gaap", "")


class TestIFRS9CreditLosses:
    def test_no_ecl_disclosure_required(self, ifrs):
        result = ifrs.credit_losses({"accounts_receivable": 4_200_000}, {"dso_days": 30})
        assert result["status"] == "DISCLOSURE_REQUIRED"

    def test_three_stage_model_compliant(self, ifrs, healthy_data):
        result = ifrs.credit_losses(healthy_data, healthy_kpis())
        assert result["status"] == "COMPLIANT"
        assert result["stages"]["stage1"] > 0


class TestIFRS16Leases:
    def test_uncapitalized_leases_non_compliant(self, ifrs):
        data = {"operating_leases_not_capitalized": 500_000}
        result = ifrs.leases(data, {})
        assert result["status"] == "NON_COMPLIANT"

    def test_ebitda_uplift_calculated(self, ifrs, healthy_data):
        result = ifrs.leases(healthy_data, healthy_kpis())
        assert result["ebitda_uplift_vs_gaap"] == 180_000

    def test_key_diff_mentions_single_model(self, ifrs, healthy_data):
        result = ifrs.leases(healthy_data, healthy_kpis())
        assert "SINGLE" in result.get("key_difference_from_gaap", "")


class TestFullCheck:
    def test_all_12_standards_returned(self, ifrs, healthy_data):
        results = ifrs.check_all(healthy_data, healthy_kpis(), healthy_variance(), healthy_runway())
        expected = ["ias1","ias2","ias7","ias12","ias16","ias33","ias36","ias37","ias38","ifrs9","ifrs15","ifrs16"]
        assert all(k in results for k in expected)

    def test_all_have_valid_status(self, ifrs, healthy_data):
        results = ifrs.check_all(healthy_data, healthy_kpis(), healthy_variance(), healthy_runway())
        valid = {"COMPLIANT","DISCLOSURE_REQUIRED","NON_COMPLIANT"}
        for key, result in results.items():
            assert result.get("status") in valid, f"Invalid status for {key}: {result.get('status')}"
