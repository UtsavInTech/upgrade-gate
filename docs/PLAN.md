# Plan to submission (28 Oct → 4 Nov 2026, IST)

> Superseded by [docs/plan/](plan/README.md) (28 Oct 2026). Kept for history.

Deadline: Nov 4, 9:00 PM ET = **Nov 5, 7:30 AM IST**. Treat **Nov 4, 9 PM IST** as the real cut-off.
Where we stand: council #2 scored **79/100** (top-ten from all 5 judges, top-five from none); with the planned work
done, **82–88** depending on outcomes. Since then: PR #1 verified on GitHub, live mode working (60/60 real calls),
claims corrected, strict budget, label-audit page, reusable Action.

The council's top-five package is: a verifiable blocked upgrade (done), honest claims (done), **validated labels and
more speakers** (open), a **clear video** (open), and **public repo + required checks** (open). Everything below
serves those. No new experiments or UI redesigns unless a step below needs them.

## Who does what

| # | Task | Owner | Time | Moves | Day |
|---|---|---|---|---|---|
| 1 | **Label audit**: label the 60 answers at `#/audit`, then `python3 scripts/audit_report.py` | you → me | 15 min + 10 min | Technical depth | Oct 28 |
| 2 | Put the audit result (κ, disagreements) on the site, README and findings; fix any rule the audit shows is wrong, then re-run the gates | me | 1 h | Technical depth | Oct 28–29 |
| 3 | **More speakers**: 2–3 people each read the 45 lines at `#/record` (different accents, phone mic is fine) | you + friends | 10 min each | Technical depth, Meta tooling | Oct 29–30 |
| 4 | **E7b**: rerun the frozen real-voice test on all speakers (~$1.50, cap $4); report it whatever it shows, grouped by item | me | 30 min | Technical depth | after #3 |
| 5 | ✅ **Canary on** (first run 28 Oct 15:56 IST: 300 answers, 0 errors, $0.21; ~$0.85/day). Was: **Switch on the canary** (pinned-model drift over days): repo variables `CANARY_MODELS=muse-spark-1.3,muse-spark-1.3-contributor`, `CANARY_BUDGET_USD=8` (secret already set) | you (2 min) | — | Meta tooling | **Oct 28** (needs days of data) |
| 6 | **Make the repo public**; branch protection on `main` requiring the 3 `upgrade-gate / …` checks → PR #1 shows *Merging is blocked* | you | 5 min | Demo, eligibility | Oct 30 |
| 7 | Publish the site (GitHub Pages from `web/dist`, workflow) so judges can click it without running anything | me | 45 min | Demo | after #6 |
| 8 | Third judging council (`docs/judging/COUNCIL_PROMPT.md`) as a checkpoint; fix the top 2 findings | you run, me fix | 1 h | all | Nov 1 |
| 9 | Canary summary into the site (does a pinned model drift? report even "no drift") | me | 45 min | Meta tooling | Nov 2 |
| 10 | **Record the 3-minute video** per `docs/DEMO.md` (PR checks → summary → clip grid → real voice → effort → scorer lesson) | you | 2–3 h | Demo | Nov 2–3 |
| 11 | Submission text (problem, what it does, findings with caveats, Meta tooling used, how built, links) | me draft, you edit | 1 h | all | Nov 3 |
| 12 | Discord ask + X thread (`docs/OUTREACH.md`); one real outside user if anyone tries it, otherwise say so | you | 30 min | Impact | Nov 3 |
| 13 | Final check: fresh clone → install → tests → PR replay → site build; links work while logged out; no secrets in repo | me | 30 min | — | Nov 4 AM |
| 14 | **Submit** | you | 15 min | — | **Nov 4 evening** |

## Cut lines (if time runs short, drop from the bottom up)

1. Keep: 1, 2, 6, 10, 11, 13, 14. These alone make a solid top-ten entry.
2. Then: 3, 4 (more speakers): the single biggest lift on the council's weakest point.
3. Then: 5, 9 (canary), 7 (hosted site), 8 (council), 12 (outreach).

## Spending

Spent so far ≈ $20 of the $90 cap (plus ~$0.13 per PR push in CI). Planned: E7b ≈ $1.50, canary ≤ $8, live PR checks
≈ $0.13 each. Expected total by submission: **≈ $30**.

## Risks

| Risk | What we do |
|---|---|
| Audit shows weak agreement on "says it can't answer" vs "wrong" | Report κ honestly, tighten the rule, re-gate, show before/after. A found-and-fixed flaw is credible |
| More speakers don't confirm the silent-failure rise | Report it; the claim narrows to synthetic voices + accuracy drop on real voice. Don't rerun until it "works" |
| Repo public exposes something private | Recordings are gitignored and never exported; final secret scan in step 13 |
| Video runs long | Cut the scorer and Contributor beats first; keep PR → summary → one clip → real voice |
| Live PR check spends on every push | It's capped at $1/run (~$0.13 actual); stop pushing to the PR branch after the video is recorded |
