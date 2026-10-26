from analyticscopilot.warehouse import build_warehouse, rebuild_mart


def test_staging_tables_are_populated():
    conn = build_warehouse(n_users=50, seed=0)
    users = conn.execute("SELECT COUNT(*) FROM stg_users").fetchone()[0]
    verifications = conn.execute("SELECT COUNT(*) FROM stg_verifications").fetchone()[0]
    assert users == 50
    assert verifications > 0


def test_mart_joins_staging_tables_correctly():
    conn = build_warehouse(n_users=50, seed=1)
    row = conn.execute("SELECT * FROM mart_verifications LIMIT 1").fetchone()
    columns = [d[0] for d in conn.execute("SELECT * FROM mart_verifications LIMIT 1").description]
    assert columns == [
        "verification_id", "user_id", "email_domain", "organization",
        "method", "status", "created_at", "signup_date",
    ]
    assert row is not None


def test_mart_row_count_matches_staging_when_no_orphans():
    conn = build_warehouse(n_users=100, seed=2)
    staging = conn.execute("SELECT COUNT(*) FROM stg_verifications").fetchone()[0]
    mart = conn.execute("SELECT COUNT(*) FROM mart_verifications").fetchone()[0]
    assert staging == mart


def test_rebuild_mart_is_idempotent():
    conn = build_warehouse(n_users=20, seed=3)
    before = conn.execute("SELECT COUNT(*) FROM mart_verifications").fetchone()[0]
    rebuild_mart(conn)
    after = conn.execute("SELECT COUNT(*) FROM mart_verifications").fetchone()[0]
    assert before == after


def test_reproducible_with_same_seed():
    a = build_warehouse(n_users=30, seed=42)
    b = build_warehouse(n_users=30, seed=42)
    a_rows = a.execute("SELECT * FROM mart_verifications ORDER BY verification_id").fetchall()
    b_rows = b.execute("SELECT * FROM mart_verifications ORDER BY verification_id").fetchall()
    assert a_rows == b_rows
