# E8 — spoken self-corrections: spark-1.2@low vs spark-1.3@low

Run: `results/e8-corrections` · clips: 45 synthetic correction, 45 control, 0 real-voice correction

## Pre-registered test (items = one note in three languages, sign test)

| Clips | Items | spark-1.2@low right | spark-1.3@low right | items worse on 1.3 | items better | p |
|---|---|---|---|---|---|---|
| correction | 15 | 22 | 13 | 7 | 2 | 0.18 |
| control | 15 | 25 | 18 | 6 | 1 | 0.12 |

Did 1.3 lose more on the correction clip than on the same note without one? items worse 3, better 3, p = 1.

**Prediction NOT CONFIRMED:** on correction clips 1.3 got 13 of 45 right vs 22 for 1.2; 7 items worse, 2 better, p = 0.18.

## Kept the number the customer took back

| Set | Clips | spark-1.2@low tries | spark-1.3@low tries | spark-1.2@low clips (majority) | spark-1.3@low clips | only 1.2 | only 1.3 | p |
|---|---|---|---|---|---|---|---|---|
| synthetic | 45 | 14 / 135 | 7 / 135 | 3 | 0 | 3 | 0 | 0.25 |

## All fields right, by slice (per clip, McNemar)

| Slice | n | Δ pts | 95% CI | lost | gained | McNemar p |
|---|---|---|---|---|---|---|
| correction clips | 45 | -20.0 | -35.6 to -4.4 | 12 | 3 | 0.0352 |
| control clips | 45 | -15.6 | -31.1 to +0.0 | 11 | 4 | 0.118 |
| correction, en | 15 | -20.0 | -46.7 to +6.7 | 4 | 1 | 0.375 |
| correction, hi | 15 | -13.3 | -40.0 to +13.3 | 3 | 1 | 0.625 |
| correction, hinglish | 15 | -26.7 | -53.3 to +0.0 | 5 | 1 | 0.219 |
| correction, order_number corrected | 24 | -29.2 | -50.0 to -8.3 | 8 | 1 | 0.0391 |
| correction, pincode corrected | 21 | -9.5 | -33.3 to +14.3 | 4 | 2 | 0.688 |
