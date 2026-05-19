from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
import re


class AnalysisOutput(BaseModel):
    executive_summary:    str        = Field(..., min_length=50)
    key_variance_drivers: List[str]  = Field(..., min_length=1, max_length=10)
    identified_risks:     List[str]  = Field(..., min_length=1)
    opportunities:        List[str]  = Field(default_factory=list)
    action_items:         List[str]  = Field(..., min_length=1, max_length=5)
    confidence_score:     float      = Field(..., ge=0.0, le=1.0)
    rag_sources_cited:    List[str]  = Field(default_factory=list)
    gaap_citations:       List[str]  = Field(default_factory=list)
    ifrs_citations:       List[str]  = Field(default_factory=list)

    @field_validator("executive_summary")
    @classmethod
    def must_reference_numbers(cls, v: str) -> str:
        if not re.search(r"\$[\d,]+|[\d.]+%|\d+\s*(million|M|K|B|billion)", v):
            raise ValueError("Executive summary must cite specific financial figures (e.g., '$1.2M', '15.3%')")
        return v

    @field_validator("action_items")
    @classmethod
    def action_items_must_have_owners(cls, v: List[str]) -> List[str]:
        for item in v:
            if not re.search(r"(CFO|CEO|Controller|FP&A|Finance|VP|Director|Owner|owner|deadline|by\s+\w+)", item, re.IGNORECASE):
                raise ValueError(f"Action item must include owner/deadline: '{item}'")
        return v
