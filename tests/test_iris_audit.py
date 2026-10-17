"""Tests for the Iris control-case audit."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from iris_audit import audit_iris_control


@pytest.fixture(scope="module")
def audit() -> dict[str, Any]:
    return audit_iris_control()


def test_iris_audit_reproduces_reference_and_sample_checks(
    audit: dict[str, Any],
) -> None:
    assert audit["n_total"] == 150
    assert audit["species_counts"] == {
        "Iris-setosa": 50,
        "Iris-versicolor": 50,
        "Iris-virginica": 50,
    }
    assert audit["duplicate_rows"] == 3
    assert audit["nonpositive_measurement_rows"] == 0
    assert len(audit["summary_statistics"]) == 12
    assert len(audit["pairwise_comparisons"]) == 12
    assert audit["reference_comparison"]["max_absolute_mean_difference_cm"] < 1e-12
    assert (
        audit["reference_comparison"][
            "max_absolute_t_interval_endpoint_difference_cm"
        ]
        < 1e-12
    )


def test_setosa_petal_ranges_do_not_overlap_other_species(
    audit: dict[str, Any],
) -> None:
    petal_rows = [
        row
        for row in audit["observed_range_overlaps"]
        if row["measurement"] in {"petal length", "petal width"}
        and row["first_species"] == "Iris-setosa"
    ]

    assert len(petal_rows) == 4
    assert all(not row["observed_ranges_overlap"] for row in petal_rows)
