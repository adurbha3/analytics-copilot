"""Natural-language-to-SQL over the mart layer only.

Testing against the real local model showed it reliably produces correct
single-table SQL, but hallucinates column names and botches joins once a
question needs more than one table (confirmed by trying several multi-table
questions and inspecting the raw generated SQL). Rather than fight that with
a bigger model or heavier prompting, this mirrors a real dbt convention:
expose one denormalized mart table (warehouse.py's mart_verifications,
already joined once, by code, not by the model) as the only thing the
assistant ever has to query. Generated SQL is still validated and actually
executed before being trusted (sql_validation.py), so a hallucinated column
name fails loudly instead of returning a wrong answer silently.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from analyticscopilot.llm import LLMBackend
from analyticscopilot.schema_catalog import schema_prompt_text
from analyticscopilot.sql_validation import validate_and_execute, QueryResult

PROMPT_TEMPLATE = """You are a SQL assistant. Given the schema below, write ONE SQLite SELECT query that answers the question. Reply with only the SQL query, no explanation.

Schema:
{schema}

Question: How many verifications have status failed?
SQL: SELECT COUNT(*) FROM mart_verifications WHERE status = 'failed';

Question: What is the most common verification method?
SQL: SELECT method, COUNT(*) AS n FROM mart_verifications GROUP BY method ORDER BY n DESC LIMIT 1;

Question: {question}
SQL:"""


@dataclass
class NL2SQLResult:
    question: str
    generated_sql: str
    query_result: QueryResult


def _extract_sql(raw: str) -> str:
    """The model sometimes wraps its answer in a code fence or adds a stray
    leading/trailing phrase; take the first line that looks like a SELECT."""
    for line in raw.splitlines():
        stripped = line.strip().strip("`")
        if stripped.upper().startswith("SELECT"):
            return stripped
    return raw.strip().strip("`")


def ask(question: str, conn: sqlite3.Connection, llm: LLMBackend) -> NL2SQLResult:
    prompt = PROMPT_TEMPLATE.format(schema=schema_prompt_text(), question=question)
    raw = llm.generate(prompt, max_new_tokens=80)
    sql = _extract_sql(raw)
    result = validate_and_execute(sql, conn)
    return NL2SQLResult(question=question, generated_sql=sql, query_result=result)
