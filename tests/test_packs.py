"""Pack tests (stdlib unittest; also runs under pytest).

    PYTHONPATH=. python3 -m unittest tests.test_packs -v
"""
from __future__ import annotations

import json
import os
import re
import unittest
from collections import Counter

from upgrade_gate.packs import PACKS, load_pack
from upgrade_gate.packs._common import DAYS_EN, DAYS_HI
from upgrade_gate.schema import Task

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_OK = os.path.exists(os.path.join(ROOT, "data", "docs-synth", "manifest.jsonl"))

SPEC_TYPES = {"number", "exact", "exact_cs", "one_of", "label", "json_fields", "json_equals", "regex",
              "contains_all", "ifeval", "json_array", "bullets", "all_caps", "word_count", "starts_with",
              "line_count", "lowercase_contains", "csv_equals", "not_refusal", "devanagari"}
IFEVAL_RULES = {"word_count_between", "no_commas", "all_caps", "all_lower", "starts_with", "ends_with",
                "line_count", "bullet_count", "devanagari_ratio_min", "must_include", "must_not_include",
                "json_parseable"}


def _num(s: str) -> float:
    return float(s.replace(",", ""))


class TestPacks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packs = {n: load_pack(n) for n in PACKS if n != "docs-synth" or DOCS_OK}

    def test_all_load_and_fields(self):
        for name, tasks in self.packs.items():
            self.assertTrue(tasks, name)
            for t in tasks:
                self.assertIsInstance(t, Task)
                self.assertEqual(t.pack, name)
                self.assertIn(t.lang, ("en", "hi", "hinglish"))
                self.assertIn(t.modality, ("text", "image", "pdf"))
                self.assertTrue(t.prompt.strip())
                self.assertIn(t.scorer["type"], SPEC_TYPES, t.id)
                json.dumps(t.reference, ensure_ascii=False)  # JSON-serialisable
                json.dumps(t.scorer, ensure_ascii=False)
                if t.scorer["type"] == "ifeval":
                    for rule in t.scorer["rules"]:
                        self.assertIn(rule["type"], IFEVAL_RULES)

    def test_ids_unique_across_packs(self):
        ids = [t.id for ts in self.packs.values() for t in ts]
        dup = [i for i, c in Counter(ids).items() if c > 1]
        self.assertEqual(dup, [])

    def test_pair_ids_resolve(self):
        for name, tasks in self.packs.items():
            by_id = {t.id: t for t in tasks}
            for t in tasks:
                if t.pair_id:
                    self.assertIn(t.pair_id, by_id, t.id)
                    other = by_id[t.pair_id]
                    self.assertNotEqual(other.lang, t.lang, t.id)
                    self.assertEqual(other.modality, t.modality, t.id)
                    self.assertEqual(other.category, t.category, t.id)

    def test_attachments_exist(self):
        for tasks in self.packs.values():
            for t in tasks:
                for a in t.attachments:
                    self.assertFalse(os.path.isabs(a), a)
                    self.assertTrue(os.path.exists(os.path.join(ROOT, a)), a)
                if t.modality != "text":
                    self.assertEqual(len(t.attachments), 1)

    def test_counts(self):
        def c(name):
            return Counter((t.lang, t.modality) for t in self.packs[name])
        m = c("math-pairs")
        self.assertEqual((m[("en", "text")], m[("hi", "text")], m[("hinglish", "text")]), (120, 120, 120))
        e = c("extract-pairs")
        self.assertEqual((e[("en", "text")], e[("hi", "text")], e[("hinglish", "text")]), (80, 80, 80))
        i = c("intent")
        self.assertGreaterEqual(i[("en", "text")], 240)
        self.assertGreaterEqual(i[("hinglish", "text")], 110)
        self.assertGreaterEqual(len({t.reference for t in self.packs["intent"]}), 15)
        f = c("ifeval")
        self.assertEqual((f[("en", "text")], f[("hi", "text")]), (100, 50))
        self.assertEqual(len(self.packs["canary"]), 50)
        if DOCS_OK:
            d = c("docs-synth")
            self.assertEqual((d[("en", "image")], d[("en", "pdf")]), (60, 60))
            self.assertEqual((d[("hi", "image")], d[("hi", "pdf")]), (40, 40))
            variants = Counter(t.meta["variant"] for t in self.packs["docs-synth"] if t.modality == "image")
            self.assertGreater(variants["rotated_noisy"], 10)

    def test_n_and_seed(self):
        for name in self.packs:
            full = self.packs[name]
            a = load_pack(name, n=25, seed=1)
            b = load_pack(name, n=25, seed=1)
            c = load_pack(name, n=25, seed=2)
            self.assertEqual(len(a), 25)
            self.assertEqual([t.id for t in a], [t.id for t in b])
            self.assertNotEqual([t.id for t in a], [t.id for t in c], name)
            ids = {t.id for t in a}
            for t in a:  # sampling never leaves a dangling pair
                if t.pair_id:
                    self.assertIn(t.pair_id, ids, (name, t.id))
            self.assertEqual(len(load_pack(name, n=10 ** 6)), len(full))
            self.assertEqual(load_pack(name, n=0), [])

    def test_stable_content(self):
        # content is fixed: repeated generation gives identical tasks
        for name in ("math-pairs", "extract-pairs", "intent", "ifeval"):
            x = [(t.id, t.prompt, json.dumps(t.reference, ensure_ascii=False)) for t in PACKS[name]()]
            y = [(t.id, t.prompt, json.dumps(t.reference, ensure_ascii=False)) for t in PACKS[name]()]
            self.assertEqual(x, y)

    def test_load_pack_returns_copies(self):
        a = load_pack("math-pairs", n=3)
        a[0].meta["x"] = 1
        self.assertNotIn("x", load_pack("math-pairs", n=3)[0].meta)

    def test_unknown_pack(self):
        with self.assertRaises(KeyError):
            load_pack("nope")


