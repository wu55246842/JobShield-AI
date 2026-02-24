import json
import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.tables import Agent, Assessment, OnetCache, ToolCatalog, ToolEmbedding
from app.schemas.agent import AgentGenerateRequest, ApifyWebhookPayload
from app.schemas.rag import RagSearchRequest, RagSearchResponse
from app.schemas.risk import RiskBreakdownItem, RiskEvaluateRequest, RiskEvaluateResponse
from app.services.agent import build_agent_config
from app.services.onet import OnetClient
from app.services.rag import embed_query, search_tools
from app.core.gsti_router import GSTIRouter
from app.utils.auth import require_ingest_api_key

router = APIRouter()
logger = logging.getLogger(__name__)
onet_client = OnetClient()
gsti_router = GSTIRouter()


def err(code: str, message: str, details: dict | None = None):
    return {"error": {"code": code, "message": message, "details": details}}


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/onet/occupation/search")
async def onet_search(q: str):
    try:
        return await onet_client.get("online/search", {"keyword": q})
    except Exception as e:
        raise HTTPException(502, detail=err("ONET_ERROR", "Failed querying O*NET", {"reason": str(e)}))


@router.get("/onet/occupation/{code}")
async def onet_occupation(code: str, db: AsyncSession = Depends(get_db)):
    cached = (await db.execute(select(OnetCache).where(OnetCache.occupation_code == code))).scalar_one_or_none()
    if cached:
        return cached.payload
    payload = await onet_client.get(f"online/occupations/{code}")
    db.add(OnetCache(occupation_code=code, payload=payload))
    await db.commit()
    return payload


@router.get("/onet/occupation/{code}/tasks")
async def onet_tasks(code: str):
    return await onet_client.get(f"online/occupations/{code}/summary")


@router.post("/risk/evaluate", response_model=RiskEvaluateResponse)
async def risk_evaluate(body: RiskEvaluateRequest, db: AsyncSession = Depends(get_db)):
    tasks: list[str] = []
    onet_payload: dict = {}
    if body.occupation_code:
        try:
            summary_payload = await onet_client.get(f"online/occupations/{body.occupation_code}/summary")
            tasks = [t.get("task", "") for t in summary_payload.get("task_statements", []) if t.get("task")]
            onet_payload["summary"] = summary_payload
        except Exception:
            tasks = body.user_inputs.tasks_preference

        try:
            detail_payload = await onet_client.get(f"online/occupations/{body.occupation_code}")
            onet_payload["detail"] = detail_payload
        except Exception:
            pass

    if not tasks:
        tasks = body.user_inputs.tasks_preference

    result = gsti_router.evaluate(
        tasks=tasks,
        onet_payload=onet_payload,
        model_version=body.model_version,
        context={
            "industry": body.user_inputs.industry,
            "region": body.user_inputs.region,
            "selected_tools": body.user_inputs.selected_tools,
            "occupation_code": body.occupation_code,
            "occupation_title": body.occupation_title,
        },
    )

    score = result["score"]
    summary = result["summary"]
    breakdown = [RiskBreakdownItem(**item) for item in result["breakdown"]]
    assessment = Assessment(
        session_id=body.session_id,
        occupation_code=body.occupation_code,
        occupation_title=body.occupation_title,
        input_payload=body.model_dump(),
        output_summary=summary,
        risk_score=score,
    )
    db.add(assessment)
    await db.commit()
    await db.refresh(assessment)
    return RiskEvaluateResponse(
        score=score,
        confidence=result.get("confidence"),
        model_version=result.get("model_version"),
        breakdown=breakdown,
        summary=summary,
        suggested_focus=result["suggested_focus"],
        assessment_id=assessment.id,
    )


@router.post("/rag/tools/search", response_model=RagSearchResponse)
async def rag_tools_search(body: RagSearchRequest, db: AsyncSession = Depends(get_db)):
    try:
        items = await search_tools(db, body.query, body.top_k, body.filters.model_dump() if body.filters else None)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=err("EMBEDDING_CONFIG_ERROR", str(e)))
    return RagSearchResponse(results=items)


@router.post("/agent/generate")
async def agent_generate(body: AgentGenerateRequest, db: AsyncSession = Depends(get_db)):
    request_id = str(uuid.uuid4())

    async def stream():
        def pack(event: str, data: dict) -> str:
            return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

        yield pack("step", {"name": "fetch_context", "status": "start"})
        tools = []
        if body.selected_tools:
            rows = (await db.execute(select(ToolCatalog).where(ToolCatalog.id.in_(body.selected_tools)))).scalars().all()
            tools = [{"name": r.name, "url": r.url} for r in rows]
        yield pack("step", {"name": "fetch_context", "status": "end", "meta": {"tools": len(tools)}})
        yield pack("step", {"name": "compose_agent", "status": "start"})
        yield pack("delta", {"type": "text", "content": "正在生成配置说明…"})

        config = build_agent_config(body.user_goal, tools, body.risk_score)
        explanation = "已基于风险分与工具偏好生成可执行 Agent 配置。"
        agent = Agent(assessment_id=body.assessment_id, config=config.model_dump(), explanation=explanation)
        db.add(agent)
        await db.commit()
        await db.refresh(agent)

        yield pack("step", {"name": "compose_agent", "status": "end"})
        yield pack("result", {"agent_config": config.model_dump(), "explanation": explanation, "next_actions": ["导出JSON", "执行首周工作流"], "agent_id": agent.id, "request_id": request_id})

    return StreamingResponse(stream(), media_type="text/event-stream")


@router.post("/ingest/apify/webhook", dependencies=[Depends(require_ingest_api_key)])
async def ingest_apify(body: ApifyWebhookPayload, db: AsyncSession = Depends(get_db)):
    for item in body.items:
        existing = (await db.execute(select(ToolCatalog).where(ToolCatalog.url == item.url))).scalar_one_or_none()
        if existing:
            existing.name = item.name
            existing.description = item.description
            existing.tags = item.tags
            existing.raw_payload = item.raw_payload
            tool = existing
        else:
            tool = ToolCatalog(**item.model_dump())
            db.add(tool)
            await db.flush()

        try:
            emb = await embed_query(f"{item.name}\n{item.description}\n{' '.join(item.tags)}")
            emb_row = (await db.execute(select(ToolEmbedding).where(ToolEmbedding.tool_id == tool.id))).scalar_one_or_none()
            if emb_row:
                emb_row.embedding = emb
                emb_row.model = "text-embedding-3-small"
            else:
                db.add(ToolEmbedding(tool_id=tool.id, embedding=emb, model="text-embedding-3-small"))
        except ValueError:
            logger.warning("Embedding skipped due to missing key", extra={"request_id": "system"})

    await db.commit()
    return {"status": "ok", "count": len(body.items), "todo": "move embedding generation to async queue for scale"}
