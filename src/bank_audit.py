"""Independent Bank Marketing reproduction and audit checks."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from statsmodels.api import Logit

from audit_tools import bootstrap_ci
from reference_analyses import ROOT, load_case_data

SEED = 42
BOOTSTRAP_RESAMPLES = 800
CAT_COLUMNS = [
    "job",
    "marital",
    "education",
    "default",
    "housing",
    "loan",
    "contact",
    "month",
    "poutcome",
]
NUM_COLUMNS = [
    "age",
    "balance",
    "day_of_week",
    "campaign",
    "previous",
    "pdays_clean",
    "prev_contacted",
]


def _prepare_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    frame = load_case_data("01_bank_marketing")
    frame["y"] = frame["y"].astype(str).str.strip().str.lower().eq("yes").astype(int)
    for column in CAT_COLUMNS:
        frame[column] = frame[column].fillna("unknown").astype(str)
    frame["prev_contacted"] = frame["pdays"].ne(-1).astype(int)
    frame["pdays_clean"] = frame["pdays"].where(frame["pdays"].ne(-1), 0)
    features = frame[CAT_COLUMNS + NUM_COLUMNS]
    return frame, features, frame["y"]


def _model(
    name: str,
    categorical_columns: list[str],
    numeric_columns: list[str],
) -> Pipeline:
    preprocessor = ColumnTransformer(
        [
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                categorical_columns,
            ),
            (
                "num",
                StandardScaler() if name == "logistic regression" else "passthrough",
                numeric_columns,
            ),
        ]
    )
    if name == "baseline (always 'no')":
        classifier: Any = DummyClassifier(strategy="prior")
    elif name == "logistic regression":
        classifier = LogisticRegression(max_iter=2000, class_weight="balanced")
    elif name == "gradient boosting":
        classifier = HistGradientBoostingClassifier(
            learning_rate=0.05,
            max_iter=300,
            max_leaf_nodes=15,
            l2_regularization=1.0,
            random_state=SEED,
        )
    else:
        raise ValueError(f"Unknown model: {name}")
    return Pipeline([("pre", preprocessor), ("model", classifier)])


def _metrics(
    actual: pd.Series | np.ndarray,
    scores: np.ndarray,
    threshold: float,
) -> dict[str, Any]:
    target = np.asarray(actual, dtype=int)
    predicted = scores >= threshold
    matrix = confusion_matrix(target, predicted, labels=[0, 1])
    return {
        "n": int(len(target)),
        "prevalence": float(target.mean()),
        "roc_auc": float(roc_auc_score(target, scores)),
        "pr_auc": float(average_precision_score(target, scores)),
        "brier_score": float(brier_score_loss(target, scores)),
        "threshold": float(threshold),
        "accuracy": float(accuracy_score(target, predicted)),
        "precision": float(precision_score(target, predicted, zero_division=0)),
        "recall": float(recall_score(target, predicted, zero_division=0)),
        "f1": float(f1_score(target, predicted, zero_division=0)),
        "confusion_matrix": matrix.tolist(),
    }


def _calibration(actual: pd.Series | np.ndarray, scores: np.ndarray) -> dict[str, Any]:
    target = np.asarray(actual, dtype=int)
    clipped = np.clip(scores, 1e-6, 1 - 1e-6)
    logit_scores = np.log(clipped / (1 - clipped))
    design = pd.DataFrame(
        {"intercept": np.ones(len(logit_scores)), "logit_score": logit_scores}
    )
    fitted = Logit(target, design).fit(disp=False)
    bins = pd.qcut(pd.Series(scores), q=10, duplicates="drop")
    grouped = pd.DataFrame({"bin": bins, "actual": target, "score": scores}).groupby(
        "bin", observed=True
    )
    calibration_bins = [
        {
            "n": int(len(group)),
            "mean_predicted": float(group["score"].mean()),
            "observed_rate": float(group["actual"].mean()),
        }
        for _, group in grouped
    ]
    ece = sum(
        row["n"] / len(target) * abs(row["mean_predicted"] - row["observed_rate"])
        for row in calibration_bins
    )
    return {
        "brier_score": float(brier_score_loss(target, scores)),
        "calibration_intercept": float(fitted.params["intercept"]),
        "calibration_slope": float(fitted.params["logit_score"]),
        "expected_calibration_error_deciles": float(ece),
        "decile_summary": calibration_bins,
    }


def _performance_interval(
    actual: np.ndarray,
    scores: np.ndarray,
    metric: Callable[[np.ndarray, np.ndarray], float],
    *,
    seed: int,
) -> list[float]:
    lower, upper = bootstrap_ci(
        np.column_stack([actual, scores]),
        lambda sample: metric(sample[:, 0].astype(int), sample[:, 1]),
        n_resamples=BOOTSTRAP_RESAMPLES,
        random_state=seed,
    )
    return [lower, upper]


def _independent_gap_interval(
    left_actual: np.ndarray,
    left_scores: np.ndarray,
    right_actual: np.ndarray,
    right_scores: np.ndarray,
    metric: Callable[[np.ndarray, np.ndarray], float],
    *,
    seed: int,
    n_resamples: int = BOOTSTRAP_RESAMPLES,
) -> tuple[float, list[float]]:
    """Bootstrap the right-minus-left metric gap across independent test sets."""
    rng = np.random.default_rng(seed)
    gaps = np.empty(n_resamples)
    for index in range(n_resamples):
        left_indices = rng.integers(0, len(left_actual), len(left_actual))
        right_indices = rng.integers(0, len(right_actual), len(right_actual))
        gaps[index] = metric(
            right_actual[right_indices], right_scores[right_indices]
        ) - metric(left_actual[left_indices], left_scores[left_indices])
    point = metric(right_actual, right_scores) - metric(left_actual, left_scores)
    lower, upper = np.quantile(gaps, [0.025, 0.975])
    return float(point), [float(lower), float(upper)]


def _paired_gap_interval(
    actual: np.ndarray,
    full_scores: np.ndarray,
    reduced_scores: np.ndarray,
    metric: Callable[[np.ndarray, np.ndarray], float],
    *,
    seed: int,
    n_resamples: int = BOOTSTRAP_RESAMPLES,
) -> tuple[float, list[float]]:
    """Bootstrap reduced-minus-full score metrics on the same test rows."""
    rng = np.random.default_rng(seed)
    gaps = np.empty(n_resamples)
    for index in range(n_resamples):
        sample = rng.integers(0, len(actual), len(actual))
        gaps[index] = metric(actual[sample], reduced_scores[sample]) - metric(
            actual[sample], full_scores[sample]
        )
    point = metric(actual, reduced_scores) - metric(actual, full_scores)
    lower, upper = np.quantile(gaps, [0.025, 0.975])
    return float(point), [float(lower), float(upper)]


def _fit_split(
    features: pd.DataFrame,
    target: pd.Series,
    train_index: np.ndarray,
    validation_index: np.ndarray,
    test_index: np.ndarray,
) -> dict[str, Any]:
    validation_results = {}
    fitted_models = {}
    for name in ("baseline (always 'no')", "logistic regression", "gradient boosting"):
        model = _model(name, CAT_COLUMNS, NUM_COLUMNS)
        model.fit(features.iloc[train_index], target.iloc[train_index])
        validation_scores = model.predict_proba(features.iloc[validation_index])[:, 1]
        validation_results[name] = {
            "roc_auc": float(
                roc_auc_score(target.iloc[validation_index], validation_scores)
            ),
            "pr_auc": float(
                average_precision_score(target.iloc[validation_index], validation_scores)
            ),
        }
        fitted_models[name] = model
    best_name = max(validation_results, key=lambda name: validation_results[name]["pr_auc"])
    best_model = fitted_models[best_name]
    validation_scores = best_model.predict_proba(features.iloc[validation_index])[:, 1]
    precision, recall, thresholds = precision_recall_curve(
        target.iloc[validation_index], validation_scores
    )
    f1_values = 2 * precision[:-1] * recall[:-1] / (
        precision[:-1] + recall[:-1] + 1e-9
    )
    threshold = float(thresholds[int(np.argmax(f1_values))])
    test_scores = best_model.predict_proba(features.iloc[test_index])[:, 1]
    test_actual = target.iloc[test_index].to_numpy()
    result = {
        "model_selected": best_name,
        "validation_results": validation_results,
        "threshold_selected_on_validation": threshold,
        "validation_best_f1": float(np.max(f1_values)),
        "test_metrics": _metrics(test_actual, test_scores, threshold),
        "test_model_baseline": {
            "prevalence_pr_auc": float(test_actual.mean()),
            "always_negative_accuracy": float((test_actual == 0).mean()),
        },
        "test_calibration": _calibration(test_actual, test_scores),
        "test_roc_auc_ci_95": _performance_interval(
            test_actual,
            test_scores,
            roc_auc_score,
            seed=SEED + 1,
        ),
        "test_pr_auc_ci_95": _performance_interval(
            test_actual,
            test_scores,
            average_precision_score,
            seed=SEED + 2,
        ),
        "test_brier_ci_95": _performance_interval(
            test_actual,
            test_scores,
            brier_score_loss,
            seed=SEED + 3,
        ),
        "top_20_percent": {
            "share_subscribed": float(
                test_actual[np.argsort(-test_scores)[: int(0.2 * len(test_scores))]].mean()
            ),
            "lift_over_test_prevalence": float(
                test_actual[np.argsort(-test_scores)[: int(0.2 * len(test_scores))]].mean()
                / test_actual.mean()
            ),
        },
        "train_rows": int(len(train_index)),
        "validation_rows": int(len(validation_index)),
        "test_rows": int(len(test_index)),
    }
    return {
        "summary": result,
        "model": best_model,
        "test_actual": test_actual,
        "test_scores": test_scores,
        "validation_actual": target.iloc[validation_index].to_numpy(),
        "validation_scores": validation_scores,
        "test_index": test_index,
    }


def audit_bank_marketing() -> dict[str, Any]:
    """Reproduce the submitted random split and compare it to source-order holdout."""
    frame, features, target = _prepare_data()
    indices = np.arange(len(features))
    train_validation, random_test = train_test_split(
        indices,
        test_size=0.20,
        stratify=target,
        random_state=SEED,
    )
    random_train, random_validation = train_test_split(
        train_validation,
        test_size=0.25,
        stratify=target.iloc[train_validation],
        random_state=SEED,
    )
    random_result = _fit_split(
        features,
        target,
        random_train,
        random_validation,
        random_test,
    )
    n = len(features)
    chronological_train = np.arange(int(n * 0.60))
    chronological_validation = np.arange(int(n * 0.60), int(n * 0.80))
    chronological_test = np.arange(int(n * 0.80), n)
    chronological_result = _fit_split(
        features,
        target,
        chronological_train,
        chronological_validation,
        chronological_test,
    )

    random_actual = random_result["test_actual"]
    random_scores = random_result["test_scores"]
    chronological_actual = chronological_result["test_actual"]
    chronological_scores = chronological_result["test_scores"]
    auc_gap = _independent_gap_interval(
        random_actual,
        random_scores,
        chronological_actual,
        chronological_scores,
        roc_auc_score,
        seed=SEED + 10,
    )
    ap_gap = _independent_gap_interval(
        random_actual,
        random_scores,
        chronological_actual,
        chronological_scores,
        average_precision_score,
        seed=SEED + 11,
    )

    model_name = chronological_result["summary"]["model_selected"]
    time_base_scores = chronological_scores
    ablations = {}
    suspected_features = {
        "campaign": ([], ["campaign"]),
        "pdays and previous-contact flag": ([], ["pdays_clean", "prev_contacted"]),
        "previous campaign outcome": (["poutcome"], []),
        "current campaign month": (["month"], []),
    }
    for offset, (label, (drop_categorical, drop_numeric)) in enumerate(
        suspected_features.items(), start=20
    ):
        selected_categories = [
            column for column in CAT_COLUMNS if column not in drop_categorical
        ]
        selected_numeric = [column for column in NUM_COLUMNS if column not in drop_numeric]
        reduced = _model(model_name, selected_categories, selected_numeric)
        reduced.fit(
            features.iloc[chronological_train][selected_categories + selected_numeric],
            target.iloc[chronological_train],
        )
        reduced_scores = reduced.predict_proba(
            features.iloc[chronological_test][selected_categories + selected_numeric]
        )[:, 1]
        ap_difference = _paired_gap_interval(
            chronological_actual,
            time_base_scores,
            reduced_scores,
            average_precision_score,
            seed=SEED + offset,
        )
        auc_difference = _paired_gap_interval(
            chronological_actual,
            time_base_scores,
            reduced_scores,
            roc_auc_score,
            seed=SEED + offset + 10,
        )
        ablations[label] = {
            "reduced_test_pr_auc": float(
                average_precision_score(chronological_actual, reduced_scores)
            ),
            "reduced_test_roc_auc": float(
                roc_auc_score(chronological_actual, reduced_scores)
            ),
            "pr_auc_difference_reduced_minus_full": ap_difference[0],
            "pr_auc_difference_ci_95": ap_difference[1],
            "roc_auc_difference_reduced_minus_full": auc_difference[0],
            "roc_auc_difference_ci_95": auc_difference[1],
        }

    month_values = frame["month"].astype(str).to_numpy()
    month_transitions = int(np.sum(month_values[1:] != month_values[:-1]))
    return {
        "random_split": random_result["summary"],
        "source_order_split": chronological_result["summary"],
        "source_order_split_definition": {
            "train_fraction": 0.60,
            "validation_fraction": 0.20,
            "test_fraction": 0.20,
            "source_month_block_transitions": month_transitions,
            "year_or_full_timestamp_column_available": False,
            "interpretation": (
                "Source row order is a temporal proxy. The raw file is grouped into "
                "contiguous month blocks but has no year or full timestamp, so exact "
                "calendar chronology is unverified."
            ),
        },
        "test_split_gaps_source_order_minus_random": {
            "roc_auc": {"difference": auc_gap[0], "ci_95": auc_gap[1]},
            "pr_auc": {"difference": ap_gap[0], "ci_95": ap_gap[1]},
        },
        "source_order_feature_ablations": ablations,
        "data_and_feature_checks": {
            "n_total": int(len(frame)),
            "positive_prevalence": float(target.mean()),
            "duration_in_model_features": False,
            "duration_columns_in_features": False,
            "campaign_current_contact_risk": (
                "campaign counts current-campaign contacts including the last contact; "
                "it may not be available before choosing a call."
            ),
            "prior_campaign_fields": ["pdays", "previous", "poutcome"],
            "current_campaign_time_fields": ["month", "day_of_week"],
            "threshold_is_selected_on_validation": True,
            "test_used_to_select_model_or_threshold": False,
        },
        "private_predictions": {
            "random": (random_actual, random_scores),
            "source_order": (chronological_actual, chronological_scores),
        },
    }


def write_bank_audit_results(audit: dict[str, Any]) -> Path:
    """Persist aggregate audit evidence and findings to the case result record."""
    path = ROOT / "cases" / "01_bank_marketing" / "results.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    random = audit["random_split"]
    source_order = audit["source_order_split"]
    gaps = audit["test_split_gaps_source_order_minus_random"]
    roc_gap = gaps["roc_auc"]
    pr_gap = gaps["pr_auc"]

    findings = [
        {
            "finding_type": "Source-order performance",
            "severity": "Major",
            "ai_output_location": "Random 60/20/20 split and final test metrics",
            "measured_effect": (
                f"The source-order holdout's ROC-AUC is {roc_gap['difference']:.3f} "
                f"lower than the random-holdout result (95% CI "
                f"{roc_gap['ci_95'][0]:.3f} to {roc_gap['ci_95'][1]:.3f}). "
                f"The PR-AUC difference is {pr_gap['difference']:.3f} "
                f"(95% CI {pr_gap['ci_95'][0]:.3f} to {pr_gap['ci_95'][1]:.3f}), "
                "which includes zero."
            ),
            "effect_estimate": roc_gap["difference"],
            "ci_95": roc_gap["ci_95"],
            "corrected_effect": {
                "source_order_model_selected": source_order["model_selected"],
                "source_order_roc_auc": source_order["test_metrics"]["roc_auc"],
                "source_order_pr_auc": source_order["test_metrics"]["pr_auc"],
                "source_order_test_prevalence": source_order["test_metrics"]["prevalence"],
                "source_order_calibration_slope": source_order["test_calibration"][
                    "calibration_slope"
                ],
                "pr_auc_difference_source_order_minus_random": pr_gap["difference"],
                "pr_auc_difference_ci_95": pr_gap["ci_95"],
                "chronology_verified": False,
            },
            "notebook_cell": "audit_evidence.ipynb code cell 2",
        },
    ]
    audit_results = {
        key: value for key, value in audit.items() if key != "private_predictions"
    }
    record["ai_audit_status"] = "complete"
    record["ai_audit_verdict"] = "Partly reliable"
    record["audit_findings"] = findings
    record["corrected_results"] = {
        "independent_audit": audit_results,
        "ai_output_verified": {
            "saved_run_exit_code": 0,
            "repair_applied": False,
            "random_split_rows_reproduced": random["test_metrics"]["n"] == 9043,
            "random_split_roc_auc_reproduced": abs(
                random["test_metrics"]["roc_auc"] - 0.8026830197925456
            )
            < 1e-12,
            "random_split_pr_auc_reproduced": abs(
                random["test_metrics"]["pr_auc"] - 0.4603221804132021
            )
            < 1e-12,
            "validation_selected_threshold_reproduced": abs(
                random["threshold_selected_on_validation"] - 0.1956613856600986
            )
            < 1e-12,
        },
        "corrected_analysis": {
            "recommended_evaluation": (
                "Use a genuinely timestamped forward holdout when deployment is "
                "intended for later campaigns; source-row order is only a stress test."
            ),
            "source_order_holdout": {
                "train_fraction": 0.60,
                "validation_fraction": 0.20,
                "test_fraction": 0.20,
                "test_metrics": source_order["test_metrics"],
                "calibration": source_order["test_calibration"],
            },
        },
    }
    path.write_text(json.dumps(record, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return path


def render_bank_audit_markdown(result_path: Path | None = None) -> Path:
    """Render the case audit from the persisted aggregate results."""
    result_path = result_path or ROOT / "cases" / "01_bank_marketing" / "results.json"
    record = json.loads(result_path.read_text(encoding="utf-8"))
    corrected = record["corrected_results"]
    audit = corrected["independent_audit"]
    random = audit["random_split"]
    source = audit["source_order_split"]
    gaps = audit["test_split_gaps_source_order_minus_random"]
    checks = audit["data_and_feature_checks"]
    random_test = random["test_metrics"]
    source_test = source["test_metrics"]
    roc_gap = gaps["roc_auc"]
    pr_gap = gaps["pr_auc"]
    lines = [
        "# Case 01 audit: Bank Marketing",
        "",
        f"**Verdict: {record['ai_audit_verdict']}**",
        "",
        "## Question and scope",
        "",
        (
            "The submitted code predicts term-deposit subscription from the UCI Bank "
            "Marketing records. This audit reproduces its saved random split and tests "
            "a source-row-order holdout. Since the data has month and weekday but no "
            "year or complete timestamp, that second split is a stress test, not a "
            "verified chronological evaluation."
        ),
        "",
        "## Reproduction",
        "",
        (
            f"The saved run and independent reproduction both use {checks['n_total']:,} "
            f"rows, with {checks['positive_prevalence']:.1%} subscribed. The random "
            "60/20/20 split selected gradient boosting on validation PR-AUC and "
            f"reproduced test ROC-AUC {random_test['roc_auc']:.3f}, PR-AUC "
            f"{random_test['pr_auc']:.3f} versus prevalence baseline "
            f"{random_test['prevalence']:.3f}, and top-20% lift "
            f"{random['top_20_percent']['lift_over_test_prevalence']:.2f}x. "
            "The AI output's headline values matched."
        ),
        "",
        "## Generalization and calibration check",
        "",
        (
            f"The 60/20/20 source-order split selected {source['model_selected']}. "
            f"Its test ROC-AUC was {source_test['roc_auc']:.3f} "
            f"(95% bootstrap CI {source['test_roc_auc_ci_95'][0]:.3f} to "
            f"{source['test_roc_auc_ci_95'][1]:.3f}) and PR-AUC "
            f"{source_test['pr_auc']:.3f} (95% CI "
            f"{source['test_pr_auc_ci_95'][0]:.3f} to "
            f"{source['test_pr_auc_ci_95'][1]:.3f}), at test prevalence "
            f"{source_test['prevalence']:.1%}."
        ),
        (
            f"Compared with the random split, source-order ROC-AUC changed by "
            f"{roc_gap['difference']:.3f} (95% CI {roc_gap['ci_95'][0]:.3f} to "
            f"{roc_gap['ci_95'][1]:.3f}). The PR-AUC change was "
            f"{pr_gap['difference']:.3f} (95% CI {pr_gap['ci_95'][0]:.3f} to "
            f"{pr_gap['ci_95'][1]:.3f}), which does not establish a difference. "
            f"Source-order calibration also worsened: slope "
            f"{source['test_calibration']['calibration_slope']:.3f}, intercept "
            f"{source['test_calibration']['calibration_intercept']:.3f}, and "
            f"decile ECE {source['test_calibration']['expected_calibration_error_deciles']:.3f}."
        ),
        (
            f"The source-order test prevalence ({source_test['prevalence']:.1%}) is "
            f"substantially above the random test prevalence ({random_test['prevalence']:.1%}). "
            "The source-order comparison also selects a different model. These results "
            "are evidence that the random holdout alone cannot establish performance "
            "on later records; they do not establish the exact future-campaign error. "
            "The submitted output reports random-holdout performance and does not "
            "explicitly claim future-campaign validity, so the source-order difference "
            "limits generalization rather than contradicting the reported test score."
        ),
        "",
        "## Feature and threshold checks",
        "",
        (
            "Duration is excluded as a post-call field, and validation—not the test "
            "set—selects the model and F1 threshold. The random split's calibration "
            f"slope is {random['test_calibration']['calibration_slope']:.3f}, "
            f"intercept {random['test_calibration']['calibration_intercept']:.3f}, "
            f"and decile ECE "
            f"{random['test_calibration']['expected_calibration_error_deciles']:.3f}."
        ),
        (
            "The code includes `campaign`, which counts contacts during the current "
            "campaign including the last contact. Confirm that the value is available "
            "at the exact intended scoring moment; the supplied records cannot establish "
            "the production data-availability contract."
        ),
        (
            "Source-order feature ablations were treated as exploratory sensitivity "
            "checks. Removing campaign count barely changed PR-AUC; removing previous "
            "campaign outcome reduced it. Removing previous-contact fields increased "
            "it on this particular holdout, so those fields should be checked for "
            "stability rather than assumed helpful."
        ),
        "",
        "## Findings",
        "",
        "| # | Finding | Severity | Measured evidence |",
        "|---|---|---|---|",
    ]
    for index, finding in enumerate(record["audit_findings"], start=1):
        lines.append(
            f"| {index} | {finding['finding_type']} | {finding['severity']} | "
            f"{finding['measured_effect']} |"
        )
    lines.extend(
        [
            "",
            "## Conclusion",
            "",
            (
                "The submitted analysis is reproducible and its random-holdout metrics "
                "are computed correctly. Its validation-selected model and threshold "
                "avoid test-set selection, and duration is properly excluded. However, "
                "the random split only supports within-dataset random-holdout claims. "
                "The source-order stress test shows lower ranking performance and poor "
                "calibration, but chronology is not verifiable without full timestamps. "
                "A timestamped future-campaign holdout and confirmation of feature "
                "availability are needed before interpreting these scores as deployment "
                "performance."
            ),
            "",
        ]
    )
    path = result_path.parent / "audit.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
