"""Tiny illustrative Olist fixture; never used as case data or a finding."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from olist_delivery import analyze_olist_delivery, build_olist_database

TINY_OLIST_TEST_FIXTURE = {
    "olist_customers_dataset.csv": (
        ["customer_id", "customer_state"],
        [["c1", "SP"], ["c2", "RJ"]],
    ),
    "olist_sellers_dataset.csv": (
        ["seller_id", "seller_state"],
        [["s1", "SP"], ["s2", "RJ"]],
    ),
    "olist_orders_dataset.csv": (
        [
            "order_id",
            "customer_id",
            "order_status",
            "order_purchase_timestamp",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
        [
            [
                "o1", "c1", "delivered", "2018-01-01 00:00:00",
                "2018-01-06 00:00:00", "2018-01-04 00:00:00",
            ],
            [
                "o2", "c1", "delivered", "2018-01-01 00:00:00",
                "2018-01-03 00:00:00", "2018-01-05 00:00:00",
            ],
            [
                "o3", "c2", "delivered", "2018-01-01 00:00:00",
                "2018-01-07 00:00:00", "2018-01-06 00:00:00",
            ],
            ["o4", "c2", "delivered", "2018-01-01 00:00:00", "2018-01-04 00:00:00", ""],
            ["o5", "c2", "processing", "2018-01-01 00:00:00", "", "2018-01-06 00:00:00"],
        ],
    ),
    "olist_order_items_dataset.csv": (
        ["order_id", "order_item_id", "seller_id", "price", "freight_value"],
        [
            ["o1", 1, "s1", 10, 1],
            ["o1", 2, "s1", 20, 2],
            ["o2", 1, "s1", 15, 1],
            ["o3", 1, "s2", 12, 1],
            ["o4", 1, "s2", 18, 1],
            ["o5", 1, "s2", 25, 1],
        ],
    ),
    "olist_order_reviews_dataset.csv": (
        ["review_id", "order_id", "review_score"],
        [
            ["r1", "o1", 4],
            ["r2", "o1", 2],
            ["r3", "o2", 5],
            ["r4", "o3", 1],
            ["r5", "o4", 4],
            ["r6", "o5", 2],
        ],
    ),
}


def write_tiny_fixture(raw_dir: Path) -> None:
    """Write the named test fixture to a temporary directory only."""
    raw_dir.mkdir(parents=True)
    for filename, (headers, rows) in TINY_OLIST_TEST_FIXTURE.items():
        with (raw_dir / filename).open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(headers)
            writer.writerows(rows)


def test_build_and_delivery_analysis_preserve_order_and_seller_grain(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    write_tiny_fixture(raw_dir)
    database = build_olist_database(raw_dir, tmp_path / "processed" / "olist.duckdb")

    with duckdb.connect(str(database), read_only=True) as connection:
        assert connection.execute("SELECT COUNT(*) FROM fact_orders").fetchone()[0] == 5

    output_dir = tmp_path / "analysis"
    result = analyze_olist_delivery(database, output_dir, min_seller_orders=3)
    assert result["n_delivered_reviewed_orders_with_known_status"] == 3
    status = {row["delivery_status"]: row for row in result["review_by_delivery_status"]}
    assert status["Late"]["order_count"] == 2
    assert status["Late"]["mean_review_score"] == 2.0
    assert status["On time"]["mean_review_score"] == 5.0
    assert status["Late"]["mean_review_score_ci_95_lower"] < 2.0
    assert status["Late"]["mean_review_score_ci_95_upper"] > 2.0
    assert status["On time"]["mean_review_score_ci_95_lower"] is None

    sellers = {row["seller_id"]: row for row in result["seller_delivery_rates"]}
    assert sellers["s1"]["delivered_reviewed_order_count"] == 2
    assert sellers["s1"]["known_delivery_status_count"] == 2
    assert sellers["s1"]["late_order_count"] == 1
    assert sellers["s1"]["late_rate"] == 0.5
    assert sellers["s2"]["delivered_reviewed_order_count"] == 2
    assert sellers["s2"]["known_delivery_status_count"] == 1
    assert sellers["s2"]["late_rate"] == 1.0
    assert not sellers["s1"]["meets_min_seller_orders"]
    assert not sellers["s2"]["meets_min_seller_orders"]

    saved = json.loads((output_dir / "case_results.json").read_text(encoding="utf-8"))
    assert saved["n_delivered_reviewed_orders_with_known_status"] == 3
    assert (output_dir / "seller_delivery_rates.csv").is_file()


def test_build_stops_when_real_source_files_are_missing(tmp_path: Path) -> None:
    try:
        build_olist_database(tmp_path / "missing", tmp_path / "processed" / "olist.duckdb")
    except FileNotFoundError as error:
        assert "olist_orders_dataset.csv" in str(error)
    else:
        raise AssertionError("Expected missing raw Olist files to stop the build")