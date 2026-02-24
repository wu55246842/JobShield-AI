from __future__ import annotations

from app.core.config_models import TrendConfig

DEFAULT_CONFIG = TrendConfig()


def compute_trend_modifier(
    industry: str | None = None,
    region: str | None = None,
    selected_tools: list[str] | None = None,
    occupation_code: str | None = None,
    occupation_title: str | None = None,
    config: TrendConfig | None = None,
) -> dict:
    del occupation_code, occupation_title
    cfg = config or DEFAULT_CONFIG

    triggers: list[dict] = []
    modifier = 0.0

    if industry:
        industry_key = industry.lower()
        for key, adj in cfg.industry_automation_pressure.items():
            if key in industry_key:
                modifier += adj
                triggers.append({"rule": "industry_automation_pressure", "match": key, "adjustment": adj})
                break

    tool_count = len(selected_tools or [])
    tool_cfg = cfg.tool_coverage_hint
    if tool_count >= tool_cfg["high_threshold"]:
        modifier += tool_cfg["high_adjustment"]
        triggers.append({"rule": "tool_coverage_hint", "match": "high_coverage", "adjustment": tool_cfg["high_adjustment"]})
    elif tool_count <= tool_cfg["low_threshold"]:
        modifier += tool_cfg["low_adjustment"]
        triggers.append({"rule": "tool_coverage_hint", "match": "low_coverage", "adjustment": tool_cfg["low_adjustment"]})

    if region:
        region_key = region.lower()
        for key, adj in cfg.region_regulation_buffer.items():
            if key in region_key:
                modifier += adj
                triggers.append({"rule": "region_regulation_buffer", "match": key, "adjustment": adj})
                break

    lower = cfg.bounds["min"]
    upper = cfg.bounds["max"]
    modifier = max(lower, min(upper, modifier))

    return {
        "value": modifier,
        "triggers": triggers,
        "explanation": "; ".join(f"{t['rule']}({t['match']}) {t['adjustment']:+.2f}" for t in triggers) or "No trend rules triggered.",
    }
