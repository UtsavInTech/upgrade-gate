"""docs-synth: field extraction from synthetic invoice / receipt images and PDFs.

Assets and ground truth are produced by scripts/build_assets.py into data/docs-synth/.
This loader only reads data/docs-synth/manifest.jsonl (no Chrome needed). Each document yields
two tasks: one with the PNG attached (modality "image") and one with the PDF ("pdf").
Hindi docs mirror the numbers of the English doc with the same index (pair_id -> that doc's
task of the same modality).
"""
from __future__ import annotations

import json
import os
from typing import List

from ..schema import Task

PACK = "docs-synth"
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MANIFEST = os.path.join(ROOT, "data", "docs-synth", "manifest.jsonl")

PROMPT = {
    "en": ("The attached document is an invoice or receipt. Extract these fields and reply with only a JSON object "
           "with these keys: vendor (the seller's business name), invoice_number, date (YYYY-MM-DD), subtotal, "
           "gst (total GST amount; if CGST and SGST are listed, their sum), total. Write subtotal, gst and total as "
           "plain numbers without ₹ or commas."),
    "hi": ("संलग्न दस्तावेज़ एक बिल या रसीद है। इससे ये फ़ील्ड निकालें और केवल एक JSON object लिखें, जिसकी keys ये हों: "
           "vendor (बेचने वाली दुकान/कंपनी का नाम), invoice_number, date (YYYY-MM-DD), subtotal, gst (कुल GST राशि; "
           "अगर CGST और SGST अलग-अलग लिखे हों तो दोनों का जोड़), total। subtotal, gst और total को बिना ₹ और कॉमा के "
           "सादी संख्या के रूप में लिखें।"),
}


def build() -> List[Task]:
    if not os.path.exists(MANIFEST):
        raise FileNotFoundError("%s missing: run `PYTHONPATH=. python3 scripts/build_assets.py`" % MANIFEST)
    tasks: List[Task] = []
    with open(MANIFEST, encoding="utf-8") as f:
        rows = [json.loads(l) for l in f if l.strip()]
    for row in rows:
        fl = row["fields"]
        spec_fields = {
            "vendor": list(row["vendor_accept"]),
            "invoice_number": [fl["invoice_number"]],
            "date": [fl["date"]],
            "subtotal": [fl["subtotal"]],
            "gst": [fl["gst"]],
            "total": [fl["total"]],
        }
        for modality, key in (("image", "png"), ("pdf", "pdf")):
            suffix = "img" if modality == "image" else "pdf"
            pair = None
            if row.get("pair_doc"):
                pair = "%s-%s" % (row["pair_doc"], suffix)
            tasks.append(Task(
                id="%s-%s" % (row["doc_id"], suffix), pack=PACK, category="doc-image", lang=row["lang"],
                modality=modality, prompt=PROMPT[row["lang"]], reference=dict(fl),
                scorer={"type": "json_fields", "fields": {k: list(v) for k, v in spec_fields.items()}, "numeric_tol": 0.01},
                attachments=[row[key]], pair_id=pair,
                meta={"group": pair or "%s-%s" % (row["doc_id"], suffix), "doc_id": row["doc_id"],
                      "layout": row["layout"], "variant": row["variant"] if modality == "image" else "clean",
                      "bilingual": row["bilingual"], "font": row["font"], "gst_rate": row["gst_rate"],
                      "line_items": row["line_items"], "date_shown": row["date_shown"]},
            ))
    return tasks
