#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import csv
import json
import sys
from itertools import product
from pathlib import Path
from statistics import mean

REPO_ROOT = Path(__file__).resolve().parents[1]
API_ROOT = REPO_ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.gsti_router import GSTIRouter
from app.models.tables import Assessment, Label, OnetCache


def candidate_subweights() -> list[dict[str, float]]:
    base = [0.15, 0.2, 0.25]
    cands = []
    for a, i, d in product(base, base, base):
        if abs((a + i + d) - 0.8) < 1e-9:
            cands.append(
                {
                    "routine_structured": a / 0.8,
                    "information_processing": i / 0.8,
                    "automation_density": d / 0.8,
                }
            )
    return cands


async def load_samples(db: AsyncSession):
    rows = (
        await db.execute(
            select(Assessment, Label)
            .join(Label, Label.assessment_id == Assessment.id)
            .where(Label.risk_score_label.is_not(None))
        )
    ).all()
    samples = []
    for assessment, label in rows:
        payload = assessment.input_payload or {}
        user_inputs = payload.get("user_inputs", {})
        tasks = user_inputs.get("tasks_preference") or []
        onet_payload = {}
        if assessment.occupation_code:
            cached = (await db.execute(select(OnetCache).where(OnetCache.occupation_code == assessment.occupation_code))).scalar_one_or_none()
            if cached:
                onet_payload = cached.payload
        samples.append(
            {
                "assessment_id": assessment.id,
                "tasks": tasks,
                "onet_payload": onet_payload,
                "context": {
                    "industry": user_inputs.get("industry"),
                    "region": user_inputs.get("region"),
                    "selected_tools": user_inputs.get("selected_tools") or [],
                    "occupation_code": assessment.occupation_code,
                    "occupation_title": assessment.occupation_title,
                },
                "label": float(label.risk_score_label),
            }
        )
    return samples


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsn", required=True, help="Async SQLAlchemy DSN, e.g. postgresql+asyncpg://...")
    args = parser.parse_args()

    engine = create_async_engine(args.dsn)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as db:
        samples = await load_samples(db)

    if len(samples) < 20:
        print(f"[WARN] labeled samples only {len(samples)} (<20), tuning may be unstable")

    k_values = [4, 6, 8, 10, 12]
    x0_values = [0.45, 0.5, 0.55]
    subweight_candidates = candidate_subweights()

    results = []
    for k, x0, auto_subweights in product(k_values, x0_values, subweight_candidates):
        params = {
            "v1": {
                "calibration": {"k": k, "x0": x0},
                "automation_subweights": auto_subweights,
            }
        }
        router = GSTIRouter.from_params(params)
        abs_errors = []
        for sample in samples:
            result = router.evaluate(
                tasks=sample["tasks"],
                onet_payload=sample["onet_payload"],
                model_version="v1",
                context=sample["context"],
            )
            abs_errors.append(abs(result["score"] - sample["label"]))
        mae = mean(abs_errors) if abs_errors else 0.0
        results.append({"k": k, "x0": x0, **auto_subweights, "mae": round(mae, 4)})

    results.sort(key=lambda x: x["mae"])
    best = results[0] if results else {"k": 8, "x0": 0.5, "routine_structured": 0.45, "information_processing": 0.35, "automation_density": 0.2, "mae": None}
    best_params = {
        "v1": {
            "calibration": {"k": best["k"], "x0": best["x0"]},
            "automation_subweights": {
                "routine_structured": best["routine_structured"],
                "information_processing": best["information_processing"],
                "automation_density": best["automation_density"],
            },
        }
    }

    Path("output").mkdir(exist_ok=True)
    with Path("output/tuning_results.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["k", "x0", "routine_structured", "information_processing", "automation_density", "mae"])
        writer.writeheader()
        writer.writerows(results)

    with Path("output/best_params.json").open("w", encoding="utf-8") as f:
        json.dump(best_params, f, ensure_ascii=False, indent=2)

    print("Best params:")
    print(json.dumps(best_params, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
