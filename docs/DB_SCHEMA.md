# DB_SCHEMA
核心表：
- assessments：评估历史（输入/输出摘要/分数）
- agents：可回放 Agent 配置 JSON
- tools_catalog：工具目录
- tool_embeddings：向量（1536）
- onet_cache：O*NET 缓存
- labels：人工标注/校正（risk label、confidence、factor overrides、notes）
- experiments：实验配置快照（model_version + params）
- experiment_assignments：A/B sticky 分流记录（user_key -> variant）
- experiment_runs：实验运行输出快照（含 breakdown/raw/calibrated）

索引：
- `idx_assessments_session_id`
- `idx_tools_catalog_source`
- `idx_tool_embeddings_hnsw`
- `idx_labels_assessment_id`
- `idx_experiment_runs_experiment_assessment`
- `idx_experiment_assignments_user_key`

向量索引：`hnsw (embedding vector_cosine_ops)`。
