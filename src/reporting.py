"""Schema-checked rendering of reports from per-case result JSON files."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
CASE_IDS = (
    "01_bank_marketing",
    "02_telco_churn",
    "03_olist_delivery_reviews",
    "04_simpsons_paradox",
    "05_multiple_comparisons",
    "06_iris_control",
)
README_START = "<!-- BEGIN AUTO CASE RESULTS -->"
README_END = "<!-- END AUTO CASE RESULTS -->"
README_FINDINGS_START = "<!-- BEGIN AUTO HEADLINE FINDINGS -->"
README_FINDINGS_END = "<!-- END AUTO HEADLINE FINDINGS -->"
CSV_FIELDS = (
    "case_id",
    "reference_status",
    "reference_rows",
    "reference_metric",
    "ai_audit_status",
    "ai_verdict",
    "demonstrated_finding_count",
)


def load_case_results(root: Path = ROOT) -> list[dict[str, Any]]:
    """Load all six results and validate each against the committed schema."""
    schema_path = root / "schemas" / "case_results.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    records: list[dict[str, Any]] = []
    for case_id in CASE_IDS:
        path = root / "cases" / case_id / "results.json"
        if not path.is_file():
            raise FileNotFoundError(f"Missing case results: {path}")
        record = json.loads(path.read_text(encoding="utf-8"))
        errors = sorted(validator.iter_errors(record), key=lambda error: list(error.path))
        if errors:
            raise ValueError(f"Invalid {path.relative_to(root)}: {errors[0].message}")
        if record["case_id"] != case_id:
            raise ValueError(f"Case id mismatch in {path.relative_to(root)}")
        records.append(record)
    return records


def _reference_rows(record: dict[str, Any]) -> int | None:
    """Read the applicable sample/order count directly from reference results."""
    results = record["reference_results"]
    if results is None:
        return None
    for key in (
        "n_total",
        "n_applicants",
        "n_delivered_reviewed_orders_with_known_status",
    ):
        if key in results:
            return int(results[key])
    return None


def _format_number(value: float) -> str:
    """Render an already-computed numeric value without inventing precision."""
    return f"{value:.3f}"


def _reference_metric(record: dict[str, Any]) -> str:
    """Select a compact metric from this record's result object, if available."""
    results = record["reference_results"]
    if results is None:
        return "pending"
    if "test_metrics" in results:
        metrics = results["test_metrics"]
        value = metrics.get("pr_auc_average_precision", metrics.get("average_precision"))
        return f"PR-AUC {_format_number(float(value))}" if value is not None else "pending"
    if "churn_prevalence" in results:
        return f"Churn prevalence {_format_number(float(results['churn_prevalence']))}"
    if "cmh" in results:
        value = results["cmh"].get("female_vs_male_common_odds_ratio")
        return f"CMH OR {_format_number(float(value))}" if value is not None else "pending"
    if "positive_prevalence" in results:
        return f">$50K prevalence {_format_number(float(results['positive_prevalence']))}"
    if "species_tests" in results:
        return f"Measurements compared {len(results['species_tests'])}"
    if "review_by_delivery_status" in results:
        grouped = {
            item["delivery_status"]: item.get("mean_review_score")
            for item in results["review_by_delivery_status"]
        }
        late = grouped.get("Late")
        on_time = grouped.get("On time")
        if late is not None and on_time is not None:
            return (
                "Mean review score late/on-time "
                f"{_format_number(late)}/{_format_number(on_time)}"
            )
    return "not reported"


