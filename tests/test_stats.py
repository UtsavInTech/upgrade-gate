from __future__ import annotations

import pytest
from upgrade_gate.stats import (majority_pass, pair_up, mcnemar_exact, paired_bootstrap_ci,
                                compare, holm, by_slice, flip_rate, sequential_test, rank_disagreements)


def test_votes_pairs_nulls_ties():
    rows = [dict(task_id=t, candidate=c, passed=p) for t,c,p in [
        ('a','old',True), ('a','old',False), ('a','old',None), ('a','new',True),
        ('b','old',None), ('b','new',True)]]
    majority = majority_pass(rows)
    assert majority == {('a','old'):False, ('a','new'):True, ('b','old'):None, ('b','new'):True}
    assert pair_up(majority,'old','new') == [('a',False,True)]
    assert flip_rate(rows) == 1
    assert flip_rate([]) == 0


def test_mcnemar_known():
    assert mcnemar_exact(0,0) == 1
    assert mcnemar_exact(10,0) == pytest.approx(.001953125)
    assert mcnemar_exact(3,3) == 1
    with pytest.raises(ValueError):
        mcnemar_exact(-1,2)


def test_bootstrap_paired_delta():
    pairs = [(str(i), i < 60, i < 70) for i in range(100)]
    low, high = paired_bootstrap_ci(pairs)
    assert low < .1 < high
    assert (low,high) == paired_bootstrap_ci(pairs)
    row = compare(pairs,'overall')
    assert row['delta'] == pytest.approx(.1)
    assert row['b'] == 0 and row['c'] == 10
    assert paired_bootstrap_ci([]) == (-1,1)


def test_holm_order_and_monotonicity():
    assert holm([.04,.001,.03]) == pytest.approx([.06,.003,.06])
    assert holm([]) == []
    assert holm([1,1]) == [1,1]


def test_slice_minimum_and_adjustment():
    pairs = [(str(i), True, False) for i in range(20)]
    tasks = [dict(id=str(i), category='doc' if i<15 else 'tiny',lang='hi',modality='text') for i in range(20)]
    slices = by_slice(pairs,tasks)
    assert len(slices) == 3
    assert all(r['p_adjusted'] >= r['p_value'] for r in slices)


def test_sequential_stopping():
    result = sequential_test([(str(i),True,False) for i in range(500)])
    assert result['stop'] and result['verdict'] == 'regression' and result['n_used'] < 500
    assert sequential_test([])['n_used'] == 0
    assert not sequential_test([('x',True,True)])['stop']
    assert sequential_test([(str(i),False,True) for i in range(500)])['verdict'] == 'improvement'
    assert sequential_test([(str(i),True,True) for i in range(1000)],max_drop=.2)['verdict'] == 'equivalent'


def test_rank_reference_failures():
    tasks = [dict(id='x',category='math',lang='en',reference='4')]
    responses = [dict(task_id='x',candidate=c,text=text) for c,text in [('old','4'),('new','5'),('new','5'),('new','4')]]
    result = rank_disagreements([('x',True,False)],responses,tasks)
    assert result[0]['cand_text'] == '5'
    assert result[0]['evidence']['failure_consistency'] == pytest.approx(2/3)
