from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

import yaml
from upgrade_gate.gate import evaluate_run
from upgrade_gate.export import export_regressions


def test_exports_parse_import_skip_and_assert(tmp_path):
    fixture = Path(__file__).parent/'fixtures'/'run_demo'
    for name in ['run.json','tasks.jsonl','scores.jsonl','responses.jsonl']:
        shutil.copy(fixture/name,tmp_path/name)
    evaluate_run(str(tmp_path),'spark-1.2','spark-1.3')
    paths = export_regressions(str(tmp_path))
    assert len(paths)==3
    config = yaml.safe_load(Path(paths[0]).read_text())
    assert len(config['tests'])==10
    assert config['tests'][0]['assert'][0]['type']=='is-json'
    spec = importlib.util.spec_from_file_location('generated',paths[1])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for case in module.CASES:
        module._assert_reference(json.dumps(case['reference']),case)
    result = subprocess.run([sys.executable,'-m','pytest','-q',paths[1]],capture_output=True,text=True)
    assert result.returncode==0, result.stdout+result.stderr
    assert '10 skipped' in result.stdout
    assert len(Path(paths[2]).read_text().splitlines())==10


def test_unconfirmed_and_empty_exports(tmp_path):
    (tmp_path/'gate.json').write_text(json.dumps({'run_id':'empty','regressions':[{'task_id':'x','evidence':{'confirmed':False}}]}))
    (tmp_path/'tasks.jsonl').write_text('')
    paths = export_regressions(str(tmp_path))
    assert yaml.safe_load(Path(paths[0]).read_text())['tests']==[]
    assert Path(paths[2]).read_text()==''


def test_exported_tests_use_supplied_fixture(tmp_path):
    # A structured reference must compare fields, not depend on JSON key order.
    reference = {'total':42,'invoice_id':'example'}
    (tmp_path/'gate.json').write_text(json.dumps({'run_id':'structured','regressions':[dict(task_id='one',category='extraction',lang='en',reference=reference,evidence={'confirmed':True})]}))
    (tmp_path/'tasks.jsonl').write_text(json.dumps(dict(id='one',prompt='Extract invoice',reference=reference,scorer={'type':'json_fields'},attachments=[]))+'\n')
    paths = export_regressions(str(tmp_path))
    test_dir = Path(paths[1]).parent
    (test_dir/'conftest.py').write_text('import pytest\n@pytest.fixture\ndef call_model():\n    return lambda prompt: \'{"invoice_id":"example","total":42,"extra":"allowed"}\'\n')
    result = subprocess.run([sys.executable,'-m','pytest','-q',paths[1]],capture_output=True,text=True)
    assert result.returncode==0, result.stdout+result.stderr
    assert '1 passed' in result.stdout
    # The same generated test must reject a real field regression.
    (test_dir/'conftest.py').write_text('import pytest\n@pytest.fixture\ndef call_model():\n    return lambda prompt: \'{"invoice_id":"example","total":43}\'\n')
    result = subprocess.run([sys.executable,'-m','pytest','-q',paths[1]],capture_output=True,text=True)
    assert result.returncode==1
    assert '1 failed' in result.stdout
