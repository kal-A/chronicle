# Evaluation report (e7-v1, deterministic_full)

Report schema: e7-report-v1

## single_prompt (24 results)

| Metric | Value | n/d | Applicability |
| --- | --- | --- | --- |
| citation_validity | — | 0/0 | not_applicable |
| citation_coverage | — | 0/0 | not_applicable |
| required_evidence_recall | 0.000 | 0/40 | applicable |
| role_recall | — | 0/0 | not_applicable |
| temporal_coverage | 0.000 | 0/6 | applicable |
| abstention_correct | 0.292 | 7/24 | applicable |
| forbidden_evidence_hits | 0.000 | 0/24 | applicable |
| cross_corpus_leakage | 0.000 | 0/24 | applicable |
| unacceptable_claims | 0.000 | 0/24 | applicable |

## basic_rag (24 results)

| Metric | Value | n/d | Applicability |
| --- | --- | --- | --- |
| citation_validity | — | 0/0 | not_applicable |
| citation_coverage | — | 0/0 | not_applicable |
| required_evidence_recall | 0.000 | 0/40 | applicable |
| role_recall | — | 0/0 | not_applicable |
| temporal_coverage | 0.000 | 0/6 | applicable |
| abstention_correct | 0.292 | 7/24 | applicable |
| forbidden_evidence_hits | 0.000 | 0/24 | applicable |
| cross_corpus_leakage | 0.000 | 0/24 | applicable |
| unacceptable_claims | 0.000 | 0/24 | applicable |

## planner_analyst (24 results)

| Metric | Value | n/d | Applicability |
| --- | --- | --- | --- |
| citation_validity | — | 0/0 | not_applicable |
| citation_coverage | — | 0/0 | not_applicable |
| required_evidence_recall | 0.000 | 0/40 | applicable |
| role_recall | — | 0/0 | not_applicable |
| temporal_coverage | 0.000 | 0/6 | applicable |
| abstention_correct | 0.292 | 7/24 | applicable |
| forbidden_evidence_hits | 0.000 | 0/24 | applicable |
| cross_corpus_leakage | 0.000 | 0/24 | applicable |
| unacceptable_claims | 0.000 | 0/24 | applicable |

## full_workflow (24 results)

| Metric | Value | n/d | Applicability |
| --- | --- | --- | --- |
| citation_validity | — | 0/0 | not_applicable |
| citation_coverage | — | 0/0 | not_applicable |
| required_evidence_recall | 0.000 | 0/40 | applicable |
| role_recall | — | 0/0 | not_applicable |
| temporal_coverage | 0.000 | 0/6 | applicable |
| abstention_correct | 0.292 | 7/24 | applicable |
| forbidden_evidence_hits | 0.000 | 0/24 | applicable |
| cross_corpus_leakage | 0.000 | 0/24 | applicable |
| unacceptable_claims | 0.000 | 0/24 | applicable |

## Gates

| Gate | Strategy | Status | Detail |
| --- | --- | --- | --- |
| no_forbidden_evidence | single_prompt | pass | 0 forbidden citation(s) |
| no_cross_corpus_leakage | single_prompt | pass | 0 cross-corpus citation(s) |
| citation_validity | single_prompt | not_applicable | citation_validity has no applicable denominator |
| citation_coverage | single_prompt | not_applicable | citation_coverage has no applicable denominator |
| required_evidence_recall | single_prompt | fail | required_evidence_recall=0.000 (threshold 0.80) |
| abstention_correctness | single_prompt | fail | 7/24 abstention decisions correct |
| no_forbidden_evidence | basic_rag | pass | 0 forbidden citation(s) |
| no_cross_corpus_leakage | basic_rag | pass | 0 cross-corpus citation(s) |
| citation_validity | basic_rag | not_applicable | citation_validity has no applicable denominator |
| citation_coverage | basic_rag | not_applicable | citation_coverage has no applicable denominator |
| required_evidence_recall | basic_rag | fail | required_evidence_recall=0.000 (threshold 0.80) |
| abstention_correctness | basic_rag | fail | 7/24 abstention decisions correct |
| no_forbidden_evidence | planner_analyst | pass | 0 forbidden citation(s) |
| no_cross_corpus_leakage | planner_analyst | pass | 0 cross-corpus citation(s) |
| citation_validity | planner_analyst | not_applicable | citation_validity has no applicable denominator |
| citation_coverage | planner_analyst | not_applicable | citation_coverage has no applicable denominator |
| required_evidence_recall | planner_analyst | fail | required_evidence_recall=0.000 (threshold 0.80) |
| abstention_correctness | planner_analyst | fail | 7/24 abstention decisions correct |
| no_forbidden_evidence | full_workflow | pass | 0 forbidden citation(s) |
| no_cross_corpus_leakage | full_workflow | pass | 0 cross-corpus citation(s) |
| citation_validity | full_workflow | not_applicable | citation_validity has no applicable denominator |
| citation_coverage | full_workflow | not_applicable | citation_coverage has no applicable denominator |
| required_evidence_recall | full_workflow | fail | required_evidence_recall=0.000 (threshold 0.80) |
| abstention_correctness | full_workflow | fail | 7/24 abstention decisions correct |
| semantic_entailment | — | incomplete | requires the single blinded human review (Slice 2) |
| usefulness | — | incomplete | requires the single blinded human review (Slice 2) |
