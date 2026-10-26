"""Never trust generated SQL blindly: reject anything that is not a single
read-only SELECT before it reaches the database, then let SQLite's own
schema enforcement catch a hallucinated table or column name rather than
silently returning wrong results.
"""
from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass

_FORBIDDEN_KEYWORDS = re.compile(
    r"\b(DROP|DELETE|INSERT|UPDATE|ALTER|ATTACH|DETACH|PRAGMA|CREATE|REPLACE|VACUUM)\b",
    re.IGNORECASE,
)


class UnsafeQueryError(ValueError):
    pass


def is_single_select_statement(sql: str) -> bool:
    cleaned = sql.strip().rstrip(";").strip()
    if ";" in cleaned:
        return False  # a second statement is hiding after the first semicolon
    if not re.match(r"^\s*SELECT\b", cleaned, re.IGNORECASE):
        return False
    if _FORBIDDEN_KEYWORDS.search(cleaned):
        return False
    return True


@dataclass
class QueryResult:
    success: bool
    columns: list[str]
    rows: list[tuple]
    error: str | None = None


def validate_and_execute(sql: str, conn: sqlite3.Connection) -> QueryResult:
    cleaned = sql.strip().rstrip(";").strip()
    if not is_single_select_statement(cleaned):
        return QueryResult(success=False, columns=[], rows=[], error="rejected: not a single read-only SELECT statement")

    try:
        cursor = conn.execute(cleaned)
        columns = [description[0] for description in cursor.description] if cursor.description else []
        rows = cursor.fetchall()
        return QueryResult(success=True, columns=columns, rows=rows)
    except sqlite3.Error as e:
        return QueryResult(success=False, columns=[], rows=[], error=f"SQL error: {e}")
