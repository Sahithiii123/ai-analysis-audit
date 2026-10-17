"""Download the public datasets used by the audit cases."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import shlex
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
OPENML_API = "https://www.openml.org/api/v1/json/data/{}"
OPENML_QUALITY_API = "https://www.openml.org/api/v1/json/data/qualities/{}"
UCI_API = "https://archive.ics.uci.edu/api/dataset?id={}"
UCB_URL = "https://vincentarelbundock.github.io/Rdatasets/csv/datasets/UCBAdmissions.csv"


def retrieval_time() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def get_json(url: str) -> dict[str, Any]:
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return response.json()


def download(url: str, target: Path) -> tuple[bytes, str]:
    try:
        response = requests.get(url, timeout=120)
        response.raise_for_status()
    except requests.RequestException as error:
        raise RuntimeError(
            f"Download failed for {url}; stopping without substituting data."
        ) from error

    payload = response.content
    if not payload:
        raise RuntimeError(f"Download returned an empty file from {url}; stopping.")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    return payload, retrieval_time()


def parse_csv(payload: bytes) -> tuple[int, int, list[str]]:
    frame = pd.read_csv(io.BytesIO(payload), sep=None, engine="python")
    return len(frame), len(frame.columns), [str(column) for column in frame.columns]


def parse_arff(payload: bytes) -> tuple[int, int, list[str]]:
    lines = payload.decode("utf-8-sig").splitlines()
    names = [
        shlex.split(line, comments=False)[1]
        for line in lines
        if line.strip().lower().startswith("@attribute ")
    ]
    data_index = next(
        (index for index, line in enumerate(lines) if line.strip().lower() == "@data"),
        None,
    )
    if data_index is None or not names:
        raise ValueError("Downloaded ARFF file is missing its attributes or @data section.")

    rows = [row for row in csv.reader(lines[data_index + 1 :]) if row]
    if any(len(row) != len(names) for row in rows):
        raise ValueError("ARFF data row width does not match the declared attributes.")
    return len(rows), len(names), names


def make_record(
    *,
    case: str,
    name: str,
    source_url: str,
    license_text: str,
    license_url: str,
    target: Path,
    payload: bytes,
    retrieved_at: str,
    dimensions: tuple[int, int, list[str]],
    source_dimensions: str,
    parsing_note: str = (
        "Source file retained unchanged; dimensions parsed from the downloaded file."
    ),
) -> dict[str, Any]:
    rows, columns, fields = dimensions
    return {
        "case": case,
        "dataset": name,
        "retrieved_at_utc": retrieved_at,
        "source_url": source_url,
        "license": license_text,
        "license_url": license_url,
        "artifact": str(target.relative_to(ROOT)) if target.is_relative_to(ROOT) else str(target),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "observed_rows": rows,
        "observed_columns": columns,
        "observed_fields": fields,
        "source_described_dimensions": source_dimensions,
        "parsing_note": parsing_note,
    }


def merge_manifest_records(
    existing_records: list[dict[str, Any]],
    refreshed_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Replace refreshed cases and preserve provenance for other downloaded cases."""
    refreshed_cases = {record["case"] for record in refreshed_records}
    combined = [
        record for record in existing_records if record.get("case") not in refreshed_cases
    ]
    combined.extend(refreshed_records)
    return combined


