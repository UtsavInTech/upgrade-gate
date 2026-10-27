"""Deterministic scorers. No model grades anything here.

Entry point::

    score_text(task, text) -> (passed: Optional[bool], score: float, detail: str)

`task.scorer` is a spec dict ``{"type": <name>, ...}``. When a spec omits its
expected value (``value`` / ``values`` / ``fields``), the task's ``reference`` is
used instead, so packs can write ``{"type": "json_fields"}`` and keep the truth
in one place.

Types (canary types keep the exact semantics of canary/checks.py):

  number {value, tol?, lenient?}      bare number; commas / Indian grouping, ₹, Rs,
                                      Devanagari digits accepted. lenient: last number.
  exact {value} / exact_cs {value}
  one_of {values}
  label {value, labels?}              bare label or {"label": ...}; case/space/_/-
                                      insensitive; several labels -> fail
  json_fields {fields, numeric_tol?}  partial score = fraction of fields right
  json_equals {value}
  json_array {length, item_type?, unique?}
  csv_equals {value}
  regex {pattern, flags?}
  contains_all {values}
  bullets {count, prefix}, all_caps, word_count {min,max,forbid?}, starts_with {value},
  line_count {value}, lowercase_contains {value}, not_refusal {contains?, min_words?},
  devanagari {min_ratio}
  ifeval {rules: [{type, ...}]}       see IFEVAL_RULES
"""
from __future__ import annotations

import json
import math
import re
import unicodedata
from typing import Any, Callable, Dict, List, Optional, Tuple

Result = Tuple[Optional[bool], float, str]

# ---------------------------------------------------------------- normalisation

REFUSAL_PATTERNS = re.compile(
    r"\b(i can['’]?t help|i cannot help|i can['’]?t assist|i cannot assist|i['’]?m sorry,? but|"
    r"i won['’]?t (help|provide)|i am unable to|i['’]?m unable to|i must decline)\b",
    re.IGNORECASE,
)

_THINK_RE = re.compile(r"^\s*<(think|thinking|reasoning)>.*?</\1>\s*", re.S | re.I)
_DEV_DIGITS = {ord("०") + i: str(i) for i in range(10)}


def strip_think(text: str) -> str:
    """Drop a leading <think>...</think> (or <thinking>/<reasoning>) block."""
    t = text
    while True:
        m = _THINK_RE.match(t)
        if not m:
            break
        t = t[m.end():]
    # some providers drop the opening tag: "reasoning...</think>answer"
    if "</think>" in t and "<think>" not in t:
        t = t.split("</think>", 1)[1]
    return t


def prepare(text: str) -> str:
    """NFC + think-block removal. Used before every scorer."""
    return strip_think(unicodedata.normalize("NFC", text)).strip()


def strip_wrapping(text: str) -> str:
    """Remove code fences, surrounding quotes/backticks and a trailing full stop or danda."""
    t = text.strip()
    fence = re.match(r"^```[a-zA-Z]*\s*\n?(.*?)\n?```$", t, re.S)
    if fence:
        t = fence.group(1).strip()
    for _ in range(2):
        if len(t) >= 2 and t[0] == t[-1] and t[0] in "\"'`":
            t = t[1:-1].strip()
    if t.endswith(".") or t.endswith("।"):
        t = t[:-1].strip()
    return t


def clean(text: str) -> str:
    return strip_wrapping(prepare(text))


def norm_digits(s: str) -> str:
    return s.translate(_DEV_DIGITS)


def _norm_value(v: Any) -> Any:
    if isinstance(v, str):
        return unicodedata.normalize("NFC", v.strip()).casefold()
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, list):
        return [_norm_value(x) for x in v]
    if isinstance(v, dict):
        return {str(k).casefold(): _norm_value(x) for k, x in v.items()}
    return v


def _same(a: Any, b: Any) -> bool:
    # bool must not equal 1/0
    if isinstance(a, bool) != isinstance(b, bool):
        return False
    return _norm_value(a) == _norm_value(b)


def _hashable(v: Any) -> Any:
    return json.dumps(_norm_value(v), sort_keys=True, ensure_ascii=False)


# ---------------------------------------------------------------- numbers

_NUM_TOKEN = re.compile(r"-?\d[\d,]*(?:\.\d+)?|-?\.\d+")


