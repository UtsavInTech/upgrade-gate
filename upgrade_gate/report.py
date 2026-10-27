"""Saved-run analysis and portable reports. This module never calls a model.

The dashboard sync script uses build_presentation(), so HTML, Markdown and the
UI share the same numbers. Correctness and format are independent score views;
missing strict_passed values stay unscored rather than inheriting passed.
"""
from __future__ import annotations

import argparse
import base64
from collections import Counter, defaultdict
import html
import json
import mimetypes
from pathlib import Path
import re

from .schema import read_jsonl
from .stats import by_slice, compare, flip_rate, holm, majority_pass, paired_bootstrap_ci, pair_up

METHODS = [
    ('Paired design', 'We ask both versions the same questions. We compare each answer with its partner, so a harder task affects both sides. The unit of evidence is a task, not an API call.'),
    ('Repeats', 'We repeat tasks to measure inconsistency. Each task gets one majority vote per model. Ties fail. Null scores are excluded; a task with no scored repeat on either side cannot be paired.'),
    ('McNemar', 'This exact test counts tasks only one version gets right. Its p-value describes how surprising that imbalance would be if neither version had an advantage. A small p-value does not prove the scoring rule is right.'),
    ('Bootstrap', 'We draw 10,000 new samples of whole task pairs, with replacement and seed 0, to estimate an interval for the pass-rate change. The intervals are pointwise, not guarantees for every slice at once. A zero-width interval at the ceiling reflects this observed sample; it does not prove zero deployment risk.'),
    ('Holm correction', 'Trying many slices creates more chances for a false alarm. Holm adjusts their p-values as a family. The release gate tests category, language and modality slices with at least 10 pairs. Intersection heatmap cells form a separate, exploratory family; they do not add release vetoes.'),
    ('Noise floor', 'We show how often scored repeats disagree for the same task and model, among groups with at least two scored repeats. This is a repeat disagreement rate, not a threshold that the quality delta must exceed. The gate uses confidence intervals and adjusted tests.'),
    ('Correctness and strict format', 'Content passed means the answer is correct under the saved scorer, including accepted Hindi spellings. Strict passed additionally requires the requested format. An older run without strict_passed shows format as unavailable. Before/after rescoring reuses the same saved answers; it measures a scoring change, not a model change.'),
    ('Decision and cost', 'Below the minimum paired sample the result is inconclusive. NO-GO follows a significantly regressing gate slice or an overall upper interval below the allowed drop. GO requires no such slice and a lower interval above that limit. Otherwise collect more evidence. These are fixed-horizon tests; use the separate sequential rule for repeated peeking. Run cost includes recorded model and judge charges; cost per 1,000 tasks normalizes to one response per task. Serving-mode repricing is an estimate at saved token usage, not a measured quality comparison.'),
]
METHOD = ' '.join(title+': '+body for title,body in METHODS)


def _text(value):
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2)


def _cell(value):
    return html.escape(str(value)).replace('|', '\\|').replace('\n', ' ')


def _fence(value):
    value = _text(value)
    fence = '`' * max(3, max((len(s) for s in re.findall(r'`+', value)), default=0)+1)
    return fence+'\n'+value+'\n'+fence


def _image(path, root):
    repo = Path(__file__).resolve().parents[1]
    for candidate in [root/path, repo/path]:
        candidate = candidate.resolve()
        if not any(candidate == allowed or allowed in candidate.parents for allowed in [root.resolve(), repo]):
            continue
        mime = mimetypes.guess_type(str(candidate))[0]
        if candidate.is_file() and mime in ['image/png', 'image/jpeg', 'image/webp', 'image/gif', 'image/svg+xml']:
            return 'data:%s;base64,%s' % (mime, base64.b64encode(candidate.read_bytes()).decode())
    return None


def _read(root, name):
    return list(read_jsonl(str(root/name))) if (root/name).exists() else []


