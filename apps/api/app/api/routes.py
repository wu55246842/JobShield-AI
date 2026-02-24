import hashlib
import json
import logging
import random
import uuid
from statistics import mean, median

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.gsti_router import GSTIRouter
from app.db.session import get_db
from app.models.tables import (
    Agent,
    Assessment,
    Experiment,
    ExperimentAssignment,
    ExperimentRun,
    Label,
    OnetCache,
    ToolCatalog,
    ToolEmbedding,
)
from app.schemas.admin import (
    CompareResponse,
    ExperimentAssignRequest,
    ExperimentAssignResponse,
    ExperimentCreateRequest,
    ExperimentMetricsResponse,
    ExperimentPatchRequest,
    ExperimentResponse,
    LabelCreateRequest,
    LabelResponse,
)
from app.schemas.agent import AgentGenerateRequest, ApifyWebhookPayload
from app.schemas.rag import RagSearchRequest, RagSearchResponse
from app.schemas.risk import RiskBreakdownItem, RiskEvaluateRequest, RiskEvaluateResponse
from app.services.agent import build_agent_config
from app.services.onet import OnetClient
from app.services.rag import embed_query, search_tools
from app.utils.auth import require_admin_api_key, require_ingest_api_key

router = APIRouter()
logger = logging.getLogger(__name__)
onet_client = OnetClient()


def err(code: str, message: str, details: dict | None = None):
    return {"error": {"code": code, "message": message, "details": details}}


def _spearman(x: list[float], y: list[float]) -> float | None:
    if len(x) < 2 or len(y) < 2:
        return None

    def rank(values: list[float]) -> list[int]:
        sorted_idx = sorted(range(len(values)), key=lambda i: values[i])
        ranks = [0] * len(values)
        for r, i in enumerate(sorted_idx, start=1):
            ranks[i] = r
        return ranks

    rx = rank(x)
    ry = rank(y)
    mx = mean(rx)
    my = mean(ry)
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    sx = sum((a - mx) ** 2 for a in rx) ** 0.5
    sy = sum((b - my) ** 2 for b in ry) ** 0.5
    if sx == 0 or sy == 0:
        return None
    return round(cov / (sx * sy), 4)


async def _resolve_experiment(db: AsyncSession, experiment_id: int | None) -> Experiment | None:
    if not experiment_id:
        return None
    exp = (await db.execute(select(Experiment).where(Experiment.id == experiment_id))).scalar_one_or_none()
    if not exp:
        raise HTTPException(404, detail="Experiment not found")
    return exp


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

    exp = await _resolve_experiment(db, body.experiment_id)
    gsti_router = GSTIRouter.from_params(exp.params if exp else None)
    eval_model_version = exp.model_version if exp else body.model_version
    variant = body.variant or "A"

    result = gsti_router.evaluate(
        tasks=tasks,
        onet_payload=onet_payload,
        model_version=eval_model_version,
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

    experiment_meta = None
    if exp:
        experiment_meta = {"id": exp.id, "name": exp.name, "variant": variant}
        db.add(
            ExperimentRun(
                experiment_id=exp.id,
                assessment_id=assessment.id,
                variant=variant,
                output={**result, "assessment_id": assessment.id, "experiment": experiment_meta},
            )
        )
        await db.commit()

    return RiskEvaluateResponse(
        score=score,
        confidence=result.get("confidence"),
        model_version=result.get("model_version"),
        breakdown=breakdown,
        summary=summary,
        suggested_focus=result["suggested_focus"],
        assessment_id=assessment.id,
        experiment=experiment_meta,
    )


@router.post("/experiments/assign", response_model=ExperimentAssignResponse)
async def assign_experiment(body: ExperimentAssignRequest, db: AsyncSession = Depends(get_db)):
    exp = (await db.execute(select(Experiment).where(Experiment.name == body.experiment_name, Experiment.is_active.is_(True)))).scalar_one_or_none()
    if not exp:
        raise HTTPException(404, detail="Active experiment not found")

    existing = (
        await db.execute(
            select(ExperimentAssignment).where(
                ExperimentAssignment.user_key == body.user_key,
                ExperimentAssignment.experiment_id == exp.id,
            )
        )
    ).scalar_one_or_none()
    if existing:
        return ExperimentAssignResponse(experiment_id=exp.id, variant=existing.variant)

    seed_hex = hashlib.sha256(f"{body.user_key}:{exp.id}".encode()).hexdigest()[:8]
    seeded = random.Random(int(seed_hex, 16))
    variant = "A" if seeded.random() < 0.5 else "B"
    db.add(ExperimentAssignment(user_key=body.user_key, experiment_id=exp.id, variant=variant))
    await db.commit()
    return ExperimentAssignResponse(experiment_id=exp.id, variant=variant)


@router.post("/admin/labels", response_model=LabelResponse, dependencies=[Depends(require_admin_api_key)])
async def create_label(body: LabelCreateRequest, db: AsyncSession = Depends(get_db)):
    label = Label(**body.model_dump())
    db.add(label)
    await db.commit()
    await db.refresh(label)
    return label


@router.get("/admin/labels", response_model=list[LabelResponse], dependencies=[Depends(require_admin_api_key)])
async def list_labels(assessment_id: int, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Label).where(Label.assessment_id == assessment_id).order_by(Label.created_at.desc()))).scalars().all()
    return list(rows)


