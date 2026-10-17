# Olist delivery and reviews: AI analysis audit

## 1. Task and AI output summary

The question asks whether late delivery is associated with review scores and how seller late rates vary. The submitted code analyzes delivered orders with valid delivery estimates, joins the latest review per order, and compares review scores and seller rates.

> “Late delivery is strongly associated with worse reviews.”

The saved code run completed without a repair. Independent reproduction matched 95,824 reviewed delivered orders, a late rate of 8.0%, and means of 2.565 (late) versus 4.294 (on time/early).

## 2. Method review

The order is the unit for the review-score comparison. The code correctly deduplicates to one latest review per order and uses distinct seller-order pairs so multiple items from the same seller do not multiply that seller’s order count. A rank correlation is appropriate for an ordinal score, and the code reports a Wilson interval for seller rates.

The saved code uses pandas, not DuckDB/SQL. That is not a flaw by itself. The blind reference notebook is absent for this case; I compared the AI run to the committed DuckDB reference implementation instead.

### Filter log

| Filter step | Rows before | Rows after |
|---|---:|---:|
| Raw orders |  | 99,441 |
| Delivered status | 99,441 | 96,478 |
| Delivery timestamp present | 96,478 | 96,470 |
| Estimated timestamp present | 96,470 | 96,470 |
| Latest review per eligible order | 96,470 | 95,824 |

## 3. Assumption review

The AI notes that the data are observational and names review selection and confounding. In the reviewed sample, adjustment for log total freight, item count, and customer-state fixed effects changes the late score estimate from -1.729 to -1.713 (95% CI [-1.751, -1.675]). No substantial attenuation was reproduced with these available controls. Product category and geographic distance are unavailable in the supplied files, so remaining confounding is untested.

Review selection is observable: 646 of 96,470 eligible delivered orders have no review. Their late rate is 25.5%, versus 8.0% among reviewed orders (difference -17.5 percentage points, 95% CI [-21.1, -14.3] points).
Other observable differences: mean total freight is 22.76 for reviewed orders and 26.19 for orders without reviews; mean item count is 1.141 versus 1.280.

## 4. Does the conclusion follow from the numbers?

Yes for the main association in reviewed orders: the late-minus-on-time mean difference is -1.729 (customer-clustered 95% CI [-1.767, -1.691]). The adjusted estimate remains negative. This is an association, not a causal delivery effect.

All-delivered late rate is 8.1%, slightly above the reviewed-order rate of 8.0%. The seller signal is real but the count of flagged sellers is overstated before multiple-testing correction.

### AI claim vs measured results

| AI claim | Independently measured |
|---|---|
| Late mean below on-time mean | 2.565 vs 4.294; difference -1.729, 95% CI [-1.767, -1.691] |
| 75 sellers above platform late rate | 75 unadjusted; 26 after BH and 13 after Bonferroni |
| Seller-level correlation reflects the relationship | Spearman rho -0.453 (bootstrap 95% CI [-0.519, -0.382]); this is an aggregate seller-level association, not an order-level effect |

## 5. Flaws table

| # | flaw type | severity | where in AI output | measured effect + interval | notebook cell |
|---|---|---|---|---|---|
| 1 | Multiple comparisons | Major | Seller-level late-rate Wilson flags | 75 flags among 623 tested sellers; 26 remain after Benjamini-Hochberg and 13 after Bonferroni adjustment. 95% interval [9.7%, 14.8%] | audit_evidence.ipynb code cell 3 |
| 2 | Review selection | Minor | Delivered-order review join and caveats | 646 of 96,470 eligible delivered orders lack a review. Their late rate is 25.5% versus 8.0% among reviewed orders. 95% interval [-21.1, -14.3] percentage points | audit_evidence.ipynb code cell 4 |
| 3 | Seller denominator | Minor | Seller-level late-rate aggregation | The code uses reviewed delivered orders. Using all delivered orders changes eligible sellers from 623 to 627 and unadjusted Wilson flags from 75 to 78. 95% interval [-0.5, 0.9] percentage points | audit_evidence.ipynb code cell 3 |
| 4 | Effect-size sign | Minor | Mann-Whitney rank-biserial print statement | The printed rank-biserial estimate is negative despite the text saying positive means on-time scores are higher. 95% interval [0.542, 0.566] | audit_evidence.ipynb code cell 2 |

