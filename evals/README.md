# Evaluation protocol

Install `requirements.txt` first. Both the app and evaluation script index only `data/public_pdfs/`. They do not index the question files or expected-answer columns.

```bash
python scripts/run_evaluation.py --label new_diagnostic
python scripts/run_evaluation.py --questions blind_questions.csv --label new_blind
python scripts/run_evaluation.py --hosted --questions blind_questions.csv --label new_hosted_blind
python scripts/audit_evaluation.py
```

## Question authorship and use

I wrote the 20 diagnostic questions for development. A classmate who had not seen the index wrote the 10 blind questions; I have confirmed that provenance. Keep the sets separate.

## Historical metric

`correct_and_cited` is the historical column name for a literal, case-insensitive expected-anchor match AND expected-source filename-stem presence. It is an automated proxy, not a semantic or claim-level citation judgement. The expected `.md` source names intentionally match the corresponding `.pdf` filename stems. Preserve this rule when reproducing the existing 17/20 and 8/10 results.

All three page chunks are retrieved at top_k=3. Consequently, the hosted source-presence result is not a strong test of citation specificity. S03 shows a valid paraphrase rejected by exact matching. Review anchors, semantic correctness and claim-level support separately; do not silently rewrite historical scores.

## Proposed next evaluation target

For a NEW independently authored set of at least 50 answerable questions, I propose at least 80% manually verified correct-and-supported answers and at least a 20 percentage-point gain over the same keyword baseline. Add 20 unanswerable questions, with a proposed refusal recall of at least 90% and false-refusal rate on answerable questions of at most 10%. These are forward-looking acceptance criteria, not targets registered before the existing results. A blinded human reviewer should score both methods using the same rubric. No LLM judge is currently used.

Freeze question text, expected evidence, model/prompt settings and file hashes before that new run. Tune only on diagnostic questions. A future reviewer must not see the system identity when assigning semantic scores. Larger tests are needed: one case changes the current blind result by 10 percentage points.

## Refusal and threshold analysis

Report refusal count / all questions, and error rate in the answers that would have been returned if the threshold had not blocked them. For hosted questions that were never generated, this counterfactual is unavailable without another controlled run. Do not substitute source absence or a refusal flag for that counterfactual.

`audit_evaluation.py` reports the historical refusal counts, separate no-key developer safety checks and a diagnostic-only offline threshold sweep. Safety checks are new developer-written tests, not extra blind observations. Its counterfactual error uses the same automated proxy and must not be described as human-rated error.

## Reproduction and record protection

Use a new `--label` for each evaluation. Existing files are protected unless `--overwrite` is explicitly provided. New runs save a manifest of question, source and code hashes. Hosted runs require a key and incur charges. Historical costs use the existing price constants and are calculated token costs, not billing receipts. New model prices must be checked before another paid evaluation.
