# Evaluation review

## Independent blind questions

A classmate who had not seen the index wrote the 10 blind questions, S01–S10. They are evaluated separately from the developer-authored diagnostic questions.

## Recorded outcomes

| Set | System | Anchor and source matches | Source presence | Refusals |
| --- | --- | --- | --- | --- |
| Diagnostic 20 | Hosted RAG | 17/20 | 20/20 | 0/20 |
| Diagnostic 20 | Keyword excerpt | 6/20 | 17/20 | 2/20 |
| Blind 10 | Hosted RAG | 8/10 | 10/10 | 0/10 |
| Blind 10 | Keyword excerpt | 3/10 | 8/10 | 0/10 |

The blind difference is five additional proxy matches, or 50 percentage points. One case changes that score by ten percentage points. No inference about learning gains, population-wide accuracy or statistical significance is made.

## What the metric misses

The scorer looks for a literal expected anchor and a matching source stem. S03 contains the valid wording “retrieve relevant passages” while the anchor is “retrieves relevant passages”; the answer fails exact matching. S10's wording and expected source also merit review against the actual passages. The package preserves these original labels and scores rather than correcting them after seeing results. A new human review should retain original scores and add independent semantic and evidence judgements in separate columns.

Each PDF has one page, and top_k=3 includes the entire three-page corpus. Hosted source presence therefore cannot establish citation specificity. The interface displays retrieved passages, which supports human inspection but does not automatically validate citations.

## Leakage check

Code inspection confirms that the model receives the question and retrieved source text, not `expected_anchor`, `expected_source`, other question rows or result CSVs. The loader points only to the PDF directory. Source documents containing answers are expected in RAG and are not, by themselves, label leakage. Diagnostic wording overlap remains a development-set limitation. This check establishes how inputs reach the model; it does not measure a performance improvement from removing leakage.

## Refusal and threshold review

The historical 30-question hosted run has no refusals. A separate `hosted_api_verification.csv` records one relevant answered query and one irrelevant football query refused. That check is useful evidence of an end-to-end refusal path, but one case is not a robust safety rate.

The offline diagnostic sweep holds questions fixed and varies only the threshold. At 0.12 the score is 10/20 with two refusals. At 0.20 it falls to 6/20 with 12 refusals. Of the ten threshold-blocked cases that would otherwise produce text, six fail the proxy metric and four pass; the other two still produce no answer with the threshold disabled. A blanket increase thus discards useful answers. The disabled-threshold counterfactual is unavailable for those two cases, and the CSV marks them separately. This sweep is offline-only; its score scale cannot calibrate hosted embeddings.

Eight separate developer checks cover five unsupported requests and three supported ones. Before the credential rule, 7/8 passed: an API-key question received an unrelated note excerpt. After the narrow deterministic rule, 8/8 passed, including refusals on all five unsupported requests and none on the three supported ones. These hand-written checks and their observed before/after results are committed separately. They are neither extra blind questions nor proof that arbitrary unsupported or adversarial questions are safe.

## Cost and preservation

The recorded hosted diagnostic cost is US$0.00184331; blind cost is US$0.00089853; total is US$0.00274184. These figures exclude separate API verification costs and are token-price calculations, not invoices.

The package retains the recorded questions, answers, scores, token counts and costs. `evals/current_question_hashes.json` records the current question-file hashes; it does not establish which code version produced the historical results. New evaluation runs save question, source and code hashes and require a fresh output label unless overwrite is explicitly enabled.
