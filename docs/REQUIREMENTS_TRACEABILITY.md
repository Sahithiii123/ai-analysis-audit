# Requirements Traceability

| Requirement | Evidence files |
|---|---|
| R1: Evaluate method, assumptions, and conclusion validity | `docs/AUDIT_PROTOCOL.md`; `docs/RUBRIC.md`; `cases/*/audit.md`; `cases/*/audit_evidence.ipynb` |
| R2: Reproduce statistical failures or verify supported claims with code and numbers | `docs/FLAW_TAXONOMY.md`; `src/*_audit.py`; `tests/`; `cases/*/audit_evidence.ipynb`; `cases/*/results.json` |
| R3: Correct analysis with uncertainty and limitations | `cases/*/corrected_analysis.ipynb`; `cases/*/results.json`; `reports/summary_table.md` |
| R4: Real data and provenance | `src/fetch_data.py`; `docs/DATA_PROVENANCE.md`; `data/raw/` (ignored); `data/processed/` |
| R5: Python, SQL, and executed notebooks | `src/`; `sql/olist_delivery_vs_reviews.sql`; `cases/*/*.ipynb`; `Makefile`; `pyproject.toml` |
| R6: Clear, evidence-linked writing | `README.md`; `docs/`; `cases/*/audit.md`; `cases/*/corrected_analysis.ipynb`; `reports/summary_table.md` |

Audit reports, evidence notebooks, corrected analyses, and machine-readable results are present for all six submitted cases. The Olist source-data reference checkpoint remains pending as recorded in `docs/DATA_PROVENANCE.md`.