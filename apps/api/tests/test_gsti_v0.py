from app.core.gsti_v0 import GSTIv0Engine


def test_accountant_high_information_processing():
    tasks = [
        "Analyze data and generate reports for monthly close.",
        "Prepare statements and compile information for audit records.",
        "Review forms and process data in standardized workflows.",
    ]
    engine = GSTIv0Engine()
    result = engine.calculate_risk(tasks)

    factors = {item["factor"]: item for item in result["breakdown"]}
    assert factors["information_processing"]["raw_value"] >= 0.66
    assert factors["routine_structured"]["raw_value"] >= 0.33
    assert result["score"] > 50
    assert "匹配关键词" in factors["information_processing"]["explanation"]


def test_nurse_high_empathy_reduces_risk():
    tasks = [
        "Counsel patients and provide emotional support to families.",
        "Advise clients and resolve conflict between care priorities.",
        "Coordinate patient care and mediate communication with physicians.",
    ]
    engine = GSTIv0Engine()
    result = engine.calculate_risk(tasks)

    factors = {item["factor"]: item for item in result["breakdown"]}
    assert factors["empathy_negotiation"]["raw_value"] >= 0.66
    assert factors["empathy_negotiation"]["direction"] == "negative"
    assert factors["empathy_negotiation"]["risk_contribution"] < 6


def test_mechanic_high_physical_reduces_risk():
    tasks = [
        "Repair engines and perform manual adjustment on site.",
        "Install replacement parts and conduct field inspection.",
        "Operate machinery on site and complete maintenance checks.",
    ]
    engine = GSTIv0Engine()
    result = engine.calculate_risk(tasks)

    factors = {item["factor"]: item for item in result["breakdown"]}
    assert factors["physical_field_work"]["raw_value"] >= 0.66
    assert factors["physical_field_work"]["direction"] == "negative"
    assert factors["physical_field_work"]["risk_contribution"] < 6
    assert 0.6 <= result["confidence"] <= 0.9
