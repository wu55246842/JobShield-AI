# ARCHITECTURE
- Web(Next.js) -> `/api/py/*` rewrite -> API(FastAPI)
- API 负责 O*NET 查询、风险计算、RAG 检索、Agent SSE 生成
- Postgres+pgvector 存 assessments/agents/tools/embeddings/onet_cache
- Apify webhook 入库工具目录并生成 embedding（MVP 同步）

## GSTI 风险引擎分层
- `gsti_v0.py`: 关键词启发式（兼容回退）
- `onet_features.py`: O*NET 数值特征抽取与归一化（结构化主特征）
- `semantic_features.py`: 可选 embedding 语义密度特征（自动化密度/人类优势密度）
- `trend_adjustment.py`: 行业/工具/地区趋势修正（配置驱动）
- `calibration.py`: Logistic 校准层，将 raw risk 稳定映射到 0-1
- `gsti_v1.py`: 因子融合、分层 breakdown、confidence 计算
- `gsti_router.py`: `v0/v1/auto` 路由与 fallback

## GSTI v1 数据依赖与回退逻辑
1. 主路径：O*NET occupation detail + summary -> numeric features + tasks。
2. 可选增强：OpenAI embedding（需要 `openai_api_key`）。
3. 回退策略：`auto` 模式下若 O*NET numeric `<3` 且 task `<5`，回退 v0。
4. `v1` 强制模式：仍返回 v1，但 summary 标注“数据不足，退化运行”。

## Explainability 结构
v1 breakdown 为三层：
1. 因子（factor）
2. 子维度（subfactors）
3. 每项贡献和来源（source/raw_value/explanation）

同时输出：
- `summary`: 2-3 句解释主驱动因子与校准结果
- `suggested_focus`: 从低人类优势维度反推 3-6 条行动建议
