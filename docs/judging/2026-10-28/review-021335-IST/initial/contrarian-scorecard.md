# Independent contrarian scorecard

Judged snapshot A: `29862c5258f9368fdc828f4c6276546b97467eac`; inspected proposed upgrade branch at `92f04d8ede349843172c8ecb96ad9b8d92131708` read-only. Scores fixed independently before consulting previous council scores. This is a solo indie entry: creativity, technical ambition and working behavior count; enterprise readiness and existing traction are not prerequisites. Field is hypothetical, so votes are judgments, not measured ranks.

## Snapshot A

| Criterion | Weight | Score /10 | Evidence and reason |
|---|---:|---:|---|
| Impact | 30% | 7.4 | Concrete release risk: filled-in wrong pincodes evade required-field checks (`README.md:52–55`; `scripts/ci_gate.py:52–76`). Reusable task input exists (`docs/BRING_YOUR_OWN_TASKS.md:8–46`), but current checks replay old evidence (`.github/workflows/upgrade-gate.yml:39–40`; `scripts/ci_gate.py:93–107`); production benefit remains demonstrated on a narrow workload. No traction deduction. |
| Demo | 25% | 7.8 | Compelling one-line upgrade → blocked deployment → audible failing case (`docs/DEMO.md:9–18`), inspectable clip/answer interface (`web/src/components/AudioSection.tsx:107–160`). The prominent real-voice confirmation overstates the item-level finding (`README.md:11`; `web/src/components/AudioSection.tsx:114–134` versus `findings/LOG.md:73`). Recorded video and actual merge protection are not credited (`docs/DEMO.md:20–22`). |
| Meta tooling | 25% | 8.5 | Substantive direct Meta version comparison plus multimodal audio/text twins, Contributor and five effort levels (`README.md:115–121`; `findings/LOG.md:51–55,81`; `experiments/out/e3_contributor.md:7–20`). Unexpected failure-mode shift and worse listening with extra effort justify a high mark; no measured open-weights or agentic outcome is invented. |
| Technical depth | 20% | 8.0 | Majority repeats, exact paired inference, Holm slices and item-cluster behavior are real (`upgrade_gate/stats.py:13–33,66–89`; `upgrade_gate/behaviour.py:78–105,137–189`; `release/policy.json:3–8`). Accuracy still bootstraps task translations separately (`upgrade_gate/gate.py:42–55,65–73`), and automatic blank/wrong/abstain labeling lacks a blinded audit (`upgrade_gate/behaviour.py:43–59`). |
| **Weighted /100** | | **78.95** | 22.2 + 19.5 + 21.25 + 16.0 |

Stage 1: **pass** on genuine Meta use and theme fit (developer release safety, multilingual voice workflows); public-repository eligibility is a separate submission condition, currently recorded as pending (`STATUS.md:18–21`). Top 5: **no**. Top 10: **yes**.

## Snapshot B: only B1–B7 assumed completed

Low assumes the audit exposes meaningful classification disagreements and fresh/more-speaker runs do not give clear corroboration; this can reduce confidence, but lack of significance in a small fresh run is not disproof. High assumes useful agreement and corroborating evidence. Neither scenario includes users, testimonials, engagement or virality. Both get the working live workflow, reusable Action, public repository, required checks, recorded video and posted outreach specified in `request.md:57–65` (B1–B7 table; exact requirements govern over line-number shorthand).

