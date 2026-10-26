# How to Find Surprising Findings

A "surprising finding" is what moves this project from ~7.7 to 9+. This guide is the method.

## 1. What counts as surprising

A finding is surprising only if **all four** are true:

1. **It breaks a belief people hold.** Write the belief down first. "Newer version is at least as good." "Higher reasoning effort is never worse." "A cheaper serving mode gives the same answers."
2. **It's measured with a number and a confidence interval.** "1.3 is worse" is an opinion. "1.3 fails 14% more PDF-table extractions than 1.2 (95% CI 8–20%, n=300)" is a finding.
3. **It survives replication** — fresh run, different seed, different day, a second judge.
4. **Someone would change a decision because of it.** A developer would delay an upgrade, switch mode, or change a judge.

If it fails any one of these, it's an observation, not a finding.

## 2. Pre-register before you run anything

Before each experiment, add an entry to [findings/LOG.md](findings/LOG.md):

```
## H<n>: <one-line hypothesis>
Belief it challenges:
My prediction (and how confident, %):
What result would count as "surprising":
What result would count as "boring":
Sample size + cost estimate:
```

Why: judges trust results that were predicted in advance. It also stops you from fishing through data until something looks interesting.

## 3. Where surprises hide (look here, not at averages)

Averages are where boring results live. Surprises live in **slices** and **tails**:

| Slice | Example question |
|---|---|
| Modality | Does 1.3 regress on images / PDFs while improving on text? |
| Language | **Hindi / Hinglish / Indic text** — does an upgrade quietly hurt non-English? (This is your "Build for Your World" angle.) |
| Reasoning effort | Is there a task type where *more* effort gives *worse* answers? |
| Serving mode | Contributor vs Standard: same inputs, are answers actually identical in quality? |
| Output format | Structured JSON / tool-call arguments — do schema errors go up after an upgrade? |
| Input length | Does the regression only appear past N tokens? |
| Consistency | Same input, same model, temperature fixed: how often does the answer flip? |
| Time | Same pinned model ID across days: does behaviour drift? (the canary) |
| Judges | Does a same-family judge forgive same-family errors? |
| Cost | Did 1.3 get better but spend 2× the tokens to do it? |

**Technique:** for every result, sort by "biggest difference between versions" and read the top 20 cases by hand. That's where you'll spot the pattern.

## 4. Pilot cheap, then scale where the signal is

1. **Smoke test (Day 1, ~$2):** 30 items × 3 versions × 1 run. Just check the pipeline works and nothing is broken (truncation, rate-limit errors, bad parsing).
2. **Scout run (~$10):** 50 items per slice × 3 versions × 3 repeats. Measure: flip rate between versions, flip rate within a version (noise floor), cost per item.
3. **Rule:** a slice is worth scaling only if the between-version difference is clearly bigger than the within-version noise.
4. **Confirm run:** scale only the 1–2 promising slices to a sample size big enough for a tight interval (paired McNemar / bootstrap).

With 50 items, a 90% → 85% drop is inside the noise. Don't celebrate small-sample differences.

## 5. Kill your own finding before a judge does

Run every candidate through this checklist:

- [ ] **Bug check:** were failures actually API errors, timeouts, truncated outputs, or parse failures? Count those separately.
- [ ] **Prompt check:** was the prompt identical across versions (byte-for-byte)?
- [ ] **Noise check:** is the effect bigger than the same model disagreeing with itself?
- [ ] **Judge check:** does the result hold with a deterministic scorer, or with a second judge from a different model family?
- [ ] **Hand check:** read 20 random "regression" cases yourself. Are they really worse?
- [ ] **Replicate:** fresh run on a different day. Same direction?
- [ ] **Skeptic pass:** ask a separate AI agent (or a friend) to argue the finding is wrong. Fix or drop.
- [ ] **Literature check:** search Google Scholar / arXiv to make sure it isn't already published. If it is, cite it and claim "first on Muse Spark".

## 6. Where to look for leads before you spend credits

- **Meta's own docs:** model cards, changelogs, "known issues" (that's how the 1.3 audio warning was found). Read every line about version differences.
- **Discord:** search for other hackers saying "1.3 got worse at X" / "different answers". Each complaint is a free hypothesis.
- **Papers:** arXiv 2608.17719 (aggregate gains hide regressions), "Test Before You Deploy" (open problems list = gaps you can fill), "Trust or Escalate" (judge cascades). Their "limitations" and "future work" sections are gold.
- **Search queries to try:** `"model update" regression LLM`, `LLM version drift behaviour`, `LLM-as-judge self-preference bias`, `non-determinism LLM API temperature 0`, `reasoning effort overthinking`.
- **Your own paper:** concept-drift ideas (ADWIN, warning vs drift levels) → re-implement fresh for the canary.

## 7. Ranking the hypotheses (do these first)

| # | Hypothesis | Surprise if true | Cost | Do when |
|---|---|---|---|---|
| H5 | Silent drift under pinned model ID (canary) | High | Low, but needs days | **Start Oct 28** |
| H1 | Same-family judge forgives same-family errors | High, and it attacks every eval tool | Low | Day 2 |
| H2 | Image/PDF regress in 1.3 vs 1.2 | Medium-high | Medium | Day 2–3 |
| H6 | Hindi/Indic regresses while English improves | High + "your world" story | Low-medium | Day 2–3 |
| H3 | Contributor ≠ Standard quality | High (money) | Low | Day 3 |
| H4 | More effort → worse on some tasks | Medium | Medium | Day 3–4 |

## 8. How a finding turns into score

- **Meta tooling (25%):** "surfaced unexpected capabilities" — a measured, real finding about Meta's own versions is exactly this.
- **Demo (25%):** open the video on the finding. "We upgraded 1.2 → 1.3. Average got better. The gate blocked it anyway. Here's why."
- **Impact (30%):** a finding every Meta API developer needs to know, plus other hackers running the gate on their own agents.
- **Technical depth (20%):** the gate's own false-pass / false-block rates, measured.

## 9. Daily routine

1. Morning: read new Discord threads + docs updates → add leads to the log.
2. Pre-register the day's 1–2 hypotheses.
3. Run scout → check noise floor → decide scale or drop.
4. Evening: run the kill-checklist on anything promising. Update [STATUS.md](STATUS.md).