@router.get("/admin/labels/recent", response_model=list[LabelResponse], dependencies=[Depends(require_admin_api_key)])
async def recent_labels(limit: int = 20, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Label).order_by(Label.created_at.desc()).limit(limit))).scalars().all()
    return list(rows)


@router.post("/admin/experiments", response_model=ExperimentResponse, dependencies=[Depends(require_admin_api_key)])
async def create_experiment(body: ExperimentCreateRequest, db: AsyncSession = Depends(get_db)):
    exp = Experiment(**body.model_dump())
    db.add(exp)
    await db.commit()
    await db.refresh(exp)
    return exp


@router.get("/admin/experiments", dependencies=[Depends(require_admin_api_key)])
async def list_experiments(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Experiment).order_by(Experiment.created_at.desc()))).scalars().all()
    data = []
    for row in rows:
        sample_count = (await db.execute(select(func.count(ExperimentRun.id)).where(ExperimentRun.experiment_id == row.id))).scalar_one()
        data.append({
            "id": row.id,
            "name": row.name,
            "description": row.description,
            "model_version": row.model_version,
            "params": row.params,
            "is_active": row.is_active,
            "created_at": row.created_at,
            "sample_count": sample_count,
        })
    return data


@router.patch("/admin/experiments/{experiment_id}", response_model=ExperimentResponse, dependencies=[Depends(require_admin_api_key)])
async def patch_experiment(experiment_id: int, body: ExperimentPatchRequest, db: AsyncSession = Depends(get_db)):
    exp = await _resolve_experiment(db, experiment_id)
    payload = body.model_dump(exclude_unset=True)
    for key, value in payload.items():
        setattr(exp, key, value)
    await db.commit()
    await db.refresh(exp)
    return exp


@router.get("/admin/experiments/{experiment_id}/runs", dependencies=[Depends(require_admin_api_key)])
async def list_experiment_runs(experiment_id: int, limit: int = 20, db: AsyncSession = Depends(get_db)):
    _ = await _resolve_experiment(db, experiment_id)
    runs = (await db.execute(select(ExperimentRun).where(ExperimentRun.experiment_id == experiment_id).order_by(ExperimentRun.created_at.desc()).limit(limit))).scalars().all()
    return [
        {
            "id": r.id,
            "assessment_id": r.assessment_id,
            "variant": r.variant,
            "score": r.output.get("score"),
            "confidence": r.output.get("confidence"),
            "created_at": r.created_at,
            "output": r.output,
        }
        for r in runs
    ]


