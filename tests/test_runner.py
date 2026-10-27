"""Runner tests against the local mock. Run: pytest tests/test_runner.py  or  python -m unittest tests.test_runner"""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from collections import Counter

from tests.mock_server import mock_server
from upgrade_gate.client import ModelClient
from upgrade_gate.runner import estimate_cost, run
from upgrade_gate.schema import Candidate, Task, read_jsonl


def _tasks(n=10):
    return [Task(id="t%02d" % i, pack="unit", category="math" if i % 2 else "cls", lang="en", modality="text",
                 prompt="What is %d+%d?" % (i, i), reference=str(2 * i), scorer={"type": "exact"})
            for i in range(n)]


CANDS = [Candidate("old", "muse-spark-1.2", {"reasoning_effort": "low"}),
         Candidate("new", "muse-spark-1.3", {"reasoning_effort": "low"})]


def _client(srv, tmp):
    return ModelClient(base_url=srv.base_url, api_key="k", cache_dir=os.path.join(tmp, "cache"),
                       rpm={"*": 0}, backoff_base=0.005)


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _answer(req):
    return "answer from %s to %s" % (req["model"], req["messages"][-1]["content"])


class TestRunner(unittest.TestCase):
    def test_writes_files_with_counts(self):
        with tempfile.TemporaryDirectory() as tmp, mock_server(answer=_answer, fail_every=7) as srv:
            out = os.path.join(tmp, "results")
            d = run(_tasks(10), CANDS, "old", repeats=3, out_root=out, run_id="r1", workers=4,
                    client=_client(srv, tmp), notes="unit", seed=123, verbose=False)
            self.assertEqual(d, os.path.join(out, "r1"))
            info = _load(os.path.join(d, "run.json"))
            self.assertEqual(info["run_id"], "r1")
            self.assertEqual(info["baseline"], "old")
            self.assertEqual(info["n_tasks"], 10)
            self.assertEqual(info["repeats"], 3)
            self.assertEqual(info["packs"], ["unit"])
            self.assertEqual([c["name"] for c in info["candidates"]], ["old", "new"])
            self.assertIn("shuffle_seed=123", info["notes"])
            self.assertIn("unit", info["notes"])
            self.assertEqual(len(list(read_jsonl(os.path.join(d, "tasks.jsonl")))), 10)
            rows = list(read_jsonl(os.path.join(d, "responses.jsonl")))
            self.assertEqual(len(rows), 60)
            keys = {(r["task_id"], r["candidate"], r["repeat"]) for r in rows}
            self.assertEqual(len(keys), 60)
            self.assertTrue(all(r["error"] is None for r in rows))  # 429s retried away
            self.assertTrue(all(not r["cached"] for r in rows))     # repeats are real calls
            self.assertEqual(Counter(r["candidate"] for r in rows), {"old": 30, "new": 30})
            r0 = [r for r in rows if r["candidate"] == "new"][0]
            self.assertIn("muse-spark-1.3", r0["text"])
            self.assertGreater(r0["cost_usd"], 0)
            self.assertEqual(r0["usage"]["reasoning_tokens"], 20)

    def test_repeats_not_cached_but_rerun_cached(self):
        with tempfile.TemporaryDirectory() as tmp, mock_server() as srv:
            client = _client(srv, tmp)
            out = os.path.join(tmp, "results")
            run(_tasks(4), CANDS[:1], "old", repeats=3, out_root=out, run_id="a", client=client, verbose=False)
            self.assertEqual(srv.calls, 12)
            d = run(_tasks(4), CANDS[:1], "old", repeats=3, out_root=out, run_id="b", client=client, verbose=False)
            self.assertEqual(srv.calls, 12)  # all from cache
            rows = list(read_jsonl(os.path.join(d, "responses.jsonl")))
            self.assertEqual(len(rows), 12)
            self.assertTrue(all(r["cached"] for r in rows))

    def test_budget_stop(self):
        with tempfile.TemporaryDirectory() as tmp, mock_server() as srv:
            # each call: 90 in + 10 cached + 50 out on spark-1.2 = ~0.000326 USD
            d = run(_tasks(50), CANDS, "old", repeats=2, out_root=os.path.join(tmp, "r"), run_id="b",
                    workers=1, budget_usd=0.002, client=_client(srv, tmp), verbose=False)
            rows = list(read_jsonl(os.path.join(d, "responses.jsonl")))
            self.assertLess(len(rows), 200)
            self.assertGreaterEqual(len(rows), 6)
            spent = sum(r["cost_usd"] for r in rows)
            self.assertGreater(spent, 0.002)
            self.assertLess(spent, 0.002 + 0.001)
            info = _load(os.path.join(d, "run.json"))
            self.assertIn("budget stop", info["notes"])
            self.assertEqual(info["budget_usd"], 0.002)

    def test_resume(self):
        with tempfile.TemporaryDirectory() as tmp, mock_server() as srv:
            out = os.path.join(tmp, "r")
            client = _client(srv, tmp)
            run(_tasks(20), CANDS, "old", repeats=1, out_root=out, run_id="x", workers=1,
                budget_usd=0.003, client=client, verbose=False)
            path = os.path.join(out, "x", "responses.jsonl")
            first = list(read_jsonl(path))
            self.assertLess(len(first), 40)
            calls_before = srv.calls
            # add an error row: it should be dropped and redone on resume
            done_key = (first[0]["task_id"], first[0]["candidate"])
            run(_tasks(20), CANDS, "old", repeats=1, out_root=out, run_id="x", workers=3, client=client,
                verbose=False)
            rows = list(read_jsonl(path))
            self.assertEqual(len(rows), 40)
            self.assertEqual(len({(r["task_id"], r["candidate"], r["repeat"]) for r in rows}), 40)
            self.assertEqual(srv.calls - calls_before, 40 - len(first))
            self.assertIn(done_key, {(r["task_id"], r["candidate"]) for r in rows})
            info = _load(os.path.join(out, "x", "run.json"))
            self.assertIn("resumed", info["notes"])

    def test_resume_retries_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "r")
            with mock_server(status_for_model={"muse-spark-1.3": 400}) as srv:
                run(_tasks(3), CANDS, "old", repeats=1, out_root=out, run_id="e", client=_client(srv, tmp),
                    verbose=False)
            path = os.path.join(out, "e", "responses.jsonl")
            rows = list(read_jsonl(path))
            self.assertEqual(sum(1 for r in rows if r["error"]), 3)
            with mock_server() as srv2:
                run(_tasks(3), CANDS, "old", repeats=1, out_root=out, run_id="e", client=_client(srv2, tmp),
                    verbose=False)
                self.assertEqual(srv2.calls, 3)
            rows = list(read_jsonl(path))
            self.assertEqual(len(rows), 6)
            self.assertTrue(all(r["error"] is None for r in rows))

    def test_bad_attachment_recorded_not_raised(self):
        with tempfile.TemporaryDirectory() as tmp, mock_server() as srv:
            t = Task(id="img", pack="p", category="c", lang="en", modality="image", prompt="?",
                     reference="x", scorer={}, attachments=[os.path.join(tmp, "missing.png")])
            d = run([t], CANDS[:1], "old", repeats=1, out_root=tmp, run_id="m", client=_client(srv, tmp),
                    verbose=False)
            rows = list(read_jsonl(os.path.join(d, "responses.jsonl")))
            self.assertEqual(len(rows), 1)
            self.assertIn("FileNotFoundError", rows[0]["error"])

    def test_validation(self):
        with self.assertRaises(ValueError):
            run(_tasks(1), CANDS, "missing", out_root=tempfile.mkdtemp(), verbose=False)

    def test_estimate_cost(self):
        tasks = [Task(id="a", pack="p", category="c", lang="en", modality="text", prompt="x" * 4000,
                      reference="", scorer={}),
                 Task(id="b", pack="p", category="c", lang="en", modality="image", prompt="",
                      reference="", scorer={}, attachments=["a.png"])]
        est = estimate_cost(tasks, CANDS + [Candidate("c", "muse-spark-1.3-contributor")], repeats=2,
                            avg_output_tokens=300)
        self.assertEqual(est["n_calls"], 12)
        in_tok = (1000 + 8) + (0 + 8 + 1000)
        exp_std = (in_tok * 2 * 1.25 + 300 * 2 * 2 * 4.25) / 1e6
        self.assertAlmostEqual(est["per_candidate_usd"]["old"], exp_std, places=6)
        self.assertAlmostEqual(est["per_candidate_usd"]["c"], (in_tok * 2 * 0.10 + 1200 * 0.20) / 1e6, places=6)
        self.assertAlmostEqual(est["total_usd"], sum(est["per_candidate_usd"].values()), places=6)


if __name__ == "__main__":
    unittest.main()
