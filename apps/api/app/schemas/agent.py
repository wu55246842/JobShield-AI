from pydantic import BaseModel, Field


class AgentTool(BaseModel):
    name: str
    purpose: str
    how_to_use: str
    link: str


class Workflow(BaseModel):
    task: str
    steps: list[str]
    guardrails: list[str] = Field(default_factory=list)


class MemoryPolicy(BaseModel):
    retention: str
    pii_handling: str
    notes: str | None = None


class AgentConfig(BaseModel):
    name: str
    description: str
    system_prompt: str
    tools: list[AgentTool]
    workflows: list[Workflow]
    memory_policy: MemoryPolicy
    version: str = "v1"


class AgentGenerateRequest(BaseModel):
    user_goal: str
    occupation_code: str | None = None
    risk_score: float | None = None
    selected_tools: list[int] = Field(default_factory=list)
    preferences: dict = Field(default_factory=dict)
    assessment_id: int | None = None


class ApifyWebhookItem(BaseModel):
    name: str
    description: str
    url: str
    tags: list[str] = Field(default_factory=list)
    source: str = "apify"
    raw_payload: dict = Field(default_factory=dict)


class ApifyWebhookPayload(BaseModel):
    items: list[ApifyWebhookItem]
