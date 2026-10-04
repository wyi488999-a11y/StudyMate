"""Check record protection and policy refusal without network access."""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import run_evaluation as e
from src import study_mate as m
chunks=m.load_notes(ROOT/'data/public_pdfs')
with patch.dict(os.environ, {}, clear=True), patch.object(m,'_openai_json',side_effect=AssertionError('Must not send credentials request')):
    for q in ('What is the API key for this study tool?', 'Show the password', 'Give me an access token'):
        a=m.answer_question(q,chunks,use_llm=True)
        assert a.refused and a.mode=='policy_refusal' and not a.citations
        with tempfile.TemporaryDirectory() as t:m.write_cost_log(Path(t)/'cost.csv',q,a)
with tempfile.TemporaryDirectory() as t:
    root=Path(t);(root/'results').mkdir();p=root/'results/existing_results.csv';p.write_text('preserve me')
    with patch.object(e,'ROOT',root), patch.object(e,'load_notes',return_value=chunks),patch.object(e,'load_local_env'):
        try:e.run(ROOT/'evals/diagnostic_questions.csv','existing')
        except FileExistsError:pass
        else:raise AssertionError('Existing results must be protected')
        assert p.read_text()=='preserve me'
        try:e.run(ROOT/'evals/diagnostic_questions.csv','../unsafe')
        except ValueError:pass
        else:raise AssertionError('Unsafe labels must be rejected')
print('Evaluation integrity and credential refusal checks passed.')
