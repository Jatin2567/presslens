# Roadmap

The current design centers on a reproducible simulated dataset, Python preparation, SQL analytics, a web dashboard, and a single-container deployment. Validate the current release before expanding the scope. The items below are **future work** until their code, tests, and evidence are present.

| Future capability | Why it may help | Evidence needed before claiming completion |
| --- | --- | --- |
| Real-source ingestion | Replace generated input with an authorized publishing source. | Source permission, field mapping, privacy/retention rules, incremental loading, retries, and reconciliation. |
| Scheduled refresh | Keep an authorized dataset current without manual builds. | A scheduler, idempotent jobs, run history, failure alerts, and atomic snapshot replacement. |
| Excel/Google Sheets analysis pack | Offer a reviewer-friendly pivot and calculation workflow. | A generated workbook or linked sheet, documented formulas, refresh steps, and reconciled results. CSV availability alone is not an integrated spreadsheet workflow. |
| Statistical uncertainty | Make small-sample comparisons easier to assess. | Minimum sample rules, confidence intervals where appropriate, documented assumptions, and numerical tests. |
| ML baseline | Evaluate a narrowly defined analytical question such as conversion propensity. | A defensible target, time-aware splits, leakage checks, baseline comparison, held-out evaluation, calibration, and a model card. No prediction capability is implied by the current dashboard. |
| AI-assisted explanations | Help users navigate metric definitions and evidence. | Source-grounded output, provenance, evaluation examples, failure handling, and explicit limits. An AI-written narrative is not a validated insight engine. |
| Larger-scale storage | Support requirements the snapshot no longer meets. | Measured query/load results and an accepted storage migration design. |
| Authenticated workspaces | Support governed, non-public datasets. | A concrete threat model, identity/access implementation, audit requirements, and tests. The public demo should contain simulated data only. |

For an internship portfolio, the strongest next improvement is a small, complete analysis: state a business question, show the cleaning decisions and SQL, inspect the results, explain a recommendation, and name what the data cannot establish. Keep the reproducible workflow and evidence ahead of feature count.
