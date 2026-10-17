# Analysis Rubric

Score each dimension from zero to two. Scores describe the submitted AI analysis, not the corrected analysis. Quote a specific passage or point to a measured result for every score; do not infer a score from polish or confidence.

| Dimension | Zero | One | Two |
|---|---|---|---|
| Question framing | Misstates the target, population, unit, or task. | Mostly identifies the question but leaves a material ambiguity. | Defines target, population, unit, and descriptive/predictive/causal scope correctly. |
| Method choice | Method cannot answer the stated question. | Plausible method with an important mismatch or unjustified choice. | Method fits the question and its choice is explained. |
| Assumption checking | Relevant assumptions are ignored or clearly violated. | Some assumptions are checked, but material checks are missing. | Key assumptions are checked with appropriate evidence and caveats. |
| Leakage control | Material leakage or invalid evaluation is present. | Some controls exist, but a material risk remains unresolved. | Features and evaluation design respect time, groups, and data-processing boundaries. |
| Uncertainty quantification | No meaningful uncertainty or effect size is reported. | Some uncertainty is reported, but important estimates or comparisons lack it. | Main effects and metrics include suitable uncertainty and sample context. |
| Causal language discipline | Unsupported causal claims are central. | Causal wording is mixed or insufficiently qualified. | Claims match the design; observational limits are explicit. |
| Reproducibility | Code/data/steps are missing or the analysis cannot be reconstructed. | Partial details exist, but a material step or parameter is absent. | Data, code, settings, and execution are recorded well enough to reproduce results. |
| Conclusion validity | Main conclusion conflicts with or is unsupported by the numbers. | Conclusion is directionally plausible but overstates scope, precision, or evidence. | Main claims follow from the estimates and are appropriately bounded. |

Per-case scoring table must include dimension, score, quoted evidence or notebook/result reference, and one-sentence justification. Do not total scores as a substitute for the verdict; report both the profile and the evidence-based verdict.