def parse_number(s: str) -> Optional[float]:
    """Parse a bare number: '1,23,456', '₹1,200', 'Rs. 50', '४२', '-3.5'. None if not bare."""
    t = norm_digits(unicodedata.normalize("NFC", s)).strip()
    t = re.sub(r"^(₹|rs\.?|inr|\$)\s*", "", t, flags=re.I)
    t = re.sub(r"\s*(₹|rs\.?|inr|rupees|रुपये|रुपए)$", "", t, flags=re.I)
    t = t.replace(",", "").replace(" ", "").replace(" ", "").strip()
    if not re.fullmatch(r"-?\d+(\.\d+)?|-?\.\d+", t):
        return None
    return float(t)


def _last_number(s: str) -> Optional[float]:
    t = norm_digits(s)
    m = re.search(r"####\s*(-?[\d,]*\.?\d+)", t)
    if m:
        return parse_number(m.group(1))
    found = _NUM_TOKEN.findall(t)
    for tok in reversed(found):
        v = parse_number(tok)
        if v is not None:
            return v
    return None


def _num_close(a: float, b: float, tol: float) -> bool:
    return abs(a - b) <= max(tol, 1e-9 * max(1.0, abs(b)))


# ---------------------------------------------------------------- json extraction

def extract_json(text: str) -> Tuple[Any, bool]:
    """Return (obj, lenient). Strict = whole cleaned text is JSON. Lenient = found inside
    a fenced block or as the first balanced {...}/[...] span. Raises ValueError."""
    t = prepare(text)
    try:
        return json.loads(strip_wrapping(t)), False
    except (ValueError, json.JSONDecodeError):
        pass
    for m in re.finditer(r"```[a-zA-Z]*\s*\n?(.*?)```", t, re.S):
        try:
            return json.loads(m.group(1).strip()), True
        except (ValueError, json.JSONDecodeError):
            continue
    dec = json.JSONDecoder()
    for i, ch in enumerate(t):
        if ch in "{[":
            try:
                obj, _ = dec.raw_decode(t[i:])
                return obj, True
            except (ValueError, json.JSONDecodeError):
                continue
    raise ValueError("no JSON found")


# ---------------------------------------------------------------- helpers

def _get(task: Any, key: str, default: Any = None) -> Any:
    if isinstance(task, dict):
        return task.get(key, default)
    return getattr(task, key, default)


def _want(task: Any, spec: Dict[str, Any], key: str) -> Any:
    if key in spec:
        return spec[key]
    ref = _get(task, "reference")
    if ref is None:
        raise KeyError("scorer spec has no %r and task has no reference" % key)
    return ref


def _b(ok: bool, detail: str = "") -> Result:
    return bool(ok), 1.0 if ok else 0.0, ("" if ok else detail)


def _lines(text: str) -> List[str]:
    return [l for l in text.strip().splitlines() if l.strip()]


def _dev_ratio(text: str) -> Optional[float]:
    letters = [c for c in text if c.isalpha() or unicodedata.category(c).startswith("M")]
    if not letters:
        return None
    dev = sum(1 for c in letters if "ऀ" <= c <= "ॿ")
    return dev / len(letters)


def _starts(text: str, value: str) -> bool:
    t = text.strip().lstrip("*_#\"' ")
    return t.casefold().startswith(value.casefold())


# ---------------------------------------------------------------- scorers
# each: fn(task, raw_text_prepared, spec) -> Result. Text is NFC + think-stripped.

def _number(task, text, spec):
    want = float(_want(task, spec, "value"))
    tol = float(spec.get("tol", 0.0))
    got = parse_number(strip_wrapping(text))
    lenient = False
    if got is None and spec.get("lenient"):
        got, lenient = _last_number(text), True
    if got is None:
        return False, 0.0, "not a bare number"
    ok = _num_close(got, want, tol)
    return ok, float(ok), "got %s%s" % (got, " (lenient)" if lenient else "")


def _exact(task, text, spec):
    want = str(_want(task, spec, "value"))
    got = strip_wrapping(text)
    ok = got.casefold() == unicodedata.normalize("NFC", want).casefold()
    return _b(ok, "got %r" % got[:80])


