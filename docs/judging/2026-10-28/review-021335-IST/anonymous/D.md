# Anonymous response D

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
