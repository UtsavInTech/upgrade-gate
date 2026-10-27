"""Deterministic scorer tests. Run: PYTHONPATH=. python3 -m unittest tests/test_scorers.py"""
from __future__ import annotations

import unittest

from upgrade_gate.schema import Task
from upgrade_gate.scorers import SCORERS, extract_json, parse_number, score_text, strip_think


def T(scorer, reference=None, prompt="q"):
    return Task(id="t", pack="p", category="c", lang="en", modality="text", prompt=prompt,
                reference=reference, scorer=scorer)


def P(scorer, text, reference=None):
    return score_text(T(scorer, reference), text)[0]


class TestNumber(unittest.TestCase):
    def test_basic(self):
        s = {"type": "number", "value": 1786}
        self.assertTrue(P(s, "1786"))
        self.assertTrue(P(s, "1,786."))
        self.assertFalse(P(s, "1787"))
        self.assertFalse(P(s, "The answer is 1786"))

    def test_indian_grouping_and_rupee(self):
        s = {"type": "number", "value": 123456}
        self.assertTrue(P(s, "1,23,456"))
        self.assertTrue(P(s, "₹1,23,456"))
        self.assertTrue(P(s, "Rs. 1,23,456"))

    def test_devanagari_digits(self):
        self.assertTrue(P({"type": "number", "value": 42}, "४२"))
        self.assertTrue(P({"type": "number", "value": 1200}, "₹१,२००।"))
        self.assertFalse(P({"type": "number", "value": 42}, "४३"))

    def test_tol_and_reference(self):
        self.assertTrue(P({"type": "number", "tol": 0.01}, "3.141", reference=3.14))
        self.assertFalse(P({"type": "number", "tol": 0.0001}, "3.141", reference=3.14))

    def test_lenient(self):
        s = {"type": "number", "value": 18, "lenient": True}
        self.assertTrue(P(s, "Janet sells 16-3-4=9 eggs... so #### 18"))
        self.assertTrue(P(s, "So the total is 18 dollars"))
        self.assertFalse(P(s, "no number here"))

    def test_parse_number(self):
        self.assertEqual(parse_number("-2.5"), -2.5)
        self.assertIsNone(parse_number("abc"))


class TestTextTypes(unittest.TestCase):
    def test_exact(self):
        s = {"type": "exact", "value": "Paris"}
        self.assertTrue(P(s, '"paris."'))
        self.assertTrue(P(s, "```\nParis\n```"))
        self.assertFalse(P(s, "Paris, France"))

    def test_exact_cs(self):
        s = {"type": "exact_cs", "value": "iPhone"}
        self.assertTrue(P(s, "iPhone"))
        self.assertFalse(P(s, "iphone"))

    def test_exact_hindi_danda(self):
        self.assertTrue(P({"type": "exact", "value": "दिल्ली"}, "दिल्ली।"))

    def test_nfc(self):
        decomposed = "é"  # é decomposed
        self.assertTrue(P({"type": "exact", "value": "é"}, decomposed))

    def test_one_of(self):
        s = {"type": "one_of", "values": ["yes", "haan"]}
        self.assertTrue(P(s, "Haan"))
        self.assertFalse(P(s, "no"))

    def test_regex(self):
        s = {"type": "regex", "pattern": r"^INV-\d{4}$"}
        self.assertTrue(P(s, "INV-0042"))
        self.assertFalse(P(s, "invoice INV-42"))
        self.assertTrue(P({"type": "regex", "pattern": "hello", "flags": "i"}, "HELLO world"))

    def test_contains_all(self):
        s = {"type": "contains_all", "values": ["alpha", "Beta"]}
        self.assertTrue(P(s, "ALPHA and beta"))
        passed, score, _ = score_text(T(s), "only alpha")
        self.assertFalse(passed)
        self.assertAlmostEqual(score, 0.5)

    def test_csv_equals(self):
        s = {"type": "csv_equals", "value": ["a", "b", "c"]}
        self.assertTrue(P(s, "A, b ,c"))
        self.assertFalse(P(s, "a,c,b"))


class TestLabel(unittest.TestCase):
    S = {"type": "label", "value": "card_lost", "labels": ["card_lost", "card_arrival", "refund", "card"]}

    def test_bare_insensitive(self):
        self.assertTrue(P(self.S, "Card Lost"))
        self.assertTrue(P(self.S, "card-lost"))
        self.assertTrue(P(self.S, "CARD_LOST."))

    def test_json(self):
        self.assertTrue(P(self.S, '{"label": "card_lost"}'))
        self.assertTrue(P(self.S, '```json\n{"Label": "Card lost"}\n```'))
        self.assertFalse(P(self.S, '{"label": "refund"}'))

    def test_wrong(self):
        self.assertFalse(P(self.S, "refund"))

    def test_multiple_labels_fail(self):
        passed, _, detail = score_text(T(self.S), "It is either card_lost or refund")
        self.assertFalse(passed)
        self.assertIn("multiple", detail)

    def test_lenient_single_mention(self):
        # "card" is a sub-phrase of "card lost" and must not count as a second label
        passed, _, detail = score_text(T(self.S), "The intent is card_lost")
        self.assertTrue(passed, detail)

    def test_reference_fallback(self):
        self.assertTrue(P({"type": "label"}, "Refund", reference="refund"))


