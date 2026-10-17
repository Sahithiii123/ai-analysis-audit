"""Checks for Telco audit design-matrix diagnostics."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from telco_audit import _design_diagnostics


def test_design_diagnostics_reports_exact_duplicate_columns() -> None:
    design = pd.DataFrame(
        {
            "internet_none": [0, 1, 0, 1],
            "security_no_internet": [0, 1, 0, 1],
            "contract": [0, 0, 1, 1],
        }
    )

    diagnostics = _design_diagnostics(design)

    assert diagnostics["column_count"] == 3
    assert diagnostics["matrix_rank"] == 2
    assert diagnostics["rank_deficiency"] == 1
    assert diagnostics["exact_duplicate_columns"] == [
        ["internet_none", "security_no_internet"]
    ]
