"""A semantic layer: typed, documented metadata about each warehouse table,
the single source of truth the NL2SQL prompt, the auto-generated docs, and
the SQL validator all read from -- so the schema is described once, not
re-typed three different ways.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ColumnSpec:
    name: str
    data_type: str
    description: str
    tests: list[str]  # dbt-style: "not_null", "unique", or "accepted_values:[...]"


@dataclass
class TableSpec:
    name: str
    description: str
    columns: list[ColumnSpec]

    @property
    def column_names(self) -> set[str]:
        return {c.name for c in self.columns}


MART_VERIFICATIONS = TableSpec(
    name="mart_verifications",
    description=(
        "One row per identity-verification attempt, denormalized with the "
        "requesting user's organization and signup details so downstream "
        "queries never need a join."
    ),
    columns=[
        ColumnSpec("verification_id", "INTEGER", "Unique identifier for the verification attempt.", ["not_null", "unique"]),
        ColumnSpec("user_id", "INTEGER", "The user who attempted verification.", ["not_null"]),
        ColumnSpec("email_domain", "TEXT", "Domain portion of the user's email address.", ["not_null"]),
        ColumnSpec("organization", "TEXT", "The organization that requested the verification.", ["not_null"]),
        ColumnSpec("method", "TEXT", "Verification method used.",
                   ["not_null", "accepted_values:[document_scan,selfie_match,sms_otp,knowledge_based]"]),
        ColumnSpec("status", "TEXT", "Outcome of the verification attempt.",
                   ["not_null", "accepted_values:[verified,failed,pending]"]),
        ColumnSpec("created_at", "TEXT", "Date the verification attempt was made (ISO 8601).", ["not_null"]),
        ColumnSpec("signup_date", "TEXT", "Date the user originally signed up (ISO 8601).", ["not_null"]),
    ],
)

CATALOG: dict[str, TableSpec] = {MART_VERIFICATIONS.name: MART_VERIFICATIONS}


def schema_prompt_text(catalog: dict[str, TableSpec] = CATALOG) -> str:
    """Render the catalog as plain text for the NL2SQL prompt."""
    lines = []
    for table in catalog.values():
        columns = ", ".join(f"{c.name} {c.data_type}" for c in table.columns)
        lines.append(f"Table {table.name}({columns})")
    return "\n".join(lines)