def _exact_cs(task, text, spec):
    want = str(_want(task, spec, "value"))
    t = text.strip()
    if len(t) >= 2 and t[0] == t[-1] and t[0] in "\"'`":
        t = t[1:-1]
    return _b(t == unicodedata.normalize("NFC", want), "got %r" % t[:80])


def _one_of(task, text, spec):
    values = _want(task, spec, "values")
    if not isinstance(values, list):
        values = [values]
    got = strip_wrapping(text)
    ok = any(_same(got, str(v)) for v in values)
    return _b(ok, "got %r" % got[:80])


def _lab_key(s: str) -> str:
    return re.sub(r"[\s_\-]+", "", unicodedata.normalize("NFC", str(s)).casefold())


def _lab_spaced(s: str) -> str:
    return re.sub(r"[\s_\-]+", " ", unicodedata.normalize("NFC", str(s)).casefold()).strip()


def _label(task, text, spec):
    want = _want(task, spec, "value")
    labels = list(spec.get("labels") or [])
    got = strip_wrapping(text)
    # JSON {"label": ...}
    try:
        obj, _ = extract_json(text)
        if isinstance(obj, dict):
            low = {str(k).casefold(): v for k, v in obj.items()}
            if "label" in low and isinstance(low["label"], str):
                got = low["label"]
    except ValueError:
        pass
    got = strip_wrapping(got)
    if _lab_key(got) == _lab_key(want):
        return True, 1.0, ""
    if labels and _lab_key(got) in {_lab_key(l) for l in labels}:
        return False, 0.0, "got %r" % got[:80]
    if not labels:
        return False, 0.0, "got %r" % got[:80]
    # lenient: find labels mentioned in the text
    hay = " " + _lab_spaced(text) + " "
    found = [l for l in labels if re.search(r"(?<!\w)" + re.escape(_lab_spaced(l)) + r"(?!\w)", hay)]
    # drop labels that are sub-phrases of another found label
    sp = [_lab_spaced(l) for l in found]
    found = [l for l, s in zip(found, sp)
             if not any(s != o and re.search(r"(?<!\w)" + re.escape(s) + r"(?!\w)", o) for o in sp)]
    if len(found) > 1:
        return False, 0.0, "multiple labels: %s" % ", ".join(map(str, found[:5]))
    if len(found) == 1:
        ok = _lab_key(found[0]) == _lab_key(want)
        return ok, float(ok), "lenient: found %r" % found[0]
    return False, 0.0, "no label in %r" % got[:80]


def _fields_spec(task, spec) -> Dict[str, List[Any]]:
    if "fields" in spec:
        return {k: (v if isinstance(v, list) else [v]) for k, v in spec["fields"].items()}
    ref = _get(task, "reference")
    if not isinstance(ref, dict):
        raise KeyError("json_fields needs spec.fields or a dict reference")
    return {k: [v] for k, v in ref.items()}


def _field_ok(got: Any, accepted: Any, tol: Optional[float]) -> bool:
    if _same(got, accepted):
        return True
    if isinstance(accepted, (int, float)) and not isinstance(accepted, bool):
        g = got
        if isinstance(g, str):
            g = parse_number(g)
        if isinstance(g, (int, float)) and not isinstance(g, bool) and g is not None:
            return _num_close(float(g), float(accepted), tol or 0.0)
    return False


def _json_fields(task, text, spec):
    fields = _fields_spec(task, spec)
    obj, lenient = extract_json(text)
    if not isinstance(obj, dict):
        return False, 0.0, "not a JSON object"
    tol = spec.get("numeric_tol")
    lower = {str(k).casefold(): v for k, v in obj.items()}
    bad = []
    for key, accepted in fields.items():
        if key.casefold() not in lower:
            bad.append("missing %s" % key)
            continue
        got = lower[key.casefold()]
        if not any(_field_ok(got, a, tol) for a in accepted):
            bad.append("%s=%r" % (key, got))
    n = len(fields)
    score = (n - len(bad)) / n if n else 1.0
    detail = "; ".join(bad)
    if lenient:
        detail = ("lenient json; " + detail).rstrip("; ")
    return not bad, score, detail


def _json_equals(task, text, spec):
    want = _want(task, spec, "value")
    obj, lenient = extract_json(text)
    ok = _same(obj, want)
    detail = "" if ok else "got %r" % (obj,)
    if lenient:
        detail = ("lenient json; " + detail).rstrip("; ")
    return ok, float(ok), detail


