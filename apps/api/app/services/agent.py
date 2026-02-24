from app.schemas.agent import AgentConfig


def build_agent_config(user_goal: str, tools: list[dict], risk_score: float | None = None) -> AgentConfig:
    risk_text = f"当前风险评分 {risk_score}，优先建立可迁移能力。" if risk_score is not None else "优先建立可迁移能力。"
    return AgentConfig(
        name="JobShield Copilot",
        description=f"围绕目标“{user_goal}”的个性化职业增强Agent",
        system_prompt=(
            "你是职业发展与AI增效助手。输出简洁、可执行步骤，不暴露内部推理。"
            + risk_text
        ),
        tools=[
            {
                "name": t["name"],
                "purpose": "用于提升目标任务效率",
                "how_to_use": "每周选择一个真实任务进行试运行并记录ROI",
                "link": t["url"],
            }
            for t in tools
        ],
        workflows=[
            {
                "task": "每周职业增强迭代",
                "steps": ["选择任务", "匹配工具", "执行与复盘", "更新作品集"],
                "guardrails": ["不上传敏感数据", "关键决策需人工复核"],
            }
        ],
        memory_policy={
            "retention": "90d",
            "pii_handling": "mask",
            "notes": "仅保存任务元信息与产出摘要",
        },
        version="v1",
    )
