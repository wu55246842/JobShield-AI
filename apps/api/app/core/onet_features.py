from __future__ import annotations

from dataclasses import dataclass


FEATURE_MAP = {
    "routine_structured": {
        "aliases": ["structured versus unstructured work", "importance of being exact or accurate", "degree of automation", "repetitive motions", "routine"],
        "endpoints": ["work_context", "work_activities"],
    },
    "information_processing": {
        "aliases": ["processing information", "analyzing data or information", "interacting with computers", "documenting/recording information", "data"],
        "endpoints": ["work_activities", "skills", "knowledge"],
    },
    "physical_field_work": {
        "aliases": ["handling and moving objects", "spend time standing", "outdoors", "manual dexterity", "physical"],
        "endpoints": ["work_context", "abilities", "work_activities"],
    },
    "empathy_social": {
        "aliases": ["assisting and caring for others", "social orientation", "concern for others", "service orientation", "dealing with external customers"],
        "endpoints": ["work_activities", "work_styles", "skills", "interests"],
    },
    "creativity_innovation": {
        "aliases": ["thinking creatively", "innovation", "originality", "artistic", "developing objectives and strategies"],
        "endpoints": ["work_activities", "abilities", "interests"],
    },
    "leadership_decision": {
        "aliases": ["making decisions and solving problems", "leadership", "coordinate the work", "guiding, directing, and motivating subordinates"],
        "endpoints": ["work_activities", "work_styles", "skills"],
    },
    "safety_compliance": {
        "aliases": ["responsibility for outcomes and results", "impact of decisions on co-workers", "safety", "frequency of conflict situations", "regulatory"],
        "endpoints": ["work_context", "work_values", "knowledge"],
    },
}

VALUE_KEYS = ["value", "score", "data_value", "level", "importance"]
SCALE_MIN_KEYS = ["min", "minimum", "scale_min"]
SCALE_MAX_KEYS = ["max", "maximum", "scale_max"]
LABEL_KEYS = ["name", "title", "element_name", "descriptor", "label"]


@dataclass
class FeaturePoint:
    value: float | None
    source: str | None
    raw_value: float | None



def _normalize(raw_value: float, item: dict) -> float:
    scale = item.get("scale") if isinstance(item.get("scale"), dict) else {}
    min_v = next((scale.get(k) for k in SCALE_MIN_KEYS if scale.get(k) is not None), None)
    max_v = next((scale.get(k) for k in SCALE_MAX_KEYS if scale.get(k) is not None), None)
    if min_v is None:
        min_v = next((item.get(k) for k in SCALE_MIN_KEYS if item.get(k) is not None), None)
    if max_v is None:
        max_v = next((item.get(k) for k in SCALE_MAX_KEYS if item.get(k) is not None), None)

    if min_v is None and max_v is None:
        if raw_value <= 1:
            return max(0.0, min(1.0, raw_value))
        return max(0.0, min(1.0, raw_value / 100.0))

    low = float(min_v if min_v is not None else 0.0)
    high = float(max_v if max_v is not None else 100.0)
    if high <= low:
        return max(0.0, min(1.0, raw_value / 100.0))
    return max(0.0, min(1.0, (raw_value - low) / (high - low)))


def _iter_items(node, path: str = ""):
    if isinstance(node, dict):
        yield path, node
        for key, value in node.items():
            next_path = f"{path}.{key}" if path else key
            yield from _iter_items(value, next_path)
    elif isinstance(node, list):
        for idx, item in enumerate(node):
            next_path = f"{path}[{idx}]"
            yield from _iter_items(item, next_path)


def extract_onet_numeric_features(onet_payload: dict) -> dict[str, dict[str, float | str | None]]:
    results: dict[str, dict[str, float | str | None]] = {}
    items = list(_iter_items(onet_payload))

    for dim, config in FEATURE_MAP.items():
        best: FeaturePoint = FeaturePoint(value=None, source=None, raw_value=None)
        for path, item in items:
            if not isinstance(item, dict):
                continue

            path_lower = path.lower()
            if config["endpoints"] and not any(endpoint in path_lower for endpoint in config["endpoints"]):
                continue

            label = " ".join(str(item.get(k, "")) for k in LABEL_KEYS).lower()
            if not any(alias in label for alias in config["aliases"]):
                continue

            raw = next((item.get(k) for k in VALUE_KEYS if item.get(k) is not None), None)
            if raw is None:
                continue

            try:
                raw_f = float(raw)
            except (TypeError, ValueError):
                continue

            normalized = _normalize(raw_f, item)
            if best.value is None or normalized > best.value:
                best = FeaturePoint(value=normalized, source=path, raw_value=raw_f)

        results[dim] = {"value": best.value, "source": best.source, "raw_value": best.raw_value}

    return results
