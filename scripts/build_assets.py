#!/usr/bin/env python3
"""Generate the docs-synth assets: synthetic invoices / receipts as PNG + PDF with known fields.

    PYTHONPATH=. python3 scripts/build_assets.py            # build everything
    PYTHONPATH=. python3 scripts/build_assets.py --limit 4  # quick smoke build

Every document is rendered from an HTML template by headless Chrome (correct Devanagari
shaping). Ground truth is the exact set of values used to fill the template, written to
data/docs-synth/manifest.jsonl. The pack loader only reads the manifest, so loading tasks
needs no Chrome. "noisy" variants (rotation, paper tint, stains, speckles) are applied with
CSS in the PNG only; the PDF of the same document is always clean.

All names, GSTINs and numbers are invented.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from decimal import ROUND_HALF_UP, Decimal

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from upgrade_gate.packs._common import CITIES, MONTHS_EN, MONTHS_HI, VENDORS, fmt_inr  # noqa: E402

OUT = os.path.join(ROOT, "data", "docs-synth")
CHROME = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
N_EN = 60
N_HI = 40          # hi docs 1..40 mirror the numbers of en docs 1..40
SEED = "docs-synth:v1"
W, H = 900, 1200

ITEMS = [  # en, hi, price range (rupees)
    ("Basmati rice 5 kg", "बासमती चावल 5 किलो", (420, 890)),
    ("Sunflower oil 1 L", "सूरजमुखी तेल 1 लीटर", (140, 210)),
    ("Toor dal 1 kg", "अरहर दाल 1 किलो", (130, 190)),
    ("A4 paper ream", "A4 काग़ज़ रिम", (240, 380)),
    ("Ball pens (box of 10)", "बॉल पेन (10 का डिब्बा)", (60, 150)),
    ("LED tube light 20 W", "एलईडी ट्यूबलाइट 20 वाट", (180, 420)),
    ("Ceiling fan", "छत का पंखा", (1450, 3600)),
    ("Extension board", "एक्सटेंशन बोर्ड", (220, 650)),
    ("Steel water bottle", "स्टील की पानी की बोतल", (250, 690)),
    ("Cotton towel", "सूती तौलिया", (150, 450)),
    ("Paracetamol strip", "पैरासिटामोल पत्ता", (18, 45)),
    ("Wireless mouse", "वायरलेस माउस", (450, 1290)),
    ("USB cable", "यूएसबी केबल", (120, 390)),
    ("Notebook (200 pages)", "कॉपी (200 पेज)", (45, 120)),
    ("Tea leaves 500 g", "चायपत्ती 500 ग्राम", (190, 320)),
    ("Sugar 1 kg", "चीनी 1 किलो", (42, 52)),
    ("Detergent powder 2 kg", "डिटर्जेंट पाउडर 2 किलो", (210, 380)),
    ("Plastic chair", "प्लास्टिक की कुर्सी", (450, 950)),
    ("Paint brush set", "पेंट ब्रश सेट", (120, 340)),
    ("Catering - veg thali", "केटरिंग - शाकाहारी थाली", (120, 260)),
]

LAYOUTS = ["classic", "receipt", "modern", "split"]
FONTS_EN = ["Helvetica, Arial, sans-serif", "Georgia, serif", "'Times New Roman', serif", "Verdana, sans-serif",
            "'Avenir Next', Avenir, sans-serif", "'Gill Sans', sans-serif"]
FONTS_HI = ["'Kohinoor Devanagari'", "'ITF Devanagari'", "'Devanagari Sangam MN'", "'Devanagari MT'"]
MONO = "'Courier New', Courier, monospace"

L_EN = {"invoice": "TAX INVOICE", "receipt": "CASH RECEIPT", "no": "Invoice No.", "date": "Date", "item": "Description",
        "qty": "Qty", "rate": "Rate", "amount": "Amount", "subtotal": "Subtotal", "gst": "GST", "cgst": "CGST",
        "sgst": "SGST", "total": "Total", "thanks": "Thank you for your business!", "bill_to": "Bill to",
        "gstin": "GSTIN", "sr": "#"}
L_HI = {"invoice": "कर बीजक", "receipt": "नकद रसीद", "no": "बिल संख्या", "date": "दिनांक", "item": "विवरण",
        "qty": "मात्रा", "rate": "दर", "amount": "राशि", "subtotal": "उप-योग", "gst": "जीएसटी", "cgst": "सीजीएसटी",
        "sgst": "एसजीएसटी", "total": "कुल", "thanks": "धन्यवाद! फिर पधारें।", "bill_to": "ग्राहक",
        "gstin": "जीएसटीआईएन", "sr": "क्र."}
CUSTOMERS = [("Riya Sharma", "रिया शर्मा"), ("Aman Gupta", "अमन गुप्ता"), ("Sunita Yadav", "सुनीता यादव"),
             ("Rahul Verma", "राहुल वर्मा"), ("Kavya Iyer", "काव्या अय्यर"), ("Imran Khan", "इमरान ख़ान"),
             ("Neha Joshi", "नेहा जोशी"), ("Vikram Singh", "विक्रम सिंह")]


def q2(x) -> Decimal:
    return Decimal(x).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def num(d: Decimal):
    """Decimal -> JSON number (int when whole)."""
    return int(d) if d == d.to_integral_value() else float(d)


def _gstin(r) -> str:
    letters = "ABCDEFGHJKLMNPQRSTUVWXYZ"
    return "%02d%s%04d%s1Z%d" % (r.randint(1, 36), "".join(r.choice(letters) for _ in range(5)), r.randint(0, 9999),
                                 r.choice(letters), r.randint(1, 9))


def make_docs():
    """Return the list of document specs (pure data, deterministic)."""
    r = random.Random(SEED)
    base = []
    for i in range(N_EN):
        vendor = r.choice(VENDORS)
        city = r.choice(CITIES)
        cust = r.choice(CUSTOMERS)
        k = r.randint(2, 6)
        picks = r.sample(ITEMS, k)
        lines = []
        for it in picks:
            qty = r.randint(1, 12)
            rate = q2(r.randint(it[2][0], it[2][1]) + r.choice([0, 0, 0, 0.5, 0.25, 0.75, 0.9]))
            lines.append({"desc_en": it[0], "desc_hi": it[1], "qty": qty, "rate": rate, "amount": q2(rate * qty)})
        subtotal = sum((l["amount"] for l in lines), Decimal("0"))
        rate_pct = r.choice([5, 12, 18, 18, 28])
        half = q2(subtotal * Decimal(rate_pct) / Decimal(200))   # CGST = SGST = half of GST
        gst = half * 2
        total = subtotal + gst
        y, mo, d = r.choice([2025, 2026]), r.randint(1, 12), r.randint(1, 28)
        layout = LAYOUTS[i % len(LAYOUTS)]
        kind = "receipt" if layout == "receipt" else "invoice"
        inv_fmt = r.choice(["INV/%d/%04d" % (y, r.randint(1, 9999)), "GST-%05d" % r.randint(1, 99999),
                            "A-%04d" % r.randint(1000, 9999), "%s/%d-%02d/%03d" % (vendor[0][:2].upper(), y, (y + 1) % 100, r.randint(1, 999))])
        if kind == "receipt":
            inv_fmt = "R%06d" % r.randint(1, 999999)
        base.append({
            "i": i + 1, "vendor": vendor, "city": city, "customer": cust, "lines": lines, "subtotal": subtotal,
            "gst_rate": rate_pct, "cgst": half, "gst": gst, "total": total, "date": (y, mo, d),
            "invoice_number": inv_fmt, "layout": layout, "kind": kind, "gstin": _gstin(r),
            "date_style": r.randrange(4), "font_en": FONTS_EN[r.randrange(len(FONTS_EN))],
            "font_hi": FONTS_HI[r.randrange(len(FONTS_HI))],
            "noisy": (i % 5 == 3), "angle": round(r.uniform(1.2, 3.5) * r.choice([-1, 1]), 2),
            "noise_seed": r.randint(0, 10 ** 6), "bilingual": (i % 2 == 0),
        })
    docs = []
    for b in base:
        docs.append(dict(b, lang="en", doc_id="docs-synth-%04d-en" % b["i"]))
    for b in base[:N_HI]:
        docs.append(dict(b, lang="hi", doc_id="docs-synth-%04d-hi" % b["i"]))
    return docs


# ------------------------------------------------------------------ HTML

def _date_str(doc) -> str:
    y, mo, d = doc["date"]
    s = doc["date_style"]
    if doc["lang"] == "hi":
        return "%02d/%02d/%04d" % (d, mo, y) if s % 2 == 0 else "%d %s %d" % (d, MONTHS_HI[mo - 1], y)
    return ["%02d/%02d/%04d" % (d, mo, y), "%02d-%s-%04d" % (d, MONTHS_EN[mo - 1][:3], y),
            "%s %d, %d" % (MONTHS_EN[mo - 1], d, y), "%02d.%02d.%04d" % (d, mo, y)][s]


def _labels(doc):
    if doc["lang"] == "en":
        return dict(L_EN)
    if doc["bilingual"]:
        return {k: "%s <small>(%s)</small>" % (v, L_EN[k]) if k not in ("thanks", "sr") else v for k, v in L_HI.items()}
    return dict(L_HI)


def _money(d: Decimal) -> str:
    return fmt_inr(float(d), 2)


def _noise_layer(doc) -> str:
    r = random.Random(doc["noise_seed"])
    dots = []
    for _ in range(260):
        dots.append('<circle cx="%d" cy="%d" r="%.1f" fill="#000" fill-opacity="%.2f"/>' % (
            r.randint(0, W), r.randint(0, H), r.uniform(0.4, 1.6), r.uniform(0.15, 0.55)))
    stains = []
    for _ in range(3):
        stains.append('<ellipse cx="%d" cy="%d" rx="%d" ry="%d" fill="#8a6d3b" fill-opacity="0.07"/>' % (
            r.randint(0, W), r.randint(0, H), r.randint(60, 200), r.randint(40, 150)))
    return ('<svg class="noise" width="%d" height="%d" xmlns="http://www.w3.org/2000/svg">%s%s</svg>'
            % (W, H, "".join(stains), "".join(dots)))


CSS = """
@page { size: A4; margin: 12mm; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body { background: %(bg)s; font-family: %(font)s; color: #1d1d1f; }
.page { width: %(pw)dpx; margin: 24px auto; padding: 36px 40px; background: #fff; %(transform)s }
h1 { margin: 0 0 4px 0; font-size: 26px; }
.muted { color: #555; font-size: 14px; }
html:lang(hi) .title { letter-spacing: 0; }
.title { letter-spacing: 2px; font-weight: 700; font-size: 18px; margin: 18px 0 8px 0; }
table { width: 100%%; border-collapse: collapse; margin-top: 14px; font-size: 15px; }
th, td { padding: 7px 8px; text-align: left; }
td.n, th.n { text-align: right; }
.classic th { border-bottom: 2px solid #222; }
.classic td { border-bottom: 1px solid #ccc; }
.modern .band { background: %(accent)s; color: #fff; margin: -36px -40px 18px -40px; padding: 22px 40px; }
.modern .band .muted, .modern .band small { color: #eef; }
.modern th { background: #f0f2f5; }
.modern tr:nth-child(even) td { background: #fafbfc; }
.split table.grid td, .split table.grid th { border: 1px solid #999; }
.totals { margin-top: 14px; margin-left: auto; width: 55%%; font-size: 15px; }
.totals td { padding: 4px 8px; }
.totals tr.grand td { font-weight: 700; font-size: 18px; border-top: 2px solid #222; }
.receipt .page { font-family: %(mono)s; }
.receipt h1 { font-size: 20px; text-align: center; }
.receipt .center { text-align: center; }
.receipt table td, .receipt table th { padding: 3px 2px; font-size: 14px; }
.receipt hr { border: none; border-top: 1px dashed #333; }
.meta td { padding: 2px 0; font-size: 15px; }
small { font-size: 0.75em; color: #555; }
.noise { position: fixed; left: 0; top: 0; pointer-events: none; }
@media print { body { background: #fff; } .page { margin: 0 auto; transform: none; } .noise { display: none; } }
"""


def render_html(doc, noisy: bool) -> str:
    L = _labels(doc)
    hi = doc["lang"] == "hi"
    font = (doc["font_hi"] + ", " + doc["font_en"]) if hi else doc["font_en"]
    if hi and doc["layout"] == "receipt":
        font = doc["font_hi"] + ", " + MONO
    vend = doc["vendor"][1] if hi else doc["vendor"][0]
    if hi and doc["bilingual"]:
        vend_html = "%s<br><span class='muted'>%s</span>" % (html.escape(doc["vendor"][1]), html.escape(doc["vendor"][0]))
    else:
        vend_html = html.escape(vend)
    city = doc["city"][1] if hi else doc["city"][0]
    cust = doc["customer"][1] if hi else doc["customer"][0]
    receipt = doc["layout"] == "receipt"
    transform = ""
    bg = "#fff"
    if noisy:
        transform = "transform: rotate(%sdeg); transform-origin: 50%% 40%%; box-shadow: 0 0 18px rgba(0,0,0,.25);" % doc["angle"]
        bg = "#d9d4c7"
    css = CSS % {"bg": bg, "font": font, "pw": 520 if receipt else 820, "transform": transform,
                 "accent": ["#1f4e79", "#7a1f3d", "#2e6b3a", "#5a3d8a"][doc["i"] % 4], "mono": font if hi else MONO}
    rows = []
    for n, l in enumerate(doc["lines"], 1):
        desc = l["desc_hi"] if hi else l["desc_en"]
        if receipt:
            rows.append("<tr><td>%s<br>%d x %s</td><td class='n'>%s</td></tr>" % (
                html.escape(desc), l["qty"], _money(l["rate"]), _money(l["amount"])))
        else:
            rows.append("<tr><td>%d</td><td>%s</td><td class='n'>%d</td><td class='n'>%s</td><td class='n'>%s</td></tr>" % (
                n, html.escape(desc), l["qty"], _money(l["rate"]), _money(l["amount"])))
    if receipt:
        head = "<tr><th>%s</th><th class='n'>%s</th></tr>" % (L["item"], L["amount"])
    else:
        head = "<tr><th>%s</th><th>%s</th><th class='n'>%s</th><th class='n'>%s (₹)</th><th class='n'>%s (₹)</th></tr>" % (
            L["sr"], L["item"], L["qty"], L["rate"], L["amount"])
    if doc["layout"] in ("split", "receipt"):
        tax_rows = ("<tr><td>%s %s%%</td><td class='n'>%s</td></tr><tr><td>%s %s%%</td><td class='n'>%s</td></tr>" % (
            L["cgst"], _pct(doc["gst_rate"] / 2.0), _money(doc["cgst"]), L["sgst"], _pct(doc["gst_rate"] / 2.0), _money(doc["cgst"])))
    else:
        tax_rows = "<tr><td>%s %d%%</td><td class='n'>%s</td></tr>" % (L["gst"], doc["gst_rate"], _money(doc["gst"]))
    totals = ("<table class='totals'><tr><td>%s</td><td class='n'>%s</td></tr>%s"
              "<tr class='grand'><td>%s</td><td class='n'>₹ %s</td></tr></table>") % (
        L["subtotal"], _money(doc["subtotal"]), tax_rows, L["total"], _money(doc["total"]))
    title = L["receipt"] if receipt else L["invoice"]
    meta = ("<table class='meta'><tr><td><b>%s:</b> %s</td></tr><tr><td><b>%s:</b> %s</td></tr>"
            "<tr><td><b>%s:</b> %s</td></tr></table>") % (L["no"], html.escape(doc["invoice_number"]),
                                                           L["date"], _date_str(doc), L["bill_to"], html.escape(cust))
    hdr_info = "<div class='muted'>%s &middot; %s: %s</div>" % (html.escape(city), L["gstin"], doc["gstin"])
    if receipt:
        body = ("<div class='page'><h1>%s</h1><div class='center muted'>%s<br>%s: %s</div><hr>"
                "<div class='center title'>%s</div>%s<hr><table>%s%s</table><hr>%s<hr>"
                "<div class='center muted'>%s</div></div>") % (
            vend_html, html.escape(city), L["gstin"], doc["gstin"], title, meta, head, "".join(rows), totals, L["thanks"])
    elif doc["layout"] == "modern":
        body = ("<div class='page'><div class='band'><h1>%s</h1>%s</div><div class='title'>%s</div>%s"
                "<table>%s%s</table>%s<p class='muted'>%s</p></div>") % (
            vend_html, hdr_info, title, meta, head, "".join(rows), totals, L["thanks"])
    else:
        cls = "grid" if doc["layout"] == "split" else ""
        body = ("<div class='page'><h1>%s</h1>%s<div class='title'>%s</div>%s<table class='%s'>%s%s</table>%s"
                "<p class='muted'>%s</p></div>") % (
            vend_html, hdr_info, title, meta, cls, head, "".join(rows), totals, L["thanks"])
    noise = _noise_layer(doc) if noisy else ""
    return ("<!doctype html><html lang='%s'><head><meta charset='utf-8'><style>%s</style></head>"
            "<body class='%s'>%s%s</body></html>") % (doc["lang"], css, doc["layout"], body, noise)


def _pct(x: float) -> str:
    return ("%d" % x) if float(x).is_integer() else ("%.1f" % x)


# ------------------------------------------------------------------ rendering

def _chrome(args, tmp):
    cmd = [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
           "--no-default-browser-check", "--user-data-dir=" + tmp] + args
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return p.returncode


def render(doc, workdir):
    tmp = tempfile.mkdtemp(prefix="chrome-", dir=workdir)
    try:
        png = os.path.join(OUT, doc["doc_id"] + ".png")
        pdf = os.path.join(OUT, doc["doc_id"] + ".pdf")
        h_png = os.path.join(workdir, doc["doc_id"] + ".png.html")
        h_pdf = os.path.join(workdir, doc["doc_id"] + ".pdf.html")
        with open(h_png, "w", encoding="utf-8") as f:
            f.write(render_html(doc, doc["noisy"]))
        with open(h_pdf, "w", encoding="utf-8") as f:
            f.write(render_html(doc, False))
        _chrome(["--screenshot=" + png, "--window-size=%d,%d" % (W, H), "file://" + h_png], tmp)
        _chrome(["--print-to-pdf=" + pdf, "--no-pdf-header-footer", "--print-to-pdf-no-header", "file://" + h_pdf], tmp)
        ok = os.path.exists(png) and os.path.getsize(png) > 1000 and os.path.exists(pdf) and os.path.getsize(pdf) > 1000
        return doc["doc_id"], ok
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def manifest_row(doc) -> dict:
    y, mo, d = doc["date"]
    hi = doc["lang"] == "hi"
    vendor_accept = [doc["vendor"][0], doc["vendor"][1]]
    return {
        "doc_id": doc["doc_id"], "lang": doc["lang"], "layout": doc["layout"], "kind": doc["kind"],
        "font": doc["font_hi"] if hi else doc["font_en"], "bilingual": bool(hi and doc["bilingual"]),
        "variant": "rotated_noisy" if doc["noisy"] else "clean", "angle": doc["angle"] if doc["noisy"] else 0,
        "png": "data/docs-synth/%s.png" % doc["doc_id"], "pdf": "data/docs-synth/%s.pdf" % doc["doc_id"],
        "pair_doc": None if not hi else "docs-synth-%04d-en" % doc["i"],
        "date_shown": _date_str(doc),
        "fields": {
            "vendor": doc["vendor"][1] if hi else doc["vendor"][0],
            "invoice_number": doc["invoice_number"],
            "date": "%04d-%02d-%02d" % (y, mo, d),
            "subtotal": num(doc["subtotal"]),
            "gst": num(doc["gst"]),
            "total": num(doc["total"]),
        },
        "vendor_accept": vendor_accept,
        "gst_rate": doc["gst_rate"],
        "cgst": num(doc["cgst"]), "sgst": num(doc["cgst"]),
        "line_items": [{"description": l["desc_hi"] if hi else l["desc_en"], "qty": l["qty"],
                        "rate": num(l["rate"]), "amount": num(l["amount"])} for l in doc["lines"]],
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="render only the first N docs (smoke test)")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--manifest-only", action="store_true", help="rewrite manifest without rendering")
    args = ap.parse_args(argv)
    if not os.path.exists(CHROME) and not args.manifest_only:
        sys.exit("Chrome not found at %s (set CHROME=...)" % CHROME)
    os.makedirs(OUT, exist_ok=True)
    docs = make_docs()
    if args.limit:
        docs = docs[:args.limit]
    if not args.manifest_only:
        work = tempfile.mkdtemp(prefix="docs-synth-")
        try:
            with ThreadPoolExecutor(max_workers=args.workers) as ex:
                results = list(ex.map(lambda d: render(d, work), docs))
        finally:
            shutil.rmtree(work, ignore_errors=True)
        bad = [d for d, ok in results if not ok]
        if bad:
            sys.exit("render failed for: %s" % ", ".join(bad))
    with open(os.path.join(OUT, "manifest.jsonl"), "w", encoding="utf-8") as f:
        for d in docs:
            f.write(json.dumps(manifest_row(d), ensure_ascii=False) + "\n")
    total = sum(os.path.getsize(os.path.join(OUT, x)) for x in os.listdir(OUT))
    print("docs: %d  size: %.1f MB  -> %s" % (len(docs), total / 1e6, OUT))


if __name__ == "__main__":
    main()
