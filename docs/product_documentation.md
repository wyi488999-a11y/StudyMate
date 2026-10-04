# Product documentation

StudyMate is intended for postgraduate learners who want to find explanations in their English course notes. The input is a question plus the included text PDFs. The output is a concise answer with candidate source labels and expandable passages, or `not found`. The two-sentence hosted instruction is a prompt constraint, not a formally enforced guarantee.

The app loads each PDF page as a chunk. Before retrieval, it rejects questions matching its credential-term rule. Other questions use TF-IDF or hosted embeddings, with an answer threshold of 0.12. Below threshold it refuses. Otherwise it extracts sentences or calls the hosted LLM. An operational error has its own UI message. The [architecture diagram](architecture.mmd) shows this flow.

I use the 20 author-written diagnostic questions for development and 10 blind questions written by a classmate who had not seen the index for separate evaluation. Historical results are 17/20 versus 6/20 diagnostic and 8/10 versus 3/10 blind, measured by literal anchor-and-source matching. Total recorded hosted token cost is US$0.00274184. The [design decisions](design_decisions.md), [evaluation review](evaluation_review.md) and [evaluation protocol](../evals/README.md) explain the limitations and proposed targets.

The smallest working path is one supplied-note question, retrieval, one LLM generation call, and one displayed answer. Embedding retrieval is a separate API request, not a second agent step. `results/hosted_api_verification.csv` records an answered RAG question and an unrelated football question that was refused. This is a historical two-case check, not a robustness estimate.

StudyMate is not for grading, credentials, personal-data lookup or professional advice. It has no authentication, multi-user isolation, OCR or production rate limiting. Candidate citations must be inspected before relying on the answer.

## Targeted and reached metrics

Reached: historical hosted anchor-and-source matches 17/20 diagnostic and 8/10 blind, versus keyword 6/20 and 3/10; calculated token cost US$0.00274184.

Proposed targets for the next evaluation: at least 80% human-verified correct-and-supported answers on 50 new answerable questions and at least a 20 percentage-point improvement over the baseline; 20 unanswerable questions to test refusal. These targets were added after the historical run and do not imply preregistration. See the [evaluation protocol](../evals/README.md) for details.
