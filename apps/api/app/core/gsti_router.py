from __future__ import annotations

from app.core.gsti_v0 import GSTIv0Engine
from app.core.gsti_v1 import GSTIv1Engine
from app.core.onet_features import extract_onet_numeric_features


class GSTIRouter:
    def __init__(self) -> None:
        self.v0 = GSTIv0Engine()
        self.v1 = GSTIv1Engine()

    def evaluate(
        self,
        tasks: list[str],
        onet_payload: dict | None,
        model_version: str = "auto",
        context: dict | None = None,
    ) -> dict:
        context = context or {}
        v1_numeric = extract_onet_numeric_features(onet_payload or {})
        numeric_count = sum(1 for item in v1_numeric.values() if item.get("value") is not None)
        too_sparse = numeric_count < 3 and len(tasks) < 5

        if model_version == "v0":
            result = self.v0.calculate_risk(tasks)
            result["model_version"] = "v0"
            return result

        if model_version == "auto" and too_sparse:
            result = self.v0.calculate_risk(tasks)
            result["model_version"] = "v0"
            result["summary"] += "（因 O*NET 数值特征和任务文本不足，自动回退到 v0）"
            return result

        v1_result = self.v1.evaluate(tasks, onet_payload, context=context, allow_degraded=model_version == "v1")
        v1_result["model_version"] = "v1"
        return v1_result
