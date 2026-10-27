# E2 — judge-version bias (H1)

Run: `/Users/utsavintech/Documents/upgrade-gate/results/e2-judges-e6-audio`

## False-pass rate by judge and by which version wrote the answer

False pass = judge says correct, ground truth says wrong. Lower is better.

| Judge | Producer | wrong answers | false passes | false-pass rate | false-fail rate |
|---|---|---|---|---|---|
| spark-1.2-c | spark-1.2@low | 125 | 0 | 0.0% | 4.3% |
| spark-1.2-c | spark-1.3@low | 124 | 0 | 0.0% | 0.0% |
| spark-1.3-c | spark-1.2@low | 125 | 0 | 0.0% | 4.3% |
| spark-1.3-c | spark-1.3@low | 124 | 0 | 0.0% | 0.0% |

## Does a judge go easier on its own version's mistakes?

Fisher exact test on wrong answers (answer level; repeats of one task are not independent, so treat p as a guide).

| Judge | false passes on 1.2's wrong answers | on 1.3's wrong answers | p |
|---|---|---|---|
| spark-1.2-c | 0 / 125 (0.0%) | 0 / 124 (0.0%) | 1 |
| spark-1.3-c | 0 / 125 (0.0%) | 0 / 124 (0.0%) | 1 |

## Would the gate decision change with this judge?

| Slice | n | Δ pts | 95% CI | lost | gained | McNemar p |
|---|---|---|---|---|---|---|
| ground truth | 134 | -2.2 | -9.7 to +5.2 | 14 | 11 | 0.69 |
| judge=spark-1.2-c | 134 | -0.7 | -8.2 to +6.7 | 13 | 12 | 1 |
| judge=spark-1.3-c | 134 | -0.7 | -8.2 to +6.7 | 13 | 12 | 1 |

A judge is biased toward the upgrade if its Δ is clearly above the ground-truth Δ.
