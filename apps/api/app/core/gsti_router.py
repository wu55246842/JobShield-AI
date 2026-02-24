from __future__ import annotations

from app.core.config_models import GSTIConfig
from app.core.gsti_v0 import DEFAULT_CONFIG as V0_DEFAULT_CONFIG
from app.core.gsti_v0 import GSTIv0Engine
from app.core.gsti_v1 import DEFAULT_CONFIG as V1_DEFAULT_CONFIG
from app.core.gsti_v1 import GSTIv1Engine
from app.core.onet_features import extract_onet_numeric_features

DEFAULT_CONFIG = GSTIConfig(v0=V0_DEFAULT_CONFIG, v1=V1_DEFAULT_CONFIG)


class GSTIRouter:
    def __init__(self, config: GSTIConfig | None = None) -> None:
        self.config = config or DEFAULT_CONFIG
        self.v0 = GSTIv0Engine(config=self.config.v0)
        self.v1 = GSTIv1Engine(config=self.config.v1)

    @classmethod
    def from_params(cls, params: dict | None = None) -> "GSTIRouter":
        if not params:
            return cls()
        merged = DEFAULT_CONFIG.model_dump()
        for key, value in params.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = {**merged[key], **value}
            else:
                merged[key] = value
        return cls(config=GSTIConfig.model_validate(merged))

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
