"""Experiment analysis code finds effects planted in a synthetic run. Stdlib only."""
from __future__ import annotations

import json
import os
import random
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "experiments"))
sys.path.insert(0, ROOT)

import common  # noqa: E402
import e1_upgrade  # noqa: E402
import e2_judge_version  # noqa: E402
import e5_hindi  # noqa: E402

A, B = "spark-1.2@low", "spark-1.3@low"


def make_run(d, n=200, seed=1):
    rng = random.Random(seed)
    tasks, scores = [], []
    for i in range(n):
        en = {"id": "t%d-en" % i, "category": "math", "lang": "en", "modality": "text", "pair_id": None}
        hi = {"id": "t%d-hi" % i, "category": "math", "lang": "hi", "modality": "text", "pair_id": en["id"]}
        tasks += [en, hi]
        # English: B improves +10 pts. Hindi: B regresses −10 pts.
        for t, (pa, pb) in ((en, (0.70, 0.80)), (hi, (0.70, 0.60))):
            base = rng.random()
            for cand, p in ((A, pa), (B, pb)):
                ok = base < p
                for rep in range(3):
                    # B's answers fool the 1.3 judge more often (planted judge-version bias)
                    jv = ok or (cand == B and rng.random() < 0.4)
                    scores.append({"run_id": "x", "task_id": t["id"], "candidate": cand, "repeat": rep,
                                   "passed": ok, "score": float(ok), "method": "deterministic",
                                   "judge_votes": [{"judge": "spark-1.3", "passed": jv},
                                                   {"judge": "wonder", "passed": ok}]})
    with open(os.path.join(d, "tasks.jsonl"), "w") as f:
        f.writelines(json.dumps(t) + "\n" for t in tasks)
    with open(os.path.join(d, "scores.jsonl"), "w") as f:
        f.writelines(json.dumps(s) + "\n" for s in scores)


class Experiments(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = self.tmp.name
        make_run(self.d)
        common.OUT = os.path.join(self.d, "out")

    def tearDown(self):
        self.tmp.cleanup()

    def load(self, name):
        with open(os.path.join(common.OUT, name + ".json")) as f:
            return json.load(f)

    def test_mcnemar(self):
        self.assertEqual(common.mcnemar_exact(0, 0), 1.0)
        self.assertAlmostEqual(common.mcnemar_exact(0, 10), 2 / 1024)

    def test_e1_finds_hindi_regression(self):
        e1_upgrade.analyse(self.d)
        rows = {r["slice"]: r for r in self.load("e1_upgrade")["rows"]}
        self.assertGreater(rows["lang=en"]["delta"], 0.05)
        self.assertLess(rows["lang=hi"]["delta"], -0.05)
        self.assertLess(rows["lang=hi"]["p"], 0.05)

    def test_e5_interaction(self):
        e5_hindi.analyse(self.d)
        inter = self.load("e5_hindi")["interaction"]["hi"]
        self.assertLess(inter["estimate"], -0.1)
        self.assertLess(inter["ci"][1], 0)

    def test_e2_detects_judge_bias(self):
        e2_judge_version.analyse(self.d)
        data = self.load("e2_judge_version")
        fp_b = data["confusion"]["spark-1.3|%s" % B].get("FP", 0)
        fp_a = data["confusion"]["spark-1.3|%s" % A].get("FP", 0)
        self.assertGreater(fp_b, fp_a)
        self.assertEqual(data["confusion"]["wonder|%s" % B].get("FP", 0), 0)
        gate = {r["slice"]: r for r in data["gate_by_judge"]}
        self.assertGreater(gate["judge=spark-1.3"]["delta"], gate["ground truth"]["delta"])


if __name__ == "__main__":
    unittest.main()


class TokenLimitSpec(unittest.TestCase):
    def test_limit_suffix(self):
        from upgrade_gate.cli import parse_candidate
        c = parse_candidate("spark-1.3-c@xhigh/16000")
        self.assertEqual(c.model_id, "muse-spark-1.3-contributor")
        self.assertEqual(c.params, {"max_completion_tokens": 16000, "reasoning_effort": "xhigh"})
        self.assertEqual(parse_candidate("spark-1.3@low").params["max_completion_tokens"], 4000)
        with self.assertRaises(SystemExit):
            parse_candidate("spark-1.3@low/abc")
