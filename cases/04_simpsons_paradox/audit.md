# Case 04 audit: Berkeley Admissions

**Verdict: Partly reliable**

## Reproduction

The saved AI run exited 0 without an exception and reproduced 4,526 applications. The independent aggregation matches its overall and department-specific rates and the displayed standardized gap.

## Overall and department-specific results

| Gender | Admitted | Applicants | Rate (95% Wilson CI) |
|---|---:|---:|---:|
| Female | 557 | 1,835 | 30.4% (28.3% to 32.5%) |
| Male | 1,198 | 2,691 | 44.5% (42.7% to 46.4%) |

The overall female-minus-male difference is -14.2 percentage points (Wald 95% CI -17.0 to -11.3).

| Department | Female rate | Male rate | Difference (F-M) | Female application share | Male application share |
|---|---:|---:|---:|---:|---:|
| A | 82.4% | 62.1% | +20.3 pp | 5.9% | 30.7% |
| B | 68.0% | 63.0% | +5.0 pp | 1.4% | 20.8% |
| C | 34.1% | 36.9% | -2.9 pp | 32.3% | 12.1% |
| D | 34.9% | 33.1% | +1.8 pp | 20.4% | 15.5% |
| E | 23.9% | 27.7% | -3.8 pp | 21.4% | 7.1% |
| F | 7.0% | 5.9% | +1.1 pp | 18.6% | 13.9% |

## Common-department-mix standardization

Using pooled applicant department weights, the standardized admission rates are 43.0% for women and 38.7% for men. The difference is +4.3 percentage points (fixed-weight 95% Wald interval +0.7 to +7.9). The composition shift from the observed -14.2-point gap is +18.4 points. This confirms a marked reversal, not a zero adjusted difference; the AI's 'near zero' phrasing understates the remaining 4.3-point estimate.
The blind reference reports a department-stratified CMH common odds ratio of 1.105 (95% CI 0.943 to 1.295, p=0.217). That is a different estimand and weighting from the standardized risk difference above; it is not a contradiction.

## Finding

| Finding | Severity | Measured evidence |
|---|---|---|
| Standardized-gap framing | Minor | The reproduced common-mix difference is 4.3 percentage points favoring women (95% fixed-weight Wald interval 0.7 to 7.9); the overall female-minus-male gap is -14.2 points. This is a substantial reduction and reversal, but the interval is not centered near zero and excludes zero under the stated model. |

## Interpretation and limits

The overall gap is strongly affected by application mix: women applied much more often to departments C-F, whose overall admission rates were lower, while men applied much more often to A and B. The department-specific descriptive rates support the Simpson reversal. However, aggregate counts do not control for applicant qualifications, identify upstream barriers, or establish that department assignment caused the marginal difference. The source covers one institution and one admissions cycle.
