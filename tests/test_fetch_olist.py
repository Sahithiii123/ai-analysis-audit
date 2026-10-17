"""Offline Olist fetch tests use a tiny CSV fixture, never case data."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from fetch_olist import _row_dimensions, credentials

TINY_CSV_TEST_FIXTURE = b"order_id,review_score\no1,4\no2,2\n"


def test_olist_credentials_fail_closed_without_values() -> None:
    with pytest.raises(RuntimeError, match="Kaggle credentials are missing"):
        credentials(None, None)
    with pytest.raises(RuntimeError, match="Kaggle credentials are missing"):
        credentials("test-user", None)


def test_csv_dimension_reader_uses_only_the_test_fixture() -> None:
    assert _row_dimensions(TINY_CSV_TEST_FIXTURE) == (
        2,
        2,
        ["order_id", "review_score"],
    )