# Full transcript — two-snapshot council

Commit 29862c5258f9368fdc828f4c6276546b97467eac; 2026-10-28 02:27:11 IST.

## User request

You are running a **neutral judging council** for a hackathon submission. Five independent judges score it,
critique each other anonymously, and a chair writes the verdict. You have no loyalty to the builder: no marks for
effort, number of agents used, prior collaboration, or how much was rebuilt. Judge only the evidence.

## The submission

- Repository: **https://github.com/UtsavInTech/upgrade-gate** (default branch `main`; also inspect branch
  `upgrade/spark-1.3` and its pull request). Record the commit hash you judged.
- Project: **Upgrade Gate**, a go/no-go gate for upgrading Meta Muse Spark models (1.2 → 1.3). It replays the same
  tasks on both versions, scores answers with fixed rules, runs paired statistics, checks whether failures became
  *silent* (wrong or blank with no warning), and blocks the pull request.
- Start with: `README.md`, `STATUS.md`, `findings/LOG.md`, `experiments/out/*.md`, `release/policy.json`,
  `.github/workflows/upgrade-gate.yml`, `scripts/ci_gate.py`, `upgrade_gate/behaviour.py`, `upgrade_gate/gate.py`,
  `upgrade_gate/stats.py`, `upgrade_gate/scorers.py`, `evidence/`, `web/` (site + report), `docs/DEMO.md`,
  `docs/BRING_YOUR_OWN_TASKS.md`, and the previous council in `docs/judging/2026-10-28/`.

**Do not spend money.** Do not call the Meta API or set any API key. You may run local commands:

```bash
python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'
PYTHONPATH=. .venv/bin/python -m pytest -q
# replay the upgrade PR locally (no API calls): voice-notes and real-voices should fail, text pass
python3 -c "import json;p='release/model.json';d=json.load(open(p));d['model']='spark-1.3@low';json.dump(d,open(p,'w'),indent=2)"
for s in voice-notes real-voices text-and-documents; do PYTHONPATH=. .venv/bin/python scripts/ci_gate.py $s --baseline spark-1.2@low; echo "exit=$?"; done
git checkout release/model.json
npm --prefix web ci && npm --prefix web run build      # optional: the site
```

## Official criteria