def main() -> None:
    load_dotenv(ROOT / ".env")
    configured_data_dir = Path(os.getenv("DATA_DIR", "data"))
    data_dir = (
        configured_data_dir
        if configured_data_dir.is_absolute()
        else ROOT / configured_data_dir
    )
    raw_dir = data_dir / "raw"
    records: list[dict[str, Any]] = []

    for dataset_id, case, name, license_text, license_url in (
        (222, "01_bank_marketing", "Bank Marketing", "CC BY 4.0", "https://archive.ics.uci.edu/dataset/222/bank+marketing"),
        (53, "06_iris_control", "Iris", "CC BY 4.0", "https://archive.ics.uci.edu/dataset/53/iris"),
    ):
        metadata = get_json(UCI_API.format(dataset_id))["data"]
        source_url = metadata["data_url"]
        target = raw_dir / case / "data.csv"
        payload, retrieved_at = download(source_url, target)
        dimensions = parse_csv(payload)
        records.append(
            make_record(
                case=case,
                name=name,
                source_url=source_url,
                license_text=license_text,
                license_url=license_url,
                target=target,
                payload=payload,
                retrieved_at=retrieved_at,
                dimensions=dimensions,
                source_dimensions=(
                    f"{metadata['num_instances']} instances; "
                    f"{metadata['num_features']} features plus target"
                ),
            )
        )

    for dataset_id, case, name in (
        (42178, "02_telco_churn", "telco-customer-churn"),
        (1590, "05_multiple_comparisons", "adult"),
    ):
        metadata = get_json(OPENML_API.format(dataset_id))["data_set_description"]
        qualities = get_json(OPENML_QUALITY_API.format(dataset_id))["data_qualities"]["quality"]
        quality_values = {item["name"]: item["value"] for item in qualities}
        source_url = metadata["url"]
        filename = Path(source_url.split("?")[0]).name
        target = raw_dir / case / filename
        payload, retrieved_at = download(source_url, target)
        dimensions = parse_arff(payload)
        source_dimensions = quality_values["NumberOfInstances"]
        source_features = quality_values["NumberOfFeatures"]
        license_text = (
            f"OpenML metadata: {metadata.get('licence', 'not stated')}; "
            "no specific license identifier supplied"
        )
        license_url = f"https://www.openml.org/d/{dataset_id}"
        if dataset_id == 1590:
            license_text += "; original UCI source states CC BY 4.0"
            license_url = "https://archive.ics.uci.edu/dataset/2/adult"
        records.append(
            make_record(
                case=case,
                name=name,
                source_url=source_url,
                license_text=license_text,
                license_url=license_url,
                target=target,
                payload=payload,
                retrieved_at=retrieved_at,
                dimensions=dimensions,
                source_dimensions=(
                    f"{source_dimensions} instances; {source_features} features "
                    "(OpenML metadata)"
                ),
            )
        )

    ucb_target = raw_dir / "04_simpsons_paradox" / "UCBAdmissions.csv"
    ucb_payload, ucb_retrieved_at = download(UCB_URL, ucb_target)
    ucb_frame = pd.read_csv(io.BytesIO(ucb_payload))
    ucb_source_columns = len(ucb_frame.columns)
    if str(ucb_frame.columns[0]).lower() in {"rownames", "unnamed: 0"}:
        ucb_frame = ucb_frame.iloc[:, 1:]
    ucb_dimensions = (
        len(ucb_frame),
        len(ucb_frame.columns),
        [str(column) for column in ucb_frame.columns],
    )
    records.append(
        make_record(
            case="04_simpsons_paradox",
            name="UCBAdmissions",
            source_url=UCB_URL,
            license_text=(
                "No dataset-specific license stated by Rdatasets; "
                "source is the R datasets base package"
            ),
            license_url="https://www.r-project.org/Licenses/",
            target=ucb_target,
            payload=ucb_payload,
            retrieved_at=ucb_retrieved_at,
            dimensions=ucb_dimensions,
            source_dimensions=(
                "24 contingency-table cells "
                "(2 admission outcomes x 2 genders x 6 departments)"
            ),
            parsing_note=(
                f"Source CSV retained unchanged ({ucb_source_columns} columns "
                "including its row-label index); "
                "the row-label index is excluded from the reported analysis columns."
            ),
        )
    )

    manifest_path = data_dir / "processed" / "download_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    existing = (
        json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest_path.is_file()
        else []
    )
    combined = merge_manifest_records(existing, records)
    manifest_path.write_text(json.dumps(combined, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(records, indent=2))
    print(f"Manifest: {manifest_path}")
    print("Olist skipped: Kaggle access awaits user confirmation.")


if __name__ == "__main__":
    main()