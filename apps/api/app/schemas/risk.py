from pydantic import BaseModel, Field


class UserInputs(BaseModel):
    skills: list[str] = Field(default_factory=list)
    tasks_preference: list[str] = Field(default_factory=list)
    industry: str | None = None
    region: str | None = None


class RiskEvaluateRequest(BaseModel):
    occupation_code: str | None = None
    occupation_title: str | None = None
    user_inputs: UserInputs
    session_id: str = "anon"


class RiskBreakdownItem(BaseModel):
    factor: str
    weight: float
    value: float
    explanation: str


class RiskEvaluateResponse(BaseModel):
    score: float
    breakdown: list[RiskBreakdownItem]
    summary: str
    suggested_focus: list[str]
    assessment_id: int | None = None
