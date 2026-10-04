"""Recompute historical metrics and run separate offline development audits. No API calls."""
import csv
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.study_mate import load_notes, answer_question, citation_label
from scripts.run_evaluation import score

def read(path):
    with path.open(encoding='utf-8') as f:
        return list(csv.DictReader(f))

def write(name, rows):
    with (ROOT / 'results' / name).open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

def main():
    summaries = []
    for label in ('hosted_diagnostic', 'hosted_blind'):
        rows = read(ROOT / 'results' / f'{label}_results.csv')
        for system in ('hosted_rag', 'keyword'):
            selected = [r for r in rows if r['system'] == system]
            refusals = sum(r['refused'] == 'True' for r in selected)
            summaries.append(dict(set=label.removeprefix('hosted_'), system=system,
                total=len(selected), anchor_and_source_matches=sum(r['correct_and_cited']=='True' for r in selected),
                source_presence=sum(r['citation_correct']=='True' for r in selected), refusals=refusals,
                refusal_rate=refusals/len(selected), counterfactual_error_among_refused='N/A (not recorded)'))
    write('audit_historical_summary.csv', summaries)
    chunks = load_notes(ROOT / 'data/public_pdfs')
    diagnostic = read(ROOT / 'evals/diagnostic_questions.csv')
    forced = {r['id']: answer_question(r['question'], chunks, threshold=-1) for r in diagnostic}
    sweep = []
    for threshold in (0, .08, .12, .2, .3, .4):
        answers = [(r, answer_question(r['question'], chunks, threshold=threshold)) for r in diagnostic]
        blocked = [r for r,a in answers if a.refused]
        evaluable = [r for r in blocked if not forced[r['id']].refused]
        errors = sum(not score(forced[r['id']], r)[0] for r in evaluable)
        sweep.append(dict(threshold=threshold, total=len(answers), matches=sum(score(a,r)[0] for r,a in answers),
            refusals=len(blocked), refusal_rate=len(blocked)/len(answers),
            counterfactual_proxy_errors_among_refused=errors,
            counterfactual_answers_available=len(evaluable),
            counterfactual_unavailable=len(blocked)-len(evaluable),
            counterfactual_proxy_error_rate=errors/len(evaluable) if evaluable else 'N/A'))
    write('audit_offline_thresholds.csv', sweep)
    safety = read(ROOT / 'evals/developer_safety_questions.csv')
    results=[]
    for r in safety:
        a=answer_question(r['question'], chunks)
        results.append(dict(id=r['id'], question=r['question'], expected_refusal=r['expected_refusal'],
            refused=a.refused, pass_check=a.refused==(r['expected_refusal']=='True'),
            score=round(a.score,5),answer=a.answer,citations=citation_label(a)))
    write('audit_offline_safety.csv',results)
    costs=[]
    for label in ('hosted_diagnostic','hosted_blind'):
        rows=read(ROOT/'results'/f'{label}_cost_log.csv')
        dollars=sum(float(r['actual_cost'].replace('$','')) for r in rows)
        costs.append(dict(set=label,queries=len(rows),calculated_usd=round(dollars,8),mean_usd=dollars/len(rows),
            embedding_tokens=sum(int(r['embedding_tokens']) for r in rows),
            input_tokens=sum(int(r['input_tokens_est']) for r in rows),output_tokens=sum(int(r['output_tokens_est']) for r in rows)))
    write('audit_cost_summary.csv',costs)
    print(json.dumps({'historical':summaries,'diagnostic_threshold_sweep':sweep,'developer_safety_passed':sum(r['pass_check'] for r in results),'developer_safety_total':len(results),'costs':costs},indent=2))
if __name__=='__main__':main()
