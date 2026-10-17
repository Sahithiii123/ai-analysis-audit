"""Unit tests use tiny illustrative fixtures only, never case data."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold

from src.audit_tools import (
    adjust_pvalues,
    binary_metrics,
    bootstrap_ci,
    check_independence,
    check_normality,
    check_sparse_cells,
    check_variance_homogeneity,
    compare_naive_adjusted_logistic,
    leakage_ablation,
    majority_class_baseline,
    make_group_splits,
    make_time_splits,
    rank_instability,
    selection_bias_sensitivity,
    shuffled_label_test,
    stratified_comparison,
    wilson_interval,
)

TINY_BINARY_FIXTURE = pd.DataFrame(
    {
        "legitimate_signal": [0.1, 0.8, 0.2, 0.9, 0.3, 0.7, 0.4, 0.6] * 3,
        "suspect_outcome_copy": [0, 1, 0, 1, 0, 1, 0, 1] * 3,
        "group": np.repeat(np.arange(6), 4),
        "outcome": [0, 1, 0, 1] * 6,
    }
)


def test_split_helpers_preserve_temporal_and_group_boundaries() -> None:
    times = np.array([5, 1, 8, 2, 6, 3, 9, 4, 7, 10])
    for train, test in make_time_splits(times, n_splits=3, gap=1):
        assert times[train].max() < times[test].min()

    groups = TINY_BINARY_FIXTURE["group"].to_numpy()
    for train, test in make_group_splits(groups, n_splits=3):
        assert not set(groups[train]).intersection(groups[test])


def test_leakage_ablation_compares_features_across_split_designs() -> None:
    features = TINY_BINARY_FIXTURE[["legitimate_signal", "suspect_outcome_copy"]]
    target = TINY_BINARY_FIXTURE["outcome"].to_numpy()
    groups = TINY_BINARY_FIXTURE["group"].to_numpy()
    naive = list(
        StratifiedKFold(n_splits=3, shuffle=True, random_state=17).split(features, target)
    )
    proper = make_group_splits(groups, n_splits=3, random_state=17)
    result = leakage_ablation(
        LogisticRegression(),
        features,
        target,
        suspect_features=["suspect_outcome_copy"],
        splitters={"naive_random": naive, "held_out_group": proper},
        scoring="roc_auc",
    )
    assert len(result) == 12
    assert set(result["feature_set"]) == {"with_suspect", "without_suspect"}
    assert set(result["split"]) == {"naive_random", "held_out_group"}


def test_bootstrap_and_multiple_comparison_helpers_are_reproducible() -> None:
    fixture = np.array([1, 2, 3, 4, 5], dtype=float)
    first = bootstrap_ci(fixture, np.mean, n_resamples=200, random_state=9)
    second = bootstrap_ci(fixture, np.mean, n_resamples=200, random_state=9)
    assert first == second
    assert first[0] <= fixture.mean() <= first[1]

    adjusted = adjust_pvalues([0.01, 0.04, 0.2])
    assert adjusted.loc[0, "p_bonferroni"] == 0.03
    assert np.all(adjusted["p_bh"] >= adjusted["p_raw"])


def test_shuffled_label_test_returns_observed_and_null_evidence() -> None:
    fixture = TINY_BINARY_FIXTURE
    result = shuffled_label_test(
        LogisticRegression(),
        fixture[["legitimate_signal"]],
        fixture["outcome"],
        cv=StratifiedKFold(n_splits=2, shuffle=True, random_state=4),
        scoring="roc_auc",
        n_permutations=10,
        random_state=11,
    )
    assert result["permutation_scores"].shape == (10,)
    assert 0 <= result["p_value"] <= 1


def test_stratified_and_regression_adjusted_effect_helpers() -> None:
    exposure = np.tile([1] * 4 + [0] * 4, 2)
    outcome = np.array([1, 1, 0, 0, 1, 0, 0, 0, 1, 1, 1, 0, 1, 1, 0, 0])
    strata = np.repeat(["A", "B"], 8)
    cmh = stratified_comparison(exposure, outcome, strata)
    assert len(cmh["by_stratum"]) == 2
    assert np.isfinite(cmh["cmh_common_odds_ratio"])
    assert len(cmh["cmh_odds_ratio_ci"]) == 2

    rng = np.random.default_rng(5)
    size = 120
    covariate = rng.integers(0, 2, size=size)
    treatment = rng.integers(0, 2, size=size)
    probability = 1 / (1 + np.exp(-(-1 + 0.6 * treatment + 0.8 * covariate)))
    outcome_values = rng.binomial(1, probability)
    regression_fixture = pd.DataFrame(
        {"outcome": outcome_values, "treatment": treatment, "covariate": covariate}
    )
    effects = compare_naive_adjusted_logistic(
        regression_fixture,
        naive_formula="outcome ~ treatment",
        adjusted_formula="outcome ~ treatment + covariate",
        exposure_term="treatment",
    )
    assert effects["naive"]["n_observations"] == size
    assert effects["adjusted"]["odds_ratio_ci_lower"] > 0


def test_proportion_intervals_rank_instability_and_selection_sensitivity() -> None:
    lower, upper = wilson_interval(0, 10)
    assert lower == 0
    assert 0 < upper < 0.5

    ranks = rank_instability(
        {"group_a": [1, 2, 1, 2], "group_b": [1, 2, 2, 1], "group_c": [0, 1, 0, 1]},
        n_resamples=200,
        random_state=3,
    )
    assert np.all((ranks["top_rank_probability"] >= 0) & (ranks["top_rank_probability"] <= 1))
    assert ranks["top_rank_probability"].sum() == 1

    sensitivity = selection_bias_sensitivity(
        0.6,
        0.4,
        exposed_selection_ratio=(0.5, 2),
        unexposed_selection_ratio=(0.5, 2),
        grid_size=11,
    )
    assert sensitivity["population_risk_difference_min"] < 0
    assert sensitivity["population_risk_difference_max"] > 0


def test_assumption_diagnostics_and_imbalance_metrics() -> None:
    independence = check_independence(["a", "a", "b", "c"])
    assert independence["n_rows_in_repeated_units"] == 1
    sparse = check_sparse_cells([[8, 2], [1, 9]])
    assert sparse["n_expected_below_threshold"] >= 0
    variance = check_variance_homogeneity([1, 2, 3, 4], [2, 3, 4, 5])
    assert 0 <= variance["p_value"] <= 1
    normality = check_normality([1, 2, 3, 4, 5, 6, 7, 8])
    assert normality["n_tested"] == 8

    metrics = binary_metrics([0, 0, 0, 1], [0.1, 0.2, 0.3, 0.9])
    assert metrics["average_precision"] == 1
    assert metrics["pr_auc_average_precision"] == 1
    assert metrics["average_precision_prevalence_baseline"] == 0.25
    baseline = majority_class_baseline([0, 0, 0, 1])
    assert baseline["majority_accuracy"] == 0.75