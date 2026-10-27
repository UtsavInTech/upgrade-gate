# Saved-run evidence dashboard

The dashboard makes no model calls. It reads local saved runs and a clearly labeled synthetic fallback.

```sh
npm --prefix ui ci
npm --prefix ui run dev
```

Install the Python project in `.venv` first (`pip install -e '.[dev]'`), because sync uses `upgrade_gate.report.build_presentation` for the same numbers as the report. Set `UPGRADE_GATE_PYTHON` to use a different Python executable. Requires Node 20.19+ or 22.12+.

`dev` and `build` discover directories under `results/` and `tests/fixtures/run_demo/`. Real runs sort before demo data. A valid `run.json` appears in the selector immediately; missing or partially written score/response files produce a pending entry. A complete run needs no pre-existing gate file. Sync computes every baseline-versus-candidate comparison from metadata, including multi-candidate effort runs. Unknown strict scores remain unavailable.

The dev server watches run metadata, score snapshots and gate files, debounces writes, and sends a refresh event. The browser also checks the index every three seconds. It keeps the current run selected when another arrives. Response streaming alone does not rebuild all runs on every paid call. Unchanged complete snapshots are cached; incomplete updates retain the last complete copied run. A static production build is a snapshot, refreshed with `npm --prefix ui run sync` and rebuilt with `npm --prefix ui run build`. There is no backend or external runtime request.

Content correctness controls the release banner. The score toggle changes charts and answer labels; it does not silently redefine the release criterion. The old-scoring before/after panel is distinct from today's strict-format metric. It joins saved rows by task/candidate/repeat and restricts the headline comparison to common paired tasks.

Heatmap rows are category × modality, columns are language. Cells require 10 pairs and Holm-adjusted p below alpha for red/green; other cells are grey with numerical labels. Their exploratory test family is separate from the gate's marginal slices. Select a cell to open its evidence. Each answer retains content, strict, scorer detail, and all repeat controls. Cost normalizes to one response per task; mode repricing is labeled as an estimate at recorded tokens.

Presenter mode has six sections. Use ← / →, the onscreen buttons, or Esc to exit. Arrow keys are left alone inside text fields and selects. Help controls explain charts without relying on hover. Mobile heatmaps scroll inside their table rather than widening the whole page.

```sh
npm --prefix ui test
npm --prefix ui run build
npm --prefix ui run preview
```

`ui/public/runs/` and `ui/dist/` are ignored. Nothing under `results/` is added to git by these scripts. Static builds include prompts, answers, and attachments: share only data you intend to distribute. Repo-relative attachments are copied with path containment checks. Generated tests and docs explain how model integrations must send images.
