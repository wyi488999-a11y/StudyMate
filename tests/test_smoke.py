"""Standard-library smoke tests for retrieval, refusal and baseline behaviour."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.study_mate import answer_question, keyword_baseline, load_notes

chunks = load_notes(ROOT / 'data' / 'public_pdfs')
answer = answer_question('What does RAG do?', chunks)
assert not answer.refused and 'grounded' in answer.answer.lower()
assert any(c.source == '01_rag.pdf' for c in answer.citations)
unknown = answer_question('Who won the football match?', chunks)
assert unknown.refused and unknown.answer == 'not found'
baseline = keyword_baseline('What is an independent test?', chunks)
assert not baseline.refused and baseline.citations
print('Smoke tests passed.')
