# DB_SCHEMA
核心表：
- assessments：评估历史（输入/输出摘要/分数）
- agents：可回放 Agent 配置 JSON
- tools_catalog：工具目录
- tool_embeddings：向量（1536）
- onet_cache：O*NET 缓存

向量索引：`hnsw (embedding vector_cosine_ops)`。
