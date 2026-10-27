# Upgrade Gate — Current Status

_Last updated: Oct 27, 2026, late evening (IST). Phase: **built; three experiments done; polishing the demo**._

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

### Architecture
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

## Results so far (all from real API runs, $18.31 spent of a $90 cap)
| Run | Question | Result | Cost |
|---|---|---|---|
| **E6 voice notes** | Does 1.3 listen worse than 1.2 (Meta's docs warn about 1.3 audio)? | Same accuracy (278 vs 274 of 405), but answers that are **wrong or blank with no warning rose 18 → 42 of 135 clips, p = 3e-6**. 1.2 often says "I can't hear the audio" (23 clips, sometimes while quoting the speech); 1.3 never does. Accuracy-only gate: INCONCLUSIVE (~9,000 more clips needed). | $3.34 |
| **E1 text, docs, Hindi** | 1.2 → 1.3 on 1,325 tasks × 3 tries | First scorer said **+1.1 pts, p = 6e-5**. Reading answers: 1.2 was right in other spellings (Somwar/Somvar). Content scoring: **0.0 change**. GO. | $14.55 |
| **E3 Contributor mode** | Same model at ~1/18 the price: same quality? | **Identical** (3,971 / 3,975 each). $0.10 vs $1.80 per 1,000 tasks. GO. | $0.40 |

Details and caveats: [findings/LOG.md](findings/LOG.md). Tables: `experiments/out/`.

## What's built
- `upgrade_gate/`: runner (resume, budget stop, cache), Meta API client with a **lifetime spending cap**, 20 deterministic scorers with separate **content vs strict-format** scores, paired stats (McNemar, bootstrap, Holm), gate (exit 0/2/3), reports and exports. 168 tests.
- Task packs: maths, extraction, intent, instructions, invoice images/PDFs, 135 spoken voice notes (+ text twins), real-voice pack.
- `web/`: findings site, **report view** (`#/report/<run>`) and a voice **recorder** (`#/record`). Light and dark.
- Canary suite (50 prompts) and GitHub workflow, ready to switch on.

## Current honest score
| Criterion | Weight | Now | What would raise it |
|---|---|---|---|
| Impact | 30% | 7.5 | a short note from 1–2 other developers who ran it; a crisp "who uses this" line |
| Demo | 25% | 8 | record the video around the report: PR check → voice-note report → one clip |
| Meta tooling | 25% | 8.5 | E6 (Meta's own 1.3 audio warning, measured) + Contributor mode + effort levels |
| Technical depth | 20% | 8.5 | E7 real-voice confirmation; measured gate error rates |
| **Weighted** | | **≈ 8.1** | **8.5+** with E7 confirmed and a sharp video |

## Remaining hypotheses
1. **Judge-version bias (E2)** — a 1.3 judge passes 1.3's mistakes more often. Cheap with Contributor judges (~$0.30).
2. **Reasoning effort isn't monotonic (E4)** — fixed: same 16k token limit at every level, cut-offs counted apart. ~$0.10–1 on Contributor.
3. **Pinned-model drift (canary)** — needs ~8 days of data.

## Open items
- [ ] E7: real-voice confirmation of E6 (lines recorded at `#/record`; run when ready, ≤ $4)
- [ ] E4 pilot, then E2 (both on Contributor, under $2 together)
- [ ] Switch on the canary: GitHub secret `MODEL_API_KEY`, variables `CANARY_MODELS`, `CANARY_BUDGET_USD=8`
- [ ] Decide whether to delete Codex's older `ui/` (the new site is `web/`)
- [ ] Record the 3-minute video ([docs/DEMO.md](docs/DEMO.md))
- [ ] Make the repo public, then submit by the evening of Nov 4 IST

## Schedule (IST)
| Date | Work |
|---|---|
| Oct 28 | E7, E4 pilot, E2. Switch on the canary |
| Oct 29–31 | Fix anything the runs turn up; site polish; ask 1–2 developers to try it |
| Nov 1–2 | Canary summary, final numbers into the site |
| Nov 3 | Record the video |
| Nov 4 | Make public, submit by evening |
