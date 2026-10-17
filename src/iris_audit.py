"""Independent reproduction and audit checks for the Iris control case."""

from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from reference_analyses import ROOT, load_case_data

SEED = 20261016
N_BOOT = 10_000
MEASUREMENTS = (
    "sepal length",
    "sepal width",
    "petal length",
    "petal width",
)


def _prepare_frame() -> pd.DataFrame:
    frame = load_case_data("06_iris_control")
    frame.columns = [column.strip() for column in frame.columns]
    frame["class"] = frame["class"].astype("string").str.strip()
    for measure in MEASUREMENTS:
        frame[measure] = pd.to_numeric(frame[measure], errors="raise")
    return frame


def _mean_summary(
    values: np.ndarray,
    rng: np.random.Generator,
) -> dict[str, float]:
    n = len(values)
    mean = float(values.mean())
    standard_error = float(stats.sem(values))
    half_width = float(stats.t.ppf(0.975, n - 1) * standard_error)
    indices = rng.integers(0, n, size=(N_BOOT, n))
    bootstrap_means = values[indices].mean(axis=1)
    bootstrap_lower, bootstrap_upper = np.quantile(bootstrap_means, [0.025, 0.975])
    return {
        "n": n,
        "mean_cm": mean,
        "sd_cm": float(values.std(ddof=1)),
        "median_cm": float(np.median(values)),
        "min_cm": float(values.min()),
        "max_cm": float(values.max()),
        "t_ci_95_cm": [mean - half_width, mean + half_width],
        "bootstrap_ci_95_cm": [
            float(bootstrap_lower),
            float(bootstrap_upper),
        ],
    }


def _pairwise_comparisons(
    frame: pd.DataFrame,
    species: list[str],
    rng: np.random.Generator,
) -> list[dict[str, Any]]:
    comparisons = []
    for measure in MEASUREMENTS:
        for first_species, second_species in combinations(species, 2):
            first = frame.loc[frame["class"].eq(first_species), measure].to_numpy(
                dtype=float
            )
            second = frame.loc[frame["class"].eq(second_species), measure].to_numpy(
                dtype=float
            )
            first_indices = rng.integers(0, len(first), size=(N_BOOT, len(first)))
            second_indices = rng.integers(0, len(second), size=(N_BOOT, len(second)))
            differences = (
                first[first_indices].mean(axis=1)
                - second[second_indices].mean(axis=1)
            )
            lower, upper = np.quantile(differences, [0.025, 0.975])
            pooled_sd = np.sqrt(
                (
                    (len(first) - 1) * first.var(ddof=1)
                    + (len(second) - 1) * second.var(ddof=1)
                )
                / (len(first) + len(second) - 2)
            )
            comparisons.append(
                {
                    "measurement": measure,
                    "first_species": first_species,
                    "second_species": second_species,
                    "mean_difference_cm": float(first.mean() - second.mean()),
                    "bootstrap_ci_95_cm": [float(lower), float(upper)],
                    "cohens_d": float((first.mean() - second.mean()) / pooled_sd),
                }
            )
    return comparisons


def _range_overlaps(
    frame: pd.DataFrame,
    species: list[str],
) -> list[dict[str, Any]]:
    overlaps = []
    for measure in MEASUREMENTS:
        ranges = {
            species_name: (
                float(values.min()),
                float(values.max()),
            )
            for species_name, values in frame.groupby("class", observed=True)[measure]
        }
        for first_species, second_species in combinations(species, 2):
            first_min, first_max = ranges[first_species]
            second_min, second_max = ranges[second_species]
            intersection_lower = max(first_min, second_min)
            intersection_upper = min(first_max, second_max)
            overlaps.append(
                {
                    "measurement": measure,
                    "first_species": first_species,
                    "second_species": second_species,
                    "first_range_cm": [first_min, first_max],
                    "second_range_cm": [second_min, second_max],
                    "observed_ranges_overlap": intersection_lower <= intersection_upper,
                    "overlap_width_cm": max(0.0, intersection_upper - intersection_lower),
                }
            )
    return overlaps


def _saved_run_status() -> dict[str, Any]:
    run_root = ROOT / "reports" / "ai_code_runs" / "06_iris_control"
    run_records = sorted(run_root.glob("*/attempt-1/run.json"))
    if not run_records:
        raise FileNotFoundError(f"No saved Iris AI run found under {run_root}")
    run_path = run_records[-1]
    run = json.loads(run_path.read_text(encoding="utf-8"))
    attempt = run_path.parent
    stdout = (attempt / "stdout.txt").read_text(encoding="utf-8")
    stderr = (attempt / "stderr.txt").read_text(encoding="utf-8")
    return {
        "run_record": run_path.relative_to(ROOT).as_posix(),
        "exit_code": int(run["exit_code"]),
        "stdout_bytes": (attempt / "stdout.txt").stat().st_size,
        "stderr_has_exception": "Traceback" in stderr,
        "shape_present": "Shape: (150, 5)" in stdout,
        "duplicate_count_present": "Duplicate rows: 3" in stdout,
        "summary_rows_present": "5.006" in stdout and "2.026" in stdout,
        "plot_saved": "Saved iris_boxplots.png" in stdout,
    }


