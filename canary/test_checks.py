"""Self-test: every gold answer must pass its check, and obvious wrong answers must fail.

Run: python3 -m unittest canary/test_checks.py
"""
import json
import os
import unittest

from checks import check

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "prompts.json"), encoding="utf-8") as f:
    PROMPTS = json.load(f)

WRONG = "I'm sorry, but I can't help with that."


class SuiteShape(unittest.TestCase):
    def test_fifty_prompts_unique_ids(self):
        ids = [p["id"] for p in PROMPTS]
        self.assertEqual(len(ids), 50)
        self.assertEqual(len(set(ids)), 50)

    def test_ten_hindi_or_hinglish(self):
        self.assertEqual(sum(p["lang"] in ("hi", "hinglish") for p in PROMPTS), 10)

    def test_pairs_point_to_real_prompts(self):
        ids = {p["id"] for p in PROMPTS}
        for p in PROMPTS:
            if "pair" in p:
                self.assertIn(p["pair"], ids, p["id"])


class GoldAndWrong(unittest.TestCase):
    def test_gold_passes(self):
        for p in PROMPTS:
            ok, why = check(p["gold"], p["check"])
            self.assertTrue(ok, "%s gold failed: %s" % (p["id"], why))

    def test_refusal_fails(self):
        for p in PROMPTS:
            ok, _ = check(WRONG, p["check"])
            self.assertFalse(ok, "%s accepted a refusal" % p["id"])


class Normalisation(unittest.TestCase):
    def test_fenced_json(self):
        ok, _ = check('```json\n{"category": "Billing"}\n```', {"type": "json_fields", "fields": {"category": ["billing"]}})
        self.assertTrue(ok)

    def test_number_with_trailing_dot_and_comma(self):
        self.assertTrue(check("1,786.", {"type": "number", "value": 1786})[0])

    def test_number_with_words_fails(self):
        self.assertFalse(check("The answer is 1786", {"type": "number", "value": 1786})[0])

    def test_bool_is_not_number(self):
        self.assertFalse(check('{"x": 1}', {"type": "json_fields", "fields": {"x": [True]}})[0])

    def test_none_response(self):
        self.assertFalse(check(None, {"type": "exact", "value": "a"})[0])

    def test_wrong_answers(self):
        cases = [
            ("1787", {"type": "number", "value": 1786}),
            ("Thursday", {"type": "exact", "value": "Friday"}),
            ("q7#k-92_zx", {"type": "exact_cs", "value": "Q7#k-92_zX"}),
            ("A cat, a dog", {"type": "word_count", "min": 1, "max": 30, "forbid": ","}),
            ("Paris", {"type": "lowercase_contains", "value": "paris"}),
            ("Delhi is the capital", {"type": "devanagari", "min_ratio": 0.95}),
            ('["red", "red", "blue", "green"]', {"type": "json_array", "length": 4, "unique": True, "item_type": "string"}),
        ]
        for text, spec in cases:
            self.assertFalse(check(text, spec)[0], text)


if __name__ == "__main__":
    unittest.main()
