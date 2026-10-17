"""Checks for Berkeley department standardization."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from berkeley_audit import _standardized_rates


def test_standardized_rates_use_the_same_department_weights() -> None:
    table = pd.DataFrame(
        [
            {"Dept": "A", "Gender": "Female", "Applicants": 100, "Rate": 0.8},
            {"Dept": "A", "Gender": "Male", "Applicants": 100, "Rate": 0.4},
            {"Dept": "B", "Gender": "Female", "Applicants": 100, "Rate": 0.2},
            {"Dept": "B", "Gender": "Male", "Applicants": 100, "Rate": 0.6},
        ]
    )

    result = _standardized_rates(table)

    assert result["rates"]["Female"] == 0.5
    assert result["rates"]["Male"] == 0.5
    assert result["female_minus_male_difference"] == 0.0
    assert result["department_weights"] == {"A": 0.5, "B": 0.5}
