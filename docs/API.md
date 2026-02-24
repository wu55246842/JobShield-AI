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
