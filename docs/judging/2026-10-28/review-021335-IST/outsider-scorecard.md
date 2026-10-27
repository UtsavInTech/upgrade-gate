# Independent judge: Outsider

Judged A at `29862c5258f9368fdc828f4c6276546b97467eac`; upgrade branch supplied as `92f04d8ede349843172c8ecb96ad9b8d92131708`. Lens: non-ML judge with five minutes, indie solo track; creativity, ambition and demonstrated function. No customer or production-maturity prerequisite. Scores below were set independently, without using the old 77 as an anchor.

Read-only inspection: README, STATUS, findings log, E3/E4/E6/E7 experiment tables, evidence run metadata, policy/workflow/CI entry point, behavior/stats/gate code, current `web/` source, demo and BYO docs. Visually inspected `web/screenshots/home.png` and `web/screenshots/report.png` using view_image. Did not judge `ui/`. Did not run tests, build, PR replay, paid calls, browser interactions or API-key actions: executor owns runtime verification. Thus functional confidence here is source/evidence-based and subject to executor results; screenshots are committed images, not a live browser check.

## A: as built

| Criterion | Weight | /10 | Evidence and judgment |
|---|---:|---:|---|
| Impact | 30% | 7.6 | An immediately intelligible developer risk: a plausible-looking wrong pincode can be stored despite passing a schema check (`README.md:52–55`, `release/policy.json:2`). BYO JSONL and commands make the tool usable beyond this experiment (`docs/BRING_YOUR_OWN_TASKS.md:8–22,38–56`). Scope remains known-answer, single-turn tasks (`README.md:125`); this limits reach, without imposing startup traction standards. |
| Demo | 25% | 8.1 | The home headline is clear (`web/src/components/Hero.tsx:60–66`); the paired colored clip grids in `web/screenshots/report.png` make one memorable moment, and the proposed wrong-pincode beat is strong (`docs/DEMO.md:9–13`). The actual video is outstanding (`STATUS.md:97`). Trust is weakened by “Confirmed with a real voice” on the front door (`README.md:11`) while the item-grouped result is borderline (`findings/LOG.md:73`), and the site mock checks include Contributor rather than matching the actual three workflow checks (`Hero.tsx:38–47`, `.github/workflows/upgrade-gate.yml:28`). |
| Meta tooling | 25% | 8.5 | Actual version-specific multimodal investigation, not a generic API wrapper: audio-only results (`experiments/out/e6_audio.md:48–74`), a five-level effort ladder (`experiments/out/e4_effort.md:5–11`), and measured Contributor equivalence and cost (`findings/LOG.md:41–44`). “More thinking, worse listening” is a second memorable surprise. No extra credit for unmeasured open-weights paths (`README.md:119,130`). |
| Technical depth | 20% | 8.2 | Repeated answers become task votes and exact paired inference (`upgrade_gate/stats.py:13–33`); related items are grouped for the policy's behavior test (`upgrade_gate/behaviour.py:149–177`; `release/policy.json:8`). Policy flows into a failing CI exit and evidence example (`scripts/ci_gate.py:103–145`). Valuable machinery with inspectable outputs. The checked-in workflow replays evidence (`.github/workflows/upgrade-gate.yml:3–6,39–40`), and human labeling remains unaudited (`STATUS.md:99`); no claimed runtime pass from this judge. |
| **Weighted /100** | | **80.65** | `7.6×3 + 8.1×2.5 + 8.5×2.5 + 8.2×2 = 80.65`. |

Stage 1: **theme PASS; genuine Meta use PASS; overall Stage 1 PASS** (`STATUS.md:20–21`; real pinned model metadata in `evidence/real-voices/run.json:4–19`; domain-specific spoken English/Hindi/Hinglish orders in `findings/LOG.md:69`). Separate submission-readiness caveat: repository publicity is outstanding (`STATUS.md:18,98`), not a reason to falsely fail theme/Meta eligibility. Top 5: **no**. Top 10: **yes**. The visual evidence story is stronger than an average developer demo, but an unrecorded video plus contradictory real-voice phrasing keeps it below my strong-field finalist threshold.

## B: exactly B1–B7 completed

Bounds are judgment scenarios, not probabilities. Low: fresh samples fail to strengthen the central result, label agreement is weak and speaker effects vary; report them honestly. High: outcomes are useful and consistent enough to strengthen confidence, but no numerical κ, new significance level, replication success, external users or engagement is presumed. The high endpoint is conditional, not an assertion those outcomes occurred.

