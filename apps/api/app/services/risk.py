from app.schemas.risk import RiskBreakdownItem


def _score_preference(items: list[str], positive: set[str], negative: set[str]) -> float:
    if not items:
        return 0.5
    normalized = {i.lower() for i in items}
    p = len(normalized & positive)
    n = len(normalized & negative)
    return min(1.0, max(0.0, 0.5 + (n - p) * 0.2))


def evaluate_risk_v0(tasks: list[str], user_inputs: dict) -> tuple[float, list[RiskBreakdownItem], str, list[str]]:
    task_blob = " ".join(tasks).lower()
    routine = 0.8 if any(k in task_blob for k in ["repeat", "routine", "data entry", "standardized"]) else 0.45
    creativity = 0.2 if any(k in task_blob for k in ["design", "strategy", "invent", "creative"]) else 0.55
    people = 0.25 if any(k in task_blob for k in ["counsel", "negot", "teach", "care"]) else 0.6
    compliance = 0.35 if any(k in task_blob for k in ["safety", "regulation", "compliance", "audit"]) else 0.5

    pref = _score_preference(
        user_inputs.get("tasks_preference", []),
        positive={"creative", "leadership", "client communication"},
        negative={"repetitive", "structured", "predictable"},
    )

    factors = [
        ("routine_structured", 0.35, routine, "任务越重复和结构化，越容易被自动化。"),
        ("creative_complexity", 0.25, creativity, "创意和非结构化决策越高，替代风险越低。"),
        ("human_interaction", 0.20, people, "高人际互动工作短期替代难度更高。"),
        ("compliance_safety", 0.10, compliance, "高合规/安全责任场景替代速度通常更慢。"),
        ("user_preference_adjustment", 0.10, pref, "用户偏好会影响岗位迁移与工具采用路径。"),
    ]

    breakdown = [RiskBreakdownItem(factor=f, weight=w, value=v, explanation=e) for f, w, v, e in factors]
    score = round(sum(w * v for _, w, v, _ in factors) * 100, 2)
    summary = "当前岗位存在中高自动化风险，建议强化高价值的人机协作技能。" if score >= 60 else "当前岗位风险可控，建议持续提升AI增强型技能。"
    focus = ["流程自动化编排", "跨工具协同", "领域知识+沟通", "结果验证与质量控制"]
    return score, breakdown, summary, focus
