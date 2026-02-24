from openai import AsyncOpenAI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings


def build_tools_filter_sql(filters: dict | None) -> tuple[str, dict]:
    clauses = []
    params: dict = {}
    if not filters:
        return "", params
    if filters.get("source"):
        clauses.append("tc.source = :source")
        params["source"] = filters["source"]
    if filters.get("tags"):
        clauses.append("tc.tags ?| :tags")
        params["tags"] = filters["tags"]
    return (" AND " + " AND ".join(clauses)) if clauses else "", params


async def embed_query(query: str) -> list[float]:
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is required for embeddings")
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    result = await client.embeddings.create(model=settings.embedding_model, input=query)
    return result.data[0].embedding


async def search_tools(db: AsyncSession, query: str, top_k: int, filters: dict | None = None) -> list[dict]:
    embedding = await embed_query(query)
    where_sql, filter_params = build_tools_filter_sql(filters)
    sql = text(
        f"""
        SELECT tc.id AS tool_id, tc.name, tc.description, tc.url, tc.tags,
               1 - (te.embedding <=> CAST(:embedding AS vector)) AS score
        FROM tool_embeddings te
        JOIN tools_catalog tc ON tc.id = te.tool_id
        WHERE 1=1 {where_sql}
        ORDER BY te.embedding <=> CAST(:embedding AS vector)
        LIMIT :top_k
        """
    )
    params = {"embedding": embedding, "top_k": top_k, **filter_params}
    rows = (await db.execute(sql, params)).mappings().all()
    return [dict(r) for r in rows]
