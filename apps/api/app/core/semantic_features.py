from __future__ import annotations

import math
from statistics import mean

from openai import OpenAI

from app.core.config import settings


AUTOMATION_ANCHOR = (
    "Highly repeatable, rules-based, predictable tasks with standard procedures, "
    "structured data handling, deterministic workflow steps, and low ambiguity."
)
HUMAN_ANCHOR = (
    "Tasks requiring empathy, trust building, negotiation, nuanced judgment, "
    "creative synthesis, leadership, and handling ambiguous social contexts."
)


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _to_01(sim: float) -> float:
    return max(0.0, min(1.0, (sim + 1.0) / 2.0))


def extract_semantic_features(tasks: list[str], model: str | None = None) -> dict | None:
    if not tasks or len(tasks) < 2:
        return None
    if not settings.openai_api_key:
        return None

    embed_model = model or settings.embedding_model
    client = OpenAI(api_key=settings.openai_api_key)

    try:
        anchor_resp = client.embeddings.create(model=embed_model, input=[AUTOMATION_ANCHOR, HUMAN_ANCHOR])
        task_resp = client.embeddings.create(model=embed_model, input=tasks)
    except Exception:
        return None

    auto_emb = anchor_resp.data[0].embedding
    human_emb = anchor_resp.data[1].embedding
    task_embs = [row.embedding for row in task_resp.data]

    auto_sims = [_cosine(emb, auto_emb) for emb in task_embs]
    human_sims = [_cosine(emb, human_emb) for emb in task_embs]

    auto_mean = mean(auto_sims)
    human_mean = mean(human_sims)

    return {
        "automation_density": _to_01(auto_mean),
        "human_density": _to_01(human_mean),
        "task_count": len(tasks),
        "automation_similarity_mean": auto_mean,
        "human_similarity_mean": human_mean,
        "model": embed_model,
    }
