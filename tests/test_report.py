from __future__ import annotations
import json
import shutil
from pathlib import Path
from upgrade_gate.gate import evaluate_run
from upgrade_gate.report import write_report


def test_report_portable_and_escaped(tmp_path):
    source = Path(__file__).parent/'fixtures'/'run_demo'
    for name in ['run.json','tasks.jsonl','scores.jsonl','responses.jsonl']:
        shutil.copy(source/name,tmp_path/name)
    gate = evaluate_run(str(tmp_path),'spark-1.2','spark-1.3')
    gate['regressions'][0]['cand_text'] = '<script>alert(1)</script>'
    (tmp_path/'gate.json').write_text(json.dumps(gate))
    paths = write_report(str(tmp_path))
    assert len(paths)==2 and all(Path(p).stat().st_size>100 for p in paths)
    html = (tmp_path/'report.html').read_text()
    assert 'NO-GO' in html and '<svg' in html and 'data:image/svg+xml;base64,' in html
    assert '<script>' not in html and '&lt;script&gt;' in html
    assert '<link' not in html and 'src="http' not in html
    assert 'Holm' in html and 'McNemar' in html
    assert 'category=doc-image' in (tmp_path/'report.md').read_text()


def test_report_no_regressions_and_custom_confidence(tmp_path):
    source = Path(__file__).parent/'fixtures'/'run_demo'
    for name in ['run.json','tasks.jsonl','scores.jsonl','responses.jsonl']:
        shutil.copy(source/name,tmp_path/name)
    gate = evaluate_run(str(tmp_path),'spark-1.2','spark-1.3',alpha=.1)
    gate['regressions'] = []
    gate['cost']['base_usd'] = 0
    gate['cost']['delta_pct'] = None
    (tmp_path/'gate.json').write_text(json.dumps(gate))
    write_report(str(tmp_path))
    html = (tmp_path/'report.html').read_text()
    assert '90.0%' in html
    assert 'No paired majority regressions.' in html
    assert 'zero baseline cost' in html
