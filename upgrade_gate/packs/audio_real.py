"""audio-real: the audio-synth lines read aloud by real people (recorded with web/#/record).

data/audio-real/manifest.jsonl is written by the recording page; each row names a speaker and the
audio-synth clip they read. Answers, instructions and scorers come from the matching audio-synth
clip, so the only thing that changes is the voice. Empty until someone records.
"""
from __future__ import annotations

import json
import os
from typing import Dict, List

from ..schema import Task
from .audio_synth import ASK, CATEGORY, _scorer

PACK = "audio-real"
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REAL = os.path.join(ROOT, "data", "audio-real", "manifest.jsonl")
SYNTH = os.path.join(ROOT, "data", "audio-synth", "manifest.jsonl")


def build() -> List[Task]:
    if not os.path.exists(REAL) or not os.path.exists(SYNTH):
        return []
    with open(SYNTH, encoding="utf-8") as f:
        synth: Dict[str, dict] = {r["clip_id"]: r for r in map(json.loads, f) if r}
    latest: Dict[tuple, dict] = {}
    with open(REAL, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                latest[(r["speaker"], r["clip_id"])] = r  # a re-recording replaces the earlier take
    tasks: List[Task] = []
    for (speaker, clip_id), r in sorted(latest.items()):
        s = synth.get(clip_id)
        if not s or not os.path.exists(os.path.join(ROOT, r["wav"])):
            continue
        kind, lang = s["kind"], s["lang"]
        tasks.append(Task(
            id="%s-%s-%s-%s" % (PACK, speaker, s["item"], lang), pack=PACK, category=CATEGORY[kind], lang=lang,
            modality="audio", prompt="Listen to the attached audio. " + ASK[kind], reference=s["answer"],
            scorer=_scorer(kind, s["answer"]), attachments=[r["wav"]], pair_id=None,
            meta={"group": "%s-%s-%s" % (PACK, speaker, s["item"]), "kind": kind, "item": s["item"],
                  "speaker": speaker, "transcript": s["transcript"], "synthetic_clip": clip_id},
        ))
    return tasks