| Criterion | Weight | Low /10 | High /10 | Evidence and permitted credit |
|---|---:|---:|---:|---|
| Impact | 30% | 7.9 | 8.6 | B4's reusable action and B6's real required checks improve practical reach even if no one adopts it (`request.md:60,62`; present BYO base at `docs/BRING_YOUR_OWN_TASKS.md:38–56`). B2/B3/B5 create additional evidence but outcomes can weaken confidence (`request.md:58–61`). No traction credit from B7. |
| Demo | 25% | 8.5 | 8.7 | B6 supplies the authentic “Merging is blocked” moment; B7 supplies an actual three-minute video of the existing script (`request.md:62–63`, `docs/DEMO.md:9–18`). B1 repairs README/site caveats (`request.md:57`). However, the script still says “It held: 6 to 13” at 1:45 (`docs/DEMO.md:14`) and concludes a general minimal-effort recommendation (`docs/DEMO.md:15`); B1 does not rewrite that script, and B2's fresh sample does not promise a red check. No imagined polished results. |
| Meta tooling | 25% | 8.6 | 8.9 | B2 makes real Meta calls part of the demonstrated PR workflow; B5 extends actual speech collection; their existence deepens the integration (`request.md:58,61`) over the existing version/mode/effort evidence (`findings/LOG.md:41–55`). Outcomes remain unknown, no open-weights deployment or agentic system invented. |
| Technical depth | 20% | 8.4 | 9.0 | B2 live budget-capped workflow, B3 blind audit with disagreement disclosure, B4 packaging, and B6 branch protection complete meaningful engineering and measurement gaps (`request.md:58–62`). Useful method credit even in a weak-outcome case; only high-case confidence from potentially useful audit/fresh-speaker evidence. Existing paired/grouped methods support it (`upgrade_gate/behaviour.py:173–189`). |
| **Weighted /100** | | **83.25** | **87.75** | Low: `23.7+21.25+21.5+16.8`; high: `25.8+21.75+22.25+18`. |

Stage 1 low/high: **theme PASS; genuine Meta use PASS; overall PASS/PASS**. Public-repo readiness additionally resolved by B6. Top 5 low/high: **no / yes**. Top 10 low/high: **yes / yes**. High-case yes is conditional on stronger evidence, not on viral engagement or paying customers. The specified video already has a compelling sequence, but the exact script prevents a 9+ demo assumption.

## Three strengths

1. A non-ML viewer can remember one failure: the correct-looking wrong pincode, then the red PR check (`docs/DEMO.md:10–13`; `scripts/ci_gate.py:137–143`).
2. Visual pairing makes evidence inspectable: same clips on each side, actual audio and answers available (`web/screenshots/report.png`; `web/src/components/TaskDrawer.tsx:73–77`).
3. It exposes its own scorer mistake, adding credibility and a distinct evaluation lesson (`README.md:28–36`; `findings/LOG.md:26–34`).

## Three weaknesses

1. Front-door and video language compress a borderline grouped real-voice finding into confirmation; caveats are buried (`README.md:11`, `docs/DEMO.md:14`, versus `findings/LOG.md:73`). B1 fixes only part of this.
2. Three audiences/stories compete in three minutes: deployment gate, research discoveries, and scorer debugging; Contributor arrives with ten seconds of explanation (`docs/DEMO.md:14–18`). It risks feeling like a report site rather than a tool someone can apply tomorrow.
3. As built, the fresh-call upgrade mechanism, reusable action, recording and true merge protection are incomplete (`.github/workflows/upgrade-gate.yml:3–6,39–40`; `STATUS.md:97–100`). These are concrete demo/adoption gaps, not an insistence on production maturity.

Highest-return next action: **make one honest, evidence-linked video of the actual blocked PR and one playable wrong-pincode case, with the grouped E7 caveat in the spoken line**. It moves Demo first and Impact second; use the current script's 0:00–1:45 spine (`docs/DEMO.md:9–14`), but replace blanket “It held” with “blank answers confirmed; grouped wrong-or-blank evidence is borderline.” No fresh model result is required to tell that true story.

Independent initial scores saved before peer review. Peer review and one possible revision to follow.
