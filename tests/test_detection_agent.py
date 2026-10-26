from analyticscopilot.warehouse import build_warehouse, rebuild_mart
from analyticscopilot.detection_agent import run_all_checks, run_schema_driven_checks, check_mart_did_not_drop_rows


def test_clean_warehouse_has_no_issues():
    conn = build_warehouse(n_users=100, seed=0)
    assert run_all_checks(conn) == []


def test_catches_injected_null_value():
    conn = build_warehouse(n_users=50, seed=1)
    conn.execute("UPDATE mart_verifications SET method = NULL WHERE verification_id = (SELECT MIN(verification_id) FROM mart_verifications)")
    issues = run_schema_driven_checks(conn)
    assert any(i.check_name == "not_null" and "method" in i.message for i in issues)


def test_catches_duplicate_primary_key():
    conn = build_warehouse(n_users=50, seed=2)
    row = conn.execute("SELECT * FROM mart_verifications LIMIT 1").fetchone()
    conn.execute("INSERT INTO mart_verifications VALUES (?, ?, ?, ?, ?, ?, ?, ?)", row)
    issues = run_schema_driven_checks(conn)
    assert any(i.check_name == "unique" and "verification_id" in i.message for i in issues)


def test_catches_unexpected_status_value():
    conn = build_warehouse(n_users=50, seed=3)
    conn.execute("UPDATE mart_verifications SET status = 'bogus_status' WHERE verification_id = (SELECT MIN(verification_id) FROM mart_verifications)")
    issues = run_schema_driven_checks(conn)
    assert any(i.check_name == "accepted_values" and "status" in i.message for i in issues)


def test_catches_mart_dropping_rows_on_orphaned_verification():
    conn = build_warehouse(n_users=50, seed=4)
    max_id = conn.execute("SELECT MAX(verification_id) FROM stg_verifications").fetchone()[0]
    conn.execute(
        "INSERT INTO stg_verifications VALUES (?, ?, ?, ?, ?)",
        (max_id + 1, 999999, "sms_otp", "verified", "2026-01-01"),
    )
    rebuild_mart(conn)
    issue = check_mart_did_not_drop_rows(conn)
    assert issue is not None
    assert "fewer row" in issue.message
