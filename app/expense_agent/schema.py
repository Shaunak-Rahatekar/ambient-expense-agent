from pydantic import BaseModel
from typing import Optional, Any
from google.adk.events.request_input import RequestInput

class ExpenseReport(BaseModel):
    id: str = "N/A"
    amount: float
    submitter: str
    employee_name: str = ""
    merchant: str = ""
    category: str = ""
    description: str
    date: str
    redacted_categories: list[str] = []


class SecurityAssessment(BaseModel):
    is_injected: bool
    reason: str

class RiskAssessment(BaseModel):
    is_risky: bool
    risk_factors: list[str]
    summary: str

class ApprovalOutcome(BaseModel):
    status: str
    reason: Optional[str] = None
