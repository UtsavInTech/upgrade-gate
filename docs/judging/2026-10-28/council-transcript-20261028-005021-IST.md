# Upgrade Gate judging council

Captured 2026-10-28 00:50:21 IST

## Original request

Okay after doing all this kind of work, many agents are still working on this project. How many marks are you willing to give me?

I have added the new UI, the UI that you have provided me. I have changed and deleted it because I didn't like this idea and I have created the UI by myself. Don't try to be so optimistic or good with me. Try to be a real judge, like four to five judges, and discuss with the five agents.

Simply run five parallel agents, then discuss the idea and the weightage that I have previously shared with you: how weightage is decided in this hackathon. Then discuss how many numbers you are going to give me and whether you are going to choose me for the top five or top ten in the hackathon or not for this project.
This is for judging and this is for improvement: what future improvement can I make? It is better to get judged also. Be a good judge and give me some real points that I can improve. If this is ready then give me marks. How many marks are you willing to give me?

Don't think like you are a builder because you are not, okay? Think like the judge and write somewhere in your garden that you have to not be biased towards me. You have to be neutral, more optimistic, and like a worldview. You have to also consider that other projects will also be the best. Think like that.


## Framed question

Judge Upgrade Gate as it exists now, including the user's replacement web UI, using Impact 30%, Demo 25%, Meta tooling 25%, Technical depth 20%. Give honest marks and top-five/top-ten selection votes against a strong hypothetical field, challenge the assessments, and prioritize improvements. Do not reward prior collaboration or builder effort.

## Neutrality charter

# Neutral judging charter

This review assesses a submission, not the developer's worth or effort.

- No extra marks for our previous contribution, familiarity with Utsav, time spent, number of agents, code volume, or replacing our former UI.
- No automatic praise and no manufactured harshness. Award credit only where evidence earns it.
- Judge the current `web/` product. The superseded `ui/` implementation is not the submitted visual experience.
- Separate observed results, implemented mechanisms, illustrative UI, integration recipes, and future promises.
- Use the supplied weights: Impact30%, Demo25%, Meta tooling25%, Technical depth20%.
- Treat the competing field as potentially excellent; never invent entrants, scores, finalist cutoffs, or acceptance probabilities.
- A narrow experiment can be useful without establishing broad production safety. A missing user study is not evidence that the problem has no value.
- Correct the judges when evidence contradicts a criticism. Live source/UI supersedes stale screenshots for implementation claims; stale submission materials still matter as packaging debt.
- Do not change product code or experimental results during judging. No paid calls, fixes, commits, or publication on the user's behalf.
- These are five fresh agent judging passes, followed by five anonymous review passes. They share a model family and source evidence. Their agreement is not independent statistical validation or a vote by actual event judges.

Score anchors used by the chair:5 means a credible prototype with substantial unproven claims;7 means an implemented, supported entry with meaningful gaps;9 requires a compelling demonstrated advantage and persuasive validation/presentation;10 is exceptional evidence and execution. These are this review's anchors, not official finalist thresholds.


## Method

Five fresh judging agents without builder conversation history, in two waves due the three-subagent concurrency limit. Five fresh anonymous peer reviewers, likewise in two waves. One shared underlying model family and evidence corpus: not independent human judges or a statistical ensemble. Product code and experiment records were not edited. Other agents were working concurrently; see evidence-snapshot.json.

## Initial judge responses

### Contrarian

Impact 7/10, Demo 8/10, Meta tooling 8/10, Technical depth 7.5/10. Weighted total: 76/100 (21 + 20 + 20 + 15).

Top-five: NO on current evidence. Top-ten: SHORTLIST. These are selection judgments, not placement predictions; I have no evidence about competing submissions.

The strongest evidence is the auditable change in failure behavior, supported by paired comparisons, text twins, preserved answers, and an unusually candid scorer correction. The current web/ report screenshot is polished and makes individual failures accessible. Direct Meta integration, Contributor experiments, spending controls, and implemented CI exit codes provide credible engineering substance.

