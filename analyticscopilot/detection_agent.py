"""A data-quality detection agent: runs schema-driven checks (null rates,
accepted values, duplicate keys) straight from the semantic layer's own
column metadata, plus a pipeline-level check that the mart build did not
silently drop rows during its join -- the kind of thing a dbt test suite
and a monitoring job would catch separately, run here as one pass.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from analyticscopilot.schema_catalog import CATALOG, TableSpec


@dataclass
class DataQualityIssue:
    check_name: str
    severity: str  # "error" or "warning"
    message: str


def _check_not_null(conn: sqlite3.Connection, table: TableSpec, column: str) -> DataQualityIssue | None:
    count = conn.execute(f"SELECT COUNT(*) FROM {table.name} WHERE {column} IS NULL").fetchone()[0]
    if count > 0:
        return DataQualityIssue("not_null", "error", f"{table.name}.{column} has {count} null value(s)")
    return None


def _check_unique(conn: sqlite3.Connection, table: TableSpec, column: str) -> DataQualityIssue | None:
    total = conn.execute(f"SELECT COUNT(*) FROM {table.name}").fetchone()[0]
    distinct = conn.execute(f"SELECT COUNT(DISTINCT {column}) FROM {table.name}").fetchone()[0]
    if total != distinct:
        return DataQualityIssue("unique", "error", f"{table.name}.{column} has {total - distinct} duplicate value(s)")
    return None


def _check_accepted_values(
    conn: sqlite3.Connection, table: TableSpec, column: str, allowed: list[str]
) -> DataQualityIssue | None:
    placeholders = ", ".join("?" for _ in allowed)
    query = f"SELECT DISTINCT {column} FROM {table.name} WHERE {column} NOT IN ({placeholders})"
    unexpected = [row[0] for row in conn.execute(query, allowed).fetchall()]
    if unexpected:
        return DataQualityIssue(
            "accepted_values", "error",
            f"{table.name}.{column} has unexpected value(s) not in {allowed}: {unexpected}",
        )
    return None


def run_schema_driven_checks(conn: sqlite3.Connection, catalog: dict[str, TableSpec] = CATALOG) -> list[DataQualityIssue]:
    """Walk every column's declared tests in the semantic layer and run the matching check."""
    issues = []
    for table in catalog.values():
        for column in table.columns:
            for test in column.tests:
                if test == "not_null":
                    issue = _check_not_null(conn, table, column.name)
                elif test == "unique":
                    issue = _check_unique(conn, table, column.name)
                elif test.startswith("accepted_values:"):
                    allowed = test.split(":", 1)[1].strip("[]").split(",")
                    issue = _check_accepted_values(conn, table, column.name, allowed)
                else:
                    issue = None
                if issue:
                    issues.append(issue)
    return issues


def check_mart_did_not_drop_rows(conn: sqlite3.Connection) -> DataQualityIssue | None:
    """The mart is built with an inner join; if a verification references a
    user_id missing from stg_users, that row is silently dropped from the
    mart. Catch that by comparing row counts instead of trusting the join
    was lossless."""
    staging_count = conn.execute("SELECT COUNT(*) FROM stg_verifications").fetchone()[0]
    mart_count = conn.execute("SELECT COUNT(*) FROM mart_verifications").fetchone()[0]
    if mart_count < staging_count:
        dropped = staging_count - mart_count
        return DataQualityIssue(
            "mart_row_count_match", "error",
            f"mart_verifications has {dropped} fewer row(s) than stg_verifications -- "
            f"likely verifications referencing a user_id missing from stg_users",
        )
    return None


def run_all_checks(conn: sqlite3.Connection, catalog: dict[str, TableSpec] = CATALOG) -> list[DataQualityIssue]:
    issues = run_schema_driven_checks(conn, catalog)
    pipeline_issue = check_mart_did_not_drop_rows(conn)
    if pipeline_issue:
        issues.append(pipeline_issue)
    return issues
