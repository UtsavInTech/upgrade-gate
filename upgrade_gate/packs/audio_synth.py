"""audio-synth: spoken English / Hindi / Hinglish clips with known answers, plus text twins.

Clips are made by scripts/build_audio.py (macOS text-to-speech) into data/audio-synth/.
Every clip gives two tasks with the same instruction:
  - modality "audio": the WAV is attached, the words are not in the prompt
  - modality "text":  the same words as written text, no audio
If a model fails a clip but passes its text twin, the problem is listening, not reasoning.
Instructions are in English for every language, so only the spoken language changes.
Kinds: math (bare number), extract (order_number, pincode, city as JSON), intent (5 labels).
"""
from __future__ import annotations

import json
import os
from typing import List

from ..schema import Task

PACK = "audio-synth"
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MANIFEST = os.path.join(ROOT, "data", "audio-synth", "manifest.jsonl")
LABELS = ["address_change", "cancel_order", "delivery_status", "payment_failed", "refund_request"]

ASK = {
    "math": "Answer the question. Reply with only the final number.",
    "extract": ("This is a customer's voice note. Reply with only a JSON object with keys order_number, "
                "pincode and city. Write order_number and pincode as digit strings and city in English."),
    "intent": ("This is a customer's voice note. Classify it as exactly one of: %s. Reply with only the label."
               % ", ".join(LABELS)),
}
CATEGORY = {"math": "math", "extract": "extraction", "intent": "classification"}


def _scorer(kind: str, answer):
    if kind == "math":
        return {"type": "number", "value": answer}
    if kind == "extract":
        return {"type": "json_fields", "fields": {
            "order_number": [answer["order_number"], int(answer["order_number"])],
            "pincode": [answer["pincode"], int(answer["pincode"])],
            "city": list(answer["city"])}}
    return {"type": "label", "value": answer, "labels": LABELS}


def build() -> List[Task]:
    if not os.path.exists(MANIFEST):
        raise FileNotFoundError("%s missing: run `PYTHONPATH=. python3 scripts/build_audio.py` (macOS)" % MANIFEST)
    with open(MANIFEST, encoding="utf-8") as f:
        rows = [json.loads(l) for l in f if l.strip()]
    tasks: List[Task] = []
    for r in rows:
        kind, lang = r["kind"], r["lang"]
        en_id = "%s-%s-en" % (PACK, r["item"])
        for modality in ("audio", "text"):
            base = "%s-%s-%s" % (PACK, r["item"], lang)
            tid = base if modality == "audio" else base + "-text"
            if modality == "audio":
                prompt = "Listen to the attached audio. " + ASK[kind]
                attachments = [r["wav"]]
            else:
                prompt = ASK[kind] + "\n\n" + r["transcript"]
                attachments = []
            pair = None if lang == "en" else (en_id if modality == "audio" else en_id + "-text")
            tasks.append(Task(
                id=tid, pack=PACK, category=CATEGORY[kind], lang=lang, modality=modality, prompt=prompt,
                reference=r["answer"], scorer=_scorer(kind, r["answer"]), attachments=attachments, pair_id=pair,
                meta={"group": "%s-%s" % (PACK, r["item"]), "kind": kind, "item": r["item"], "voice": r["voice"],
                      "transcript": r["transcript"], "twin": base + "-text" if modality == "audio" else base}))
    return tasks


def build_audio_only() -> List[Task]:
    """Just the spoken clips, without text twins (for experiments where the twins add nothing)."""
    out = [t for t in build() if t.modality == "audio"]
    for t in out:
        t.pack = "audio-clips"
    return out
