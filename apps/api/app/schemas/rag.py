from pydantic import BaseModel, Field


class RagFilters(BaseModel):
    tags: list[str] | None = None
    source: str | None = None


class RagSearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=8, ge=1, le=20)
    filters: RagFilters | None = None


class RagResult(BaseModel):
    tool_id: int
    name: str
    description: str
    url: str
    score: float
    tags: list[str]


class RagSearchResponse(BaseModel):
    results: list[RagResult]
