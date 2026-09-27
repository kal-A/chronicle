# Evaluation report (e7-v1, qwen_gate)

Report schema: e7-report-v1

## full_workflow (3 results)

| Metric | Value | n/d | Applicability |
| --- | --- | --- | --- |
| citation_validity | — | 0/0 | not_applicable |
| citation_coverage | — | 0/0 | not_applicable |
| required_evidence_recall | 0.000 | 0/7 | applicable |
| role_recall | — | 0/0 | not_applicable |
| temporal_coverage | 0.000 | 0/3 | applicable |
| abstention_correct | 0.000 | 0/3 | applicable |
| forbidden_evidence_hits | 0.000 | 0/3 | applicable |
| cross_corpus_leakage | 0.000 | 0/3 | applicable |
| unacceptable_claims | 0.000 | 0/3 | applicable |

## Gates

| Gate | Strategy | Status | Detail |
| --- | --- | --- | --- |
| no_forbidden_evidence | full_workflow | pass | 0 forbidden citation(s) |
| no_cross_corpus_leakage | full_workflow | pass | 0 cross-corpus citation(s) |
| citation_validity | full_workflow | not_applicable | citation_validity has no applicable denominator |
| citation_coverage | full_workflow | not_applicable | citation_coverage has no applicable denominator |
| required_evidence_recall | full_workflow | fail | required_evidence_recall=0.000 (threshold 0.80) |
| abstention_correctness | full_workflow | fail | 0/3 abstention decisions correct |
| semantic_entailment | — | incomplete | requires the single blinded human review (Slice 2) |
| usefulness | — | incomplete | requires the single blinded human review (Slice 2) |
