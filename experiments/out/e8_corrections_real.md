# E8 — spoken self-corrections: spark-1.2@low vs spark-1.3@low

Run: `results/e8-real` · clips: 0 synthetic correction, 0 control, 15 real-voice correction

## Pre-registered test (items = one note in three languages, sign test)

| Clips | Items | spark-1.2@low right | spark-1.3@low right | items worse on 1.3 | items better | p |
|---|---|---|---|---|---|---|
| correction | 0 | 0 | 0 | 0 | 0 | 1 |
| control | 0 | 0 | 0 | 0 | 0 | 1 |

Did 1.3 lose more on the correction clip than on the same note without one? items worse 0, better 0, p = 1.

**Prediction NOT CONFIRMED:** on correction clips 1.3 got 0 of 0 right vs 0 for 1.2; 0 items worse, 0 better, p = 1.

## Kept the number the customer took back

| Set | Clips | spark-1.2@low tries | spark-1.3@low tries | spark-1.2@low clips (majority) | spark-1.3@low clips | only 1.2 | only 1.3 | p |
|---|---|---|---|---|---|---|---|---|
| real voice | 15 | 0 / 45 | 3 / 45 | 0 | 1 | 0 | 1 | 1 |

## All fields right, by slice (per clip, McNemar)

| Slice | n | Δ pts | 95% CI | lost | gained | McNemar p |
|---|---|---|---|---|---|---|
| correction clips | 0 | — | — to — | 0 | 0 | 1 |
| control clips | 0 | — | — to — | 0 | 0 | 1 |
| correction, en | 0 | — | — to — | 0 | 0 | 1 |
| correction, hi | 0 | — | — to — | 0 | 0 | 1 |
| correction, hinglish | 0 | — | — to — | 0 | 0 | 1 |
| correction, order_number corrected | 0 | — | — to — | 0 | 0 | 1 |
| correction, pincode corrected | 0 | — | — to — | 0 | 0 | 1 |
| correction, real voice | 15 | -53.3 | -80.0 to -26.7 | 8 | 0 | 0.00781 |
