# Retrieval augmented generation

Retrieval augmented generation, or RAG, first retrieves relevant passages from a trusted document collection. A language model then writes an answer using those passages as evidence. RAG is useful when an answer must be grounded in documents that the system owner controls.

---

# Citations and abstention

A citation should identify the source and page or chunk used for an answer. If the retrieval score is below a chosen threshold, the system should abstain and return `not found` rather than guess. Abstention rate and the error rate among abstained cases should both be measured.
