"""Build and analyze the Olist delivery/review tables with DuckDB."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import duckdb
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from scipy import stats

from audit_tools import wilson_interval

ROOT = Path(__file__).resolve().parents[1]
RAW_FILES = {
    "customers": "olist_customers_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "order_reviews": "olist_order_reviews_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
}
MODEL_SQL = """
CREATE OR REPLACE TABLE dim_customers AS
SELECT customer_id, customer_state FROM raw_customers;

CREATE OR REPLACE TABLE dim_sellers AS
SELECT seller_id, seller_state FROM raw_sellers;

CREATE OR REPLACE TABLE fact_orders AS
SELECT order_id, customer_id, order_status,
       TRY_CAST(order_purchase_timestamp AS TIMESTAMP) AS purchased_at,
       TRY_CAST(order_delivered_customer_date AS TIMESTAMP) AS delivered_at,
       TRY_CAST(order_estimated_delivery_date AS TIMESTAMP) AS estimated_at,
       CASE
           WHEN TRY_CAST(order_delivered_customer_date AS TIMESTAMP) IS NULL
             OR TRY_CAST(order_estimated_delivery_date AS TIMESTAMP) IS NULL THEN NULL
           ELSE TRY_CAST(order_delivered_customer_date AS TIMESTAMP)
                > TRY_CAST(order_estimated_delivery_date AS TIMESTAMP)
       END AS is_late,
       CASE
           WHEN TRY_CAST(order_delivered_customer_date AS TIMESTAMP) IS NULL
             OR TRY_CAST(order_estimated_delivery_date AS TIMESTAMP) IS NULL THEN NULL
           WHEN TRY_CAST(order_delivered_customer_date AS TIMESTAMP)
                > TRY_CAST(order_estimated_delivery_date AS TIMESTAMP)
           THEN GREATEST(
               DATE_DIFF(
                   'day',
                   CAST(order_estimated_delivery_date AS DATE),
                   CAST(order_delivered_customer_date AS DATE)
               ),
               1
           )
           ELSE 0
       END AS days_late
FROM raw_orders;

CREATE OR REPLACE TABLE fact_order_items AS
SELECT order_id,
       TRY_CAST(order_item_id AS INTEGER) AS order_item_id,
       seller_id,
       TRY_CAST(price AS DOUBLE) AS price,
       TRY_CAST(freight_value AS DOUBLE) AS freight_value
FROM raw_order_items;

