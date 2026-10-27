# Upgrade Gate

**Should you upgrade from Muse Spark 1.2 to 1.3?** Upgrade Gate replays the same tasks through both versions and gives a **go / no-go** with evidence:
- paired statistics (exact McNemar, bootstrap CIs, Holm correction, sequential stopping),
- per-slice breakdowns (category, language, modality), because an average can improve while one slice breaks,
- cost difference,
- the exact regressed cases, exported as promptfoo and pytest tests for your own suite.

Built for the Meta Global AI Developer Hackathon (indie track).

## Quick start

```bash
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
cp .env.example .env            # add MODEL_API_KEY
.venv/bin/upgrade-gate check    # one tiny call per model
.venv/bin/upgrade-gate estimate --packs math-pairs,docs-synth --n 40
.venv/bin/upgrade-gate all --packs math-pairs,extract-pairs,intent,ifeval,docs-synth \
    -b spark-1.2@low -c spark-1.3@low --n 40 --budget 10 --yes
```
Exit code: 0 = go, 2 = no-go, 3 = inconclusive, so it can gate a CI pipeline.

**Spending cap.** Every real API call reserves its worst-case cost first and is refused if the
lifetime total could pass `MAX_TOTAL_SPEND_USD` (default $90; anything above $100 is clamped to
$100). Spend is logged in `.spend/ledger.jsonl`; don't delete it. `upgrade-gate spend` shows
what's left. The GitHub canary has its own `CANARY_BUDGET_USD` (default $15), which is set aside
inside the same limit. A run stopped by the cap can be resumed with the same `--run-id`.

## Layout

| Path | What |
|---|---|
| `upgrade_gate/client.py` | Meta Model API client: retries, rate limits, disk cache, cost |
| `upgrade_gate/packs/` | Task packs with known answers (math, extraction, intent, instructions, invoice images/PDFs; en / hi / hinglish matched pairs) |
| `upgrade_gate/runner.py` | Replays tasks × candidates × repeats under a budget |
| `upgrade_gate/scorers.py`, `judges/` | Deterministic scoring + blind LLM judge cascade |
| `upgrade_gate/stats.py`, `gate.py` | Paired stats and the go/no-go rule |
| `upgrade_gate/report.py`, `export.py` | HTML/Markdown report, promptfoo + pytest export |
| `ui/` | Dashboard used in the demo |
| `canary/` | 4×-daily drift monitor for pinned model IDs (H5) |
| `experiments/` | Pre-registered studies E1–E5 |
| `findings/LOG.md` | Hypotheses, literature, results |

Docs: [STATUS](STATUS.md) · [research guide](RESEARCH_GUIDE.md) · [contract](docs/CONTRACT.md) · [Meta API notes](docs/META_API.md)
