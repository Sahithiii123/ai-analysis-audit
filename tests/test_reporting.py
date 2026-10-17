"""Report tests use temporary schema-shaped fixtures, never case results."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import build_case_results
from reporting import (
    CASE_IDS,
    README_END,
    README_FINDINGS_END,
    README_FINDINGS_START,
    README_START,
    build_reports,
)
from verify_numbers import verify_numbers

TINY_RESULTS_TEST_FIXTURE = {
    "schema_version": 1,
    "question": "Test-only question.",
    "source_sha256": {},
    "ai_audit_status": "not_started",
    "ai_audit_verdict": None,
    "audit_findings": None,
    "corrected_results": None,
    "generated_at_utc": "2026-10-16T00:00:00Z",
}


def write_result_fixtures(root: Path) -> None:
    """Write test-only result records under a pytest temporary directory."""
    schema_dir = root / "schemas"
    schema_dir.mkdir()
    source_schema = Path(__file__).resolve().parents[1] / "schemas" / "case_results.schema.json"
    (schema_dir / "case_results.schema.json").write_bytes(source_schema.read_bytes())
    for case_id in CASE_IDS:
        case_dir = root / "cases" / case_id
        case_dir.mkdir(parents=True)
        record = dict(TINY_RESULTS_TEST_FIXTURE)
        record.update(
            {
                "case_id": case_id,
                "reference_status": "awaiting_raw_data"
                if case_id == "03_olist_delivery_reviews"
                else "complete",
                "reference_results": None
                if case_id == "03_olist_delivery_reviews"
                else {
                    "n_total": 12,
                    "test_metrics": {"pr_auc_average_precision": 0.375},
                },
            }
        )
        if case_id == CASE_IDS[0]:
            record.update(
                {
                    "ai_audit_status": "complete",
                    "ai_audit_verdict": "Partly reliable",
                    "audit_findings": [
                        {
                            "finding_type": "Fixture evidence",
                            "measured_effect": "Measured fixture difference: 2 records.",
                        }
                    ],
                }
            )
        (case_dir / "results.json").write_text(json.dumps(record), encoding="utf-8")
    (root / "README.md").write_text(
        (
            f"# Test report\n\n{README_FINDINGS_START}\nplaceholder\n"
            f"{README_FINDINGS_END}\n\n{README_START}\nplaceholder\n{README_END}\n"
        ),
        encoding="utf-8",
    )


def test_report_outputs_are_verified_against_result_fixtures(tmp_path: Path) -> None:
    write_result_fixtures(tmp_path)
    build_reports(tmp_path)
    verify_numbers(tmp_path)
    generated_readme = (tmp_path / "README.md").read_text(encoding="utf-8")
    assert "Measured fixture difference: 2 records." in generated_readme

    csv_path = tmp_path / "reports" / "summary_table.csv"
    csv_path.write_text(
        csv_path.read_text(encoding="utf-8").replace("PR-AUC 0.375", "PR-AUC 0.376"),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="summary_table.csv"):
        verify_numbers(tmp_path)


def test_result_refresh_preserves_existing_audit_fields(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    case_id = "01_bank_marketing"
    case_dir = tmp_path / "cases" / case_id
    case_dir.mkdir(parents=True)
    previous = {
        "ai_audit_status": "complete",
        "ai_audit_verdict": "Partly reliable",
        "audit_findings": [{"label": "test-only measured fixture finding"}],
        "corrected_results": {"test_fixture_metric": 0.5},
    }
    (case_dir / "results.json").write_text(json.dumps(previous), encoding="utf-8")
    monkeypatch.setattr(build_case_results, "ROOT", tmp_path)
    monkeypatch.setattr(build_case_results, "run_reference", lambda _: {"n_total": 12})

    result = build_case_results.make_case_record(
        case_id,
        data_dir=tmp_path / "data",
        generated_at_utc="2026-10-16T00:00:00Z",
    )

    assert result["ai_audit_status"] == "complete"
    assert result["ai_audit_verdict"] == "Partly reliable"
    assert result["audit_findings"] == previous["audit_findings"]
    assert result["corrected_results"] == previous["corrected_results"]