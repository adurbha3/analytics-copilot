"""Generate a markdown data dictionary and a dbt-style schema.yml test stub
straight from the semantic layer -- the same catalog that drives the NL2SQL
prompt and the detection agent's checks, so documentation never drifts out
of sync with what is actually tested.
"""
from __future__ import annotations

from analyticscopilot.schema_catalog import CATALOG, TableSpec


def generate_markdown_docs(catalog: dict[str, TableSpec] = CATALOG) -> str:
    lines = ["# Data Dictionary", ""]
    for table in catalog.values():
        lines.append(f"## `{table.name}`")
        lines.append("")
        lines.append(table.description)
        lines.append("")
        lines.append("| Column | Type | Description | Tests |")
        lines.append("| --- | --- | --- | --- |")
        for column in table.columns:
            tests = ", ".join(column.tests) if column.tests else "-"
            lines.append(f"| {column.name} | {column.data_type} | {column.description} | {tests} |")
        lines.append("")
    return "\n".join(lines)


def generate_dbt_schema_yaml(catalog: dict[str, TableSpec] = CATALOG) -> str:
    """A minimal, hand-rolled YAML stub in dbt's schema.yml shape (no yaml
    library dependency needed for this small, flat structure)."""
    lines = ["version: 2", "", "models:"]
    for table in catalog.values():
        lines.append(f"  - name: {table.name}")
        lines.append(f"    description: \"{table.description}\"")
        lines.append("    columns:")
        for column in table.columns:
            lines.append(f"      - name: {column.name}")
            lines.append(f"        description: \"{column.description}\"")
            if column.tests:
                lines.append("        tests:")
                for test in column.tests:
                    if test.startswith("accepted_values:"):
                        values = test.split(":", 1)[1].strip("[]").split(",")
                        lines.append("          - accepted_values:")
                        lines.append(f"              values: {values}")
                    else:
                        lines.append(f"          - {test}")
    return "\n".join(lines)
