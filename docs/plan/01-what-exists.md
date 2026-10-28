# 1. What Upgrade Gate does today (28 Oct 2026)

One line: **before you switch your app from Muse Spark 1.2 to 1.3, Upgrade Gate replays your own tasks on both,
checks how the new model fails, and blocks the pull request if it fails quietly more often.**

## The product

| Part | What it does | Where |
|---|---|---|
| **Gate (CLI)** | `upgrade-gate run / score / gate / report`: runs tasks on two models, 3 tries each, scores every answer against a known result, decides GO / NO-GO / INCONCLUSIVE (exit 0 / 2 / 3) | `upgrade_gate/cli.py` |
| **Failure-type check** | Sorts every wrong answer into: says it can't answer, no answer, blank, wrong with no warning. Blocks if blank + wrong-with-no-warning rises | `upgrade_gate/behaviour.py` |
| **Careful statistics** | Paired comparison per task, exact McNemar, item-level sign test (en/hi/Hinglish of one note grouped), bootstrap range, Holm correction across input types | `upgrade_gate/behaviour.py`, `stats.py` |
| **Release policy** | One JSON file says which failures count, how much rise is allowed and why (written for the voice-order shop) | `release/policy.json` |
| **Scoring** | Content score (Hindi spelling folded) and strict-format score, so a formatting quirk can't fake a gain | `upgrade_gate/scorers.py` |
| **Spending safety** | Lifetime cap ($90, hard ceiling $100), per-run budget that reserves each call's worst case before sending, canary budget | `upgrade_gate/spend.py` |
| **Bring your own tasks** | Any `.jsonl` file of tasks works | `docs/BRING_YOUR_OWN_TASKS.md`, `examples/my_tasks.jsonl` |

## In GitHub

| Part | What it does |
|---|---|
| **PR check** (`.github/workflows/upgrade-gate.yml`) | Any PR that changes `release/model.json` runs three checks: voice-notes, real-voices, text-and-documents (replay from saved evidence, $0) plus a live sample (10 clips, real calls, ≤ $1) |
| **Reusable Action** (`action.yml`) | Other repos can add `uses: UtsavInTech/upgrade-gate@main` with replay or live mode |
| **PR #1** | "Upgrade to Muse Spark 1.3": voice-notes ❌, real-voices ❌, text ✅, live sample ✅ (inconclusive). The real blocked upgrade |
| **Canary** (`canary.yml`) | 4× a day, pinned 1.3 and 1.3 Contributor, checks if the same model drifts over days ($10 budget, ~$0.85/day) |

## Task packs (all with known answers)

math-pairs, extract-pairs, intent, ifeval (text, en/hi/Hinglish) · docs-synth (images, PDFs) ·
audio-synth (135 spoken clips + text twins) · audio-real (your 45 recordings, private) ·
audio-corrections (E8: 90 clips + your 15 correction takes) · canary.

## What we found (findings/LOG.md)

| # | Finding | Strength |
|---|---|---|
| E6 | Synthetic voices: 1.3 fails silently far more (18 → 42 of 135 clips; by item 18 vs 1, p = 0.00008). Gate says NO-GO | Strong |
| E7 | Your real voice: accuracy −11 pts (CI −20 to −2) and blanks appear (0 → 6). Silent-failure rise borderline by item (p = 0.06) | Medium, one speaker |
| E4 | More reasoning effort makes 1.3 worse at listening (72.8% → 58.5%) | Post hoc |
| E3 | Contributor mode: same pass/fail at 1/18 of the cost | Strong |
| E2 | No judge-version bias when the judge has a reference answer | Strong |
| E1 | A scorer artefact invented a +1.1 pt "gain"; fixed | Lesson |
| E8 | Self-corrections: not confirmed as a separate problem. On your voice 1.3 got 1 of 15 correction notes right vs 9, mostly blanks, but your plain notes show a similar gap | Negative result, reported |

## The website (`web/`, Vite + React, light/dark)

| Page | What it shows |
|---|---|
| `#/` home | PR-checks panel ("Merging is blocked"), audio findings, clip grid, effort, scoring lesson, cost, how it works |
| `#/report/<run>` | Full report per run, click any task to see both answers |
| `#/voiceorder` | **VoiceOrder**, the demo shop app: a Hindi/Hinglish voice note → order. Side-by-side 1.2 vs 1.3: CORRECT ORDER SAVED / WRONG ORDER SAVED / ASKS THE CUSTOMER / ORDER LOST. Record your own note live |
| `#/record`, `#/record/corrections` | Record real voice lines (saved privately) |
| `#/audit` | Blind 60-answer label check (are our failure types right?) |

## Numbers

190 tests passing · ≈ $22.93 spent of $90 · 1 speaker recorded (you, 60 lines) · label audit not done yet.
