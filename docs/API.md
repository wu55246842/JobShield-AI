# API
- `GET /health`
- `GET /onet/occupation/search?q=`
- `GET /onet/occupation/{code}`
- `GET /onet/occupation/{code}/tasks`
- `POST /risk/evaluate`
- `POST /rag/tools/search`
- `POST /agent/generate` (SSE events: `step`, `delta`, `result`)
- `POST /ingest/apify/webhook` (requires `X-API-Key`)

错误格式统一：`{ "error": { "code", "message", "details?" } }`

## POST /risk/evaluate

### Request
```json
{
  "occupation_code": "43-3031.00",
  "occupation_title": "Bookkeeping Clerk",
  "session_id": "anon",
  "model_version": "auto",
  "user_inputs": {
    "skills": ["excel", "reporting"],
    "tasks_preference": ["data entry", "review forms"],
    "industry": "finance back office",
    "region": "eu",
    "selected_tools": ["airtable", "zapier"]
  }
}
```

`model_version` 支持 `v0|v1|auto`（默认 `auto`）：
- `auto`: 当 O*NET 数值维度 `<3` 且任务文本 `<5` 时回退 `v0`
- `v1`: 强制运行 GSTI v1（数据不足时降级运行并降低置信提示）
- `v0`: 仅运行关键词启发式版本

### GSTI v1 说明
- 核心特征来自 O*NET 数值维度，字段通过 `FEATURE_MAP` + 多候选键路径做鲁棒解析。当前实现假设常见字段名包括：`name/title/element_name` 与 `value/score/data_value/level/importance`，并支持 `scale.min/max` 或 `min/max` 归一化。可在 `app/core/onet_features.py` 中调整。 
- 可选语义层使用 embedding 估计 `automation_density` / `human_density`；无 API key 或调用失败时自动跳过。
- 趋势修正项来自可配置表（行业压力、工具覆盖、地区监管缓冲），范围限制在 `[-0.15, 0.15]`。
- 最终分数先计算 `raw_risk` 再通过 logistic calibration 映射到 `0-100`。

### Response（高风险示例）
```json
{
  "score": 81.4,
  "confidence": 0.84,
  "model_version": "v1",
  "summary": "GSTI v1 评估为高风险...",
  "suggested_focus": ["强化同理心沟通与客户访谈能力"],
  "breakdown": [
    {
      "factor": "automation_susceptibility",
      "weight": 0.35,
      "direction": "positive",
      "value": 0.81,
      "risk_contribution": 28.35,
      "subfactors": [
        {
          "name": "routine_structured",
          "value": 0.88,
          "weight": 0.45,
          "source": "detail.work_context[0]",
          "raw_value": 88,
          "explanation": "..."
        }
      ],
      "explanation": "..."
    }
  ]
}
```

### Response（低风险示例）
```json
{
  "score": 33.2,
  "confidence": 0.79,
  "model_version": "v1",
  "summary": "GSTI v1 评估为低风险...",
  "suggested_focus": ["持续更新行业工具栈并形成复盘机制"],
  "breakdown": [
    {
      "factor": "human_advantage",
      "weight": 0.35,
      "direction": "negative",
      "value": 0.79,
      "risk_contribution": 7.35,
      "subfactors": [
        {
          "name": "empathy_social",
          "value": 0.92,
          "weight": 0.30,
          "source": "detail.work_activities[0]",
          "raw_value": 92,
          "explanation": "..."
        }
      ],
      "explanation": "..."
    }
  ]
}
```
