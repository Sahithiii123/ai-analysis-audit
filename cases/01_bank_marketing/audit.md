# Case 01 audit: Bank Marketing

**Verdict: Partly reliable**

## Question and scope

The submitted code predicts term-deposit subscription from the UCI Bank Marketing records. This audit reproduces its saved random split and tests a source-row-order holdout. Since the data has month and weekday but no year or complete timestamp, that second split is a stress test, not a verified chronological evaluation.

## Reproduction

The saved run and independent reproduction both use 45,211 rows, with 11.7% subscribed. The random 60/20/20 split selected gradient boosting on validation PR-AUC and reproduced test ROC-AUC 0.803, PR-AUC 0.460 versus prevalence baseline 0.117, and top-20% lift 3.12x. The AI output's headline values matched.

## Generalization and calibration check

The 60/20/20 source-order split selected logistic regression. Its test ROC-AUC was 0.668 (95% bootstrap CI 0.656 to 0.678) and PR-AUC 0.441 (95% CI 0.425 to 0.460), at test prevalence 31.6%.
Compared with the random split, source-order ROC-AUC changed by -0.135 (95% CI -0.153 to -0.117). The PR-AUC change was -0.019 (95% CI -0.054 to 0.022), which does not establish a difference. Source-order calibration also worsened: slope 0.332, intercept -0.727, and decile ECE 0.159.
The source-order test prevalence (31.6%) is substantially above the random test prevalence (11.7%). The source-order comparison also selects a different model. These results are evidence that the random holdout alone cannot establish performance on later records; they do not establish the exact future-campaign error. The submitted output reports random-holdout performance and does not explicitly claim future-campaign validity, so the source-order difference limits generalization rather than contradicting the reported test score.

## Feature and threshold checks

Duration is excluded as a post-call field, and validation—not the test set—selects the model and F1 threshold. The random split's calibration slope is 1.078, intercept 0.138, and decile ECE 0.010.
The code includes `campaign`, which counts contacts during the current campaign including the last contact. Confirm that the value is available at the exact intended scoring moment; the supplied records cannot establish the production data-availability contract.
Source-order feature ablations were treated as exploratory sensitivity checks. Removing campaign count barely changed PR-AUC; removing previous campaign outcome reduced it. Removing previous-contact fields increased it on this particular holdout, so those fields should be checked for stability rather than assumed helpful.

## Findings

| # | Finding | Severity | Measured evidence |
|---|---|---|---|
| 1 | Source-order performance | Major | The source-order holdout's ROC-AUC is -0.135 lower than the random-holdout result (95% CI -0.153 to -0.117). The PR-AUC difference is -0.019 (95% CI -0.054 to 0.022), which includes zero. |

## Conclusion

The submitted analysis is reproducible and its random-holdout metrics are computed correctly. Its validation-selected model and threshold avoid test-set selection, and duration is properly excluded. However, the random split only supports within-dataset random-holdout claims. The source-order stress test shows lower ranking performance and poor calibration, but chronology is not verifiable without full timestamps. A timestamped future-campaign holdout and confirmation of feature availability are needed before interpreting these scores as deployment performance.
