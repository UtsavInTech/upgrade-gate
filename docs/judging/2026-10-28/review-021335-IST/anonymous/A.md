# Anonymous response A

Judged main `29862c5258f9368fdc828f4c6276546b97467eac`; upgrade branch supplied as `92f04d8ede349843172c8ecb96ad9b8d92131708`. Independent initial judgment, before anonymous peer review. Indie solo criteria: creativity, technical ambition, whether it works. No deduction for lacking startup production maturity. No previous council score used as an anchor.

## Snapshot A

| Criterion | Weight | /10 | Evidence and judgment |
|---|---:|---:|---|
| Impact | 30% | 7.1 | Concrete voice-order release risk and an actionable workflow policy (`release/policy.json:2–8`), reusable user task input (`docs/BRING_YOUR_OWN_TASKS.md:8–22,38–47`). No demonstrated outside adoption or observed customer loss. A compelling developer problem, with limited evidence of breadth. |
| Demo | 25% | 8.0 | The source-pinned upgrade → failed checks → exact wrong answer is a strong three-minute narrative (`docs/DEMO.md:9–18`; `scripts/ci_gate.py:125–143`). Viewed both current committed screenshots with `view_image`: clear headline and paired clip visualization. Home's mocked check list includes Contributor mode instead of the actual real-voices matrix (`.github/workflows/upgrade-gate.yml:22–28`); real-voice confirmation wording exceeds grouped combined-silent evidence (`web/src/components/AudioSection.tsx:114–133`). No recorded video verified. |
| Meta tooling | 25% | 8.5 | Real version-pinned direct API study (`evidence/voice-notes/run.json:7,15`; `upgrade_gate/client.py:197–213`), measured Contributor comparison (`experiments/out/e3_contributor.md:5–20`), and five reasoning levels with nontrivial audio/cost reversal (`experiments/out/e4_effort.md:5–11`). E2 is an honest null, not proof of a superior judge (`experiments/out/e2_judge_version.md:9–23`). Strongly beyond a wrapper; no measured Wonder or Open result credited. |
| Technical depth | 20% | 8.0 | Paired majority-vote gate, slice correction, bootstrap intervals and explicit power limits (`upgrade_gate/gate.py:18–28,42–84`); grouped behavior robustness and policy (`upgrade_gate/behaviour.py:220–246`); worst-case spend reservation (`upgrade_gate/spend.py:156–168`). Executor independently reports 178 tests/build PASS and PR replay 2/2/0; I did not rerun those. Present CI replays saved evidence (`scripts/ci_gate.py:93–107`), and label validity remains unaudited. |
| **Weighted /100** | | **78.55** | 21.30 + 20.00 + 21.25 + 16.00 |

Stage 1: **PASS** for theme fit and real Meta use. Multilingual voice workflows plausibly fit Build for Your World and the measured failure-mode/effort reversals fit Push the Frontier. Repository eligibility is separate: parent authenticated verification (`github-readonly.json`) reports private=true, no PRs, no upgrade-gate workflow run and no main rules/protection. It does not yet meet the public-at-submission requirement; new-work eligibility is unverified. Local replay is verified, but a hosted PR/block/deploy skip is not. **Top 5: no. Top 10: yes.** Votes concern a strong hypothetical field, not observed competitors.

### What was actually used

- Versions: committed E1/E6/E7 responses identify Spark 1.2 and 1.3, both low effort. I counted 7,950 text/document, 1,620 voice-note (audio plus text twins), and 270 real-voice response rows, with equal candidates. Counts are calls, not independent tasks. 1.1 preset existence (`upgrade_gate/cli.py:27`) is not an additional measured comparison.
- Contributor: E3 records zero changed task outcomes across 1,325 tasks, including 100 image and 100 PDF tasks (`experiments/out/e3_contributor.md:9–20`). Credit observed equivalence in this easy suite and cost advantage; equal scores do not by themselves prove byte-identical answers or broad equivalence. README's “identical answers” is stronger than the committed result table demonstrates (`README.md:13`).
- Reasoning: all five levels were run on audio, not merely exposed as a setting. With cutoff failures included, 72.8→68.9→64.2→63.7→58.5%; cutoff-excluded scores are not monotonic (64.8→66.0 at medium→high). The important endpoint survives excluded cutoffs (72.8→61.1), so this is more than a token-budget artifact, but do not claim every finished-answer step worsened (`experiments/out/e4_effort.md:7–11,23–25`; `web/src/components/EffortSection.tsx:64–67`).
- Multimodal: text, images, PDFs and audio are present in actual studies; the strongest unexpected finding is audio. Audio risk was already warned about by Meta, so award measurement and operationalization rather than discovery of an undocumented supported capability (`README.md:9`).
- Judges: E2 evaluates reference-grounded Spark 1.2/1.3 Contributor judges: zero false passes on 125+124 wrong answers per judge, with nonzero 4.3% false-fail on 1.2 outputs (`experiments/out/e2_judge_version.md:11–14`). This narrow null does not establish absence of version bias generally.
- Wonder and hosted Spark Open: implemented presets/adapters (`upgrade_gate/cli.py:32,109–123`; `upgrade_gate/judges/llm.py:120–132`), not measured results here. E2 defaults only to two Contributor judges (`experiments/e2_judge_version.py:123–129`). No extra tooling/bonus credit for intended future use.
- E7: one speaker, 45 language clips representing related items (`experiments/out/e7_real_voices.md:3,34–43`). Combined wrong-or-blank grouped comparison is **5 worse / 0 better, p=.0625**, not a behavior-policy flag. Blank-answer result is separately supported. Current real-voices NO-GO comes from the task-level accuracy confidence interval crossing the permitted loss, not a grouped combined-silent confirmation. Its CI still inherits task-unit dependence concerns. Do not upgrade p=.0625 to significance because the PR fails.

