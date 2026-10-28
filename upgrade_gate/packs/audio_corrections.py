"""audio-corrections (E8): order voice notes where the customer takes a number back and says it again.

data/audio-corrections/manifest.jsonl is written by scripts/build_corrections.py. 15 items × en/hi/hinglish,
each as a correction clip ("9 3 4 3 7… sorry, no, 9 3 4 7 3") and a control clip with only the final number.
The right answer is always the final number. Real-voice takes of the correction lines (recorded on
web/#/record/corrections, saved in data/audio-real/) are added with meta speaker set.
Same instruction, scorer and voices as the audio-synth extract clips.
"""
from __future__ import annotations

import json
import os
from typing import Dict, List

from ..schema import Task
from .audio_synth import ASK, CATEGORY, _scorer

PACK = "audio-corrections"
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MANIFEST = os.path.join(ROOT, "data", "audio-corrections", "manifest.jsonl")
REAL = os.path.join(ROOT, "data", "audio-real", "manifest.jsonl")
PROMPT = "Listen to the attached audio. " + ASK["extract"]


def _task(tid: str, r: dict, wav: str, speaker: str) -> Task:
    return Task(
        id=tid, pack=PACK, category=CATEGORY["extract"], lang=r["lang"], modality="audio", prompt=PROMPT,
        reference=r["answer"], scorer=_scorer("extract", r["answer"]), attachments=[wav], pair_id=None,
        meta={"group": "%s-%s" % (PACK, r["item"]), "kind": "extract", "item": r["item"], "variant": r["variant"],
              "field": r["field"], "first": r["first"], "speaker": speaker, "voice": r.get("voice"),
              "transcript": r["transcript"], "clip": r["clip_id"]})


def build() -> List[Task]:
    if not os.path.exists(MANIFEST):
        raise FileNotFoundError("%s missing: run `PYTHONPATH=. python3 scripts/build_corrections.py` (macOS)"
                                % MANIFEST)
    with open(MANIFEST, encoding="utf-8") as f:
        rows: Dict[str, dict] = {r["clip_id"]: r for r in map(json.loads, f) if r}
    tasks = [_task("%s-%s" % (PACK, cid[len("corr-"):]), r, r["wav"], "synthetic") for cid, r in rows.items()]
    latest: Dict[tuple, dict] = {}
    if os.path.exists(REAL):
        with open(REAL, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    x = json.loads(line)
                    if x["clip_id"] in rows:
                        latest[(x["speaker"], x["clip_id"])] = x  # a re-recording replaces the earlier take
    for (speaker, cid), x in sorted(latest.items()):
        if os.path.exists(os.path.join(ROOT, x["wav"])):
            tasks.append(_task("%s-%s-%s" % (PACK, speaker, cid[len("corr-"):]), rows[cid], x["wav"], speaker))
    return tasks
