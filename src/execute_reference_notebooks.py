"""Execute the five blind reference notebooks with the project kernel."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
CASE_IDS = (
    "01_bank_marketing",
    "02_telco_churn",
    "04_simpsons_paradox",
    "05_multiple_comparisons",
    "06_iris_control",
)
KERNEL_NAME = "ai-analysis-audit"


def _ensure_cell_metadata(notebook: Any) -> None:
    """Keep stable IDs and explicit language metadata after execution."""
    for index, cell in enumerate(notebook.cells, start=1):
        cell_id = cell.get("id") or f"cell-{index:03d}"
        cell["id"] = cell_id
        cell.metadata["id"] = cell_id
        cell.metadata["language"] = "python" if cell.cell_type == "code" else "markdown"


def execute_reference_notebooks() -> list[Path]:
    """Execute each reference notebook from the repository root and save outputs."""
    executed_paths = []
    for case_id in CASE_IDS:
        path = ROOT / "cases" / case_id / "reference_analysis.ipynb"
        notebook = nbformat.read(path, as_version=4)
        client = NotebookClient(
            notebook,
            kernel_name=KERNEL_NAME,
            timeout=600,
            resources={"metadata": {"path": str(ROOT)}},
            allow_errors=False,
        )
        client.execute()
        _ensure_cell_metadata(notebook)
        nbformat.validate(notebook)
        nbformat.write(notebook, path)
        executed_paths.append(path)
    return executed_paths


def main() -> int:
    for path in execute_reference_notebooks():
        print(path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