def _summary(scores, tasks, baseline, candidate, field, thresholds):
    selected = [dict(row, passed=row.get(field)) for row in scores if row['candidate'] in [baseline, candidate]]
    majority = majority_pass(selected)
    pairs = pair_up(majority, baseline, candidate)
    overall = compare(pairs, 'overall')
    alpha = thresholds['alpha']
    overall['ci_low'], overall['ci_high'] = paired_bootstrap_ci(pairs, alpha=alpha)
    overall['noise_floor'] = flip_rate(selected)
    overall['unpaired_tasks'] = len(tasks)-len(pairs)
    overall['api_error_rows'] = sum(row.get('passed') is None for row in selected)
    slices = by_slice(pairs, tasks)
    task_map = {task['id']: task for task in tasks}
    for row in slices:
        key, value = row['slice'].split('=', 1)
        subset = [p for p in pairs if str(task_map[p[0]].get(key)) == value]
        row['ci_low'], row['ci_high'] = paired_bootstrap_ci(subset, alpha=alpha)
        row['verdict'] = ('regression' if row['delta'] < 0 else 'improvement') if row['p_adjusted'] < alpha else 'inconclusive'
    cells = defaultdict(list)
    for pair in pairs:
        task = task_map[pair[0]]
        cells[(task['category'], task['lang'], task['modality'])].append(pair)
    cell_rows = []
    for (category, lang, modality), members in sorted(cells.items()):
        row = compare(members, '%s / %s / %s' % (category, lang, modality))
        row['ci_low'], row['ci_high'] = paired_bootstrap_ci(members, alpha=alpha)
        row.update(category=category, lang=lang, modality=modality, task_ids=[p[0] for p in members])
        cell_rows.append(row)
    eligible = [row for row in cell_rows if row['n'] >= 10]
    for row, adjusted in zip(eligible, holm([row['p_value'] for row in eligible])):
        row['p_adjusted'] = adjusted
    for row in cell_rows:
        row['verdict'] = ('regression' if row['delta'] < 0 else 'improvement') if row['p_adjusted'] is not None and row['p_adjusted'] < alpha else 'inconclusive'
    bad = sorted([row for row in slices if row['verdict'] == 'regression'], key=lambda r: r['delta'])
    n, margin = len(pairs), thresholds['max_drop']
    if n < thresholds['min_n']:
        decision, reason = 'inconclusive', 'Only %d paired tasks; need %d more to reach the minimum.' % (n, thresholds['min_n']-n)
    elif bad:
        worst = bad[0]
        decision, reason = 'no-go', '%s drops %.1f points while the overall change is %+.1f points. Hold the upgrade for this workflow.' % (worst['slice'].replace('=', ' · '), -worst['delta']*100, overall['delta']*100)
    elif overall['ci_high'] < -margin:
        decision, reason = 'no-go', 'The overall confidence interval lies below the allowed %.1f-point drop. Hold the upgrade.' % (margin*100)
    elif overall['ci_low'] > -margin:
        decision, reason = 'go', 'No tested slice regresses significantly. The overall change is %+.1f points and clears the %.1f-point drop limit on these tasks.' % (overall['delta']*100, margin*100)
    else:
        decision, reason = 'inconclusive', 'The overall interval overlaps the allowed drop. More independent tasks are needed.'
    groups = defaultdict(list)
    for row in selected:
        groups[row['task_id']].append(row)
    regressions = []
    for task_id, base, cand in pairs:
        if not base or cand:
            continue
        task = task_map[task_id]
        supporting = [s['slice'] for s in bad if str(task.get(s['slice'].split('=', 1)[0])) == s['slice'].split('=', 1)[1]]
        votes = {name: [r['passed'] for r in groups[task_id] if r['candidate'] == name and r['passed'] is not None] for name in [baseline, candidate]}
        regressions.append(dict(task_id=task_id, category=task['category'], lang=task['lang'], modality=task['modality'],
            reference=task['reference'], evidence=dict(base_passes=sum(votes[baseline]), base_repeats=len(votes[baseline]),
                cand_passes=sum(votes[candidate]), cand_repeats=len(votes[candidate]),
                failure_consistency=1-sum(votes[candidate])/len(votes[candidate]), supporting_slices=supporting,
                confirmed=bool(n >= thresholds['min_n'] and (supporting or overall['ci_high'] < -margin)))))
    regressions.sort(key=lambda r: (-r['evidence']['failure_consistency'], r['task_id']))
    raw = {}
    for name in [baseline, candidate]:
        values = [r['passed'] for r in selected if r['candidate'] == name and r['passed'] is not None]
        raw[name] = dict(passed=sum(values), scored=len(values), rate=sum(values)/len(values) if values else None)
    return dict(available=bool(pairs), field=field, overall=overall, slices=slices, cells=cell_rows,
                regressions=regressions, raw=raw, decision=decision, reason=reason)


