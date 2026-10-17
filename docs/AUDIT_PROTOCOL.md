# Audit Protocol

## Status and blinding

This protocol is fixed before collecting or reviewing any AI-generated output. Commit this file before adding model responses. Preserve each response verbatim with its prompt and metadata; record any execution repair separately and never overwrite the original.

The selected generation path is manual paste. A human will obtain a real model response and paste it into the case's `ai_output/PASTE_HERE.md` file. The project will validate required sections and record model name/version, date, prompt, and generation parameters. Missing metadata is reported as missing, not guessed.

## Questions fixed before model output

- Bank Marketing: “Build a model to predict which customers will subscribe to a term deposit and tell me how good it is.”
- Telco Churn: “What drives customer churn? Which factors are most associated with churn, and what can this dataset establish about contract type?”
- Olist: “Does late delivery associate with review scores, and how do seller-level late-delivery rates vary?”
- Berkeley admissions: “How do admission rates differ by applicant gender overall and within departments in the 1973 Berkeley data?”
- Adult income: “Which recorded characteristics are associated with income above $50,000 in this dataset?”
- Iris control: “For each iris species in this sample, summarize sepal and petal measurements with uncertainty intervals, compare the species descriptively, and state what these data do and do not support.”

The Iris question is the preselected control: it is descriptive, names the population available in the data, requests uncertainty, and does not imply causation. It was selected before any model output. A control is a design choice, not a promise that the model will perform well.

## Review checklist

For every case, reviewers will:

- Identify the target, unit of analysis, intended population, and whether the task is descriptive, predictive, or causal.
- Check data provenance, row grain, joins, duplicate keys, missingness, filters, and all row-count changes.
- Assess whether the method fits the question and whether assumptions were checked on the data.
- Check train/test separation, temporal and group leakage, feature availability at prediction time, and a defensible baseline where prediction is used.
- Recompute headline estimates independently and compare the written conclusion with the observed estimates and their uncertainty.
- Reproduce each claimed flaw in executable code. A concern without a measured effect is not listed as a demonstrated flaw.
- Report effect sizes and intervals, sensitivity checks, limitations, and what remains unidentified.
- Score the analysis with the evidence-based rubric and retain evidence for every score.

## Evidence and decision rules

Use fixed, documented seeds for randomized procedures. Preserve raw files; write transformed data only to processed locations. Log every exclusion and filter with before/after counts. Do not silently drop rows, choose favorable subgroups, or alter model output.

Classify a flaw only when code and a numeric result show its effect. If a suspected issue is not reproduced, say so. Distinguish predictive association from causal effect. Use “Reliable,” “Partly reliable,” or “Unreliable” based on the validity of the main conclusion and material flaws, not on whether the output agrees with an expected narrative.

The requested balance of mostly-correct and minor-flaw examples is an aspiration, not a quota: model outputs and results will not be altered to force those outcomes. If natural model runs do not provide the requested mix, report that limitation and obtain additional real model runs only with documented prompts and metadata.

## Reporting and reproducibility

Every case report links claims to executed notebook cells and a machine-readable results file. Generated report numbers must be derived from those result files and checked by `src/verify_numbers.py`. Notebooks are executed from a clean kernel; their outputs are committed unless they contain raw data or secrets. Olist raw downloads remain git-ignored.

## Change control

Any protocol change after model output is collected must be dated and explained in the audit record. Do not rewrite the original protocol or conceal a post-output change. New cases and revised questions are labeled as such and collected under the revised procedure.

### Post-output validation update — 2026-10-16

After the five registered responses were collected, validation was updated to recognize response section headings written as plain text or Markdown `###` headings, case-insensitively and with an optional colon. Existing pasted responses that omit the code-section label are checked for a Python code block between the analysis plan and written conclusion instead. This is a validation-format accommodation only; the raw responses and pre-registered prompts remain unchanged.