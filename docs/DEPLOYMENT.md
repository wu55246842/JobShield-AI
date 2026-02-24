# DEPLOYMENT
## API
- Dockerfile: `apps/api/Dockerfile`
- 部署到 Render/Fly.io/自建：暴露 `8000`，配置 `DATABASE_URL`、`OPENAI_API_KEY` 等。

## Web (Vercel)
- Root: `apps/web`
- Env: `NEXT_PUBLIC_API_BASE_URL=https://<api-domain>`
- 已通过 `next.config.js` rewrites 代理 `/api/py/*`。

## CORS
- 本地允许 `localhost:3000`
- 生产建议仅允许 Vercel 域名并继续使用 rewrite 降低跨域复杂度。