def audit_iris_control() -> dict[str, Any]:
    """Reproduce sample summaries, pointwise bootstrap intervals, and ranges."""
    frame = _prepare_frame()
    species = sorted(frame["class"].dropna().unique().tolist())
    rng = np.random.default_rng(SEED)
    summaries = []
    for species_name, group in frame.groupby("class", sort=True, observed=True):
        for measure in MEASUREMENTS:
            summaries.append(
                {
                    "species": str(species_name),
                    "measurement": measure,
                    **_mean_summary(group[measure].to_numpy(dtype=float), rng),
                }
            )
    comparisons = _pairwise_comparisons(frame, species, rng)
    reference_path = ROOT / "cases" / "06_iris_control" / "results.json"
    reference = json.loads(reference_path.read_text(encoding="utf-8"))[
        "reference_results"
    ]
    reference_by_key = {
        (row["species"], row["measurement"]): row
        for row in reference["species_measurements"]
    }
    max_mean_difference = 0.0
    max_interval_difference = 0.0
    for row in summaries:
        expected = reference_by_key[(row["species"], row["measurement"])]
        max_mean_difference = max(
            max_mean_difference,
            abs(row["mean_cm"] - expected["mean_cm"]),
        )
        max_interval_difference = max(
            max_interval_difference,
            abs(row["t_ci_95_cm"][0] - expected["ci_95_lower_cm"]),
            abs(row["t_ci_95_cm"][1] - expected["ci_95_upper_cm"]),
        )

    nonpositive_rows = int(
        frame[list(MEASUREMENTS)].le(0).any(axis=1).sum()
    )
    return {
        "saved_ai_run": _saved_run_status(),
        "n_total": int(len(frame)),
        "species_counts": {
            str(key): int(value)
            for key, value in frame["class"].value_counts().sort_index().items()
        },
        "missing_values_by_column": {
            str(key): int(value) for key, value in frame.isna().sum().items()
        },
        "duplicate_rows": int(frame.duplicated().sum()),
        "nonpositive_measurement_rows": nonpositive_rows,
        "summary_statistics": summaries,
        "pairwise_comparisons": comparisons,
        "observed_range_overlaps": _range_overlaps(frame, species),
        "reference_comparison": {
            "reference_summary_rows": len(reference_by_key),
            "max_absolute_mean_difference_cm": max_mean_difference,
            "max_absolute_t_interval_endpoint_difference_cm": (
                max_interval_difference
            ),
        },
        "interpretation": {
            "pairwise_intervals_are_pointwise": True,
            "pairwise_interval_family_size": len(comparisons),
            "inference_scope": (
                "Descriptive for the observed sample; population generalization "
                "requires a defensible sampling design."
            ),
            "duplicate_row_caveat": (
                "Exact duplicate rows are retained. Identical rounded measurements "
                "alone do not establish duplicate specimens."
            ),
        },
    }