class TestAnswers(unittest.TestCase):
    """Recompute answers from the English prompt text with independent parsing."""

    def setUp(self):
        self.math = [t for t in load_pack("math-pairs") if t.lang == "en"]

    def _sub(self, s):
        return [t for t in self.math if t.meta["subtype"] == s]

    def test_number_scorer_matches_reference(self):
        for t in load_pack("math-pairs"):
            if t.scorer["type"] == "number":
                self.assertEqual(t.scorer["value"], t.reference)

    def test_shopping(self):
        for t in self._sub("shopping"):
            pairs = re.findall(r"(\d+) [^₹]*?₹(\d+) (?:each|per)", t.prompt)
            self.assertTrue(pairs, t.prompt)
            total = sum(int(q) * int(p) for q, p in pairs)
            note = re.search(r"₹(\d+) note", t.prompt)
            disc = re.search(r"(\d+)% discount", t.prompt)
            if note:
                want = int(note.group(1)) - total
            elif disc:
                want = total * (100 - int(disc.group(1))) / 100.0
            else:
                want = total
            self.assertAlmostEqual(t.reference, want, places=6, msg=t.prompt)
            self.assertGreaterEqual(t.reference, 0)

    def test_percent(self):
        for t in self._sub("percentage"):
            p = t.prompt
            m = re.match(r"What is (\d+)% of (\d+)\?", p)
            if m:
                want = int(m.group(1)) * int(m.group(2)) / 100.0
            elif "goes up" in p:
                price, pct = map(int, re.search(r"₹(\d+)\. Its price goes up by (\d+)%", p).groups())
                want = price * (1 + pct / 100.0)
            elif "% off" in p:
                price, pct = map(int, re.search(r"₹(\d+)\. It is on sale at (\d+)% off", p).groups())
                want = price * (1 - pct / 100.0)
            else:
                a, b = map(int, re.search(r"scored (\d+) marks out of (\d+)", p).groups())
                want = a * 100.0 / b
            self.assertAlmostEqual(t.reference, want, places=6, msg=p)

    def test_time(self):
        for t in self._sub("time"):
            p = t.prompt
            times = re.findall(r"(\d\d):(\d\d)", p)
            mins = [int(h) * 60 + int(m) for h, m in times]
            if "leaves at" in p:
                h = re.search(r"(\d+) hours?", p)
                m = re.search(r"(\d+) minutes", p)
                dur = (int(h.group(1)) * 60 if h else 0) + int(m.group(1))
                end = mins[0] + dur
                self.assertEqual(t.reference, "%02d:%02d" % (end // 60, end % 60), p)
                self.assertIn(t.reference, t.scorer["values"])
            else:
                self.assertEqual(t.reference, mins[1] - mins[0], p)

    def test_units(self):
        factors = {("kilometres", "metres"): 1000, ("kilograms", "grams"): 1000, ("litres", "millilitres"): 1000,
                   ("hours", "minutes"): 60, ("metres", "centimetres"): 100, ("minutes", "seconds"): 60,
                   ("days", "hours"): 24, ("tonnes", "kilograms"): 1000}
        for t in self._sub("units"):
            m = re.match(r"How many (\w+) are there in ([\d.]+) (\w+)\?", t.prompt) or \
                re.match(r"Convert ([\d.]+) (\w+) to (\w+)\.", t.prompt)
            g = m.groups()
            if t.prompt.startswith("How"):
                to, x, frm = g
            else:
                x, frm, to = g
            self.assertAlmostEqual(t.reference, float(x) * factors[(frm, to)], places=6, msg=t.prompt)

    def test_weekday(self):
        for t in self._sub("weekday"):
            day, k = re.search(r"today is (\w+), .*? (\d+) days", t.prompt).groups()
            d = DAYS_EN.index(day)
            want = (d + int(k)) % 7 if "from now" in t.prompt else (d - int(k)) % 7
            self.assertEqual(t.reference, DAYS_EN[want])
            self.assertIn(DAYS_HI[want], t.scorer["values"])

    def test_interest(self):
        for t in self._sub("simple_interest"):
            p, r, y = map(int, re.search(r"₹(\d+) .*?(\d+)% per year .*?(\d+) years", t.prompt).groups())
            si = p * r * y / 100.0
            want = p + si if "total amount" in t.prompt else si
            self.assertAlmostEqual(t.reference, want, places=6, msg=t.prompt)

    def test_triples_share_answer(self):
        by = {}
        for t in load_pack("math-pairs"):
            by.setdefault(t.meta["group"], []).append(t)
        for g, ts in by.items():
            self.assertEqual(len(ts), 3)
            specs = {json.dumps(t.scorer, sort_keys=True, ensure_ascii=False) for t in ts}
            self.assertEqual(len(specs), 1, g)  # same accepted answers in every language
            nums = [re.findall(r"\d+(?:\.\d+)?", t.prompt) for t in ts]
            self.assertEqual(sorted(nums[0]), sorted(nums[1]), g)  # same numbers in the text
            self.assertEqual(sorted(nums[0]), sorted(nums[2]), g)

    def test_hindi_is_devanagari(self):
        for name in ("math-pairs", "extract-pairs", "ifeval"):
            for t in load_pack(name):
                if t.lang == "hi":
                    self.assertTrue(re.search(r"[\u0900-\u097F]", t.prompt), t.id)
                if t.lang == "hinglish":
                    self.assertFalse(re.search(r"[\u0900-\u097F]", t.prompt), t.id)

    def test_extraction_fields_in_text(self):
        for t in load_pack("extract-pairs"):
            src = t.meta["source_text"]
            ref = t.reference
            for k, v in ref.items():
                accepted = t.scorer["fields"][k]
                self.assertIn(v, accepted)
                if k in ("order_id", "invoice_no", "email"):
                    self.assertIn(v, src)
                if k == "phone":
                    self.assertTrue(re.fullmatch(r"\d{10}", v))
                    self.assertIn(v, re.sub(r"\D", "", src))
                if k in ("total", "amount"):
                    shown = [_num(x) for x in re.findall(r"₹([\d,]+(?:\.\d+)?)", src)]
                    self.assertIn(float(v), shown, t.id)
                if k == "date":
                    self.assertTrue(re.fullmatch(r"\d{4}-\d\d-\d\d", v))
                if k == "time":
                    self.assertTrue(re.fullmatch(r"\d\d:\d\d", v))
            if t.meta["subtype"] == "order" and " x " in src:  # unit price shown: qty * price == total
                shown = [_num(x) for x in re.findall(r"₹([\d,]+)", src)]
                q = ref["quantity"]
                self.assertTrue(any(abs(s * q - ref["total"]) < 1e-6 for s in shown), t.id)

    def test_extraction_dates_times(self):
        from upgrade_gate.packs._common import MONTHS_EN
        for t in load_pack("extract-pairs"):
            if t.lang != "en":
                continue
            src = t.meta["source_text"]
            if t.meta["subtype"] == "invoice":
                d, m, y = re.search(r"(\d\d)/(\d\d)/(\d{4})", src).groups()
                self.assertEqual(t.reference["date"], "%s-%s-%s" % (y, m, d))
            if t.meta["subtype"] == "appointment":
                m = re.search(r"(\d+):(\d\d) (AM|PM)", src)
                h = int(m.group(1)) % 12 + (12 if m.group(3) == "PM" else 0)
                self.assertEqual(t.reference["time"], "%02d:%s" % (h, m.group(2)))
                dm = re.search(r"(\d+) (%s) (\d{4})" % "|".join(MONTHS_EN), src) or \
                    re.search(r"(%s) (\d+), (\d{4})" % "|".join(MONTHS_EN), src)
                g = dm.groups()
                if g[0].isdigit():
                    d, mon, y = g
                else:
                    mon, d, y = g
                self.assertEqual(t.reference["date"], "%s-%02d-%02d" % (y, MONTHS_EN.index(mon) + 1, int(d)))

    def test_intent_labels(self):
        tasks = load_pack("intent")
        labels = set(tasks[0].scorer["labels"])
        for t in tasks:
            self.assertIn(t.reference, labels)
            self.assertEqual(t.scorer["value"], t.reference)
            self.assertIn(t.meta["message"], t.prompt)
        msgs = [t.meta["message"] for t in tasks if t.lang == "en"]
        self.assertEqual(len(msgs), len(set(msgs)))
        hg = [t for t in tasks if t.lang == "hinglish"]
        self.assertTrue(all(t.pair_id for t in hg))

    def test_ifeval_pairs(self):
        tasks = {t.id: t for t in load_pack("ifeval")}
        for t in tasks.values():
            if t.lang == "hi":
                en = tasks[t.pair_id]
                hi_types = [r["type"] for r in t.scorer["rules"]]
                self.assertEqual(hi_types[:-1], [r["type"] for r in en.scorer["rules"]])
                self.assertEqual(hi_types[-1], "devanagari_ratio_min")


@unittest.skipUnless(DOCS_OK, "docs-synth assets not built")
class TestDocs(unittest.TestCase):
    def test_arithmetic_and_pairs(self):
        tasks = load_pack("docs-synth")
        by_id = {t.id: t for t in tasks}
        for t in tasks:
            li = t.meta["line_items"]
            ref = t.reference
            for l in li:
                self.assertAlmostEqual(l["qty"] * l["rate"], l["amount"], places=6)
            self.assertAlmostEqual(sum(l["amount"] for l in li), ref["subtotal"], places=6)
            self.assertAlmostEqual(ref["subtotal"] + ref["gst"], ref["total"], places=6)
            self.assertLess(abs(ref["subtotal"] * t.meta["gst_rate"] / 100.0 - ref["gst"]), 0.02)
            self.assertTrue(re.fullmatch(r"\d{4}-\d\d-\d\d", ref["date"]))
            if t.pair_id:
                other = by_id[t.pair_id]
                for k in ("invoice_number", "date", "subtotal", "gst", "total"):
                    self.assertEqual(ref[k], other.reference[k])

    def test_assets_size(self):
        d = os.path.join(ROOT, "data", "docs-synth")
        total = sum(os.path.getsize(os.path.join(d, f)) for f in os.listdir(d))
        self.assertLess(total, 40 * 1024 * 1024)

    def test_files_are_real_png_pdf(self):
        for t in load_pack("docs-synth"):
            with open(os.path.join(ROOT, t.attachments[0]), "rb") as f:
                head = f.read(8)
            if t.modality == "image":
                self.assertEqual(head, b"\x89PNG\r\n\x1a\n")
            else:
                self.assertEqual(head[:5], b"%PDF-")


class TestCanary(unittest.TestCase):
    def test_spec_passthrough(self):
        with open(os.path.join(ROOT, "canary", "prompts.json"), encoding="utf-8") as f:
            rows = {r["id"]: r for r in json.load(f)}
        for t in load_pack("canary"):
            row = rows[t.meta["canary_id"]]
            self.assertEqual(t.scorer, dict(row["check"], strict_only=True))
            self.assertEqual(t.prompt, row["prompt"])

    def test_gold_passes_canary_checks(self):
        import sys
        sys.path.insert(0, os.path.join(ROOT, "canary"))
        try:
            import checks  # canary/checks.py
        finally:
            sys.path.pop(0)
        for t in load_pack("canary"):
            if t.scorer["type"] in ("not_refusal",) or t.reference is None:
                continue
            ok, why = checks.check(t.reference, t.scorer)
            self.assertTrue(ok, (t.id, why))


if __name__ == "__main__":
    unittest.main()
