# JobShield AI

全栈 MVP：职业替代风险评估 + AI Agent 定制。

## Monorepo 结构
- `apps/web` Next.js 14 App Router 前端
- `apps/api` FastAPI 后端（SSE + OpenAPI）
- `packages/shared` 共享占位
- `docker/docker-compose.yml` 本地一键启动
- `docs/*` 设计与部署文档

## 本地运行（Docker 推荐）
1. 复制环境变量模板：
   - `cp apps/api/.env.example apps/api/.env`
   - `cp apps/web/.env.example apps/web/.env.local`
2. 可选配置：`OPENAI_API_KEY`、`ONET_USERNAME`、`ONET_PASSWORD`
3. 启动：
   - `cd docker && docker compose up --build`
4. 访问：
   - Web: `http://localhost:3000`
   - API docs: `http://localhost:8000/docs`

## 无 Docker 运行
- API:
  - `cd apps/api && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && uvicorn app.main:app --reload`
- Web:
  - `cd apps/web && npm install && npm run dev`

## 端到端流程示例（curl）
1) 评估风险
```bash
curl -X POST http://localhost:8000/risk/evaluate \
  -H 'content-type: application/json' \
  -d '{"occupation_code":"15-1252.00","occupation_title":"Software Developer","session_id":"demo","user_inputs":{"skills":["python"],"tasks_preference":["creative"]}}'
```

2) 搜索工具（需 OPENAI_API_KEY 且有 embeddings）
```bash
curl -X POST http://localhost:8000/rag/tools/search \
  -H 'content-type: application/json' \
  -d '{"query":"AI coding assistant","top_k":5}'
```

3) 流式生成 Agent
```bash
curl -N -X POST http://localhost:8000/agent/generate \
  -H 'content-type: application/json' \
  -d '{"user_goal":"提高就业韧性","risk_score":62.1}'
```
