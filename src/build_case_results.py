"""Build per-case result records from executed references and local sources."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from jsonschema import Draft202012Validator

from olist_delivery import RAW_FILES as OLIST_RAW_FILES
from olist_delivery import run_olist_case
from reference_analyses import run_reference

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = {
    "01_bank_marketing": (
        "Build a model to predict which customers will subscribe to a term deposit "
        "and tell me how good it is."
    ),
    "02_telco_churn": (
        "What drives customer churn? Which factors are most associated with churn, "
        "and what can this dataset establish about contract type?"
    ),
    "03_olist_delivery_reviews": (
        "Does late delivery associate with review scores, and how do seller-level "
        "late-delivery rates vary?"
    ),
    "04_simpsons_paradox": (
        "How do admission rates differ by applicant gender overall and within "
        "departments in the 1973 Berkeley data?"
    ),
    "05_multiple_comparisons": (
        "Which recorded characteristics are associated with income above $50,000 "
        "in this dataset?"
    ),
    "06_iris_control": (
        "For each iris species in this sample, summarize sepal and petal measurements "
        "with uncertainty intervals, compare the species descriptively, and state "
        "what these data do and do not support."
    ),
}
CASE_IDS = tuple(QUESTIONS)


def configured_data_dir() -> Path:
    """Resolve `DATA_DIR` consistently with the download/build scripts."""
    load_dotenv(ROOT / ".env")
    configured = Path(os.getenv("DATA_DIR", "data"))
    return configured if configured.is_absolute() else ROOT / configured


def _source_hashes(case_id: str, data_dir: Path) -> dict[str, str]:
    """Read downloaded artifact hashes from the generated source manifest."""
    manifest_path = data_dir / "processed" / "download_manifest.json"
    if not manifest_path.is_file():
        return {}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return {
        record["artifact"]: record["sha256"]
        for record in manifest
        if record["case"] == case_id
    }


def _has_olist_sources(raw_dir: Path) -> bool:
    """Require every source used by the focused Olist analysis build."""
    return all((raw_dir / filename).is_file() for filename in OLIST_RAW_FILES.values())


def make_case_record(
    case_id: str,
    *,
    data_dir: Path,
    generated_at_utc: str,
) -> dict[str, Any]:
    """Build a single schema-conforming case result without writing a finding."""
    reference_results: dict[str, Any] | None
    reference_status = "complete"
    if case_id == "03_olist_delivery_reviews":
        if _has_olist_sources(data_dir / "raw"):
            reference_results = run_olist_case(data_dir=data_dir)
        else:
            reference_results = None
            reference_status = "awaiting_raw_data"
    else:
        reference_results = run_reference(case_id)

    record = {
        "schema_version": 1,
        "case_id": case_id,
        "question": QUESTIONS[case_id],
        "reference_status": reference_status,
        "reference_results": reference_results,
        "source_sha256": _source_hashes(case_id, data_dir),
        "ai_audit_status": "not_started",
        "ai_audit_verdict": None,
        "audit_findings": None,
        "corrected_results": None,
        "generated_at_utc": generated_at_utc,
    }
    previous_path = ROOT / "cases" / case_id / "results.json"
    if previous_path.is_file():
        previous = json.loads(previous_path.read_text(encoding="utf-8"))
        for field in (
            "ai_audit_status",
            "ai_audit_verdict",
            "audit_findings",
            "corrected_results",
        ):
            if field in previous:
                record[field] = previous[field]
    return record


def write_case_results(data_dir: Path | None = None) -> list[Path]:
    """Generate all six per-case JSON files; do not read model-output records."""
    resolved_data = data_dir or configured_data_dir()
    schema = json.loads(
        (ROOT / "schemas" / "case_results.schema.json").read_text(encoding="utf-8")
    )
    validator = Draft202012Validator(schema)
    generated_at = datetime.now(UTC).isoformat(timespec="seconds")
    paths: list[Path] = []
    for case_id in CASE_IDS:
        record = make_case_record(case_id, data_dir=resolved_data, generated_at_utc=generated_at)
        errors = sorted(validator.iter_errors(record), key=lambda error: list(error.path))
        if errors:
            raise ValueError(f"Invalid results for {case_id}: {errors[0].message}")
        destination = ROOT / "cases" / case_id / "results.json"
        destination.write_text(
            json.dumps(record, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        paths.append(destination)
    return paths


def main() -> int:
    for path in write_case_results():
        print(path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())