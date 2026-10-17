"""Checks for Bank Marketing audit interval calculations."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from bank_audit import _independent_gap_interval, _paired_gap_interval


def test_paired_gap_interval_is_zero_for_identical_scores() -> None:
    actual = np.tile([0, 1], 100)
    scores = np.linspace(0.01, 0.99, len(actual))

    difference, interval = _paired_gap_interval(
        actual,
        scores,
        scores,
        roc_auc_score,
        seed=42,
        n_resamples=100,
    )

    assert difference == 0.0
    assert interval == [0.0, 0.0]


def test_independent_gap_interval_is_reproducible() -> None:
    actual = np.tile([0, 1], 200)
    scores = np.linspace(0.01, 0.99, len(actual))

    first = _independent_gap_interval(
        actual,
        scores,
        actual,
        scores,
        roc_auc_score,
        seed=42,
        n_resamples=100,
    )
    second = _independent_gap_interval(
        actual,
        scores,
        actual,
        scores,
        roc_auc_score,
        seed=42,
        n_resamples=100,
    )

    assert first == second
    assert first[0] == 0.0
    assert first[1][0] <= 0.0 <= first[1][1]
