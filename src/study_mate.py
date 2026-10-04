"""Core retrieval, grounded-answer, evaluation and cost-logging functions for StudyMate.

The module runs without an API key using transparent local TF-IDF retrieval.
When hosted mode is selected and an OpenAI or OpenRouter key is configured,
`answer_question` uses hosted embeddings and an LLM. Retrieved source labels
refer to local chunks; they do not verify support for individual claims.
"""
from __future__ import annotations

import csv
import json
import math
import os
import re
import urllib.request
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

TOKEN = re.compile(r"[a-zA-Z0-9]+")
STOP = {"a", "an", "and", "are", "as", "at", "be", "by", "can", "did", "do", "does", "for", "from", "how", "in", "is", "it", "of", "on", "or", "should", "the", "to", "what", "when", "where", "which", "who", "why", "with"}
EMBEDDING_PRICE_PER_MILLION_USD = 0.02
GPT4O_MINI_INPUT_PRICE_PER_MILLION_USD = 0.15
GPT4O_MINI_OUTPUT_PRICE_PER_MILLION_USD = 0.60


@dataclass
class Chunk:
    chunk_id: str
    source: str
    page: str
    text: str


@dataclass
class Answer:
    answer: str
    citations: list[Chunk]
    score: float
    refused: bool
    mode: str
    estimated_input_tokens: int = 0
    estimated_output_tokens: int = 0
    embedding_tokens: int = 0