Three weaknesses hold it back:
1. The demo misstates its denominator. docs/DEMO.md describes 135 voice notes and gives 84.8% → 83.6% accuracy. The screenshot’s figures combine audio with perfect text twins. experiments/out/e6_audio.md reports audio-only majority accuracy around 69%, with a −2.2-point delta. This materially softens the apparent audio failure rate.
2. Confident and downstream harm exceed the measurement. experiments/e6_audio.py::_mode labels every incorrect response outside a narrow denial pattern confident wrong. It does not measure confidence. Empty JSON fields are detectable with ordinary validation, so the claim that nobody would know needs an actual downstream integration test.
3. Validation remains narrow. E1’s ceiling performance and E4’s 30 easy tasks limit conclusions. E7 supplies encouraging confirmation—6 → 13 silent-failure tasks, p=.016—but covers one speaker and reused lines. Its outputs and recordings were untracked during this audit; the committed findings still describe confirmation as planned.

Highest-return improvement: publish one reproducible, correctly denominated demonstration showing the current behavior gate actually blocking deployment, with E7 evidence committed and its single-speaker limitation explicit. That connects the strongest finding to demonstrated product impact.

### First principles

Impact 7/10; Demo 8/10; Meta tooling 8/10; Technical depth 7.5/10. Weighted total: 76/100.

Selection recommendation: top-ten YES; top-five NO on current evidence. These are judging recommendations, not acceptance predictions.

The problem is valuable: release owners need evidence about consequential failures, not merely aggregate accuracy. The strongest evidence is E6’s paired audio/text design and inspectable saved answers: silent wrong/blank failures increase 18→42, despite nearly unchanged accuracy. This now changes the actual decision: cli.py invokes behaviour.apply_to_gate, and saved results/e6-audio/gate.json records NO-GO, with accuracy alone INCONCLUSIVE. That mechanism is implemented. E7 is also completed locally: 6→13, p=.015625, on 45 clips from one human speaker. Honest correction of E1’s scorer-induced improvement strengthens credibility.

Three shortcomings limit the marks:
1. Unproven operational value. README’s support-team scenario is explicitly illustrative. There is no demonstrated customer workflow, release-owner adoption, or measured avoided harm. A plausible deployment problem does not establish demand.
2. Limited independent evidence. audio_synth.py shares underlying items across translations; stats.py treats task pairs independently. E7 reuses those lines with one speaker (e7_real_voices.md). Its confirmation supports this narrow setting, not broad voice-note reliability.
3. The risk definition needs validation. behaviour.py groups readily detectable empty JSON with wrong populated answers and identifies abstention through regexes. Those can warrant different release policies. Moreover, web/screenshots/report.png still shows INCONCLUSIVE while current exported data and code say NO-GO; findings documentation still calls E7 planned.

Highest-return improvement: run one documented release decision with an actual voice-workflow owner, using their held-out clips and explicitly agreed failure costs. Demonstrate which harmful errors survive ordinary schema checks and why the gate changes their action.

### Outsider

Impact 7/10; Demo 7.5/10; Meta tooling 8/10; Technical depth 8/10. Weighted total: 75.75/100.

My selection votes against a strong hypothetical field: Top five NO. Top ten SHORTLIST. These are selection judgments, not predictions about unknown competitors.

The first minute communicates a recognizable buyer problem: a developer upgrading models wants evidence before deployment. The current web/ screenshots have readable hierarchy and a useful pull-request metaphor. The paired clip grid makes the failure shift visible. Source inspection shows audio players, transcripts, reference answers, and repeated outputs, so a judge has the ingredients to verify an example. I did not audition playback or exercise the browser.

Three blockers:
1. The presentation contradicts its latest evidence. Screenshots and docs/DEMO.md show INCONCLUSIVE/review required; current exported data and saved gate results say NO-GO. The home-page caveat still calls real voices in progress, although E7 reports 6→13 silent failures across 45 clips, p=0.016.
2. The headline denominator changes. The report’s 84.8→83.6% pools audio with perfect text twins; audio-only results are substantially lower. The behavioral gate describes 18→42 of 270 tasks while the visual tells the audio-only story of 135 clips. These choices need explicit labels.
3. Deployment value is asserted more convincingly than demonstrated. The README supplies a credible CI handoff, but the depicted PR is illustrative. One actual blocked workflow and generated regression artifact would establish the product’s operational payoff.