def _json_array(task, text, spec):
    arr, _ = extract_json(text)
    if not isinstance(arr, list):
        return False, 0.0, "not a JSON array"
    if len(arr) != spec["length"]:
        return False, 0.0, "length %d" % len(arr)
    if spec.get("item_type") == "string" and not all(isinstance(x, str) for x in arr):
        return False, 0.0, "non-string item"
    if spec.get("unique") and len({_hashable(x) for x in arr}) != len(arr):
        return False, 0.0, "duplicates"
    return True, 1.0, ""


def _csv_equals(task, text, spec):
    want = _want(task, spec, "value")
    parts = [p.strip() for p in strip_wrapping(text).split(",")]
    return _b(_same(parts, want), "got %r" % parts)


def _regex(task, text, spec):
    flags = 0
    for f in spec.get("flags", ""):
        flags |= {"i": re.I, "s": re.S, "m": re.M}.get(f, 0)
    ok = re.search(spec["pattern"], text, flags) is not None
    return _b(ok, "no match for %r" % spec["pattern"])


def _contains_all(task, text, spec):
    values = _want(task, spec, "values")
    if not isinstance(values, list):
        values = [values]
    low = text.casefold()
    missing = [v for v in values if unicodedata.normalize("NFC", str(v)).casefold() not in low]
    n = len(values)
    score = (n - len(missing)) / n if n else 1.0
    return not missing, score, ("missing %r" % missing if missing else "")


def _bullets(task, text, spec):
    lines = _lines(text)
    ok = len(lines) == spec["count"] and all(l.lstrip().startswith(spec["prefix"]) for l in lines)
    return _b(ok, "%d lines" % len(lines))


def _all_caps(task, text, spec):
    letters = [c for c in text if c.isalpha()]
    return _b(bool(letters) and all(c.isupper() for c in letters), "has lowercase")


def _word_count(task, text, spec):
    n = len(text.split())
    if spec.get("forbid") and spec["forbid"] in text:
        return False, 0.0, "contains %r" % spec["forbid"]
    return _b(spec["min"] <= n <= spec["max"], "%d words" % n)


def _starts_with(task, text, spec):
    t = text.strip().lstrip("*_#\"' ")
    return _b(_starts(text, spec["value"]), "starts %r" % t[:20])


def _line_count(task, text, spec):
    n = len(_lines(text))
    return _b(n == spec["value"], "%d lines" % n)


def _lowercase_contains(task, text, spec):
    if any(c.isupper() for c in text):
        return False, 0.0, "has uppercase"
    return _b(spec["value"] in text, "missing %r" % spec["value"])


def _not_refusal(task, text, spec):
    if REFUSAL_PATTERNS.search(text):
        return False, 0.0, "refused"
    low = text.casefold()
    for word in spec.get("contains", []):
        if word.casefold() not in low:
            return False, 0.0, "missing %r" % word
    if len(text.split()) < spec.get("min_words", 0):
        return False, 0.0, "too short"
    return True, 1.0, ""


def _devanagari(task, text, spec):
    r = _dev_ratio(text)
    if r is None:
        return False, 0.0, "no letters"
    return _b(r >= spec["min_ratio"], "devanagari ratio %.2f" % r)


# ---------------------------------------------------------------- ifeval rules
# each: fn(text, rule) -> (ok, detail)

def _r_word_count_between(t, r):
    n = len(t.split())
    return r.get("min", 0) <= n <= r.get("max", float("inf")), "%d words" % n


def _r_no_commas(t, r):
    return ("," not in t and "،" not in t), "has comma"


def _r_all_caps(t, r):
    letters = [c for c in t if c.isalpha() and c.upper() != c.lower()]
    return bool(letters) and all(c.isupper() for c in letters), "has lowercase"


def _r_all_lower(t, r):
    letters = [c for c in t if c.isalpha() and c.upper() != c.lower()]
    return bool(letters) and not any(c.isupper() for c in letters), "has uppercase"


def _r_starts_with(t, r):
    return _starts(t, r["value"]), "starts %r" % t.strip()[:20]


def _r_ends_with(t, r):
    s = t.strip().rstrip("*_\"'` ").strip()
    return s.casefold().endswith(str(r["value"]).casefold()), "ends %r" % s[-20:]


