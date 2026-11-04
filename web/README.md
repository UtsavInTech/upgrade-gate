# Upgrade Gate: the site

- `#/` — overview: the headline result, real answers from both models, and the gate's three decisions.
- `#/voiceorder` — the app being protected; plays saved notes, or a new recording when the server has a key.
- `#/findings` — findings and methods: voice notes, effort ladder, scoring lesson, Contributor mode, how it works.
- `#/report/<run>` — the product view: run tabs with gate verdicts, pass-rate summary, slice table with
  95% ranges, every task with both versions' answers, filters, search, and a detail panel with audio,
  documents, all three tries and the scorer's reason. Runs include `e6-audio`, `e9-route-synth`, `e10-real-voices`, `e1-upgrade`, `e3-contributor`.
- `#/record` — record the voice-note lines in a real voice; used for E7 and E10.
- `#/audit` — blind relabelling of a sample of answers, to check the failure-type labels.

```bash
npm --prefix web install
npm --prefix web run data   # export saved runs from results/ into web/public (no API calls)
npm --prefix web run dev    # http://127.0.0.1:5191
npm --prefix web run build  # static site in web/dist
```

Stack: Vite, React 19, TypeScript, Tailwind CSS 4, Motion. `scripts/export_web.py` reuses the experiments'
own analysis code, so the numbers match `experiments/out/*.md`. The exported data and compressed clips in
`web/public` are committed so a fresh clone works without `results/`.
