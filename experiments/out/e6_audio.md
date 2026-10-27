# E6 — audio: spark-1.2@low vs spark-1.3@low

Run: `results/e6-audio`

## Correct answer (content score)

| Slice | n | Δ pts | 95% CI | lost | gained | McNemar p |
|---|---|---|---|---|---|---|
| audio: overall | 134 | -2.2 | -9.7 to +5.2 | 14 | 11 | 0.69 |
| audio: lang=en | 45 | +6.7 | -6.7 to +20.0 | 3 | 6 | 0.508 |
| audio: lang=hi | 45 | -11.1 | -22.2 to +0.0 | 6 | 1 | 0.125 |
| audio: lang=hinglish | 44 | -2.3 | -15.9 to +11.4 | 5 | 4 | 1 |
| audio: category=classification | 45 | +4.4 | +0.0 to +11.1 | 0 | 2 | 0.5 |
| audio: category=extraction | 44 | -18.2 | -34.1 to -2.3 | 11 | 3 | 0.0574 |
| audio: category=math | 45 | +6.7 | -6.7 to +20.0 | 3 | 6 | 0.508 |
| text: overall | 135 | +0.0 | +0.0 to +0.0 | 0 | 0 | 1 |
| text: lang=en | 45 | +0.0 | +0.0 to +0.0 | 0 | 0 | 1 |
| text: lang=hi | 45 | +0.0 | +0.0 to +0.0 | 0 | 0 | 1 |
| text: lang=hinglish | 45 | +0.0 | +0.0 to +0.0 | 0 | 0 | 1 |
| text: category=classification | 45 | +0.0 | +0.0 to +0.0 | 0 | 0 | 1 |
| text: category=extraction | 45 | +0.0 | +0.0 to +0.0 | 0 | 0 | 1 |
| text: category=math | 45 | +0.0 | +0.0 to +0.0 | 0 | 0 | 1 |

## Exact format (strict score)

| Slice | n | Δ pts | 95% CI | lost | gained | McNemar p |
|---|---|---|---|---|---|---|
| audio: overall | 134 | -0.7 | -8.2 to +6.7 | 13 | 12 | 1 |
| audio: lang=en | 45 | +6.7 | -6.7 to +20.0 | 3 | 6 | 0.508 |
| audio: lang=hi | 45 | -11.1 | -22.2 to +0.0 | 6 | 1 | 0.125 |
| audio: lang=hinglish | 44 | +2.3 | -11.4 to +15.9 | 4 | 5 | 1 |
| audio: category=classification | 45 | +4.4 | +0.0 to +11.1 | 0 | 2 | 0.5 |
| audio: category=extraction | 44 | -18.2 | -34.1 to -2.3 | 11 | 3 | 0.0574 |
| audio: category=math | 45 | +11.1 | -2.2 to +24.4 | 2 | 7 | 0.18 |
| text: overall | 135 | +0.0 | +0.0 to +0.0 | 0 | 0 | 1 |
| text: lang=en | 45 | +0.0 | +0.0 to +0.0 | 0 | 0 | 1 |
| text: lang=hi | 45 | +0.0 | +0.0 to +0.0 | 0 | 0 | 1 |
| text: lang=hinglish | 45 | +0.0 | +0.0 to +0.0 | 0 | 0 | 1 |
| text: category=classification | 45 | +0.0 | +0.0 to +0.0 | 0 | 0 | 1 |
| text: category=extraction | 45 | +0.0 | +0.0 to +0.0 | 0 | 0 | 1 |
| text: category=math | 45 | +0.0 | +0.0 to +0.0 | 0 | 0 | 1 |

## Listening failures (audio wrong, text twin right, majority of repeats)

