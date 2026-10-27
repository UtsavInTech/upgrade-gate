"""Judge, cascade and score_run tests. No network. Run:
PYTHONPATH=. python3 -m unittest tests/test_judges.py"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
import threading
import unittest
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from upgrade_gate.judges import Cascade, Judge, LLMJudge, OpenAICompatJudge, build_judge_messages, parse_verdict
from upgrade_gate.judges.base import VERDICT_SCHEMA
from upgrade_gate.schema import Task, read_jsonl
from upgrade_gate.scoring import judge_agreement, score_run


@dataclass
class FakeResult:
    text: Optional[str]
    cost_usd: float = 0.001
    error: Optional[str] = None
    usage: Dict[str, int] = field(default_factory=dict)


class FakeClient:
    """Returns canned outputs; records every call."""

    def __init__(self, outputs=None, fn=None, reject_rf=False):
        self.outputs = list(outputs or [])
        self.fn = fn
        self.reject_rf = reject_rf
        self.calls: List[dict] = []
        self.lock = threading.Lock()

    def chat(self, model_id, messages, params=None, **kw):
        with self.lock:
            self.calls.append({"model_id": model_id, "messages": messages, "params": dict(params or {})})
        if self.reject_rf and "response_format" in (params or {}):
            return FakeResult(None, 0.0, "HTTP 400: response_format not supported")
        if self.fn:
            return FakeResult(self.fn(model_id, messages))
        return FakeResult(self.outputs.pop(0) if self.outputs else None, error=None if self.outputs or True else "x")


def verdict(correct, conf=0.9, why="ok"):
    return json.dumps({"correct": correct, "confidence": conf, "rationale": why})


TASK = Task(id="t1", pack="p", category="qa", lang="en", modality="text",
            prompt="Capital of France?", reference="Paris", scorer={"type": "exact"})


class StaticJudge(Judge):
    def __init__(self, name, passed, conf):
        self.name, self.passed, self.conf, self.n = name, passed, conf, 0

    def vote(self, task, text):
        self.n += 1
        return {"judge": self.name, "passed": self.passed, "confidence": self.conf,
                "rationale": "static", "cost_usd": 0.01}


class TestParse(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(parse_verdict(verdict(True, 0.7, "x")), (True, 0.7, "x"))
        self.assertEqual(parse_verdict('```json\n{"correct": "false", "confidence": 80}\n```')[:2], (False, 0.8))
        self.assertEqual(parse_verdict("<think>hmm</think>" + verdict(False))[0], False)
        self.assertIsNone(parse_verdict("I think it's right")[0])
        self.assertIsNone(parse_verdict('{"confidence": 0.5}')[0])
        self.assertIsNone(parse_verdict(None)[0])


class TestLLMJudge(unittest.TestCase):
    def test_vote_and_schema(self):
        c = FakeClient([verdict(True, 0.95, "matches")])
        j = LLMJudge("spark-1.3", "muse-spark-1.3", c, params={"reasoning_effort": "low"})
        v = j.vote(TASK, "Paris")
        self.assertEqual(v["judge"], "spark-1.3")
        self.assertTrue(v["passed"])
        self.assertAlmostEqual(v["confidence"], 0.95)
        self.assertEqual(set(v), {"judge", "passed", "confidence", "rationale", "cost_usd"})
        call = c.calls[0]
        self.assertEqual(call["model_id"], "muse-spark-1.3")
        self.assertEqual(call["params"]["response_format"], VERDICT_SCHEMA)
        self.assertEqual(call["params"]["reasoning_effort"], "low")

    def test_parse_failure_is_none(self):
        v = LLMJudge("j", "m", FakeClient(["not json"])).vote(TASK, "Paris")
        self.assertIsNone(v["passed"])

    def test_api_error_is_none(self):
        class Err(FakeClient):
            def chat(self, *a, **k):
                return FakeResult(None, 0.0, "timeout")
        v = LLMJudge("j", "m", Err()).vote(TASK, "Paris")
        self.assertIsNone(v["passed"])
        self.assertIn("api error", v["rationale"])

    def test_response_format_fallback(self):
        c = FakeClient([verdict(False, 0.9)], reject_rf=True)
        j = LLMJudge("j", "m", c)
        v = j.vote(TASK, "Lyon")
        self.assertFalse(v["passed"])
        self.assertEqual(len(c.calls), 2)
        self.assertNotIn("response_format", c.calls[1]["params"])
        j.vote(TASK, "Lyon")  # remembers: no response_format next time
        self.assertEqual(len(c.calls), 3)
        self.assertNotIn("response_format", c.calls[2]["params"])

    def test_blind_prompt(self):
        t = Task(id="t9", pack="p", category="qa", lang="en", modality="text", prompt="2+2?",
                 reference=4, scorer={"type": "number"}, meta={"candidate": "spark-1.3", "model": "muse-spark-1.3"})
        c = FakeClient([verdict(True)])
        LLMJudge("j", "muse-wonder-1.0", c).vote(t, "<think>easy</think>4")
        blob = json.dumps(c.calls[0]["messages"])
        for leak in ("spark-1.3", "spark-1.2", "muse-spark", "candidate model"):
            self.assertNotIn(leak, blob)
        self.assertIn("2+2?", blob)
        self.assertNotIn("easy", blob)  # reasoning block stripped
        msgs = build_judge_messages(TASK, "Paris")
        self.assertIn("Paris", msgs[1]["content"])

    def test_open_compat_uses_injected_client(self):
        c = FakeClient([verdict(True)])
        j = OpenAICompatJudge("spark-open", base_url="http://x", api_key="k", model="muse-spark-open", client=c)
        self.assertTrue(j.vote(TASK, "Paris")["passed"])
        self.assertEqual(c.calls[0]["model_id"], "muse-spark-open")

    def test_open_compat_needs_config(self):
        old = {k: os.environ.pop(k, None) for k in ("OPEN_JUDGE_BASE", "OPEN_JUDGE_MODEL")}
        cwd = os.getcwd()
        tmp = tempfile.mkdtemp()
        try:
            os.chdir(tmp)  # no .env here
            with self.assertRaises(ValueError):
                OpenAICompatJudge("x")
        finally:
            os.chdir(cwd)
            shutil.rmtree(tmp)
            for k, v in old.items():
                if v is not None:
                    os.environ[k] = v


class TestCascade(unittest.TestCase):
    def test_confident_cheap_no_escalation(self):
        cheap, strong = StaticJudge("cheap", True, 0.9), StaticJudge("strong", False, 0.99)
        v = Cascade(cheap, strong, 0.8).vote(TASK, "Paris")
        self.assertTrue(v["passed"])
        self.assertFalse(v["escalated"])
        self.assertEqual(strong.n, 0)
        self.assertEqual(len(v["votes"]), 1)
        self.assertEqual(v["judge"], "cascade:cheap->strong")

    def test_unsure_cheap_escalates(self):
        cheap, strong = StaticJudge("cheap", True, 0.5), StaticJudge("strong", False, 0.99)
        v = Cascade(cheap, strong, 0.8).vote(TASK, "Paris")
        self.assertFalse(v["passed"])
        self.assertTrue(v["escalated"])
        self.assertEqual([x["judge"] for x in v["votes"]], ["cheap", "strong"])
        self.assertAlmostEqual(v["cost_usd"], 0.02)

    def test_parse_fail_escalates(self):
        cheap, strong = StaticJudge("cheap", None, 0.99), StaticJudge("strong", True, 0.9)
        v = Cascade(cheap, strong).vote(TASK, "Paris")
        self.assertTrue(v["escalated"])
        self.assertTrue(v["passed"])


# ---------------------------------------------------------------- score_run

def _write_run(d):
    tasks = [
        dict(id="a", pack="p", category="qa", lang="en", modality="text", prompt="Capital of France?",
             reference="Paris", scorer={"type": "exact"}, attachments=[], pair_id=None, meta={}),
        dict(id="b", pack="p", category="math", lang="hi", modality="text", prompt="२+२?",
             reference=4, scorer={"type": "number"}, attachments=[], pair_id=None, meta={}),
        dict(id="c", pack="p", category="open", lang="en", modality="text", prompt="Write a haiku",
             reference="any haiku", scorer={}, attachments=[], pair_id=None, meta={}),
    ]
    rows = []
    for cand, ta, tb in (("spark-1.2", "Paris", "5"), ("spark-1.3", "Lyon", "४")):
        rows.append(dict(run_id="r1", task_id="a", candidate=cand, repeat=0, text=ta, usage={}, cost_usd=0.0, latency_ms=1))
        rows.append(dict(run_id="r1", task_id="b", candidate=cand, repeat=0, text=tb, usage={}, cost_usd=0.0, latency_ms=1))
        rows.append(dict(run_id="r1", task_id="c", candidate=cand, repeat=0, text="old pond", usage={}, cost_usd=0.0, latency_ms=1))
    rows.append(dict(run_id="r1", task_id="a", candidate="spark-1.3", repeat=1, text=None, usage={},
                     cost_usd=0.0, latency_ms=1, error="HTTP 500"))
    with open(os.path.join(d, "tasks.jsonl"), "w", encoding="utf-8") as f:
        for t in tasks:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")
    with open(os.path.join(d, "responses.jsonl"), "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(os.path.join(d, "run.json"), "w") as f:
        json.dump({"run_id": "r1"}, f)


def always_yes(model_id, messages):
    return verdict(True, 0.9)


def says_correct_if_paris_or_4(model_id, messages):
    body = messages[1]["content"].split("## Candidate response", 1)[1]
    ok = ("Paris" in body) or ("४" in body)
    return verdict(ok, 0.9)


class TestScoreRun(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        _write_run(self.d)

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_deterministic(self):
        path = score_run(self.d)
        recs = list(read_jsonl(path))
        self.assertEqual(len(recs), 7)
        by = {(r["task_id"], r["candidate"], r["repeat"]): r for r in recs}
        self.assertTrue(by[("a", "spark-1.2", 0)]["passed"])
        self.assertFalse(by[("a", "spark-1.3", 0)]["passed"])
        self.assertFalse(by[("b", "spark-1.2", 0)]["passed"])
        self.assertTrue(by[("b", "spark-1.3", 0)]["passed"])   # Devanagari digit
        self.assertIsNone(by[("c", "spark-1.2", 0)]["passed"])  # no scorer
        err = by[("a", "spark-1.3", 1)]
        self.assertIsNone(err["passed"])
        self.assertIsNone(err["score"])
        self.assertIn("api error", err["detail"])
        self.assertTrue(all(r["method"] == "deterministic" and r["run_id"] == "r1" for r in recs))

    def test_both_records_all_votes(self):
        yes = LLMJudge("yes-man", "m1", FakeClient(fn=always_yes))
        fair = LLMJudge("fair", "m2", FakeClient(fn=says_correct_if_paris_or_4))
        path = score_run(self.d, judges=[yes, fair], mode="both", workers=4)
        recs = list(read_jsonl(path))
        by = {(r["task_id"], r["candidate"], r["repeat"]): r for r in recs}
        r = by[("a", "spark-1.3", 0)]
        self.assertFalse(r["passed"])  # truth stays deterministic
        self.assertEqual(r["method"], "deterministic")
        self.assertEqual(sorted(v["judge"] for v in r["judge_votes"]), ["fair", "yes-man"])
        self.assertGreater(r["cost_usd"], 0)
        self.assertEqual(by[("a", "spark-1.3", 1)]["judge_votes"], [])  # api error: no judging

        ag = judge_agreement(path)
        self.assertEqual(ag["n_truth_records"], 4)
        yj, fj = ag["judges"]["yes-man"], ag["judges"]["fair"]
        self.assertEqual(yj["n"], 4)
        self.assertAlmostEqual(yj["accuracy"], 0.5)
        self.assertAlmostEqual(yj["false_pass_rate"], 1.0)
        self.assertAlmostEqual(yj["false_fail_rate"], 0.0)
        self.assertAlmostEqual(fj["accuracy"], 1.0)
        self.assertEqual(set(yj["by_candidate"]), {"spark-1.2", "spark-1.3"})
        self.assertAlmostEqual(yj["by_candidate"]["spark-1.3"]["inflation"], 0.5)

    def test_judge_mode_with_cascade(self):
        cheap = LLMJudge("cheap", "m1", FakeClient(fn=lambda m, msgs: verdict(True, 0.3)))
        strong = LLMJudge("strong", "m2", FakeClient(fn=says_correct_if_paris_or_4))
        cas = Cascade(cheap, strong, 0.8)
        path = score_run(self.d, judges=[cas], mode="judge")
        recs = list(read_jsonl(path))
        by = {(r["task_id"], r["candidate"], r["repeat"]): r for r in recs}
        r = by[("a", "spark-1.3", 0)]
        self.assertEqual(r["method"], "cascade:cheap->strong")
        self.assertFalse(r["passed"])  # strong overrode cheap
        names = [v["judge"] for v in r["judge_votes"]]
        self.assertEqual(names, ["cheap", "strong", "cascade:cheap->strong"])
        self.assertIn("det=fail", r["detail"])
        self.assertTrue(by[("c", "spark-1.2", 0)]["passed"] in (True, False))  # judged even without scorer

    def test_judge_mode_needs_judges(self):
        with self.assertRaises(ValueError):
            score_run(self.d, mode="judge")


class TestAgreementMath(unittest.TestCase):
    def test_counts(self):
        d = tempfile.mkdtemp()
        try:
            p = os.path.join(d, "scores.jsonl")
            rows = []
            # truth: old passes 2/4, new passes 2/4. Judge J favours "new": always says pass on new.
            spec = [("old", True, True), ("old", True, False), ("old", False, False), ("old", False, False),
                    ("new", True, True), ("new", True, True), ("new", False, True), ("new", False, True)]
            for i, (cand, truth, jv) in enumerate(spec):
                rows.append({"run_id": "r", "task_id": "t%d" % i, "candidate": cand, "repeat": 0,
                             "passed": truth, "score": float(truth), "method": "deterministic", "detail": "",
                             "judge_votes": [{"judge": "J", "passed": jv, "confidence": 0.9},
                                             {"judge": "K", "passed": None, "confidence": 0.0}],
                             "cost_usd": 0.0})
            rows.append({"run_id": "r", "task_id": "x", "candidate": "new", "repeat": 0, "passed": None,
                         "score": None, "method": "deterministic", "detail": "api error", "judge_votes": [],
                         "cost_usd": 0.0})
            with open(p, "w") as f:
                for r in rows:
                    f.write(json.dumps(r) + "\n")
            ag = judge_agreement(p)
            j = ag["judges"]["J"]
            self.assertEqual((j["tp"], j["fn"], j["tn"], j["fp"]), (3, 1, 2, 2))
            self.assertAlmostEqual(j["accuracy"], 5 / 8)
            self.assertAlmostEqual(j["false_pass_rate"], 2 / 4)
            self.assertAlmostEqual(j["false_fail_rate"], 1 / 4)
            self.assertAlmostEqual(j["by_candidate"]["old"]["inflation"], -0.25)
            self.assertAlmostEqual(j["by_candidate"]["new"]["inflation"], 0.5)
            self.assertAlmostEqual(j["by_candidate"]["new"]["false_pass_rate"], 1.0)
            self.assertAlmostEqual(j["preference"], 0.75)
            self.assertEqual(j["favoured"], "new")
            k = ag["judges"]["K"]
            self.assertEqual(k["unparsed"], 8)
            self.assertEqual(k["n"], 0)
            self.assertIsNone(k["accuracy"])
        finally:
            shutil.rmtree(d)


if __name__ == "__main__":
    unittest.main()
