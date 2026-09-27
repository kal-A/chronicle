# Evaluation report (e7-v1, deterministic_full)

Report schema: e7-report-v1

## full_workflow (6 results)

| Metric | Value | n/d | Applicability |
| --- | --- | --- | --- |
| citation_validity | 1.000 | 3/3 | applicable |
| citation_coverage | 1.000 | 3/3 | applicable |
| required_evidence_recall | 0.143 | 1/7 | applicable |
| role_recall | 1.000 | 3/3 | applicable |
| temporal_coverage | — | 0/0 | not_applicable |
| abstention_correct | 0.667 | 4/6 | applicable |
| forbidden_evidence_hits | 0.000 | 0/6 | applicable |
| cross_corpus_leakage | 0.000 | 0/6 | applicable |
| unacceptable_claims | 0.000 | 0/6 | applicable |

## Gates

| Gate | Strategy | Status | Detail |
| --- | --- | --- | --- |
| no_forbidden_evidence | full_workflow | pass | 0 forbidden citation(s) |
| no_cross_corpus_leakage | full_workflow | pass | 0 cross-corpus citation(s) |
| citation_validity | full_workflow | pass | citation_validity=1.000 (threshold 0.95) |
| citation_coverage | full_workflow | pass | citation_coverage=1.000 (threshold 0.80) |
| required_evidence_recall | full_workflow | fail | required_evidence_recall=0.143 (threshold 0.80) |
| abstention_correctness | full_workflow | fail | 4/6 abstention decisions correct |
| semantic_entailment | — | incomplete | requires the single blinded human review (Slice 2) |
| usefulness | — | incomplete | requires the single blinded human review (Slice 2) |
