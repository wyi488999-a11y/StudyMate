"""Run transparent RAG and keyword-baseline evaluation on a CSV question set."""
from __future__ import annotations
import csv
import sys
import argparse
import hashlib
import json
import re
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.study_mate import answer_question, citation_label, keyword_baseline, load_local_env, load_notes, write_cost_log


def score(answer, row):
    expected_stem = Path(row['expected_source']).stem
    cited = any(Path(chunk.source).stem == expected_stem for chunk in answer.citations)
    correct = row['expected_anchor'].lower() in answer.answer.lower()
    return correct and cited, correct, cited


def run(question_file: Path, label: str, hosted: bool = False, overwrite: bool = False):
    if not re.fullmatch(r"[A-Za-z0-9_-]+", label):
        raise ValueError('Use only letters, numbers, underscores and hyphens in --label.')
    load_local_env(ROOT)
    if hosted and not (os.getenv('OPENAI_API_KEY') or os.getenv('OPENROUTER_API_KEY')):
        raise ValueError('Hosted evaluation requires an API key.')
    (ROOT / 'results').mkdir(exist_ok=True)
    chunks = load_notes(ROOT / 'data' / 'public_pdfs')
    rows = list(csv.DictReader(question_file.open(encoding='utf-8')))
    if any(row['question'].startswith('REPLACE') for row in rows):
        raise ValueError('Blind-question template is not an evaluation dataset. Replace every placeholder first.')
    output = ROOT / 'results' / f'{label}_results.csv'
    cost_log = ROOT / 'results' / f'{label}_cost_log.csv'
    manifest = ROOT / 'results' / f'{label}_manifest.json'
    if not overwrite and any(p.exists() for p in (output, cost_log, manifest)):
        raise FileExistsError('Choose a new --label or explicitly use --overwrite.')
    files = [question_file, ROOT / 'src/study_mate.py', Path(__file__)] + sorted((ROOT / 'data/public_pdfs').glob('*.pdf'))
    manifest.write_text(json.dumps({
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'started', 'hosted': hosted, 'threshold': 0.12, 'top_k': 3,
        'question_count': len(rows),
        'sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    }, indent=2))
    if cost_log.exists():
        cost_log.unlink()
    with output.open('w', newline='', encoding='utf-8') as file:
        fields = ['id', 'set', 'system', 'question', 'answer', 'citations', 'score', 'refused', 'correct', 'citation_correct', 'correct_and_cited']
        writer = csv.DictWriter(file, fieldnames=fields); writer.writeheader()
        summary = {'rag': 0, 'hosted_rag': 0, 'keyword': 0, 'total': len(rows)}
        for row in rows:
            rag_name = 'hosted_rag' if hosted else 'rag'
            for system, answer in [(rag_name, answer_question(row['question'], chunks, use_llm=hosted)), ('keyword', keyword_baseline(row['question'], chunks))]:
                both, correct, cited = score(answer, row)
                summary[system] += both
                writer.writerow({'id': row['id'], 'set': row['set'], 'system': system, 'question': row['question'], 'answer': answer.answer, 'citations': citation_label(answer), 'score': f'{answer.score:.3f}', 'refused': answer.refused, 'correct': correct, 'citation_correct': cited, 'correct_and_cited': both})
                if system == rag_name: write_cost_log(cost_log, row['question'], answer)
    meta = json.loads(manifest.read_text()); meta['status'] = 'complete'
    manifest.write_text(json.dumps(meta, indent=2))
    active = 'hosted_rag' if hosted else 'rag'
    print(f'{label}: {active} {summary[active]}/{summary["total"]}; keyword baseline {summary["keyword"]}/{summary["total"]}. See {output.name}.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--questions', default='diagnostic_questions.csv', help='CSV file inside evals/')
    parser.add_argument('--label', default='diagnostic', help='Prefix for the results CSV')
    parser.add_argument('--hosted', action='store_true', help='Use configured hosted embeddings and LLM')
    parser.add_argument('--overwrite', action='store_true', help='Explicitly replace existing outputs for this label')
    args = parser.parse_args()
    run(ROOT / 'evals' / args.questions, args.label, hosted=args.hosted, overwrite=args.overwrite)
