#!/usr/bin/env python
"""Ask the conversational analytics assistant a question in plain language."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analyticscopilot.warehouse import build_warehouse
from analyticscopilot.llm import LocalLLM
from analyticscopilot.nl2sql import ask


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question", type=str)
    args = parser.parse_args()

    print("Building the warehouse and loading the local model (first run downloads ~700MB)...")
    conn = build_warehouse()
    llm = LocalLLM()

    result = ask(args.question, conn, llm)
    print(f"\nQ: {result.question}")
    print(f"Generated SQL: {result.generated_sql}")
    if result.query_result.success:
        print(f"Columns: {result.query_result.columns}")
        for row in result.query_result.rows[:20]:
            print(f"  {row}")
    else:
        print(f"Could not trust this answer: {result.query_result.error}")


if __name__ == "__main__":
    main()
