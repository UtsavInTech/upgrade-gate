"""Import a friend's recordings from the public site's "Download all" file.

  python3 scripts/import_recordings.py ~/Downloads/voice-notes-riya.zip [--force]

Writes data/audio-real/<speaker>/<clip>.wav (git-ignored, stays private), keeps their speaker.json
(voice, consent) next to them, and appends data/audio-real/manifest.jsonl the same way the local
recording page does. The zip came from someone else's phone, so every entry is checked: only known
clip ids, a valid speaker name, real WAV data, and no paths outside the speaker folder.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import zipfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "data", "audio-real")
SPEAKER = re.compile(r"^[a-z0-9-]{1,32}$")
MAX_WAV = 10_000_000


def known_clips() -> set:
    ids = set()
    for name in ("record.json", "record-corrections.json"):
        with open(os.path.join(REPO, "web", "public", "data", name), encoding="utf-8") as f:
            ids.update(row["clip_id"] for row in json.load(f))
    return ids


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("zip")
    ap.add_argument("--force", action="store_true", help="replace clips this speaker already has")
    args = ap.parse_args(argv)

    clips = known_clips()
    wavs, meta, speaker = {}, None, None
    with zipfile.ZipFile(args.zip) as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            parts = info.filename.split("/")
            if len(parts) != 2 or not SPEAKER.match(parts[0]):
                raise SystemExit(f"unexpected entry {info.filename!r}")
            if speaker and parts[0] != speaker:
                raise SystemExit("the file mixes more than one speaker")
            speaker = parts[0]
            if parts[1] == "speaker.json":
                meta = json.loads(z.read(info).decode("utf-8"))
                continue
            clip = parts[1][:-4] if parts[1].endswith(".wav") else None
            if clip not in clips:
                raise SystemExit(f"unknown clip {parts[1]!r}")
            if info.file_size > MAX_WAV:
                raise SystemExit(f"{parts[1]} is too large")
            data = z.read(info)
            if data[:4] != b"RIFF" or data[8:12] != b"WAVE":
                raise SystemExit(f"{parts[1]} is not a WAV file")
            wavs[clip] = data
    if not speaker or not wavs:
        raise SystemExit("no recordings in this file")

    folder = os.path.join(OUT, speaker)
    os.makedirs(folder, exist_ok=True)
    existing = [c for c in wavs if os.path.exists(os.path.join(folder, c + ".wav"))]
    if existing and not args.force:
        raise SystemExit(f"{speaker} already has {len(existing)} of these clips; rerun with --force to replace")

    now = dt.datetime.now(dt.timezone.utc).isoformat()
    with open(os.path.join(OUT, "manifest.jsonl"), "a", encoding="utf-8") as manifest:
        for clip, data in sorted(wavs.items()):
            with open(os.path.join(folder, clip + ".wav"), "wb") as f:
                f.write(data)
            manifest.write(json.dumps({
                "speaker": speaker, "clip_id": clip,
                "wav": f"data/audio-real/{speaker}/{clip}.wav", "ts": now, "source": "import",
            }) + "\n")
    if meta is not None:
        with open(os.path.join(folder, "speaker.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

    voice = (meta or {}).get("voice") or "not given"
    print(f"{speaker}: imported {len(wavs)} clips (voice: {voice}) into data/audio-real/{speaker}/")
    with open(os.path.join(REPO, "web", "public", "data", "record.json"), encoding="utf-8") as f:
        main_set = [row["clip_id"] for row in json.load(f)]
    missing = [c for c in main_set if c not in wavs]
    if missing:
        print(f"  {len(missing)} of the {len(main_set)} main lines not recorded yet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
