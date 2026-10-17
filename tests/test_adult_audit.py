"""Checks for Adult audit proportion and Cramer's V helpers."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from adult_audit import _bias_corrected_cramers_v, _wilson_difference_interval


def test_wilson_difference_interval_contains_observed_difference() -> None:
    difference = 3 / 10 - 1 / 10

    lower, upper = _wilson_difference_interval(3, 10, 1, 10)

    assert lower < difference < upper


def test_bias_corrected_cramers_v_does_not_exceed_uncorrected_value() -> None:
    corrected = _bias_corrected_cramers_v(50.0, 100, 2, 2)

    assert 0.0 < corrected < (0.5**0.5)
