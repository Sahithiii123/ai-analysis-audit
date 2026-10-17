# Reproduce the Completed Audit on Another Machine

The six registered case audits are complete and committed separately. Submitted responses, run records, evidence notebooks, corrected analyses, and case results are preserved in the repository. Do not recollect or replace those responses when reproducing the current audit.

## Repository and environment

Raw datasets and `.env` credentials are excluded from Git. Before transferring the repository, check that the worktree is clean and that raw files and secrets are not tracked:

```powershell
git status --short
git ls-files data/raw
git log --oneline -6
```

`git ls-files data/raw` should print nothing. Do not force-add `.env`, Kaggle credentials, or raw dataset files. No remote push is part of the completed audit; configure a private remote only if you later choose to publish this repository.

Create the project environment outside OneDrive and install its pinned dependencies:

```powershell
python -m venv C:\dev\venvs\ai-analysis-audit
C:\dev\venvs\ai-analysis-audit\Scripts\python.exe -m pip install -r requirements.txt
C:\dev\venvs\ai-analysis-audit\Scripts\python.exe -m ipykernel install --sys-prefix --name ai-analysis-audit --display-name "Python (ai-analysis-audit)"
```

Validate the checkout without fetching data:

```powershell
C:\dev\venvs\ai-analysis-audit\Scripts\python.exe -m pytest tests -q
C:\dev\venvs\ai-analysis-audit\Scripts\python.exe -m ruff check src tests
```

## Data and provenance

The five non-Kaggle source datasets can be fetched with:

```powershell
C:\dev\venvs\ai-analysis-audit\Scripts\python.exe src\fetch_data.py
```

Olist's five raw CSVs are present in the user-provided project ZIP, but not in the extracted repository or Git. Their recorded SHA-256 hashes are in `cases/03_olist_delivery_reviews/results.json`. Before using or redistributing them, verify the current Kaggle terms. To reproduce from a clean Git checkout, either obtain an authorized copy and verify its hashes or fetch through the documented Kaggle flow after configuring credentials locally in the ignored `.env`. Never put credentials in commands, commits, or chat.

Raw files are required to independently rerun the reference notebooks and Olist analysis. The committed case results and executed notebooks preserve the current audit evidence but do not substitute for a fresh source-data retrieval.

## Reports and verification

After changing a case's `results.json`, regenerate the summary tables and README block, then verify all generated numbers:

```powershell
C:\dev\venvs\ai-analysis-audit\Scripts\python.exe src\build_reports.py
C:\dev\venvs\ai-analysis-audit\Scripts\python.exe src\verify_numbers.py
```

Do not run `make all` merely to rebuild report tables: it also fetches data and executes reference notebooks. `make test` and `make lint` do not fetch data.

## Existing model-code runs

Per-case model-code outputs and execution records are retained under `reports/ai_code_runs/`. The original responses in `cases/*/ai_output/raw_response.txt` are preserved; any execution failure or audit correction is recorded separately. Do not overwrite a response or its original code to make a run succeed. If collecting a new response or changing a question, document the protocol change and prompt before requesting that new output.

The recorded executions do not constitute a general security certification of arbitrary Python or a guarantee that Docker isolation and resource limits are appropriate on another host. Validate the sandbox on the destination machine before running any new untrusted code.

## Remaining data and interpretation limits

- The Olist source retrieval time is not recorded in the current provenance table, and current Kaggle terms still require verification before redistribution.
- The Telco source is marked public by OpenML, but a specific upstream license was not established.
- The case analyses are descriptive or predictive for their documented samples. They do not establish causal effects or population-wide generalization without an appropriate design.
- Use the case-specific audit reports and `reports/summary_table.md` for the completed findings and current reference-data statuses.
