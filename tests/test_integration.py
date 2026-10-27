"""Integration: packs <-> scorers agree, and the full pipeline runs end-to-end on a mock API.

Stdlib only. Run: PYTHONPATH=. python3 -m unittest tests.test_integration
"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest

from upgrade_gate.packs import PACKS, load_pack
from upgrade_gate.schema import Task, read_jsonl
from upgrade_gate.scorers import score_text


def perfect_answer(t: Task):
    """Build an answer that must pass, from the task's own spec. None = can't synthesise."""
    s = t.scorer
    kind = s["type"]
    if t.pack == "canary":
        return t.meta.get("gold")
    if kind == "number":
        v = s.get("value", t.reference)
        return str(int(v)) if float(v).is_integer() else str(v)
    if kind == "one_of":
        return s["values"][0]
    if kind == "json_fields":
        fields = s.get("fields") or {k: [v] for k, v in t.reference.items()}
        return json.dumps({k: v[0] for k, v in fields.items()}, ensure_ascii=False)
    if kind == "label":
        return s["value"]
    return None


def wrong_answer(t: Task):
    kind = t.scorer["type"]
    if kind == "number":
        return "999999"
    if kind == "one_of":
        return "definitely-not-an-answer"
    if kind == "json_fields":
        return json.dumps({k: "WRONG" for k in (t.scorer.get("fields") or t.reference)})
    if kind == "label":
        other = [l for l in t.scorer["labels"] if l != t.scorer["value"]]
        return other[0]
    return None


class PacksMatchScorers(unittest.TestCase):
    def test_every_task_perfect_passes_and_wrong_fails(self):
        problems = []
        checked = 0
        for name in PACKS:
            for t in load_pack(name):
                good = perfect_answer(t)
                if good is not None:
                    checked += 1
                    ok, _, why = score_text(t, good)
                    if ok is not True:
                        problems.append("%s good failed: %s | %r" % (t.id, why, good[:80]))
                bad = wrong_answer(t)
                if bad is not None:
                    ok, _, why = score_text(t, bad)
                    if ok is not False:
                        problems.append("%s wrong passed: %r" % (t.id, bad[:80]))
        self.assertGreater(checked, 1000)
        self.assertEqual(problems, [], "\n".join(problems[:30]))

    def test_numeric_strings_accepted_for_numeric_fields(self):
        t = next(x for x in load_pack("docs-synth") if x.scorer["type"] == "json_fields")
        fields = {k: v[0] for k, v in t.scorer["fields"].items()}
        for k, v in list(fields.items()):
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                fields[k] = "{:,.2f}".format(v)
        ok, _, why = score_text(t, json.dumps(fields, ensure_ascii=False))
        self.assertTrue(ok, why)


class IfevalEdgeRules(unittest.TestCase):
    def task(self, rules):
        return Task(id="x", pack="ifeval", category="instruction", lang="en", modality="text",
                    prompt="p", reference=None, scorer={"type": "ifeval", "rules": rules})

    def check(self, rules, text):
        return score_text(self.task(rules), text)[0]

    def test_bullets_star_and_dot(self):
        r = [{"type": "bullet_count", "value": 2, "prefix": "-"}]
        self.assertTrue(self.check(r, "- a\n- b"))
        self.assertTrue(self.check(r, "* a\n• b"))

    def test_json_parseable_keys_exact(self):
        r = [{"type": "json_parseable", "keys": ["a", "b"]}]
        self.assertTrue(self.check(r, '{"a": 1, "b": 2}'))
        self.assertFalse(self.check(r, '{"a": 1}'))

    def test_must_not_include_whole_word_devanagari(self):
        r = [{"type": "must_not_include", "values": ["दिल्ली"]}]
        self.assertFalse(self.check(r, "मैं दिल्ली में रहता हूँ"))
        self.assertTrue(self.check(r, "मैं मुंबई में रहता हूँ"))

    def test_ends_with_strips_danda(self):
        r = [{"type": "ends_with", "value": "धन्यवाद"}]
        self.assertTrue(self.check(r, "आपका धन्यवाद।"))


class EndToEnd(unittest.TestCase):
    """run -> score -> gate -> report -> export through the CLI, against the mock API."""

    def test_pipeline_on_mock(self):
        from tests.mock_server import mock_server as MockServer
        from upgrade_gate import cli

        from upgrade_gate.client import build_messages

        def key(content):
            # invoice tasks share one prompt; the attachment is what tells them apart
            return json.dumps(content, sort_keys=True, ensure_ascii=False)

        tasks = {}
        for name in ("math-pairs", "intent", "docs-synth"):
            for t in load_pack(name, n=24, seed=3):
                tasks[key(build_messages(t)[-1]["content"])] = t

        def answer(req):
            t = tasks.get(key(req["messages"][-1]["content"]))
            good = perfect_answer(t) if t else "?"
            # plant a regression: 1.3 fails every doc-image task
            if "1.3" in req["model"] and t is not None and t.category == "doc-image":
                return wrong_answer(t) or "?"
            return good or "?"

        tmp = tempfile.mkdtemp()
        try:
            with MockServer(answer=answer) as srv:
                os.environ["MODEL_API_BASE"] = srv.base_url
                os.environ["MODEL_API_KEY"] = "test"
                os.environ["UPGRADE_GATE_CACHE_DIR"] = os.path.join(tmp, "cache")
                code = cli.main(["all", "--packs", "math-pairs,intent,docs-synth", "--n", "24", "--seed", "3",
                                 "-b", "spark-1.2@low", "-c", "spark-1.3@low", "--repeats", "2",
                                 "--out", tmp, "--run-id", "e2e", "--yes", "--workers", "8"])
            run_dir = os.path.join(tmp, "e2e")
            for f in ("run.json", "tasks.jsonl", "responses.jsonl", "scores.jsonl", "gate.json",
                      "report.md", "report.html"):
                self.assertTrue(os.path.exists(os.path.join(run_dir, f)), f)
            with open(os.path.join(run_dir, "gate.json")) as f:
                gate = json.load(f)
            self.assertEqual(gate["decision"], "no-go", gate.get("reasons"))
            self.assertEqual(code, 2)
            self.assertTrue(any("doc" in r for r in gate["reasons"]), gate["reasons"])
            self.assertTrue(os.listdir(os.path.join(run_dir, "exports")))
            errs = [r for r in read_jsonl(os.path.join(run_dir, "responses.jsonl")) if r.get("error")]
            self.assertEqual(errs, [])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
            os.environ.pop("MODEL_API_BASE", None)
            os.environ.pop("MODEL_API_KEY", None)
            os.environ.pop("UPGRADE_GATE_CACHE_DIR", None)


if __name__ == "__main__":
    unittest.main()
