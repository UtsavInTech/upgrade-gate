# Upgrade Gate — Current Status

_Last updated: Oct 27, 2026 (IST). Phase: **research before building**. No code written yet._

## The event

| | |
|---|---|
| Hackathon | Meta Global AI Developer Hackathon (run by Cerebral Valley) |
| Track | Indie developer track, **solo** |
| Status | **Approved** (email from Cerebral Valley confirmed) |
| Build window | Oct 26 → Nov 4, 9:00 PM ET |
| Hard deadline (IST) | **Nov 5, 7:30 AM IST**. Treat the evening of **Nov 4 IST** as the real cut-off |
| Submit at | cerebralvalley.ai/e/meta-ai-developer-hackathon/hackathon/submit |

### Rules that shape the project
- **New work only.** Demo may show only what's built during the event. Old code (AdaptiveML Studio, FocusSpace) can't be copied in. Ideas and logic from your paper can be cited and re-implemented fresh.
- **Repo must be public at submission.** This repo is **private for now** so other hackers can't read the plan. Make it public before you submit.
- **Banned as generic:** basic RAG apps, simple image analyzers, "AI for education" chatbots, medical advice tools.
- **Stage 1:** pass/fail on theme fit + real use of Meta's models.
- **Stage 2 rubric (0–10):** Impact 30% · Demo 25% · Use of Meta AI tooling 25% · Technical depth 20%. The tooling criterion rewards going "beyond a basic integration" and surfacing **unexpected capabilities**.
- Top 5 per track get their 3-minute demo video judged live.
- Bonus prizes worth targeting: $10K best open-weights build (Muse Spark Open / Glimmer), $5K best agentic use, $20K most viral X post.
- Submission ownership: must be solely yours; organisers get a perpetual licence to it.

## The idea: Upgrade Gate

A cost-aware, statistically sound **go / no-go gate for model upgrades**. Its first job is a public study of Muse Spark 1.1 vs 1.2 vs 1.3 across modalities and reasoning-effort levels.

How it got here: Dubash → farm advisory → Verified Learning → Munim → self-healing solar vision → stale-model study → Ruko → regression radar → "find what your tests miss" → **Upgrade Gate**. Each earlier idea was dropped for being crowded, not lived, or not needing Meta's models.

### Architecture (planned)
```
Task packs (public data, known answers) ──► Adaptive runner ──► Meta Model API
 structured · doc/PDF/image · tool args      repeats, risk        Spark 1.1/1.2/1.3
                                             categories, budget   × effort levels
                         ▼
 Scorers: deterministic first (schema, exact match, run code)
          then judge cascade: Spark Open (cheap) → Muse Wonder only on disagreement
                         ▼
 Stats: paired deltas, per-category CIs, sequential stopping, disagreement mining
            ▼                          ▼
 Gate report (go/no-go, $)     Export: Promptfoo-style YAML + pytest
                               Canary: same model ID over days → change detection
```
- **Single-turn tasks only** (extraction, classification, triage). Full agent replay is out of scope.
- Paired tests (McNemar / bootstrap CIs) are the core. Drift detection (ADWIN via the River library, re-implemented fresh) is used **only** for the multi-day canary, where timestamps are real.
- Export to existing tools so it complements LangSmith / Braintrust / Promptfoo instead of cloning them.

## What research already killed (don't claim these)
- "Averages hide regressions" — already published for the GPT line (arXiv 2608.17719).
- Paired / sequential gates — partly published ("Test Before You Deploy", 2026).
- Judge cascades — prior work exists ("Trust or Escalate").
- Any "first tool" / "nobody has done this" wording.
- What survives: **the first study of Muse Spark versions, serving modes and effort levels, with a gate whose own error rates are measured.**

## Current honest score
| Criterion | Weight | Now | Needed for 9+ |
|---|---|---|---|
| Impact | 30% | 7 | real hackers using it on their own agents |
| Demo | 25% | 8 | live "gate blocks a bad upgrade" moment |
| Meta tooling | 25% | 8 | a surprising finding about Meta's own models |
| Technical depth | 20% | 8 | gate with measured false-pass / false-block rates |
| **Weighted** | | **≈ 7.7** (skeptic agent: 5.9 on the original spec) | **9+** |

The single biggest lever is **a real, validated surprising finding**. See [RESEARCH_GUIDE.md](RESEARCH_GUIDE.md).

## Candidate surprises (hypotheses, not results)
1. **Judge-lineage false passes** — a judge from the same model family passes that family's errors more often than an outside judge.
2. **Image / PDF regressions in 1.3 vs 1.2** — Meta's own docs warn audio quality may degrade in 1.3; check if other modalities do too.
3. **Contributor vs Standard mode equivalence** — Contributor is ~15× cheaper per call; are outputs actually the same quality?
4. **Reasoning effort isn't monotonic** — higher effort sometimes worse on some task categories.
5. **Silent drift under a pinned model ID** — the multi-day canary.

All five are unverified. They become findings only after the experiments in the guide.

## Literature check (Oct 27)
Details and sources in [findings/LOG.md](findings/LOG.md).
- **Muse Spark 1.1 is marked deprecated** (successor 1.2, no retirement date). Check on the first API call. If it's going away, capture the 1.1 baseline first.
- **H1:** general same-family judge bias is already published. What's left open is **judge-version bias in upgrade gates**.
- **H5:** no recent peer-reviewed study of a pinned version over days. Added **H5b: answers change with server load / time of day**.
- **H6:** no public Hindi results for Muse Spark, and no study of whether an upgrade widens the Hindi–English gap. Hindi IFEval/GSM8K give matched pairs.

## Open items / blockers
- [ ] Meta Model API call works from India (decides everything)
- [ ] $150 Meta credits claimed (needs card on Meta account)
- [ ] Modal ($100) / Baseten ($100) / Fireworks ($25) credits requested
- [ ] Discord role claimed; ask: Glimmer vs SAM 3 vs SAM 3.1, which Spark versions are reachable
- [ ] Confirm whether "max" reasoning effort exists and how Contributor-mode limits work
- [ ] Pick demo datasets and check licenses (candidates: CORD, SROIE, Banking77)
- [ ] **Start the canary by Oct 28** — it needs ~8 days of data
- [ ] Make repo public before submitting

## Schedule (IST)
| Date | Work |
|---|---|
| Oct 27 | Research + first API call. Agents 101 session 9:30 PM |
| Oct 28–29 | Runner, deterministic scorers, paired stats on 2 task packs. **Start canary.** Agents 102 Oct 28 9:30 PM |
| Oct 30–31 | Adaptive stopping, judge cascade, disagreement mining |
| Nov 1–2 | Full study run, report, export |
| Nov 3 | Get other hackers on Discord to run it (Impact evidence). Record 3-min video |
| Nov 4 | Submit by evening IST |