def build_presentation(run_dir: str) -> dict:
    """Compute UI/report views from saved records, for every candidate comparison.

    Does not write gate.json or mutate the inputs. Unknown strict scores are null.
    Before/after headline tests use only tasks paired in both snapshots, ensuring
    that changing sample composition cannot manufacture a rescoring story.
    """
    root = Path(run_dir)
    run = json.loads((root/'run.json').read_text(encoding='utf-8'))
    saved_gate = json.loads((root/'gate.json').read_text(encoding='utf-8')) if (root/'gate.json').exists() else {}
    thresholds = {key: saved_gate.get('thresholds', {}).get(key, default) for key, default in [('alpha', .05), ('max_drop', .02), ('min_n', 30)]}
    tasks, scores, responses = [_read(root, name) for name in ['tasks.jsonl', 'scores.jsonl', 'responses.jsonl']]
    old = _read(root, 'scores.before-rescore.jsonl')
    baseline = run['baseline']
    names = [c['name'] for c in run['candidates']]
    unknown = {row['task_id'] for row in scores}-{task['id'] for task in tasks}
    if unknown:
        raise ValueError('Scored task missing from tasks.jsonl: '+sorted(unknown)[0])
    comparisons = []
    response_map = {(r['task_id'], r['candidate'], r['repeat']): r for r in responses}
    for candidate in [name for name in names if name != baseline]:
        content = _summary(scores, tasks, baseline, candidate, 'passed', thresholds)
        strict = _summary(scores, tasks, baseline, candidate, 'strict_passed', thresholds)
        before_after = None
        if old:
            before_pairs = pair_up(majority_pass(old), baseline, candidate)
            after_pairs = pair_up(majority_pass(scores), baseline, candidate)
            common = {p[0] for p in before_pairs} & {p[0] for p in after_pairs}
            before_view = _summary([r for r in old if r['task_id'] in common], tasks, baseline, candidate, 'passed', thresholds)
            after_view = _summary([r for r in scores if r['task_id'] in common], tasks, baseline, candidate, 'passed', thresholds)
            previous = {(r['task_id'], r['candidate'], r['repeat']): r for r in old}
            changes = []
            for row in scores:
                key = (row['task_id'], row['candidate'], row['repeat'])
                prior = previous.get(key)
                if row['task_id'] in common and row['candidate'] in [baseline, candidate] and prior and prior.get('passed') != row.get('passed'):
                    response = response_map.get(key, {})
                    changes.append(dict(task_id=row['task_id'], candidate=row['candidate'], repeat=row['repeat'],
                        before=prior.get('passed'), after=row.get('passed'), strict=row.get('strict_passed'),
                        detail=row.get('detail', ''), before_detail=prior.get('detail', ''), text=response.get('text')))
            changes.sort(key=lambda r: (not bool(re.search(r'somw|budhw|raviv|सोम|बुध|रवि', r['text'] or '', re.I)), r['task_id'], r['candidate'], r['repeat']))
            before_after = dict(before=before_view['overall'], after=after_view['overall'], changed_rows=len(changes),
                common_tasks=len(common), examples=changes[:12], source_before='scores.before-rescore.jsonl', source_after='scores.jsonl')
        costs = []
        for name in [baseline, candidate]:
            candidate_meta = next((c for c in run['candidates'] if c['name'] == name), {})
            rows = [r for r in responses if r['candidate'] == name]
            model = sum(r.get('cost_usd', 0) or 0 for r in rows)
            judge = sum(r.get('cost_usd', 0) or 0 for r in scores if r['candidate'] == name)
            usage = {key: sum(r.get('usage', {}).get(key, 0) or 0 for r in rows) for key in ['input_tokens', 'output_tokens', 'reasoning_tokens', 'cached_tokens']}
            # Same recorded token usage, two price schedules. Explicitly estimated.
            estimated = {}
            model_id = candidate_meta.get('model_id', '')
            if model_id.startswith('muse-spark-1.'):
                from .pricing import cost
                standard_id = model_id.removesuffix('-contributor')
                for mode, target in [('standard', standard_id), ('contributor', standard_id+'-contributor')]:
                    from .pricing import is_known
                    estimated[mode] = sum(cost(target, r.get('usage', {})) for r in rows)/len(rows)*1000 if rows and is_known(target) else None
            costs.append(dict(candidate=name, model_id=model_id, mode='Contributor' if 'contributor' in model_id else 'Standard' if model_id.startswith('muse-') else 'Recorded',
                calls=len(rows), unique_tasks=len({r['task_id'] for r in rows}), model_usd=model, judge_usd=judge,
                total_usd=model+judge, per_1000_tasks=(model+judge)/len(rows)*1000 if rows else None,
                usage=usage, estimated_per_1000=estimated))
        comparisons.append(dict(baseline=baseline, candidate=candidate, content=content, strict=strict, rescore=before_after, costs=costs))
    return dict(run_id=run['run_id'], synthetic='synthetic-demo' in run.get('packs', []), thresholds=thresholds,
                comparisons=comparisons, total_calls=len(responses), total_run_usd=sum((r.get('cost_usd', 0) or 0) for r in responses+scores),
                notes=run.get('notes', ''), source='Saved local JSON/JSONL records; no model calls', methods=[dict(title=t, body=b) for t,b in METHODS])


