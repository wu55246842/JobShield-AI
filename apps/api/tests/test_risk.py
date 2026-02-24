from app.services.risk import evaluate_risk_v0


def test_risk_v0_routine_higher_score():
    score, breakdown, _, _ = evaluate_risk_v0(
        ["Perform routine data entry in standardized format"],
        {"tasks_preference": ["repetitive"]},
    )
    assert score > 60
    assert any(item.factor == "routine_structured" for item in breakdown)
