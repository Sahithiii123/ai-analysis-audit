# Case 02 audit: Telco Churn

**Verdict: Partly reliable**

## Scope and saved output

The AI response proposes descriptive churn rates, a chi-square test, mutual-information ranking, and an adjusted logistic model. Its saved sandbox run fails before printing any result. The response itself labels the code unrun and gives no numerical estimates. The original prompt, response, code, and run logs were preserved.

## Measured execution problems

The saved run exits 1 because `scipy.io.arff.loadarff` raises `NotImplementedError: String attributes not supported yet, sorry` for the ARFF string attribute. The run has no stdout.
Using the repository's ARFF loader, the submitted logistic formula produces 18 design columns with rank 16. `InternetService == No`, `OnlineSecurity == No internet service`, and `TechSupport == No internet service` are identical indicator columns. The submitted fit therefore fails with `LinAlgError: Singular matrix`.

## Independent descriptive results

The loaded data has 7,043 customers and overall churn prevalence 26.5%. Contract rates are:

| Contract | Churn | Customers | Rate (95% Wilson CI) |
|---|---:|---:|---:|
| Month-to-month | 1,655 | 3,875 | 42.7% (41.2% to 44.3%) |
| One year | 166 | 1,473 | 11.3% (9.8% to 13.0%) |
| Two year | 48 | 1,695 | 2.8% (2.1% to 3.7%) |

The contract-by-churn chi-square statistic is 1184.6 on 2 degrees of freedom (p=5.86e-258); Cramer's V=0.410. The minimum expected cell count is 390.9.

### Mutual-information ranking

| Rank | Feature | Mutual information |
|---:|---|---:|
| 1 | Contract | 0.0985 |
| 2 | tenure | 0.0679 |
| 3 | OnlineSecurity | 0.0647 |
| 4 | TechSupport | 0.0630 |
| 5 | InternetService | 0.0556 |
| 6 | OnlineBackup | 0.0468 |
| 7 | MonthlyCharges | 0.0455 |
| 8 | TotalCharges | 0.0450 |
| 9 | PaymentMethod | 0.0445 |
| 10 | DeviceProtection | 0.0439 |
| 11 | StreamingMovies | 0.0320 |
| 12 | StreamingTV | 0.0319 |
| 13 | PaperlessBilling | 0.0192 |
| 14 | Dependents | 0.0145 |
| 15 | SeniorCitizen | 0.0126 |
| 16 | Partner | 0.0115 |
| 17 | MultipleLines | 0.0008 |
| 18 | PhoneService | 0.0001 |
| 19 | gender | 0.0000 |

Contract has the largest point estimate. Its MI advantage over tenure is 0.0305; the empirical 95% interval across 200 stratified 80% subsamples is 0.0143 to 0.0343. Contract ranks first in every subsample. This is an unadjusted stability check, not a causal or adjusted effect ranking.

## Corrected adjusted model

Recoding `No internet service` as `No` for the two included add-on fields removes the exact duplicate columns while preserving `InternetService` in the model. The corrected model converges on 7,043 rows. Its contract odds ratios relative to month-to-month are:

| Contract | Adjusted odds ratio (95% CI) |
|---|---:|
| One year | 0.516 (0.419 to 0.635) |
| Two year | 0.262 (0.187 to 0.368) |
The blind reference model uses a smaller adjustment set. Its odds ratios and 95% CIs versus this corrected specification are One year: 0.470 (0.383 to 0.577) versus 0.516 (0.419 to 0.635); Two year: 0.216 (0.154 to 0.302) versus 0.262 (0.187 to 0.368). The point estimates differ modestly, but the intervals overlap.

Median tenure is 12 months for month-to-month customers, 44 for one-year, and 64 for two-year customers. This overlap pattern emphasizes that contract and tenure are associated.

## Findings

| # | Finding | Severity | Measured evidence |
|---|---|---|---|
| 1 | ARFF loader failure | Major | The saved run exited 1 with NotImplementedError: String attributes not supported yet, sorry; stdout is 0 bytes, so none of the requested statistics were emitted. |
| 2 | Rank-deficient adjusted model | Major | The design has 18 columns but rank 16 (deficiency 2); the exact submitted model then fails with LinAlgError: Singular matrix. |

## Conclusion and limitations

The descriptive contract association is strong, and the independently fitted corrected model retains lower adjusted churn odds for longer contracts. This supports the response's qualitative association conclusion, but not because its saved code produced those results: that code fails at input and its specified regression is singular. The dataset is observational; self-selection, contract rules, and the large tenure differences prevent a causal interpretation. The corrected adjusted odds ratios are conditional associations, not effects of switching a customer to a longer contract.
