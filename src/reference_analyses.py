"""Blind, reproducible reference analyses for the five fetched non-Olist cases."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from scipy import stats
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from statsmodels.formula.api import logit

from audit_tools import (
    adjust_pvalues,
    binary_metrics,
    bootstrap_ci,
    majority_class_baseline,
    stratified_comparison,
    wilson_interval,
)
from fetch_data import parse_arff

ROOT = Path(__file__).resolve().parents[1]
CASE_IDS = (
    "01_bank_marketing",
    "02_telco_churn",
    "04_simpsons_paradox",
    "05_multiple_comparisons",
    "06_iris_control",
)
SEED = 20261016


def data_directory() -> Path:
    """Resolve DATA_DIR consistently with the downloader and sandbox runner."""
    load_dotenv(ROOT / ".env")
    configured = Path(os.getenv("DATA_DIR", "data"))
    return configured if configured.is_absolute() else ROOT / configured


def load_case_data(case: str) -> pd.DataFrame:
    """Load one already-downloaded real source file without generating data."""
    raw = data_directory() / "raw"
    if case in {"01_bank_marketing", "06_iris_control"}:
        filenames = {
            "01_bank_marketing": "01_bank_marketing/data.csv",
            "06_iris_control": "06_iris_control/data.csv",
        }
        return pd.read_csv(raw / filenames[case], sep=None, engine="python")
    if case in {"02_telco_churn", "05_multiple_comparisons"}:
        filenames = {
            "02_telco_churn": "02_telco_churn/telco-customer-churn.arff",
            "05_multiple_comparisons": "05_multiple_comparisons/adult.arff",
        }
        payload = (raw / filenames[case]).read_bytes()
        lines = payload.decode("utf-8-sig").splitlines()
        fields = parse_arff(payload)[2]
        data_start = next(
            index for index, line in enumerate(lines) if line.strip().lower() == "@data"
        )
        records = csv.reader(
            (
                line
                for line in lines[data_start + 1 :]
                if line.strip() and not line.lstrip().startswith("%")
            ),
            quotechar="'",
            skipinitialspace=True,
        )
        frame = pd.DataFrame(
            [[value.strip() for value in row] for row in records],
            columns=fields,
        )
        if case == "05_multiple_comparisons":
            frame = frame.replace("?", np.nan)
            numeric_columns = (
                "age",
                "fnlwgt",
                "education-num",
                "capital-gain",
                "capital-loss",
                "hours-per-week",
            )
        else:
            numeric_columns = (
                "SeniorCitizen",
                "tenure",
                "MonthlyCharges",
                "TotalCharges",
            )
        for column in numeric_columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
        return frame
    if case == "04_simpsons_paradox":
        frame = pd.read_csv(raw / "04_simpsons_paradox" / "UCBAdmissions.csv")
        if str(frame.columns[0]).lower() in {"rownames", "unnamed: 0"}:
            frame = frame.drop(columns=frame.columns[0])
        return frame
    raise ValueError(f"Unsupported reference case: {case}")


def _json_value(value: Any) -> Any:
    """Convert NumPy and pandas scalars into JSON-compatible Python values."""
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if isinstance(value, pd.DataFrame):
        return [_json_value(row) for row in value.to_dict(orient="records")]
    if isinstance(value, np.ndarray):
        return [_json_value(item) for item in value.tolist()]
    if isinstance(value, np.generic):
        return value.item()
    if pd.isna(value):
        return None
    return value


def _interval_dict(successes: int, total: int) -> dict[str, float | int]:
    lower, upper = wilson_interval(successes, total)
    return {
        "successes": successes,
        "n": total,
        "rate": successes / total if total else float("nan"),
        "ci_95_lower": lower,
        "ci_95_upper": upper,
    }


def _group_rates(
    frame: pd.DataFrame,
    group_column: str,
    positive: pd.Series,
) -> list[dict[str, Any]]:
    """Summarize a binary outcome by all observed levels of a grouping variable."""
    table: list[dict[str, Any]] = []
    group_values = frame[group_column].astype(object).where(frame[group_column].notna(), "Missing")
    grouped = pd.DataFrame({"group": group_values, "positive": positive.astype(bool)})
    for label, sample in grouped.groupby("group", sort=True, observed=True):
        sample_positive = int(sample["positive"].sum())
        table.append(
            {
                "group": str(label),
                **_interval_dict(sample_positive, len(sample)),
            }
        )
    return table


def run_bank_marketing() -> dict[str, Any]:
    """Fit a leakage-aware term-deposit model and evaluate a held-out test set."""
    frame = load_case_data("01_bank_marketing")
    target = frame["y"].map({"yes": 1, "no": 0}).astype(int)
    features = frame.drop(columns=["y", "duration"])
    train_x, test_x, train_y, test_y = train_test_split(
        features,
        target,
        test_size=0.2,
        stratify=target,
        random_state=42,
    )
    numeric_columns = train_x.select_dtypes(include=[np.number]).columns.tolist()
    categorical_columns = [column for column in train_x.columns if column not in numeric_columns]
    numeric_pipeline = Pipeline(
        [("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]
    )
    categorical_pipeline = Pipeline(
        [
            ("impute", SimpleImputer(strategy="most_frequent")),
            ("encode", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    model = Pipeline(
        [
            (
                "preprocess",
                ColumnTransformer(
                    [
                        ("numeric", numeric_pipeline, numeric_columns),
                        ("categorical", categorical_pipeline, categorical_columns),
                    ]
                ),
            ),
            ("logistic_regression", LogisticRegression(max_iter=1000, random_state=42)),
        ]
    )
    model.fit(train_x, train_y)
    scores = model.predict_proba(test_x)[:, 1]
    predictions = model.predict(test_x)
    metrics = binary_metrics(test_y, scores)
    ap_ci = bootstrap_ci(
        np.column_stack([test_y.to_numpy(), scores]),
        lambda rows: __import__("sklearn.metrics", fromlist=["average_precision_score"])
        .average_precision_score(rows[:, 0].astype(int), rows[:, 1]),
        n_resamples=400,
        random_state=42,
    )
    roc_ci = bootstrap_ci(
        np.column_stack([test_y.to_numpy(), scores]),
        lambda rows: __import__("sklearn.metrics", fromlist=["roc_auc_score"])
        .roc_auc_score(rows[:, 0].astype(int), rows[:, 1]),
        n_resamples=400,
        random_state=43,
    )
    majority = majority_class_baseline(train_y)
    baseline_label = majority["majority_class"]
    return {
        "case": "01_bank_marketing",
        "question": (
            "Build a model to predict which customers will subscribe to a term deposit "
            "and tell me how good it is."
        ),
        "method": (
            "Stratified 80/20 holdout; preprocessing fit within a logistic-regression "
            "pipeline; duration excluded because it is recorded during/after the call; "
            "no class reweighting."
        ),
        "n_total": len(frame),
        "n_train": len(train_x),
        "n_test": len(test_x),
        "positive_prevalence_test": metrics["prevalence"],
        "test_metrics": {
            **metrics,
            "accuracy": float(accuracy_score(test_y, predictions)),
            "majority_class_baseline_accuracy": float((test_y == baseline_label).mean()),
        },
        "intervals": {
            "average_precision_ci_95": ap_ci,
            "roc_auc_ci_95": roc_ci,
        },
        "limitations": [
            (
                "The random holdout estimates performance for records from this dataset, "
                "not future campaigns or a new institution."
            ),
            "Threshold-specific utility and deployment costs were not supplied.",
            (
                "Predictive associations do not identify effects of changing customer "
                "contact or product policy."
            ),
        ],
    }


def run_telco_churn() -> dict[str, Any]:
    """Summarize churn by contract and fit a covariate-adjusted association model."""
    frame = load_case_data("02_telco_churn")
    frame["Churn_binary"] = frame["Churn"].map({"Yes": 1, "No": 0}).astype(int)
    frame["SeniorCitizen"] = pd.to_numeric(frame["SeniorCitizen"], errors="raise")
    contract = _group_rates(frame, "Contract", frame["Churn_binary"].astype(bool))
    fitted = logit(
        "Churn_binary ~ C(Contract, Treatment(reference='Month-to-month')) + "
        "tenure + MonthlyCharges + SeniorCitizen + C(PaymentMethod) + "
        "C(InternetService) + C(Partner) + C(Dependents)",
        data=frame,
    ).fit(disp=False)
    intervals = fitted.conf_int()
    contract_effects = []
    for term in fitted.params.index:
        if term.startswith("C(Contract,"):
            contract_effects.append(
                {
                    "term": term,
                    "odds_ratio": float(np.exp(fitted.params[term])),
                    "ci_95_lower": float(np.exp(intervals.loc[term, 0])),
                    "ci_95_upper": float(np.exp(intervals.loc[term, 1])),
                    "p_value": float(fitted.pvalues[term]),
                }
            )
    return {
        "case": "02_telco_churn",
        "question": (
            "What drives customer churn? Which factors are most associated with churn, "
            "and what can this dataset establish about contract type?"
        ),
        "method": (
            "Descriptive churn rates by contract with Wilson intervals; logistic association "
            "model adjusted for tenure, monthly charges, senior-citizen status, payment "
            "method, internet service, partner, and dependents."
        ),
        "n_total": len(frame),
        "churn_prevalence": float(frame["Churn_binary"].mean()),
        "contract_rates": contract,
        "adjusted_contract_odds_ratios": contract_effects,
        "model_n": int(fitted.nobs),
        "limitations": [
            (
                "This is an observational customer dataset; adjusted odds ratios are not "
                "causal effects."
            ),
            (
                "The covariate set is limited to recorded fields and cannot remove "
                "unmeasured confounding."
            ),
            (
                "The source is a sample dataset; results do not establish effects for a "
                "specific future intervention or population."
            ),
        ],
    }


def run_berkeley_admissions() -> dict[str, Any]:
    """Compare admission proportions by gender overall and within departments."""
    frame = load_case_data("04_simpsons_paradox")
    frame["Freq"] = pd.to_numeric(frame["Freq"], errors="raise").astype(int)
    expanded_exposure = np.repeat(frame["Gender"].eq("Female").to_numpy(), frame["Freq"])
    expanded_outcome = np.repeat(frame["Admit"].eq("Admitted").to_numpy(), frame["Freq"])
    expanded_dept = np.repeat(frame["Dept"].to_numpy(), frame["Freq"])
    overall = {}
    for gender in ("Female", "Male"):
        rows = frame["Gender"].eq(gender)
        admitted = int(frame.loc[rows & frame["Admit"].eq("Admitted"), "Freq"].sum())
        total = int(frame.loc[rows, "Freq"].sum())
        overall[gender] = _interval_dict(admitted, total)
    by_department = []
    for (department, gender), group in frame.groupby(["Dept", "Gender"], sort=True):
        admitted = int(group.loc[group["Admit"].eq("Admitted"), "Freq"].sum())
        total = int(group["Freq"].sum())
        by_department.append(
            {"department": department, "gender": gender, **_interval_dict(admitted, total)}
        )
    cmh = stratified_comparison(expanded_exposure, expanded_outcome, expanded_dept)
    return {
        "case": "04_simpsons_paradox",
        "question": (
            "How do admission rates differ by applicant gender overall and within "
            "departments in the 1973 Berkeley data?"
        ),
        "method": (
            "Reconstruct applicant counts from the 24-cell contingency table; Wilson "
            "intervals for gender and department rates; Cochran-Mantel-Haenszel common "
            "odds ratio across departments."
        ),
        "n_applicants": int(frame["Freq"].sum()),
        "overall_rates": overall,
        "department_rates": by_department,
        "cmh": {
            "female_vs_male_common_odds_ratio": cmh["cmh_common_odds_ratio"],
            "odds_ratio_ci_95": cmh["cmh_odds_ratio_ci"],
            "test_statistic": cmh["cmh_statistic"],
            "p_value": cmh["cmh_p_value"],
        },
        "limitations": [
            "The data are aggregated counts from one institution and one admissions cycle.",
            (
                "Department-level comparisons are descriptive; applicant qualifications "
                "and application choices are not represented in the table."
            ),
            (
                "Neither the marginal nor stratified association identifies discrimination "
                "or a causal mechanism."
            ),
        ],
    }


def run_adult_income() -> dict[str, Any]:
    """Describe sample income rates with intervals across recorded attributes."""
    frame = load_case_data("05_multiple_comparisons")
    positive = frame["class"].eq(">50K")
    frame = frame.assign(
        age_band=pd.cut(
            pd.to_numeric(frame["age"], errors="raise"),
            bins=[0, 25, 35, 45, 55, np.inf],
            right=False,
            labels=["under-25", "25-34", "35-44", "45-54", "55+"],
        )
    )
    positive = positive.loc[frame.index]
    return {
        "case": "05_multiple_comparisons",
        "question": (
            "Which recorded characteristics are associated with income above $50,000 "
            "in this dataset?"
        ),
        "method": (
            "Descriptive sample proportions and Wilson score intervals by age band, "
            "education, sex, and workclass; no causal interpretation or data-driven "
            "hypothesis selection."
        ),
        "n_total": len(frame),
        "positive_count": int(positive.sum()),
        "positive_prevalence": float(positive.mean()),
        "group_rates": {
            column: _group_rates(frame, column, positive)
            for column in ("age_band", "education", "sex", "workclass")
        },
        "limitations": [
            (
                "Intervals describe this extracted sample and do not account for the "
                "Census sampling design."
            ),
            (
                "The `fnlwgt` field is not used as a design weight because the public "
                "extract lacks the full design information needed for design-based "
                "uncertainty."
            ),
            (
                "Group differences are descriptive associations; they do not establish "
                "the effects of changing a recorded characteristic."
            ),
        ],
    }


def run_iris_control() -> dict[str, Any]:
    """Report per-species measurement means, intervals, and descriptive tests."""
    frame = load_case_data("06_iris_control")
    species_column = "class"
    measurements = ["sepal length", "sepal width", "petal length", "petal width"]
    species_results: list[dict[str, Any]] = []
    tests: list[dict[str, Any]] = []
    for measure in measurements:
        samples = [
            frame.loc[frame[species_column].eq(species), measure].astype(float).to_numpy()
            for species in sorted(frame[species_column].unique())
        ]
        test = stats.kruskal(*samples)
        tests.append(
            {
                "measurement": measure,
                "kruskal_statistic": float(test.statistic),
                "p_raw": float(test.pvalue),
            }
        )
        for species, values in zip(sorted(frame[species_column].unique()), samples, strict=True):
            mean = float(values.mean())
            standard_error = float(stats.sem(values))
            lower, upper = stats.t.interval(
                0.95,
                df=len(values) - 1,
                loc=mean,
                scale=standard_error,
            )
            species_results.append(
                {
                    "species": species,
                    "measurement": measure,
                    "n": int(len(values)),
                    "mean_cm": mean,
                    "ci_95_lower_cm": float(lower),
                    "ci_95_upper_cm": float(upper),
                }
            )
    adjusted = adjust_pvalues([test["p_raw"] for test in tests])
    for index, test in enumerate(tests):
        test["p_bonferroni"] = float(adjusted.loc[index, "p_bonferroni"])
        test["p_bh"] = float(adjusted.loc[index, "p_bh"])
    return {
        "case": "06_iris_control",
        "question": (
            "For each iris species in this sample, summarize sepal and petal measurements "
            "with uncertainty intervals, compare the species descriptively, and state what "
            "these data do and do not support."
        ),
        "method": (
            "Species-specific means and 95% t intervals for four measurements; "
            "Kruskal-Wallis comparisons with Bonferroni and Benjamini-Hochberg adjustment "
            "across the four prespecified measurement tests."
        ),
        "n_total": len(frame),
        "species_measurements": species_results,
        "species_tests": tests,
        "limitations": [
            (
                "Intervals quantify mean uncertainty under independent-sample assumptions; "
                "they are not prediction intervals for individual flowers."
            ),
            (
                "The dataset is a small historical sample with limited provenance for a "
                "broader target population."
            ),
            (
                "Species differences in these measurements are descriptive and do not "
                "establish biological mechanisms or causal effects."
            ),
        ],
    }


ANALYSES = {
    "01_bank_marketing": run_bank_marketing,
    "02_telco_churn": run_telco_churn,
    "04_simpsons_paradox": run_berkeley_admissions,
    "05_multiple_comparisons": run_adult_income,
    "06_iris_control": run_iris_control,
}


def run_reference(case: str) -> dict[str, Any]:
    """Run and return a single blind reference analysis using local source data."""
    if case not in ANALYSES:
        raise ValueError(f"Unsupported reference case: {case}")
    return _json_value(ANALYSES[case]())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True, choices=CASE_IDS)
    arguments = parser.parse_args()
    print(json.dumps(run_reference(arguments.case), indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())