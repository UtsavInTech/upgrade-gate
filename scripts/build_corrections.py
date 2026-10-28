"""Build data/audio-corrections/: order voice notes where the customer corrects a number mid-sentence (E8).

Each of 15 items exists in English, Hindi and Hinglish, and in two versions with the same final details:
  corr  a number is said, taken back ("… sorry, no, …") and replaced
  ctrl  the same note with only the final number
8 items correct the order number, 7 the pincode. macOS `say` + `afconvert`, 16 kHz mono WAV, fixed seed.
The answer is always the *final* value; `first` records the taken-back one.

    PYTHONPATH=. python3 scripts/build_corrections.py
"""
from __future__ import annotations

import json
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from build_audio import speak, spaced, voice  # noqa: E402
from upgrade_gate.packs._common import CITIES, NAMES  # noqa: E402

OUT = os.path.join(ROOT, "data", "audio-corrections")
SEED = 20261028 + 8
ITEMS = 15
PAUSE = "[[slnc 450]]"  # a short silence in macOS speech, as people pause before correcting


def _change(digits: str, rng: random.Random) -> str:
    """A believable slip: swap two neighbouring digits, or change one digit."""
    d = list(digits)
    for _ in range(20):
        if rng.random() < 0.5:
            i = rng.randrange(1, len(d) - 1)
            d[i], d[i + 1] = d[i + 1], d[i]
        else:
            i = rng.randrange(1, len(d))
            d[i] = str((int(d[i]) + rng.randint(1, 8)) % 10)
        if "".join(d) != digits:
            return "".join(d)
        d = list(digits)
    return digits[:-1] + str((int(digits[-1]) + 1) % 10)


def lines(n, c, order, pin, field, first, gender):
    """(en, hi, hinglish) for the correction version and the control version."""
    bol, bol_hi = ("rahi", "रही") if gender == "f" else ("raha", "रहा")
    O, P, F = spaced(order), spaced(pin), spaced(first)
    if field == "order_number":
        en_c = ("Hello, this is %s from %s. My order number is %s. %s Sorry, no, %s. My pincode is %s. "
                "Please call me back." % (n[0], c[0], F, PAUSE, O, P))
        hi_c = ("नमस्ते, मैं %s %s से बोल %s हूँ। मेरा ऑर्डर नंबर %s है। %s नहीं नहीं, माफ़ कीजिए, %s है। मेरा पिनकोड %s है। "
                "कृपया मुझे वापस कॉल करें।" % (n[1], c[1], bol_hi, F, PAUSE, O, P))
        hl_c = ("Hello, main %s %s se bol %s hoon. Mera order number %s hai. %s Nahi nahi, sorry, %s hai. "
                "Mera pincode %s hai. Please mujhe call back kijiye." % (n[0], c[0], bol, F, PAUSE, O, P))
    else:
        en_c = ("Hello, this is %s from %s. My order number is %s. My pincode is %s. %s Sorry, I mean %s. "
                "Please call me back." % (n[0], c[0], O, F, PAUSE, P))
        hi_c = ("नमस्ते, मैं %s %s से बोल %s हूँ। मेरा ऑर्डर नंबर %s है। मेरा पिनकोड %s है। %s नहीं, माफ़ कीजिए, %s है। "
                "कृपया मुझे वापस कॉल करें।" % (n[1], c[1], bol_hi, O, F, PAUSE, P))
        hl_c = ("Hello, main %s %s se bol %s hoon. Mera order number %s hai. Mera pincode %s hai. %s Nahi, sorry, "
                "%s hai. Please mujhe call back kijiye." % (n[0], c[0], bol, O, F, PAUSE, P))
    en_k = "Hello, this is %s from %s. My order number is %s. My pincode is %s. Please call me back." % (n[0], c[0], O, P)
    hi_k = ("नमस्ते, मैं %s %s से बोल %s हूँ। मेरा ऑर्डर नंबर %s है। मेरा पिनकोड %s है। कृपया मुझे वापस कॉल करें।"
            % (n[1], c[1], bol_hi, O, P))
    hl_k = ("Hello, main %s %s se bol %s hoon. Mera order number %s hai. Mera pincode %s hai. "
            "Please mujhe call back kijiye." % (n[0], c[0], bol, O, P))
    return {"corr": {"en": en_c, "hi": hi_c, "hinglish": hl_c}, "ctrl": {"en": en_k, "hi": hi_k, "hinglish": hl_k}}


def main() -> None:
    if sys.platform != "darwin":
        sys.exit("needs macOS `say` and `afconvert`")
    rng = random.Random(SEED)
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for i in range(ITEMS):
        n, c = rng.choice(NAMES), rng.choice(CITIES)
        order, pin = str(rng.randint(10000, 99999)), str(rng.randint(110000, 859999))
        field = "order_number" if i < 8 else "pincode"
        first = _change(order if field == "order_number" else pin, rng)
        text = lines(n, c, order, pin, field, first, n[2])
        for variant in ("corr", "ctrl"):
            for lang in ("en", "hi", "hinglish"):
                cid = "corr-%02d-%s-%s" % (i, lang, variant)
                rel = os.path.join("data", "audio-corrections", cid + ".wav")
                v = voice(lang, n[2])
                if not os.path.exists(os.path.join(ROOT, rel)):
                    speak(text[variant][lang], v, os.path.join(ROOT, rel))
                rows.append({"clip_id": cid, "kind": "extract", "item": "corr-%02d" % i, "lang": lang,
                             "variant": variant, "field": field, "first": first, "voice": v,
                             "transcript": text[variant][lang].replace(PAUSE + " ", "").replace(PAUSE, ""),
                             "answer": {"order_number": order, "pincode": pin, "city": [c[0], c[1]]}, "wav": rel})
        print("corr-%02d done (%s: %s -> %s)" % (i, field, first, order if field == "order_number" else pin), flush=True)
    with open(os.path.join(OUT, "manifest.jsonl"), "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("wrote %d clips" % len(rows))


if __name__ == "__main__":
    main()
