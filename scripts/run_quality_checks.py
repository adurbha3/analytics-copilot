#!/usr/bin/env python
"""Run the data-quality detection agent against the warehouse and print any
issues found."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analyticscopilot.warehouse import build_warehouse
from analyticscopilot.detection_agent import run_all_checks


def main() -> None:
    conn = build_warehouse()
    issues = run_all_checks(conn)

    if not issues:
        print("No data quality issues found.")
        return

    print(f"Found {len(issues)} data quality issue(s):\n")
    for issue in issues:
        print(f"[{issue.severity.upper()}] {issue.check_name}: {issue.message}")


if __name__ == "__main__":
    main()
