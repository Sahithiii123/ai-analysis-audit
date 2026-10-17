"""Fail if generated report tables diverge from case result JSON."""

from __future__ import annotations

import sys
from pathlib import Path

from reporting import ROOT, expected_reports


def verify_numbers(root: Path = ROOT) -> None:
    """Rebuild expected report strings from results and compare byte-for-byte."""
    expected_csv, expected_markdown, expected_readme = expected_reports(root)
    reports = root / "reports"
    actual_csv = reports / "summary_table.csv"
    actual_markdown = reports / "summary_table.md"
    if not actual_csv.is_file() or actual_csv.read_text(encoding="utf-8") != expected_csv:
        raise ValueError("reports/summary_table.csv does not match cases/*/results.json")
    if (
        not actual_markdown.is_file()
        or actual_markdown.read_text(encoding="utf-8") != expected_markdown
    ):
        raise ValueError("reports/summary_table.md does not match cases/*/results.json")

    readme_path = root / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    if readme != expected_readme:
        raise ValueError("README generated findings/results do not match cases/*/results.json")
    print("Verified report numbers against all six case result files.")


def main() -> int:
    try:
        verify_numbers()
    except (FileNotFoundError, ValueError) as error:
        print(f"Number verification failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())