def load_local_env(root: str | Path) -> None:
    """Load a local `.env` file without adding a dependency; `.env` is gitignored."""
    path = Path(root) / '.env'
    if not path.exists():
        return
    for raw in path.read_text(encoding='utf-8').splitlines():
        if '=' in raw and not raw.lstrip().startswith('#'):
            key, value = raw.split('=', 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _api_key() -> str:
    return os.getenv('OPENROUTER_API_KEY') or os.environ['OPENAI_API_KEY']


def _base_url() -> str:
    explicit = os.getenv('AI_API_BASE_URL')
    if explicit:
        return explicit.rstrip('/')
    return 'https://openrouter.ai/api/v1' if _api_key().startswith('sk-or-') else 'https://api.openai.com/v1'


def _model_name() -> str:
    configured = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    if _base_url().startswith('https://openrouter.ai') and configured == 'gpt-4o-mini':
        return 'openai/gpt-4o-mini'
    return configured


def _embedding_model_name() -> str:
    configured = os.getenv('OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')
    if _base_url().startswith('https://openrouter.ai') and configured == 'text-embedding-3-small':
        return 'openai/text-embedding-3-small'
    return configured


def words(text: str) -> list[str]:
    return [x.lower() for x in TOKEN.findall(text) if x.lower() not in STOP]


def load_notes(notes_dir: str | Path) -> list[Chunk]:
    """Read `.md`/`.txt` notes or PDF pages; `---` starts a text-note page-like chunk."""
    chunks: list[Chunk] = []
    for path in sorted(Path(notes_dir).glob("*")):
        suffix = path.suffix.lower()
        if suffix == '.pdf':
            try:
                from pypdf import PdfReader
            except ImportError as exc:
                raise RuntimeError('PDF input requires pypdf. Run: python -m pip install -r requirements.txt') from exc
            for number, page in enumerate(PdfReader(str(path)).pages, 1):
                clean = (page.extract_text() or '').strip()
                if clean:
                    chunks.append(Chunk(f"{path.stem}-{number}", path.name, str(number), clean))
            continue
        if suffix not in {".md", ".txt"}:
            continue
        for number, block in enumerate(path.read_text(encoding="utf-8").split("\n---\n"), 1):
            clean = block.strip()
            if clean:
                chunks.append(Chunk(f"{path.stem}-{number}", path.name, str(number), clean))
    if not chunks:
        raise ValueError("No .md, .txt or .pdf note files found. Add notes before indexing.")
    return chunks


def _idf(chunks: Iterable[Chunk]) -> dict[str, float]:
    all_chunks = list(chunks)
    document_frequency = Counter({term: 0 for term in set()})
    for chunk in all_chunks:
        document_frequency.update(set(words(chunk.text)))
    n = len(all_chunks)
    return {term: math.log((n + 1) / (count + 1)) + 1 for term, count in document_frequency.items()}


def retrieve(question: str, chunks: list[Chunk], top_k: int = 3) -> list[tuple[Chunk, float]]:
    """Return TF-IDF cosine-ranked source chunks; this is the offline baseline/retriever."""
    idf = _idf(chunks)
    q = Counter(words(question))
    q_norm = math.sqrt(sum((q[t] * idf.get(t, 0)) ** 2 for t in q)) or 1
    ranked = []
    for chunk in chunks:
        d = Counter(words(chunk.text))
        dot = sum(q[t] * d[t] * idf.get(t, 0) ** 2 for t in q)
        d_norm = math.sqrt(sum((d[t] * idf.get(t, 0)) ** 2 for t in d)) or 1
        ranked.append((chunk, dot / (q_norm * d_norm)))
    return sorted(ranked, key=lambda pair: pair[1], reverse=True)[:top_k]


def keyword_baseline(question: str, chunks: list[Chunk]) -> Answer:
    """Baseline: return the best matching source excerpt, never ask an LLM."""
    best, score = retrieve(question, chunks, top_k=1)[0]
    if score < 0.08:
        return Answer("not found", [], score, True, "keyword")
    excerpt = " ".join(re.split(r"(?<=[.!?])\s+", best.text.replace("\n", " "))[:2])
    return Answer(excerpt, [best], score, False, "keyword")


def _extractive_answer(question: str, evidence: list[Chunk]) -> str:
    q = set(words(question))
    sentences = []
    for chunk in evidence:
        for sentence in re.split(r"(?<=[.!?])\s+", chunk.text):
            value = len(q.intersection(words(sentence)))
            if value:
                sentences.append((value, sentence.strip()))
    selected = [sentence for _, sentence in sorted(sentences, reverse=True)[:2]]
    return " ".join(selected) or "not found"


def _openai_json(endpoint: str, payload: dict) -> dict:
    body = json.dumps(payload).encode()
    headers = {"Authorization": f"Bearer {_api_key()}", "Content-Type": "application/json"}
    if _base_url().startswith('https://openrouter.ai'):
        headers['HTTP-Referer'] = 'http://localhost:8510'
        headers['X-Title'] = 'StudyMate Course Project'
    request = urllib.request.Request(f"{_base_url()}/{endpoint}", data=body, headers=headers)
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.loads(response.read())


def _openai_answer(question: str, evidence: list[Chunk]) -> tuple[str, int, int]:
    """Call a hosted LLM with source-only instructions using the REST API."""
    source_text = "\n\n".join(f"[{c.source}, page {c.page}]\n{c.text}" for c in evidence)
    prompt = (
        "Answer in no more than two sentences using ONLY the supplied excerpts. "
        "If they do not answer the question, reply exactly: not found.\n\n"
        f"Question: {question}\n\nExcerpts:\n{source_text}"
    )
    response = _openai_json('chat/completions', {"model": _model_name(), "messages": [{"role": "user", "content": prompt}], "temperature": 0})
    usage = response.get('usage', {})
    return response['choices'][0]['message']['content'].strip(), usage.get('prompt_tokens', 0), usage.get('completion_tokens', 0)


def _openai_retrieve(question: str, chunks: list[Chunk], top_k: int = 3) -> tuple[list[tuple[Chunk, float]], int]:
    """Use a hosted embedding model for retrieval when an API key is configured."""
    response = _openai_json('embeddings', {'model': _embedding_model_name(), 'input': [question] + [c.text for c in chunks]})
    vectors = [item['embedding'] for item in sorted(response['data'], key=lambda x: x['index'])]
    q, document_vectors = vectors[0], vectors[1:]
    def cosine(left, right):
        denominator = math.sqrt(sum(x*x for x in left)) * math.sqrt(sum(x*x for x in right))
        return sum(x*y for x, y in zip(left, right)) / denominator if denominator else 0.0
    ranked = sorted(((chunk, cosine(q, vector)) for chunk, vector in zip(chunks, document_vectors)), key=lambda pair: pair[1], reverse=True)
    return ranked[:top_k], response.get('usage', {}).get('prompt_tokens', 0)


def answer_question(question: str, chunks: list[Chunk], threshold: float = 0.12, use_llm: bool = False) -> Answer:
    """Retrieve evidence, abstain below threshold, then answer from evidence only."""
    # Explicit non-use: credential questions never reach a model or the retriever.
    if re.search(r"\b(?:api[ -]?keys?|passwords?|access[ -]?tokens?|secret[ -]?keys?)\b", question, re.I):
        return Answer("not found", [], 0.0, True, "policy_refusal")
    embedding_tokens = 0
    input_tokens = output_tokens = 0
    if use_llm and not (os.getenv('OPENAI_API_KEY') or os.getenv('OPENROUTER_API_KEY')):
        raise ValueError('Hosted mode requires OPENAI_API_KEY or OPENROUTER_API_KEY.')
    if use_llm:
        retrieved, embedding_tokens = _openai_retrieve(question, chunks)
    else:
        retrieved = retrieve(question, chunks)
    evidence = [chunk for chunk, _ in retrieved]
    score = retrieved[0][1]
    if score < threshold:
        return Answer("not found", [], score, True, "hosted_embedding_and_llm" if use_llm else "offline_extractive", 0, 0, embedding_tokens)
    if use_llm:
        text, input_tokens, output_tokens = _openai_answer(question, evidence)
        mode = "hosted_embedding_and_llm"
    else:
        text, mode = _extractive_answer(question, evidence), "offline_extractive"
    if text.lower().strip() == "not found":
        return Answer("not found", [], score, True, mode, input_tokens, output_tokens, embedding_tokens)
    if mode == 'hosted_embedding_and_llm':
        return Answer(text, evidence, score, False, mode, input_tokens, output_tokens, embedding_tokens)
    return Answer(text, evidence, score, False, mode, math.ceil(sum(len(c.text) for c in evidence) / 4), math.ceil(len(text) / 4), embedding_tokens)


def citation_label(answer: Answer) -> str:
    return "; ".join(f"{c.source}, page {c.page}" for c in answer.citations) or "None"


def write_cost_log(path: str | Path, question: str, answer: Answer, embedding_tokens: int = 0) -> None:
    """Log provider token usage in hosted mode and character-based estimates offline.

    Hosted cost uses the module price constants; offline API cost is zero.
    The CSV field names are retained for compatibility with historical logs."""
    new_file = not Path(path).exists()
    with Path(path).open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["question", "mode", "embedding_tokens", "input_tokens_est", "output_tokens_est", "provider", "listed_price_reference", "actual_cost"])
        if new_file:
            writer.writeheader()
        embed = answer.embedding_tokens or embedding_tokens
        hosted = answer.mode == 'hosted_embedding_and_llm'
        cost = embed * EMBEDDING_PRICE_PER_MILLION_USD / 1_000_000
        if hosted:
            cost += answer.estimated_input_tokens * GPT4O_MINI_INPUT_PRICE_PER_MILLION_USD / 1_000_000
            cost += answer.estimated_output_tokens * GPT4O_MINI_OUTPUT_PRICE_PER_MILLION_USD / 1_000_000
        writer.writerow({"question": question, "mode": answer.mode, "embedding_tokens": embed, "input_tokens_est": answer.estimated_input_tokens, "output_tokens_est": answer.estimated_output_tokens, "provider": _model_name() if hosted else 'offline', "listed_price_reference": "gpt-4o-mini: $0.15 input/$0.60 output; text-embedding-3-small: $0.02 per 1M tokens", "actual_cost": f"${cost:.8f}" if hosted else 'offline $0.00'})
