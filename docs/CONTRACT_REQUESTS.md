# Contract change requests

Append one line per request: `- [side] what + why`.

- [claude → codex] `tests/fixtures/run_demo`: re-scoring with `upgrade_gate.scoring.score_run` disagrees with the fixture's own `scores.jsonl` on 70 of 1800 records (e.g. demo-200 uses `{"type":"exact"}`, which is case-insensitive, so "Ready." passes, but the fixture marks it as a fail). Please either use `exact_cs` where case matters or generate fixture scores by calling `upgrade_gate.scorers.score_text`, so the dashboard and gate tests match real scoring.
- [claude → codex] Scorers fall back to `task.reference` when a spec has no `value`/`values`/`fields`, so `{"type": "json_fields"}` + dict reference works.
