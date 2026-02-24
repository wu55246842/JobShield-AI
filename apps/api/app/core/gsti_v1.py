from __future__ import annotations

from app.core.calibration import calibrate
from app.core.onet_features import extract_onet_numeric_features
from app.core.semantic_features import extract_semantic_features
from app.core.trend_adjustment import compute_trend_modifier


TOP_LEVEL_WEIGHTS = {
    "automation_susceptibility": 0.35,
    "human_advantage": 0.35,
    "responsibility_constraints": 0.15,
    "trend_modifier": 0.15,
}


class GSTIv1Engine:
    def evaluate(
        self,
        tasks: list[str],
        onet_payload: dict | None,
        context: dict | None = None,
        allow_degraded: bool = True,
    ) -> dict:
        context = context or {}
        onet_features = extract_onet_numeric_features(onet_payload or {})
        semantic = extract_semantic_features(tasks)
        trend = compute_trend_modifier(
            industry=context.get("industry"),
            region=context.get("region"),
            selected_tools=context.get("selected_tools"),
            occupation_code=context.get("occupation_code"),
            occupation_title=context.get("occupation_title"),
        )

        values = {k: v["value"] for k, v in onet_features.items()}

        def n(v, default=0.5):
            return default if v is None else v

        auto_sub = {
            "routine_structured": (n(values.get("routine_structured")), 0.45, onet_features.get("routine_structured", {})),
            "information_processing": (n(values.get("information_processing")), 0.35, onet_features.get("information_processing", {})),
            "automation_density": (semantic.get("automation_density") if semantic else None, 0.20, {"source": f"embedding:{semantic.get('model')}" if semantic else "embedding:unavailable"}),
        }
        human_sub = {
            "empathy_social": (n(values.get("empathy_social")), 0.30, onet_features.get("empathy_social", {})),
            "creativity_innovation": (n(values.get("creativity_innovation")), 0.25, onet_features.get("creativity_innovation", {})),
            "leadership_decision": (n(values.get("leadership_decision")), 0.25, onet_features.get("leadership_decision", {})),
            "human_density": (semantic.get("human_density") if semantic else None, 0.20, {"source": f"embedding:{semantic.get('model')}" if semantic else "embedding:unavailable"}),
        }
        resp_sub = {
            "safety_compliance": (n(values.get("safety_compliance")), 0.55, onet_features.get("safety_compliance", {})),
            "physical_field_work": (n(values.get("physical_field_work")), 0.45, onet_features.get("physical_field_work", {})),
        }

        auto_val, auto_breakdown = self._compose_subfactors(auto_sub)
        human_val, human_breakdown = self._compose_subfactors(human_sub)
        resp_val, resp_breakdown = self._compose_subfactors(resp_sub)

        factors = [
            self._factor_item("automation_susceptibility", "positive", TOP_LEVEL_WEIGHTS["automation_susceptibility"], auto_val, auto_breakdown),
            self._factor_item("human_advantage", "negative", TOP_LEVEL_WEIGHTS["human_advantage"], human_val, human_breakdown),
            self._factor_item("responsibility_constraints", "negative", TOP_LEVEL_WEIGHTS["responsibility_constraints"], resp_val, resp_breakdown),
            {
                "factor": "trend_modifier",
                "weight": TOP_LEVEL_WEIGHTS["trend_modifier"],
                "direction": "bidirectional",
                "value": round(trend["value"], 4),
                "risk_contribution": round(trend["value"] * 100, 4),
                "subfactors": trend["triggers"],
                "explanation": trend["explanation"],
            },
        ]

        raw_risk = (
            TOP_LEVEL_WEIGHTS["automation_susceptibility"] * auto_val
            + TOP_LEVEL_WEIGHTS["human_advantage"] * (1 - human_val)
            + TOP_LEVEL_WEIGHTS["responsibility_constraints"] * (1 - resp_val)
            + trend["value"]
        )
        raw_risk = max(0.0, min(1.0, raw_risk))
        calibrated = calibrate(raw_risk)

        score = round(calibrated * 100, 2)
        confidence = self._confidence(tasks, onet_features)
        numeric_count = sum(1 for item in onet_features.values() if item.get("value") is not None)
        degraded = allow_degraded and numeric_count < 3

        summary = self._summary(score, factors, degraded, raw_risk, calibrated)
        focus = self._suggested_focus(human_val, values)

        return {
            "score": score,
            "confidence": confidence,
            "breakdown": factors,
            "summary": summary,
            "suggested_focus": focus,
            "raw_risk": round(raw_risk, 4),
            "calibrated_risk": round(calibrated, 4),
            "numeric_feature_count": numeric_count,
            "task_count": len(tasks),
            "semantic_features": semantic,
        }

    def _compose_subfactors(self, subfactors: dict[str, tuple[float | None, float, dict]]) -> tuple[float, list[dict]]:
        available = {k: (v, w, src) for k, (v, w, src) in subfactors.items() if v is not None}
        total_weight = sum(w for _, w, _ in available.values()) or 1.0
        breakdown = []
        value = 0.0
        for name, (sub_value, sub_weight, source_meta) in available.items():
            norm_weight = sub_weight / total_weight
            value += sub_value * norm_weight
            breakdown.append(
                {
                    "name": name,
                    "value": round(sub_value, 4),
                    "weight": round(norm_weight, 4),
                    "source": source_meta.get("source"),
                    "raw_value": source_meta.get("raw_value"),
                    "explanation": f"{name} contributes {norm_weight:.2f} with value {sub_value:.2f}.",
                }
            )
        return value, breakdown

    def _factor_item(self, name: str, direction: str, weight: float, value: float, subfactors: list[dict]) -> dict:
        contribution = value * weight * 100 if direction == "positive" else (1 - value) * weight * 100
        return {
            "factor": name,
            "weight": weight,
            "direction": direction,
            "value": round(value, 4),
            "risk_contribution": round(contribution, 4),
            "subfactors": subfactors,
            "explanation": f"{name} computed from {len(subfactors)} subfactors.",
        }

    def _confidence(self, tasks: list[str], onet_features: dict) -> float:
        confidence = 0.65
        confidence += min(len(tasks) / 60.0, 0.15)

        numeric_count = sum(1 for item in onet_features.values() if item.get("value") is not None)
        if numeric_count >= 6:
            confidence += 0.08
        if numeric_count < 3:
            confidence -= 0.12

        return max(0.55, min(0.92, round(confidence, 2)))

    def _summary(self, score: float, factors: list[dict], degraded: bool, raw_risk: float, calibrated: float) -> str:
        dominant = max(factors, key=lambda x: abs(x.get("risk_contribution", 0)), default=None)
        level = "高" if score >= 70 else ("中" if score >= 40 else "低")
        base = f"GSTI v1 评估为{level}风险（{score:.1f}），raw={raw_risk:.2f}，calibrated={calibrated:.2f}。"
        if dominant:
            base += f"主要驱动因子为 {dominant['factor']}。"
        if degraded:
            base += " 数据不足，v1 处于退化运行模式。"
        return base

    def _suggested_focus(self, human_advantage: float, values: dict[str, float | None]) -> list[str]:
        suggestions = ["建立AI协作与结果验证习惯"]
        if (values.get("empathy_social") or 0.5) < 0.45:
            suggestions.append("强化同理心沟通与客户访谈能力")
        if (values.get("creativity_innovation") or 0.5) < 0.45:
            suggestions.append("训练创意问题定义与方案生成能力")
        if (values.get("leadership_decision") or 0.5) < 0.45:
            suggestions.append("提升跨团队决策与利益相关方协调能力")
        if human_advantage < 0.5:
            suggestions.append("增加高不确定性任务承担比例")
        suggestions.append("持续更新行业工具栈并形成复盘机制")
        return suggestions[:6]
