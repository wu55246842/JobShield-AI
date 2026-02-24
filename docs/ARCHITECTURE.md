# ARCHITECTURE
- Web(Next.js) -> `/api/py/*` rewrite -> API(FastAPI)
- API 负责 O*NET 查询、风险计算、RAG 检索、Agent SSE 生成
- Postgres+pgvector 存 assessments/agents/tools/embeddings/onet_cache
- Apify webhook 入库工具目录并生成 embedding（MVP 同步）
