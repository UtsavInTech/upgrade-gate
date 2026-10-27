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
