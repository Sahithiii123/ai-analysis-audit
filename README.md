
# AI Analysis Audit
 
**Evaluating AI-generated data analyses on real datasets: checking method choice and assumptions, stress-testing the statistics, and writing the better analysis.**
 
A model writes the analysis. This project checks whether the statistics hold up, with every claim reproduced in code on real public data, and then delivers a corrected analysis with honest uncertainty and a clear takeaway.
 
## What this project demonstrates
 
| The work | How this repo shows it |
|---|---|
| **Evaluate AI-built analyses on real datasets** | Six real public datasets. For each AI analysis: is the method appropriate, are the assumptions checked, and does the conclusion actually follow from the numbers? |
| **Red-team the statistics** | Targeted checks for data leakage, p-hacking and multiple comparisons, confounding, Simpson's paradox, selection bias, and missing uncertainty. Each flaw claim is reproduced with an effect size and a confidence interval. |
| **Write the better analysis** | A corrected notebook per case: sound methodology, bootstrap and analytic intervals, sensitivity checks, and a short plain-language takeaway with a before-versus-after comparison. |
| **Python, SQL, notebooks** | Python (pandas, NumPy, SciPy, statsmodels, scikit-learn), SQL on DuckDB, executed Jupyter notebooks, pytest, ruff, GitHub Actions CI, and a Docker sandbox for running model-written code. |
| **Clear written English** | Every audit follows one structure: question, method review, assumption review, conclusion check, flaws with measured evidence, what the AI got right, verdict, and rubric scores. |
 
## How each audit works
 
1. Freeze each question and preserve the submitted response and metadata without editing its original code.
2. Record source provenance, row grain, checksums, sample filters, and missing-data handling.
3. Reproduce the submitted code and headline numerical claims using the recorded data and run output.
4. Independently recompute estimates, intervals, sensitivity checks, and any demonstrated flaw.
5. Write evidence and corrected-analysis notebooks; keep associations, prediction, and causal claims distinct.
6. Save case findings in `results.json`, generate the summary tables, and verify every generated number.
## Measured findings
 
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
 
## What each case tests
 
- **01 Bank Marketing:** leakage control, validation design, calibration, and generalization under a source-order holdout.
- **02 Telco Churn:** confounding, causal wording, model diagnostics (collinearity), and repairing and re-running failed code.
- **03 Olist Delivery and Reviews:** SQL on DuckDB, review-selection bias, multiple-testing correction on seller rankings, and confounder-adjusted effect estimates.
- **04 Berkeley Admissions:** Simpson's paradox and standardized comparisons.
- **05 Adult Income:** multiple-comparison correction (Bonferroni, Benjamini-Hochberg), missing-data patterns, and effect sizes versus p-values.
- **06 Iris (control):** a pre-registered control case. It confirms the audit method does not manufacture flaws when an analysis is sound.
## What the AI got right
 
- The Bank Marketing random-holdout performance and the main prediction workflow reproduce; the audit adds a source-row-order stress test.
- The Telco response identified contract type as strongly associated with churn, and the corrected adjusted comparisons keep that ordering.
- The Olist analysis found substantially lower reviews for late deliveries; the audit adds review-selection and seller-denominator checks.
- The Berkeley response recognized the role of department composition; standardization confirms the marginal direction reverses.
- The Adult response's broad sample associations and internal holdout AUC reproduce.
- The Iris response's descriptive conclusions and mean intervals reproduce.
## Built for rigor and reproducibility
 
- The audit protocol, flaw taxonomy, and scoring rubric were written before any model output was collected ([docs/AUDIT_PROTOCOL.md](docs/AUDIT_PROTOCOL.md)).
- Independent reference analyses were written on the real data before the AI outputs were audited.
- Original model responses are preserved verbatim; every audit number is generated from `results.json` and checked by `src/verify_numbers.py`.
- Fixed seeds, pinned dependencies, unit-tested audit helpers, and CI.
## Scope
 
A focused six-case study: one model family, one run per case, built to demonstrate the audit method rather than to rank models. Findings describe associations in the documented public datasets, and causal claims are called out explicitly. Data sources, checksums, and licenses are in [docs/DATA_PROVENANCE.md](docs/DATA_PROVENANCE.md); the full register is in [docs/LIMITATIONS.md](docs/LIMITATIONS.md).
 
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
