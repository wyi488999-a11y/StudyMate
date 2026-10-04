"""Regression checks with stubbed API responses; no network requests."""
import csv
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import study_mate as m
chunks = [m.Chunk('1', 'notes.pdf', '1', 'Evidence.')]
with patch.dict(os.environ, {}, clear=True):
    a = m.answer_question('unknown', chunks)
    with tempfile.TemporaryDirectory() as tmp:
        m.write_cost_log(Path(tmp) / 'cost.csv', 'unknown', a)
    try:
        m.answer_question('unknown', chunks, use_llm=True)
    except ValueError:
        pass
    else:
        raise AssertionError('Missing key must not silently use offline mode')
with patch.dict(os.environ, {'OPENROUTER_API_KEY':'test-key', 'AI_API_BASE_URL':'https://openrouter.ai/api/v1'}, clear=True), patch.object(m, '_openai_retrieve', return_value=([(chunks[0], .8)], 10)), patch.object(m, '_openai_answer', return_value=('not found', 100, 5)):
    a = m.answer_question('unknown', chunks, use_llm=True)
    assert a.refused and a.estimated_input_tokens == 100 and a.estimated_output_tokens == 5
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / 'cost.csv'
        m.write_cost_log(p, 'unknown', a)
        row = next(csv.DictReader(p.open()))
        assert row['actual_cost'] == '$0.00001820', row
print('Hosted-path regression checks passed (no network).')