CREATE OR REPLACE TABLE fact_reviews AS
SELECT review_id, order_id, TRY_CAST(review_score AS INTEGER) AS review_score
FROM raw_order_reviews;
"""
ANALYSIS_SQL = ROOT / "sql" / "olist_delivery_vs_reviews.sql"


def resolve_data_dir() -> Path:
    """Resolve `DATA_DIR` using the same convention as the other data scripts."""
    load_dotenv(ROOT / ".env")
    configured = Path(os.getenv("DATA_DIR", "data"))
    return configured if configured.is_absolute() else ROOT / configured


def build_olist_database(raw_dir: Path, database_path: Path) -> Path:
    """Load required source CSVs and construct order-grain DuckDB fact tables.

    The five required files are read unchanged from `raw_dir`; no source data
    are copied, filtered, or written back. This focused build does not require
    product, payment, or geolocation CSVs because they are outside the case
    question. It raises before opening a database if any required source is
    absent.
    """
    missing = [filename for filename in RAW_FILES.values() if not (raw_dir / filename).is_file()]
    if missing:
        raise FileNotFoundError(
            f"Missing Olist source CSV(s) in {raw_dir}: {', '.join(missing)}"
        )
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(str(database_path))
    try:
        for table, filename in RAW_FILES.items():
            connection.execute(
                f"CREATE OR REPLACE TABLE raw_{table} AS "
                "SELECT * FROM read_csv_auto(?, header=true, all_varchar=true)",
                [str(raw_dir / filename)],
            )
        connection.execute(MODEL_SQL)
        return database_path
    finally:
        connection.close()


def _mean_ci(values: pd.Series) -> tuple[float | None, float | None]:
    """Return a two-sided 95% t interval for a mean, or nulls if undefined."""
    clean = values.dropna().astype(float)
    if clean.size < 2:
        return None, None
    standard_error = stats.sem(clean)
    lower, upper = stats.t.interval(
        0.95,
        df=clean.size - 1,
        loc=clean.mean(),
        scale=standard_error,
    )
    return float(lower), float(upper)


def _row_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """Convert a DataFrame to JSON-compatible records with nonfinite values null."""
    records = frame.replace({np.nan: None}).to_dict(orient="records")
    for record in records:
        for key, value in record.items():
            if isinstance(value, np.generic):
                record[key] = value.item()
            if isinstance(record[key], float) and not np.isfinite(record[key]):
                record[key] = None
    return records


def analyze_olist_delivery(
    database_path: Path,
    output_dir: Path,
    *,
    min_seller_orders: int = 30,
    sql_path: Path = ANALYSIS_SQL,
) -> dict[str, Any]:
    """Execute delivery/review SQL and save reproducible CSV and JSON outputs."""
    if not database_path.is_file():
        raise FileNotFoundError(f"Olist DuckDB database not found: {database_path}")
    if min_seller_orders < 1:
        raise ValueError("min_seller_orders must be positive")
    output_dir.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(str(database_path))
    try:
        connection.execute(sql_path.read_text(encoding="utf-8"))
        status = connection.execute(
            "SELECT * FROM review_by_delivery_status ORDER BY delivery_status"
        ).fetchdf()
        buckets = connection.execute(
            "SELECT * FROM review_by_lateness_bucket ORDER BY bucket_order"
        ).fetchdf()
        sellers = connection.execute(
            "SELECT * FROM seller_delivery_rates ORDER BY seller_id"
        ).fetchdf()
        orders = connection.execute(
            "SELECT is_late, days_late, review_score FROM reviewed_delivered_orders"
        ).fetchdf()
    finally:
        connection.close()

    status_records = _row_records(status)
    bucket_records = _row_records(buckets)
    seller_records = _row_records(sellers)

    # Grouped SQL summaries cannot reconstruct individual observations; derive
    # the design-based mean intervals from order-level rows for each group.
    for record in status_records:
        selected = orders.loc[
            orders["is_late"].eq(record["delivery_status"] == "Late"),
            "review_score",
        ]
        lower, upper = _mean_ci(selected)
        record["mean_review_score_ci_95_lower"] = lower
        record["mean_review_score_ci_95_upper"] = upper
    for record in bucket_records:
        bucket = record["lateness_bucket"]
        if bucket == "On time":
            mask = orders["days_late"].eq(0)
        elif bucket == "1-3 days":
            mask = orders["days_late"].between(1, 3)
        elif bucket == "4-7 days":
            mask = orders["days_late"].between(4, 7)
        else:
            mask = orders["days_late"].ge(8)
        lower, upper = _mean_ci(orders.loc[mask, "review_score"])
        record["mean_review_score_ci_95_lower"] = lower
        record["mean_review_score_ci_95_upper"] = upper

    seller_intervals: list[dict[str, Any]] = []
    for record in seller_records:
        count = int(record["known_delivery_status_count"])
        late = int(record["late_order_count"])
        lower, upper = wilson_interval(late, count) if count else (None, None)
        record["late_rate_ci_95_lower"] = lower
        record["late_rate_ci_95_upper"] = upper
        record["meets_min_seller_orders"] = (
            int(record["delivered_reviewed_order_count"]) >= min_seller_orders
        )
        seller_intervals.append(record)

    csv_outputs = {
        "review_by_delivery_status.csv": status_records,
        "review_by_lateness_bucket.csv": bucket_records,
        "seller_delivery_rates.csv": seller_intervals,
    }
    for filename, rows in csv_outputs.items():
        pd.DataFrame(rows).to_csv(output_dir / filename, index=False)

    total_orders = int(status["order_count"].sum()) if not status.empty else 0
    summary = {
        "case": "03_olist_delivery_reviews",
        "question": (
            "Does late delivery associate with review scores, and how do seller-level "
            "late-delivery rates vary?"
        ),
        "n_delivered_reviewed_orders_with_known_status": total_orders,
        "review_by_delivery_status": status_records,
        "review_by_lateness_bucket": bucket_records,
        "seller_delivery_rates": seller_intervals,
        "min_seller_orders_flag": min_seller_orders,
        "limitations": [
            "Orders without a customer-delivered timestamp or any review row are excluded.",
            (
                "Repeated reviews are averaged per order before joining; seller rates count "
                "a distinct order once per seller."
            ),
            (
                "Review-score differences and late-delivery rates are observational "
                "associations, not causal effects."
            ),
            (
                "Seller intervals use a Wilson binomial interval and do not account for "
                "dependence across sellers or repeated customer behavior."
            ),
        ],
    }
    (output_dir / "case_results.json").write_text(
        json.dumps(summary, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return summary


def run_olist_case(
    data_dir: Path | None = None,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Build and run the Olist case using the configured local data directory."""
    resolved_data = data_dir or resolve_data_dir()
    resolved_output = output_dir or resolved_data / "processed" / "olist_delivery"
    database = resolved_data / "processed" / "olist_delivery.duckdb"
    build_olist_database(resolved_data / "raw", database)
    return analyze_olist_delivery(database, resolved_output)


def main() -> int:
    result = run_olist_case()
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())