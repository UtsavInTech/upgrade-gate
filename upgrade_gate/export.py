"""Turn statistically supported majority regressions into portable checks."""
from __future__ import annotations

import json
from pathlib import Path
import yaml
from .schema import read_jsonl


JS_EQUAL = '''const canonical = x => Array.isArray(x) ? x.map(canonical) :
  x !== null && typeof x === 'object' ? Object.fromEntries(Object.keys(x).sort().map(k => [k, canonical(x[k])])) : x;
const equal = (a,b) => JSON.stringify(canonical(a)) === JSON.stringify(canonical(b));'''


def _assertions(task):
    reference = task['reference']
    if task.get('scorer',{}).get('type') == 'contains':
        return [{'type':'contains','value':str(reference)}]
    if isinstance(reference,(dict,list,int,float,bool)) or reference is None:
        expected = json.dumps(reference,ensure_ascii=True)
        expression = 'Object.keys(expected).every(k => Object.prototype.hasOwnProperty.call(actual,k) && equal(actual[k], expected[k]))' if isinstance(reference,dict) else 'equal(actual, expected)'
        script = JS_EQUAL+'\nconst expected = '+expected+';\ntry { const actual = JSON.parse(output); return '+expression+'; } catch { return false; }'
        return [{'type':'is-json'},{'type':'javascript','value':script}]
    return [{'type':'equals','value':str(reference).strip()}]


PYTEST_SOURCE = '''"""Generated regression checks; synthetic sources remain synthetic.

Supply a call_model(prompt) fixture in conftest.py to evaluate a model. Without
that fixture, cases skip. Image-aware fixtures can inspect
request.node.callspec.params['case']['attachments'] to send image inputs.
Paths are repo-relative; preserve the original task assets when moving this file.
These checks implement deterministic reference assertions, not model judges.
"""
from __future__ import annotations
import json
import pytest

CASES = json.loads(__CASES__)


def _assert_reference(output, case):
    reference = case['reference']
    assert isinstance(output, str), 'call_model must return response text'
    if case.get('scorer', {}).get('type') == 'contains':
        assert str(reference) in output
    elif isinstance(reference, (dict, list, int, float, bool)) or reference is None:
        actual = json.loads(output)
        if isinstance(reference, dict):
            assert isinstance(actual, dict)
            assert all(key in actual and actual[key] == value for key, value in reference.items())
        else:
            assert actual == reference
    else:
        assert output.strip() == str(reference).strip()


@pytest.mark.parametrize('case', CASES, ids=[case['task_id'] for case in CASES])
def test_regression(case, request):
    try:
        call_model = request.getfixturevalue('call_model')
    except pytest.FixtureLookupError as exc:
        if exc.argname != 'call_model':
            raise
        pytest.skip('Provide a call_model(prompt) fixture to run exported regression checks')
    _assert_reference(call_model(case['prompt']), case)
'''


def export_regressions(run_dir: str) -> list:
    """Export confirmed regressions; return YAML, pytest, and raw JSONL paths.

    Confirmed means a majority regression with supporting statistical evidence
    recorded by the gate. Legacy gate rows without a confirmed flag are included.
    Promptfoo users supply their provider via --providers; image-aware templates
    must send vars.attachments. Generated pytest cases use the supplied fixture.
    """
    root = Path(run_dir)
    gate = json.loads((root/'gate.json').read_text(encoding='utf-8'))
    tasks = {t['id']:t for t in read_jsonl(str(root/'tasks.jsonl'))}
    cases, tests = [], []
    for row in gate['regressions']:
        if not row.get('evidence',{}).get('confirmed',True):
            continue
        task = tasks[row['task_id']]
        case = dict(row,prompt=task['prompt'],scorer=task.get('scorer',{}),attachments=task.get('attachments',[]))
        cases.append(case)
        tests.append(dict(description='%s / %s / %s' % (row['task_id'],row['category'],row['lang']),
                          vars={'prompt':task['prompt'],'attachments':task.get('attachments',[])},
                          assert_=_assertions(task)))
    for test in tests:
        test['assert'] = test.pop('assert_')
    output = root/'exports'
    output.mkdir(exist_ok=True)
    yaml_path, test_path, raw_path = [output/name for name in ['promptfoo.yaml','test_regressions.py','regressions.jsonl']]
    config = dict(description='Upgrade Gate confirmed regressions: '+gate['run_id'],prompts=['{{prompt}}'],tests=tests)
    yaml_path.write_text('# Supply a provider: promptfoo eval -c promptfoo.yaml --providers <provider-id>\n# Image tasks: configure a multimodal prompt template using vars.attachments.\n'+yaml.safe_dump(config,allow_unicode=True,sort_keys=False),encoding='utf-8')
    test_path.write_text(PYTEST_SOURCE.replace('__CASES__',repr(json.dumps(cases,ensure_ascii=True))),encoding='utf-8')
    raw_path.write_text(''.join(json.dumps(c,ensure_ascii=False)+'\n' for c in cases),encoding='utf-8')
    return [str(yaml_path),str(test_path),str(raw_path)]
