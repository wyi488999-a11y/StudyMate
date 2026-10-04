# Evaluation design

An evaluation question needs an expected answer and an expected source. Correctness and citation correctness are separate checks: an answer may be plausible but cite the wrong source. A keyword-search baseline should run on exactly the same questions as the RAG system.

---

# Independent test questions

Questions written by the system builder can help tune prompts and thresholds, but they may reuse the source wording. A separate set written by someone who has not seen the index is a more credible blind test. Report the diagnostic set and blind set separately, using counts such as 8/10 rather than only percentages.