def _r_line_count(t, r):
    n = len(_lines(t))
    return n == r["value"], "%d lines" % n


def _r_bullet_count(t, r):
    prefixes = [r["prefix"]] if r.get("prefix") else ["- ", "* ", "• "]
    n = sum(1 for l in _lines(t) if any(l.lstrip().startswith(p) for p in prefixes))
    return n == r["value"], "%d bullets" % n


def _r_devanagari_ratio_min(t, r):
    x = _dev_ratio(t)
    return (x is not None and x >= r["value"]), "devanagari ratio %s" % ("n/a" if x is None else "%.2f" % x)


def _r_must_include(t, r):
    low = t.casefold()
    miss = [v for v in r["values"] if str(v).casefold() not in low]
    return not miss, "missing %r" % miss


def _r_must_not_include(t, r):
    low = t.casefold()
    hit = [v for v in r["values"] if str(v).casefold() in low]
    return not hit, "contains %r" % hit


def _r_json_parseable(t, r):
    try:
        json.loads(strip_wrapping(t))
        return True, ""
    except (ValueError, json.JSONDecodeError):
        return False, "not json"


IFEVAL_RULES: Dict[str, Callable[[str, Dict[str, Any]], Tuple[bool, str]]] = {
    "word_count_between": _r_word_count_between,
    "no_commas": _r_no_commas,
    "all_caps": _r_all_caps,
    "all_lower": _r_all_lower,
    "starts_with": _r_starts_with,
    "ends_with": _r_ends_with,
    "line_count": _r_line_count,
    "bullet_count": _r_bullet_count,
    "devanagari_ratio_min": _r_devanagari_ratio_min,
    "must_include": _r_must_include,
    "must_not_include": _r_must_not_include,
    "json_parseable": _r_json_parseable,
}


def _ifeval(task, text, spec):
    rules = spec.get("rules") or []
    for r in rules:
        if r.get("type") not in IFEVAL_RULES:
            raise ValueError("unknown ifeval rule type: %s" % r.get("type"))
    if not rules:
        return True, 1.0, "no rules"
    failed = []
    for r in rules:
        ok, why = IFEVAL_RULES[r["type"]](text, r)
        if not ok:
            failed.append("%s: %s" % (r["type"], why))
    score = (len(rules) - len(failed)) / len(rules)
    return not failed, score, "; ".join(failed)


SCORERS: Dict[str, Callable[[Any, str, Dict[str, Any]], Result]] = {
    "number": _number,
    "exact": _exact,
    "exact_cs": _exact_cs,
    "one_of": _one_of,
    "label": _label,
    "json_fields": _json_fields,
    "json_equals": _json_equals,
    "json_array": _json_array,
    "csv_equals": _csv_equals,
    "regex": _regex,
    "contains_all": _contains_all,
    "bullets": _bullets,
    "all_caps": _all_caps,
    "word_count": _word_count,
    "starts_with": _starts_with,
    "line_count": _line_count,
    "lowercase_contains": _lowercase_contains,
    "not_refusal": _not_refusal,
    "devanagari": _devanagari,
    "ifeval": _ifeval,
}


def has_scorer(task: Any) -> bool:
    spec = _get(task, "scorer") or {}
    return bool(spec.get("type"))


def score_text(task: Any, text: Optional[str]) -> Result:
    """Score one response. Unknown scorer type -> ValueError. text None -> (None, 0.0, 'api error')."""
    spec = _get(task, "scorer") or {}
    kind = spec.get("type")
    fn = SCORERS.get(kind)
    if fn is None:
        raise ValueError("unknown scorer type: %s" % kind)
    if kind == "ifeval":  # validate rules even when text is missing
        for r in spec.get("rules") or []:
            if r.get("type") not in IFEVAL_RULES:
                raise ValueError("unknown ifeval rule type: %s" % r.get("type"))
    if text is None:
        return None, 0.0, "api error"
    t = prepare(text)
    try:
        passed, score, detail = fn(task, t, spec)
    except (ValueError, json.JSONDecodeError, TypeError) as e:
        if isinstance(e, ValueError) and str(e).startswith("unknown "):
            raise
        return False, 0.0, "parse error: %s" % e
    if score is None or (isinstance(score, float) and math.isnan(score)):
        score = float(bool(passed))
    return passed, float(score), detail