| Criterion | Weight | Low | High | Evidence and conditional reasoning |
|---|---:|---:|---:|---|
| Impact | 30% | 7.2 | 8.2 | B2+B4+B6 remove the handoff gap shown by `scripts/ci_gate.py:93–107` and `docs/BRING_YOUR_OWN_TASKS.md:38–55`; poor B3 agreement reduces trust in what is blocked, while good B3+B5 makes the domain value more convincing. No adoption assumption. |
| Demo | 25% | 8.4 | 8.9 | B1+B2+B6+B7 turn `docs/DEMO.md:9–22` into a completed, public, live demonstration with genuine merge blocking. Low still has a coherent gate story with honestly uncertain science; high adds a clean corroboration moment. B1 does not silently rewrite all LOG/STATUS/script overclaims. |
| Meta tooling | 25% | 8.5 | 9.0 | B2 fresh Meta calls and B5 frozen-rule new speakers deepen the measured use already in `findings/LOG.md:51–55,68–74,81`. Poor replication is useful model knowledge but cannot be advertised as another positive discovery; high corroboration strengthens the finding. No open-weights or agentic bonus invented. |
| Technical depth | 20% | 7.8 | 8.8 | B3 blinded audit, B2 budget-capped collection and B4 reusable integration add real methods. Bad label agreement still harms correctness; good agreement raises confidence. Task-based accuracy CI and multiplicity boundaries in `upgrade_gate/gate.py:22–28,42–73` and `upgrade_gate/behaviour.py:181–189` remain unchanged by B1–B7. |
| **Weighted /100** | | **79.45** | **86.95** | Low 21.6+21+21.25+15.6; high 24.6+22.25+22.5+17.6 |

Stage 1 low/high: **pass/pass**. Public-repository condition B6 is met by assumption, independently of Stage 1. Top 5 low/high: **no/yes**. Top 10 low/high: **shortlist/yes**.

## Statistical and claim audit

1. **Denominators verified from committed evidence:** E6 is 270 tasks: 135 audio plus 135 text twins, each with three repeats per version. Headline 278 versus 274 correct is out of 405 audio responses per version, not 405 independent clips. Behavior headline is a majority flag on 135 audio tasks. The accuracy table has 134 usable audio pairs, because scored API errors are excluded (`experiments/out/e6_audio.md:9,52–59,67`; `upgrade_gate/stats.py:13–27`). No pooled audio+text denominator may be substituted.
2. **E6 is still compelling after clustering.** Read-only `behaviour.check` yields combined wrong+blank 18→42 tasks; discordants 2 baseline-only/26 candidate-only, exact p=0.0000030323863. There are 45 item clusters, with 18 worse/1 better, p=0.0000762939453. Across audio and text modalities the actual behavior gate Holm p=0.0001525878906, so it still flags. Wrong-only is also robust at item level: 14 worse/1 better, p=0.0009765625. This prevents a contrarian from dismissing a real finding because the headline used task-level p (`upgrade_gate/behaviour.py:78–105,173–189`; `findings/LOG.md:73`).
3. **E7 is weaker than the headline and differs from E6.** Forty-five clips are 15 underlying items × three languages, not 45 independent semantic items (`findings/LOG.md:69,73`). Combined wrong+blank 6→13 tasks yields p=.015625, but item signs are 5 worse/0 better, p=.0625. Actual policy therefore does not flag silent failures. Filled-in wrong-only majorities are 6→6; discordants1/1 and item signs1/1, p=1. This is compatible with a meaningful blank-output problem, not confirmation that real speech produces more filled-in wrong answers. E7's existing NO-GO survives via the task-based accuracy CI, not the combined-silent criterion (`upgrade_gate/gate.py:65–70`; `release/policy.json:5–8`). The LOG's earlier 'NO-GO on both counts' is stale (`findings/LOG.md:70,73`).
4. **Blank-only is not an independent-item statistical confirmation either.** E7 has 18 blank response rows out of 135, with majority blank flags on 6 of 45 clips, p=.03125 task-level. Recomputing `_paired` for blank-only with item clusters gives 4 worse/0 better, p=.125. B1's required 'confirmed for blank answers' deserves credit as a narrower descriptive observation; it must not be expanded into 'statistically confirmed after clustering'. Blanks visibly occurred; independence-aware significance is another claim (`experiments/out/e7_real_voices.md:21–28`; classification and cluster algorithm `upgrade_gate/behaviour.py:43–59,78–105`).
5. **Multiplicity and post-hoc claims:** E6 failure taxonomy was chosen after reading outcomes (`findings/LOG.md:93`); frozen E7 mitigates that but does not fix correlated translations. Accuracy Holm correction covers category/language/modality slices; behavior has its own modality family. Neither is one global correction across every experiment, endpoint and release decision. This is acceptable exploratory hackathon engineering if labeled; it is not a demonstrated overall 5% false-block guarantee. Accuracy CIs are explicitly pointwise and fixed-horizon (`upgrade_gate/gate.py:22–28`; `README.md:127–129`).
6. **E4 effort data:** cutoff-as-failure percentages 72.8,68.9,64.2,63.7,58.5 are indeed monotonically decreasing. Finished-answer accuracy is 72.8,69.1,64.8,66.0,61.1, so it is not monotonic on that endpoint. Same16000-token limit is used, but high effort still cuts off more; endpoint p=.0009 is selected after seeing results, not evidence that every adjacent step is significant (`experiments/out/e4_effort.md:5–28`; `findings/LOG.md:51–55`; `web/src/components/EffortSection.tsx:113–116`). Good disclosure already exists; don't deduct as if concealed. It remains a strong Meta-specific exploratory trend, not a universal minimal-effort recommendation.
7. **Other headline precision:** E3 records identical task majority pass outcomes, not proof that every raw textual answer is identical (`experiments/out/e3_contributor.md:7–20` versus `README.md:13`; `web/src/components/Hero.tsx:45`). E2 correctly bounds its result to reference-given grading and 249 wrong answer rows, with repeated observations acknowledged (`experiments/out/e2_judge_version.md:11–23`; `findings/LOG.md:59–62`). Zero false passes is not a measured universal absence of bias.
8. **Upgrade branch isn't the latest policy tree.** Read-only diff at the pinned commits shows `release/policy.json` absent on the upgrade branch plus older behavior/CI code. The branch is a real candidate change, but its exact checks cannot be assumed to execute A's newly hardened main policy. B2 being 'shown working on the upgrade PR' receives its stipulated mechanism credit; B does not imply all unrelated branch code has been reconciled.

