# Case 05 audit: Adult Income and Multiple Comparisons

**Verdict: Reliable**

## Reproduction and multiple-testing audit

The saved run completed on 48,842 rows (23.9% above $50K) and its 25% random holdout AUC reproduces at 0.899 (95% bootstrap CI 0.893 to 0.905). The independent run matched the printed AUC of 0.899.
The code tests 14 features, not each category level, and applies Benjamini-Hochberg and Bonferroni correction to those same tests. 13 of 14 remain significant after Bonferroni; `fnlwgt` is the exception. The multiplicity correction is implemented correctly for this stated family.
10 test p-values are returned as 0.0 from floating-point underflow and print as `0`; zero is not an exact p-value. The threshold-based significance decisions remain unchanged.

## Effect-size results

| Feature | Metric | Effect |
|---|---|---:|
| relationship | Cramer's V | 0.454 |
| marital-status | Cramer's V | 0.448 |
| education-num | absolute rank-biserial | 0.432 |
| education | Cramer's V | 0.366 |
| age | absolute rank-biserial | 0.365 |
| occupation | Cramer's V | 0.350 |
| hours-per-week | absolute rank-biserial | 0.344 |
| sex | Cramer's V | 0.215 |
| workclass | Cramer's V | 0.182 |
| capital-gain | absolute rank-biserial | 0.179 |
| race | Cramer's V | 0.100 |
| native-country | Cramer's V | 0.096 |
| capital-loss | absolute rank-biserial | 0.068 |
| fnlwgt | absolute rank-biserial | 0.008 |

The response's broad qualitative conclusion is supported: relationship and marital status, education, age, occupation, hours, and capital gain show large sample associations; capital loss is smaller; fnlwgt's association is negligible. The printed table sorts Cramer's V and absolute rank-biserial on one axis, but these are different effect measures and should not be treated as a calibrated cross-type ranking. Within-type comparisons are more defensible.

## Missing values

| Feature | High-income rate when missing | When observed | Missing minus observed (95% Newcombe CI) |
|---|---:|---:|---:|
| workclass | 9.5% (n=2,799) | 24.8% (n=46,043) | -15.3 pp (-16.4 to -14.1) |
| occupation | 9.4% (n=2,809) | 24.8% (n=46,033) | -15.4 pp (-16.5 to -14.2) |
| native-country | 25.7% (n=857) | 23.9% (n=47,985) | +1.8 pp (-1.1 to +4.8) |

Missing workclass and occupation are strongly associated with lower income (9.5% versus 24.8%; 9.4% versus 24.8%). Missing native-country differs slightly in the opposite direction, and its interval includes zero.

## Model and population scope

The independent pipeline reproduces the random holdout AUC and the printed largest adjusted coefficient directions. This is an internal random split of the same extracted records, not external validation.
The unweighted sample prevalence is 23.93%; using `fnlwgt` only as a descriptive weight changes it to 23.78%. Because the question asks about this dataset, the unweighted analysis is descriptive of these rows; it should not be described as a design-weighted estimate for the U.S. population.
Relationship and marital status are associated (Cramer's V=0.488); education and education-num map one-to-one in the observed categories. The model drops education and keeps education-num, as described.

## Findings and conclusion

| Finding | Severity | Measured evidence |
|---|---|---|
| Missingness direction | Minor | Missing workclass and occupation records have lower high-income rates, but missing native-country records are +1.8 percentage points higher than observed records (95% CI -1.1 to +4.8). The broad claim that all three missingness patterns skew lower income is not supported. |
| Zero-formatted p-values | Minor | 10 of 14 raw p-values underflow to 0.0 and print as zero; these should be reported as below numeric precision, not literal probability zero. The corrected significance decisions are unchanged. |

The saved code and principal conclusions reproduce. The main qualifications are the missing-country direction, zero-formatted extreme p-values, mixed effect-size scales, and the fact that an unweighted dataset split does not establish population or causal relationships.
