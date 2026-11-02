# Submission text (draft — edit in your own voice before pasting)

Submit at: cerebralvalley.ai/e/meta-ai-developer-hackathon/hackathon/submit · Deadline: Wed 4 Nov, 9:00 PM ET
(Thu 5 Nov, 7:30 AM IST). Track: Indie developer · Theme: Build for Your World.

---

## Project name
Upgrade Gate

## Tagline (one line)
Before you switch to a new Muse Spark version, check how it fails, not just how often it's right.

## Links
- Live site: https://web-production-00176.up.railway.app (mirror: https://utsavintech.github.io/upgrade-gate/)
- Try the app it protects: https://web-production-00176.up.railway.app/#/voiceorder
- Code: https://github.com/UtsavInTech/upgrade-gate
- The blocked upgrade: https://github.com/UtsavInTech/upgrade-gate/pull/1
- Video: <add link>

## The problem
Small Indian shops increasingly take orders as voice notes in Hindi, Hinglish and English. If an app like that
upgrades its AI model and the new model starts saving the wrong pincode, nobody notices until parcels go to the
wrong address. Most teams decide on an upgrade by checking a pass rate. We found a case where the pass rate
doesn't move but the failures become invisible.

## What it does
Upgrade Gate replays your own tasks on the old and new model, repeats each call, and turns the differences into
GO, NO-GO or INCONCLUSIVE with the failing answers attached. It uses paired exact tests, confidence intervals and
correction across slices (language, input type, task type), and it checks **how** answers fail: a model that says
"I can't hear this" is safer than one that returns a correctly shaped wrong answer. It runs as a GitHub Action:
the pull request that bumps the model fails its check and the deploy step never runs.

We built a small voice-order app, VoiceOrder, as the thing it protects. Upgrading it is a one-line change, and
that pull request is blocked.

## What we found (real Meta Model API runs, $26.93 in all)
- **Voice notes, Spark 1.2 → 1.3 (135 synthetic clips):** same accuracy (278 vs 274 of 405 answers), but answers
  that are wrong or blank with no warning rose from 18 to 42 clips (p = 3 × 10⁻⁶). 1.2 often says it can't hear
  the clip; 1.3 never does. An accuracy-only gate calls this INCONCLUSIVE.
- **Real voices (two speakers, 90 clips, predictions written down before each run):** accuracy fell 8.9 points,
  so the gate says NO-GO. The silent-failure rise did **not** repeat for the second speaker, and we say so.
- **A safe route:** Muse Voice Transcribe first, then Spark 1.3, passes the gate on synthetic notes (+12.8 points)
  and on the new speaker (+4.4). Pooled real voices are still inconclusive, so that pull request stays blocked too.
- **More reasoning, worse listening:** on voice clips 1.3 went from 72.8% right at minimal effort to 58.5% at
  xhigh, at 6× the cost (a post-hoc comparison).
- **Contributor mode:** same pass/fail as Standard on all 1,325 text tasks, at $0.10 vs $1.80 per 1,000.
- **We caught our own mistake:** our first scorer reported a significant Hindi gain for 1.3. It was spelling
  (Somwar vs Somvar). With content scoring the change is zero.

## How we use Meta's models
- **Muse Spark 1.2 and 1.3** via the Meta Model API: the models under test, across text, images, PDFs and audio.
- **Reasoning-effort levels** (minimal → xhigh): measured as a release variable, not a fixed setting.
- **Contributor mode** (`-contributor` model IDs): measured for quality, not just price.
- **Muse Voice Transcribe:** the second stage of the upgrade route that passes the gate.
- **Spark 1.2 and 1.3 as judges:** tested for bias toward their own version (none found with a reference answer).
- The surprise: Meta's docs warn that 1.3 audio is "not fully supported". We measured what that means in practice:
  not lower accuracy, but fewer admissions that it hasn't understood.

## How it's built
Python package (`upgrade_gate/`: runner with resume, cache and a lifetime spending cap; deterministic scorers;
paired statistics; gate; reports; exports to pytest and Promptfoo), a reusable GitHub Action, a React + Vite site,
and the VoiceOrder app. 196 tests. Every experiment from E7 on was pre-registered in `findings/LOG.md` before it ran.

## Limits (we'd want a release owner to read these)
- Single-turn tasks only; no agent or tool-use replay.
- Real-voice evidence is two speakers and 15 scripted items.
- The blind label audit of our failure-type labels: <fill in after the audit: κ and disagreements, or "not completed">.
- No outside team has run it on their own workload yet.

## Built during the event
All code, data and results were made from 27 Oct 2026 onward. Utsav designed the study and ran the experiments;
Claude Code and Codex helped write code.
