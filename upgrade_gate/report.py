"""Portable, self-contained Markdown and HTML evidence reports."""
from __future__ import annotations

import base64
import json
import mimetypes
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from .schema import read_jsonl

METHOD = ('Each task contributes one paired observation after majority voting over scored repeats; ties fail, '
          'null scores are excluded, and tasks missing either side are dropped. Exact two-sided McNemar tests '
          'use discordant pairs. Pointwise percentile bootstrap intervals resample paired tasks (10,000 draws, '
          'seed 0). Holm adjustment controls familywise error across all eligible slices (at least 10 pairs), '
          'including overlapping slices. Noise floor is the fraction of task/candidate groups with at least '
          'two scored repeats that disagree. This is a fixed-horizon decision; repeated peeking at these '
          'intervals is not valid sequential inference. The separate sequential_test uses mixture betting '
          'e-processes. Inconclusive sample-size estimates are approximate, not stopping guarantees. '
          'Regressed cases are majority-vote disagreements; confirmed exports additionally require supporting '
          'slice or overall statistical evidence. Cost includes model and judge charges; judge cost is a component, '
          'not an extra amount to add. Missing/error calls can bias the scored population; inspect exclusion counts. '
          'A GO clears the drop margin and the tested slices; it does not prove that every subpopulation is safe.')


def _text(value):
    return json.dumps(value,ensure_ascii=False,indent=2) if not isinstance(value,str) else value


def _cell(value):
    return str(value).replace('|','\\|').replace('\n',' ')


def _fence(value):
    value = _text(value)
    fence = '`' * max(3, max((len(s) for s in __import__('re').findall(r'`+',value)),default=0)+1)
    return fence+'\n'+value+'\n'+fence


def _image(path, root):
    repo = Path(__file__).resolve().parents[1]
    for candidate in [root/path, repo/path]:
        candidate = candidate.resolve()
        if not any(candidate == allowed or allowed in candidate.parents for allowed in [root.resolve(),repo]):
            continue
        mime = mimetypes.guess_type(str(candidate))[0]
        if candidate.is_file() and mime in ['image/png','image/jpeg','image/webp','image/gif','image/svg+xml']:
            return 'data:%s;base64,%s' % (mime,base64.b64encode(candidate.read_bytes()).decode())
    return None


def write_report(run_dir: str) -> list:
    """Read gate.json and run artifacts; write report.md and standalone report.html."""
    root = Path(run_dir)
    gate = json.loads((root/'gate.json').read_text(encoding='utf-8'))
    run = json.loads((root/'run.json').read_text(encoding='utf-8'))
    tasks = {t['id']:t for t in read_jsonl(str(root/'tasks.jsonl'))}
    slices = sorted(gate['slices'],key=lambda s:s['delta'])
    level = 100 * (1-gate['thresholds']['alpha'])
    cases = []
    for regression in gate['regressions'][:10]:
        task = tasks[regression['task_id']]
        cases.append(dict(regression, prompt=task['prompt'],reference_text=_text(task['reference']),
                          images=[image for image in [_image(path,root) for path in task.get('attachments',[])] if image]))
    chart_rows = [gate['overall']]+slices
    extent = max(.05,max(abs(row[key]) for row in chart_rows for key in ['ci_low','ci_high'])*1.15)
    def x(value):
        return 245+(value+extent)/(2*extent)*500
    env = Environment(loader=FileSystemLoader(str(Path(__file__).parent/'templates')),autoescape=select_autoescape(['html']))
    env.filters['pts'] = lambda value: '%+.1f' % (value*100)
    env.filters['usd'] = lambda value: '$%.4f' % value
    env.filters['pvalue'] = lambda value: '%.4g' % value
    html = env.get_template('report.html').render(gate=gate,run=run,slices=slices,cases=cases,
                 method=METHOD,level=level,rows=chart_rows,x=x,extent=extent,chart_height=65+len(chart_rows)*34)
    overall, cost = gate['overall'],gate['cost']
    md = ['# %s — Upgrade Gate' % gate['decision'].upper(), '',gate['reasons'][0],'',
          '> '+run.get('notes',''),'', '## Headline numbers','',
          '- %d paired tasks; %d unpaired tasks; %d null score rows.' % (overall['n'],overall.get('unpaired_tasks',0),overall.get('api_error_rows',0)),
          '- Overall change: %+.1f pts (%g%% CI %+.1f to %+.1f).' % (overall['delta']*100,level,overall['ci_low']*100,overall['ci_high']*100),
          '- Pass rates: %.1f%% → %.1f%%; repeat noise floor %.1f%%.' % (overall['base_rate']*100,overall['cand_rate']*100,overall.get('noise_floor',0)*100),'',
          '## Slices — worst first','', '| Slice | n | Delta (pts) | CI (pts) | Holm p | Verdict |', '|---|---:|---:|---|---:|---|']
    for row in slices:
        md.append('| %s | %d | %+.1f | %+.1f to %+.1f | %.4g | %s |' % (_cell(row['slice']),row['n'],row['delta']*100,row['ci_low']*100,row['ci_high']*100,row['p_adjusted'],row['verdict']))
    md += ['', 'The HTML companion includes an inline SVG confidence-interval forest chart.', '', '## Cost comparison','',
           '| Candidate | Model + judge USD | Input tokens | Output tokens |', '|---|---:|---:|---:|']
    for name,key in [(gate['baseline'],'base_usd'),(gate['candidate'],'cand_usd')]:
        usage = cost.get('usage',{}).get(name,{})
        md.append('| %s | %.6f | %d | %d |' % (_cell(name),cost[key],usage.get('input_tokens',0),usage.get('output_tokens',0)))
    md += ['', 'Combined judging component: $%.6f.' % cost['judge_usd'], '', '## Top regressions','']
    if not cases:
        md.append('No paired majority regressions.')
    for case in cases:
        md += ['### '+_cell(case['task_id'])+' · '+_cell(case['category'])+' · '+_cell(case['lang']), '',
               'Prompt:',_fence(case['prompt']),'','Reference:',_fence(case['reference_text']),'',
               'Old answer:',_fence(case['base_text']),'','New answer:',_fence(case['cand_text']),'']
    md += ['## Method notes','',METHOD,'', 'Configured drop limit: %.1f pts; alpha: %g; minimum paired tasks: %d.' % (gate['thresholds']['max_drop']*100,gate['thresholds']['alpha'],gate['thresholds']['min_n']),'']
    paths = [root/'report.md',root/'report.html']
    paths[0].write_text('\n'.join(md),encoding='utf-8')
    paths[1].write_text(html,encoding='utf-8')
    return [str(p) for p in paths]
