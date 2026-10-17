"""Reusable, evidence-oriented statistical helpers for case audits.

These functions compute diagnostics and sensitivity analyses; they do not
classify a result as a flaw or establish causality. Callers must document the
estimand, sampling design, and assumptions appropriate to each case.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.base import clone
from sklearn.metrics import average_precision_score, get_scorer, roc_auc_score
from sklearn.model_selection import (
    GroupKFold,
    TimeSeriesSplit,
    permutation_test_score,
)
from statsmodels.formula.api import logit
from statsmodels.stats.contingency_tables import StratifiedTable
from statsmodels.stats.multitest import multipletests


def _one_dimensional(values: Sequence[Any], name: str) -> np.ndarray:
    """Return a nonempty one-dimensional array or raise a useful error."""
    array = np.asarray(values)
    if array.ndim != 1 or array.size == 0:
        raise ValueError(f"{name} must be a nonempty one-dimensional sequence")
    return array


def make_time_splits(
    times: Sequence[Any],
    *,
    n_splits: int = 5,
    gap: int = 0,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Create expanding-window splits ordered by timestamps.

    Ties retain input order. Returned indices address the original input rows.
    The training indices always precede the test indices in sorted time order;
    this prevents future observations from entering a training fold, but does
    not address other forms of leakage or justify a temporal estimand.
    """
    time_values = _one_dimensional(times, "times")
    if n_splits < 2 or gap < 0:
        raise ValueError("n_splits must be at least 2 and gap must be nonnegative")
    order = np.argsort(time_values, kind="stable")
    splitter = TimeSeriesSplit(n_splits=n_splits, gap=gap)
    return [(order[train], order[test]) for train, test in splitter.split(order)]


