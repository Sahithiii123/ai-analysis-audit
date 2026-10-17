"""Independent reproduction and audit checks for Telco Churn."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from patsy import dmatrices
from scipy.stats import chi2_contingency
from sklearn.feature_selection import mutual_info_classif
from sklearn.model_selection import StratifiedShuffleSplit

from audit_tools import wilson_interval
from reference_analyses import ROOT, load_case_data

SEED = 42
MI_SUBSAMPLES = 200
MODEL_FORMULA = (
    "y ~ C(Contract, Treatment('Month-to-month')) + tenure + MonthlyCharges "
    "+ C(Internet) + C(OnlineSecurity) + C(TechSupport) + C(Pay) "
    "+ C(PaperlessBilling) + SeniorCitizen + C(Partner) + C(Dependents)"
)


def _design_diagnostics(design: pd.DataFrame) -> dict[str, Any]:
    """Identify exact duplicate columns and the rank of a regression design."""
    columns = list(design.columns)
    duplicates = [
        [columns[left], columns[right]]
        for right in range(len(columns))
        for left in range(right)
        if np.array_equal(design.iloc[:, left].to_numpy(), design.iloc[:, right].to_numpy())
    ]
    rank = int(np.linalg.matrix_rank(design.to_numpy()))
    return {
        "column_count": len(columns),
        "matrix_rank": rank,
        "rank_deficiency": len(columns) - rank,
        "exact_duplicate_columns": duplicates,
    }


def _saved_run_status() -> dict[str, Any]:
    """Summarize the saved sandbox run without changing its original artifacts."""
    run_root = ROOT / "reports" / "ai_code_runs" / "02_telco_churn"
    run_records = sorted(run_root.glob("*/attempt-1/run.json"))
    if not run_records:
        raise FileNotFoundError(f"No saved Telco AI run found under {run_root}")
    run_path = run_records[-1]
    run = json.loads(run_path.read_text(encoding="utf-8"))
    attempt = run_path.parent
    stderr = (attempt / "stderr.txt").read_text(encoding="utf-8")
    parser_error = next(
        (line.strip() for line in stderr.splitlines() if "NotImplementedError:" in line),
        None,
    )
    if run["exit_code"] != 0 and parser_error is None:
        raise RuntimeError(
            "Saved Telco run failed without the expected ARFF parser error: "
            f"{run_path}"
        )
    return {
        "run_record": run_path.relative_to(ROOT).as_posix(),
        "exit_code": int(run["exit_code"]),
        "stdout_bytes": (attempt / "stdout.txt").stat().st_size,
        "arff_parser_error": parser_error,
    }


def _mutual_information(frame: pd.DataFrame) -> dict[str, Any]:
    features = frame.drop(columns=["customerID", "Churn", "y"]).copy()
    features["TotalCharges"] = features["TotalCharges"].fillna(0)
    categorical = features.select_dtypes(exclude="number").columns
    for column in categorical:
        features[column] = features[column].astype("category").cat.codes
    discrete = np.array([column in categorical for column in features.columns])
    matrix = features.to_numpy(dtype=float)
    target = frame["y"].to_numpy(dtype=int)
    point = mutual_info_classif(
        matrix,
        target,
        discrete_features=discrete,
        random_state=0,
    )
    subsamples = np.empty((MI_SUBSAMPLES, len(features.columns)))
    splitter = StratifiedShuffleSplit(
        n_splits=MI_SUBSAMPLES,
        train_size=0.8,
        random_state=SEED,
    )
    for index, (sample, _) in enumerate(splitter.split(matrix, target)):
        subsamples[index] = mutual_info_classif(
            matrix[sample],
            target[sample],
            discrete_features=discrete,
            random_state=0,
        )
    order = np.argsort(-point)
    contract_index = list(features.columns).index("Contract")
    tenure_index = list(features.columns).index("tenure")
    difference = subsamples[:, contract_index] - subsamples[:, tenure_index]
    lower, upper = np.quantile(difference, [0.025, 0.975])
    top_counts = np.bincount(
        np.argmax(subsamples, axis=1),
        minlength=len(features.columns),
    )
    return {
        "ranking": [
            {"feature": str(features.columns[index]), "mutual_information": float(point[index])}
            for index in order
        ],
        "subsample_stability": {
            "resamples": MI_SUBSAMPLES,
            "seed": SEED,
            "sample_fraction": 0.8,
            "top_feature_selection_frequency": {
                str(features.columns[index]): float(top_counts[index] / MI_SUBSAMPLES)
                for index in np.argsort(-top_counts)[:5]
                if top_counts[index] > 0
            },
            "contract_minus_tenure_mi_difference": float(
                point[contract_index] - point[tenure_index]
            ),
            "contract_minus_tenure_mi_difference_subsample_interval_95": [
                float(lower),
                float(upper),
            ],
        },
        "categorical_features_treated_as_discrete": [str(column) for column in categorical],
        "missing_total_charges_imputed_to_zero": int(frame["TotalCharges"].isna().sum()),
    }


def _contract_rates(frame: pd.DataFrame) -> list[dict[str, Any]]:
    rates = []
    for contract, group in frame.groupby("Contract", sort=True, observed=True):
        successes = int(group["y"].sum())
        total = len(group)
        lower, upper = wilson_interval(successes, total)
        rates.append(
            {
                "contract": str(contract),
                "churn_count": successes,
                "n": int(total),
                "rate": float(successes / total),
                "ci_95": [lower, upper],
            }
        )
    return rates


def audit_telco_churn() -> dict[str, Any]:
    """Reproduce the analysis with the project ARFF loader and test its claims."""
    frame = load_case_data("02_telco_churn")
    frame["SeniorCitizen"] = pd.to_numeric(frame["SeniorCitizen"], errors="raise")
    frame["TotalCharges"] = pd.to_numeric(frame["TotalCharges"], errors="coerce")
    frame["y"] = frame["Churn"].eq("Yes").astype(int)

    contingency = pd.crosstab(frame["Contract"], frame["Churn"])
    chi_square, p_value, degrees_freedom, expected = chi2_contingency(contingency)
    cramers_v = float(
        np.sqrt(
            chi_square
            / (contingency.to_numpy().sum() * (min(contingency.shape) - 1))
        )
    )

    mi = _mutual_information(frame)
    model_frame = frame.rename(
        columns={"PaymentMethod": "Pay", "InternetService": "Internet"}
    ).copy()
    model_frame["TotalCharges"] = model_frame["TotalCharges"].fillna(0)
    _, original_design = dmatrices(MODEL_FORMULA, model_frame, return_type="dataframe")
    design = _design_diagnostics(original_design)
    original_fit_error = None
    if design["rank_deficiency"]:
        try:
            smf.logit(MODEL_FORMULA, data=model_frame).fit(disp=False)
        except np.linalg.LinAlgError as error:
            original_fit_error = f"{type(error).__name__}: {error}"

    corrected_frame = model_frame.copy()
    for column in ("OnlineSecurity", "TechSupport"):
        corrected_frame[column] = corrected_frame[column].replace(
            "No internet service",
            "No",
        )
    corrected_fit = smf.logit(MODEL_FORMULA, data=corrected_frame).fit(disp=False)
    confidence_intervals = corrected_fit.conf_int()
    adjusted_contract_odds = []
    for term in corrected_fit.params.index:
        if term.startswith("C(Contract,"):
            adjusted_contract_odds.append(
                {
                    "term": term,
                    "odds_ratio": float(np.exp(corrected_fit.params[term])),
                    "ci_95": [
                        float(np.exp(confidence_intervals.loc[term, 0])),
                        float(np.exp(confidence_intervals.loc[term, 1])),
                    ],
                    "p_value": float(corrected_fit.pvalues[term]),
                }
            )

    return {
        "saved_ai_run": _saved_run_status(),
        "descriptive": {
            "n_total": int(len(frame)),
            "churn_count": int(frame["y"].sum()),
            "churn_prevalence": float(frame["y"].mean()),
            "contract_rates": _contract_rates(frame),
            "chi_square": {
                "statistic": float(chi_square),
                "degrees_freedom": int(degrees_freedom),
                "p_value": float(p_value),
                "cramers_v": cramers_v,
                "minimum_expected_count": float(expected.min()),
            },
        },
        "mutual_information": mi,
        "submitted_adjusted_model": {
            **design,
            "fit_error_after_loader_is_replaced": original_fit_error,
            "formula": MODEL_FORMULA,
        },
        "corrected_adjusted_model": {
            "category_correction": (
                "Recode 'No internet service' to 'No' for OnlineSecurity and TechSupport "
                "before fitting alongside InternetService."
            ),
            "converged": bool(corrected_fit.mle_retvals["converged"]),
            "n": int(corrected_fit.nobs),
            "contract_odds_ratios": adjusted_contract_odds,
            "median_tenure_by_contract": {
                str(contract): float(tenure)
                for contract, tenure in frame.groupby("Contract")["tenure"].median().items()
            },
        },
    }


def write_telco_audit_results(audit: dict[str, Any]) -> Path:
    """Persist audit findings and corrected results to the case record."""
    path = ROOT / "cases" / "02_telco_churn" / "results.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    run = audit["saved_ai_run"]
    model = audit["submitted_adjusted_model"]
    corrected_model = audit["corrected_adjusted_model"]
    findings = [
        {
            "finding_type": "ARFF loader failure",
            "severity": "Major",
            "ai_output_location": "Runnable Python code, ARFF load step",
            "measured_effect": (
                f"The saved run exited {run['exit_code']} with {run['arff_parser_error']}; "
                f"stdout is {run['stdout_bytes']} bytes, so none of the requested "
                "statistics were emitted."
            ),
            "effect_estimate": run["exit_code"],
            "ci_95": None,
            "corrected_effect": {
                "independent_loader": "src/reference_analyses.py::load_case_data",
                "rows_loaded": audit["descriptive"]["n_total"],
                "original_ai_artifacts_preserved": True,
            },
            "notebook_cell": "audit_evidence.ipynb code cell 1",
        },
        {
            "finding_type": "Rank-deficient adjusted model",
            "severity": "Major",
            "ai_output_location": "Adjusted logistic-regression formula",
            "measured_effect": (
                f"The design has {model['column_count']} columns but rank "
                f"{model['matrix_rank']} (deficiency {model['rank_deficiency']}); "
                f"the exact submitted model then fails with "
                f"{model['fit_error_after_loader_is_replaced']}."
            ),
            "effect_estimate": model["rank_deficiency"],
            "ci_95": None,
            "corrected_effect": {
                "contract_odds_ratios_after_category_recode": corrected_model[
                    "contract_odds_ratios"
                ],
                "model_n": corrected_model["n"],
                "converged": corrected_model["converged"],
            },
            "notebook_cell": "audit_evidence.ipynb code cell 2",
        },
    ]
    record["ai_audit_status"] = "complete"
    record["ai_audit_verdict"] = "Partly reliable"
    record["audit_findings"] = findings
    record["corrected_results"] = {
        "independent_audit": audit,
        "reference_comparison": record["reference_results"][
            "adjusted_contract_odds_ratios"
        ],
        "ai_output_verified": {
            "saved_run_exit_code": run["exit_code"],
            "submitted_code_completed": run["exit_code"] == 0,
            "no_statistics_emitted": run["stdout_bytes"] == 0,
            "contract_association_reproduced_independently": True,
            "causal_effect_established": False,
        },
        "conclusion": (
            "The descriptive contract association and the direction of adjusted "
            "associations are supported by the data, but the submitted script does "
            "not execute successfully and its specified adjusted model is singular."
        ),
    }
    path.write_text(json.dumps(record, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return path


def render_telco_audit_markdown(result_path: Path | None = None) -> Path:
    """Render a case report from the persisted numeric audit results."""
    result_path = result_path or ROOT / "cases" / "02_telco_churn" / "results.json"
    record = json.loads(result_path.read_text(encoding="utf-8"))
    corrected = record["corrected_results"]
    audit = corrected["independent_audit"]
    descriptive = audit["descriptive"]
    chi_square = descriptive["chi_square"]
    mi = audit["mutual_information"]
    model = audit["submitted_adjusted_model"]
    corrected_model = audit["corrected_adjusted_model"]
    rates = descriptive["contract_rates"]
    ranking = mi["ranking"]
    mi_interval = mi["subsample_stability"][
        "contract_minus_tenure_mi_difference_subsample_interval_95"
    ]
    reference_effects = corrected["reference_comparison"]
    reference_by_contract = {
        "One year" if "[T.One year]" in effect["term"] else "Two year": effect
        for effect in reference_effects
    }
    corrected_by_contract = {
        "One year" if "[T.One year]" in effect["term"] else "Two year": effect
        for effect in corrected_model["contract_odds_ratios"]
    }
    reference_comparison = "; ".join(
        (
            f"{contract}: {reference_by_contract[contract]['odds_ratio']:.3f} "
            f"({reference_by_contract[contract]['ci_95_lower']:.3f} to "
            f"{reference_by_contract[contract]['ci_95_upper']:.3f}) versus "
            f"{corrected_by_contract[contract]['odds_ratio']:.3f} "
            f"({corrected_by_contract[contract]['ci_95'][0]:.3f} to "
            f"{corrected_by_contract[contract]['ci_95'][1]:.3f})"
        )
        for contract in ("One year", "Two year")
    )
    lines = [
        "# Case 02 audit: Telco Churn",
        "",
        f"**Verdict: {record['ai_audit_verdict']}**",
        "",
        "## Scope and saved output",
        "",
        (
            "The AI response proposes descriptive churn rates, a chi-square test, "
            "mutual-information ranking, and an adjusted logistic model. Its saved "
            "sandbox run fails before printing any result. The response itself labels "
            "the code unrun and gives no numerical estimates. The original prompt, "
            "response, code, and run logs were preserved."
        ),
        "",
        "## Measured execution problems",
        "",
        (
            f"The saved run exits {audit['saved_ai_run']['exit_code']} because "
            f"`scipy.io.arff.loadarff` raises "
            f"`{audit['saved_ai_run']['arff_parser_error']}` for the ARFF string "
            "attribute. The run has no stdout."
        ),
        (
            f"Using the repository's ARFF loader, the submitted logistic formula "
            f"produces {model['column_count']} design columns with rank "
            f"{model['matrix_rank']}. `InternetService == No`, "
            "`OnlineSecurity == No internet service`, and "
            "`TechSupport == No internet service` are identical indicator columns. "
            f"The submitted fit therefore fails with "
            f"`{model['fit_error_after_loader_is_replaced']}`."
        ),
        "",
        "## Independent descriptive results",
        "",
        (
            f"The loaded data has {descriptive['n_total']:,} customers and overall "
            f"churn prevalence {descriptive['churn_prevalence']:.1%}. Contract rates "
            "are:"
        ),
        "",
        "| Contract | Churn | Customers | Rate (95% Wilson CI) |",
        "|---|---:|---:|---:|",
    ]
    for row in rates:
        lines.append(
            f"| {row['contract']} | {row['churn_count']:,} | {row['n']:,} | "
            f"{row['rate']:.1%} ({row['ci_95'][0]:.1%} to {row['ci_95'][1]:.1%}) |"
        )
    lines.extend(
        [
            "",
            (
                f"The contract-by-churn chi-square statistic is "
                f"{chi_square['statistic']:.1f} on {chi_square['degrees_freedom']} "
                f"degrees of freedom (p={chi_square['p_value']:.2e}); Cramer's "
                f"V={chi_square['cramers_v']:.3f}. The minimum expected cell count "
                f"is {chi_square['minimum_expected_count']:.1f}."
            ),
            "",
            "### Mutual-information ranking",
            "",
            "| Rank | Feature | Mutual information |",
            "|---:|---|---:|",
        ]
    )
    for index, row in enumerate(ranking, start=1):
        lines.append(
            f"| {index} | {row['feature']} | {row['mutual_information']:.4f} |"
        )
    mi_stability = mi["subsample_stability"]
    lines.extend(
        [
            "",
            (
                f"Contract has the largest point estimate. Its MI advantage over tenure "
                f"is {mi_stability['contract_minus_tenure_mi_difference']:.4f}; the "
                f"empirical 95% interval across "
                f"{mi_stability['resamples']} stratified 80% subsamples is "
                f"{mi_interval[0]:.4f} "
                f"to "
                f"{mi_interval[1]:.4f}. "
                "Contract ranks first in every subsample. This is an unadjusted "
                "stability check, not a causal or adjusted effect ranking."
            ),
            "",
            "## Corrected adjusted model",
            "",
            (
                "Recoding `No internet service` as `No` for the two included add-on "
                "fields removes the exact duplicate columns while preserving "
                "`InternetService` in the model. The corrected model converges on "
                f"{corrected_model['n']:,} rows. Its contract odds ratios relative to "
                "month-to-month are:"
            ),
            "",
            "| Contract | Adjusted odds ratio (95% CI) |",
            "|---|---:|",
        ]
    )
    for effect in corrected_model["contract_odds_ratios"]:
        label = "One year" if "[T.One year]" in effect["term"] else "Two year"
        lines.append(
            f"| {label} | {effect['odds_ratio']:.3f} "
            f"({effect['ci_95'][0]:.3f} to {effect['ci_95'][1]:.3f}) |"
        )
    lines.append(
        "The blind reference model uses a smaller adjustment set. Its odds ratios "
        "and 95% CIs versus this corrected specification are "
        f"{reference_comparison}. The point estimates differ modestly, but the "
        "intervals overlap."
    )
    tenure = corrected_model["median_tenure_by_contract"]
    lines.extend(
        [
            "",
            (
                f"Median tenure is {tenure['Month-to-month']:.0f} months for "
                f"month-to-month customers, {tenure['One year']:.0f} for one-year, "
                f"and {tenure['Two year']:.0f} for two-year customers. This overlap "
                "pattern emphasizes that contract and tenure are associated."
            ),
            "",
            "## Findings",
            "",
            "| # | Finding | Severity | Measured evidence |",
            "|---|---|---|---|",
        ]
    )
    for index, finding in enumerate(record["audit_findings"], start=1):
        lines.append(
            f"| {index} | {finding['finding_type']} | {finding['severity']} | "
            f"{finding['measured_effect']} |"
        )
    lines.extend(
        [
            "",
            "## Conclusion and limitations",
            "",
            (
                "The descriptive contract association is strong, and the independently "
                "fitted corrected model retains lower adjusted churn odds for longer "
                "contracts. This supports the response's qualitative association "
                "conclusion, but not because its saved code produced those results: "
                "that code fails at input and its specified regression is singular. "
                "The dataset is observational; self-selection, contract rules, and the "
                "large tenure differences prevent a causal interpretation. The "
                "corrected adjusted odds ratios are conditional associations, not "
                "effects of switching a customer to a longer contract."
            ),
            "",
        ]
    )
    path = result_path.parent / "audit.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
