from pydantic import BaseModel, Field
from typing import Optional, Any

class ExpenseReport(BaseModel):
    amount: float
    submitter: str
    category: str
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

class ExpenseExtraction(BaseModel):
    is_complete: bool = Field(description="Set to true only if ALL required fields are present in the user's message history.")
    missing_info_message: Optional[str] = Field(default=None, description="Message asking the user for missing fields. Be polite and list exactly what is still needed: amount, submitter, category, description, date.")
    expense: Optional[ExpenseReport] = Field(default=None, description="The extracted expense report. Only populate if is_complete is true.")
