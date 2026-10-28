# 2. What is left (must do before submitting)

These close the gaps the judging councils named: **unchecked labels, one speaker, no hosted demo, no video.**
Without them we are a solid top-ten entry; with them, a top-five candidate.

| # | Task | Owner | Time | Why it matters |
|---|---|---|---|---|
| L1 | **Label audit**: label 60 answers at `localhost:5191/#/audit` | you | 15 min | Proves our failure types (blank, wrong, can't hear) are labelled right. Judges' #1 doubt |
| L2 | Audit report → site, README, LOG; fix any rule it shows is wrong, re-run gates | me | 1 h | Turns the audit into evidence (κ score + disagreements) |
| L3 | **2–3 more speakers** record the 45 lines at `#/record` (friends, family, phone mic fine) | you + friends | 10 min each | E7 rests on one voice. More voices = the finding is not about you |
| L4 | **E7b**: rerun the frozen real-voice test on all speakers (~$1.50, cap $4), report whatever it shows | me | 30 min | The strongest possible evidence |
| L5 | ✅ public 28 Oct; branch protection still to do · **Make the repo public** + branch protection on `main` (require the 3 `upgrade-gate / …` checks) | you | 5 min | PR #1 then visibly says "Merging is blocked" to anyone |
| L6 | ✅ live 28 Oct · **Hosted site** on GitHub Pages, including a static VoiceOrder (see 03 → A1) | me | 3 h | Judges click a link instead of installing anything |
| L7 | **3-minute video** (script in `docs/DEMO.md`) | you | 2–3 h | Most judges watch the video first |
| L8 | **Submission text** | me draft, you edit | 1 h | Problem, what it does, findings with caveats, Meta tooling, links |
| L9 | **Final check**: fresh clone → install → tests → PR replay → site build; secret scan; links logged out | me | 30 min | Nothing breaks when a judge tries it |
| L10 | **Submit** | you | 15 min | Nov 4 evening IST |

## How to do the ones that are yours

**L1 — Label audit**
1. Make sure the site runs: in a terminal, `cd web && npm run dev` (port 5191).
2. Open `http://localhost:5191/#/audit`, name `utsav`.
3. For each answer pick: correct / says it can't answer / blank / wrong / unsure. Don't look up our label; it's hidden on purpose.
4. Tell me "audit done". I run `python3 scripts/audit_report.py`.

**L3 — More speakers**
1. Each person opens `http://localhost:5191/#/record` on your laptop (or sends you voice notes of the 45 lines).
2. They type their own name (e.g. `riya`), read each line, Save and next.
3. Ask them first if their recording may be used in a private test; it stays out of the public repo.

**L5 — Public repo**
GitHub → repo → Settings → General → Danger zone → Change visibility → Public.
Then Settings → Branches → Add rule for `main` → Require status checks → tick
`upgrade-gate / voice-notes`, `upgrade-gate / real-voices`, `upgrade-gate / text-and-documents` → Save.

**L7 — Video**
Follow `docs/DEMO.md`. Record with QuickTime (File → New Screen Recording) at 1080p, voice over live.
Order: VoiceOrder (1.3 saves the wrong pincode) → PR #1 blocked → check summary → clip grid → your real voice → how to use it.
