#!/usr/bin/env python
"""Generate the markdown data dictionary and dbt-style schema.yml test stub
from the semantic layer, and write them to docs/."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analyticscopilot.auto_docs import generate_markdown_docs, generate_dbt_schema_yaml


def main() -> None:
    out_dir = Path(__file__).resolve().parent.parent / "docs"
    out_dir.mkdir(exist_ok=True)

    (out_dir / "data_dictionary.md").write_text(generate_markdown_docs())
    (out_dir / "schema.yml").write_text(generate_dbt_schema_yaml())

    print(f"Wrote {out_dir / 'data_dictionary.md'}")
    print(f"Wrote {out_dir / 'schema.yml'}")


if __name__ == "__main__":
    main()