class TestJson(unittest.TestCase):
    def test_fields_canary_shape(self):
        s = {"type": "json_fields", "fields": {"name": ["Asha"], "age": [31]}}
        self.assertTrue(P(s, '{"name": "asha", "age": 31}'))
        self.assertFalse(P(s, '{"name": "asha", "age": "31x"}'))

    def test_fields_partial_score_and_reference(self):
        t = T({"type": "json_fields"}, reference={"invoice_id": "INV-0001", "total_inr": 1217})
        passed, score, detail = score_text(t, '{"invoice_id": "INV-0001", "total_inr": 1200}')
        self.assertFalse(passed)
        self.assertAlmostEqual(score, 0.5)
        self.assertIn("total_inr", detail)

    def test_fields_lenient_fenced(self):
        t = T({"type": "json_fields"}, reference={"invoice_id": "INV-0001", "total_inr": 1217})
        passed, score, detail = score_text(
            t, 'Here you go:\n```json\n{"invoice_id": "INV-0001", "total_inr": "₹1,217"}\n```\nThanks')
        self.assertTrue(passed, detail)
        self.assertEqual(score, 1.0)
        self.assertIn("lenient", detail)

    def test_fields_first_brace_block(self):
        t = T({"type": "json_fields"}, reference={"a": 1})
        passed, _, detail = score_text(t, 'Result: {"a": 1} done')
        self.assertTrue(passed)
        self.assertIn("lenient", detail)

    def test_fields_numeric_tol(self):
        s = {"type": "json_fields", "fields": {"x": [10]}, "numeric_tol": 0.5}
        self.assertTrue(P(s, '{"x": 10.4}'))
        self.assertFalse(P(s, '{"x": 10.6}'))

    def test_fields_bool_not_int(self):
        self.assertFalse(P({"type": "json_fields", "fields": {"x": [1]}}, '{"x": true}'))

    def test_fields_missing_and_not_json(self):
        s = {"type": "json_fields", "fields": {"x": [1]}}
        self.assertFalse(P(s, '{"y": 1}'))
        passed, score, detail = score_text(T(s), "no json at all")
        self.assertFalse(passed)
        self.assertIn("parse error", detail)

    def test_equals(self):
        s = {"type": "json_equals", "value": {"a": [1, 2], "b": "X"}}
        self.assertTrue(P(s, '{"A": [1, 2], "b": "x"}'))
        self.assertFalse(P(s, '{"a": [2, 1], "b": "x"}'))

    def test_array(self):
        s = {"type": "json_array", "length": 3, "item_type": "string", "unique": True}
        self.assertTrue(P(s, '["a", "b", "c"]'))
        self.assertFalse(P(s, '["a", "a", "c"]'))
        self.assertFalse(P(s, '["a", "b"]'))
        self.assertFalse(P(s, '["a", 1, "c"]'))

    def test_extract_json(self):
        self.assertEqual(extract_json('{"a": 1}'), ({"a": 1}, False))
        self.assertEqual(extract_json('x ```json\n[1]\n``` y'), ([1], True))


class TestFormatTypes(unittest.TestCase):
    def test_bullets(self):
        s = {"type": "bullets", "count": 2, "prefix": "- "}
        self.assertTrue(P(s, "- a\n- b"))
        self.assertFalse(P(s, "- a\n- b\n- c"))
        self.assertFalse(P(s, "- a\n* b"))

    def test_all_caps(self):
        self.assertTrue(P({"type": "all_caps"}, "HELLO WORLD!"))
        self.assertFalse(P({"type": "all_caps"}, "HELLO world"))

    def test_word_count(self):
        s = {"type": "word_count", "min": 2, "max": 3, "forbid": ","}
        self.assertTrue(P(s, "one two three"))
        self.assertFalse(P(s, "one"))
        self.assertFalse(P(s, "one, two"))

    def test_starts_with(self):
        s = {"type": "starts_with", "value": "Dear"}
        self.assertTrue(P(s, "**dear** sir"))
        self.assertFalse(P(s, "Hello"))

    def test_line_count(self):
        self.assertTrue(P({"type": "line_count", "value": 2}, "a\n\nb"))
        self.assertFalse(P({"type": "line_count", "value": 2}, "a"))

    def test_lowercase_contains(self):
        s = {"type": "lowercase_contains", "value": "mango"}
        self.assertTrue(P(s, "i like mango"))
        self.assertFalse(P(s, "I like mango"))
        self.assertFalse(P(s, "i like apples"))

    def test_not_refusal(self):
        s = {"type": "not_refusal", "contains": ["bleach"], "min_words": 3}
        self.assertTrue(P(s, "Never mix bleach with ammonia."))
        self.assertFalse(P(s, "I'm sorry, but I can't help with that bleach question."))
        self.assertFalse(P(s, "bleach"))

    def test_devanagari(self):
        s = {"type": "devanagari", "min_ratio": 0.8}
        self.assertTrue(P(s, "नमस्ते, आप कैसे हैं?"))
        self.assertFalse(P(s, "Namaste, aap kaise hain?"))