- **spark-1.2@low**: 42 — audio-synth-extract-00-en, audio-synth-extract-00-hi, audio-synth-extract-01-hi, audio-synth-extract-01-hinglish, audio-synth-extract-02-hi, audio-synth-extract-03-en, audio-synth-extract-04-en, audio-synth-extract-04-hi, audio-synth-extract-05-en, audio-synth-extract-05-hinglish, audio-synth-extract-06-en, audio-synth-extract-06-hi, audio-synth-extract-06-hinglish, audio-synth-extract-07-en, audio-synth-extract-07-hi, audio-synth-extract-08-hi, audio-synth-extract-09-en, audio-synth-extract-09-hi, audio-synth-extract-09-hinglish, audio-synth-extract-10-en, audio-synth-extract-10-hinglish, audio-synth-extract-11-en, audio-synth-extract-11-hinglish, audio-synth-extract-13-en, audio-synth-extract-13-hi, audio-synth-extract-13-hinglish, audio-synth-intent-01-en, audio-synth-intent-02-en, audio-synth-intent-04-en, audio-synth-intent-07-en, audio-synth-math-00-en, audio-synth-math-00-hinglish, audio-synth-math-01-en, audio-synth-math-03-en, audio-synth-math-04-hinglish, audio-synth-math-06-en, audio-synth-math-06-hinglish, audio-synth-math-08-hinglish, audio-synth-math-10-hinglish, audio-synth-math-13-en, audio-synth-math-13-hinglish, audio-synth-math-14-en
- **spark-1.3@low**: 44 — audio-synth-extract-00-hi, audio-synth-extract-01-hi, audio-synth-extract-01-hinglish, audio-synth-extract-02-hi, audio-synth-extract-02-hinglish, audio-synth-extract-03-en, audio-synth-extract-03-hi, audio-synth-extract-04-en, audio-synth-extract-04-hi, audio-synth-extract-04-hinglish, audio-synth-extract-05-en, audio-synth-extract-05-hinglish, audio-synth-extract-06-en, audio-synth-extract-06-hinglish, audio-synth-extract-07-hi, audio-synth-extract-08-en, audio-synth-extract-08-hi, audio-synth-extract-09-en, audio-synth-extract-09-hi, audio-synth-extract-09-hinglish, audio-synth-extract-10-en, audio-synth-extract-10-hi, audio-synth-extract-10-hinglish, audio-synth-extract-11-en, audio-synth-extract-12-en, audio-synth-extract-12-hi, audio-synth-extract-12-hinglish, audio-synth-extract-13-en, audio-synth-extract-13-hi, audio-synth-extract-13-hinglish, audio-synth-extract-14-en, audio-synth-extract-14-hi, audio-synth-extract-14-hinglish, audio-synth-intent-01-en, audio-synth-intent-02-en, audio-synth-math-00-en, audio-synth-math-00-hinglish, audio-synth-math-01-en, audio-synth-math-06-hinglish, audio-synth-math-07-hi, audio-synth-math-07-hinglish, audio-synth-math-08-hi, audio-synth-math-13-en, audio-synth-math-14-en

## How each version fails (every audio answer, 3 repeats)

| Version | Language | correct | says it can't hear | confident wrong | silent blank | no answer (token limit) |
|---|---|---|---|---|---|---|
| spark-1.2@low | all | 278 | 65 | 60 | 0 | 2 |
| spark-1.2@low | en | 78 | 40 | 17 | 0 | 0 |
| spark-1.2@low | hi | 106 | 2 | 27 | 0 | 0 |
| spark-1.2@low | hinglish | 94 | 23 | 16 | 0 | 2 |
| spark-1.3@low | all | 274 | 4 | 90 | 30 | 7 |
| spark-1.3@low | en | 88 | 1 | 29 | 15 | 2 |
| spark-1.3@low | hi | 94 | 1 | 35 | 5 | 0 |
| spark-1.3@low | hinglish | 92 | 2 | 26 | 10 | 5 |

Correct answers that ALSO claimed the model can't hear audio (it quoted the spoken words): spark-1.2@low 11, spark-1.3@low 0

## Did the failure type change? (paired, majority of repeats per task, exact McNemar)

| Flag | Language | Tasks | spark-1.2@low | spark-1.3@low | only spark-1.2@low | only spark-1.3@low | p |
|---|---|---|---|---|---|---|---|
| confident wrong or blank | all | 135 | 18 | 42 | 2 | 26 | 3e-06 |
| confident wrong or blank | en | 45 | 6 | 17 | 0 | 11 | 0.00098 |
| confident wrong or blank | hi | 45 | 9 | 14 | 1 | 6 | 0.12 |
| confident wrong or blank | hinglish | 45 | 3 | 11 | 1 | 9 | 0.021 |
| says it can't hear | all | 135 | 23 | 0 | 23 | 0 | 2.4e-07 |
| says it can't hear | en | 45 | 14 | 0 | 14 | 0 | 0.00012 |
| says it can't hear | hi | 45 | 0 | 0 | 0 | 0 | 1 |
| says it can't hear | hinglish | 45 | 9 | 0 | 9 | 0 | 0.0039 |
