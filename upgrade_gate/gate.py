"""Fixed-horizon gate decisions over task-paired model evaluations."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
import json
import math
from pathlib import Path

import numpy as np
from scipy.stats import norm

from .schema import read_jsonl
from .stats import (by_slice, compare, flip_rate, majority_pass, paired_bootstrap_ci,
                    pair_up, rank_disagreements)


def evaluate_run(run_dir: str, baseline: str, candidate: str,
                 max_drop: float = 0.02, alpha: float = 0.05, min_n: int = 30) -> dict:
    """Write gate.json using paired tasks after majority voting over repeats.

    Below min_n paired tasks: inconclusive. Otherwise no-go if any eligible
    slice has Holm-adjusted p < alpha and delta < 0, or overall CI upper
    bound < -max_drop. Go if no slice regresses significantly and overall
    CI lower bound > -max_drop. All other outcomes are inconclusive.
    Slices require >=10 pairs. CIs are pointwise (1-alpha) percentile bootstrap
    intervals, not simultaneous or anytime-valid. Holm covers all tested
    category/language/modality slices. Errors are excluded, not counted as fails.
    Costs include model response cost plus each candidate's judging cost;
    judge_usd is the combined judging component, not an extra charge to add.
    """
    if baseline == candidate:
        raise ValueError('Baseline and candidate must differ')
    if not 0 <= max_drop < 1 or not 0 < alpha < 1 or min_n < 1:
        raise ValueError('Invalid gate thresholds')
    root = Path(run_dir)
    run = json.loads((root / 'run.json').read_text(encoding='utf-8'))
    tasks = list(read_jsonl(str(root / 'tasks.jsonl')))
    names = {baseline, candidate}
    scores = [r for r in read_jsonl(str(root / 'scores.jsonl')) if r['candidate'] in names]
    responses = [r for r in read_jsonl(str(root / 'responses.jsonl')) if r['candidate'] in names]
    pairs = pair_up(majority_pass(scores), baseline, candidate)
    task_map = {t['id']: t for t in tasks}
    if any(p[0] not in task_map for p in pairs):
        raise ValueError('Scored task missing from tasks.jsonl')
    overall = compare(pairs, 'overall')
    overall['ci_low'], overall['ci_high'] = paired_bootstrap_ci(pairs, alpha=alpha)
    overall['noise_floor'] = flip_rate(scores)
    overall['unpaired_tasks'] = len(tasks) - len(pairs)
    overall['api_error_rows'] = sum(r.get('passed') is None for r in scores)
    slices = by_slice(pairs, tasks)
    for row in slices:
        field, value = row['slice'].split('=', 1)
        members = [p for p in pairs if str(task_map[p[0]].get(field)) == value]
        row['ci_low'], row['ci_high'] = paired_bootstrap_ci(members, alpha=alpha)
        row['verdict'] = ('regression' if row['delta'] < 0 else 'improvement') if row['p_adjusted'] < alpha else 'no-change' if row['b'] + row['c'] == 0 else 'inconclusive'
    overall['verdict'] = ('regression' if overall['delta'] < 0 else 'improvement') if overall['p_value'] < alpha else 'no-change' if overall['b'] + overall['c'] == 0 and pairs else 'inconclusive'
    bad_slices = sorted([s for s in slices if s['verdict'] == 'regression'], key=lambda s: s['delta'])
    level = 100 * (1 - alpha)
    reasons = []
    enough = len(pairs) >= min_n
    if not enough:
        decision = 'inconclusive'
        reasons.append('Only %d paired tasks; need at least %d more to reach the minimum of %d.' % (len(pairs), min_n-len(pairs), min_n))
    elif bad_slices or overall['ci_high'] < -max_drop:
        decision = 'no-go'
        for row in bad_slices:
            reasons.append('%s regressed %+.1f pts (%g%% CI %+.1f to %+.1f, Holm p=%.4g); overall changed %+.1f pts.' % (row['slice'], row['delta']*100, level, row['ci_low']*100, row['ci_high']*100, row['p_adjusted'], overall['delta']*100))
        if overall['ci_high'] < -max_drop:
            reasons.append('Overall CI upper bound %+.1f pts is below the allowed drop of %.1f pts.' % (100*overall['ci_high'],100*max_drop))
    elif overall['ci_low'] > -max_drop:
        decision = 'go'
        reasons.append('Overall change %+.1f pts (%g%% CI %+.1f to %+.1f) clears the %.1f pt drop limit; no tested slice regresses significantly.' % (overall['delta']*100,level,overall['ci_low']*100,overall['ci_high']*100,max_drop*100))
    else:
        decision = 'inconclusive'
        differences = np.array([int(c)-int(b) for _,b,c in pairs])
        distance = abs(overall['delta'] + max_drop)
        if distance < 1e-10:
            reasons.append('The estimate lies on the drop limit. No finite sample size guarantees a decision; collect at least %d more tasks for a new estimate.' % max(min_n,len(pairs)))
        else:
            variance = max(float(np.var(differences, ddof=1)) if len(pairs)>1 else 1, 1/max(1,len(pairs)))
            target = math.ceil((norm.ppf(1-alpha/2)+norm.ppf(.8))**2 * variance / distance**2)
            more = max(1,target-len(pairs))
            reasons.append('CI overlaps the drop limit. Approximately %d more independent tasks are needed (normal approximation, 80%% power; not a guarantee).' % more)
    model_cost = {name: sum(float(r.get('cost_usd') or 0) for r in responses if r['candidate']==name) for name in names}
    judge_cost = {name: sum(float(r.get('cost_usd') or 0) for r in scores if r['candidate']==name) for name in names}
    totals = {name:model_cost[name]+judge_cost[name] for name in names}
    usage = {name:{token:sum(r.get('usage',{}).get(token,0) or 0 for r in responses if r['candidate']==name) for token in ['input_tokens','output_tokens','reasoning_tokens']} for name in names}
    cost = dict(base_usd=totals[baseline],cand_usd=totals[candidate],
                delta_pct=(totals[candidate]/totals[baseline]-1)*100 if totals[baseline] else None,
                judge_usd=sum(judge_cost.values()), model_usd=model_cost, judge_by_candidate=judge_cost, usage=usage)
    # Explicit candidate ordering makes arbitrary acquisition/file order harmless.
    ordered = [r for name in [baseline,candidate] for r in responses if r['candidate']==name]
    regressions = rank_disagreements(pairs, ordered, tasks)
    score_groups = defaultdict(list)
    for row in scores:
        if row.get('passed') is not None:
            score_groups[(row['task_id'],row['candidate'])].append(bool(row['passed']))
    for row in regressions:
        base_votes = score_groups[(row['task_id'],baseline)]
        cand_votes = score_groups[(row['task_id'],candidate)]
        supporting = [s['slice'] for s in bad_slices if str(task_map[row['task_id']].get(s['slice'].split('=',1)[0])) == s['slice'].split('=',1)[1]]
        row['evidence'] = dict(base_passes=sum(base_votes), base_repeats=len(base_votes),
                               cand_passes=sum(cand_votes),cand_repeats=len(cand_votes),
                               failure_consistency=1-sum(cand_votes)/len(cand_votes),
                               confirmed=bool(enough and (supporting or overall['ci_high'] < -max_drop)),
                               supporting_slices=supporting, source='majority of score rows')
        # Select representative texts from scored repeats; judges can differ from exact matching.
        for name, field, outcome in [(baseline,'base_text',True),(candidate,'cand_text',False)]:
            repeats = {s['repeat'] for s in scores if s['task_id']==row['task_id'] and s['candidate']==name and s.get('passed') is outcome}
            matching = [r for r in responses if r['task_id']==row['task_id'] and r['candidate']==name and r['repeat'] in repeats and r.get('text') is not None]
            if matching:
                row[field] = matching[0]['text']
    regressions.sort(key=lambda r:(-r['evidence']['failure_consistency'],-sum(t['category']==r['category'] for t in tasks),r['task_id']))
    result = dict(run_id=run['run_id'],baseline=baseline,candidate=candidate,decision=decision,reasons=reasons,
                  overall=overall,slices=slices,regressions=regressions,cost=cost,
                  thresholds=dict(max_drop=max_drop,alpha=alpha,min_n=min_n,slice_min_n=10,
                    confidence_level=1-alpha,n_boot=10000,bootstrap_seed=0,
                    rules={'no-go':'n >= min_n and (any slice Holm p < alpha and delta < 0, or overall CI high < -max_drop)',
                           'go':'n >= min_n, no significant regressing slice, and overall CI low > -max_drop',
                           'inconclusive':'otherwise; sample size estimates assume independent task pairs'},
                    cost_includes_judging=True),created_utc=datetime.now(timezone.utc).isoformat())
    (root/'gate.json').write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
    return result
