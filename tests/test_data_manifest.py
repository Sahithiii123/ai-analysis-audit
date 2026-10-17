"""Verify provenance against the real downloaded dataset files."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from src.fetch_data import merge_manifest_records, parse_arff, parse_csv

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "processed" / "download_manifest.json"


def test_manifest_refresh_preserves_other_case_provenance() -> None:
    existing = [
        {"case": "01_bank_marketing", "sha256": "old"},
        {"case": "03_olist_delivery_reviews", "sha256": "olist"},
    ]
    refreshed = [{"case": "01_bank_marketing", "sha256": "new"}]
    assert merge_manifest_records(existing, refreshed) == [
        {"case": "03_olist_delivery_reviews", "sha256": "olist"},
        {"case": "01_bank_marketing", "sha256": "new"},
    ]


def test_manifest_matches_downloaded_real_datasets() -> None:
    if not MANIFEST.is_file():
        pytest.skip("Fetch the real datasets with src/fetch_data.py first.")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    expected_cases = {
        "01_bank_marketing",
        "02_telco_churn",
        "04_simpsons_paradox",
        "05_multiple_comparisons",
        "06_iris_control",
    }
    assert expected_cases.issubset({record["case"] for record in manifest})

    for record in manifest:
        artifact = ROOT / record["artifact"]
        payload = artifact.read_bytes()
        assert hashlib.sha256(payload).hexdigest() == record["sha256"]

        if artifact.suffix == ".arff":
            dimensions = parse_arff(payload)
        else:
            dimensions = parse_csv(payload)
            if record["case"] == "04_simpsons_paradox":
                dimensions = (dimensions[0], dimensions[1] - 1, dimensions[2][1:])

        assert dimensions[0] == record["observed_rows"]
        assert dimensions[1] == record["observed_columns"]
        assert dimensions[2] == record["observed_fields"]