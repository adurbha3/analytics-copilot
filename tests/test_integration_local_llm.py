"""One true end-to-end test against the real local model, confirming NL2SQL
actually produces a correct, executable query for a simple single-table
question -- not just that mocked pieces connect. Skipped if the model
cannot be downloaded in this environment."""
import pytest

from analyticscopilot.warehouse import build_warehouse


@pytest.fixture(scope="module")
def real_llm():
    try:
        from analyticscopilot.llm import LocalLLM

        llm = LocalLLM()
        llm.generate("Say hi.", max_new_tokens=5)
        return llm
    except Exception as e:
        pytest.skip(f"local model unavailable in this environment: {e}")


def test_real_model_answers_a_simple_count_question(real_llm):
    from analyticscopilot.nl2sql import ask

    conn = build_warehouse(n_users=100, seed=0)
    expected = conn.execute("SELECT COUNT(*) FROM mart_verifications WHERE status = 'failed'").fetchone()[0]

    result = ask("How many verifications have status failed?", conn, real_llm)
    assert result.query_result.success
    assert result.query_result.rows[0][0] == expected
