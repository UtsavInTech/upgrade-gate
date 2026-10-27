"""Silent-failure check (upgrade_gate/behaviour.py). Stdlib only, no API calls."""
from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest

from upgrade_gate.behaviour import answer_type, apply_to_gate, check


class AnswerType(unittest.TestCase):
    def test_types(self):
        self.assertEqual(answer_type("42", None, True), "correct")
        self.assertEqual(answer_type(None, "HTTP 500", None), "no answer")
        self.assertEqual(answer_type("I don't have the ability to listen to audio attachments.", None, False), "abstain")
        self.assertEqual(answer_type("I'm sorry, but I can't help with that.", None, False), "abstain")
        self.assertEqual(answer_type('{"order_number": "", "pincode": "", "city": ""}', None, False), "blank")
        self.assertEqual(answer_type("   ", None, False), "blank")
        self.assertEqual(answer_type('{"order_number": "4991"}', None, False), "wrong")

    def test_says_cant_hear_but_answers_correctly_counts_as_correct(self):
        self.assertEqual(answer_type("I can't hear audio, but from your text: 374", None, True), "correct")


def _write_run(d, rows):
    """rows: list of (task_id, candidate, repeat, text, passed)."""
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "responses.jsonl"), "w") as f, open(os.path.join(d, "scores.jsonl"), "w") as g:
        for tid, cand, rep, text, passed in rows:
            f.write(json.dumps({"task_id": tid, "candidate": cand, "repeat": rep, "text": text, "error": None}) + "\n")
            g.write(json.dumps({"task_id": tid, "candidate": cand, "repeat": rep, "passed": passed}) + "\n")


class Check(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_flags_switch_from_abstain_to_silent_wrong(self):
        rows = []
        for i in range(60):
            for r in range(3):
                if i < 20:  # old says it can't hear, new answers wrong without saying so
                    rows.append(("t%d" % i, "old", r, "I can't hear the audio.", False))
                    rows.append(("t%d" % i, "new", r, '{"order_number": "1"}', False))
                else:
                    rows.append(("t%d" % i, "old", r, "ok", True))
                    rows.append(("t%d" % i, "new", r, "ok", True))
        _write_run(self.tmp, rows)
        res = check(self.tmp, "old", "new")
        self.assertEqual((res["silent"]["baseline"], res["silent"]["candidate"]), (0, 20))
        self.assertEqual((res["abstain"]["baseline"], res["abstain"]["candidate"]), (20, 0))
        self.assertTrue(res["flagged"])
        # accuracy is identical, so only the failure-type check can block this
        with open(os.path.join(self.tmp, "gate.json"), "w") as f:
            json.dump({"baseline": "old", "candidate": "new", "decision": "go", "reasons": ["fine"]}, f)
        gate = apply_to_gate(self.tmp)
        self.assertEqual(gate["decision"], "no-go")
        self.assertEqual(gate["accuracy_decision"], "go")
        self.assertTrue(gate["reasons"][0].startswith("Silent failures rose"))

    def test_no_flag_when_types_unchanged(self):
        rows = [("t%d" % i, c, r, "x", i % 5 != 0) for i in range(50) for c in ("old", "new") for r in range(3)]
        _write_run(self.tmp, rows)
        self.assertFalse(check(self.tmp, "old", "new")["flagged"])


if __name__ == "__main__":
    unittest.main()


class PerInputType(unittest.TestCase):
    def test_text_twins_do_not_dilute_audio(self):
        tmp = tempfile.mkdtemp()
        try:
            rows, tasks = [], []
            for i in range(40):
                for mod in ("audio", "text"):
                    tid = "%s-%d" % (mod, i)
                    tasks.append({"id": tid, "modality": mod})
                    for r in range(3):
                        bad = mod == "audio" and i < 15
                        rows.append((tid, "old", r, "ok" if not bad else "I can't hear the audio.", not bad))
                        rows.append((tid, "new", r, "ok" if not bad else '{"order_number": "12"}', not bad))
            _write_run(tmp, rows)
            with open(os.path.join(tmp, "tasks.jsonl"), "w") as f:
                for t in tasks:
                    f.write(json.dumps(t) + "\n")
            res = check(tmp, "old", "new")
            self.assertEqual(res["population"], "audio input")
            self.assertEqual(res["tasks"], 40)  # audio clips only, not 80
            self.assertTrue(res["by_input"]["audio"]["flagged"])
            self.assertFalse(res["by_input"]["text"]["flagged"])
            self.assertIn("Audio input", res["reason"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class PolicyAndItems(unittest.TestCase):
    def _run(self, tmp, n_items, worse_items, langs=("en", "hi", "hinglish")):
        rows, tasks = [], []
        for i in range(n_items):
            for lang in langs:
                tid = "item%d-%s" % (i, lang)
                tasks.append({"id": tid, "modality": "audio", "meta": {"item": "item%d" % i}})
                bad = i < worse_items
                for r in range(3):
                    rows.append((tid, "old", r, "ok", True))
                    rows.append((tid, "new", r, '{"pincode": "380015"}' if bad else "ok", not bad))
        _write_run(tmp, rows)
        with open(os.path.join(tmp, "tasks.jsonl"), "w") as f:
            for t in tasks:
                f.write(json.dumps(t) + "\n")

    def test_item_level_needs_enough_independent_items(self):
        tmp = tempfile.mkdtemp()
        try:
            self._run(tmp, n_items=15, worse_items=3)  # 9 tasks worse, but only 3 independent items
            per_task = check(tmp, "old", "new", unit="task")
            per_item = check(tmp, "old", "new", unit="item")
            self.assertTrue(per_task["flagged"])
            self.assertFalse(per_item["flagged"])
            self.assertIn("Not robust", per_item["note"])
            self._run(tmp, n_items=15, worse_items=8)  # 8 of 15 items worse
            self.assertTrue(check(tmp, "old", "new", unit="item")["flagged"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_policy_loads_and_validates(self):
        from upgrade_gate.behaviour import load_policy
        self.assertEqual(load_policy(None)["silent_failures"]["unit"], "item")
        tmp = tempfile.mkdtemp()
        try:
            p = os.path.join(tmp, "policy.json")
            with open(p, "w") as f:
                json.dump({"silent_failures": {"count": ["wrong"]}, "why": "blanks are caught by our schema"}, f)
            pol = load_policy(p)
            self.assertEqual(pol["silent_failures"]["count"], ["wrong"])
            self.assertEqual(pol["silent_failures"]["max_rise"], 0.02)  # default kept
            with open(p, "w") as f:
                json.dump({"silent_failures": {"count": ["confident"]}}, f)
            with self.assertRaises(ValueError):
                load_policy(p)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_blank_only_rise_is_ignored_when_policy_counts_wrong_only(self):
        tmp = tempfile.mkdtemp()
        try:
            rows = []
            for i in range(30):
                for r in range(3):
                    rows.append(("t%d" % i, "old", r, "ok", True))
                    rows.append(("t%d" % i, "new", r, '{"pincode": ""}' if i < 12 else "ok", i >= 12))
            _write_run(tmp, rows)
            self.assertTrue(check(tmp, "old", "new", count=("wrong", "blank"))["flagged"])
            self.assertFalse(check(tmp, "old", "new", count=("wrong",))["flagged"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
