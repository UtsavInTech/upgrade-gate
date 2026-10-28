# 3. What is worth adding (and how)

Ranked by how much each moves the judging, against time. All of these are mine unless marked.
Nothing here needs a new experiment, and nothing redesigns the site.

## A. Must-add (they support the "must do" list)

### A1. Static VoiceOrder for the hosted site — 2 h
**Why:** today VoiceOrder needs the local Python server. On GitHub Pages judges would see an empty app.
**How:**
1. `scripts/export_web.py` writes `web/public/data/voiceorder.json`: for each sample note, the saved 1.2 and 1.3
   answers (already in the E6 run, $0), the shop checks and the verdict.
2. `VoiceOrder.tsx`: if `/api/voiceorder/config` fails, load the JSON instead. Samples work the same.
   The "Record your own" tab shows "Runs locally only: clone the repo" instead of a broken button.
3. Test: `npm run build && npx vite preview`, with the Python server stopped.

### A2. GitHub Pages workflow — 45 min
**How:** `.github/workflows/pages.yml`: on push to main → `npm ci && npm run build` in `web/` → `actions/upload-pages-artifact` → `actions/deploy-pages`.
Set Vite `base: "./"` (hash routes already work from any folder). You enable Pages once: Settings → Pages → Source: GitHub Actions.

### A3. Post the result as a PR comment — 1.5 h
**Why:** today the result sits in the Actions summary, one click deep. A comment on the PR is what a team actually sees.
**How:**
1. `scripts/ci_gate.py` also writes the summary markdown to `$RUNNER_TEMP/upgrade-gate-<name>.md`.
2. New step in `action.yml` (input `comment: true`, needs `pull-requests: write`): find an existing comment with the
   marker `<!-- upgrade-gate:<name> -->` via `gh api`, edit it, or create one. So pushes update one comment, not spam.
3. Workflow: add `permissions: pull-requests: write`. Test on PR #1 (replay mode, $0).

## B. High value, do if time allows

### B1. "Why not a leaderboard or Promptfoo?" section — 1 h
**Why:** the first question any judge asks. Answer in a small table on the site and README:
leaderboards = someone else's data, one average score; Promptfoo/Braintrust = CI runs on your data but report
pass rates; Upgrade Gate = your data, *how failures change* (blank / wrong-with-no-warning) with grouped statistics,
a written release policy, and a blocking PR check. Be fair: say what they do better (dashboards, many providers).

### B2. `upgrade-gate init` — 3 h
**Why:** turns "you could use this" into "it takes 5 minutes". Strongest proof of reuse.
**How:**
1. New CLI command writes into the current repo: `release/model.json`, `release/policy.json` (with a `why` to fill in),
   `tasks/my_tasks.jsonl` (3 examples), `.github/workflows/upgrade-gate.yml` using the Action in live mode.
2. Refuses to overwrite existing files; prints the two things to do next (add `MODEL_API_KEY`, open a PR changing the model).
3. Test in a temp folder; then **demo it**: a second tiny public repo (e.g. `voiceorder-shop`) made only with `init`,
   with one PR that the gate checks. Takes ~$0.15.

### B3. Canary drift on the site — 1.5 h (after ~5 days of data, Nov 2)
**Why:** answers "does the same pinned model change over days?" Meta-specific and nobody else shows it.
**How:** `scripts/canary_summary.py` reads the canary runs (artifacts or committed logs), per day pass rate and
answers that changed between runs of the same prompt; small line chart + "N of 300 answers changed" on the site.
Report "no drift" plainly if that's the result.

## C. Polish (only after A and B)

| # | Item | Time | How |
|---|---|---|---|
| C1 | Mobile and accessibility pass | 1 h | 375 px check of every page, keyboard focus, contrast in dark mode |
| C2 | README top section rewrite | 30 min | 5 lines: problem → what it does → one result → link to PR #1 → link to site |
| C3 | Third judging council | 1 h | Run `docs/judging/COUNCIL_PROMPT.md` on Nov 1, fix the top 2 |
| C4 | Outreach (you) | 30 min | Discord + X post from `docs/OUTREACH.md`; if someone tries it, quote them |

## Not doing (and why)

- **More experiments** beyond E7b: E8 shows the risk of chasing every lead. Our evidence is enough; more voices is what's missing.
- **Following E8's "gives up on corrections" lead**: not pre-registered, small; logged as a lead only.
- **Site redesign**: the design is settled; changes now cost time and risk breakage.
- **Other model families**: the story is the Spark 1.2 → 1.3 upgrade.
