from app.services.rag import build_tools_filter_sql


def test_build_tools_filter_sql_with_filters():
    sql, params = build_tools_filter_sql({"source": "apify", "tags": ["automation"]})
    assert "tc.source = :source" in sql
    assert "tc.tags ?| :tags" in sql
    assert params["source"] == "apify"
