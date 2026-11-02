# Upgrade Gate — Current Status

_Last updated: Nov 2, 2026 (IST). Phase: **built, deployed, ten experiments done; video and submission left**._

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
- **Repo must be public at submission.** Public since 28 Oct.
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

## Results so far (all from real API runs, $26.93 spent of a $90 cap)
| Run | Question | Result | Cost |
|---|---|---|---|
| **E6 voice notes** | Does 1.3 listen worse than 1.2 (Meta's docs warn about 1.3 audio)? | Same accuracy (278 vs 274 of 405), but answers that are **wrong or blank with no warning rose 18 → 42 of 135 clips, p = 3e-6**. 1.2 often says "I can't hear the audio" (21 tasks by the gate's labels, 23 by E6's own pattern); 1.3 never does. Accuracy-only gate: INCONCLUSIVE (~9,000 more clips needed). | $3.34 |
| **E1 text, docs, Hindi** | 1.2 → 1.3 on 1,325 tasks × 3 tries | First scorer said **+1.1 pts, p = 6e-5**. Reading answers: 1.2 was right in other spellings (Somwar/Somvar). Content scoring: **0.0 change**. GO. | $14.55 |
| **E7 real voice** | Does E6 hold with a person's voice? (pre-registered) | **Partly.** Accuracy −11 pts (gate NO-GO); blank clips 0 → 6. Wrong-or-blank 6 → 13 per clip (p = 0.016) but borderline by item (5 vs 0, p = 0.06). | $0.78 |
| **E4 effort ladder** | Is more reasoning effort ever worse? | **Yes, on voice clips:** 72.8% (minimal) → 58.5% (xhigh), p = 0.0009; "can't hear" 0 → 44; 6× the cost. Post-hoc. Text: 100% at every level. | $0.64 |
| **E2 judge bias** | Does a judge go easy on its own version? | **No** (with a reference answer): 0 false passes of ~250 wrong answers for either judge. | $0.06 |
| **E3 Contributor mode** | Same model at ~1/18 the price: same quality? | **Same pass/fail on every task.** $0.10 vs $1.80 per 1,000 tasks. GO. | $0.40 |
| **E8 self-corrections** | Does 1.3 keep a number the speaker took back? (pre-registered) | **Not confirmed.** 1.3 is worse on these notes overall, not because of the correction. | $2.59 |
| **E9 transcribe route** | Is Voice Transcribe → Spark 1.3 a safe upgrade? (pre-registered) | **GO** on 135 synthetic notes (+12.8 pts); real voice INCONCLUSIVE. The gain is from transcription, not 1.3. [PR #2](https://github.com/UtsavInTech/upgrade-gate/pull/2) stays blocked. | ~$2.95 |
| **E10 second speaker** | Does E7 hold for another person? (pre-registered) | New speaker: plain upgrade INCONCLUSIVE, **silent-failure rise did not repeat** (8 → 7); route GO (+4.4). Pooled 90 clips: plain upgrade NO-GO on accuracy (−8.9), route INCONCLUSIVE. | ~$0.70 |

Details and caveats: [findings/LOG.md](findings/LOG.md). Tables: `experiments/out/`.

## What's built
- `upgrade_gate/`: runner (resume, budget stop, cache), Meta API client with a **lifetime spending cap**, deterministic scorers with separate **content vs strict-format** scores, paired stats (McNemar, bootstrap, Holm, item-level test), gate that also checks **how answers fail** (exit 0/2/3), release policy file, reports and exports, `init` for new repos. **196 tests.**
- Reusable GitHub Action (`action.yml`), replay or live mode with a strict spend cap. PR #1 (plain 1.3 upgrade) and PR #2 (transcribe route) are both blocked by it.
- `voiceorder/`: the small voice-order app the gate protects; uses `release/model.json`.
- `web/`: findings site, report view, VoiceOrder page, voice recorder, blind label-audit page. Hosted at https://web-production-00176.up.railway.app (mirror on GitHub Pages).
- Canary suite (50 prompts) and a scheduled workflow (one full real run on 28 Oct).

## Open items
- [x] Repo public; branch protection on `main` requires the three `upgrade-gate / …` checks
- [x] Hosted site with live VoiceOrder (Railway) + GitHub Pages mirror
- [x] Second speaker recorded and run (E10), reported as it came out
- [ ] **Label the 60-answer audit** at `#/audit`, then `python3 scripts/audit_report.py` (κ + disagreements)
- [ ] **Record the 3-minute video** ([docs/DEMO.md](docs/DEMO.md))
- [ ] **Edit and paste the submission text** ([docs/SUBMISSION.md](docs/SUBMISSION.md))
- [ ] Fix the GitHub repo description typos ("go/n-go", "Meta Global I Developer")
- [ ] Optional: post the X thread (`docs/OUTREACH.md`); one outside-user trial, or say plainly there wasn't one
- [ ] Decide whether to delete the older `ui/` (the site is `web/`)
- [ ] Submit by the evening of Nov 4 IST

## Schedule (IST)
| Date | Work |
|---|---|
| Nov 2 | Label audit; docs synced to E10 |
| Nov 3 | Record the video; finalise submission text |
| Nov 4 | Submit by evening |
