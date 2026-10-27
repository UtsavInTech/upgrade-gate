# Upgrade Gate — results site

One-page story of the experiments: the audio finding, the scoring lesson, the Contributor-mode cost
result and how the gate works. Light and dark themes, presenter mode (Present button, then ← / →).

```bash
npm --prefix web install
npm --prefix web run data   # export saved runs from results/ into web/public (no API calls)
npm --prefix web run dev    # http://127.0.0.1:5191
npm --prefix web run build  # static site in web/dist
```

Stack: Vite, React 19, TypeScript, Tailwind CSS 4, Motion. Data comes from `scripts/export_web.py`, which
reuses the experiments' own analysis code, so the numbers match `experiments/out/*.md`.
`web/public/data/site.json` and the example clips are committed so a fresh clone works without `results/`.
