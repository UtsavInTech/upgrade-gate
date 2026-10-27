# Build contract

Two builders work in parallel: **Claude side** and **Codex side**. Each owns its own files. Nobody edits files they don't own. This is what keeps `git pull --rebase && git push` conflict-free.

## Ownership

| Area | Owner | Files |
|---|---|---|
| Shared shapes | Claude (read-only for Codex) | `upgrade_gate/schema.py`, `docs/CONTRACT.md`, `pyproject.toml` |
| Model client, cache, cost | Claude | `upgrade_gate/client.py`, `upgrade_gate/pricing.py` |
| Task packs | Claude | `upgrade_gate/packs/**`, `data/**` |
| Runner | Claude | `upgrade_gate/runner.py` |
| Scorers + judge cascade | Claude | `upgrade_gate/scorers.py`, `upgrade_gate/judges/**` |
| CLI | Claude | `upgrade_gate/cli.py` |
| Experiments | Claude | `experiments/**` |
| Canary | Claude | `canary/**`, `.github/workflows/canary.yml` |
| **Paired statistics + gate decision** | **Codex** | `upgrade_gate/stats.py`, `upgrade_gate/gate.py` |
| **Reports** | **Codex** | `upgrade_gate/report.py`, `upgrade_gate/templates/**` |
| **Exports** | **Codex** | `upgrade_gate/export.py` |
| **Web dashboard** | **Codex** | `ui/**` |
| **Codex tests + fixtures** | **Codex** | `tests/test_stats.py`, `tests/test_gate.py`, `tests/test_report.py`, `tests/test_export.py`, `tests/fixtures/**` |
| Claude tests | Claude | every other `tests/test_*.py` |

Need a new dependency or a schema change? Add a line to `docs/CONTRACT_REQUESTS.md` (either side may append). Don't edit `pyproject.toml` or `schema.py` directly from the Codex side.

## Data flow

```
packs  ──► tasks (Task)
runner ──► results/<run_id>/run.json + responses.jsonl   (ResponseRecord)
scorers──► results/<run_id>/scores.jsonl                 (ScoreRecord)
gate   ──► results/<run_id>/gate.json                    (GateResult)      [Codex]
report ──► results/<run_id>/report.md, report.html                         [Codex]
export ──► results/<run_id>/exports/promptfoo.yaml, test_regressions.py    [Codex]
ui     ──► reads results/<run_id>/*.json(l)                                [Codex]
```

Field definitions live in [`upgrade_gate/schema.py`](../upgrade_gate/schema.py).

## Python functions each side calls

The CLI (Claude) calls these Codex functions. **Keep these signatures exactly:**

```python
# upgrade_gate/gate.py
def evaluate_run(run_dir: str, baseline: str, candidate: str,
                 max_drop: float = 0.02, alpha: float = 0.05, min_n: int = 30) -> dict:
    """Read run.json, scores.jsonl, responses.jsonl and tasks (via run_dir/tasks.jsonl).
    Write and return gate.json (GateResult dict)."""

# upgrade_gate/report.py
def write_report(run_dir: str) -> list:          # returns paths written (report.md, report.html)

# upgrade_gate/export.py
def export_regressions(run_dir: str) -> list:    # returns paths written (promptfoo.yaml, test_regressions.py)
```

The runner also writes `results/<run_id>/tasks.jsonl` (one Task dict per line), so stats and reports can read category, lang, modality and reference without importing packs.

## Conventions

- Python ≥ 3.9 (`from __future__ import annotations`; no `match`, no `X | Y` at runtime).
- Repeats: a task's pass value for a candidate is the **majority vote over its repeats**. Ties count as fail. Records with `passed: null` are excluded, and the task is dropped from the pair if either side has no scored repeat.
- Git: commit small, then `git pull --rebase origin main && git push origin HEAD:main`. Never force-push. Commit messages start with `codex:` or `claude:`.
