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
