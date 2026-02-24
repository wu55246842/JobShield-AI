from __future__ import annotations

from pydantic import BaseModel, Field


class CalibrationConfig(BaseModel):
    k: float = 8.0
    x0: float = 0.5


class TrendConfig(BaseModel):
    industry_automation_pressure: dict[str, float] = Field(default_factory=lambda: {
        "customer service": 0.09,
        "content operations": 0.08,
        "data entry": 0.1,
        "finance back office": 0.07,
        "healthcare": -0.03,
        "education": -0.02,
    })
    tool_coverage_hint: dict[str, float] = Field(default_factory=lambda: {
        "high_threshold": 6,
        "low_threshold": 1,
        "high_adjustment": 0.05,
        "low_adjustment": -0.03,
    })
    region_regulation_buffer: dict[str, float] = Field(default_factory=lambda: {
        "eu": -0.04,
        "germany": -0.04,
        "france": -0.04,
        "california": -0.03,
        "singapore": -0.01,
    })
    bounds: dict[str, float] = Field(default_factory=lambda: {"min": -0.15, "max": 0.15})


class GSTIv0FactorConfig(BaseModel):
    weight: float
    direction: str
    keywords: list[str]


class GSTIv0Config(BaseModel):
    factors: dict[str, GSTIv0FactorConfig]


class GSTIv1Config(BaseModel):
    top_level_weights: dict[str, float] = Field(default_factory=lambda: {
        "automation_susceptibility": 0.35,
        "human_advantage": 0.35,
        "responsibility_constraints": 0.15,
        "trend_modifier": 0.15,
    })
    automation_subweights: dict[str, float] = Field(default_factory=lambda: {
        "routine_structured": 0.45,
        "information_processing": 0.35,
        "automation_density": 0.20,
    })
    human_subweights: dict[str, float] = Field(default_factory=lambda: {
        "empathy_social": 0.30,
        "creativity_innovation": 0.25,
        "leadership_decision": 0.25,
        "human_density": 0.20,
    })
    responsibility_subweights: dict[str, float] = Field(default_factory=lambda: {
        "safety_compliance": 0.55,
        "physical_field_work": 0.45,
    })
    calibration: CalibrationConfig = Field(default_factory=CalibrationConfig)
    trend: TrendConfig = Field(default_factory=TrendConfig)


class GSTIConfig(BaseModel):
    v0: GSTIv0Config
    v1: GSTIv1Config = Field(default_factory=GSTIv1Config)