def make_group_splits(
    groups: Sequence[Any],
    *,
    n_splits: int = 5,
    shuffle: bool = True,
    random_state: int = 42,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Create folds that keep every group wholly in train or test.

    This is appropriate only when the held-out-group target reflects the
    intended deployment or inference population. It does not establish
    independence between distinct groups.
    """
    group_values = _one_dimensional(groups, "groups")
    if n_splits < 2:
        raise ValueError("n_splits must be at least 2")
    unique_groups = np.unique(group_values)
    if unique_groups.size < n_splits:
        raise ValueError("n_splits cannot exceed the number of unique groups")
    splitter = GroupKFold(n_splits=n_splits, shuffle=shuffle, random_state=random_state)
    placeholder = np.zeros(group_values.size)
    return list(splitter.split(placeholder, groups=group_values))


def leakage_ablation(
    estimator: Any,
    features: pd.DataFrame,
    target: Sequence[Any],
    *,
    suspect_features: Sequence[str],
    splitters: Mapping[str, Sequence[tuple[Sequence[int], Sequence[int]]]],
    scoring: str,
) -> pd.DataFrame:
    """Compare a model with/without suspect columns under supplied splits.

    `splitters` should name and include both naive and design-appropriate
    splits when leakage is suspected. The helper evaluates identical feature
    sets over each split and reports every fold score; it does not decide
    which split is scientifically appropriate. Requires a pandas DataFrame so
    suspect columns can be named explicitly.
    """
    if not isinstance(features, pd.DataFrame):
        raise TypeError("features must be a pandas DataFrame with named columns")
    if not suspect_features:
        raise ValueError("suspect_features must contain at least one column")
    missing = set(suspect_features).difference(features.columns)
    if missing:
        raise ValueError(f"Unknown suspect feature(s): {sorted(missing)}")
    if not splitters:
        raise ValueError("splitters must contain at least one named split strategy")
    target_values = _one_dimensional(target, "target")
    if len(features) != target_values.size:
        raise ValueError("features and target must have the same number of rows")

    scorer = get_scorer(scoring)
    feature_sets = {
        "with_suspect": features,
        "without_suspect": features.drop(columns=list(suspect_features)),
    }
    rows: list[dict[str, Any]] = []
    for split_name, folds in splitters.items():
        for fold_number, (train_indices, test_indices) in enumerate(folds, start=1):
            train = np.asarray(train_indices, dtype=int)
            test = np.asarray(test_indices, dtype=int)
            if train.size == 0 or test.size == 0:
                raise ValueError(f"{split_name} fold {fold_number} has an empty partition")
            for feature_label, selected_features in feature_sets.items():
                fitted = clone(estimator)
                fitted.fit(selected_features.iloc[train], target_values[train])
                score = scorer(fitted, selected_features.iloc[test], target_values[test])
                rows.append(
                    {
                        "split": split_name,
                        "fold": fold_number,
                        "feature_set": feature_label,
                        "score_name": scoring,
                        "score": float(score),
                        "n_train": int(train.size),
                        "n_test": int(test.size),
                    }
                )
    return pd.DataFrame(rows)


def bootstrap_ci(
    values: Sequence[Any] | np.ndarray,
    statistic: Callable[[np.ndarray], float],
    *,
    n_resamples: int = 2000,
    confidence_level: float = 0.95,
    random_state: int = 42,
) -> tuple[float, float]:
    """Return a percentile bootstrap interval for an iid row statistic.

    `statistic` receives resampled rows (axis 0). This assumes the rows are
    exchangeable sampling units; clustered, paired, or time-series data need a
    design-preserving bootstrap instead. The interval is percentile-based and
    does not correct bias or multiplicity.
    """
    array = np.asarray(values)
    if array.ndim == 0 or array.shape[0] < 2:
        raise ValueError("values must contain at least two observations")
    if n_resamples < 100:
        raise ValueError("n_resamples must be at least 100")
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must be between 0 and 1")
    rng = np.random.default_rng(random_state)
    estimates = np.empty(n_resamples, dtype=float)
    for index in range(n_resamples):
        sample = array[rng.integers(0, array.shape[0], size=array.shape[0])]
        estimates[index] = statistic(sample)
    tail = (1 - confidence_level) / 2
    lower, upper = np.quantile(estimates, [tail, 1 - tail])
    return float(lower), float(upper)


def shuffled_label_test(
    estimator: Any,
    features: Any,
    target: Sequence[Any],
    *,
    cv: Any,
    scoring: str,
    n_permutations: int = 1000,
    groups: Sequence[Any] | None = None,
    random_state: int = 42,
) -> dict[str, Any]:
    """Compare cross-validated score to a shuffled-target null distribution.

    The supplied CV design must be valid for the data (for example, group or
    temporal splits where required). Permutations assume labels are exchangeable
    under the null; clustered or temporal labels require restricted shuffling.
    """
    if n_permutations < 1:
        raise ValueError("n_permutations must be positive")
    score, permutation_scores, p_value = permutation_test_score(
        estimator,
        features,
        target,
        groups=groups,
        cv=cv,
        n_permutations=n_permutations,
        random_state=random_state,
        scoring=scoring,
        n_jobs=1,
    )
    return {
        "observed_score": float(score),
        "permutation_scores": np.asarray(permutation_scores, dtype=float),
        "p_value": float(p_value),
        "n_permutations": n_permutations,
        "scoring": scoring,
    }


def adjust_pvalues(p_values: Sequence[float]) -> pd.DataFrame:
    """Return raw, Bonferroni, and Benjamini-Hochberg adjusted p-values."""
    values = _one_dimensional(p_values, "p_values").astype(float)
    if not np.isfinite(values).all() or ((values < 0) | (values > 1)).any():
        raise ValueError("p_values must be finite and between 0 and 1")
    bonferroni = multipletests(values, method="bonferroni")[1]
    benjamini_hochberg = multipletests(values, method="fdr_bh")[1]
    return pd.DataFrame(
        {
            "p_raw": values,
            "p_bonferroni": bonferroni,
            "p_bh": benjamini_hochberg,
        }
    )


def stratified_comparison(
    exposure: Sequence[Any],
    outcome: Sequence[Any],
    strata: Sequence[Any],
) -> dict[str, Any]:
    """Compare a binary outcome by binary exposure within strata and by CMH.

    Values are interpreted as Boolean (true=exposed/outcome). The CMH common
    odds ratio and test rely on a meaningful stratum definition and a common
    odds-ratio interpretation. Empty exposure/outcome cells are retained as
    zeroes; inspect sparsity before interpreting the asymptotic test.
    """
    exposure_values = _one_dimensional(exposure, "exposure").astype(bool)
    outcome_values = _one_dimensional(outcome, "outcome").astype(bool)
    stratum_values = _one_dimensional(strata, "strata")
    if not (exposure_values.size == outcome_values.size == stratum_values.size):
        raise ValueError("exposure, outcome, and strata must have equal lengths")

    labels = pd.unique(stratum_values)
    tables: list[np.ndarray] = []
    summaries: list[dict[str, Any]] = []
    for label in labels:
        selected = stratum_values == label
        table = np.array(
            [
                [
                    np.sum(selected & exposure_values & outcome_values),
                    np.sum(selected & exposure_values & ~outcome_values),
                ],
                [
                    np.sum(selected & ~exposure_values & outcome_values),
                    np.sum(selected & ~exposure_values & ~outcome_values),
                ],
            ],
            dtype=int,
        )
        tables.append(table)
        exposed_total = int(table[0].sum())
        unexposed_total = int(table[1].sum())
        summaries.append(
            {
                "stratum": label,
                "exposed_events": int(table[0, 0]),
                "exposed_total": exposed_total,
                "exposed_rate": float(table[0, 0] / exposed_total) if exposed_total else np.nan,
                "unexposed_events": int(table[1, 0]),
                "unexposed_total": unexposed_total,
                "unexposed_rate": (
                    float(table[1, 0] / unexposed_total) if unexposed_total else np.nan
                ),
            }
        )

    stratified = StratifiedTable(np.stack(tables, axis=2), shift_zeros=True)
    test = stratified.test_null_odds()
    lower, upper = stratified.oddsratio_pooled_confint()
    return {
        "by_stratum": pd.DataFrame(summaries),
        "cmh_common_odds_ratio": float(stratified.oddsratio_pooled),
        "cmh_odds_ratio_ci": (float(lower), float(upper)),
        "cmh_statistic": float(test.statistic),
        "cmh_p_value": float(test.pvalue),
        "tables": tables,
    }


def compare_naive_adjusted_logistic(
    data: pd.DataFrame,
    *,
    naive_formula: str,
    adjusted_formula: str,
    exposure_term: str,
    confidence_level: float = 0.95,
) -> dict[str, dict[str, float]]:
    """Compare crude and adjusted logistic-regression odds ratios.

    Formulas are supplied by the caller; include transformations such as
    `C(category)` explicitly. The exposure term must be a single estimable
    coefficient in both models. This is an associational comparison, not a
    causal adjustment guarantee; adjustment can introduce bias and odds ratios
    are non-collapsible.
    """
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must be between 0 and 1")
    alpha = 1 - confidence_level
    results: dict[str, dict[str, float]] = {}
    for label, formula in (("naive", naive_formula), ("adjusted", adjusted_formula)):
        fitted = logit(formula, data=data).fit(disp=False)
        if exposure_term not in fitted.params:
            raise ValueError(f"Exposure term {exposure_term!r} is not a model coefficient")
        estimate = float(fitted.params[exposure_term])
        interval = fitted.conf_int(alpha=alpha).loc[exposure_term]
        results[label] = {
            "log_odds_ratio": estimate,
            "odds_ratio": float(np.exp(estimate)),
            "odds_ratio_ci_lower": float(np.exp(interval.iloc[0])),
            "odds_ratio_ci_upper": float(np.exp(interval.iloc[1])),
            "n_observations": int(fitted.nobs),
        }
    return results


def wilson_interval(
    successes: int,
    trials: int,
    *,
    confidence_level: float = 0.95,
) -> tuple[float, float]:
    """Compute a Wilson score interval for one binomial proportion."""
    if trials <= 0 or not 0 <= successes <= trials:
        raise ValueError("require trials > 0 and 0 <= successes <= trials")
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must be between 0 and 1")
    z = stats.norm.ppf(1 - (1 - confidence_level) / 2)
    proportion = successes / trials
    denominator = 1 + z**2 / trials
    center = (proportion + z**2 / (2 * trials)) / denominator
    half_width = (
        z
        * np.sqrt(proportion * (1 - proportion) / trials + z**2 / (4 * trials**2))
        / denominator
    )
    return float(center - half_width), float(center + half_width)


def rank_instability(
    samples: Mapping[str, Sequence[float]],
    *,
    n_resamples: int = 2000,
    random_state: int = 42,
) -> pd.DataFrame:
    """Bootstrap rank probabilities for small-sample group means.

    Each group is independently resampled with replacement. Rank 1 is the
    highest mean. This quantifies sampling instability under iid-within-group
    assumptions; it does not account for shared sampling, multiple outcomes,
    or selection of groups after viewing the data.
    """
    if len(samples) < 2 or n_resamples < 100:
        raise ValueError("provide at least two groups and 100 resamples")
    arrays = {
        name: _one_dimensional(values, name).astype(float)
        for name, values in samples.items()
    }
    if any(not np.isfinite(values).all() for values in arrays.values()):
        raise ValueError("all group values must be finite")
    rng = np.random.default_rng(random_state)
    names = list(arrays)
    ranks = np.empty((n_resamples, len(names)), dtype=int)
    for iteration in range(n_resamples):
        means = [
            rng.choice(arrays[name], size=arrays[name].size, replace=True).mean()
            for name in names
        ]
        order = np.argsort(-np.asarray(means), kind="stable")
        ranks[iteration, order] = np.arange(1, len(names) + 1)
    return pd.DataFrame(
        {
            "group": names,
            "observed_mean": [float(arrays[name].mean()) for name in names],
            "top_rank_probability": [(ranks[:, index] == 1).mean() for index in range(len(names))],
            "mean_rank": [float(ranks[:, index].mean()) for index in range(len(names))],
        }
    )


def selection_bias_sensitivity(
    exposed_selected_rate: float,
    unexposed_selected_rate: float,
    *,
    exposed_selection_ratio: tuple[float, float],
    unexposed_selection_ratio: tuple[float, float],
    grid_size: int = 101,
) -> dict[str, Any]:
    """Bound a population risk difference over assumed outcome-selection ratios.

    Each ratio is P(selected | outcome=1, exposure) divided by
    P(selected | outcome=0, exposure). Under this selection model, the
    population outcome odds equal selected-sample odds divided by the ratio.
    The result is a sensitivity range, not an estimate; its usefulness depends
    on credible externally chosen ratio ranges and the assumed selection model.
    """
    rates = (exposed_selected_rate, unexposed_selected_rate)
    if any(not 0 <= rate <= 1 for rate in rates):
        raise ValueError("selected rates must be between 0 and 1")
    if grid_size < 2:
        raise ValueError("grid_size must be at least 2")

    def validate_range(value: tuple[float, float]) -> None:
        if len(value) != 2 or not 0 < value[0] <= value[1] < np.inf:
            raise ValueError("selection-ratio bounds must be finite, positive, and ordered")

    validate_range(exposed_selection_ratio)
    validate_range(unexposed_selection_ratio)

    def corrected_probability(rate: float, ratio: float) -> float:
        if rate in (0, 1):
            return rate
        odds = rate / (1 - rate) / ratio
        return odds / (1 + odds)

    exposed_ratios = np.linspace(*exposed_selection_ratio, grid_size)
    unexposed_ratios = np.linspace(*unexposed_selection_ratio, grid_size)
    differences = [
        corrected_probability(exposed_selected_rate, exposed_ratio)
        - corrected_probability(unexposed_selected_rate, unexposed_ratio)
        for exposed_ratio in exposed_ratios
        for unexposed_ratio in unexposed_ratios
    ]
    return {
        "observed_selected_risk_difference": exposed_selected_rate - unexposed_selected_rate,
        "population_risk_difference_min": float(min(differences)),
        "population_risk_difference_max": float(max(differences)),
        "grid_size_per_group": grid_size,
        "exposed_selection_ratio": exposed_selection_ratio,
        "unexposed_selection_ratio": unexposed_selection_ratio,
        "selection_model": (
            "P(selected|outcome=1, exposure) / P(selected|outcome=0, exposure)"
        ),
    }


def check_independence(unit_ids: Sequence[Any]) -> dict[str, Any]:
    """Flag repeated unit identifiers as a dependence risk, not a test.

    Unique IDs do not prove independent observations; this only detects exact
    repeated identifiers and reports their count for follow-up.
    """
    identifiers = _one_dimensional(unit_ids, "unit_ids")
    unique_count = int(pd.Series(identifiers).nunique(dropna=False))
    return {
        "n_rows": int(identifiers.size),
        "n_unique_units": unique_count,
        "n_rows_in_repeated_units": int(identifiers.size - unique_count),
        "repeated_unit_ids_present": unique_count < identifiers.size,
        "interpretation": "A unique-ID check cannot establish independence.",
    }


def check_sparse_cells(
    observed_counts: Sequence[Sequence[int]],
    *,
    expected_count_threshold: float = 5,
) -> dict[str, Any]:
    """Report sparse expected counts for a contingency-table chi-square test."""
    table = np.asarray(observed_counts, dtype=int)
    if table.ndim != 2 or min(table.shape) < 2 or (table < 0).any():
        raise ValueError("observed_counts must be a nonnegative 2D table of at least 2x2")
    if expected_count_threshold <= 0:
        raise ValueError("expected_count_threshold must be positive")
    statistic, p_value, degrees_freedom, expected = stats.chi2_contingency(
        table,
        correction=False,
    )
    return {
        "chi_square": float(statistic),
        "p_value": float(p_value),
        "degrees_freedom": int(degrees_freedom),
        "expected_counts": expected,
        "n_expected_below_threshold": int(np.sum(expected < expected_count_threshold)),
        "expected_count_threshold": expected_count_threshold,
    }


def check_variance_homogeneity(
    *groups: Sequence[float],
    alpha: float = 0.05,
) -> dict[str, Any]:
    """Run median-centered Levene's test and report the variance assumption check."""
    if len(groups) < 2 or any(len(group) < 2 for group in groups):
        raise ValueError("provide at least two groups with at least two observations each")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")
    result = stats.levene(*(np.asarray(group, dtype=float) for group in groups), center="median")
    return {
        "statistic": float(result.statistic),
        "p_value": float(result.pvalue),
        "alpha": alpha,
        "evidence_of_unequal_variance": bool(result.pvalue < alpha),
        "test": "Levene median-centered",
    }


def check_normality(
    values: Sequence[float],
    *,
    alpha: float = 0.05,
    max_n: int = 5000,
    random_state: int = 42,
) -> dict[str, Any]:
    """Run Shapiro-Wilk, subsampling large inputs with a fixed random seed.

    The p-value can be overly sensitive at large n and underpowered at small n;
    this diagnostic does not replace graphical checks or model residual review.
    """
    array = _one_dimensional(values, "values").astype(float)
    array = array[np.isfinite(array)]
    if array.size < 3:
        raise ValueError("at least three finite observations are required")
    if not 0 < alpha < 1 or max_n < 3:
        raise ValueError("alpha must be between 0 and 1 and max_n at least 3")
    if array.size > max_n:
        rng = np.random.default_rng(random_state)
        array = rng.choice(array, size=max_n, replace=False)
    result = stats.shapiro(array)
    return {
        "statistic": float(result.statistic),
        "p_value": float(result.pvalue),
        "n_tested": int(array.size),
        "alpha": alpha,
        "evidence_against_normality": bool(result.pvalue < alpha),
        "test": "Shapiro-Wilk",
    }


def binary_metrics(
    actual: Sequence[Any],
    scores: Sequence[float],
) -> dict[str, float | int | None]:
    """Report prevalence, average-precision PR-AUC, its baseline, and ROC-AUC."""
    actual_values = _one_dimensional(actual, "actual").astype(int)
    score_values = _one_dimensional(scores, "scores").astype(float)
    if actual_values.size != score_values.size:
        raise ValueError("actual and scores must have equal lengths")
    if not np.isin(actual_values, [0, 1]).all():
        raise ValueError("actual must contain only binary values 0 and 1")
    if not np.isfinite(score_values).all():
        raise ValueError("scores must be finite")
    prevalence = float(actual_values.mean())
    return {
        "n": int(actual_values.size),
        "positive_count": int(actual_values.sum()),
        "prevalence": prevalence,
        "average_precision": float(average_precision_score(actual_values, score_values)),
        "pr_auc_average_precision": float(
            average_precision_score(actual_values, score_values)
        ),
        "average_precision_prevalence_baseline": prevalence,
        "roc_auc": (
            float(roc_auc_score(actual_values, score_values))
            if np.unique(actual_values).size == 2
            else None
        ),
    }


def majority_class_baseline(actual: Sequence[Any]) -> dict[str, float | int]:
    """Return class counts and majority-class accuracy as a simple baseline."""
    values = _one_dimensional(actual, "actual")
    labels, counts = np.unique(values, return_counts=True)
    majority_index = int(np.argmax(counts))
    return {
        "n": int(values.size),
        "n_classes": int(labels.size),
        "majority_class": labels[majority_index].item(),
        "majority_count": int(counts[majority_index]),
        "majority_accuracy": float(counts[majority_index] / values.size),
    }