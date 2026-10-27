# Neutral judging council — two snapshots
Judged 2026-10-28 02:27:11 IST. Indie solo entry.

**Chair verdict: A = 79/100. B = 82.06–87.70/100, conditional on the unknown audit and fresh/more-speaker outcomes.** A earns a top-ten selection vote from all five judges, not a top-five vote. In B, only the favorable evidence case earns five top-five votes. These are demanding hypothetical-field judgments, not predictions about the unseen entrants.

## Snapshot and independence
- Main commit: `29862c5258f9368fdc828f4c6276546b97467eac`.
- Upgrade branch: `upgrade/spark-1.3` at `92f04d8ede349843172c8ecb96ad9b8d92131708`; merge-base `b92153a34d1715520fa9f4aee643c81829576b5f`. Its actual three-dot diff changes only `release/model.json` from1.2 to1.3. Comparing its whole older tree to newer main is not evidence of PR deletions.
- Tracked working tree matched the pinned main commit at start and after verification. Only this judging output was added. The allowed temporary model-file change was byte-restored; isolated branch replay used a disposable archive, not a checkout over the active repository.
- Five fresh independent judging contexts, then each judge anonymously reviewed exactly two other initial cards and made at most one opinion revision. The concurrency ceiling allowed three subagents at once, so both phases ran in waves. All five share one model family and evidence corpus; agreement is not independent human validation.
- No loyalty credit for prior collaboration, effort, agent count, code volume or replacing the old UI. The current `web/` site was judged; the superseded `ui/` design was not. No product fixes, Meta API calls, API-key setting, paid model runs, commits or remote changes were made.
- Official public event page independently supports the indie emphasis on creativity, technical ambition and whether the submission works; startup production readiness is a different track. The numerical30/25/25/20 weights are used as instructed from the team rules in STATUS, not claimed independently visible on the retrieved public page. Source: [public event page](https://cerebralvalley.ai/e/meta-ai-developer-hackathon).

## Stage 1 and submission eligibility
**A and B: Stage1 PASS for theme fit and real Meta use, five of five judges.** The multilingual voice-order workflow and measured model behavior fit the supplied themes, and committed response/model metadata supports real Meta use. This is not an attestation of every event eligibility condition or new-work provenance.
**A is not public-submission-ready:** the authenticated repository lookup returned private=true. Publicity and required branch protection are separate from passing theme/model-use screening. B6 explicitly satisfies those conditions by assumption. We do not impose startup customer traction or enterprise maturity as an indie prerequisite.

## Verification ledger
| Verification | Observed result | Boundary |
|---|---|---|
| Python suite on pinned main |178 passed, exit0,25.76s|Existing environment; no installs/model calls|
| `npm --prefix web run build` |TypeScript + Vite pass, exit0|Build success is not a recorded demo video|
| Main local replay: voice-notes |exit2, NO-GO|Behavioral item test causes veto|
| Main local replay: real-voices |exit2, NO-GO|Grouped combined silent test not flagged; accuracy CI supplies veto|
| Main local replay: text-and-documents |exit0, GO|Saved known-answer evidence|
| Actual upgrade branch in isolated archive |Same exits2/2/0|Older behavior logic; not the latest policy tree|
| Live site `http://127.0.0.1:5191` |Opened home/report; readable clip grid, playable-clip controls and answer examples present|No video or external user engagement verified; chair did not independently re-transcribe every recording|
| Model config after verification |Original bytes restored, git diff empty|No model upgrade was left applied|

Full executor commands/stdout are in `review-021335-IST/executor-commands.json`. Root branch commands/stdout are in `branch-replay.json`. A first isolated-branch setup attempt accidentally resolved the virtualenv executable symlink to bare system Python and could not import numpy; the corrected venv-path replay passed expected codes. That setup mistake is retained in `branch-replay-setup-attempt.json` and is not charged as a project failure. Temporary generated branch artifacts were discarded. Main reports/gates were generated only in the temporary runner directories.

### Hosted PR verification — not established
Read-only authenticated GitHub GETs verified the private repo and upgrade branch. With the available credentials, `/pulls?state=all&per_page=100` returned an empty list; Actions returned only two failed canary runs, not an upgrade-gate run. Main branch rules returned an empty list, and the protection endpoint returned404. The chair asked for a direct PR URL; the user directed us to inspect the branch, which we did. No accessible PR URL/run was supplied or found.
**Therefore A receives credit for a working local replay and checked-in workflow, not for an independently verified hosted red PR, completed deploy-skipped run or enforced merge block.** This is a verification limitation, not an accusation about intent. The workflow deploy step is also an echo/template placeholder, not an external application deployment (`.github/workflows/upgrade-gate.yml:45–58`). B2 and B6 receive their explicitly stipulated working-hosted-mechanism credit. Redacted observations: `review-021335-IST/github-readonly.json`.

## Five final scorecards
| Judge | A /100 | B low | B high | A top5 | A top10 | B top5 low/high | B top10 low/high |
|---|---:|---:|---:|---|---|---|---|
|contrarian|78.65|79.45|86.95|no|yes|no/yes|shortlist/yes|
|first-principles|79.50|83.30|88.60|no|yes|no/yes|yes/yes|
|outsider|79.95|82.00|87.80|no|yes|no/yes|yes/yes|
|opportunity|78.55|81.20|86.75|no|yes|no/yes|yes/yes|
|executor|78.35|84.35|88.40|no|yes|no/yes|yes/yes|

A weighted mean **79.00**, judge range **78.35–79.95**. B low-case mean **82.06**, judge range **79.45–84.35**; B high-case mean **87.70**, judge range **86.75–88.60**. Score spreads are subjective disagreement, not confidence intervals, ranking probabilities or percentiles. Totals were recomputed from criterion marks; arithmetic slips in initial prose are retained in the transcript rather than silently treated as different judgments.

## Criterion progress: previous → A → B
| Criterion | Weight | Previous /10 | A /10 | B low–high /10 | What drove the change |
|---|---:|---:|---:|---:|---|
|Impact|30%|7.20|7.44|7.64–8.42|Policy-defined wrong-pincode consequence, portable evidence and BYO path improve concrete utility. B adds distribution/live integration and more evidence, not invented customers or traction.|
|Demo|25%|7.90|7.74|8.48–8.82|The assessment fell slightly despite a clearer UI: the asserted hosted PR is unverified and E7 confirmation language exceeds the grouped result. B supplies the actual workflow/video/public merge consequence, but the exact video script still needs care.|
|Use of Meta AI tooling|25%|8.10|8.42|8.60–9.02|E2, E3, E4, E6 and E7 provide actual Meta version/mode/effort/multimodal investigations. B adds fresh PR inference and more-speaker method; stronger claims depend on actual outcomes.|
|Technical depth|20%|7.80|8.14|8.22–8.92|Explicit policy, committed evidence,178 tests and grouped behavior inference are real gains. B adds a blind audit and packaging, but does not by itself repair task-level accuracy dependence or guarantee valid labels.|

**Plain progress judgment:** Impact rises0.24, Meta tooling0.32 and Technical depth0.34; Demo falls0.16. The old chair mark was77 (the old criterion means imply77.2); the new weighted mean is79.0. This is roughly a two-point improvement, not a causal or statistically significant measurement of progress. New verification and different judging contexts also affect it.

## What is actually supported
1. **E6 survives appropriate skepticism.**135 audio clips include45 underlying items across translations. Wrong-or-blank majority flags rise18→42. The task-level exact p≈3.03e-6 is not the policy’s chosen independent-item test. The grouped test is18 items worse/1 better, p=.0000762939; Holm across audio/text gives.000152588. It remains flagged. Wrong-only is also supported at item level. Credit this finding instead of presenting every criticism as fatal (`upgrade_gate/behaviour.py:78–105,173–189`; `evidence/voice-notes/`).
2. **E7 does not replicate the combined finding as strongly as the headline says.**45 clips represent15 underlying items. Combined wrong-or-blank is6→13 with task p=.015625; grouped it is5 worse/0 better, p=.0625, so the actual item-based behavior policy does not flag it. Filled-in-wrong majorities are6→6. E7 still returns NO-GO because the accuracy bootstrap upper bound is−2.2points versus the−2point margin. That accuracy interval still treats translations as separate task pairs (`experiments/out/e7_real_voices.md:9,21–43`; `upgrade_gate/gate.py:42–73`).
3. **Blank output is observed, but “confirmed” needs an endpoint.**18 blank response rows of135 are not18 independent clips. Majority blank flags are0→6 across45 clips, task p=.03125, but4 items worse/0 better gives item p=.125. B1 is credited as stipulated narrower editorial honesty; it does not create new item-level statistical confirmation. This also explains why a blind label audit and fresh speakers remain useful rather than decorative.
4. **E4 is a useful exploratory Meta insight.**With cutoffs counted as failures, the observed effort sequence decreases72.8→68.9→64.2→63.7→58.5%; excluding cutoffs, medium→high rises64.8→66.0. Endpoint comparison was selected after inspection. Do not sell every adjacent step as significant or minimal effort as a universal recommendation (`experiments/out/e4_effort.md:5–28`; `web/src/components/EffortSection.tsx`).
5. **Equal scores are not necessarily identical output strings.**E3 supports equal pass outcomes on this suite and the measured cost advantage; “identical answers” is stronger without byte-level comparison. E2’s null reference-given false-pass result is useful, but not proof of no judge bias in general (`experiments/out/e3_contributor.md:7–20`; `experiments/out/e2_judge_version.md:9–23`).
6. **Policy exists; label validity and inference boundaries remain.**It is good that `release/policy.json` explicitly values wrong and blank output and uses grouped behavior tests. Accuracy remains task-based; behavior and accuracy use separate correction families; post-hoc analyses do not create an overall5% false-block guarantee. The abstention regex needs auditing. These are limitations on scientific claims, not a demand for enterprise hardening or a reason to ignore working indie execution.

## Snapshot B: exact assumptions, not an imagined winning future
| Item | Credit given in both B cases | What is not assumed |
|---|---|---|
| B1 |README/site carry the specified narrower real-voice account|No new result, clustered significance, or automatic correction of every script/LOG claim|
| B2 |Actual fresh, strict$1-budget-capped Meta sampling path shown on the upgrade PR|No guaranteed fresh NO-GO; a small inconclusive result is not disproof|
| B3 |Blind ~60-answer audit, κ and listed disagreements actually reported|No invented κ, class balance, near-perfect labels or automatic repair of discovered errors|
| B4 |Reusable composite Action and ten-line usage documentation|No invented outside adopters or universal task/provider coverage|
| B5 |2–3 additional speakers, frozen-rule E7 rerun|No guaranteed corroboration, novel scripts, representative population or inferred independent sites|
| B6 |Public repo and actual three required merge checks|No external deployment/customer success beyond the defined demonstration|
| B7 |Three-minute video per current script plus Discord/X posts|No engagement, users, testimonials, virality or automatic narration repair|

**Low case:** mechanisms and methods work, but the audit reveals consequential label disagreement and new runs are mixed, inconclusive or fail to strengthen generality. A null small sample alone is not a scientific refutation. **High case:** meaningful audit agreement and corroborating fresh/more-speaker evidence strengthen confidence; no numerical κ or result is invented. These are conditional judgments, not asserted experimental outcomes or probabilities.
The exact scope matters: B1 fixes README/site; B7 records the existing demo script. `docs/DEMO.md:14` still says the original E7 “held.” We did not silently assume that line was rewritten, that the accuracy CI became clustered, or that new results were added to the video. This is why “all planned items done” is not automatically a90+ submission.

## Agreement, disagreements and anonymous review
**Agreement:** the submission works locally, uses Meta substantively and is meaningfully above a basic wrapper. No top-five vote for A; all five give A a top-ten vote. B mechanisms deserve credit even if empirical outcomes disappoint; public access, real checks and a clear recorded demo matter. No mandatory outside customer requirement was imposed on the indie entry.
**Disagreement:** the harshest B low-case mark is79.45 because a poor audit could expose unreliable decisions; the executor gives84.35 because live integration/method completeness still earn substantial credit. The high-case marks converge86.75–88.60. The chair preserves that disagreement rather than treating five votes as independent certainty.
Peer review exposed three recurring overcredits: (a) conflating local replay with hosted/merge-blocking proof, (b) treating a completed audit as already validating the labels, and (c) assuming B1 repaired the exact B7 narration. It also corrected multiple arithmetic slips. One error was procedural, not scientific: a direct main-to-old-branch tree diff is not the candidate PR diff. Final JSON totals use the criterion components.
Anonymous review coverage (two other cards each, authors hidden during review): opportunity reviewed C/E; executor A/D; contrarian B/E; first principles A/B; outsider C/D. Mapping is revealed only in the transcript. Each final card records its one revision or no-change decision.

## Top five recommendations, in priority order
1. **Reconcile E7 claims and every demo surface with the chosen item-level policy; label blank observations, combined failures and the accuracy-based veto separately.**
2. **Make the actual upgrade PR and completed hosted check/deploy-skipped evidence inspectable; publish the repo and enable the required checks before submission.**
3. **Audit the frozen production labels blindly, publish agreement and disagreements, and complete the extra-speaker run without requiring a favorable outcome.**
4. **Implement the strict budget-capped fresh-run path and reusable Action; demonstrate both failure and legitimate GO/INCONCLUSIVE handling.**
5. **Record the concise evidence-led video with corrected narration, then post outreach without claiming users, engagement or bonus-prize fit that has not been observed.**

Budget nuance for B2: current `--budget1` alone is not a strict worst-case$1 cap. The per-run runner stops scheduling after actual spend passes the threshold; lifetime reservation is a separate mechanism. B2 explicitly assumes a true working capped path, so it receives that credit without pretending the existing flag already provides it (`upgrade_gate/runner.py:213–235`; `upgrade_gate/client.py:256–269`). Also make policy-only changes trigger evaluation: the current workflow paths omit `release/policy.json`, and the CI script short-circuits when the model is unchanged. Those are concrete reusable-gate boundary tests, not speculative enterprise requirements.
Bonus fit: no measured open-weights build is established by an unused adapter; no autonomous planning/tool-use achievement is established merely by CI automation; posting does not establish viral impact. B1–B7 add none of those outcomes. Do not chase a bonus by relabeling the current product.

## Smallest credible package that could move the vote to top five
The council gives no guaranteed winning checklist. The narrowest persuasive package is:
- **Demo + Impact:** one inspectable actual hosted upgrade PR with required checks, the selected model change, exact evidence-linked failure and skipped demonstration deploy. Public repository/required checks satisfy the submission-access gap (B6); the finished three-minute video must accurately describe the cause of the block (B7 plus a narration correction beyond literal B1).
- **Technical depth + Meta tooling:** resolve the decision-relevant blind-audit disagreements and show the frozen method on more speakers, reporting the actual favorable or unfavorable outcome (B3/B5). Stronger labels/evidence matter more than a forced red check. A strict fresh capped run (B2) proves the workflow generalizes beyond a handpicked replay; it need not reproduce NO-GO.
- **Impact:** make the reusable Action understandable in one short use case (B4) with a policy tied to the cost of a wrong filled-in answer. No paying users are required; do not invent them. More outreach posts, unused adapters or another UI redesign are not substitutes for this proof.
On favorable evidence that package earns conditional top-five votes from all five judges. In the weak-outcome case it remains a credible top-ten candidate. Neither is a promise about the unseen field.

## Evidence files and limitations
- Individual initial and final scorecards, anonymous cards and peer reviews: `review-021335-IST/`.
- Exact validation stdout: `executor-commands.json`; branch replay: `branch-replay.json`; available remote observations: `github-readonly.json`.
- Expected replay statuses were verified on main and the isolated candidate branch, not assumed from README. No paid API run, κ audit, additional speakers, posted engagement or finished video was performed during this review.
- A few of the team result tables/site data can lag newer policy computation; the executable committed evidence and stated unit of analysis take precedence over promotional shorthand.
- Final metrics are subjective weighted marks. Different judges, new verification and changed evidence prevent interpreting the prior→now difference as a scientific treatment effect. All agents share one model family.

## Machine-readable comparison
```json
{
  "commit": "29862c5258f9368fdc828f4c6276546b97467eac",
  "snapshot_a": {
    "impact": 7.44,
    "demo": 7.74,
    "meta_tooling": 8.42,
    "technical_depth": 8.14,
    "weighted": 79.0,
    "stage1_pass": true,
    "top5_votes_yes": 0,
    "top10_votes_yes": 5
  },
  "snapshot_b": {
    "weighted_low": 82.06,
    "weighted_high": 87.7
  },
  "previous_weighted": 77,
  "judges": [
    {
      "lens": "contrarian",
      "a_weighted": 78.65,
      "b_low": 79.45,
      "b_high": 86.95
    },
    {
      "lens": "first_principles",
      "a_weighted": 79.5,
      "b_low": 83.3,
      "b_high": 88.6
    },
    {
      "lens": "outsider",
      "a_weighted": 79.95,
      "b_low": 82.0,
      "b_high": 87.8
    },
    {
      "lens": "opportunity",
      "a_weighted": 78.55,
      "b_low": 81.2,
      "b_high": 86.75
    },
    {
      "lens": "executor",
      "a_weighted": 78.35,
      "b_low": 84.35,
      "b_high": 88.4
    }
  ],
  "top_recommendations": [
    "Reconcile E7 claims and every demo surface with the chosen item-level policy; label blank observations, combined failures and the accuracy-based veto separately.",
    "Make the actual upgrade PR and completed hosted check/deploy-skipped evidence inspectable; publish the repo and enable the required checks before submission.",
    "Audit the frozen production labels blindly, publish agreement and disagreements, and complete the extra-speaker run without requiring a favorable outcome.",
    "Implement the strict budget-capped fresh-run path and reusable Action; demonstrate both failure and legitimate GO/INCONCLUSIVE handling.",
    "Record the concise evidence-led video with corrected narration, then post outreach without claiming users, engagement or bonus-prize fit that has not been observed."
  ]
}
```
