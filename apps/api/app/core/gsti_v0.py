from __future__ import annotations

from dataclasses import dataclass


FACTOR_CONFIG = {
    "routine_structured": {
        "weight": 0.22,
        "direction": "positive",
        "keywords": [
            "record",
            "process data",
            "enter data",
            "calculate",
            "monitor equipment",
            "inspect",
            "assemble",
            "file documents",
            "review forms",
            "standard procedure",
            "standardized",
        ],
    },
    "information_processing": {
        "weight": 0.18,
        "direction": "positive",
        "keywords": [
            "analyze data",
            "generate reports",
            "prepare statements",
            "compile information",
            "audit records",
            "reporting",
            "financial analysis",
            "data analysis",
        ],
    },
    "physical_field_work": {
        "weight": 0.14,
        "direction": "negative",
        "keywords": [
            "operate machinery on site",
            "repair",
            "install",
            "physical assistance",
            "manual adjustment",
            "field inspection",
            "on site",
            "maintenance",
        ],
    },
    "empathy_negotiation": {
        "weight": 0.16,
        "direction": "negative",
        "keywords": [
            "counsel",
            "negotiate",
            "mediate",
            "advise clients",
            "resolve conflict",
            "provide emotional support",
            "patient care",
            "support families",
        ],
    },
    "creativity_leadership": {
        "weight": 0.18,
        "direction": "negative",
        "keywords": [
            "develop strategy",
            "design new solutions",
            "lead team",
            "make high-level decisions",
            "innovation",
            "vision",
            "architect",
        ],
    },
    "compliance_safety": {
        "weight": 0.12,
        "direction": "negative",
        "keywords": [
            "ensure compliance",
            "regulatory approval",
            "legal responsibility",
            "safety standards enforcement",
            "regulatory",
            "legal",
            "safety protocols",
        ],
    },
}

# TODO v1:
# - 接入 O*NET structured work context numeric scores
# - 使用 NLP embedding 相似度代替简单关键词
# - 根据行业动态调整权重


@dataclass
class _FactorObservation:
    raw_value: float
    matched_keywords: int
    total_tasks: int


class GSTIv0Engine:
    def extract_factor_scores(self, tasks: list[str]) -> dict[str, dict[str, float | int]]:
        if not tasks:
            return {
                factor: {"raw_value": 0.0, "matched_keywords": 0, "total_tasks": 0}
                for factor in FACTOR_CONFIG
            }

        normalized_tasks = [task.lower() for task in tasks]
        observations: dict[str, dict[str, float | int]] = {}
        for factor, config in FACTOR_CONFIG.items():
            keywords = config["keywords"]
            matched_keywords = sum(
                1
                for task in normalized_tasks
                for keyword in keywords
                if keyword in task
            )
            task_match_count = sum(
                1
                for task in normalized_tasks
                if any(keyword in task for keyword in keywords)
            )
            raw_value = min(1.0, task_match_count / len(normalized_tasks))
            observations[factor] = {
                "raw_value": raw_value,
                "matched_keywords": matched_keywords,
                "total_tasks": len(normalized_tasks),
            }

        return observations

    def calculate_risk(self, tasks: list[str]) -> dict:
        observations = self.extract_factor_scores(tasks)
        breakdown = []
        risk_sum = 0.0

        for factor, config in FACTOR_CONFIG.items():
            weight = config["weight"]
            direction = config["direction"]
            obs = _FactorObservation(**observations[factor])

            if direction == "positive":
                contribution = obs.raw_value * weight * 100
                direction_text = "正向影响风险（值越高，风险越高）"
            else:
                contribution = (1 - obs.raw_value) * weight * 100
                direction_text = "反向影响风险（值越高，风险越低）"

            risk_sum += contribution
            breakdown.append(
                {
                    "factor": factor,
                    "weight": weight,
                    "raw_value": round(obs.raw_value, 4),
                    "risk_contribution": round(contribution, 4),
                    "direction": direction,
                    "explanation": (
                        f"匹配关键词 {obs.matched_keywords} 次 / 任务总数 {obs.total_tasks}。"
                        f"该因子为{direction_text}。"
                    ),
                }
            )

        score = max(0.0, min(100.0, round(risk_sum, 2)))
        confidence = min(0.9, round(0.6 + min(len(tasks) / 50, 0.3), 2))

        return {
            "score": score,
            "confidence": confidence,
            "breakdown": breakdown,
            "summary": self.generate_summary(score, breakdown),
            "suggested_focus": self.suggest_focus(score, breakdown),
        }

    def generate_summary(self, score: float, breakdown: list[dict]) -> str:
        strongest = max(breakdown, key=lambda item: item["risk_contribution"], default=None)
        if score >= 70:
            level = "高风险"
        elif score >= 40:
            level = "中风险"
        else:
            level = "低风险"

        if strongest:
            return f"该职业属于{level}自动化风险，主要受 {strongest['factor']} 因子驱动。"
        return f"该职业属于{level}自动化风险。"

    def suggest_focus(self, score: float, breakdown: list[dict]) -> list[str]:
        suggestions = ["提升AI工具协作能力", "建立持续学习与转型计划"]

        high_risk_factors = sorted(
            breakdown,
            key=lambda item: item["risk_contribution"],
            reverse=True,
        )[:2]
        factors = {item["factor"] for item in high_risk_factors}

        if "routine_structured" in factors or "information_processing" in factors:
            suggestions.append("提升决策能力")
            suggestions.append("加强跨职能协作能力")
        if score >= 70:
            suggestions.append("发展创意与领导类不可替代能力")

        return suggestions
