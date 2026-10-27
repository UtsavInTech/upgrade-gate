"""Task-paired inference. Repeats are votes, never independent observations."""
from __future__ import annotations

from collections import Counter, defaultdict
import json
from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy.special import logsumexp
from scipy.stats import binomtest


def majority_pass(score_rows) -> Dict[Tuple[str, str], Optional[bool]]:
    votes = defaultdict(list)
    for row in score_rows:
        key = (row['task_id'], row['candidate'])
        votes[key]  # Retain all-error groups as None.
        if row.get('passed') is not None:
            votes[key].append(bool(row['passed']))
    return {key: sum(values) > len(values) / 2 if values else None for key, values in votes.items()}


def pair_up(majority, baseline, candidate) -> List[tuple]:
    return [(task_id, value, majority[(task_id, candidate)])
            for (task_id, name), value in sorted(majority.items())
            if name == baseline and value is not None
            and majority.get((task_id, candidate)) is not None]


def mcnemar_exact(b, c) -> float:
    if b < 0 or c < 0 or int(b) != b or int(c) != c:
        raise ValueError('Discordant counts must be nonnegative integers')
    return float(binomtest(int(b), int(b + c), .5).pvalue) if b + c else 1.0


def paired_bootstrap_ci(pairs, n_boot=10000, alpha=0.05, seed=0) -> tuple:
    """Percentile CI resampling whole task pairs, conditional on scored tasks."""
    if not 0 < alpha < 1 or n_boot < 1:
        raise ValueError('Require 0 < alpha < 1 and n_boot >= 1')
    if not pairs:
        return (-1.0, 1.0)
    differences = np.array([int(c) - int(b) for _, b, c in pairs])
    # The empirical distribution has only three values. Multinomial counts are
    # exactly equivalent to resampling n differences and avoid an n_boot*n array.
    probabilities = np.array([(differences == value).mean() for value in [-1, 0, 1]])
    draws = np.random.default_rng(seed).multinomial(len(pairs), probabilities, size=n_boot)
    deltas = (draws[:, 2] - draws[:, 0]) / len(pairs)
    return tuple(float(v) for v in np.quantile(deltas, [alpha / 2, 1 - alpha / 2]))


def compare(pairs, slice_name) -> dict:
    n = len(pairs)
    b = sum(bool(base) and not cand for _, base, cand in pairs)
    c = sum(bool(cand) and not base for _, base, cand in pairs)
    low, high = paired_bootstrap_ci(pairs)
    base_rate = sum(bool(base) for _, base, _ in pairs) / n if n else 0.0
    cand_rate = sum(bool(cand) for _, _, cand in pairs) / n if n else 0.0
    p = mcnemar_exact(b, c)
    delta = (c - b) / n if n else 0.0
    return dict(slice=slice_name, n=n, base_rate=base_rate, cand_rate=cand_rate,
                delta=delta, ci_low=low, ci_high=high, b=b, c=c, p_value=p,
                p_adjusted=None, verdict=('regression' if delta < 0 else 'improvement')
                if p < .05 else 'no-change' if b + c == 0 and n else 'inconclusive')


def holm(p_values) -> list:
    """Holm familywise adjustment, preserving the original input order."""
    p = np.asarray(p_values, dtype=float)
    if np.any(~np.isfinite(p)) or np.any((p < 0) | (p > 1)):
        raise ValueError('p-values must be finite and in [0, 1]')
    order = np.argsort(p, kind='stable')
    result = np.empty(len(p))
    adjusted = np.minimum(1, np.maximum.accumulate(p[order] * np.arange(len(p), 0, -1)))
    result[order] = adjusted
    return result.tolist()


def by_slice(pairs, tasks) -> list:
    tasks = {task['id']: task for task in tasks} if not isinstance(tasks, dict) else tasks
    groups = defaultdict(list)
    for pair in pairs:
        task = tasks.get(pair[0], {})
        for field in ['category', 'lang', 'modality']:
            if task.get(field) is not None:
                groups[field + '=' + str(task[field])].append(pair)
    comparisons = [compare(group, name) for name, group in sorted(groups.items()) if len(group) >= 10]
    for row, adjusted in zip(comparisons, holm([r['p_value'] for r in comparisons])):
        row['p_adjusted'] = adjusted
        row['verdict'] = ('regression' if row['delta'] < 0 else 'improvement') if adjusted < .05 else 'no-change' if row['b'] + row['c'] == 0 else 'inconclusive'
    return comparisons


def flip_rate(score_rows) -> float:
    """Fraction of groups with >=2 scored repeats that contain both outcomes."""
    groups = defaultdict(list)
    for row in score_rows:
        if row.get('passed') is not None:
            groups[(row['task_id'], row['candidate'])].append(bool(row['passed']))
    eligible = [votes for votes in groups.values() if len(votes) >= 2]
    return sum(len(set(votes)) > 1 for votes in eligible) / len(eligible) if eligible else 0.0


