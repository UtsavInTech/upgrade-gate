# 4. Day by day (29 Oct → 4 Nov 2026, IST)

Cut-off: **Nov 4, 9 PM IST** (official deadline Nov 5, 7:30 AM IST).

| Day | You | Me | Done when |
|---|---|---|---|
| **Wed 29 Oct** | L1 label audit (15 min). Ask 2–3 people to record (L3) | L2 audit → site. A1 static VoiceOrder | κ on the site; VoiceOrder works with the server off |
| **Thu 30 Oct** | L5 repo public + branch protection (5 min). Enable Pages | A2 Pages workflow. A3 PR comment | Public link opens the site; PR #1 has a gate comment and says "Merging is blocked" |
| **Fri 31 Oct** | Collect recordings | B1 comparison section. L4 E7b as soon as recordings arrive | E7b result in LOG and on site, whatever it shows |
| **Sat 1 Nov** | Run council #3 (C3) | B2 `upgrade-gate init` + demo repo | A second repo gated with `init` |
| **Sun 2 Nov** | Video rehearsal | B3 canary drift; fix council findings | Canary section live |
| **Mon 3 Nov** | **Record the video** (L7). Outreach (C4) | L8 submission draft; C1, C2 polish | Video uploaded (unlisted), draft ready |
| **Tue 4 Nov** | Edit submission; **Submit by evening** (L10) | L9 fresh-clone check in the morning | Submitted |

## If time runs short (drop from the bottom)

1. Keep: L1, L2, L5, A1, A2, L7, L8, L9, L10 → solid top-ten entry.
2. Then: L3 + L4 (more speakers), A3 (PR comment).
3. Then: B1, B2, B3, C1–C4.

## Money

Spent ≈ $22.93 of $90. Planned: E7b ≈ $1.50 · B2 demo ≈ $0.15 · live PR checks ≈ $0.13 each · canary ≈ $0.85/day
(≈ $6 to Nov 4). **Expected total ≈ $32.** Hard ceiling stays $100.

## Risks

| Risk | What we do |
|---|---|
| Audit shows our labels are often wrong | Report κ, tighten the rule, re-gate, show before/after. A found-and-fixed flaw is credible |
| Friends don't record in time | Ship with one speaker and say so; the synthetic result (E6) still stands |
| E7b doesn't confirm | Report it. The claim narrows to "synthetic voices + accuracy drop on real voice" |
| Public repo leaks something | Recordings are gitignored and never exported; secret scan in L9 |
| Video runs long | Cut scorer and Contributor parts first; keep VoiceOrder → PR → one clip → real voice |
