# Upgrade Gate dashboard

Local, static React + TypeScript dashboard. Requires Node 20.19+ or 22.12+.

```sh
cd ui
npm install
npm run dev
```

Open the Vite URL (normally http://127.0.0.1:5173). `dev` and `build` sync complete runs from `../results/*` plus the committed synthetic fixture. `npm run sync` refreshes an already running dev server's data; reload the page afterward. Incomplete runs are skipped with a message. The fixture is always clearly marked as synthetic.

```sh
npm run build
npm run preview
```

The production `dist/` folder includes the copied JSON, reports, exports, and referenced assets. Serve it as a static site at the root path. There is no backend and no model API key is needed. Review real run contents before sharing the static build: prompts and raw responses are included.

The dashboard supports run selection, click-to-filter slice plots, task selection, all repeats or individual repeats, response diff spans, attachments, costs, and mobile layouts. Generated assets under `public/runs/` are ignored; source fixtures remain in `tests/fixtures/run_demo/`.

For a new run, first call the contract APIs `evaluate_run`, `write_report`, and `export_regressions`. The standalone report link expects `write_report` to have run. Exported image cases retain attachment paths; model fixtures/providers must send these images.
