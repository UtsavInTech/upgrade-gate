# E7 — real voices: spark-1.2@low vs spark-1.3@low

Run: `results/e7-real-voices` · speakers: utsav · clips: 45

## Correct answer

| Slice | n | Δ pts | 95% CI | lost | gained | McNemar p |
|---|---|---|---|---|---|---|
| overall | 45 | -11.1 | -20.0 to -2.2 | 5 | 0 | 0.0625 |
| lang=en | 15 | -13.3 | -33.3 to +0.0 | 2 | 0 | 0.5 |
| lang=hi | 15 | -6.7 | -20.0 to +0.0 | 1 | 0 | 1 |
| lang=hinglish | 15 | -13.3 | -33.3 to +0.0 | 2 | 0 | 0.5 |
| category=classification | 15 | +0.0 | +0.0 to +0.0 | 0 | 0 | 1 |
| category=extraction | 15 | -33.3 | -60.0 to -13.3 | 5 | 0 | 0.0625 |
| category=math | 15 | +0.0 | +0.0 to +0.0 | 0 | 0 | 1 |

## How each version fails (every answer)

| Version | Language | correct | says it can't hear | confident wrong | silent blank | no answer (token limit) |
|---|---|---|---|---|---|---|
| spark-1.2@low | all | 106 | 7 | 22 | 0 | 0 |
| spark-1.2@low | en | 36 | 1 | 8 | 0 | 0 |
| spark-1.2@low | hi | 34 | 3 | 8 | 0 | 0 |
| spark-1.2@low | hinglish | 36 | 3 | 6 | 0 | 0 |
| spark-1.3@low | all | 96 | 3 | 17 | 18 | 1 |
| spark-1.3@low | en | 34 | 2 | 2 | 7 | 0 |
| spark-1.3@low | hi | 30 | 1 | 8 | 5 | 1 |
| spark-1.3@low | hinglish | 32 | 0 | 7 | 6 | 0 |

## Pre-registered test (paired, majority of 3 tries, exact McNemar)

| Flag | Language | Tasks | spark-1.2@low | spark-1.3@low | p |
|---|---|---|---|---|---|
| confident wrong or blank | all | 45 | 6 | 13 | 0.016 |
| confident wrong or blank | en | 15 | 2 | 3 | 1 |
| confident wrong or blank | hi | 15 | 3 | 5 | 0.5 |
| confident wrong or blank | hinglish | 15 | 1 | 5 | 0.12 |
| says it can't hear | all | 45 | 1 | 0 | 1 |
| says it can't hear | en | 15 | 0 | 0 | 1 |
| says it can't hear | hi | 15 | 0 | 0 | 1 |
| says it can't hear | hinglish | 15 | 1 | 0 | 1 |

**Prediction CONFIRMED:** confident wrong or blank 6 → 13 tasks, p = 0.016.
