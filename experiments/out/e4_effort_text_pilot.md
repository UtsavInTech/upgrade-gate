# E4 — reasoning effort ladder on muse-spark-1.3 Contributor (limit 16000 tokens)

Run: `results/e4-effort`

| Effort | correct (finished answers) | correct (cut-offs as fail) | cut off | avg output tokens | cost $ |
|---|---|---|---|---|---|
| minimal | 100.0% | 100.0% | 0 / 30 | 196 | 0.001 |
| low | 100.0% | 100.0% | 0 / 30 | 430 | 0.003 |
| medium | 100.0% | 100.0% | 0 / 30 | 686 | 0.004 |
| high | 100.0% | 100.0% | 0 / 30 | 710 | 0.004 |
| xhigh | 100.0% | 100.0% | 0 / 30 | 751 | 0.005 |

## Step-ups (negative Δ = more effort was worse; cut-offs excluded)

| Slice | n | Δ pts | 95% CI | lost | gained | McNemar p |
|---|---|---|---|---|---|---|
| minimal→low extraction | 10 | +0.0 | +0.0 to +0.0 | 0 | 0 | 1 |
| minimal→low instruction | 10 | +0.0 | +0.0 to +0.0 | 0 | 0 | 1 |
| minimal→low math | 10 | +0.0 | +0.0 to +0.0 | 0 | 0 | 1 |
| low→medium extraction | 10 | +0.0 | +0.0 to +0.0 | 0 | 0 | 1 |
| low→medium instruction | 10 | +0.0 | +0.0 to +0.0 | 0 | 0 | 1 |
| low→medium math | 10 | +0.0 | +0.0 to +0.0 | 0 | 0 | 1 |
| medium→high extraction | 10 | +0.0 | +0.0 to +0.0 | 0 | 0 | 1 |
| medium→high instruction | 10 | +0.0 | +0.0 to +0.0 | 0 | 0 | 1 |
| medium→high math | 10 | +0.0 | +0.0 to +0.0 | 0 | 0 | 1 |
| high→xhigh extraction | 10 | +0.0 | +0.0 to +0.0 | 0 | 0 | 1 |
| high→xhigh instruction | 10 | +0.0 | +0.0 to +0.0 | 0 | 0 | 1 |
| high→xhigh math | 10 | +0.0 | +0.0 to +0.0 | 0 | 0 | 1 |