Best quality: the evidence chain connects a visible failure to preserved answers and affordable Meta-specific experiments.

First improvement: make one consistent, 60-second demonstration—play a real recorded clip, expose the blank answer, show the saved NO-GO decision, then show the deployment check failing.

### Opportunity

Impact 8.0/10, Demo 8.0/10, Meta tooling 8.5/10, Technical depth 8.0/10. Weighted total: 81.25/100. Top 10 YES. Top 5 NO against a strong hypothetical field. These are selection votes, not ranking probabilities.

The strongest defensible distinguishing value is the complete evidence-to-release-decision chain: replayed multilingual tasks, inspectable answers, audited scoring, paired statistics, and an implemented behavioral veto. Commit 7b70647 matters: the CLI now applies upgrade_gate/behaviour.py, so E6 actually becomes NO-GO rather than merely displaying an interesting exploratory finding. E7 strengthens that story: the frozen experiment reports silent failures increasing 6→13 across 45 human-recorded clips, p=0.015625. That earns credit today, despite its limits. E1’s openly documented scorer correction also demonstrates useful evaluation judgment.

Three current weaknesses:
1. Limited external validity: experiments/out/e7_real_voices.md contains one speaker and reused scripted lines; web/src/components/AudioSection.tsx acknowledges possible reading slips. This does not establish performance across production speakers or noisy recordings.
2. Policy depends on heuristics: upgrade_gate/behaviour.py identifies abstention using regexes, with no demonstrated multilingual classification audit. Wrong answers with uncertainty wording can therefore change the release verdict.
3. Submission evidence is inconsistent: web/screenshots/report.png still displays INCONCLUSIVE, while current exported data says NO-GO. E7 outputs and related web changes are uncommitted; README/findings still describe E7 as planned.

Highest-return improvement: run a small, frozen, independently reviewed multi-speaker holdout, audit the failure labels, then package its results with synchronized screenshots and committed exports. That would strengthen the project’s central claim more than adding another feature.

### Executor

Impact 7/10, Demo 8/10, Meta tooling 8/10, Technical depth 8/10. Weighted total: 77/100.

Against a strong hypothetical field: Top 5 NO. Top 10 SHORTLIST. This judges the inspected snapshot, not an actual rank prediction.

The strongest asset is inspectable evidence for a useful release decision: accuracy alone can obscure a worsening failure mode. The current CLI applies behaviour.py after the accuracy gate and returns NO-GO; this is implemented behavior, not merely a dashboard annotation. E7 genuinely exists locally: 45 human clips, one speaker, 270 responses, and silent failures increasing 6→13, exact paired p=.015625. The current web/ source offers a polished route from verdict to individual answers and audio.

Three shortcomings limit selection:
1. The demonstration overstates integration. web/src/components/Hero.tsx simulates pull-request checks; .github/workflows/canary.yml runs monitoring, not a candidate-upgrade PR gate. README’s deployment workflow is an integration recipe. No inspected evidence demonstrates an actual blocked upgrade PR.
2. The submission tells conflicting versions of the result. Saved web/screenshots/report.png and docs/DEMO.md still present INCONCLUSIVE, while current source and E6’s saved gate say NO-GO. E6’s behavior gate also counts 270 audio-plus-text tasks, whereas the headline uses 135 audio clips. E7 exports and recordings are untracked, weakening fresh-clone reproducibility.
3. Validation remains narrow. experiments/out/e7_real_voices.md supports one speaker and 45 reused-script clips. It strengthens the specific finding, but establishes neither production impact nor broad release-policy reliability.