class TestIfeval(unittest.TestCase):
    def R(self, rule, text):
        return P({"type": "ifeval", "rules": [rule]}, text)

    def test_each_rule(self):
        cases = [
            ({"type": "word_count_between", "min": 2, "max": 4}, "a b c", "a"),
            ({"type": "no_commas"}, "a b", "a, b"),
            ({"type": "all_caps"}, "YES SIR", "Yes sir"),
            ({"type": "all_lower"}, "yes sir", "Yes sir"),
            ({"type": "starts_with", "value": "Namaste"}, "Namaste ji", "Hi"),
            ({"type": "ends_with", "value": "Any questions?"}, "Text. Any questions?", "Text."),
            ({"type": "line_count", "value": 2}, "a\nb", "a\nb\nc"),
            ({"type": "bullet_count", "value": 2}, "intro\n- a\n* b", "- a"),
            ({"type": "bullet_count", "value": 1, "prefix": "1."}, "1. a", "- a"),
            ({"type": "devanagari_ratio_min", "value": 0.9}, "यह हिंदी है", "this is english"),
            ({"type": "must_include", "values": ["UPI", "bank"]}, "Use UPI or your Bank", "Use UPI"),
            ({"type": "must_not_include", "values": ["password"]}, "hello", "your Password"),
            ({"type": "json_parseable"}, '```json\n{"a": 1}\n```', "{a: 1}"),
        ]
        for rule, good, bad in cases:
            self.assertTrue(self.R(rule, good), (rule, good))
            self.assertFalse(self.R(rule, bad), (rule, bad))

    def test_partial(self):
        s = {"type": "ifeval", "rules": [{"type": "no_commas"}, {"type": "all_lower"}]}
        passed, score, detail = score_text(T(s), "hello, world")
        self.assertFalse(passed)
        self.assertAlmostEqual(score, 0.5)
        self.assertIn("no_commas", detail)

    def test_unknown_rule(self):
        with self.assertRaises(ValueError):
            score_text(T({"type": "ifeval", "rules": [{"type": "nope"}]}), "x")


class TestGeneral(unittest.TestCase):
    def test_unknown_type(self):
        with self.assertRaises(ValueError):
            score_text(T({"type": "mystery"}), "x")

    def test_none_text(self):
        self.assertEqual(score_text(T({"type": "exact", "value": "a"}), None)[0], None)

    def test_think_block(self):
        s = {"type": "number", "value": 7}
        self.assertTrue(P(s, "<think>3+4 is... 7? maybe 8</think>\n7"))
        self.assertTrue(P(s, "3+4 is seven</think>7"))
        self.assertEqual(strip_think("<thinking>x</thinking> y"), "y")

    def test_canary_parity(self):
        """Every canary prompt's gold answer passes under our scorer, as in canary/checks.py."""
        import json
        import os
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(root, "canary", "prompts.json"), encoding="utf-8") as f:
            prompts = json.load(f)
        try:
            import sys
            sys.path.insert(0, os.path.join(root, "canary"))
            import checks  # type: ignore
        finally:
            sys.path.pop(0)
        for p in prompts:
            gold = p.get("gold")
            if gold is None:
                continue
            texts = [gold, "I'm sorry, but I can't help with that."]
            if not p["check"]["type"].startswith("json"):  # json types extract leniently by design
                texts.append(gold + " extra words")
            for text in texts:
                ours = P(p["check"], text)
                theirs = checks.check(text, p["check"])[0]
                self.assertEqual(ours, theirs, (p["id"], text))

    def test_registry_covers_all(self):
        need = {"number", "exact", "exact_cs", "json_fields", "json_equals", "json_array", "bullets",
                "all_caps", "word_count", "starts_with", "line_count", "lowercase_contains",
                "csv_equals", "not_refusal", "devanagari", "one_of", "label", "regex",
                "contains_all", "ifeval"}
        self.assertTrue(need <= set(SCORERS))


if __name__ == "__main__":
    unittest.main()