def sequential_test(pairs, max_drop=0.02, alpha=0.05, min_n=30) -> dict:
    """Anytime-valid mixture betting test on independent task differences D∈[-1,1].

    For a mean bound m, mix 16 fixed-fraction wealth processes
    product(1 + lambda*(D-m)), with |lambda|<=.49. Each is a nonnegative
    supermartingale under its directional null (conditional mean bounded by m).
    Ville's inequality permits arbitrary peeking. Four directional tests each
    receive alpha/4: regression below -margin, improvement above +margin, and
    both sides of equivalence (-margin,+margin). Equivalence requires both
    one-sided e-values to cross. No stopping guarantee for small effects.
    Input order must be the acquisition order, not an outcome-sorted ranking.
    This rule does not make the fixed-horizon gate's bootstrap CI anytime-valid.
    """
    if not 0 < max_drop < 1 or not 0 < alpha < 1 or min_n < 1:
        raise ValueError('Require margin and alpha in (0,1), and positive min_n')
    fractions = np.geomspace(.001, .49, 16)
    log_wealth = np.zeros((4, len(fractions)))
    # null: mean >= -margin; <= +margin; <= -margin; >= +margin
    bounds = np.array([-max_drop, max_drop, -max_drop, max_drop])
    signs = np.array([-1, 1, 1, -1])
    crossed = np.zeros(4, dtype=bool)
    count = 0
    for count, (_, base, cand) in enumerate(pairs, 1):
        diff = int(cand) - int(base)
        log_wealth += np.log1p(signs[:, None] * fractions * (diff - bounds[:, None]))
        crossed |= logsumexp(log_wealth, axis=1) - np.log(len(fractions)) >= np.log(4 / alpha)
        if count >= min_n:
            verdict = 'regression' if crossed[0] else 'improvement' if crossed[1] else 'equivalent' if crossed[2] and crossed[3] else None
            if verdict:
                return dict(stop=True, verdict=verdict, n_used=count)
    return dict(stop=False, verdict='inconclusive', n_used=count)


def reference_matches(text, task) -> bool:
    """Reference checks used to summarize deterministic repeat evidence only."""
    if text is None:
        return False
    reference = task['reference']
    scorer = task.get('scorer', {})
    if scorer.get('type') == 'contains':
        return str(reference) in text
    if isinstance(reference, (dict, list, int, float, bool)):
        try:
            parsed = json.loads(text)
        except (ValueError, TypeError):
            return False
        if isinstance(reference, dict) and isinstance(parsed, dict):
            return all(key in parsed and parsed[key] == value for key, value in reference.items())
        return parsed == reference
    return text.strip() == str(reference).strip()


def rank_disagreements(pairs, responses, tasks) -> list:
    """Rank baseline-only successes by repeated reference failures, then slice size.

    The gate replaces inferred repeat evidence with authoritative score rows;
    this standalone helper can only infer deterministic reference agreement.
    Responses should contain only the two candidates under comparison.
    """
    tasks = {task['id']: task for task in tasks} if not isinstance(tasks, dict) else tasks
    category_sizes = Counter(task['category'] for task in tasks.values())
    groups = defaultdict(lambda: defaultdict(list))
    for row in responses:
        groups[row['task_id']][row['candidate']].append(row)
    ranked = []
    # Candidate ordering must be explicit: callers attach role before passing;
    # otherwise response acquisition order defines baseline then candidate.
    names = list(dict.fromkeys(row['candidate'] for row in responses))
    for task_id, base, cand in pairs:
        if not base or cand or task_id not in tasks or len(names) < 2:
            continue
        task = tasks[task_id]
        base_rows, cand_rows = groups[task_id][names[0]], groups[task_id][names[1]]
        def representative(rows, want_pass):
            valid = [r for r in rows if r.get('text') is not None]
            matching = [r for r in valid if reference_matches(r['text'], task) == want_pass]
            values = [r['text'] for r in matching or valid]
            return Counter(values).most_common(1)[0][0] if values else ''
        valid = [r for r in cand_rows if r.get('text') is not None]
        consistency = sum(not reference_matches(r['text'], task) for r in valid) / len(valid) if valid else 0
        ranked.append(dict(task_id=task_id, category=task['category'], lang=task['lang'],
                           base_text=representative(base_rows, True), cand_text=representative(cand_rows, False),
                           reference=task['reference'], evidence={'failure_consistency': consistency,
                           'scored_repeats': len(valid), 'source': 'reference comparison'}))
    return sorted(ranked, key=lambda row: (-row['evidence']['failure_consistency'], -category_sizes[row['category']], row['task_id']))
