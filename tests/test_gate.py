from __future__ import annotations
import json
import shutil
from pathlib import Path

import pytest
from upgrade_gate.gate import evaluate_run
from upgrade_gate.schema import read_jsonl, write_jsonl

FIXTURE = Path(__file__).parent/'fixtures'/'run_demo'


def copy_run(tmp_path):
    for name in ['run.json','tasks.jsonl','responses.jsonl','scores.jsonl']:
        shutil.copy(FIXTURE/name,tmp_path/name)
    return tmp_path


def test_fixture_no_go(tmp_path):
    root = copy_run(tmp_path)
    result = evaluate_run(str(root),'spark-1.2','spark-1.3')
    assert result['decision'] == 'no-go'
    assert result['overall']['delta'] == pytest.approx(8/300)
    assert result['overall']['noise_floor'] > 0
    assert any(s['slice']=='category=doc-image' and s['verdict']=='regression' for s in result['slices'])
    assert next(s for s in result['slices'] if s['slice']=='lang=hi')['delta'] == pytest.approx(-.06)
    assert len(result['regressions']) == 10
    assert all(r['evidence']['confirmed'] for r in result['regressions'])
    assert json.loads((root/'gate.json').read_text()) == result


def test_no_regression_go_and_judge_cost(tmp_path):
    root = copy_run(tmp_path)
    scores = list(read_jsonl(str(root/'scores.jsonl')))
    for row in scores:
        row['passed'] = True
        row['cost_usd'] = .001
    write_jsonl(str(root/'scores.jsonl'),scores)
    result = evaluate_run(str(root),'spark-1.2','spark-1.3')
    assert result['decision'] == 'go'
    assert result['regressions'] == []
    assert result['cost']['judge_usd'] == pytest.approx(1.8)
    assert result['cost']['base_usd'] == pytest.approx(result['cost']['model_usd']['spark-1.2']+.9)


def test_low_n_empty_and_uncertain(tmp_path):
    root = copy_run(tmp_path)
    write_jsonl(str(root/'scores.jsonl'),[])
    result = evaluate_run(str(root),'spark-1.2','spark-1.3')
    assert result['decision']=='inconclusive'
    assert '30 more' in result['reasons'][0]
    assert result['overall']['ci_low']==-1
    with pytest.raises(ValueError):
        evaluate_run(str(root),'same','same')


def test_horizon_and_custom_alpha(tmp_path):
    root = copy_run(tmp_path)
    result = evaluate_run(str(root),'spark-1.2','spark-1.3',alpha=.001)
    assert not any(s['verdict']=='regression' for s in result['slices'])
    assert result['thresholds']['confidence_level']==.999
    assert result['decision']=='inconclusive'
    assert 'more independent tasks' in result['reasons'][0]


def test_fixture_matches_shared_shapes_and_live_scorers():
    from upgrade_gate.schema import RunInfo, Task, ResponseRecord, ScoreRecord
    from upgrade_gate.scorers import score_text
    RunInfo(**json.loads((FIXTURE/'run.json').read_text()))
    tasks = {row['id']:row for row in read_jsonl(str(FIXTURE/'tasks.jsonl'))}
    scores = {(row['task_id'],row['candidate'],row['repeat']):row for row in read_jsonl(str(FIXTURE/'scores.jsonl'))}
    for task in tasks.values():
        Task(**task)
    for response in read_jsonl(str(FIXTURE/'responses.jsonl')):
        ResponseRecord(**response)
        score = scores[(response['task_id'],response['candidate'],response['repeat'])]
        ScoreRecord(**score)
        assert score_text(tasks[response['task_id']],response['text'])[0] == score['passed']


def test_reverse_response_order_and_authoritative_scores(tmp_path):
    root = copy_run(tmp_path)
    responses = list(read_jsonl(str(root/'responses.jsonl')))
    write_jsonl(str(root/'responses.jsonl'),reversed(responses))
    gate = evaluate_run(str(root),'spark-1.2','spark-1.3')
    case = next(row for row in gate['regressions'] if row['task_id']=='demo-000')
    assert json.loads(case['base_text'])['total_inr']==1200
    assert json.loads(case['cand_text'])['total_inr']==1300
    assert case['evidence']['cand_passes']==0
