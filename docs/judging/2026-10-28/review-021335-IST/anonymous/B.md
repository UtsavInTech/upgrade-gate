# Anonymous response B

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
