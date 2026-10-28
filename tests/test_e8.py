"""E8 (spoken self-corrections): pack contents and the analysis on a planted run. Stdlib only."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "experiments"))
sys.path.insert(0, ROOT)

import e8_corrections as e8  # noqa: E402
from upgrade_gate.packs import audio_corrections  # noqa: E402

HAVE_CLIPS = os.path.exists(audio_corrections.MANIFEST)


class SavedField(unittest.TestCase):
    def test_reads_digits_from_json(self):
        self.assertEqual(e8.saved_field('```json\n{"order_number": "8 0 0 3 5", "pincode": 126072}\n```',
                                        "order_number"), "80035")
        self.assertEqual(e8.saved_field('{"Pincode": 126072}', "pincode"), "126072")

    def test_no_json(self):
        self.assertIsNone(e8.saved_field("I can't hear the audio.", "order_number"))
        self.assertIsNone(e8.saved_field('{"city": "Pune"}', "order_number"))


@unittest.skipUnless(HAVE_CLIPS, "run scripts/build_corrections.py first")
class Pack(unittest.TestCase):
    def test_synthetic_clips(self):
        with mock.patch.object(audio_corrections, "REAL", "/nonexistent"):
            tasks = audio_corrections.build()
        self.assertEqual(len(tasks), 90)
        self.assertEqual(len({t.id for t in tasks}), 90)
        for t in tasks:
            final = t.reference[t.meta["field"]]
            self.assertNotEqual(t.meta["first"], final)  # the taken-back number is never the answer
            self.assertTrue(t.attachments[0].endswith(".wav"))
            if t.meta["variant"] == "corr":
                self.assertIn(" ".join(t.meta["first"]), t.meta["transcript"])
            else:
                self.assertNotIn(" ".join(t.meta["first"]), t.meta["transcript"])


def _run(d, wrong_b_corr):
    """Planted run: 15 items × 3 langs × corr/ctrl. B keeps the first number on `wrong_b_corr` items."""
    tasks, scores, resps = [], [], []
    for i in range(15):
        for lang in ("en", "hi", "hinglish"):
            for variant in ("corr", "ctrl"):
                tid = "c-%02d-%s-%s" % (i, lang, variant)
                tasks.append({"id": tid, "lang": lang, "modality": "audio", "meta": {
                    "item": "corr-%02d" % i, "variant": variant, "field": "order_number", "first": "11111",
                    "speaker": "synthetic"}})
                for cand in (e8.A, e8.B):
                    bad = cand == e8.B and variant == "corr" and i < wrong_b_corr
                    num = "11111" if bad else "22222"
                    for rep in range(3):
                        scores.append({"task_id": tid, "candidate": cand, "repeat": rep, "passed": not bad})
                        resps.append({"task_id": tid, "candidate": cand, "repeat": rep,
                                      "text": json.dumps({"order_number": num})})
    for name, rows in (("tasks", tasks), ("scores", scores), ("responses", resps)):
        with open(os.path.join(d, name + ".jsonl"), "w") as f:
            f.writelines(json.dumps(r) + "\n" for r in rows)


class Analysis(unittest.TestCase):
    def _analyse(self, wrong):
        with tempfile.TemporaryDirectory() as d:
            _run(d, wrong)
            out = {}
            with mock.patch.object(e8, "write_result", lambda name, text, data: out.update(data)):
                e8.analyse(d)
            return out

    def test_finds_planted_effect(self):
        out = self._analyse(wrong=8)
        self.assertTrue(out["confirmed"])
        self.assertEqual((out["primary"]["worse"], out["primary"]["better"]), (8, 0))
        self.assertEqual(out["control"]["worse"], 0)
        kf = out["kept_first"][0]
        self.assertEqual((kf[e8.A], kf[e8.B]), (0, 24))

    def test_no_effect(self):
        out = self._analyse(wrong=0)
        self.assertFalse(out["confirmed"])
        self.assertEqual(out["primary"]["p"], 1.0)


if __name__ == "__main__":
    unittest.main()
