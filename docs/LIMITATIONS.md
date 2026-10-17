# Limitations and Remaining Work

This register describes scope, provenance, and process limitations for the completed six-case audit. It is not an additional finding about any model.

## Completed checkpoint

- Submitted responses are preserved verbatim, with case-specific run records and audit evidence. Audit verdicts and demonstrated findings are recorded in each case's `results.json`.
- All six case reference results and model-output audits are complete in their result records. The Olist raw CSVs are absent from the extracted working tree but are present in the user-provided ZIP; their five SHA-256 values match `cases/03_olist_delivery_reviews/results.json`.
- The five locally available non-Olist source datasets have recorded hashes. Raw data are git-ignored and must be retrieved again on another machine.
- The Olist source CSVs are not present in the extracted repository's configured data directory. A fresh analysis there requires placing or fetching the authorized source files and verifying current Kaggle terms. The persisted case reference results are complete, but they do not make the extracted checkout independently rerunnable without those CSVs.
- The reference analyses describe their documented samples or evaluate internal predictive holdouts. They do not identify causal effects or justify generalization beyond a defensible sampling design.

## Scope of the model review

- The audit includes six cases, one response/run per case, from one model family. It is a set of case studies, not a benchmark, a replication study, or evidence about other model families or later versions. Results should not be generalized beyond the cases and recorded runs.
- Responses were obtained through a chat interface. Sampling settings were not exposed or recorded, so generation randomness and repeatability cannot be assessed.
- All analysis and audit results were produced on one machine. Re-running the code on another machine may produce differences from software versions, platform behavior, random-number implementations, or unavailable source files.

## Response and prompt records

- Case 03's `ai_output/PASTE_HERE.md` was rebuilt from three pasted response pieces and headings were added to make the record conform to the validator. The saved `raw_response.txt` is authoritative for the original response; the rebuilt paste file is a validation aid and must not be treated as an unaltered transcript.
- On 2026-10-16, after response collection, the validator was changed to accept section headings as plain text or Markdown `###` headings, case-insensitively and with an optional colon. When the response omitted a code-section heading, validation instead checks for a Python code block between the analysis plan and written conclusion. This format accommodation is documented in `docs/AUDIT_PROTOCOL.md`; it did not alter prompts or response content.
- An Olist pilot script named `olist_late_delivery_reviews.py` was discarded. Its prompt was not registered, asked for a confident conclusion, and omitted the seller-level question. It was not used for the registered case analysis, its results, or the current audit. The registered Olist prompt and preserved run are the relevant records.

## Reproducibility and operational limits

- Recreate the pinned Python environment and retrieve source datasets using the documented provenance steps before rerunning analyses on another machine. Olist retrieval additionally requires approved Kaggle access and license review.
- Per-case AI-code run records preserve outputs and execution outcomes. They are evidence for the recorded runs, not a general security certification of arbitrary Python or a guarantee that the runner's isolation/resource limits are suitable for another host.
- The six case audits are complete for the submitted responses. New responses or changed questions require preserving their prompts and metadata and documenting any protocol changes before adding results.
- Regenerate the summaries with `src/build_reports.py` and verify them with `src/verify_numbers.py` after any case-result update.