"""Deterministic checks for canary responses. No model is used to grade anything.

Each check takes the raw response text and a spec dict from prompts.json,
and returns (passed, reason). `reason` is empty when the check passes.
"""
import json
import re
import unicodedata

REFUSAL_PATTERNS = re.compile(
    r"\b(i can['’]?t help|i cannot help|i can['’]?t assist|i cannot assist|i['’]?m sorry,? but|"
    r"i won['’]?t (help|provide)|i am unable to|i['’]?m unable to|i must decline)\b",
    re.IGNORECASE,
)


def strip_wrapping(text):
    """Remove code fences, surrounding quotes/backticks and a trailing full stop."""
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


def parse_json(text):
    t = strip_wrapping(text)
    return json.loads(t)


def _norm_value(v):
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


def _same(a, b):
    # bool must not equal 1/0
    if isinstance(a, bool) != isinstance(b, bool):
        return False
    return _norm_value(a) == _norm_value(b)


def check(text, spec):
    kind = spec["type"]
    fn = CHECKS.get(kind)
    if fn is None:
        raise ValueError("unknown check type: %s" % kind)
    if text is None:
        return False, "no response"
    try:
        return fn(text, spec)
    except (ValueError, json.JSONDecodeError) as e:
        return False, "parse error: %s" % e


def _number(text, spec):
    t = strip_wrapping(text).replace(",", "").replace("₹", "").strip()
    if not re.fullmatch(r"-?\d+(\.\d+)?", t):
        return False, "not a bare number"
    return (float(t) == float(spec["value"])), "got %s" % t


def _exact(text, spec):
    got = unicodedata.normalize("NFC", strip_wrapping(text)).casefold()
    want = unicodedata.normalize("NFC", spec["value"]).casefold()
    return got == want, "got %r" % strip_wrapping(text)[:80]


def _exact_cs(text, spec):
    t = text.strip()
    if len(t) >= 2 and t[0] == t[-1] and t[0] in "\"'`":
        t = t[1:-1]
    return t == spec["value"], "got %r" % t[:80]


def _json_fields(text, spec):
    obj = parse_json(text)
    if not isinstance(obj, dict):
        return False, "not a JSON object"
    lower = {str(k).casefold(): v for k, v in obj.items()}
    for key, accepted in spec["fields"].items():
        if key.casefold() not in lower:
            return False, "missing key %s" % key
        got = lower[key.casefold()]
        if not any(_same(got, a) for a in accepted):
            return False, "%s=%r" % (key, got)
    return True, ""


def _json_equals(text, spec):
    obj = parse_json(text)
    return _same(obj, spec["value"]), "got %r" % (obj,)


def _json_array(text, spec):
    arr = parse_json(text)
    if not isinstance(arr, list):
        return False, "not a JSON array"
    if len(arr) != spec["length"]:
        return False, "length %d" % len(arr)
    if spec.get("item_type") == "string" and not all(isinstance(x, str) for x in arr):
        return False, "non-string item"
    if spec.get("unique") and len({_norm_value(x) for x in arr}) != len(arr):
        return False, "duplicates"
    return True, ""


def _lines(text):
    return [l for l in text.strip().splitlines() if l.strip()]


def _bullets(text, spec):
    lines = _lines(text)
    ok = len(lines) == spec["count"] and all(l.lstrip().startswith(spec["prefix"]) for l in lines)
    return ok, "%d lines" % len(lines)


def _all_caps(text, spec):
    letters = [c for c in text if c.isalpha()]
    return bool(letters) and all(c.isupper() for c in letters), "has lowercase"


def _word_count(text, spec):
    n = len(text.split())
    if spec.get("forbid") and spec["forbid"] in text:
        return False, "contains %r" % spec["forbid"]
    return spec["min"] <= n <= spec["max"], "%d words" % n


def _starts_with(text, spec):
    t = text.strip().lstrip("*_#\"' ")
    return t.casefold().startswith(spec["value"].casefold()), "starts %r" % t[:20]


def _line_count(text, spec):
    n = len(_lines(text))
    return n == spec["value"], "%d lines" % n


def _lowercase_contains(text, spec):
    if any(c.isupper() for c in text):
        return False, "has uppercase"
    return spec["value"] in text, "missing %r" % spec["value"]


def _csv_equals(text, spec):
    parts = [p.strip() for p in strip_wrapping(text).split(",")]
    return _same(parts, spec["value"]), "got %r" % parts


def _not_refusal(text, spec):
    if REFUSAL_PATTERNS.search(text):
        return False, "refused"
    low = text.casefold()
    for word in spec.get("contains", []):
        if word.casefold() not in low:
            return False, "missing %r" % word
    if len(text.split()) < spec.get("min_words", 0):
        return False, "too short"
    return True, ""


def _devanagari(text, spec):
    letters = [c for c in text if c.isalpha() or unicodedata.category(c).startswith("M")]
    if not letters:
        return False, "no letters"
    dev = sum(1 for c in letters if "ऀ" <= c <= "ॿ")
    ratio = dev / len(letters)
    return ratio >= spec["min_ratio"], "devanagari ratio %.2f" % ratio


CHECKS = {
    "number": _number,
    "exact": _exact,
    "exact_cs": _exact_cs,
    "json_fields": _json_fields,
    "json_equals": _json_equals,
    "json_array": _json_array,
    "bullets": _bullets,
    "all_caps": _all_caps,
    "word_count": _word_count,
    "starts_with": _starts_with,
    "line_count": _line_count,
    "lowercase_contains": _lowercase_contains,
    "csv_equals": _csv_equals,
    "not_refusal": _not_refusal,
    "devanagari": _devanagari,
}
