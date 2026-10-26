from analyticscopilot.llm import StubLLM
from analyticscopilot.nl2sql import ask, _extract_sql
from analyticscopilot.warehouse import build_warehouse


def test_extract_sql_from_plain_response():
    assert _extract_sql("SELECT COUNT(*) FROM mart_verifications;") == "SELECT COUNT(*) FROM mart_verifications;"


def test_extract_sql_strips_code_fence_and_stray_text():
    raw = "Sure, here you go:\n```\nSELECT COUNT(*) FROM mart_verifications;\n```"
    assert _extract_sql(raw) == "SELECT COUNT(*) FROM mart_verifications;"


def test_ask_executes_valid_generated_sql():
    conn = build_warehouse(n_users=30, seed=0)
    llm = StubLLM(["SELECT COUNT(*) FROM mart_verifications"])
    result = ask("How many verifications are there?", conn, llm)
    assert result.query_result.success
    assert result.query_result.rows[0][0] > 0


def test_ask_reports_failure_for_unsafe_generated_sql():
    conn = build_warehouse(n_users=30, seed=0)
    llm = StubLLM(["DROP TABLE mart_verifications"])
    result = ask("Delete everything", conn, llm)
    assert not result.query_result.success


def test_ask_reports_failure_for_hallucinated_column():
    conn = build_warehouse(n_users=30, seed=0)
    llm = StubLLM(["SELECT made_up_column FROM mart_verifications"])
    result = ask("What is the made up thing?", conn, llm)
    assert not result.query_result.success
    assert "SQL error" in result.query_result.error
