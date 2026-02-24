from __future__ import annotations

TREND_CONFIG = {
    "industry_automation_pressure": {
        "customer service": 0.09,
        "content operations": 0.08,
        "data entry": 0.1,
        "finance back office": 0.07,
        "healthcare": -0.03,
        "education": -0.02,
    },
    "tool_coverage_hint": {
        "high_threshold": 6,
        "low_threshold": 1,
        "high_adjustment": 0.05,
        "low_adjustment": -0.03,
    },
    "region_regulation_buffer": {
        "eu": -0.04,
        "germany": -0.04,
        "france": -0.04,
        "california": -0.03,
        "singapore": -0.01,
    },
    "bounds": {"min": -0.15, "max": 0.15},
}


def compute_trend_modifier(
    industry: str | None = None,
    region: str | None = None,
    selected_tools: list[str] | None = None,
    occupation_code: str | None = None,
    occupation_title: str | None = None,
) -> dict:
    del occupation_code, occupation_title

    triggers: list[dict] = []
    modifier = 0.0

    if industry:
        industry_key = industry.lower()
        for key, adj in TREND_CONFIG["industry_automation_pressure"].items():
            if key in industry_key:
                modifier += adj
                triggers.append({"rule": "industry_automation_pressure", "match": key, "adjustment": adj})
                break

    tool_count = len(selected_tools or [])
    tool_cfg = TREND_CONFIG["tool_coverage_hint"]
    if tool_count >= tool_cfg["high_threshold"]:
        modifier += tool_cfg["high_adjustment"]
        triggers.append({"rule": "tool_coverage_hint", "match": "high_coverage", "adjustment": tool_cfg["high_adjustment"]})
    elif tool_count <= tool_cfg["low_threshold"]:
        modifier += tool_cfg["low_adjustment"]
        triggers.append({"rule": "tool_coverage_hint", "match": "low_coverage", "adjustment": tool_cfg["low_adjustment"]})

    if region:
        region_key = region.lower()
        for key, adj in TREND_CONFIG["region_regulation_buffer"].items():
            if key in region_key:
                modifier += adj
                triggers.append({"rule": "region_regulation_buffer", "match": key, "adjustment": adj})
                break

    lower = TREND_CONFIG["bounds"]["min"]
    upper = TREND_CONFIG["bounds"]["max"]
    modifier = max(lower, min(upper, modifier))

    return {
        "value": modifier,
        "triggers": triggers,
        "explanation": "; ".join(f"{t['rule']}({t['match']}) {t['adjustment']:+.2f}" for t in triggers) or "No trend rules triggered.",
    }
