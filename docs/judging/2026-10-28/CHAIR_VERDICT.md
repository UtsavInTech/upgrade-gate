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

## Late evidence note

Late-arriving evidence: while this report was being finalized, commit18e2dca published E7 confirmation. The original judges’ untracked-E7 observations are historical, not a remaining current defect. E2 and full E4 tables also arrived after the five initial scorecards: E2 reports no observed false-pass preference in this sample; E4 shows descriptive accuracy/cost changes but no significant adjacent-step category comparison in its displayed tests. The chair inspected these tables but the five initial judges did not fully re-audit them. They receive no invented breakthrough credit and do not resolve the central deployment-validation gap. The77/100 verdict remains a snapshot assessment, not a continuously updated ranking.
