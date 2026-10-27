from __future__ import annotations
import json
import shutil
from pathlib import Path

import pytest
from upgrade_gate.gate import evaluate_run
from upgrade_gate.report import build_presentation, write_report
from upgrade_gate.schema import read_jsonl, write_jsonl


def copy_demo(root):
    source=Path(__file__).parent/'fixtures'/'run_demo'
    for name in ['run.json','tasks.jsonl','scores.jsonl','responses.jsonl']:
        shutil.copy(source/name,root/name)


def test_report_portable_and_escaped(tmp_path):
    copy_demo(tmp_path)
    rows=list(read_jsonl(str(tmp_path/'responses.jsonl')))
    for row in rows:
        if row['task_id']=='demo-000' and row['candidate']=='spark-1.3':
            row['text']='<script>alert(1)</script>'
    write_jsonl(str(tmp_path/'responses.jsonl'),rows)
    evaluate_run(str(tmp_path),'spark-1.2','spark-1.3')
    paths=write_report(str(tmp_path))
    assert len(paths)==2 and all(Path(p).stat().st_size>100 for p in paths)
    html=(tmp_path/'report.html').read_text()
    assert 'NO-GO' in html and '<svg' in html and 'data:image/svg+xml;base64,' in html
    assert '<script>' not in html and '&lt;script&gt;' in html
    assert '<link' not in html and 'src="http' not in html
    assert 'Holm' in html and 'McNemar' in html
    lines=(tmp_path/'report.md').read_text().splitlines()
    assert 'Top regressions:' in lines[2] and 'Cost of this run:' in lines[3]
    assert 'demo data' in lines[4]
    assert 'Methods in plain words' in html and 'Strict requested format' in html
    assert 'Unavailable' in html


def test_report_no_regressions_and_custom_confidence(tmp_path):
    copy_demo(tmp_path)
    scores=list(read_jsonl(str(tmp_path/'scores.jsonl')))
    for row in scores:row['passed']=True
    write_jsonl(str(tmp_path/'scores.jsonl'),scores)
    evaluate_run(str(tmp_path),'spark-1.2','spark-1.3',alpha=.1)
    write_report(str(tmp_path))
    html=(tmp_path/'report.html').read_text()
    assert '90%' in html and 'No paired majority regressions.' in html
    assert 'zero baseline cost' in html


def test_dual_metrics_rescore_and_key_alignment(tmp_path):
    copy_demo(tmp_path)
    scores=list(read_jsonl(str(tmp_path/'scores.jsonl')))
    old=[dict(row) for row in scores]
    for row in scores:row['strict_passed']=row['passed']
    # Old and new files intentionally use different order. Only the scorer changes.
    for row in old:
        if row['task_id']=='demo-100' and row['candidate']=='spark-1.2':row['passed']=False
    for row in scores:
        if row['task_id']=='demo-100':row['passed']=True
    write_jsonl(str(tmp_path/'scores.jsonl'),scores)
    write_jsonl(str(tmp_path/'scores.before-rescore.jsonl'),reversed(old))
    data=build_presentation(str(tmp_path));view=data['comparisons'][0]
    assert view['strict']['available']
    assert view['rescore']['changed_rows']>0
    assert all(example['task_id']=='demo-100' for example in view['rescore']['examples'])
    assert view['rescore']['before']['n']==view['rescore']['after']['n']
    assert view['content']['overall']['delta']!=view['strict']['overall']['delta']
    assert len(view['content']['cells'])>0
    assert all(cell['p_adjusted'] is None or 0<=cell['p_adjusted']<=1 for cell in view['content']['cells'])


def test_multiple_candidates_and_cost_normalization(tmp_path):
    copy_demo(tmp_path)
    run=json.loads((tmp_path/'run.json').read_text())
    run['candidates'].append(dict(name='third@high',model_id='muse-spark-1.3',params={}))
    (tmp_path/'run.json').write_text(json.dumps(run))
    for name in ['scores.jsonl','responses.jsonl']:
        rows=list(read_jsonl(str(tmp_path/name)))
        rows += [dict(row,candidate='third@high') for row in rows if row['candidate']=='spark-1.3']
        write_jsonl(str(tmp_path/name),rows)
    data=build_presentation(str(tmp_path))
    assert len(data['comparisons'])==2
    cost=data['comparisons'][1]['costs'][1]
    assert cost['per_1000_tasks']==pytest.approx(cost['total_usd']/cost['calls']*1000)
    assert cost['estimated_per_1000']['contributor']<cost['estimated_per_1000']['standard']
    assert not data['comparisons'][0]['strict']['available']
    write_report(str(tmp_path))
    assert 'third@high' in (tmp_path/'report.html').read_text()