The deadline bottleneck is packaging a coherent, reproducible release story. Next action: produce one frozen submission showing an actual offline CI gate blocking a candidate, with committed E7 evidence and regenerated screenshots/script that agree with the current verdict.

## Verified updates before anonymous review

Chair inspected live web UI at http://127.0.0.1:5191 on Oct28 IST. Hero now says Failed/Merging blocked, and home includes real-voice confirmation6→13 with explicit one-speaker caveat. Do not claim the live homepage still says confirmation in progress.

Live E6 report shows NO-GO and Accuracy alone INCONCLUSIVE. Headline pass rate84.8→83.6 pools audio+text twins; report subtitle says voice notes each with text twin. It does not explicitly label headline as pooled. Behavior reason18→42 of270 and audio clip figure18→42 of135 both appear. This is a denominator-labeling/estimand problem, not proof of fabricated numbers.

E7 is completed locally on45 clips by one speaker. Primary frozen experiment imports the older E6 failure rules; generic production behaviour.py uses a broader abstention regex. E7 findings should not be assumed to validate every generic production classification rule.

Stored screenshots/docs/DEMO still say INCONCLUSIVE; local source/UI has advanced. Do not double-count this as absent gate implementation. Human voice recordings may stay private; reproducibility can use consented samples, scripts, hashes, outputs and limitations, not forced publication of private recordings.

