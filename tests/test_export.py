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
