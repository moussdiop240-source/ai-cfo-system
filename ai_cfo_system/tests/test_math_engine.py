"""Tests for the deterministic math engine."""
import sys

import pytest

sys.path.insert(0, ".")

from backend.agents.math_engine import FinancialCalculationEngine


@pytest.fixture
def engine():
    return FinancialCalculationEngine()


@pytest.fixture
def sample_data():
    return {
        "revenue": 12_500_000,
        "cogs": 5_225_000,
        "gross_profit": 7_275_000,
        "ebitda": 2_800_000,
        "ebit": 2_460_000,
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
        "interest_expense": 420_000,
        "pre_tax_income": 2_040_000,
        "tax_provision": 150_000,
    }


class TestVarianceAnalysis:
    def test_basic_variance(self, engine):
        actuals = {"revenue": 12_500_000, "cogs": 5_225_000}
        budget  = {"revenue": 11_000_000, "cogs": 5_000_000}
        result = engine.calculate_variance_analysis(actuals, budget)

        assert result["line_items"]["revenue"]["variance_abs"] == 1_500_000
        assert result["line_items"]["revenue"]["variance_pct"] == pytest.approx(13.64, abs=0.01)
        assert result["line_items"]["revenue"]["material"] is True  # >5%
        assert result["line_items"]["revenue"]["favorable"] is True
        assert result["method"] == "pandas_exact_arithmetic"

    def test_negative_variance(self, engine):
        actuals = {"revenue": 9_000_000}
        budget  = {"revenue": 10_000_000}
        result = engine.calculate_variance_analysis(actuals, budget)

        assert result["line_items"]["revenue"]["variance_abs"] == -1_000_000
        assert result["line_items"]["revenue"]["favorable"] is False

    def test_immaterial_variance(self, engine):
        actuals = {"revenue": 10_200_000}
        budget  = {"revenue": 10_000_000}
        result = engine.calculate_variance_analysis(actuals, budget)
        assert result["line_items"]["revenue"]["variance_pct"] == 2.0
        assert result["line_items"]["revenue"]["material"] is False

    def test_totals_calculation(self, engine):
        actuals = {"revenue": 12_000_000, "cogs": 5_000_000}
        budget  = {"revenue": 11_000_000, "cogs": 4_800_000}
        result = engine.calculate_variance_analysis(actuals, budget)
        assert result["totals"]["actual"] == 17_000_000
        assert result["totals"]["budget"] == 15_800_000


class TestKPICalculation:
    def test_gross_margin(self, engine, sample_data):
        kpis = engine.calculate_kpis(sample_data)
        assert kpis["gross_margin_pct"] == pytest.approx(58.2, abs=0.1)

    def test_current_ratio(self, engine, sample_data):
        kpis = engine.calculate_kpis(sample_data)
        expected = 18_000_000 / 8_500_000
        assert kpis["current_ratio"] == pytest.approx(expected, abs=0.01)

    def test_net_debt(self, engine, sample_data):
        kpis = engine.calculate_kpis(sample_data)
        assert kpis["net_debt"] == 12_000_000 - 6_200_000

    def test_basic_eps(self, engine, sample_data):
        kpis = engine.calculate_kpis(sample_data)
        assert kpis["basic_eps"] == pytest.approx(1_890_000 / 4_500_000, abs=0.001)

    def test_diluted_eps_lower_than_basic(self, engine, sample_data):
        kpis = engine.calculate_kpis(sample_data)
        assert kpis["diluted_eps"] <= kpis["basic_eps"]

    def test_zero_division_safety(self, engine):
        data = {"revenue": 0, "current_liabilities": 0}
        kpis = engine.calculate_kpis(data)
        assert kpis["gross_margin_pct"] == 0.0
        assert kpis["current_ratio"] == 0.0


class TestAnomalyDetection:
    def test_low_gross_margin_flagged(self, engine, sample_data):
        data = {**sample_data, "ebitda": 100_000}
        kpis = {"gross_margin_pct": 14.5, "current_ratio": 2.0, "net_margin_pct": 1.0, "dso_days": 30, "debt_to_equity": 1.0, "net_debt": 0, "ccc_days": 45}
        flags = engine.detect_anomalies(data, kpis)
        assert any("gross margin" in f.lower() for f in flags)

    def test_current_ratio_critical(self, engine, sample_data):
        kpis = {"gross_margin_pct": 50.0, "current_ratio": 0.8, "net_margin_pct": 5.0, "dso_days": 30, "debt_to_equity": 1.0, "net_debt": 0}
        flags = engine.detect_anomalies(sample_data, kpis)
        assert any("current ratio" in f.lower() for f in flags)


class TestForecast:
    def test_forecast_produces_correct_periods(self, engine):
        historical = [100, 110, 121, 133, 146, 161, 177, 195]
        result = engine.forecast_revenue(historical, periods=6)
        assert len(result["forecast"]) == 6

    def test_insufficient_data_fallback(self, engine):
        historical = [100, 110]
        result = engine.forecast_revenue(historical, periods=3)
        assert len(result["forecast"]) == 3
        assert result["method"] == "linear_extrapolation"


class TestApprovalTriggers:
    def test_high_variance_triggers_hitl(self, engine):
        variance = {"totals": {"variance_pct": 15.0}}
        kpis = {"gross_margin_pct": 45.0}
        triggers = engine.check_approval_triggers(variance, kpis, [], None, None)
        reasons = [t["reason"] for t in triggers]
        assert "variance_exceeds_10pct" in reasons

    def test_low_gm_triggers_hitl(self, engine):
        variance = {"totals": {"variance_pct": 5.0}}
        kpis = {"gross_margin_pct": 25.0}
        triggers = engine.check_approval_triggers(variance, kpis, [], None, None)
        reasons = [t["reason"] for t in triggers]
        assert "gross_margin_below_30pct" in reasons

    def test_no_triggers_when_healthy(self, engine):
        variance = {"totals": {"variance_pct": 3.0}}
        kpis = {"gross_margin_pct": 55.0}
        triggers = engine.check_approval_triggers(variance, kpis, [], None, None)
        assert len(triggers) == 0
