# Design decisions

## Problem and closest alternative

I address one problem: a postgraduate learner cannot quickly locate a relevant explanation in supplied course notes. StudyMate displays retrieved passages so the learner can check the answer against the notes. The learner persona is a design scenario, not a documented user interview.

Google's NotebookLM / Gemini Notebook is the closest documented alternative: it answers questions from uploaded sources and supplies citations. My project does not claim to invent that capability. My reason to build is control of this project's retrieval threshold, exact evaluation files, baseline and cost logs, with a no-key offline path. I have not performed a head-to-head product benchmark. Reference: [Google source-grounded chat documentation](https://support.google.com/gemininotebook/answer/16179559?hl=en).

## Why this technology

I choose RAG because the evidence must come from supplied notes. A general prompted LLM lacks that connection; narrow supervised learning would require labels for a different prediction task; an agent loop adds no necessary capability to a one-question workflow. TF-IDF excerpt search is my measured non-LLM baseline. Thresholds, cost arithmetic, file handling and scoring remain deterministic. The LLM is an optional generation layer, not an arithmetic or safety authority.

## Build and rent by layer

| Layer | Decision and actual component | Reason and trade-off |
| --- | --- | --- |
| Interface and serving | Reuse Streamlit; own the local UI and evidence display | Fast local delivery; no multi-user production controls |
| Orchestration | Own Python functions and source-only prompt | Transparent routing and refusals; more maintenance |
| Model | Rent OpenRouter access to openai/gpt-4o-mini and openai/text-embedding-3-small | No model training; API cost, latency and provider dependence |
| Data and retrieval | Own note inventory, pypdf loading and TF-IDF; rent embeddings only in hosted mode | Reproducible offline path; page chunking and repeated document embedding limit scale |
| Evaluation and observability | Own CSV question sets, keyword baseline, manifests and cost audit | Inspectable outcomes; exact matching needs human review |

I went directly to code because the threshold, exported evidence and identical-question comparison are the core learning goals. No comparison with a low-code implementation was conducted.

## Cost and deployment

For each hosted question, the normal path makes one embedding request for the question plus all document chunks, and one generation request. A threshold refusal omits the generation request. Historical cost is `(embedding_tokens × 0.02 + input_tokens × 0.15 + output_tokens × 0.60) / 1,000,000` USD, using the recorded price assumptions. The 30-question run totals US$0.00274184, averaging US$0.0000913947 per question. A simple 1,000-question extrapolation is US$0.0913947 only if token sizes, prices and retry behaviour stay the same. This excludes hosting, labour, network charges, verification calls and taxes. A larger corpus increases repeated embedding spend; caching is future work.

My deployment plan is a local Python environment, dependency install, no-key tests, then Streamlit. This package is not production hosting.

## Risks and implemented controls

| Risk | Current mitigation and evidence | Remaining limit |
| --- | --- | --- |
| Confident but irrelevant answer | Evidence threshold, visible candidate sources and expandable excerpts; error audit | Retrieval overlap does not prove answerability or claim support |
| Credential question | Deterministic refusal for API-key, password, access-token and secret-key terms before retrieval/API use | English pattern rule; may refuse benign explanations and does not detect every sensitive request |
| Misleading evaluation | Separate diagnostic/blind records, exact-score definition, overwrite protection and new-run hashes | Independent human semantic ratings are not included |
| API/connection failure | UI distinguishes operational failure from evidence refusal; request timeout | No retry budget, rate limit or production monitoring |
| Source instruction attack | Only curator-supplied local notes are loaded; source-only prompt; no tool execution | Prompt-level instruction separation and attack testing are incomplete |
| Privacy or unauthorised material | Supplied licence/inventory; no identities in released question CSV | Future collection needs a permission/consent record; no automated privacy filter |

I use the [OWASP Top 10 for LLM Applications 2025](https://owasp.org/projects/top-10-for-large-language-model-applications) as a named risk taxonomy, especially prompt injection, sensitive disclosure and misinformation. This is a design reference, not a claim of compliance or completed penetration testing.
