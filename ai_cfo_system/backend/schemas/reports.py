from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ComplianceSection(BaseModel):
    standard: str
    status: str   # "COMPLIANT" | "DISCLOSURE_REQUIRED" | "NON_COMPLIANT"
    finding: str
    disclosure_note: Optional[str] = None


class RiskItem(BaseModel):
    description: str
    severity: str  # "critical" | "high" | "medium" | "low"
    quantified_impact: Optional[str] = None
    mitigation: Optional[str] = None


class ActionItem(BaseModel):
    action: str
    owner: str
    deadline: str
    standard_reference: Optional[str] = None
    priority: str = "medium"


class BoardReport(BaseModel):
    # Header
    company_name: str
    period: str
    report_format: str
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    approved_by: Optional[str] = None

    # Sections
    executive_summary: str = Field(..., min_length=100)
    revenue_performance: str
    cost_margin_analysis: str
    gaap_compliance_notes: List[ComplianceSection]
    ifrs_compliance_notes: List[ComplianceSection]
    risk_assessment: List[RiskItem]
    action_plan: List[ActionItem]

    # Key metrics (from math engine — exact)
    kpi_snapshot: Dict[str, Any] = Field(default_factory=dict)
    variance_summary: Dict[str, Any] = Field(default_factory=dict)

    # Metadata
    rag_sources: List[str] = Field(default_factory=list)
    math_engine_version: str = "deterministic_v1"
    total_tokens_used: Optional[int] = None
