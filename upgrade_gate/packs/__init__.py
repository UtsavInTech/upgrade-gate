"""Task packs: synthetic, license-free test items with known answers.

    from upgrade_gate.packs import PACKS, load_pack
    tasks = load_pack("math-pairs", n=60, seed=1)

Packs (category, langs):
    math-pairs     math            en / hi / hinglish, matched triples (pair_id -> English task)
    extract-pairs  extraction      en / hi / hinglish, matched triples
    intent         classification  en + hinglish (hinglish paired to an English twin)
    ifeval         instruction     en + hi (hi paired to an English twin)
    docs-synth     doc-image       en + hi, modality image (PNG) and pdf; needs data/docs-synth/
    audio-synth    math/extraction/classification  en / hi / hinglish, modality audio (WAV) + text twin
    audio-clips    audio-synth without the text twins
    audio-real     the same lines read by real people (web/#/record); empty until recorded
    audio-corrections  E8: voice notes where a number is taken back and said again, plus controls
    canary         mixed           canary/prompts.json wrapped as Tasks

Content of every pack is fixed (generated from a fixed internal seed), so ids and tasks are
identical on every run. `seed` only chooses WHICH tasks are returned when `n` is given.
Sampling keeps pair groups together (meta["group"]); the English member of a group comes first,
so a truncated group never leaves a pair_id pointing at a task that was not returned.

----------------------------------------------------------------------------------------
SCORER SPECS (Task.scorer) -- every "type" used by these packs. Text normalisation below
("norm") = strip, remove code fences / wrapping quotes / one trailing "." or "।", NFC,
casefold -- same as canary/checks.py strip_wrapping + _exact.

New spec types (math-pairs, extract-pairs, intent, ifeval, docs-synth):
  number      {"value": float|int, "tol"?: float}
              Response is a bare number (commas, "₹", "Rs" stripped). Pass if |x - value| <= tol
              (default 1e-6). Used by math-pairs.
  one_of      {"values": [str, ...]}
              Pass if norm(response) equals norm(any value). Used for weekday names (English,
              Devanagari and romanised spellings all accepted) and HH:MM times ("09:05", "9:05").
  json_fields {"fields": {key: [accepted, ...]}, "numeric_tol"?: float}
              Response parses as a JSON object (after norm-style fence stripping). For every key
              (key match case-insensitive) the value must equal one accepted value: strings
              compared NFC+casefold+strip; numbers compared with numeric_tol (default 0). A
              numeric string like "18450" or "18,450.00" should be accepted for a numeric
              accepted value. Extra keys are ignored. Used by extract-pairs and docs-synth
              (numeric_tol 0.01).
  label       {"value": str, "labels": [str, ...]}
              Classification. Normalise (norm, also treat spaces/hyphens as underscores). Accept
              the label alone, or a JSON object {"label": "..."} / {"intent": "..."}. Pass if it
              equals value. Fail if the response is not one of `labels`. Used by intent.
  ifeval      {"rules": [rule, ...]}  -- pass only if EVERY rule passes. Rules:
      word_count_between  {"min": int, "max": int}     whitespace-split word count in [min, max]
      no_commas           {}                           no "," (also no "،" / "，")
      all_caps            {}                           every cased letter is uppercase (>=1 letter)
      all_lower           {}                           no uppercase letter
      starts_with         {"value": str}               response (leading whitespace, quotes, * _ # stripped)
                                                       starts with value, casefold
      ends_with           {"value": str}               response with trailing whitespace, quotes and
                                                       . ! । stripped ends with value, casefold
      line_count          {"value": int}               number of non-empty lines == value
      bullet_count        {"value": int, "prefix": "-"} lines whose lstrip() starts with prefix == value
                                                       (accept "*" or "•" as bullets too)
      devanagari_ratio_min {"value": float}            share of letters+marks in U+0900..U+097F >= value
                                                       (same formula as canary _devanagari)
      must_include        {"values": [str]}            every value appears as a casefold substring
      must_not_include    {"values": [str]}            no value appears as a whole word: tokens =
                                                       re.findall(r"[\\w\\u0900-\\u097F]+", casefold(text))
                                                       (Devanagari vowel signs are not \\w, hence the range)
      json_parseable      {"keys"?: [str]}             whole response (fences stripped) parses as JSON;
                                                       if keys given it is an object with exactly those keys
  Listed for completeness, not used by these packs: exact {value}, exact_cs {value},
  json_equals {value}, regex {pattern}, contains_all {values}.

Canary spec types (canary pack only; spec = canary/prompts.json "check" unchanged; implement by
delegating to canary/checks.py `check(text, spec)`):
  number {value}, exact {value}, exact_cs {value}, json_fields {fields}, json_equals {value},
  json_array {length, item_type?, unique?}, bullets {count, prefix}, all_caps {},
  word_count {min, max, forbid?}, starts_with {value}, line_count {value},
  lowercase_contains {value}, csv_equals {value}, not_refusal {contains?, min_words?},
  devanagari {min_ratio}
----------------------------------------------------------------------------------------
"""
from __future__ import annotations

import random
from typing import Callable, Dict, List, Optional

from ..schema import Task
from . import audio_corrections, audio_real, audio_synth, canary_pack, docs_synth, extract_pairs, ifeval_pack, intent, math_pairs

PACKS: Dict[str, Callable[..., List[Task]]] = {
    "math-pairs": math_pairs.build,
    "extract-pairs": extract_pairs.build,
    "intent": intent.build,
    "ifeval": ifeval_pack.build,
    "docs-synth": docs_synth.build,
    "audio-synth": audio_synth.build,
    "audio-real": audio_real.build,
    "audio-clips": audio_synth.build_audio_only,
    "audio-corrections": audio_corrections.build,
    "canary": canary_pack.build,
}

_CACHE: Dict[str, List[Task]] = {}


def _all(name: str) -> List[Task]:
    if name not in PACKS:
        raise KeyError("unknown pack %r; known: %s" % (name, ", ".join(sorted(PACKS))))
    if name not in _CACHE:
        _CACHE[name] = PACKS[name]()
    return _CACHE[name]


def _copy(t: Task) -> Task:
    import copy
    return copy.deepcopy(t)


def load_pack(name: str, n: Optional[int] = None, seed: int = 0) -> List[Task]:
    """Return tasks of pack `name`. With `n`, a seeded sample of n tasks that keeps pair groups
    together (whole groups are taken; only the last group may be cut, never its English member).
    Returned tasks keep the pack's original order."""
    tasks = _all(name)
    if n is None or n >= len(tasks):
        return [_copy(t) for t in tasks]
    if n <= 0:
        return []
    order = {t.id: i for i, t in enumerate(tasks)}
    groups: Dict[str, List[Task]] = {}
    for t in tasks:
        groups.setdefault(t.meta.get("group") or t.id, []).append(t)
    keys = sorted(groups)
    random.Random("%s:%d" % (name, seed)).shuffle(keys)
    picked: List[Task] = []
    for k in keys:
        g = sorted(groups[k], key=lambda t: (t.pair_id is not None, order[t.id]))  # unpaired/English first
        picked.extend(g[: n - len(picked)])
        if len(picked) >= n:
            break
    picked.sort(key=lambda t: order[t.id])
    return [_copy(t) for t in picked]


def load_packs(names: List[str], n: Optional[int] = None, seed: int = 0) -> List[Task]:
    """Convenience: several packs, `n` applied per pack."""
    out: List[Task] = []
    for nm in names:
        out.extend(load_pack(nm, n=n, seed=seed))
    return out