## 6. What the AI got right

- Its principal score comparison is reproduced: later delivery is strongly associated with lower scores in this reviewed sample.
- It uses one latest review per order and counts each seller-order pair once despite multi-item orders.
- It explicitly avoids causal language and names confounding, review selection, and multi-seller attribution as caveats.
- The seller-level association is negative, but the code correctly treats it as a seller-level summary rather than a causal estimate.

## 7. Verdict

**Partly reliable** — The main reviewed-order association is supported, but unadjusted seller flags overstate certainty and one reported effect sign is reversed.

## 8. Rubric

| Dimension | Score (0–2) | Evidence | Justification |
|---|---:|---|---|
| Question framing | 2 | The response defines lateness from delivery versus the estimate, scores reviews, and reports seller-level order rates. | The units and observational association question are clear. |
| Method choice | 2 | The script compares score distributions by late status, uses Spearman for an ordinal score, and deduplicates seller-order pairs. | The main descriptive methods fit the stated questions. |
| Assumption checking | 1 | Adjusted late-score estimate is -1.713 (95% CI -1.751 to -1.675); the response itself lists confounding and self-selection but does not measure their effects. | Important observed confounding and review selection were not tested. |
| Leakage control | 2 | The analysis is descriptive and does not train or evaluate a predictor. | Predictive leakage is not applicable to the submitted methods. |
| Uncertainty quantification | 1 | Wilson seller intervals are used, but the main mean-score difference is not given an interval in the submitted output. | Intervals are present for seller rates but omitted for main effects. |
| Causal language discipline | 2 | The response says, “Observational data only (no causal claim).” | The response explicitly limits its claims to association. |
| Reproducibility | 2 | The response includes runnable Python code, file names, filtering, and the saved run completed successfully. | The submitted execution and code are reproducible in the available environment. |
| Conclusion validity | 1 | Reproduction gives late and on-time means of 2.565 and 4.294; the mean difference is -1.729 (95% CI -1.767 to -1.691). | The main association is correct, but seller significance and one effect sign are misstated. |

The score describes the submitted AI analysis, not this corrected audit.

Recorded finding types: Multiple comparisons, Review selection, Seller denominator, Effect-size sign.

## Reference comparison and limitations

A blind case-03 `reference_analysis.ipynb` is not present, so a notebook-to-notebook comparison could not be made. The committed DuckDB reference result is available and broadly agrees on the lower late-order review scores.

The DuckDB result has 95,830 orders versus 95,824 in the AI reproduction (difference 6). Late and on-time means are 2.567 and 4.294 in the reference, versus 2.565 and 4.294 in the AI reproduction.

Bucket means also differ because the reference uses calendar-date lateness and the AI uses elapsed timestamp days:

| Lateness bucket | AI mean score | DuckDB reference mean score |
|---|---:|---:|
| on time / early | 4.294 | 4.294 |
| 1-3 days late | 3.766 | 3.595 |
| 4-7 days late | 2.316 | 2.106 |
| >7 days late | 1.727 | 1.698 |

The exact order-count difference remains unexplained. The review aggregation and bucket definitions differ, so the reference numbers are reported separately rather than substituted for the AI-code reproduction.

The adjusted estimate is limited to reviewed orders and available covariates; it does not control product category or distance. 1,275 delivered orders (1.3%) have more than one seller; attributing each to every seller is suitable for seller-specific service summaries but makes seller observations overlap.