**From the public event page** (cerebralvalley.ai/e/meta-ai-developer-hackathon, read 28 Oct 2026):
- Indie developer track: judged on *"creativity, technical ambition, and whether it works."*
- Startup track: judged on *"technical execution and whether it holds up in production."*
- Themes: *"Build for Your World"* (bring Meta's models into your domain, a problem you know firsthand) or
  *"Push the Frontier."* Submissions due Nov 4, 9:00 PM ET; judging Nov 4–8; live finals Nov 9.

**From the official rules as recorded by the team** (`STATUS.md`; treat as the scoring rubric):
- Stage 1: pass/fail on theme fit and real use of Meta's models.
- Stage 2, each 0–10: **Impact 30% · Demo 25% · Use of Meta AI tooling 25% · Technical depth 20%.** The tooling
  criterion rewards going beyond a basic integration and surfacing unexpected capabilities.
- Top 5 per track have their 3-minute demo video judged live. New work only; repo public at submission.
- Bonus prizes the team targets: best open-weights build, best agentic use, most viral X post.

This is an **indie, solo** entry. Score against a strong hypothetical field (you have no real competitors to see).

## Score two snapshots

**Snapshot A: as built.** Only what exists in the repository at the commit you judge. Verify, don't trust: check
headline numbers against `experiments/out/` and `evidence/`, run the tests and the PR replay, open the site.

**Snapshot B: projected.** Assume the planned items below are done **exactly as specified, and nothing more**.
Credit their *existence and method*. Where an item's *outcome* is unknown, do not assume it went well: score a
low and a high case and report the range.

| # | Planned item (assume done) | Outcome assumed? |
|---|---|---|
| B1 | README and site describe the real-voice result honestly: "confirmed for blank answers; borderline when the 3 language versions are grouped as one item (5 vs 0, p = 0.062)" | Yes (wording only) |
| B2 | **Live mode**: when the repo secret `MODEL_API_KEY` is set, the upgrade-gate workflow runs `upgrade-gate all` on a small fresh sample (e.g. 30 voice clips, budget-capped at $1) instead of replaying `evidence/`; shown working on the upgrade PR | Mechanism yes; whether the fresh sample reproduces the NO-GO: **unknown** |
| B3 | **Label audit**: a person blind-labels ~60 answers (correct / says it can't answer / blank / wrong); agreement with the automatic rules reported as Cohen's κ with the disagreements listed | Method yes; κ value: **unknown** |
| B4 | **Reusable GitHub Action** `uses: UtsavInTech/upgrade-gate@v1` (composite action + 10-line usage doc) | Yes |
| B5 | 2–3 more speakers recorded; E7 rerun with the frozen rules | Method yes; result: **unknown** |
| B6 | Repo public; branch protection on `main` requires the three `upgrade-gate / …` checks, so the PR shows "Merging is blocked" | Yes |
| B7 | 3-minute video recorded per `docs/DEMO.md`; Discord ask and X thread posted per `docs/OUTREACH.md` | Posted yes; engagement, outside users, virality: **unknown, assume none** |

Do not invent traction, users, testimonials or results that the table marks unknown.

## The five judges (score independently first)

1. **Contrarian.** Hunts for overclaims, weak statistics, stale or inconsistent numbers, and anything a hostile judge
   would quote. Checks denominators (audio-only vs pooled), post-hoc analyses, multiple comparisons.
2. **First principles.** Is the problem real and important? Does the mechanism actually solve it? What would a
   release owner at a company need that is missing?
3. **Outsider.** A non-ML hackathon judge with 5 minutes. Is the story clear from the README, site and video
   script? Would they remember one moment? Is anything confusing or jargon-heavy?
4. **Opportunity / Meta.** How well does it use Meta's tooling (versions, Contributor mode, reasoning effort,
   multimodal input, open weights)? Does it surface something unexpected about Meta's models? Bonus-prize fit.
5. **Executor.** Does it work? Run the tests, the PR replay and the site build. Check the workflow, the policy file,
   bring-your-own-tasks, spending cap. Report every command you ran and its result.

Each judge returns, for **both** snapshots:

| Criterion | Weight | Score 0–10 | One-line reason with a file/line or command as evidence |
|---|---|---|---|
| Impact | 30% | | |
| Demo | 25% | | |
| Meta tooling | 25% | | |
| Technical depth | 20% | | |
| **Weighted /100** | | | |

Plus: Stage 1 pass/fail · top-5 vote (yes/no) · top-10 vote (yes/shortlist/no) · 3 strengths · 3 weaknesses ·
the single highest-return next action. For snapshot B, give low/high scores where outcomes are unknown.

## Then

1. **Anonymous peer review.** Each judge reviews two other scorecards (labelled A–E, authors hidden): what they
   got wrong, missed, or over/under-credited. Judges may revise once, stating what changed.
2. **Chair verdict.** Final mark for A and for B (low–high), weighted mean and range across judges, where they
   agree and clash, blind spots, and the top 5 recommendations in priority order.
3. **Progress check.** Compare with the previous council (`docs/judging/2026-10-28/`, chair mark **77/100**,
   Impact 7.2, Demo 7.9, Meta tooling 8.1, Technical depth 7.8). For each criterion: previous, now (A), projected
   (B), and what drove the change. Say plainly if something got worse.
4. **What would move it to top 5?** Name the smallest set of concrete changes, with the criterion each moves.

## Output

Write a report to `docs/judging/<date>/council-report-<timestamp>.md`, and end your answer with this JSON so
runs can be compared automatically:

```json
{
  "commit": "",
  "snapshot_a": {"impact": 0, "demo": 0, "meta_tooling": 0, "technical_depth": 0, "weighted": 0,
                 "stage1_pass": true, "top5_votes_yes": 0, "top10_votes_yes": 0},
  "snapshot_b": {"weighted_low": 0, "weighted_high": 0},
  "previous_weighted": 77,
  "judges": [{"lens": "contrarian", "a_weighted": 0, "b_low": 0, "b_high": 0}],
  "top_recommendations": []
}
```

Rules for the council: every score needs evidence from the repo or a command you ran; mark anything you could
not verify; scores are judgments, not probabilities or percentile ranks; all five judges share one model family,
so say so in the report.


## Shared verified facts

# Shared verified facts for peer review

Snapshot A = main29862c5258f9368fdc828f4c6276546b97467eac. Upgrade branch92f04d8ede349843172c8ecb96ad9b8d92131708; merge-baseb92153a. Actual three-dot candidate change is only release/model.json. A direct A-to-older-branch diff is not a PR deletion diff. The older candidate branch lacks main's latest policy; do not assume historical hosted checks used the newly pinned main code.

Executor ran178 tests successfully, web build successfully, and main's local CI replays with candidate temporarily1.3 and explicit1.2 baseline. Exits: voice-notes2, real-voices2, text-and-documents0. Original release/model.json bytes restored, tracked diff empty. Full stdout in executor-commands.json. No Meta API calls or keys; generated decisions/reports are in temp directories.

Authenticated read-only GitHub API: repository private=true. Upgrade branch verified at supplied SHA. GET /pulls?state=all&per_page=100 returned[] with available credentials. Actions query listed only two failed canary runs and no upgrade-gate run. Main rules endpoint returned[]; protection endpoint404. See github-readonly.json. Therefore hosted PR, completed upgrade checks, actual deploy-skipped run, and merge blocking were NOT independently verified. Do not accuse fabrication; evidence may be unavailable to this credential. Root asked user for direct PR URL. Credit verified local reproducibility, not an unverified hosted demonstration. B2 and B6 are explicitly stipulated working in projected B and receive that credit.

Public event page was read: https://cerebralvalley.ai/e/meta-ai-developer-hackathon. It supports indie creativity, technical ambition, whether it works; startup production readiness is a different track. It does not expose numeric stage2 weights in the retrieved page: use30/25/25/20 from user/STATUS instruction. Stage1 theme+actualMeta pass is separate from current private-repo eligibility condition. No mandatory commercial traction prerequisite for indie. No competitors or acceptance odds observed.

E6 audio-only wrong+blank18→42/135,45 underlying items,18 worse1better item p=.0000762939; Holm across audio+text=.000152588 still flagged. E7 combined6→13/45 tasksp=.015625 but15items5worse0better itemp=.0625 -> behavior NOT flagged. Real-voice NO-GO comes from task-level accuracy CI upper−2.2points versus−2margin; that accuracy interval is not item-cluster aware. E7 wrong-only majority6→6, p1. Blank-only majority0→6/45 with taskp=.03125,4worse0better items p=.125.18blank answers/135response rows is descriptive, not18independent clips. B1 promised wording credit is not a new statistical finding and must not silently become clustered significance.

B means EXACT B1–B7 done. Mechanism/method yes, empirical outcomes unknown. Don't add speaker diversity/task novelty/independent external users/κ values/viral engagement not promised. A nonsignificant fresh30-clips result is not automatically disproof; low-κ can expose real label errors. B7 video follows the existing script, whose 'it held' line is not explicitly repaired by B1 (README+site only). No assumed paying users or production maturity. Open-weights/agentic/viral bonuses need actual relevant evidence; neither traffic posting nor unused adapters prove them.

You must critique TWO specified anonymous cards, then revise your own scorecard AT MOST ONCE and state what changed. Do not read mapping file or other judges' final cards. Submit final JSON and evidence-backed prose; finish the turn to free the next wave.


## Initial independent scorecards

### contrarian

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


### first-principles

# Independent first-principles scorecard

Judged main commit `29862c5258f9368fdc828f4c6276546b97467eac`; upgrade snapshot supplied as `92f04d8ede349843172c8ecb96ad9b8d92131708`. This is the initial independent card, before reading other current cards or the previous council. Rubric: Impact 30%, Demo 25%, Meta tooling 25%, Technical depth 20%. Lens: an indie solo hackathon entry judged on creativity, ambition, and whether it works; company release-owner requirements below explain practical limits, not a startup-readiness bar.

## First-principles judgment

The problem is real in the evidence: an aggregate pass rate does not tell a release owner whether a failure will trigger the fallback their product relies on. The concrete policy makes this meaningful: a customer who gets an explicit inability message can type the order; a plausible wrong pincode may get stored (`release/policy.json:2–8`). Comparing the same workload, separating content from format, checking failure type, and emitting a blocking exit code is a coherent solution. The Hindi pincode demonstration is substantially more memorable than an abstract benchmark improvement (`scripts/ci_gate.py:52–76`; `docs/DEMO.md:9–13`).

Its largest gap is decision validity rather than missing infrastructure. It automates decisions over the supplied tasks and labels; it cannot establish that those tasks represent the release owner's traffic, that the labels faithfully model harm, or that translated versions are independent. The current behavior gate explicitly handles related translations, while the accuracy gate still bootstraps tasks independently (`upgrade_gate/behaviour.py:78–105,137–189`; `upgrade_gate/stats.py:36–48`). Those are different guarantees. A reusable Action and a live sample improve delivery but do not resolve sampling or scoring validity by themselves.

## Snapshot A — as built

| Criterion | Weight | Score /10 | Evidence and reason |
|---|---:|---:|---|
| Impact | 30% | 7.7 | A tangible release-policy problem and a strong synthetic-audio finding; users can supply known-answer tasks, but domain coverage and setup remain the user's responsibility (`release/policy.json:2–8`; `docs/BRING_YOUR_OWN_TASKS.md:3–4,18–36,55–56`; `findings/LOG.md:73–74`). No outside adoption is assumed. |
| Demo | 25% | 7.7 | Clear one-line upgrade → failed check → wrong Hindi pincode story, polished saved report screenshots and answer inspection; the video is still a script, the current site overstates E7, and the asserted hosted PR/check demonstration is absent in the chair's authenticated API verification (`docs/DEMO.md:9–18`; `web/src/components/Report.tsx:54–65`; `web/src/components/AudioSection.tsx:111–160`; `STATUS.md:92,97`; `github-readonly.json`). |
| Meta tooling | 25% | 8.3 | Real pinned Meta-version evidence plus serving-mode and effort experiments goes beyond a wrapper; text Contributor equivalence and effort/audio surprises are actual results, while open-weights judging remains a supported path rather than a demonstrated differentiator (`evidence/real-voices/run.json:4–19`; `experiments/out/e3_contributor.md:5–20`; `experiments/out/e4_effort.md:1–11`; `README.md:117–119,130`). |
| Technical depth | 20% | 8.2 | Repeat voting, paired exact inference, Holm slices, explicit harmful-answer policy and fail-closed nonzero CI integration form a working chain; grouped behavior inference is stronger than the still task-independent accuracy CI, and rule labels lack the planned blinded audit (`upgrade_gate/stats.py:13–48,66–89`; `upgrade_gate/gate.py:61–84`; `upgrade_gate/behaviour.py:173–189`; `.github/workflows/upgrade-gate.yml:21–57`; `STATUS.md:99`). |
| **Weighted /100** | | **79.5** | `7.7×3 + 7.7×2.5 + 8.3×2.5 + 8.2×2`. |

Stage 1: **PASS on theme fit and real Meta use**. Theme: Push the Frontier, through a measured investigation of failure behavior and effort; Build for Your World is plausible through the concrete Indian multilingual voice-order domain, but no firsthand deployed workload is established. Public-repository eligibility is a separate **currently unmet** submission requirement: `STATUS.md:18,98` says private/publication pending, confirmed by the chair's authenticated API response `private=true` (`github-readonly.json`). Stage 1 pass does not certify every administrative requirement.

Top 5: **no**. Top 10: **yes**, against the stipulated strong hypothetical field. Scores are qualitative judgments, not actual standings or probabilities.

Three strengths:

1. The policy connects a measured change to a concrete product consequence and fallback, rather than maximizing one generic benchmark (`release/policy.json:2–8`).
2. Inspectable answers and the retained scorer false start demonstrate why a release owner should audit their measurement (`README.md:28–36`; `upgrade_gate/scorers.py:98–116`).
3. The working pipeline produces a reviewable decision, case, and report; it handles known uncertainty with INCONCLUSIVE instead of forcing a verdict (`scripts/ci_gate.py:93–145`; `upgrade_gate/gate.py:61–84`).

Three weaknesses:

1. E7 is one speaker, 15 underlying items translated three ways. Its combined wrong-or-blank result is 5 items worse, 0 better, p=.0625; the README/site/demo still foreground confirmation (`findings/LOG.md:69–74`; `README.md:11`; `web/src/components/AudioSection.tsx:114–134`; `docs/DEMO.md:14`).
2. The current workflow replays a fixed model pair and the deploy job is an illustrative echo. More seriously, the chair's authenticated GitHub API found no PRs, no upgrade-gate workflow runs, and no main branch rules/protection; `STATUS.md:92` claims a real blocked upgrade that remote evidence does not substantiate (`github-readonly.json`; `scripts/ci_gate.py:93–107`; `.github/workflows/upgrade-gate.yml:49–58`). Credit the local replay and workflow code; withhold hosted demonstration credit.
3. Measurement authority still rests on automatic heuristics and a small chosen task population: abstention matching can change harm labels, all-error scores are excluded from accuracy voting, and main accuracy intervals ignore item clusters (`upgrade_gate/behaviour.py:31–59`; `upgrade_gate/stats.py:13–27,36–48`; `README.md:125–129`).

Highest-return next action: **freeze and run one coherent, cluster-aware validation of the release decision**, with blind label audit and additional speakers, and carry its exact outcome into README/site/video. Prioritize trustworthy decision evidence over another feature. Correct the present E7 wording immediately while collecting it.

## Snapshot B — B1–B7 done exactly, no extra successes assumed

| Criterion | Weight | Low /10 | High /10 | Evidence and conditional reason |
|---|---:|---:|---:|---|
| Impact | 30% | 8.0 | 8.7 | B4 Action and B6 required checks make the mechanism much easier to adopt; low retains uncertain fresh-sample generality/label validity, high credits a successful fresh run and robust additional-speaker result. BYO contract exists, but no users or traffic are invented (`docs/BRING_YOUR_OWN_TASKS.md:38–56`; `request.md:B2–B6 table`). |
| Demo | 25% | 8.6 | 9.0 | B1 fixes the main overstatement; B2 working live mode, B6 actual merge block, and B7 recorded video complete the central experience. Even an inconclusive fresh sample can demonstrate an honest gate; high gets a clean, credible new failure finding (`docs/DEMO.md:9–22`; `request.md:B1,B2,B6,B7`). |
| Meta tooling | 25% | 8.6 | 9.0 | Fresh budget-capped Meta calls on the PR add meaningful integration credit regardless of result; favorable B2/B5 outcomes strengthen the measured unexpected finding. No additional Meta modality, agent system, or open-weights result is implied (`README.md:117–121`; `request.md:B2,B5`). |
| Technical depth | 20% | 8.4 | 9.0 | Blinded audit with κ/disagreements and frozen-rule additional-speaker rerun merit method credit; low κ or failed replication limits trust, high agreement and cross-speaker replication strengthen it. B1 does not add statistical replication; B1–B7 do not promise cluster-corrected accuracy inference (`upgrade_gate/gate.py:46–55`; `upgrade_gate/stats.py:36–48`; `request.md:B1–B5`). |
| **Weighted /100** | | **83.75** | **89.10** | Low `24 + 21.5 + 21.5 + 16.8`; high `26.1 + 22.5 + 22.5 + 18`. |

Stage 1: **PASS**, theme and genuine Meta use retained; **public-repo requirement satisfied by B6**. Top 5: **low no / high yes**. Top 10: **low yes / high yes**.

Low case: working fresh-run mechanism, but the fresh data do not reproduce a persuasive NO-GO; label audit shows consequential disagreements/weak agreement; added speakers fail to reproduce the main effect. This does not erase the original E6 evidence or deny the stipulated working mechanism. High case: the audit agrees well with rules, fresh evidence supports the release concern, and additional speakers reproduce it. Neither case invents κ, exact new counts, engagement, outside users, testimonials, virality, or customers.

B-item accounting:

- **B1:** accurate wording receives credibility/demo credit only. The existing blank-answer observations remain evidence; wording supplies no new sample or statistical confirmation.
- **B2:** working, $1-capped fresh-mode execution on the upgrade PR receives mechanism credit in both cases. A 30-clip run can be underpowered; a NO-GO is not assumed.
- **B3:** completed blinded ~60-answer audit and published κ/disagreements receive method credit in both; agreement quality remains conditional.
- **B4:** completed composite Action and short usage doc receive adoption/mechanism credit. This is not evidence that anyone adopted it.
- **B5:** 2–3 additional speakers and a frozen-rule E7 rerun receive method/coverage credit in both; favorable replication belongs only in high.
- **B6:** public repository and actual branch protection receive concrete eligibility/demo/delivery credit.
- **B7:** video and posted Discord ask/X thread receive completion credit. Engagement and virality are zero-assumed, not scored as success.

Three B strengths: (1) an actual small fresh evaluation now participates in the PR; (2) externally reusable action plus required checks closes the release-control loop; (3) audit and more speakers directly challenge measurement quality. Three B weaknesses: (1) those outcomes can still be unfavorable; (2) representativeness and cluster-corrected accuracy remain unpromised; (3) ~30 fresh clips and ~60 audit labels may leave meaningful uncertainty, and no independent adoption is established. Highest-return B next action: **resolve any audit disagreements and make the gate's accuracy/behavior decisions share a defensible item-level sampling contract**, then publish the decision's scope clearly. This is a next action, not assumed B implementation.

## Verification record and limits

Read README, STATUS, findings, experiment tables, policy, workflow, CI gate, behavior gate, accuracy gate, stats, scorer source, BYO docs, demo, and current web source. Inspected both committed `web/screenshots/home.png` and `web/screenshots/report.png`; these are static screenshots, not a claim that I exercised the browser. The homepage screenshot/source presents an illustrative one-red/two-green panel including Contributor mode, whereas the actual workflow matrix is voice-notes/real-voices/text-and-documents (`web/src/components/Hero.tsx:21–48,136–138`; `.github/workflows/upgrade-gate.yml:28`).

Independent read-only Python inspection of committed evidence and `behaviour.check` returned:

| Suite | Tasks | Responses | Verified behavior |
|---|---:|---:|---|
| voice-notes | 270 (135 audio + text twins) | 1,620 | audio silent 18→42; task p=.0000030323863; grouped 18 worse/1 better, p=.0000762939453, adjusted p=.000152587891; flagged true. |
| real-voices | 45 | 270 | silent 6→13; task p=.015625; 15 grouped items, 5 worse/0 better, p=.0625; behavior flagged false. |
| text-and-documents | 1,325 | 7,950 | response rows verified, 3,975 per model. |

Relevant record anchors: `evidence/voice-notes/run.json:1`, `evidence/real-voices/run.json:22–29`, `evidence/text-and-documents/run.json:1`; calculations follow `upgrade_gate/behaviour.py:78–105,137–189`.

E7's actual NO-GO is from the accuracy gate: the unclustered task-bootstrap upper bound −2.2 points clears the 2-point drop threshold despite the exact McNemar p=.0625 (`experiments/out/e7_real_voices.md:9`; `upgrade_gate/gate.py:65–70`). It is not the grouped combined behavior test rejecting at .05. This matters because the present headline can imply both mechanisms independently confirmed the finding.

Executor evidence supplied by chair: **178 tests passed; web build passed; replay voice-notes exit 2, real-voices exit 2, text exit 0; release file restored**. I did not rerun tests, build, or replay, mutate release files, call models, set keys, or commit. Shell actions were read-only `cat`, `nl`, `rg`, `git rev-parse HEAD`, `git status --short`, and the evidence-inspection Python snippet. Only this scorecard was written. Before this card finalized, the chair supplied authenticated read-only GitHub API verification: repo private=true; upgrade branch exists at the supplied hash; pulls endpoint returned HTTP 200 and []; only two failed canary runs and no upgrade-gate run; main rules []; branch protection 404. Full redacted record: `github-readonly.json`. This changed Demo from provisional 7.9 to 7.7 (weighted 80.0→79.5) for the unsupported hosted-demo assertion; no other judge's score was consulted. No previous-score comparison is made until the independent stage is complete. All council judges share one model family, which limits perspective diversity.


### outsider

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


### opportunity

# Independent scorecard — Opportunity / Meta

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


### executor

# Independent executor scorecard — initial, awaiting anonymous peer review

Commit A: `29862c5258f9368fdc828f4c6276546b97467eac`. Upgrade candidate: `92f04d8ede349843172c8ecb96ad9b8d92131708`. Working tree matches A for tracked files; only judging artifacts untracked. Judged as a solo indie entry for creativity, ambition and whether it works, without production-readiness penalties.

| Criterion | Weight | A /10 | Evidence and reason |
|---|---:|---:|---|
| Impact |30%|7.4|`release/policy.json:2` ties the gate to lost orders and unsafe digits; `docs/BRING_YOUR_OWN_TASKS.md:8–47` makes it adaptable. Useful demonstrated release decision, with an illustrative workflow rather than demonstrated outside adoption.|
| Demo |25%|7.8|`docs/DEMO.md:9–18` has a memorable correct-shaped wrong-pincode → red checks story; replay commands reproduce it. `README.md:11` and `docs/DEMO.md:14` oversell E7 relative to `findings/LOG.md:73`; no recorded video verified.|
| Meta tooling |25%|8.3|`evidence/real-voices/run.json:4–20` pins actual Muse models and effort; `experiments/out/e4_effort.md:5–11` exposes adverse effort behavior; `experiments/out/e3_contributor.md:5–20` compares serving modes and modalities. More than a wrapper, but no demonstrated open-weights/agentic bonus build.|
| Technical depth |20%|8.2|178 tests pass; all three replay decisions and web build work. `upgrade_gate/behaviour.py:78–105,173–189` handles clustered translations plus multiplicity; `upgrade_gate/gate.py:18–28` still treats accuracy task pairs independently.|
| Weighted /100 ||**78.75**||

Stage 1 theme fit: **pass** (Build for Your World, multilingual voice/order workflow). Real Meta use: **pass on saved evidence**, not a new API authentication check. Public repository eligibility is separate: `STATUS.md:18,98` says private/pending; live remote status to be supplied by chair. Top-5: **no**. Top-10: **yes** against a hypothetical strong indie field; these are judgments, not ranks observed among competitors.

Three strengths: (1) Runnable decision path whose failure types add information beyond average accuracy. (2) Auditable evidence, paired tests and policy, including an honest record of fixing the scorer. (3) Meta-specific multimodal/effort/Contributor experiments produce a useful engineering lesson.

Three weaknesses: (1) E7 summary claim is stronger than grouped-item evidence. (2) Current PR CI replays fixed evidence rather than collecting fresh evidence and has no reusable Action yet. (3) Generalization rests on one real speaker; accuracy uncertainty still ignores item dependence, and the launch video is pending.

Highest-return next action: implement and show the small budget-capped live gate on the upgrade PR, preserving honest GO/NO-GO/INCONCLUSIVE output whatever the new sample finds. A fresh NO-GO is not an engineering acceptance criterion.

## Snapshot B, exactly B1–B7

| Criterion | Weight | Low /10 | High /10 | Evidence and reason |
|---|---:|---:|---:|---|
| Impact |30%|7.9|8.4|`request.md:60–63` reusable Action, public access, merge enforcement and outreach lower adoption friction; no assumed outside users. High case has clearer measured generalization from B5, not imagined traction.|
| Demo |25%|8.7|9.0|`request.md:57–63` honest site wording, live workflow, blocked merge and finished three-minute video strengthen demonstrability even if fresh evidence is null. Audit disagreement and mixed speaker results could make claims harder to explain; original `docs/DEMO.md:14` also remains a potential overstatement because B1 specifies README/site only.|
| Meta tooling |25%|8.6|9.0|`request.md:58–61` adds working fresh Meta calls and broader frozen-rule evidence, beyond today's saved replay. High case adds convincing model-behavior evidence; a well-executed null still earns mechanism credit.|
| Technical depth |20%|8.7|9.1|`request.md:58–62` adds a working capped runner, blind-label audit with listed disagreements, more speakers and reusable composite Action. Low κ weakens measurement validity; high κ strengthens it. Neither value is assumed.|
| Weighted /100 ||**84.30**|**88.25**||

B Stage 1 theme and real Meta use: **pass** in both cases. Public eligibility: **satisfied by B6 assumption**, independent of Stage 1. Top-5 low: **no**, high: **yes**. Top-10 low/high: **yes/yes**.

B1 credited only for specified wording, not retroactive edits to every document. B2 credited for live mechanism, fresh sample and actual $1 cap shown working; no assumed repeated NO-GO. B3 credited for blind method and transparent disagreements; κ unknown. B4 credited for composite Action and concise instructions. B5 credited for additional speakers and frozen rerun; findings unknown. B6 credited for public repository and actual required merge checks. B7 credited for recorded video and posts; zero assumed engagement, users or virality.

B three strengths: working public integration with a real merge consequence; measurement audit plus new-speaker method; finished honest demo. B three weaknesses: label reliability and speaker outcome may limit conclusions; task-independent accuracy intervals remain; no observed user adoption or meaningful open-weights/agentic bonus evidence. B highest-return next action: resolve and show the audit's largest disagreement category with a hand-inspectable example and correct uncertainty reporting, rather than seeking a favorable replication result.

## Executor verification

`executor-commands.json` records exact executable validation commands, exit codes and full stdout. No key set and no Meta call made. No installs, product edits or commits.

- `PYTHONPATH=. .venv/bin/python -m pytest -q`: exit 0, **178 passed in 25.76s**. STATUS still says 168.
- `npm --prefix web run build`: exit 0; TypeScript check + Vite production build, 1998 transformed modules, build 1.88s. Build output under `web/dist/`.
- Candidate temporarily set to `spark-1.3@low` while preserving original bytes; three scripts run with explicit `--baseline spark-1.2@low`.
- voice-notes: exit 2 NO-GO. Accuracy inconclusive; silent failure item test 18 worse/1 better of 45 items, p=0.0000763; task counts18→42 of135.
- real-voices: exit 2 NO-GO. Silent rise grouped over15 items is5 worse/0 better, p=.0625 and not flagged. Blocking comes from accuracy CI upper−2.2 points, beyond policy−2 points. That accuracy CI still treats translations independently.
- text-and-documents: exit 0 GO, zero paired accuracy delta on1325 tasks.
- Model original bytes restored in `finally`; `git diff --exit-code -- release/model.json`: exit0. Final git status only judging directory untracked.
- Reports and gate.json generated under `/var/folders/gy/zlxy5zjj35nbfw0qnfrqzwdm0000gn/T/upgrade-gate-{voice-notes,real-voices,text-and-documents}/`; exact stdout paths recorded in JSON.

Inspection commands (all exit0): `cat request.md`; `git status --short`; `git rev-parse HEAD`; `git diff A --stat`; `rg --files … | head`; numbered reads of README, STATUS, workflow, release policy, ci_gate, spend, BYO guide, gate, behaviour, runner, client, E3/E4/E6/E7 tables, E7 metadata, DEMO, findings LOG and request; `cat web/package.json`; branch log, merge-base, diff stat and focused release-model diff. An initial full A→branch diff produced excessive output due large exported JSON; reran scoped diffs. No unexpected mutation resulted.

Workflow: `.github/workflows/upgrade-gate.yml:28,39–58` runs three independent checks, saves reports even on failure, skips the demonstration deploy job if any check fails. Deployment itself is an echo placeholder: no actual external app deployment is claimed. Paths omit `release/policy.json` (`:9–14`) and unchanged model returns success (`scripts/ci_gate.py:89–91`), so current workflow is specifically the model-change demo.

Budget: `upgrade_gate/client.py:256–269` reserves worst-case before requests and settles afterward; `spend.py:31–34,156–179` clamps local ceiling and uses an append ledger. Reservations are only process-local, so claims of cross-process strict cap deserve qualification. `runner.py:213–235` per-run budget stops scheduling after spend exceeds threshold; merely passing `--budget 1` is not the strict cap assumed by B2. These are bounded limitations, not startup-hardening demands.

Branch: merge-base is `b92153a34d1715520fa9f4aee643c81829576b5f`. Its actual base→upgrade diff is only `release/model.json`; comparing current A directly to stale upgrade HEAD creates36-file differences and is not evidence the PR deletes those later changes. Local replay above evaluates A's current gate with the upgrade model; remote runs on stale branch may use earlier gate logic. Chair handles remote verification and browser viewing; I verified build and source, not interactive browser behavior.


## Anonymous mapping revealed

{
  "A": "opportunity",
  "B": "executor",
  "C": "contrarian",
  "D": "first-principles",
  "E": "outsider"
}

## Peer discussion and single revisions

### contrarian

# Contrarian anonymous peer review and sole revision

Read only the assigned anonymous B and E cards and verified-facts.md for this peer round. I did not inspect mappings or other scorecards.

## Response B

Accurate and well supported: the executor demonstrates actual local behavior with 178 passing tests, a working web build and replay exits2/2/0. Its distinction between E7 behavior not flagging and accuracy producing NO-GO is essential. Its correction that the three-dot upgrade diff is only the model file prevents a misleading deletion accusation. The separate Stage1 and public-repository conditions and method credit for a null replication fit the indie rubric.

Missed or underemphasized: B does not report blank-only item p=.125. The phrase 'honest site wording' for B1 is appropriate only as the promised narrower wording, not a statistically confirmed blank effect. Its budget analysis is useful but B2 explicitly stipulates an effective $1 cap, so existing implementation weakness must not be used to withhold B2's projected cap credit. It handles that distinction adequately in the table.

Overcredit risk: B-low technical8.7 is generous when low κ may expose classification failures that B1–B7 do not promise to fix. A completed audit improves transparency, but measuring an unreliable release label does not itself repair it. B-low impact7.9 can be defended by Action/public/merge integration, yet its explanation should say whether severe disagreements would undermine decision usefulness. My lower bound treats those outcomes more cautiously. No forced convergence: this is a judgment difference, not an arithmetic error.

New shared API evidence means B's A demo should credit local reproducibility without implying a verified hosted PR/check run. Repository private=true is now verified, while no PR/check/protection was found by available credentials (`verified-facts.md:7`). Lack of visibility is not proof of deception or absence in every context.

## Response E

Accurate and useful: E recognizes the site's check list differs from the real workflow matrix, the difficulty of compressing multiple research stories into three minutes, and the specific B1/B7 boundary: README/site wording changes do not silently rewrite the existing recorded script. Its high-demo score below9 is a defensible consequence. Scope limited to known-answer tasks is a real reach constraint without being an invented commercial traction requirement.

Missed: the scorecard repeats a proposed 'blank answers confirmed' spoken line without distinguishing descriptive occurrence from independent-item significance. Blank-only item evidence is four worse/zero better, p=.125 (`verified-facts.md:11`). Its suggested replacement should explicitly say blanks were observed while combined grouped evidence is borderline. E also needs the newly verified local test/build/replay support, while avoiding the upgrade-PR visualization being promoted into an observed hosted run (`verified-facts.md:5,7`).

Possible overcredit: high impact8.6 is ambitious for the exact B package, since extra speakers do not guarantee independent new task items or a broader actual deployment domain. The score can still be defended by useful integration and good outcomes; it should not imply those unpromised dimensions. Low technical8.4 retains generous audit-method credit in the poor-label scenario. I regard that as optimistic conditional scoring rather than a categorical factual error.

## Sole revision of my scores

A Demo **7.8→7.6**: authenticated GitHub evidence did not independently verify a hosted upgrade PR, completed checks, deploy-skipped run or merge blocking, and confirmed current repository privacy (`verified-facts.md:7`). My initial narrative credited the existing source/local path but could read as crediting a completed hosted moment; that uncertainty now warrants a small reduction. The local experience remains reproducible, so this is not a large penalty.

A Technical **8.0→8.1**: independent executor evidence now confirms178 tests, web build and all three expected replay exits with the model restored (`verified-facts.md:5`), improving 'whether it works' confidence beyond my initial source-only inspection. This does not fix translation-dependent accuracy intervals or validate the research labels.

A Impact7.4 and Meta8.5 unchanged. Revised A weighted **78.65** (=22.2+19+21.25+16.2). Stage1 pass, top5 no, top10 yes unchanged. Stage1 does not fail merely because repo is currently private; public submission readiness remains incomplete.

B unchanged: low Impact7.2/Demo8.4/Meta8.5/Technical7.8, weighted79.45; high8.2/8.9/9.0/8.8, weighted86.95. B2/B6 explicitly supply the working public hosted mechanism, so A's newly verified hosting gap is not carried into B. B1's narrower wording gets its stipulated credit only. Low κ may reduce confidence, while a nonsignificant30-clip sample is not by itself evidence the E6 effect is false. B Stage1 pass/pass, top5 no/yes, top10 shortlist/yes unchanged.

Clarification without further score change: my initial A→old-branch comparison demonstrates version skew, not a PR deletion diff. Actual three-dot candidate change is release/model.json only (`verified-facts.md:3`). Do not describe the candidate PR as deleting the policy or later main files.

Single next action unchanged: reconcile the prominently spoken/displayed scientific story with the actual item-level policy and show robust E6 separately from E7's observed blanks and borderline combined grouped result. This has immediate credibility value; it does not require buying a favorable replication outcome.


### first-principles

# Anonymous peer review and one final revision

Reviewed only anonymous A, anonymous B, and shared verified-facts; no author mapping or other final cards. Main remains `29862c5258f9368fdc828f4c6276546b97467eac`.

## Card A

- **Correct and useful:** distinguishes actual model experiments from exposed adapters, confines Contributor claims to measured task outcomes, and identifies that finished-answer effort scores are not monotonic. Its task-count and E7 interpretation agree with shared verification (`experiments/out/e3_contributor.md:9–20`; `experiments/out/e4_effort.md:7–11`; `findings/LOG.md:73`). This is an appropriate Meta-tooling reading, rather than giving bonus credit for unmeasured Open/Wonder paths.
- **Overcredit/missed scope:** B's description of a completed “honest recorded demo” is stronger than B1–B7 promise. B1 fixes README/site; B7 records the existing script, whose E7 “It held” line remains (`docs/DEMO.md:14`; request B1/B7). The grouped caveat therefore cannot be silently propagated into the video. Some B Demo gain remains fully justified by live mode, actual protection, and completion, but 9.0 high should acknowledge this residual contradiction.
- **Possible undercredit:** Impact 7.1 is defensible, but lack of outside adoption/customer loss should be a limit on demonstrated breadth, not a threshold for an indie project's utility. A known-answer gate that catches a plausible wrong pincode already establishes a concrete mechanism (`release/policy.json:2`; `scripts/ci_gate.py:52–76`). I would value that somewhat more while retaining all sampling caveats.
- **Arithmetic:** B low components sum to **82.30**, not 82.40. The other stated A/B-high sums are correct.

## Card B

- **Correct and useful:** actual execution establishes that this works locally; it distinguishes placeholder deploy from an external deployment, notes the accuracy/behavior clustering split, and explicitly refuses to require a favorable fresh NO-GO. Its budget distinction is substantive: a per-run scheduling stop is not automatically the exact strict $1-cap mechanism stipulated for B2 (`upgrade_gate/runner.py:213–235`; `upgrade_gate/client.py:256–269`).
- **Overcredit/omission:** B low technical 8.7 gives substantial justified method credit but little visible reduction for an adverse audit that could expose the gate's wrong harm labels. Completing an audit and validating the decisions are different achievements (`upgrade_gate/behaviour.py:43–59`; request B3). I prefer a somewhat lower low case while retaining a high high case. This is a judgment difference, not a factual error.
- **Residual demo problem:** B correctly notices B1 does not fix `docs/DEMO.md:14`, yet its later B-strength phrase “finished honest demo” assumes the repair. The final narrative should retain that caveat in both B outcome cases.
- **Remote update:** fold in the shared authenticated findings rather than leaving the card's “live remote status to be supplied” unresolved. Repository is currently private with no hosted PR/check/block demonstrated to available credentials. This limits verified demonstration; it does not prove intent or fabrication (`github-readonly.json`; shared verified-facts).
- **Arithmetic:** recomputation gives A **78.85**, B low **84.35**, and B high **88.40**, rather than 78.75/84.30/88.25. Component scores should drive the aggregate.

## One revision to my initial judgment

My initial card remains preserved. A stays **Impact 7.7, Demo 7.7, Meta tooling 8.3, Technical depth 8.2 = 79.50**; Stage 1 theme/Meta pass, current public eligibility unmet, top 5 no, top 10 yes.

I revise **B Demo 8.6–9.0 → 8.4–8.8**. B1 corrects README/site only, and B7 follows the existing script; the unsupported generalized E7 “It held” line is not stipulated repaired (`docs/DEMO.md:14`). The favorable high case can support the finding with new evidence, but the literal recorded narrative still fails to explain the original grouped interpretation. This is the only score revision. Impact remains 8.0–8.7; Meta 8.6–9.0; Technical depth 8.4–9.0. Python recomputation gives **B 83.30–88.60**, with top 5 no/yes and top 10 yes/yes. Original B low arithmetic was also off: its original components sum to 83.80, not 83.75.

Two clarifications do not change A: E7's 18 blank response rows are a real descriptive observation, not 18 independent clips or grouped statistical confirmation. Blank-only majority is 0→6/45 at task p=.03125 but grouped 4 worse/0 better p=.125; combined silent behavior is 5/0 p=.0625, not flagged. The actual NO-GO is the still unclustered accuracy CI (`experiments/out/e7_real_voices.md:9,21–25`; `upgrade_gate/gate.py:65–70`; shared verified-facts). B1's assumed “confirmed for blank answers” wording earns scope/credibility credit; it adds no statistical replication. Also, a nonsignificant ~30-clip fresh result is not automatically disproof. Low represents limited or unfavorable evidence, while preserving full method/mechanism existence credit.

B still assumes exactly B1–B7: genuine working fresh $1-capped PR mechanism, completed blind κ audit with disagreements, Action, 2–3 extra speakers with frozen-rule rerun, public protected repo, recorded video and posts. No favorable κ, independent speaker populations, novel task pack, outside users, virality, or cluster-aware accuracy fix is invented. Highest-return action remains a coherent cluster-aware validation and resolution of the audit's decision-relevant disagreements; following B, align accuracy/behavior sampling contracts and communicate actual outcomes.

All weights recomputed in Python using `3*impact + 2.5*demo + 2.5*meta_tooling + 2*technical_depth`. Machine-readable result is `first-principles-final.json`. No product modifications, tests, model calls, keys, release mutation, commits, or remote writes were performed in this round.


### outsider

# Outsider: anonymous peer review and single revision

Reviewed only anonymous cards C and D and the shared facts for peer comparison; did not inspect the mapping or other cards. Initial independent card remains preserved. This is my one final revision.

## Card C

**What it gets right:** Its distinction between E6's robust item-grouped finding and E7's borderline combined behavior result is essential. I had recognized the wording gap but underweighted the fact that blank-only also lacks item-level significance: 4 worse/0 better, p=.125 (`verified-facts.md:11`; `upgrade_gate/behaviour.py:78–105`). The correction matters to the non-ML judge because “confirmed” sounds stronger than the evidence contract supports. It is also right that working methods deserve credit even if empirical results are null, and that no open-weights or agentic bonus follows from an unused adapter.

**What it misses or over/under-credits:** Its initial demo analysis does not incorporate the now-shared lack of API-visible hosted PR/check evidence. The local workflow works, but a five-minute judge has not yet been shown the promised hosted blocked-PR moment (`verified-facts.md:5–7` versus `STATUS.md:92`). Its B low Impact7.2/Tech7.8 are defensible only for consequential audit errors, not merely nonsignificance on a small fresh sample; C largely says that, but the range should make the distinction prominent. B4 and B6 definitely improve handoff and release-control reach. B high Demo8.9 is a little generous for a video still containing the exact “It held” line (`docs/DEMO.md:14`; `verified-facts.md:13`). Its caution about an older candidate branch is useful, but the diff must be framed correctly: actual three-dot candidate change is only `release/model.json`, not deletion of latest main policy (`verified-facts.md:3`).

## Card D

**What it gets right:** Concrete product consequence and fallback give the study practical meaning, with no artificial traction prerequisite (`release/policy.json:2–8`). It correctly separates verified local replay from unverified hosted checks and distinguishes Stage1 theme/Meta use from repository-publicity readiness (`verified-facts.md:5–9`). The point that transport/packaging cannot repair measurement validity is particularly strong.

**What it misses or over/under-credits:** B high Demo9.0 credits a “clean, credible new failure finding” too readily as part of the existing-script video. Favorable fresh outcomes can increase confidence conditionally, but B7 does not promise a rewritten or extended video showing those new results; B1 changes only README/site, leaving `docs/DEMO.md:14`'s “It held” line (`request.md:57–63`; `verified-facts.md:13`). Likewise “B1 fixes the main overstatement” must be limited to those two surfaces; neither the script nor every stale LOG/STATUS line is repaired. Its otherwise sound B low method credit could more explicitly allow consequential bad audit agreement to lower technical confidence despite the new mechanism. Additional speakers are method/coverage, not guaranteed independent representative replication; D's final conditional explanation largely acknowledges that.

## Revised final scores

| Criterion | Weight | A final | B low final | B high final | Evidence for retained or revised mark |
|---|---:|---:|---:|---:|---|
| Impact |30%|7.6|7.7|8.6|A and B high unchanged: real pincode harm and BYO utility (`release/policy.json:2`; `docs/BRING_YOUR_OWN_TASKS.md:38–56`). B low **7.9→7.7**: the specified audit may expose consequential label errors, reducing the intervention's trustworthy value even with easier packaging (`request.md:59–61`; `verified-facts.md:13`). A merely inconclusive 30-clip run alone does not justify this reduction.|
| Demo |25%|7.8|8.4|8.7|A **8.1→7.8**: API-visible hosted PR/check evidence unavailable; only local2/2/0 replay is verified (`verified-facts.md:5–7`), against `STATUS.md:92`'s real blocked-upgrade claim. B low **8.5→8.4**: exact-script “It held” persists and unfavorable audit outcomes sharpen that credibility problem (`docs/DEMO.md:14`; `verified-facts.md:11,13`). High unchanged: actual recorded video and B6 genuine merge block are substantial stipulated gains, but the unchanged script caps the mark (`request.md:62–63`).|
| Meta tooling |25%|8.5|8.6|8.9|Unchanged. Actual versions, multimodal twins, Contributor and effort ladder remain substantial (`findings/LOG.md:41–55,81`). B2 working fresh budget-capped integration earns method credit, not guaranteed new positive discovery (`request.md:58`; `verified-facts.md:13`).|
| Technical depth |20%|8.2|8.2|9.0|A unchanged: executor178 tests/build and local2/2/0 corroborate function (`verified-facts.md:5`), balanced against unclustered accuracy CI and unaudited labels (`upgrade_gate/gate.py:42–55`; `STATUS.md:99`). B low **8.4→8.2**: a completed audit could expose material rule errors; publishing κ is method credit, not correctness proof (`request.md:59`; `verified-facts.md:13`). High unchanged and conditional, with no invented κ or replication result.|
| **Weighted /100**||**79.90**|**82.00**|**87.75**|A `22.8+19.5+21.25+16.4`; B low `23.1+21+21.5+16.4`; B high `25.8+21.75+22.25+18`.|

Votes unchanged: A Stage1 pass, top5 no, top10 yes. B low/high Stage1 pass/pass, top5 no/yes, top10 yes/yes. Stage1 means theme plus real Meta use; A private-repo submission-readiness caveat remains, resolved only by B6. No claim of observed competitor ranking.

B1's “confirmed for blank answers” receives the stipulated wording credit only. It does not create item-independent statistical confirmation. E7 behavior is not flagged under the grouped policy; NO-GO is driven by the task-level accuracy CI upper−2.2points against−2margin, itself not cluster-aware (`verified-facts.md:11`; `upgrade_gate/gate.py:65–70`). No hosted fabrication inference is warranted: the API result is a verification limit with available credentials, while local replay is demonstrably successful (`verified-facts.md:5–7`).

Three final strengths remain: memorable wrong-pincode failure and red-check story; visual paired clips with inspectable answers; retained scorer false start. Three weaknesses: inconsistent E7 confidence language; hosted/video/live-action gaps in A; unknown labeling and task/population validity. Highest-return action remains an honest recorded blocked-PR/one-case demonstration with the item-grouped E7 caveat in the spoken line (`docs/DEMO.md:9–14`), now explicitly requiring the hosted PR/check evidence to be made reviewable. Do not assume paid fresh findings are necessary to tell the already-supported E6 story.

Revisions reflect evidence and uncertainty, not convergence toward another judge or the previous77. Initial totals80.65/83.25–87.75 become final79.90/82.00–87.75. All judges share one model family, limiting independence.


### opportunity

# Opportunity / Meta — anonymous peer review and single revision

Read only anonymous C and E, shared verified-facts, and my own initial scorecard. Initial opportunity-scorecard.md is preserved unchanged. All judgments remain for indie creativity, ambition and whether it works; outside adoption is not an eligibility threshold.

## Card C

C correctly distinguishes the real E6 item-robust finding from E7's combined-silent p=.0625, and makes the valuable further distinction that blank-only is descriptive/task-significant but not item-significant (4 worse/0 better, p=.125). This is more precise than my initial statement that blank confirmation was “separately supported.” I adopt that correction: B1's prescribed wording is editorial credit, not evidence of a new clustered finding. C also appropriately keeps task-level accuracy clustering as an unresolved issue in B (`upgrade_gate/gate.py:42–55,65–73`; `request.md:57–63`).

C's branch-staleness observation needs the shared-fact qualification: the actual three-dot candidate change is only release/model.json. An A-to-old-branch tree diff is not a PR deletion diff. The missing current policy prevents crediting a historical run as today's verified implementation; it does not establish that the PR itself deletes the policy. Hosted demonstration should also be marked unverified under the authenticated findings, rather than “blocked deployment” read as observed fact (`scripts/ci_gate.py:93–107`; shared github-readonly.json). C's final formality language of public status “pending” understates the now verified private=true state, while correctly separating that from theme/Meta Stage 1.

C is slightly conservative in B-low Meta8.5: a shown-working fresh-call workflow merits a small increase over the current saved replay even if a small sample is inconclusive, since tooling credit concerns demonstrated capability as well as positive findings (`request.md:58`). Its low impact/technical scores can reasonably fall with a poor audit; method completion alone does not guarantee measurement validity. I would not impose any additional penalty for no outside users.

## Card E

E correctly emphasizes the current demo script's unrepaired “It held” and broad minimal-effort recommendation (`docs/DEMO.md:14–15`). B1 only edits README/site and B7 records the existing script, so my initial B-high demo9.0 was over-credit. E's UI mock/matrix mismatch is also concrete, relevant presentation feedback rather than a production standard (`web/src/components/Hero.tsx:38–47`; `.github/workflows/upgrade-gate.yml:28`). Its Meta8.5 is well grounded in actual effort/Contributor/multimodal work, without counting unused adapters.

E gives B-low technical8.4 despite explicitly allowing weak label agreement. That underweights the possibility that the audit reveals actual classification defects. It also does not address the unchanged accuracy CI's task-vs-item dependence; B1–B7 do not fix that (`upgrade_gate/gate.py:42–55`; `request.md:58–61`). It is reasonable for B methods to raise the score, but 8.4 should not be automatic when those methods expose faulty evidence. Its B-high impact8.6 seems generous relative to the still narrow workload; practical reusable packaging merits credit, but recording 2–3 additional speakers does not imply varied tasks, independent usage, or demonstrated reach. This is a scope/effectiveness constraint, not a traction prerequisite.

Arithmetic: E's printed A80.65 recalculates to80.70; B-high87.75 recalculates to87.80. C's displayed totals recalculate correctly. These are small arithmetic errors, not substantive disagreements.

## Single revision of my judgment

A remains Impact7.1 / Demo8.0 / Meta8.5 / Technical8.0 = **78.55**. Its high Meta score recognizes genuine indie ambition, and its impact score reflects a bounded demonstrated workload, not a demand for commercial traction. Stage1 pass, top5 no, top10 yes. Private/public submission eligibility remains separate.

B changes once:
- Impact LOW7.5→7.4; HIGH8.2 unchanged. Audit-revealed weaknesses can offset part of reusable packaging's benefit; no adoption is presumed.
- Demo LOW8.5 unchanged; HIGH9.0→8.7 because B7 preserves the existing script's claim compression and B1 does not rewrite it (`docs/DEMO.md:14–15`; `request.md:57,63`).
- Meta LOW8.7/HIGH9.2 unchanged: the fresh PR integration works by stipulation, and favorable outcomes can strengthen the measured Meta insight. No Open/Wonder/agentic bonus added.
- Technical LOW8.4→8.0; HIGH9.0→8.7. Completed audit/replication methods merit credit in both cases, but weak agreement can reveal real scorer faults and all seven additions leave task-based accuracy CI dependencies unresolved (`upgrade_gate/gate.py:42–55,65–73`; `request.md:58–61`).

Revised B = **81.20–86.75**. Stage1 pass throughout; top5 LOW no/HIGH yes; top10 yes/yes. These are conditional evidence scenarios, not forecast success or failure. A nonsignificant 30-clip fresh run is not itself disproof. B1's blank wording is accepted exactly as prescribed, without converting descriptive/task evidence into item-level statistical confirmation (shared facts: blank-only grouped p=.125).

Highest-return A action remains a budget-capped fresh PR run with the actual grouped-policy result shown. Highest-return B action remains addressing actual blinded-audit disagreements; the final spoken script must also disclose the grouped caveat before claiming broad replication. No product edits, API calls, keys, tests/builds, release mutations or commits performed.


### executor

# Executor anonymous peer review and single revision

Read only anonymous A, anonymous D and shared verified facts in this peer round. Did not inspect mapping or other cards. No additional tests or API calls.

## Card A

What it gets right: strong distinction between actual Meta experiments and unused adapters; equal outcome scores do not establish identical answers. Its E4 denominator and cutoff caveats are useful. It correctly credits local replay while withholding hosted-check credit and explicitly preserves B2/B6 mechanism credit.

What it missed or overcredited: describing the blank-answer result as separately supported needs an exact scope. The observed 18 blank response rows out of135 are strong descriptive evidence, but blank-only majority is0→6/45 and grouped item significance is p=.125; neither18 independent clips nor a clustered confirmation follows (`verified-facts.md`, E7 paragraph; `upgrade_gate/behaviour.py:78–105`). B1 is stipulated wording, not new statistical confirmation. Its B technical low reason groups failed replication with low κ. These are different: low κ can invalidate measurement; a null fresh sample can be a correct output of a working gate and should not itself lower engineering-method credit. Its B demo account should explicitly retain the script's unrepaired 'it held' line (`docs/DEMO.md:14`; request B1 edits README/site only). Low impact7.1 is defensible but somewhat conservative given a reproducible policy-driven developer tool; no customer adoption is required by indie rules.

## Card D

What it gets right: the strongest engineering limit is decision validity, especially separate task-independent accuracy and grouped behavior guarantees. The model-change workflow is demonstrably useful even with an echo deployment. It correctly distinguishes B method credit, outcome credit, public eligibility and no mandatory commercial adoption.

What it got wrong or needs qualification: the phrase 'hosted ... demonstration is absent' is stronger than the API proof permits; with available credentials it was not verified. The API found no PRs or upgrade runs, but this is not a universal assertion that none exists. Its own later text partly qualifies this correctly (`verified-facts.md`, authenticated GitHub paragraph). B1 fixes README/site only, so it does not fully fix the recorded narrative if B7 uses `docs/DEMO.md:14` unchanged. B high impact8.7 may overweight corroborating a chosen speaker/workload effect compared with making a reusable, accurate decision; exact B still promises no new task population or actual adoption. 'Fresh data do not reproduce a persuasive NO-GO' is not inherently a validity failure for30 clips; nonsignificance may simply be honest uncertainty. Low κ, unlike a null result, can establish a real labeling defect. Preserve that distinction when explaining the score range.

## My one revision

A Demo **7.8→7.6**, A weighted **78.85→78.35**. Other A scores remain Impact7.4, Meta8.3, depth8.2. Reason: authenticated read-only remote verification could not substantiate the asserted hosted PR/check/deploy-skipped scene (`verified-facts.md`, authenticated GitHub paragraph; underlying `github-readonly.json`), and the site check panel differs from the real workflow matrix as noted by A/D. This withholds hosted demonstration credit while retaining all local replay and build credit (`executor-commands.json`). It is not an accusation of fabrication. Public repository private=true is a separate currently unmet submission eligibility condition; theme and actual Meta evidence still pass Stage1.

B remains **84.35–88.40**: B2/B6 explicitly supply the missing working live mode and protection, so A's remote-verification limitation must not reduce B. The low/high technical difference concerns whether audit disagreement exposes consequential rule errors and whether broader observed evidence improves confidence; a favorable NO-GO is never required for technical implementation credit. Fresh null/GO/inconclusive runs can be successful gate demonstrations. B1's 'confirmed for blank answers' receives only stipulated editorial-completion credit: no new clustered-significance credit. The existing script's 'it held' line remains a residual B demo risk because B1 repairs README/site only. No additional users, task diversity, κ, repeated effect or virality assumed.

A Top5 no, Top10 yes; B low Top5 no, high yes; Top10 both yes. Stage1 theme/Meta pass for all; B6 satisfies public-repository assumption. Single highest-return action remains the budget-capped live PR gate with actual observed outcome and scope, not a forced positive replication. For B, address consequential audit disagreements and align sampling/uncertainty contracts.

Arithmetic correction: initial criterion scores total78.85, not the initially printed78.75. Final78.35; B84.35–88.40. This corrects sums only, not a second substantive score revision.


## Chair report

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

