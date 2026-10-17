# AI Analysis Audit

This repository documents independent, reproducible audits of six AI-generated analyses using public datasets: bank marketing, telecom churn, Olist delivery and reviews, Berkeley admissions, Adult income, and Iris measurements. It preserves submitted responses, reproduces their claims against the data, records corrected estimates and uncertainty, and distinguishes measured findings from causal or population-wide claims.

## Headline findings

<!-- BEGIN AUTO HEADLINE FINDINGS -->

- **01_bank_marketing — Source-order performance:** The source-order holdout's ROC-AUC is -0.135 lower than the random-holdout result (95% CI -0.153 to -0.117). The PR-AUC difference is -0.019 (95% CI -0.054 to 0.022), which includes zero.
- **02_telco_churn — ARFF loader failure:** The saved run exited 1 with NotImplementedError: String attributes not supported yet, sorry; stdout is 0 bytes, so none of the requested statistics were emitted.
- **03_olist_delivery_reviews — Multiple comparisons:** 75 flags among 623 tested sellers; 26 remain after Benjamini-Hochberg and 13 after Bonferroni adjustment.
- **04_simpsons_paradox — Standardized-gap framing:** The reproduced common-mix difference is 4.3 percentage points favoring women (95% fixed-weight Wald interval 0.7 to 7.9); the overall female-minus-male gap is -14.2 points. This is a substantial reduction and reversal, but the interval is not centered near zero and excludes zero under the stated model.
- **05_multiple_comparisons — Missingness direction:** Missing workclass and occupation records have lower high-income rates, but missing native-country records are +1.8 percentage points higher than observed records (95% CI -1.1 to +4.8). The broad claim that all three missingness patterns skew lower income is not supported.

<!-- END AUTO HEADLINE FINDINGS -->

## Case summary

<!-- BEGIN AUTO CASE RESULTS -->

The table below is generated from the six case `results.json` files.

| Case | Reference status | Reference rows | Reference metric | AI audit status | Verdict | Demonstrated findings |
|---|---|---:|---|---|---|---:|
| 01_bank_marketing | complete | 45211 | PR-AUC 0.396 | complete | Partly reliable | 1 |
| 02_telco_churn | complete | 7043 | Churn prevalence 0.265 | complete | Partly reliable | 2 |
| 03_olist_delivery_reviews | complete | 95830 | Mean review score late/on-time 2.567/4.294 | complete | Partly reliable | 4 |
| 04_simpsons_paradox | complete | 4526 | CMH OR 1.105 | complete | Partly reliable | 1 |
| 05_multiple_comparisons | complete | 48842 | >$50K prevalence 0.239 | complete | Reliable | 2 |
| 06_iris_control | complete | 150 | Measurements compared 4 | complete | Reliable | 0 |

<!-- END AUTO CASE RESULTS -->

## What the AI got right

- The Bank Marketing random-holdout performance and the main prediction workflow reproduce; the audit qualifies how that score changes under a source-row-order stress test.
- The Telco response identified contract type as strongly associated with churn, and corrected adjusted contract comparisons retain that ordering after fixing a singular model design.
- The Olist analysis found substantially lower reviews for late deliveries; the audit adds review-selection and seller-denominator checks rather than treating the association as causal.
- The Berkeley response recognized the role of department composition; common-mix standardization reverses the marginal direction but does not yield a near-zero point estimate.
- The Adult response’s broad sample associations and internal holdout AUC reproduce; the audit qualifies missingness direction, underflowed p-values, and unlike effect-size scales.
- The Iris response’s descriptive conclusions, mean intervals, and sample-scope cautions reproduce.

## Method in six steps

1. Freeze each question and preserve the submitted response and metadata without editing its original code.
2. Record source provenance, row grain, checksums, sample filters, and missing-data handling.
3. Reproduce the submitted code and headline numerical claims using the recorded data and run output.
4. Independently recompute estimates, intervals, sensitivity checks, and any demonstrated flaw.
5. Write evidence and corrected-analysis notebooks; keep associations, prediction, and causal claims distinct.
6. Save case findings in `results.json`, generate the summary tables, and verify every generated number.

## Limitations

This is six case studies, one response/run per case, from one model family, not a benchmark or evidence of general model performance. Responses came through a chat interface; sampling settings were not recorded by the interface. All results were produced on one machine. Dataset sampling frames and provenance constrain generalization, and these audits do not establish causation. Olist raw files are in the user-provided ZIP but not the extracted working tree; consult [DATA_PROVENANCE.md](docs/DATA_PROVENANCE.md) for the recorded hashes and unverified license status. See [LIMITATIONS.md](docs/LIMITATIONS.md) for the complete register.

## Reproduce

Run these PowerShell commands from the repository root. Use the documented environment outside OneDrive:

```powershell
python -m venv C:\dev\venvs\ai-analysis-audit
C:\dev\venvs\ai-analysis-audit\Scripts\python.exe -m pip install -r requirements.txt
C:\dev\venvs\ai-analysis-audit\Scripts\python.exe -m pytest tests -q
C:\dev\venvs\ai-analysis-audit\Scripts\python.exe -m ruff check src tests
C:\dev\venvs\ai-analysis-audit\Scripts\python.exe src\build_reports.py
C:\dev\venvs\ai-analysis-audit\Scripts\python.exe src\verify_numbers.py
```

To refetch non-Kaggle inputs and rerun registered reference notebooks, first configure `DATA_DIR` as documented in `.env.example`, then run:

```powershell
C:\dev\venvs\ai-analysis-audit\Scripts\python.exe src\fetch_data.py
C:\dev\venvs\ai-analysis-audit\Scripts\python.exe src\execute_reference_notebooks.py
C:\dev\venvs\ai-analysis-audit\Scripts\python.exe src\build_case_results.py
C:\dev\venvs\ai-analysis-audit\Scripts\python.exe src\build_reports.py
C:\dev\venvs\ai-analysis-audit\Scripts\python.exe src\verify_numbers.py
```

Olist requires authorized Kaggle access and license verification before download; see [DATA_PROVENANCE.md](docs/DATA_PROVENANCE.md). These commands do not collect new model responses or execute model-written code. `make test` and `make lint` are equivalents for the test and lint steps.

## Repository map

- `cases/`: prompts, preserved outputs, audit reports, evidence/corrected notebooks, and result records for each case.
- `src/`: source retrieval, reference analyses, audit helpers, report generation, and validation.
- `tests/`: focused and project-level tests, including test-only fixtures.
- `data/`: downloaded/processed inputs; raw data are ignored by Git.
- `reports/`: generated cross-case summaries and recorded AI-code runs.
- `docs/`: audit protocol, provenance, rubric, limitations, and reproducibility notes.
- `sql/` and `sandbox/`: Olist query and isolated AI-code execution configuration.
