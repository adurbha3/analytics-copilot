from analyticscopilot.sql_validation import is_single_select_statement, validate_and_execute
from analyticscopilot.warehouse import build_warehouse


def test_accepts_plain_select():
    assert is_single_select_statement("SELECT * FROM mart_verifications")


def test_rejects_non_select_statements():
    assert not is_single_select_statement("DROP TABLE mart_verifications")
    assert not is_single_select_statement("DELETE FROM mart_verifications")
    assert not is_single_select_statement("UPDATE mart_verifications SET status='verified'")


def test_rejects_stacked_statements():
    assert not is_single_select_statement("SELECT 1; DROP TABLE mart_verifications;")


def test_rejects_select_with_embedded_forbidden_keyword():
    # a SELECT that smuggles a second statement via a semicolon is still caught
    assert not is_single_select_statement("SELECT * FROM mart_verifications; DELETE FROM mart_verifications;")


def test_validate_and_execute_runs_valid_query():
    conn = build_warehouse(n_users=20, seed=0)
    result = validate_and_execute("SELECT COUNT(*) FROM mart_verifications", conn)
    assert result.success
    assert result.columns == ["COUNT(*)"]
    assert len(result.rows) == 1


def test_validate_and_execute_rejects_unsafe_query():
    conn = build_warehouse(n_users=20, seed=0)
    result = validate_and_execute("DROP TABLE mart_verifications", conn)
    assert not result.success
    assert "rejected" in result.error


def test_validate_and_execute_reports_hallucinated_column_cleanly():
    conn = build_warehouse(n_users=20, seed=0)
    result = validate_and_execute("SELECT nonexistent_column FROM mart_verifications", conn)
    assert not result.success
    assert "SQL error" in result.error
