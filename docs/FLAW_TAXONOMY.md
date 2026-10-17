# Flaw Taxonomy

Severity describes the impact on the headline claim: **Critical** invalidates the central conclusion or makes the analysis unusable; **Major** materially changes the estimate, model validity, or decision; **Minor** weakens precision or interpretation without reversing the main result; **Cosmetic** affects presentation but not the statistical result.

| Flaw | Definition | Detection and reproducible evidence |
|---|---|---|
| Target or feature leakage | A predictor contains the outcome, post-outcome information, or information unavailable at prediction time. | Check feature timing and provenance; compare validation performance with and without the suspect feature using a split that matches deployment. |
| Temporal, preprocessing, or duplicate leakage | Time order, groups, or duplicated records cross evaluation boundaries; preprocessing learns from held-out data. | Inspect split membership and transformation fit scope; rerun with temporal/group separation and train-only preprocessing. |
| Multiple comparisons / p-hacking | Many hypotheses or analysis paths are tried but only favorable results are reported. | Count tests and paths; report raw and adjusted p-values using Bonferroni and Benjamini-Hochberg; compare to label/permutation checks. |
| Confounding / omitted-variable bias | A third variable distorts an observed association between exposure and outcome. | Compare crude, stratified, and adjusted estimates; report the covariates, effect change, and remaining causal assumptions. |
| Simpson's paradox / aggregation error | An aggregate association differs from or reverses the within-stratum pattern because group composition differs. | Compute aggregate and stratum-specific rates from the same records and show denominators. |
| Selection / survivorship / non-response bias | Inclusion in the analyzed sample depends on outcome or related variables, limiting or distorting inference. | Define inclusion and exclusion; quantify excluded share and observable differences; run sensitivity bounds where possible. |
| Unsupported causal claim | Observational association is described as an intervention effect without an identification design. | Compare wording to study design; report adjusted association and explain unmeasured-confounding and identification limits. |
| Wrong test / violated assumptions | The test or model does not fit the outcome, dependence structure, distribution, or cell sizes. | Check design and diagnostics; rerun an appropriate test/model and compare estimates and uncertainty. |
| Missing uncertainty | A point estimate, metric, or rank is presented without an interval or stability assessment. | Bootstrap or use a suitable analytic interval; quantify ranking instability and sample sizes. |
| Metric misuse | A metric is uninformative for the task, imbalance, threshold, or decision, or lacks a baseline. | Report prevalence and baseline; compare suitable metrics such as PR-AUC and ROC-AUC, plus threshold-specific performance. |
| Small-sample noise | Sparse data or repeated subgrouping produces unstable estimates presented as a stable signal. | Show denominators and intervals; bootstrap or resample to assess estimate and ranking stability. |
| Overclaiming | Certainty, scope, or generalization in the wording exceeds the data and design. | Map each claim to its estimate, interval, sample, and design; rewrite unsupported certainty explicitly. |
| Data-handling error | Filters, joins, grain changes, key duplication, parsing, or missing-value handling alter the analysis incorrectly or invisibly. | Assert keys and row grain; log counts before/after operations; compare join cardinalities and independently recompute aggregates. |

For every case finding, state the taxonomy label, severity, location in the raw output, measured evidence, and notebook cell that reproduces it. A detection checklist alone is not evidence of a flaw.