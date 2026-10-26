"""A small dbt-style warehouse: raw-ish staging tables, and a single
denormalized mart table built from them via a real SQL join -- run once by
this code, not by the NL2SQL layer, which only ever queries the finished
mart (see nl2sql.py's docstring for why).
"""
from __future__ import annotations

import sqlite3

from analyticscopilot.synthetic_data import generate_users, generate_verifications

CREATE_STAGING_SQL = """
CREATE TABLE stg_users (
    user_id INTEGER PRIMARY KEY,
    email_domain TEXT NOT NULL,
    organization TEXT NOT NULL,
    signup_date TEXT NOT NULL
);

CREATE TABLE stg_verifications (
    verification_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    method TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""

CREATE_MART_SQL = """
CREATE TABLE mart_verifications AS
SELECT
    v.verification_id,
    v.user_id,
    u.email_domain,
    u.organization,
    v.method,
    v.status,
    v.created_at,
    u.signup_date
FROM stg_verifications v
JOIN stg_users u ON v.user_id = u.user_id;
"""


def build_warehouse(n_users: int = 300, seed: int | None = 0) -> sqlite3.Connection:
    """Build an in-memory SQLite warehouse: staging tables loaded from
    synthetic data, then a mart table built from them via a real join."""
    conn = sqlite3.connect(":memory:")
    conn.executescript(CREATE_STAGING_SQL)

    users = generate_users(n=n_users, seed=seed)
    verifications = generate_verifications(users, seed=seed)

    conn.executemany(
        "INSERT INTO stg_users VALUES (?, ?, ?, ?)",
        [(u.user_id, u.email_domain, u.organization, u.signup_date.isoformat()) for u in users],
    )
    conn.executemany(
        "INSERT INTO stg_verifications VALUES (?, ?, ?, ?, ?)",
        [(v.verification_id, v.user_id, v.method, v.status, v.created_at.isoformat()) for v in verifications],
    )
    conn.commit()

    rebuild_mart(conn)
    return conn


def rebuild_mart(conn: sqlite3.Connection) -> None:
    conn.execute("DROP TABLE IF EXISTS mart_verifications")
    conn.executescript(CREATE_MART_SQL)
    conn.commit()