def _forest(rows):
    extent = max(.05, max((abs(row[k]) for row in rows for k in ['ci_low', 'ci_high']), default=0)*1.15)
    x = lambda v: 245+(v+extent)/(2*extent)*500
    height = 65+len(rows)*34
    parts = ['<svg class="forest" role="img" aria-label="Paired changes and pointwise confidence intervals" viewBox="0 0 800 %d">' % height,
             '<line x1="%g" x2="%g" y1="10" y2="%d" stroke="currentColor" stroke-dasharray="4 4"/>' % (x(0), x(0), height-30)]
    for i, row in enumerate(rows):
        y = 25+i*34
        parts.append('<text x="0" y="%d" fill="currentColor">%s</text><line x1="%g" x2="%g" y1="%d" y2="%d" stroke="currentColor" stroke-width="2"/><circle cx="%g" cy="%d" r="5" fill="currentColor"/>' % (y+5, html.escape(row['slice']), x(row['ci_low']), x(row['ci_high']), y, y, x(row['delta']), y))
    parts.append('<text x="245" y="%d" fill="currentColor">Worse ← %+.1f pts</text><text x="745" y="%d" text-anchor="end" fill="currentColor">%+.1f pts → Better</text></svg>' % (height-5, -extent*100, height-5, extent*100))
    return ''.join(parts)


