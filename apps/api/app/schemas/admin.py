from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class LabelCreateRequest(BaseModel):
    assessment_id: int
    rater: str
    risk_score_label: float | None = Field(default=None, ge=0, le=100)
    confidence_label: float | None = Field(default=None, ge=0, le=1)
    notes: str | None = None
    factor_overrides: dict = Field(default_factory=dict)
    label_type: str = "risk_score"


class LabelResponse(BaseModel):
    id: int
    assessment_id: int
    rater: str
    label_type: str
    risk_score_label: float | None
    confidence_label: float | None
    factor_overrides: dict
    notes: str | None
    created_at: datetime


class ExperimentCreateRequest(BaseModel):
    name: str
    description: str | None = None
    model_version: str = "v1"
    params: dict = Field(default_factory=dict)
    is_active: bool = False


class ExperimentPatchRequest(BaseModel):
    description: str | None = None
    model_version: str | None = None
    params: dict | None = None
    is_active: bool | None = None


class ExperimentResponse(BaseModel):
    id: int
    name: str
    description: str | None
    model_version: str
    params: dict
    is_active: bool
    created_at: datetime


class ExperimentAssignRequest(BaseModel):
    user_key: str
    experiment_name: str


class ExperimentAssignResponse(BaseModel):
    experiment_id: int
    variant: str


class ExperimentMetricsResponse(BaseModel):
    experiment_id: int
    sample_count: int
    by_variant: dict
    error_metrics: dict
    score_distribution: dict


class CompareResponse(BaseModel):
    assessment_id: int
    outputs: dict