def summary_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Create report rows whose values are sourced only from results JSON."""
    rows = []
    for record in records:
        findings = record["audit_findings"]
        rows.append(
            {
                "case_id": record["case_id"],
                "reference_status": record["reference_status"],
                "reference_rows": _reference_rows(record),
                "reference_metric": _reference_metric(record),
                "ai_audit_status": record["ai_audit_status"],
                "ai_verdict": record["ai_audit_verdict"] or "pending",
                "demonstrated_finding_count": len(findings) if findings is not None else None,
            }
        )
    return rows


def render_csv(rows: list[dict[str, Any]]) -> str:
    """Render a deterministic CSV summary."""
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def render_markdown(rows: list[dict[str, Any]]) -> str:
    """Render a deterministic Markdown summary table."""
    header = (
        "| Case | Reference status | Reference rows | Reference metric | "
        "AI audit status | Verdict | Demonstrated findings |\n"
    )
    separator = "|---|---|---:|---|---|---|---:|\n"
    body = []
    for row in rows:
        values = [row[field] for field in CSV_FIELDS]
        values = ["" if value is None else str(value) for value in values]
        body.append(
            "| "
            + " | ".join(value.replace("|", "\\|") for value in values)
            + " |\n"
        )
    return header + separator + "".join(body)


def render_readme_block(rows: list[dict[str, Any]]) -> str:
    """Build a marker-delimited README section from the same report rows."""
    return (
        f"{README_START}\n\n"
        "The table below is generated from the six case `results.json` files.\n\n"
        + render_markdown(rows)
        + f"\n{README_END}"
    )


def render_readme_findings(records: list[dict[str, Any]]) -> str:
    """Render up to five measured headline findings from the case result records."""
    findings = []
    for record in records:
        case_findings = record["audit_findings"] or []
        if not case_findings:
            continue
        finding = case_findings[0]
        findings.append(
            f"- **{record['case_id']} — {finding['finding_type']}:** "
            f"{finding['measured_effect']}"
        )
        if len(findings) == 5:
            break
    if not findings:
        findings.append("- No measured findings are recorded in the case results yet.")
    return (
        f"{README_FINDINGS_START}\n\n"
        + "\n".join(findings)
        + f"\n\n{README_FINDINGS_END}"
    )


def _replace_marked_block(
    readme: str,
    block: str,
    start_marker: str,
    end_marker: str,
) -> str:
    """Replace exactly one marker-delimited block, preserving surrounding text."""
    start = readme.find(start_marker)
    end = readme.find(end_marker)
    if start == -1 or end == -1 or end < start:
        raise ValueError(f"README must contain markers {start_marker} and {end_marker}")
    if readme.find(start_marker, start + len(start_marker)) != -1:
        raise ValueError(f"README contains multiple {start_marker!r} markers")
    if readme.find(end_marker, end + len(end_marker)) != -1:
        raise ValueError(f"README contains multiple {end_marker!r} markers")
    end += len(end_marker)
    return readme[:start] + block + readme[end:]


def replace_readme_block(readme: str, block: str) -> str:
    """Replace the generated case-results block."""
    return _replace_marked_block(readme, block, README_START, README_END)


def expected_reports(root: Path = ROOT) -> tuple[str, str, str]:
    """Return canonical CSV, Markdown, and README block from result files."""
    records = load_case_results(root)
    rows = summary_rows(records)
    readme = (root / "README.md").read_text(encoding="utf-8")
    readme = _replace_marked_block(
        readme,
        render_readme_findings(records),
        README_FINDINGS_START,
        README_FINDINGS_END,
    )
    readme = replace_readme_block(readme, render_readme_block(rows))
    return render_csv(rows), render_markdown(rows), readme


def build_reports(root: Path = ROOT) -> list[Path]:
    """Generate CSV/Markdown summaries and update the generated README section."""
    csv_text, markdown_text, expected_readme = expected_reports(root)
    reports_dir = root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    csv_path = reports_dir / "summary_table.csv"
    markdown_path = reports_dir / "summary_table.md"
    csv_path.write_text(csv_text, encoding="utf-8", newline="")
    markdown_path.write_text(markdown_text, encoding="utf-8", newline="")
    readme_path = root / "README.md"
    readme_path.write_text(expected_readme, encoding="utf-8", newline="")
    return [csv_path, markdown_path, readme_path]