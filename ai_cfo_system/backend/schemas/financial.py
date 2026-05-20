import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class LineItem(BaseModel):
    name: str
    actual: float
    budget: Optional[float] = None
    prior_year: Optional[float] = None
    category: Optional[str] = None  # "revenue"|"cogs"|"opex"|"capex"
    notes: Optional[str] = None


class FinancialDataSchema(BaseModel):
    company_name: str
    period: str  # "Q1 2025", "FY 2024", "January 2025"
    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")

    # Income Statement
    revenue: Optional[float] = None
    cogs: Optional[float] = None
    gross_profit: Optional[float] = None
    ebitda: Optional[float] = None
    ebit: Optional[float] = None
    interest_expense: Optional[float] = None
    pre_tax_income: Optional[float] = None
    tax_provision: Optional[float] = None
    net_income: Optional[float] = None
    rd_expense: Optional[float] = None
    sga_expense: Optional[float] = None
    depreciation_amortization: Optional[float] = None

    # Balance Sheet
    total_assets: Optional[float] = None
    total_equity: Optional[float] = None
    current_assets: Optional[float] = None
    current_liabilities: Optional[float] = None
    cash: Optional[float] = None
    total_debt: Optional[float] = None
    accounts_receivable: Optional[float] = None
    accounts_payable: Optional[float] = None
    inventory: Optional[float] = None
    goodwill: Optional[float] = None
    rou_assets: Optional[float] = None
    lease_liability: Optional[float] = None
    deferred_revenue: Optional[float] = None
    deferred_tax_asset: Optional[float] = None

    # Cash Flow
    cash_from_operations: Optional[float] = None
    cash_from_investing: Optional[float] = None
    cash_from_financing: Optional[float] = None
    capex: Optional[float] = None
    free_cash_flow: Optional[float] = None
    monthly_cash_burn: Optional[float] = None

    # Equity
    shares_outstanding: Optional[float] = None
    diluted_shares: Optional[float] = None

    # Budget comparison
    actuals: Optional[Dict[str, float]] = None
    budget: Optional[Dict[str, float]] = None
    historical_revenue: Optional[List[float]] = None

    # Compliance metadata
    inventory_cost_method: Optional[str] = "fifo"
    revenue_recognition_policy: Optional[str] = None
    interest_cash_flow_classification: Optional[str] = "operating"
    publicly_listed: Optional[bool] = False
    impairment_test_performed: Optional[bool] = None
    segments: Optional[List[Dict[str, Any]]] = None
    fair_value_investments: Optional[List[Dict[str, Any]]] = None
    contingent_liabilities: Optional[List[Dict[str, Any]]] = None

    # Line items
    line_items: Optional[List[LineItem]] = None

    @field_validator("period")
    @classmethod
    def validate_period(cls, v: str) -> str:
        patterns = [
            r"^Q[1-4]\s+\d{4}$",
            r"^FY\s+\d{4}$",
            r"^H[1-2]\s+\d{4}$",
            r"^(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}$",
            r"^\d{4}$",
        ]
        if not any(re.match(p, v) for p in patterns):
            raise ValueError(f"Period '{v}' must be format 'Q1 2025', 'FY 2024', 'H1 2024', or 'January 2025'")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        valid = {"USD", "EUR", "GBP", "CAD", "AUD", "JPY", "CHF", "CNY", "SGD", "HKD"}
        if v not in valid:
            raise ValueError(f"Currency must be one of {valid}")
        return v

    @field_validator("revenue", "cogs", "total_assets", "total_equity", mode="before")
    @classmethod
    def must_be_positive(cls, v):
        if v is not None and float(v) < 0:
            raise ValueError("Financial values should be positive (signs are handled by the math engine)")
        return v

    def compute_derived(self) -> "FinancialDataSchema":
        """Compute gross_profit, ebit from components if not provided."""
        if self.gross_profit is None and self.revenue and self.cogs:
            self.gross_profit = round(self.revenue - self.cogs, 2)
        if self.ebit is None and self.ebitda and self.depreciation_amortization:
            self.ebit = round(self.ebitda - self.depreciation_amortization, 2)
        return self
