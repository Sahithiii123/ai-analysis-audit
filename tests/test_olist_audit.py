"""Checks for Olist audit effect direction and intervals."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from olist_audit import _bootstrap_rank_biserial, _difference_interval


def test_rank_biserial_is_positive_when_second_group_scores_higher() -> None:
    late_scores = np.ones(40, dtype=int)
    on_time_scores = np.full(40, 5, dtype=int)

    estimate, lower, upper = _bootstrap_rank_biserial(late_scores, on_time_scores)

    assert estimate == 1.0
    assert lower == 1.0
    assert upper == 1.0


def test_rank_biserial_is_negative_when_second_group_scores_lower() -> None:
    high_scores = np.full(40, 5, dtype=int)
    low_scores = np.ones(40, dtype=int)

    estimate, lower, upper = _bootstrap_rank_biserial(high_scores, low_scores)

    assert estimate == -1.0
    assert lower == -1.0
    assert upper == -1.0


def test_newcombe_interval_contains_proportion_difference() -> None:
    difference = 0.5 - 0.25

    lower, upper = _difference_interval(0.5, 100, 0.25, 100)

    assert lower < difference < upper