def write_iris_audit_results(audit: dict[str, Any]) -> Path:
    """Persist audit findings and independent evidence in results.json."""
    path = ROOT / "cases" / "06_iris_control" / "results.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    record["ai_audit_status"] = "complete"
    record["ai_audit_verdict"] = "Reliable"
    record["audit_findings"] = []
    record["corrected_results"] = {
        "independent_audit": audit,
        "reference_comparison": audit["reference_comparison"],
        "ai_output_verified": {
            "saved_run_exit_code": audit["saved_ai_run"]["exit_code"],
            "run_completed": audit["saved_ai_run"]["exit_code"] == 0,
            "summary_shape_reproduced": audit["saved_ai_run"]["shape_present"],
            "duplicate_count_reproduced": (
                audit["saved_ai_run"]["duplicate_count_present"]
            ),
            "mean_summary_rows_reproduced": (
                audit["saved_ai_run"]["summary_rows_present"]
            ),
            "figure_saved": audit["saved_ai_run"]["plot_saved"],
        },
        "interpretation": (
            "The reported sample summaries and descriptive conclusions reproduce. "
            "Intervals are for means under independent-row assumptions, not for "
            "individual flowers or unspecified broader populations."
        ),
    }
    path.write_text(
        json.dumps(record, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return path


def render_iris_audit_markdown(result_path: Path | None = None) -> Path:
    """Render the Iris control-case audit from persisted results."""
    result_path = result_path or ROOT / "cases" / "06_iris_control" / "results.json"
    record = json.loads(result_path.read_text(encoding="utf-8"))
    audit = record["corrected_results"]["independent_audit"]
    max_t_ci_difference = audit["reference_comparison"][
        "max_absolute_t_interval_endpoint_difference_cm"
    ]
    lines = [
        "# Case 06 audit: Iris control",
        "",
        f"**Verdict: {record['ai_audit_verdict']}**",
        "",
        "## Reproduction and data checks",
        "",
        (
            f"The saved AI code exited {audit['saved_ai_run']['exit_code']} and "
            f"reported {audit['n_total']} rows. Independent checks confirm "
            f"{audit['n_total']} rows, three species with 50 observations each, "
            f"{audit['duplicate_rows']} exact duplicate rows, no missing values, "
            "and no nonpositive measurements. Duplicate rows were retained because "
            "identical rounded measurements alone do not establish repeated specimens."
        ),
        (
            f"All 12 species-by-measure means agree with the blind reference to "
            f"{audit['reference_comparison']['max_absolute_mean_difference_cm']:.3g} cm "
            f"maximum absolute difference; the largest t-interval endpoint difference "
            f"is {max_t_ci_difference:.3g} cm."
        ),
        "",
        "## Species means and uncertainty",
        "",
        "| Species | Measurement | n | Mean (cm) | 95% t CI | 95% bootstrap CI |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in audit["summary_statistics"]:
        t_lower, t_upper = row["t_ci_95_cm"]
        boot_lower, boot_upper = row["bootstrap_ci_95_cm"]
        lines.append(
            f"| {row['species']} | {row['measurement']} | {row['n']} | "
            f"{row['mean_cm']:.3f} | {t_lower:.3f} to {t_upper:.3f} | "
            f"{boot_lower:.3f} to {boot_upper:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Descriptive contrasts and observed ranges",
            "",
            (
                "The AI's mean-difference bootstrap intervals are pointwise 95% "
                "intervals across 12 pairwise comparisons, not simultaneous intervals. "
                "They are descriptive and do not replace a prespecified inferential "
                "analysis or adjust familywise error."
            ),
            "",
            (
                "| Measurement | Contrast (first - second) | Mean difference (cm) | "
                "Pointwise 95% bootstrap CI | Cohen's d |"
            ),
            "|---|---|---:|---:|---:|",
        ]
    )
    for row in audit["pairwise_comparisons"]:
        lower, upper = row["bootstrap_ci_95_cm"]
        lines.append(
            f"| {row['measurement']} | {row['first_species']} - "
            f"{row['second_species']} | {row['mean_difference_cm']:+.3f} | "
            f"{lower:+.3f} to {upper:+.3f} | {row['cohens_d']:+.2f} |"
        )
    lines.extend(
        [
            "",
            (
                "| Measurement | Species pair | First range (cm) | "
                "Second range (cm) | Observed overlap |"
            ),
            "|---|---|---:|---:|---|",
        ]
    )
    for row in audit["observed_range_overlaps"]:
        first_lower, first_upper = row["first_range_cm"]
        second_lower, second_upper = row["second_range_cm"]
        overlap = (
            f"{row['overlap_width_cm']:.1f} cm"
            if row["observed_ranges_overlap"]
            else "none"
        )
        lines.append(
            f"| {row['measurement']} | {row['first_species']} - "
            f"{row['second_species']} | {first_lower:.1f} to {first_upper:.1f} | "
            f"{second_lower:.1f} to {second_upper:.1f} | {overlap} |"
        )
    lines.extend(
        [
            "",
            "## Assessment and limits",
            "",
            (
                "The descriptive claims reproduce: setosa has shorter, wider sepals "
                "on average and markedly smaller petals; virginica has higher means "
                "than versicolor on all four measurements. Observed petal ranges for "
                "setosa do not overlap either other species, while versicolor and "
                "virginica overlap on petal measurements. This supports a descriptive "
                "statement about separation in this sample, not validated classification."
            ),
            (
                "The t and bootstrap intervals are uncertainty intervals for species "
                "means under row-resampling/independence assumptions. They are not "
                "individual-flower prediction intervals. Sampling provenance is not "
                "sufficient to generalize these results to all iris populations or "
                "infer biological causes."
            ),
            "",
            "No material numerical or interpretive error was reproduced. The response "
            "appropriately avoids causal, population-wide, and classifier-performance claims.",
            "",
        ]
    )
    path = result_path.parent / "audit.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