Official Promptfoo docs show before/after GitHub Action evaluations (https://www.promptfoo.dev/docs/integrations/github-action/); Braintrust docs show model/experiment comparison, improvements/regressions and cost (https://www.braintrust.dev/foundations/how-to-analyze-your-eval-results). Thus generic evaluation/CI features alone are not a demonstrated unique wedge. These are established tools, not known entrants in this hackathon.

## Anonymization mapping

A = Outsider

B = Opportunity

C = Contrarian

D = First principles

E = Executor

## Anonymous peer reviews

### Reviewer 1

Strongest: D. It separates an implemented gate from demonstrated operational value, questions independence across translated tasks, and asks whether errors survive ordinary validation. C adds the strongest critique of the unmeasured confident-wrong claim. Biggest blind spot: B. Its81.25 gives substantial credit to the evidence-to-release chain without establishing how that differs materially from existing evaluation tools. Its generic-regex concern needs qualification: E7's frozen experiment uses older E6 rules, so production classification weaknesses do not automatically invalidate E7. All five missed a credible comparative baseline for differentiation and explicit anchors for each rubric score, especially Meta tooling8–8.5. Live corrections matter: homepage already shows failure and completed one-speaker confirmation; stale assets are packaging debt. Pooled headline needs labeling, not accusations of fabricated numbers. Top-ten shortlist, not top-five.77.2 is arithmetically correct but misleadingly precise; shared evidence, assumptions and unspecified anchors do not create calibrated certainty.

### Reviewer 2

D is strongest: implemented gate versus operational value, correlated translations, and schema-detectable blanks versus harmful populated answers. Its top-ten YES is more confident than the evidence supports. B has largest blind spot:81.25 and firm top-ten vote overcredit the evidence-to-release chain. E6's rule was selected after observing failures; frozen E7 is useful confirmation on reused scripts and one speaker. E7 tests older E6 rules, not the broader production classifier. All five underweight the distinction between a behavioral finding and validated release policy. Audit multilingual labels, account for translation dependence, show errors surviving existing checks and changing an owner's decision. Existing eval tools have comparison and CI features. A's homepage criticism is superseded by live UI; stale artifacts are packaging, not missing implementation. Reproducibility need not expose private voices. Top-ten shortlist; top-five no.77.2 is rubric judgment, not validated ranking.

### Reviewer 3

Strongest E: a feasible deadline plan credits the implemented veto and live E7 UI, then freezes evidence, fixes denominators, synchronizes materials and demonstrates a blocked candidate workflow. Demo plus Meta tooling are50%, so immediate return may exceed recruiting speakers/customer validation. Biggest blind spot D: owner access, consent, held-out recordings and agreed error costs have dependencies; making that the next action risks achievable demo/reproducibility gains. Traction is unproven. Missing across all five: a demonstrated competitive wedge. Promptfoo/Braintrust already offer evaluation comparisons and CI capabilities. Explain and demonstrate why Meta audio/text pairing plus behavioral policy changes a decision existing workflows miss; use preserved outputs rather than claim broad uniqueness. More experiments have opportunity cost. Top-ten shortlist, top-five no.77.2 is a consensus center, not calibrated ranking or decimal-precise judgment.

### Reviewer 4

Strongest E: distinguishes implemented NO-GO from illustrative PR, credits E7 and proposes feasible improvement. Correct stale presentation concerns: NO-GO and real-voice confirmation are already live; A's in-progress homepage claim has no weight. Largest blind spot is insufficient demonstration of incremental benefit over ordinary validation and existing evaluation tooling; narrow experiments are not adoption or production impact. All five missed whether veto threshold and error costs were specified before observing results. Statistical detection does not automatically justify deployment policy. Top-ten shortlist with credible selection case; top-five no. Unknown competitors preclude stronger placement claims. First freeze a reproducible workflow run showing CLI blocking, correct denominators, synchronized artifacts and explicit one-speaker limits. Report77/100;77.2 only as arithmetic mean. Score spread is subjective disagreement, not confidence interval.

### Reviewer 5

Strongest C: distinguishes wrong without explicit abstention from measured confidence, identifies pooled accuracy and challenges harm claims. Stale observations yield to live Failed/Merging blocked and completed E7 with one-speaker caveat. Biggest blind spot B:81.25 gives too much commercial credit without customer use or blocked workflow. Existing tools offer comparisons/CI. Missing customer proof limits confidence in demand, not proof of no value. All five missed need to freeze/audit actual estimand and taxonomy:270 pooled tasks versus135 audio clips are denominator ambiguities, not fabricated data. Separate schema-detectable blanks from populated wrong answers; audit multilingual abstention. E7 validates frozen E6 rules on one speaker, not every production regex; account for shared underlying items. Top-five no; top-ten yes narrowly.77.2 is snapshot rubric assessment, not percentile/probability/calibrated consensus. Prioritize scoring clarity, audited examples and one reproducible blocked workflow over more features.

## Chairman synthesis

# Where the Council Agrees

**Chair's mark:77/100. Top-five vote: no today. Top-ten vote: shortlist for serious consideration, not an automatic slot.** Five original scores range75.75–81.25; their weighted arithmetic mean is77.2. Decimal precision does not make these subjective judgments calibrated. No actual competing submissions were available.

The current product is a credible working entry with real Meta experiments, not just a mockup. Its strongest asset is the connection between saved paired answers, failure behavior, and an implemented release veto. The live site now shows NO-GO for E6 and completed E7 human-voice confirmation. We credit both. No judge awards top-five status on the inspected evidence; two original judges vote top-ten yes and three shortlist it. All five anonymous reviews retain a top-five no stance.

| Criterion | Weight | Mean score /10 | Weighted points |
|---|---:|---:|---:|
| Impact |30%|7.2|21.60|
| Demo |25%|7.9|19.75|
| Meta tooling |25%|8.1|20.25|
| Technical depth |20%|7.8|15.60|
| Total |100%||77.20|

Impact loses the most ground: a convincing problem and an engineering mechanism are present, but inspected evidence does not establish use by an external release owner, avoided incidents, or why an existing evaluation workflow would be insufficient. Demo earns credit for the user's readable replacement UI, clip grids and inspectable answers. Meta integration earns credit for real version, modality and serving-mode comparisons. Technical depth earns credit for paired tests, repeats, cost tracking and scorer auditing; it loses credit for narrow validation and a failure taxonomy whose reliability is not measured sufficiently.

# Where the Council Clashes

The opportunity judge gives81.25, emphasizing the Meta-specific evidence-to-decision chain. The other four give75.75–77, emphasizing missing operational proof and measurement limits. The chair sides with the lower cluster: demonstrated differentiation and impact matter more than feature completeness.

The practical disagreement is sequencing. Multi-speaker holdout validation would strengthen the science. A real workflow owner would strengthen Impact. But one actual reproducible candidate-upgrade workflow run is the best immediate deadline investment: it can establish that the product changes a release action without depending on new recruitment or more features. After that, broader speakers and independently audited labels are the best validation investment.

# Blind Spots the Council Caught

1. Some initial criticisms used stale artifacts. The live homepage already shows Failed/Merging blocked and one-speaker E7 confirmation. We reject the claims that those live features are absent. Stored screenshots, README and demo script still lag; that is packaging debt, not absence of implementation.
2. E6 has two populations:135 audio clips and135 perfect text twins. The live report headline84.8%→83.6% pools them. The audio-only table has134 fully paired clips and delta−2.2 points. The behavior reason reports18→42 across270 pooled tasks; the clip grid reports the same numerators across135 audio clips. These figures are not fabricated, but unclear labels obscure the relevant population and practical effect. Use one clearly labeled population per headline.
3. “Confidently wrong” is not measured confidence. The rules identify an incorrect answer without matched abstention wording. Distinguish populated wrong answers from empty fields that simple validators can already reject. A stronger claim is about failure signaling under this specified taxonomy, not psychological confidence.
4. E6 is exploratory because its rules followed inspection of outputs. E7 supplies a frozen primary confirmation:6→13 across45 human clips, exact paired p=.015625. It is one speaker reading reused lines. That supports this setting, not population-wide voice reliability. E7's older E6 rules also differ from the broader production abstention regex; confirmation of one does not automatically validate the other.
5. Statistical significance does not choose an appropriate business loss or release threshold. The silent-failure policy needs an explicit reason that its cost/threshold matches the user's workflow. Related translations/scripts also warrant dependence-aware sensitivity analysis.
6. Generic model comparisons and CI evaluations already exist. Promptfoo documents before/after GitHub Action evaluations; Braintrust documents experiment comparison, regressions and costs. These are comparison baselines, not presumed entrants in this hackathon. The defensible wedge is the particular failure-signaling decision the Meta study supports, demonstrated beyond an ordinary accuracy check.

# The Recommendation

**This is ready to demonstrate; it is not yet a top-five-ready submission on the evidence inspected. Freeze feature expansion and strengthen the proof.**

Priority1 — In the next focused work session, record an actual candidate-upgrade workflow: saved input → accuracy-only result → behavioral NO-GO → nonzero gate exit → deployment step demonstrably skipped → one reproducible failing case. Show a correctly shaped but wrong populated answer, so the example survives basic required-field checks. Use offline saved records to avoid unnecessary paid calls. The PR card can introduce this; the workflow run must prove it. This is presently a missing demonstration, not a missing gate implementation.

Priority2 — Make the submission tell one version of the result. Explicitly label audio-only and pooled figures, sample counts, correct/strict/behavioral metrics, and which correction family applies. Regenerate screenshots and synchronize README, findings and the three-minute script with the live NO-GO and completed E7. Preserve privacy: reproducibility can use consented samples, scripts, hashes, outputs and caveats rather than requiring private recordings to be public.

Priority3 — Independently audit the failure labels and reference transcripts, especially populated-wrong versus abstention versus blank. Report agreement and mistakes. Freeze the actual production rule before a fresh multi-speaker holdout. Include varied accents/recording conditions and avoid treating translations of the same base item as independent evidence without a sensitivity check. Do not call one-speaker confirmation broad validation.

Priority4 — Obtain one genuine release-owner trial using their approved held-out tasks. Record the decision before and after the gate and what ordinary validation missed. If no user trial is available before submission, state that limitation rather than substitute a hypothetical scenario or invented traction.

Priority5 — Explain the competitive wedge in one sentence and show the comparison: an accuracy-based evaluation can appear unchanged, while a specified harmful failure-signaling rate causes a defensible release hold. Credit existing evaluation tools; position this as a decision layer or exportable policy rather than claiming to have invented evaluations or CI gating.

# The One Thing to Do First

**Produce one verifiable blocked upgrade workflow using the existing saved results.** The best next improvement is proof of the decision changing an action, not another UI redesign or experiment menu. Then use the remaining time to strengthen the labels and holdout evidence behind that action.

This assessment is not a percentile, confidence interval, promise of qualification, or estimate of actual top-ten odds. It judges the inspected snapshot against a demanding standard; the real event panel and field may differ.

Sources: `experiments/out/e6_audio.md`, local `experiments/out/e7_real_voices.md`, `upgrade_gate/behaviour.py`, `upgrade_gate/cli.py`, local saved gate JSON, current `web/` source/live site, `web/screenshots`, `docs/DEMO.md`, README. External comparison sources: [Promptfoo GitHub Action](https://www.promptfoo.dev/docs/integrations/github-action/), [Braintrust experiment analysis](https://www.braintrust.dev/foundations/how-to-analyze-your-eval-results).


## Evidence snapshot

```json
{
  "timestamp": "2026-10-28T00:50:21.472687+05:30",
  "head": "18e2dcaf85e2f7ea3c1dbb738434b64915f003f7",
  "status": " M scripts/export_web.py\n?? docs/judging/\n?? experiments/out/e2_judge_version.json\n?? experiments/out/e2_judge_version.md\n?? experiments/out/e4_effort.json\n?? experiments/out/e4_effort.md\n?? results/e2-judges.log\n?? results/e3-contributor.log\n?? results/e4-effort.log\n?? results/e4-pilot.log\n?? results/e6-audio.log\n?? results/e7-real-voices.log\n",
  "evidence_sha256": {
    "README.md": "1fdef588ad9bda3b31a1b092336c8de47e40558451f237cfc6e71be843ef1135",
    "docs/DEMO.md": "403118e66e7e2ce68a6d938e75b0cdef08e7095b53b8a7730fe581b5dd856354",
    "upgrade_gate/behaviour.py": "31c519c3a94217f20e09c1cef9f8bc8bcd55ab0edccf7467ed930d8bb310d2f7",
    "upgrade_gate/cli.py": "d44ebddf5d0ef61f164bd3a888cfc2831238bd6256df9f644f1a7342317f1246",
    "experiments/out/e6_audio.md": "c81fe353bc67f62614c22845ca2c67ae205b0d8def7deaea257c10b9b27a4adc",
    "experiments/out/e7_real_voices.md": "517488faba48580bc83506c5ed6beb540520395c9f29493cc4ff168f6faf4c79",
    "web/src/components/Hero.tsx": "a9dda87d22c241c2ae1f0fac23d34257205783a333e3c19828b4aeeb56867bc9",
    "web/src/components/AudioSection.tsx": "830097ce8e50c3db0ea4de7fc7f4ca7600dbd297ace6ba91cd4c9b56dbc894fd",
    "web/src/components/Report.tsx": "19d0ba163344dbc2b7bbd03bd61de7ef7e343c8846d9e796044e3e734b2e3734",
    "results/e6-audio/gate.json": "2e25d7aa8a5dfc6c4560b6c9ee5954bb9300909e7f9d382dfea568596c994e71",
    "results/e7-real-voices/gate.json": "3caa541810369435e08df736e22edf6aa5abc8268fff85eddb830d6e160e56b2"
  }
}
```


## Late evidence note after initial scoring

Late-arriving evidence: while this report was being finalized, commit18e2dca published E7 confirmation. The original judges’ untracked-E7 observations are historical, not a remaining current defect. E2 and full E4 tables also arrived after the five initial scorecards: E2 reports no observed false-pass preference in this sample; E4 shows descriptive accuracy/cost changes but no significant adjacent-step category comparison in its displayed tests. The chair inspected these tables but the five initial judges did not fully re-audit them. They receive no invented breakthrough credit and do not resolve the central deployment-validation gap. The77/100 verdict remains a snapshot assessment, not a continuously updated ranking.

Latest observed commit: 18e2dcaf85e2f7ea3c1dbb738434b64915f003f7
