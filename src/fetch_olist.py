"""Download the required Olist CSVs from Kaggle using local .env credentials."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
DATASET_SLUG = "olistbr/brazilian-ecommerce"
DOWNLOAD_URL = f"https://www.kaggle.com/api/v1/datasets/download/{DATASET_SLUG}"
DATASET_PAGE = f"https://www.kaggle.com/datasets/{DATASET_SLUG}"
REQUIRED_FILES = (
    "olist_customers_dataset.csv",
    "olist_orders_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_sellers_dataset.csv",
)


def credentials(username: str | None, key: str | None) -> tuple[str, str]:
    """Return Kaggle credentials or fail without disclosing any configured value."""
    if not username or not key:
        raise RuntimeError(
            "Kaggle credentials are missing. Set KAGGLE_USERNAME and KAGGLE_KEY "
            "in the ignored .env file; never pass credentials as command-line arguments."
        )
    return username, key


def _row_dimensions(payload: bytes) -> tuple[int, int, list[str]]:
    """Count CSV records and fields without transforming their source bytes."""
    text = payload.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(text))
    header = next(reader)
    rows = sum(1 for _ in reader)
    return rows, len(header), header


def _artifact_path(path: Path) -> str:
    """Store a root-relative path when possible, otherwise retain the absolute path."""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def fetch_olist(data_dir: Path | None = None) -> list[dict[str, Any]]:
    """Download, validate, and preserve the five source CSVs required by case 03.

    Credentials are loaded from the repository's ignored `.env` file or process
    environment. The downloaded ZIP is temporary; only the required original
    CSV members are kept. The data-specific license is not inferred: confirm
    the current Kaggle terms before analysis.
    """
    load_dotenv(ROOT / ".env")
    username, key = credentials(os.getenv("KAGGLE_USERNAME"), os.getenv("KAGGLE_KEY"))
    if data_dir is None:
        configured = Path(os.getenv("DATA_DIR", "data"))
        data_dir = configured if configured.is_absolute() else ROOT / configured
    raw_dir = data_dir / "raw" / "03_olist_delivery_reviews"
    raw_dir.mkdir(parents=True, exist_ok=True)

    descriptor, temporary_zip_name = tempfile.mkstemp(
        prefix="olist-download-",
        suffix=".zip",
        dir=raw_dir,
    )
    os.close(descriptor)
    temporary_zip = Path(temporary_zip_name)
    try:
        response = requests.get(
            DOWNLOAD_URL,
            auth=(username, key),
            timeout=(30, 300),
            stream=True,
        )
        response.raise_for_status()
        with temporary_zip.open("wb") as destination:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    destination.write(chunk)

        with zipfile.ZipFile(temporary_zip) as archive:
            by_basename: dict[str, str] = {}
            for member in archive.namelist():
                if Path(member).name in REQUIRED_FILES:
                    if Path(member).name in by_basename:
                        raise ValueError(f"Kaggle archive contains duplicate {Path(member).name}")
                    by_basename[Path(member).name] = member
            missing = [filename for filename in REQUIRED_FILES if filename not in by_basename]
            if missing:
                raise ValueError(f"Kaggle archive is missing required CSVs: {', '.join(missing)}")
            payloads = {
                filename: archive.read(by_basename[filename]) for filename in REQUIRED_FILES
            }
    except (requests.RequestException, zipfile.BadZipFile) as error:
        raise RuntimeError(
            "Olist Kaggle download failed; no substitute data were used. "
            "Check credentials, network access, and dataset availability."
        ) from error
    finally:
        temporary_zip.unlink(missing_ok=True)

    retrieved_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    records = []
    for filename, payload in payloads.items():
        rows, columns, fields = _row_dimensions(payload)
        target = raw_dir / filename
        target.write_bytes(payload)
        records.append(
            {
                "case": "03_olist_delivery_reviews",
                "dataset": "Brazilian E-Commerce Public Dataset by Olist",
                "retrieved_at_utc": retrieved_at,
                "source_url": DOWNLOAD_URL,
                "license": (
                    "Not stated by this download script; verify current Kaggle dataset "
                    "terms before analysis"
                ),
                "license_url": DATASET_PAGE,
                "artifact": _artifact_path(target),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "observed_rows": rows,
                "observed_columns": columns,
                "observed_fields": fields,
                "source_described_dimensions": "Not read from Kaggle dataset metadata",
                "parsing_note": (
                    "CSV bytes retained unchanged; dimensions read from the downloaded "
                    "header and records."
                ),
            }
        )

    manifest_path = data_dir / "processed" / "download_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    existing = (
        json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest_path.is_file()
        else []
    )
    combined = [
        record for record in existing if record.get("case") != "03_olist_delivery_reviews"
    ] + records
    manifest_path.write_text(json.dumps(combined, indent=2) + "\n", encoding="utf-8")
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, help="override DATA_DIR for this download")
    arguments = parser.parse_args()
    records = fetch_olist(arguments.data_dir)
    for record in records:
        print(
            f"{record['artifact']}: {record['observed_rows']} rows x "
            f"{record['observed_columns']} columns; SHA-256 {record['sha256']}"
        )
    print("Confirm the dataset's current Kaggle license terms before analysis.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())