## Three strengths

- Memorable, meaningful failure distinction; E6 survives an appropriately skeptical cluster analysis.
- Substantial Meta investigation across versions, modalities, serving mode and effort rather than a thin API wrapper.
- Auditable saved answers and explicit scorer false start; actual policy code is more careful than the promotional headline.

## Three weaknesses

- E7 confirmation wording outruns the item-level evidence, including blank-only significance if interpreted strictly; several surfaces still tell the older story.
- Live collection/reusable integration/video/merge protection are projected for A, and the pinned upgrade branch has stale policy code.
- Statistical assurance remains partial: task-level accuracy CI with correlated translations, separate test families, post-hoc endpoints, and unaudited automatic failure labels.

Single highest-return next action: reconcile the README/site/demo/LOG with the actual frozen item-level policy and put the precise E6 robust result plus the E7 blank observation/borderline combined result in the same visible evidence panel. This preserves the compelling discovery while removing an easy credibility attack; B1 only partially specifies that reconciliation.

## Verification boundary and commands

Only read-only git/rg/nl/cat inspection and local pure analysis were performed. No keys, network API, paid calls, tests/builds, release changes or commits. Executor owns tests/build/replay and browser validation. I inspected current web source; I did not independently claim browser behavior. Analysis commands used `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python` importing `behaviour.check`, `answer_type`, `_paired`, reading saved evidence, and printing combined, wrong-only and blank-only clustered results. Those functions do not write gate artifacts. Evidence authenticity is consistent with recorded model metadata; no independent provenance attestation claimed.

## Previous comparison after independent scoring

Previous rubric totals supplied by the request: Impact7.2, Demo7.9, Meta8.1, Technical7.8, chair77. A here:7.4,7.8,8.5,8.0, weighted78.95. Main gain is concrete policy/PR workflow and strong Meta-specific results; demo slips0.1 because prominent E7 wording still contradicts the stronger code. Different judge/lens scores are not a causal measurement of project progress. No previous score was used as a target.

Revision status: initial independent scorecard; awaiting two anonymous peer reviews. All judges share one model family, limiting independence.
