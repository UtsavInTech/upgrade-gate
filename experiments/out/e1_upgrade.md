# E1 — spark-1.2@low vs spark-1.3@low

Run: `results/e1-upgrade`

| Slice | n | Δ pts | 95% CI | lost | gained | McNemar p |
|---|---|---|---|---|---|---|
| overall | 1325 | +1.1 | +0.6 to +1.7 | 0 | 15 | 6.1e-05 |
| category=classification | 375 | +0.0 | +0.0 to +0.0 | 0 | 0 | 1 |
| category=doc-image | 200 | +0.5 | +0.0 to +1.5 | 0 | 1 | 1 |
| category=extraction | 240 | +0.0 | +0.0 to +0.0 | 0 | 0 | 1 |
| category=instruction | 150 | +0.0 | +0.0 to +0.0 | 0 | 0 | 1 |
| category=math | 360 | +3.9 | +1.9 to +6.1 | 0 | 14 | 0.000122 |
| lang=en | 675 | +0.0 | +0.0 to +0.0 | 0 | 0 | 1 |
| lang=hi | 330 | +1.8 | +0.6 to +3.3 | 0 | 6 | 0.0312 |
| lang=hinglish | 320 | +2.8 | +1.2 to +4.7 | 0 | 9 | 0.00391 |
| modality=image | 100 | +0.0 | +0.0 to +0.0 | 0 | 0 | 1 |
| modality=pdf | 100 | +1.0 | +0.0 to +3.0 | 0 | 1 | 1 |
| modality=text | 1125 | +1.2 | +0.6 to +2.0 | 0 | 14 | 0.000122 |
