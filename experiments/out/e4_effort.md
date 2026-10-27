# E4 — reasoning effort ladder on muse-spark-1.3 Contributor (limit 16000 tokens)

Run: `results/e4-effort`

| Effort | correct (finished answers) | correct (cut-offs as fail) | cut off | avg output tokens | cost $ |
|---|---|---|---|---|---|
| minimal | 72.8% | 72.8% | 0 / 405 | 375 | 0.035 |
| low | 69.1% | 68.9% | 1 / 405 | 818 | 0.072 |
| medium | 64.8% | 64.2% | 4 / 405 | 1500 | 0.127 |
| high | 66.0% | 63.7% | 14 / 405 | 2051 | 0.172 |
| xhigh | 61.1% | 58.5% | 17 / 405 | 2562 | 0.213 |

## Step-ups (negative Δ = more effort was worse; cut-offs excluded)

| Slice | n | Δ pts | 95% CI | lost | gained | McNemar p |
|---|---|---|---|---|---|---|
| minimal→low classification | 45 | +2.2 | +0.0 to +6.7 | 0 | 1 | 1 |
| minimal→low extraction | 45 | -13.3 | -28.9 to +0.0 | 9 | 3 | 0.146 |
| minimal→low math | 45 | +0.0 | -8.9 to +8.9 | 2 | 2 | 1 |
| low→medium classification | 45 | -2.2 | -6.7 to +0.0 | 1 | 0 | 1 |
| low→medium extraction | 45 | -6.7 | -22.2 to +8.9 | 8 | 5 | 0.581 |
| low→medium math | 45 | -6.7 | -15.6 to +2.2 | 4 | 1 | 0.375 |
| medium→high classification | 45 | +0.0 | -6.7 to +6.7 | 1 | 1 | 1 |
| medium→high extraction | 44 | +0.0 | -15.9 to +15.9 | 7 | 7 | 1 |
| medium→high math | 45 | +6.7 | -4.4 to +17.8 | 2 | 5 | 0.453 |
| high→xhigh classification | 45 | +0.0 | -6.7 to +6.7 | 1 | 1 | 1 |
| high→xhigh extraction | 43 | -9.3 | -25.6 to +7.0 | 8 | 4 | 0.388 |
| high→xhigh math | 45 | -6.7 | -17.8 to +4.4 | 5 | 2 | 0.453 |