def write_report(run_dir: str) -> list:
    """Write Markdown and self-contained HTML, using current saved score views."""
    root = Path(run_dir)
    analysis = build_presentation(run_dir)
    if not analysis['comparisons']:
        raise ValueError('A report needs a baseline and at least one candidate')
    run = json.loads((root/'run.json').read_text(encoding='utf-8'))
    tasks = {t['id']: t for t in _read(root, 'tasks.jsonl')}
    responses = _read(root, 'responses.jsonl')
    scores = _read(root, 'scores.jsonl')
    preferred = json.loads((root/'gate.json').read_text()).get('candidate') if (root/'gate.json').exists() else None
    comparison = next((c for c in analysis['comparisons'] if c['candidate'] == preferred), analysis['comparisons'][0])
    content = comparison['content']
    worst = sorted([s for s in content['slices'] if s['verdict'] == 'regression'], key=lambda s:s['delta'])[:3]
    top = '; '.join('%s %+.1f pts' % (s['slice'], s['delta']*100) for s in worst) or 'None significant after Holm correction.'
    md = ['# %s — Upgrade Gate' % content['decision'].upper(), content['reason'],
          'Top regressions: '+top, 'Cost of this run: $%.4f (%d recorded calls; includes judging).' % (analysis['total_run_usd'], analysis['total_calls']),
          'Data: '+('demo data (synthetic; not measured model results).' if analysis['synthetic'] else 'saved API run '+analysis['run_id']+'.'), '']
    body = ['<header class="banner"><span class="label">Upgrade Gate / %s</span><h1>%s</h1><p class="reason">%s</p><p>Top regressions: %s</p><p>Run cost: $%.4f · %d recorded calls</p><p class="note">%s</p></header>' %
            (html.escape(analysis['run_id']), content['decision'].upper(), html.escape(content['reason']), html.escape(top), analysis['total_run_usd'], analysis['total_calls'], 'Demo data — synthetic, not measured model results.' if analysis['synthetic'] else html.escape(run.get('notes','')))]
    for comparison in analysis['comparisons']:
        baseline, candidate = comparison['baseline'], comparison['candidate']
        heading = baseline+' → '+candidate
        md += ['## '+heading, '']
        body.append('<h2>%s</h2>' % html.escape(heading))
        rescore = comparison['rescore']
        if rescore:
            md += ['### The scorer changed. The answers did not.', '', '| Scoring | Paired tasks | Change (pts) | McNemar p |', '|---|---:|---:|---:|']
            table_rows = []
            for label,key in [('Before · old scorer','before'),('After · content scorer','after')]:
                row = rescore[key]
                md.append('| %s | %d | %+.2f | %.6g |' % (label,row['n'],row['delta']*100,row['p_value']))
                table_rows.append('<tr><td>%s</td><td>%d</td><td>%+.2f pts</td><td>%.6g</td></tr>' % (label,row['n'],row['delta']*100,row['p_value']))
            note = '%d score rows changed on the same %d paired tasks; no new API calls. Before is the old scorer, not today’s strict_passed metric.' % (rescore['changed_rows'],rescore['common_tasks'])
            md += ['',note,'']
            body.append('<section class="rescore"><h3>The scorer changed. The answers did not.</h3><table><tr><th>Scoring</th><th>n</th><th>Change</th><th>McNemar p</th></tr>%s</table><p>%s</p></section>' % (''.join(table_rows),note))
            for example in rescore['examples'][:2]:
                explanation = '%s · %s · repeat %d: old %s → content %s; strict %s' % (example['task_id'],example['candidate'],example['repeat']+1,example['before'],example['after'],example['strict'])
                md += [explanation,_fence(example['text']), '']
                body.append('<p>%s</p><pre>%s</pre>' % (html.escape(explanation),html.escape(example['text'] or '')))
        for label,key in [('Content correctness','content'),('Strict requested format','strict')]:
            view = comparison[key]
            md += ['### '+label,'']
            body.append('<h3>%s</h3>' % label)
            if not view['available']:
                md += ['Unavailable: this run has no paired scored values for this metric.','']
                body.append('<p class="note">Unavailable: this run has no paired scored values for this metric.</p>')
                continue
            overall = view['overall']
            level = 100*(1-analysis['thresholds']['alpha'])
            headline = '%d paired tasks · %.2f%% → %.2f%% · %+.2f pts (%g%% CI %+.2f to %+.2f) · p=%.6g · repeat noise %.2f%%' % (overall['n'],overall['base_rate']*100,overall['cand_rate']*100,overall['delta']*100,level,overall['ci_low']*100,overall['ci_high']*100,overall['p_value'],overall['noise_floor']*100)
            md += [headline,'','| Slice | n | Change (pts) | CI (pts) | Holm p | Result |','|---|---:|---:|---|---:|---|']
            body.append('<p>%s</p><div class="scroll"><table><tr><th>Slice</th><th>n</th><th>Change</th><th>CI (pts)</th><th>Holm p</th><th>Result</th></tr>' % html.escape(headline))
            for row in sorted(view['slices'],key=lambda s:s['delta']):
                md.append('| %s | %d | %+.2f | %+.2f to %+.2f | %.4g | %s |' % (_cell(row['slice']),row['n'],row['delta']*100,row['ci_low']*100,row['ci_high']*100,row['p_adjusted'],row['verdict']))
                body.append('<tr><td>%s</td><td>%d</td><td>%+.2f</td><td>%+.2f to %+.2f</td><td>%.4g</td><td>%s</td></tr>' % (html.escape(row['slice']),row['n'],row['delta']*100,row['ci_low']*100,row['ci_high']*100,row['p_adjusted'],row['verdict']))
            body.append('</table></div><div class="scroll">%s</div>' % _forest([overall]+sorted(view['slices'],key=lambda s:s['delta'])))
            if not view['regressions']:
                md += ['', 'No paired majority regressions.', '']
                body.append('<p>No paired majority regressions.</p>')
            # Every significant slice gets a representative case, then top disagreements.
            ids = list(dict.fromkeys([next((r['task_id'] for r in view['regressions'] if s['slice'] in r['evidence']['supporting_slices']),None) for s in view['slices'] if s['verdict']=='regression'] + [r['task_id'] for r in view['regressions'][:10]]))
            for task_id in [i for i in ids if i is not None]:
                task = tasks[task_id]
                answers = []
                details = []
                for name,want_pass in [(baseline,True),(candidate,False)]:
                    scored = [r for r in scores if r['task_id']==task_id and r['candidate']==name and r.get(view['field']) is want_pass]
                    repeats = {s['repeat'] for s in scored}
                    answer = next((r.get('text') or '' for r in responses if r['task_id']==task_id and r['candidate']==name and r['repeat'] in repeats),'')
                    answers.append(answer)
                    details.append('; '.join(sorted({s.get('detail','') for s in scored if s.get('detail')})))
                md += ['#### '+task_id,'',_fence(task['prompt']),'','Reference:',_fence(task['reference']),'',baseline+':',_fence(answers[0]),'',candidate+':',_fence(answers[1]),'','Rule: '+_cell(json.dumps(task.get('scorer',{}),ensure_ascii=False)), 'Scorer detail: '+_cell(details[1] or 'Saved score is failed; no detail recorded.'),'']
                images = [_image(asset,root) for asset in task.get('attachments',[])]
                body.append('<article class="case"><h4>%s</h4><p>%s</p>%s<div class="answers">%s</div><p>Rule: %s</p><p>Scorer detail: %s</p></article>' % (html.escape(task_id),html.escape(task['prompt']), ''.join('<img src="%s" alt="Task attachment for %s">' % (image,html.escape(task_id)) for image in images if image), ''.join('<div><h4>%s</h4><pre>%s</pre></div>' % (html.escape(title),html.escape(_text(answer))) for title,answer in [('Reference',task['reference']),(baseline,answers[0]),(candidate,answers[1])]),html.escape(json.dumps(task.get('scorer',{}),ensure_ascii=False)),html.escape(details[1] or 'Saved score is failed; no detail recorded.')))
        md += ['### Cost comparison','','| Candidate | Serving mode | Run USD | USD / 1,000 tasks | Standard estimate | Contributor estimate |','|---|---|---:|---:|---:|---:|']
        body.append('<h3>Cost comparison</h3><div class="scroll"><table><tr><th>Candidate</th><th>Mode</th><th>Run USD</th><th>USD / 1,000 tasks</th><th>Standard estimate</th><th>Contributor estimate</th></tr>')
        for cost in comparison['costs']:
            estimated = cost['estimated_per_1000']
            vals = [cost['total_usd'],cost['per_1000_tasks'],estimated.get('standard'),estimated.get('contributor')]
            formatted = ['$%.4f'%v if v is not None else 'n/a' for v in vals]
            md.append('| %s | %s | %s |' % (_cell(cost['candidate']),cost['mode'],' | '.join(formatted)))
            body.append('<tr><td>%s</td><td>%s</td>%s</tr>' % (html.escape(cost['candidate']),cost['mode'],''.join('<td>%s</td>'%v for v in formatted)))
        body.append('</table></div><p class="note">Per 1,000 tasks means one response per task. Standard/Contributor estimates reprice the saved token usage, not a new quality or latency experiment. Unknown prices are n/a; zero baseline cost has no percentage comparison.</p>')
        md += ['', 'Per 1,000 tasks means one response per task. Standard/Contributor figures are estimates at saved token usage, not measured serving-mode quality. Unknown prices are n/a.','']
    md += ['## Methods in plain words','']
    body.append('<h2>Methods in plain words</h2>')
    for title,paragraph in METHODS:
        md += ['### '+title,'',paragraph,'']
        body.append('<h3>%s</h3><p class="methods">%s</p>' % (title,html.escape(paragraph)))
    body.append('<footer>Sources: run.json, tasks.jsonl, responses.jsonl, scores.jsonl; scores.before-rescore.jsonl when present. No model calls were made to generate this report.</footer>')
    css = ''' :root{color-scheme:light dark;--bg:#f6f5f1;--surface:#fff;--ink:#202623;--muted:#53615a;--line:#d8dfd9;--accent:#9c381f}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.65 Georgia,serif}main{max-width:1120px;margin:auto;padding:36px 24px}h1,h2,h3,h4,.label,table{font-family:Helvetica,sans-serif}h1{font-size:clamp(44px,9vw,96px);line-height:1;margin:18px 0;color:var(--accent);letter-spacing:-.06em}h2{font-size:26px;margin:42px 0 18px}h3{font-size:20px;margin:30px 0 14px}.label{font-size:12px;text-transform:uppercase;letter-spacing:.12em;color:var(--muted)}.banner{border-top:5px solid var(--accent);padding-top:18px}.reason{font-size:23px}.note,.methods,footer{color:var(--muted)}.scroll{overflow:auto}table{border-collapse:collapse;width:100%;font-size:13px;white-space:nowrap}th,td{text-align:right;padding:12px;border-bottom:1px solid var(--line)}th:first-child,td:first-child{text-align:left}.forest{width:100%;min-width:640px;font:13px Helvetica,sans-serif}.rescore{border:1px solid var(--line);padding:20px;background:var(--surface);overflow:auto}.case{padding:20px 0;border-top:1px solid var(--line)}.answers{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}pre{white-space:pre-wrap;overflow-wrap:anywhere;margin:0;padding:16px;background:var(--surface);border:1px solid var(--line);font:13px/1.6 Menlo,monospace}.case img{max-width:400px;width:100%;margin:16px 0}footer{border-top:1px solid var(--line);margin-top:40px;padding-top:20px;font-size:13px}@media(prefers-color-scheme:dark){:root{--bg:#111715;--surface:#18201c;--ink:#edf2ed;--muted:#a2b1a8;--line:#344139;--accent:#ef987a}}@media(max-width:650px){main{padding:20px 16px}.answers{grid-template-columns:1fr}.reason{font-size:19px}}@media print{body{background:white;color:black}.case{break-inside:avoid}}'''
    document = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; img-src data:; style-src \'unsafe-inline\'"><title>%s · Upgrade Gate</title><style>%s</style></head><body><main>%s</main></body></html>' % (content['decision'].upper(),css,''.join(body))
    paths = [root/'report.md', root/'report.html']
    paths[0].write_text('\n'.join(md),encoding='utf-8')
    paths[1].write_text(document,encoding='utf-8')
    return [str(p) for p in paths]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Analyze saved records without making model calls')
    parser.add_argument('run_dir')
    parser.add_argument('--analysis', action='store_true')
    args = parser.parse_args()
    if args.analysis:
        print(json.dumps(build_presentation(args.run_dir),ensure_ascii=False,allow_nan=False))
    else:
        print('\n'.join(write_report(args.run_dir)))