@router.get("/admin/experiments/{experiment_id}/metrics", response_model=ExperimentMetricsResponse, dependencies=[Depends(require_admin_api_key)])
async def experiment_metrics(experiment_id: int, db: AsyncSession = Depends(get_db)):
    _ = await _resolve_experiment(db, experiment_id)
    runs = (await db.execute(select(ExperimentRun).where(ExperimentRun.experiment_id == experiment_id))).scalars().all()
    by_variant: dict[str, dict] = {}
    errors: list[float] = []
    pred_vals: list[float] = []
    label_vals: list[float] = []
    scores = [float(r.output.get("score", 0.0)) for r in runs]

    for r in runs:
        by_variant.setdefault(r.variant, {"count": 0, "scores": []})
        by_variant[r.variant]["count"] += 1
        by_variant[r.variant]["scores"].append(float(r.output.get("score", 0.0)))

        label = (await db.execute(select(Label).where(Label.assessment_id == r.assessment_id).order_by(Label.created_at.desc()))).scalar_one_or_none()
        if label and label.risk_score_label is not None:
            pred = float(r.output.get("score", 0.0))
            lab = float(label.risk_score_label)
            errors.append(abs(pred - lab))
            pred_vals.append(pred)
            label_vals.append(lab)

    for v in by_variant.values():
        sc = v.pop("scores")
        v["mean"] = round(mean(sc), 4) if sc else None
        v["median"] = round(median(sc), 4) if sc else None

    dist = {
        "mean": round(mean(scores), 4) if scores else None,
        "median": round(median(scores), 4) if scores else None,
        "p25": round(sorted(scores)[int(len(scores) * 0.25)], 4) if scores else None,
        "p75": round(sorted(scores)[int(len(scores) * 0.75)], 4) if scores else None,
    }

    return ExperimentMetricsResponse(
        experiment_id=experiment_id,
        sample_count=len(runs),
        by_variant=by_variant,
        error_metrics={
            "mae": round(mean(errors), 4) if errors else None,
            "spearman": _spearman(pred_vals, label_vals),
            "labeled_count": len(errors),
        },
        score_distribution=dist,
    )


@router.get("/admin/assessments/{assessment_id}/compare", response_model=CompareResponse, dependencies=[Depends(require_admin_api_key)])
async def compare_assessment(assessment_id: int, models: str = "v0,v1", experiment_id: int | None = None, db: AsyncSession = Depends(get_db)):
    assessment = (await db.execute(select(Assessment).where(Assessment.id == assessment_id))).scalar_one_or_none()
    if not assessment:
        raise HTTPException(404, detail="Assessment not found")

    body = assessment.input_payload
    tasks = body.get("user_inputs", {}).get("tasks_preference", [])
    onet_payload = {}
    if assessment.occupation_code:
        cached = (await db.execute(select(OnetCache).where(OnetCache.occupation_code == assessment.occupation_code))).scalar_one_or_none()
        if cached:
            onet_payload = cached.payload

    exp = await _resolve_experiment(db, experiment_id) if experiment_id else None
    gsti_router = GSTIRouter.from_params(exp.params if exp else None)
    outputs = {}
    for model in [m.strip() for m in models.split(",") if m.strip()]:
        outputs[model] = gsti_router.evaluate(
            tasks=tasks,
            onet_payload=onet_payload,
            model_version=model,
            context={
                "industry": body.get("user_inputs", {}).get("industry"),
                "region": body.get("user_inputs", {}).get("region"),
                "selected_tools": body.get("user_inputs", {}).get("selected_tools", []),
                "occupation_code": assessment.occupation_code,
                "occupation_title": assessment.occupation_title,
            },
        )

    return CompareResponse(assessment_id=assessment_id, outputs=outputs)


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
