from pydantic import BaseModel, Field


class UserInputs(BaseModel):
    skills: list[str] = Field(default_factory=list)
    tasks_preference: list[str] = Field(default_factory=list)
    industry: str | None = None
    region: str | None = None
    selected_tools: list[str] = Field(default_factory=list)


class RiskEvaluateRequest(BaseModel):
    occupation_code: str | None = None
    occupation_title: str | None = None
    user_inputs: UserInputs
    session_id: str = "anon"
    model_version: str = "auto"
    experiment_id: int | None = None
    variant: str | None = None
    user_key: str | None = None


class RiskSubfactorItem(BaseModel):
    name: str | None = None
    value: float | None = None
    weight: float | None = None
    source: str | None = None
    raw_value: float | None = None
    explanation: str | None = None
    rule: str | None = None
    match: str | None = None
    adjustment: float | None = None


class RiskBreakdownItem(BaseModel):
    factor: str
    weight: float
    value: float
    explanation: str
    direction: str | None = None
    risk_contribution: float | None = None
    subfactors: list[RiskSubfactorItem] | None = None


class RiskEvaluateResponse(BaseModel):
    score: float
    confidence: float | None = None
    model_version: str | None = None
    breakdown: list[RiskBreakdownItem]
    summary: str
    suggested_focus: list[str]
    assessment_id: int | None = None
    experiment: dict | None = None
