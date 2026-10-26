# Analytics Copilot

**A conversational analytics (natural-language-to-SQL) assistant over a small dbt-style staging-to-mart warehouse, a schema-driven data-quality detection agent, and automated documentation/test generation — all reading from one shared semantic layer.**

## Why this exists

This targets four things named side by side in a specific job description: conversational analytics chatbots on top of a modern data stack, AI-assisted pipeline automation (testing, documentation, monitoring), detection agents for data quality, and domain-driven data architecture. Rather than build four disconnected demos, everything here reads from one semantic layer (`analyticscopilot/schema_catalog.py`): the same column metadata drives the NL2SQL prompt, the auto-generated docs, and the detection agent's checks, so the three pieces never drift out of sync with each other.

## A real finding that shaped the design

I tested the local language model directly on natural-language-to-SQL before committing to an architecture. Simple single-table questions ("how many verifications failed?") produced correct SQL reliably. Multi-table questions requiring a join consistently failed: the model referenced columns on the wrong table or invented a window function over the wrong source, producing confident-looking but wrong SQL. Rather than reach for a bigger model, the warehouse is built the way a real dbt project handles exactly this tradeoff: one denormalized mart table (`mart_verifications`), already joined once by code, is the only thing the assistant ever has to query. Generated SQL is still never trusted blindly — it is validated as a single read-only `SELECT` and then actually executed, so a hallucinated column name fails loudly (a clear error) instead of silently returning a wrong answer.

All data (users, organizations, verification events) is synthetic and fictional, generated for this project — no real users or company data is involved.

**A known limitation, stated plainly rather than hidden**: `sql_validation.py` only checks that generated SQL is safe (a single read-only `SELECT`, no hallucinated table or column name) and that it executes -- it cannot verify the *answer* is semantically correct. Asking "what fraction of verifications failed?" currently returns a raw count instead of a ratio: the SQL is valid and runs cleanly, but it does not answer the question asked. Catching that class of error would need either a stronger model or an answer-grounding check (e.g. comparing the question's expected unit/shape to the result), which is a natural next step rather than something papered over here.

## Features

- **Warehouse** (`analyticscopilot/warehouse.py`) — SQLite staging tables (`stg_users`, `stg_verifications`) and a single mart table built from them via a real SQL join, mirroring a dbt staging-to-mart pipeline.
- **Semantic layer** (`analyticscopilot/schema_catalog.py`) — one typed, documented description of the mart's columns (including dbt-style `not_null` / `unique` / `accepted_values` test declarations) that every other module reads from.
- **Conversational analytics** (`analyticscopilot/nl2sql.py`) — turns a plain-language question into SQL via a local open-source LLM (no API key), validated and executed before any result is trusted (`analyticscopilot/sql_validation.py`).
- **Data-quality detection agent** (`analyticscopilot/detection_agent.py`) — runs the semantic layer's own declared tests against live data, plus a pipeline-level check that the mart's join did not silently drop rows.
- **Automated documentation** (`analyticscopilot/auto_docs.py`) — generates a markdown data dictionary and a dbt-style `schema.yml` test stub directly from the semantic layer.
- **Tested** — 25 automated tests (`pytest`), almost all deterministic (a scriptable LLM stub covers the NL2SQL plumbing), plus one true end-to-end integration test against the real local model — run automatically on push via GitHub Actions.

## Install

```bash
git clone https://github.com/adurbha3/analytics-copilot.git
cd analytics-copilot
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Needs Python 3.9+. The first run downloads the local LLM (~360M parameters, ~700MB) from Hugging Face.

## Usage

Ask a question in plain language:

```bash
python scripts/ask.py "How many verifications have status failed?"
```

Run the data-quality detection agent:

```bash
python scripts/run_quality_checks.py
```

Generate the data dictionary and dbt schema stub:

```bash
python scripts/generate_docs.py
```

## Project layout

```
analyticscopilot/
  synthetic_data.py   fictional identity-verification users and events
  warehouse.py        SQLite staging tables + the mart-building join
  schema_catalog.py   the semantic layer: one source of truth for columns and tests
  llm.py              pluggable LLM backend: LocalLLM (real) and StubLLM (fast/deterministic)
  sql_validation.py   reject anything but a single read-only SELECT, then execute it
  nl2sql.py           the conversational analytics assistant
  detection_agent.py  schema-driven data quality checks + a pipeline-level join check
  auto_docs.py        markdown data dictionary + dbt schema.yml generation
scripts/
  ask.py                  CLI: ask one question
  run_quality_checks.py   CLI: run the detection agent
  generate_docs.py        CLI: write the data dictionary and schema.yml
tests/                pytest suite covering every module above
```

## Running tests

```bash
pip install -r requirements-dev.txt
pytest -v
```
