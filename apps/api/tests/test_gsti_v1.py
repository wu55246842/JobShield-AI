from app.core.calibration import calibrate
from app.core.gsti_router import GSTIRouter
from app.core.gsti_v1 import GSTIv1Engine
from app.core.trend_adjustment import compute_trend_modifier


def _payload_high_routine():
    return {
        "detail": {
            "work_context": [
                {"name": "Structured versus Unstructured Work", "value": 90, "scale": {"min": 0, "max": 100}},
                {"name": "Importance of Being Exact or Accurate", "value": 85, "scale": {"min": 0, "max": 100}},
            ],
            "work_activities": [
                {"name": "Processing Information", "value": 88, "scale": {"min": 0, "max": 100}},
                {"name": "Interacting With Computers", "value": 90, "scale": {"min": 0, "max": 100}},
                {"name": "Thinking Creatively", "value": 25, "scale": {"min": 0, "max": 100}},
                {"name": "Making Decisions and Solving Problems", "value": 40, "scale": {"min": 0, "max": 100}},
            ],
            "skills": [{"name": "Service Orientation", "value": 20, "scale": {"min": 0, "max": 100}}],
        }
    }


def _payload_high_empathy():
    return {
        "detail": {
            "work_activities": [
                {"name": "Assisting and Caring for Others", "value": 95, "scale": {"min": 0, "max": 100}},
                {"name": "Thinking Creatively", "value": 70, "scale": {"min": 0, "max": 100}},
                {"name": "Making Decisions and Solving Problems", "value": 75, "scale": {"min": 0, "max": 100}},
                {"name": "Processing Information", "value": 45, "scale": {"min": 0, "max": 100}},
            ],
            "work_context": [
                {"name": "Responsibility for Outcomes and Results", "value": 82, "scale": {"min": 0, "max": 100}},
                {"name": "Spend Time Standing", "value": 55, "scale": {"min": 0, "max": 100}},
            ],
        }
    }


def test_gsti_v1_high_routine_job():
    engine = GSTIv1Engine()
    tasks = ["Enter standardized records", "Compile routine transaction reports"]
    result = engine.evaluate(tasks=tasks, onet_payload=_payload_high_routine(), context={"industry": "data entry"})

    factors = {item["factor"]: item for item in result["breakdown"]}
    assert factors["automation_susceptibility"]["value"] > 0.7
    assert result["score"] > 60


def test_gsti_v1_high_empathy_job():
    engine = GSTIv1Engine()
    tasks = ["Counsel patients", "Coordinate family care plans", "Support emotional recovery"]
    result = engine.evaluate(tasks=tasks, onet_payload=_payload_high_empathy(), context={"industry": "healthcare"})

    factors = {item["factor"]: item for item in result["breakdown"]}
    assert factors["human_advantage"]["value"] > 0.7
    assert result["score"] < 55


def test_gsti_v1_missing_onet_fallback():
    router = GSTIRouter()
    result = router.evaluate(tasks=["do work"], onet_payload={}, model_version="auto", context={})
    assert result["model_version"] == "v0"


def test_calibration_monotonic():
    values = [calibrate(v) for v in [0.1, 0.3, 0.5, 0.7, 0.9]]
    assert values == sorted(values)


def test_trend_modifier_bounds():
    result = compute_trend_modifier(industry="data entry", region="eu", selected_tools=[str(i) for i in range(20)])
    assert -0.15 <= result["value"] <= 0.15
