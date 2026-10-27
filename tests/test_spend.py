"""Lifetime spending cap. Stdlib only. Run: PYTHONPATH=. python3 -m unittest tests.test_spend"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest

from tests.mock_server import mock_server
from upgrade_gate import spend
from upgrade_gate.client import ModelClient
from upgrade_gate.runner import run
from upgrade_gate.schema import Candidate, Task, read_jsonl

# each mocked call bills 1M output tokens on Spark = $4.25
BIG_USAGE = {"prompt_tokens": 0, "completion_tokens": 1_000_000}
ENV = ("MAX_TOTAL_SPEND_USD", "CANARY_BUDGET_USD", "UPGRADE_GATE_LEDGER")


class SpendBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.saved = {k: os.environ.pop(k, None) for k in ENV}
        os.environ["UPGRADE_GATE_LEDGER"] = os.path.join(self.tmp, "ledger.jsonl")
        os.environ["CANARY_BUDGET_USD"] = "0"
        os.environ["MAX_TOTAL_SPEND_USD"] = "10"
        self.canary_dir = os.path.join(self.tmp, "canary-data")
        self._orig_canary = spend.canary_spent_usd
        spend.canary_spent_usd = lambda data_dir=None: self._orig_canary(data_dir or self.canary_dir)
        self._orig_billable = spend.is_billable
        spend.is_billable = lambda base_url: True  # treat the localhost mock as the real API
        spend._ledger = None

    def tearDown(self):
        spend.canary_spent_usd = self._orig_canary
        spend.is_billable = self._orig_billable
        spend._ledger = None
        for k, v in self.saved.items():
            os.environ.pop(k, None)
            if v is not None:
                os.environ[k] = v
        shutil.rmtree(self.tmp, ignore_errors=True)


class Limits(SpendBase):
    def test_hard_ceiling_clamps(self):
        os.environ["MAX_TOTAL_SPEND_USD"] = "500"
        self.assertEqual(spend.limit_usd(), 100.0)

    def test_default_is_90(self):
        os.environ.pop("MAX_TOTAL_SPEND_USD")
        from upgrade_gate import config
        if not config.get("MAX_TOTAL_SPEND_USD"):
            self.assertEqual(spend.limit_usd(), 90.0)

    def test_mock_hosts_not_billable(self):
        self.assertFalse(self._orig_billable("http://127.0.0.1:8080/v1"))
        self.assertTrue(self._orig_billable("https://api.meta.ai/v1"))

    def test_unknown_model_refused(self):
        with self.assertRaises(spend.SpendCapError):
            spend.worst_case_usd("some-new-model", [{"role": "user", "content": "hi"}], {})


class LedgerTests(SpendBase):
    def test_reserve_refuses_over_limit_and_persists(self):
        lg = spend.ledger()
        r = lg.reserve(6.0)
        lg.settle(r, 6.0, "muse-spark-1.3")
        with self.assertRaises(spend.SpendCapError):
            lg.reserve(5.0)
        # a second process sees the same total
        self.assertAlmostEqual(spend.Ledger().spent(), 6.0)

    def test_in_flight_reservations_count(self):
        lg = spend.ledger()
        lg.reserve(6.0)
        with self.assertRaises(spend.SpendCapError):
            lg.reserve(5.0)

    def test_canary_budget_is_set_aside(self):
        os.environ["CANARY_BUDGET_USD"] = "8"
        with self.assertRaises(spend.SpendCapError):
            spend.ledger().reserve(3.0)  # 8 + 3 > 10

    def test_canary_spend_read_from_data(self):
        os.makedirs(os.path.join(self.canary_dir, "2026-10-28"))
        with open(os.path.join(self.canary_dir, "2026-10-28", "run-x.jsonl"), "w") as f:
            f.write(json.dumps({"model": "muse-spark-1.3", "usage": BIG_USAGE}) + "\n")
        os.environ["CANARY_BUDGET_USD"] = "5"
        b = spend.CanaryBudget(self.canary_dir)
        self.assertAlmostEqual(b.spent, 4.25)
        with self.assertRaises(spend.SpendCapError):
            b.reserve(1.0)


class ClientAndRunner(SpendBase):
    def test_client_stops_before_sending(self):
        with mock_server(answer="ok", usage=BIG_USAGE) as srv:
            c = ModelClient(base_url=srv.base_url, api_key="k", cache_dir="", rpm={"*": 0})
            msgs = [{"role": "user", "content": "hi"}]
            for _ in range(3):  # 3 x $4.25 = $12.75; the 3rd is allowed because 8.50 + worst case < 10
                c.chat("muse-spark-1.3", msgs, {"max_completion_tokens": 100})
            with self.assertRaises(spend.SpendCapError):
                c.chat("muse-spark-1.3", msgs, {"max_completion_tokens": 100})
            self.assertEqual(srv.calls, 3)
        self.assertAlmostEqual(spend.Ledger().spent(), 12.75)

    def test_runner_stops_and_notes_it(self):
        tasks = [Task(id="t%d" % i, pack="unit", category="c", lang="en", modality="text",
                      prompt="q%d" % i, reference="x", scorer={"type": "exact"}) for i in range(10)]
        cands = [Candidate("old", "muse-spark-1.2", {"max_completion_tokens": 100}),
                 Candidate("new", "muse-spark-1.3", {"max_completion_tokens": 100})]
        with mock_server(answer="x", usage=BIG_USAGE) as srv:
            c = ModelClient(base_url=srv.base_url, api_key="k", cache_dir="", rpm={"*": 0})
            run_dir = run(tasks, cands, baseline="old", repeats=1, out_root=self.tmp, run_id="cap",
                          client=c, workers=1, verbose=False)
            self.assertEqual(srv.calls, 3)
        rows = list(read_jsonl(os.path.join(run_dir, "responses.jsonl")))
        self.assertEqual(len(rows), 3)
        with open(os.path.join(run_dir, "run.json")) as f:
            self.assertIn("spend cap", json.dumps(json.load(f)))


if __name__ == "__main__":
    unittest.main()


class StrictRunBudget(SpendBase):
    def test_run_budget_is_never_exceeded(self):
        usage = {"prompt_tokens": 10, "completion_tokens": 1000}  # a full 1,000-token answer: $0.00425
        tasks = [Task(id="t%d" % i, pack="unit", category="c", lang="en", modality="text",
                      prompt="q%d" % i, reference="x", scorer={"type": "exact"}) for i in range(20)]
        cands = [Candidate("new", "muse-spark-1.3", {"max_completion_tokens": 1000})]
        os.environ["MAX_TOTAL_SPEND_USD"] = "50"
        with mock_server(answer="x", usage=usage) as srv:
            c = ModelClient(base_url=srv.base_url, api_key="k", cache_dir="", rpm={"*": 0}, run_budget_usd=0.01)
            run_dir = run(tasks, cands, baseline="new", repeats=1, out_root=self.tmp, run_id="strict",
                          client=c, workers=1, verbose=False, budget_usd=0.01)
            calls = srv.calls
        rows = list(read_jsonl(os.path.join(run_dir, "responses.jsonl")))
        spent = sum(r["cost_usd"] for r in rows)
        self.assertLessEqual(spent, 0.01)
        self.assertEqual(calls, 2)  # the third call's worst case would pass $0.01, so it is never sent


class AttachmentEstimate(unittest.TestCase):
    def test_audio_reserved_by_duration_not_base64_size(self):
        import base64
        ten_seconds = base64.b64encode(b"\0" * 320000).decode()  # 10 s of 16 kHz mono 16-bit audio
        msgs = [{"role": "user", "content": [{"type": "text", "text": "Listen."},
                                             {"type": "input_audio", "input_audio": {"data": ten_seconds, "format": "wav"}}]}]
        tokens = spend._input_tokens(msgs)
        self.assertGreater(tokens, 600)     # still well above the ~200 Meta bills for 10 s
        self.assertLess(tokens, 1000)       # but not the ~213,000 that counting base64 as text gave
        self.assertLess(spend.worst_case_usd("muse-spark-1.3", msgs, {"max_completion_tokens": 4000}), 0.02)