### Strengths, weaknesses, next action

Three strengths:
1. Distinctive Meta-specific insight: extra reasoning can degrade listening while raising cost, and unchanged average accuracy can conceal a failure-mode shift.
2. A real developer artifact ties the investigation to a release decision, with inspectable examples rather than a chart-only research story.
3. Measured Contributor economics and multilingual/multimodal coverage make resourcefulness visible without requiring an elaborate agent system.

Three weaknesses:
1. Real-voice “confirmed” communication overstates the combined grouped finding; this damages the credibility of the central Meta insight.
2. One speaker, synthetic/easy tasks, and unmeasured label agreement limit generality; E3 near-ceiling equivalence is not broad serving-mode validation.
3. The current checked-in workflow is saved-answer replay, while the UI suggests a fully operational merge-blocking experience; no verified live fresh-sample check or outside use in A.

Highest-return next action: ship the budget-capped fresh-sample PR run with the grouped-unit interpretation displayed alongside its actual outcome. This makes the Meta integration and release story demonstrably current. A fresh inconclusive/GO outcome must remain visible and honest.

Bonus fit: **open weights: no demonstrated fit** (adapter only); **agentic: weak/no demonstrated fit** (automated evaluation is useful, but no measured autonomous planning/tool-use accomplishment); **viral X: no demonstrated fit** (posting or a shareable chart does not establish virality). These are not deductions from the core four criteria.

## Snapshot B — exactly B1–B7

All seven items below are credited as done as specified in `request.md:57–63`. B1 is editorial clarification, not a new confirmation experiment. No extra users, favorable κ, replication, or social engagement is assumed.

| Criterion | Weight | LOW /10 | HIGH /10 | Evidence and conditional reason |
|---|---:|---:|---:|---|
| Impact | 30% | 7.5 | 8.2 | Reusable Action, protected public PR and extra speakers make the mechanism usable (`request.md:60–62`; existing BYO path `docs/BRING_YOUR_OWN_TASKS.md:38–47`). Low: fresh/new-speaker outcomes weaken generality; high: those measurements corroborate utility. Neither case assumes adoption. |
| Demo | 25% | 8.5 | 9.0 | Exact B1 clarity, B2 shown live, B6 actual merge block, B7 recorded three-minute narrative (`request.md:57–63`; `docs/DEMO.md:9–18`). Low still receives full existence credit, but an inconclusive replication is less decisive for the narrated finding. High has a coherent reproduced finding; no viral reach credit. |
| Meta tooling | 25% | 8.7 | 9.2 | The current measured effort/Contributor/version breadth remains (`experiments/out/e4_effort.md:5–11`; `experiments/out/e3_contributor.md:9–20`), plus genuine fresh Meta calls in PR (`request.md:58`). High rewards stronger demonstrated cross-speaker behavior insight; low credits the integration even if the original effect does not replicate. No Open/Wonder/agentic additions assumed. |
| Technical depth | 20% | 8.4 | 9.0 | Blind ~60-answer audit with disagreements and κ, frozen-rule speaker replication, $1 fresh-run cap and reusable action (`request.md:58–61`) substantially improve evaluation method. Low κ or failed replication constrain demonstrated validity; high agreement/replication strengthens it. Methods are complete in both cases. |
| **Weighted /100** | | **82.40** | **88.10** | Low 22.50+21.25+21.75+16.80; high 24.60+22.50+23.00+18.00. |

Low/high are conditional evidence cases, not confidence bounds and not forecasts. κ and fresh/new-speaker outcomes are unknown; no invented numeric values. Poor audit results could reveal defects whose repair is outside B's exact assumptions.

Stage 1: **PASS** in both cases. B6 assumes public repository and required check protection, but does not independently settle all new-work/event eligibility. **Top 5: LOW no / HIGH yes. Top 10: LOW yes / HIGH yes.**

B strengths: (1) visibly real and cost-limited PR integration, (2) blind labeling plus cross-speaker replication as completed methods, (3) a reusable Action with an honest recorded demo and working protection. B weaknesses: (1) no outside users or engagement, (2) replication and κ can disappoint, (3) the exact additions do not establish open-weights or agentic bonus fit and still concern a narrow workload. B highest-return next action after those additions: respond to the actual blind-audit disagreements before extending claims; if agreement is strong, prioritize a genuinely different external task pack and publish its outcome without assuming success.

Verification boundaries: used only read-only shell inspection and `view_image`; no API, keys, tests, build, release mutation or commits. Read README, STATUS, experiment result tables/JSON keys, evidence counts, workflow, gate/client/spend/behavior paths and demo/BYO docs. Two attempted source lookups (`upgrade_gate/payloads.py`, `upgrade_gate/messages.py`) did not exist; no inference drawn from them. Raw E2/E3/E4 full response-level replay not independently revalidated, so result-table claims carry that limitation. Executor outcomes are explicitly attributed, not claimed as my own commands. No other new judge scorecards read. Parent subsequently supplied authenticated GitHub findings: private repository, no PRs, no hosted upgrade-gate run, no protection/rules. Those findings reinforce the A demo limitation; B2/B6 are still explicitly assumed working in B. Scores remain unchanged because A already credited replay rather than a verified hosted block.
