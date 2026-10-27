"""extract-pairs: JSON field extraction from short synthetic messages, in en / hi / hinglish.

Types: orders, contacts, appointments, invoices (20 each per language). One set of facts per
item, phrased in three languages. Expected fields are the facts used to write the text.
"""
from __future__ import annotations

from typing import Dict, List

from ..schema import Task
from ._common import CITIES, MONTHS_EN, MONTHS_HI, NAMES, VENDORS, fmt_inr, numval, rng_for

PACK = "extract-pairs"
PER_TYPE = 20

INTRO = {
    "en": "Extract the fields below from the message and reply with only a JSON object with these keys: %s.\n\nMessage: %s",
    "hi": "नीचे दिए गए संदेश से ये फ़ील्ड निकालें और केवल एक JSON object लिखें, जिसकी keys ये हों: %s।\n\nसंदेश: %s",
    "hinglish": "Neeche diye gaye message se ye fields nikalo aur sirf ek JSON object likho, jiski keys ye hon: %s.\n\nMessage: %s",
}

KEYDOC = {
    "number": {"en": "a number", "hi": "संख्या", "hinglish": "number"},
    "rupees": {"en": "a number in rupees, no ₹ sign or commas", "hi": "रुपये में संख्या, बिना ₹ चिह्न और कॉमा के",
               "hinglish": "rupaye mein number, bina ₹ sign aur comma ke"},
    "phone": {"en": "exactly 10 digits, no spaces, dashes or +91", "hi": "केवल 10 अंक, बिना स्पेस, डैश या +91 के",
              "hinglish": "sirf 10 digits, bina space, dash ya +91 ke"},
    "date": {"en": "YYYY-MM-DD", "hi": "YYYY-MM-DD", "hinglish": "YYYY-MM-DD"},
    "time": {"en": "24-hour HH:MM", "hi": "24-घंटे वाला HH:MM", "hinglish": "24-hour HH:MM"},
}

PRODUCTS = [  # en, hi, hinglish, unit price range
    ("steel water bottle", "स्टील की पानी की बोतल", "steel ki paani ki bottle", (249, 699)),
    ("cotton bedsheet", "सूती चादर", "cotton bedsheet", (399, 1299)),
    ("pressure cooker", "प्रेशर कुकर", "pressure cooker", (899, 2499)),
    ("school bag", "स्कूल बैग", "school bag", (499, 1499)),
    ("LED bulb", "एलईडी बल्ब", "LED bulb", (79, 249)),
    ("ceiling fan", "सीलिंग फ़ैन", "ceiling fan", (1499, 3999)),
    ("basmati rice bag (5 kg)", "बासमती चावल का बैग (5 किलो)", "basmati chawal ka bag (5 kilo)", (450, 899)),
    ("phone charger", "फ़ोन चार्जर", "phone charger", (299, 999)),
    ("yoga mat", "योगा मैट", "yoga mat", (349, 1199)),
    ("tiffin box", "टिफ़िन बॉक्स", "tiffin box", (199, 599)),
]

DOCTORS = [("Mehta", "मेहता"), ("Banerjee", "बनर्जी"), ("Qureshi", "क़ुरैशी"), ("Pillai", "पिल्लई"),
           ("Saxena", "सक्सेना"), ("Ghosh", "घोष"), ("Rathore", "राठौर"), ("Desai", "देसाई")]


def _keys(lang: str, keys) -> str:
    out = []
    for k, kind in keys:
        if kind:
            out.append("%s (%s)" % (k, KEYDOC[kind][lang]))
        else:
            out.append(k)
    return ", ".join(out)


def _names(nm):
    return [nm[0], nm[1]]


def _order(r, i):
    nm = r.choice(NAMES)
    prod = r.choice(PRODUCTS)
    q = r.randint(2, 9)
    price = r.randint(prod[3][0], prod[3][1])
    total = q * price
    oid = "ORD-%05d" % r.randint(10000, 99999)
    city = r.choice(CITIES)
    t = i % 2
    text = {}
    if t == 0:
        text["en"] = "Hi, my name is %s. Please confirm my order %s: %s, %d pieces, total ₹%s. Deliver to %s." % (
            nm[0], oid, prod[0], q, fmt_inr(total), city[0])
        text["hi"] = "नमस्ते, मेरा नाम %s है। कृपया मेरा ऑर्डर %s कन्फ़र्म करें: %s, %d नग, कुल ₹%s। डिलीवरी %s में चाहिए।" % (
            nm[1], oid, prod[1], q, fmt_inr(total), city[1])
        text["hinglish"] = "Hi, mera naam %s hai. Mera order %s confirm kar do: %s, %d piece, total ₹%s. Delivery %s mein chahiye." % (
            nm[0], oid, prod[2], q, fmt_inr(total), city[0])
    else:
        text["en"] = "Order %s placed by %s (%s). Items: %d x %s at ₹%s each. Order value ₹%s, cash on delivery." % (
            oid, nm[0], city[0], q, prod[0], fmt_inr(price), fmt_inr(total))
        text["hi"] = "ऑर्डर %s, ग्राहक: %s (%s)। सामान: %d x %s, ₹%s प्रति नग। ऑर्डर की कुल राशि ₹%s, कैश ऑन डिलीवरी।" % (
            oid, nm[1], city[1], q, prod[1], fmt_inr(price), fmt_inr(total))
        text["hinglish"] = "Order %s, customer: %s (%s). Saamaan: %d x %s, ₹%s per piece. Order ki total value ₹%s, cash on delivery." % (
            oid, nm[0], city[0], q, prod[2], fmt_inr(price), fmt_inr(total))
    keys = [("order_id", None), ("customer", None), ("quantity", "number"), ("total", "rupees")]
    fields = {"order_id": [oid], "customer": _names(nm), "quantity": [q], "total": [total]}
    ref = {"order_id": oid, "customer": nm[0], "quantity": q, "total": total}
    return "order", keys, text, fields, ref


def _phone_fmt(r, digits: str) -> str:
    v = r.randrange(4)
    if v == 0:
        return "+91 %s %s" % (digits[:5], digits[5:])
    if v == 1:
        return "%s-%s" % (digits[:5], digits[5:])
    if v == 2:
        return "0%s %s" % (digits[:5], digits[5:])
    return digits


def _contact(r, i):
    nm = r.choice(NAMES)
    city = r.choice(CITIES)
    digits = str(r.choice([6, 7, 8, 9])) + "".join(str(r.randrange(10)) for _ in range(9))
    phone = _phone_fmt(r, digits)
    fn, ln = nm[0].lower().split()
    email = r.choice(["%s.%s@example.com", "%s%s@example.in", "%s_%s@example.org"]) % (fn, ln)
    t = i % 2
    text = {}
    if t == 0:
        text["en"] = "New contact saved: %s from %s. Email: %s. Mobile: %s" % (nm[0], city[0], email, phone)
        text["hi"] = "नया संपर्क सेव हुआ: %s, %s से। ईमेल: %s। मोबाइल: %s" % (nm[1], city[1], email, phone)
        text["hinglish"] = "Naya contact save hua: %s, %s se. Email: %s. Mobile: %s" % (nm[0], city[0], email, phone)
    else:
        text["en"] = "Please call %s back on %s. Lives in %s; you can also write to %s if the call doesn't connect." % (
            nm[0], phone, city[0], email)
        text["hi"] = "कृपया %s को %s पर वापस कॉल करें। वे %s में रहते हैं; कॉल न लगे तो %s पर ईमेल भी कर सकते हैं।" % (
            nm[1], phone, city[1], email)
        if nm[2] == "f":
            text["hi"] = text["hi"].replace("वे %s में रहते हैं" % city[1], "वे %s में रहती हैं" % city[1])
        text["hinglish"] = "Please %s ko %s pe call back karo. Woh %s mein rehte hain; call na lage toh %s pe email bhi kar sakte ho." % (
            nm[0], phone, city[0], email)
        if nm[2] == "f":
            text["hinglish"] = text["hinglish"].replace("rehte hain", "rehti hain")
    keys = [("name", None), ("phone", "phone"), ("city", None), ("email", None)]
    fields = {"name": _names(nm), "phone": [digits], "city": [city[0], city[1]], "email": [email]}
    ref = {"name": nm[0], "phone": digits, "city": city[0], "email": email}
    return "contact", keys, text, fields, ref


def _period(h: int):
    if h < 12:
        return "AM", "सुबह", "subah"
    if h < 16:
        return "PM", "दोपहर", "dopahar"
    if h < 20:
        return "PM", "शाम", "shaam"
    return "PM", "रात", "raat"


def _appointment(r, i):
    nm = r.choice(NAMES)
    doc = r.choice(DOCTORS)
    y = r.choice([2025, 2026, 2027])
    mo = r.randint(1, 12)
    d = r.randint(1, 28)
    h = r.randint(8, 20)
    mi = r.choice([0, 15, 30, 45])
    h12 = h if h <= 12 else h - 12
    ampm, p_hi, p_hg = _period(h)
    iso = "%04d-%02d-%02d" % (y, mo, d)
    hm = "%02d:%02d" % (h, mi)
    t12 = "%d:%02d" % (h12, mi)
    t = i % 2
    text = {}
    if t == 0:
        text["en"] = "Dr. %s's clinic: %s is booked for %d %s %d at %s %s." % (doc[0], nm[0], d, MONTHS_EN[mo - 1], y, t12, ampm)
        text["hi"] = "डॉ. %s क्लिनिक: %s का अपॉइंटमेंट %d %s %d को %s %s बजे है।" % (doc[1], nm[1], d, MONTHS_HI[mo - 1], y, p_hi, t12)
        text["hinglish"] = "Dr. %s clinic: %s ka appointment %d %s %d ko %s %s baje hai." % (doc[0], nm[0], d, MONTHS_EN[mo - 1], y, p_hg, t12)
    else:
        text["en"] = "Reminder for %s: your visit with Dr. %s has been moved to %s %d, %d, %s %s. Please arrive 10 minutes early." % (
            nm[0], doc[0], MONTHS_EN[mo - 1], d, y, t12, ampm)
        text["hi"] = "%s के लिए सूचना: डॉ. %s के साथ आपका अपॉइंटमेंट अब %d %s %d को %s %s बजे है। कृपया 10 मिनट पहले पहुँचें।" % (
            nm[1], doc[1], d, MONTHS_HI[mo - 1], y, p_hi, t12)
        text["hinglish"] = "%s ke liye reminder: Dr. %s ke saath aapka appointment ab %d %s %d ko %s %s baje hai. Please 10 minute pehle pahunchein." % (
            nm[0], doc[0], d, MONTHS_EN[mo - 1], y, p_hg, t12)
    keys = [("name", None), ("date", "date"), ("time", "time")]
    fields = {"name": _names(nm), "date": [iso], "time": [hm]}
    ref = {"name": nm[0], "date": iso, "time": hm}
    return "appointment", keys, text, fields, ref


def _invoice(r, i):
    v = r.choice(VENDORS)
    inv = "INV-%04d" % r.randint(1000, 9999)
    y = r.choice([2025, 2026])
    mo = r.randint(1, 12)
    d = r.randint(1, 28)
    paise = r.choice([0, 0, 0, 50, 25, 75])
    amount = r.randint(800, 250000) + paise / 100.0
    dec = 2 if paise else 0
    amt_s = fmt_inr(amount, dec)
    dmy = "%02d/%02d/%04d" % (d, mo, y)
    iso = "%04d-%02d-%02d" % (y, mo, d)
    t = i % 2
    text = {}
    if t == 0:
        text["en"] = "Invoice %s from %s, dated %s. Amount payable: ₹%s (including GST)." % (inv, v[0], dmy, amt_s)
        text["hi"] = "%s का बिल नंबर %s, दिनांक %s। देय राशि: ₹%s (GST सहित)।" % (v[1], inv, dmy, amt_s)
        text["hinglish"] = "%s ka invoice %s, date %s. Payable amount: ₹%s (GST ke saath)." % (v[0], inv, dmy, amt_s)
    else:
        text["en"] = "Payment due: ₹%s to %s against invoice no. %s issued on %s. Please pay within 15 days." % (amt_s, v[0], inv, dmy)
        text["hi"] = "भुगतान बाकी: %s को ₹%s, बिल संख्या %s के लिए, जो %s को जारी हुआ था। कृपया 15 दिन के अंदर भुगतान करें।" % (
            v[1], amt_s, inv, dmy)
        text["hinglish"] = "Payment pending: %s ko ₹%s, invoice no. %s ke liye, jo %s ko issue hua tha. Please 15 din ke andar pay karo." % (
            v[0], amt_s, inv, dmy)
    keys = [("invoice_no", None), ("vendor", None), ("date", "date"), ("amount", "rupees")]
    amt = numval(amount)
    fields = {"invoice_no": [inv], "vendor": [v[0], v[1]], "date": [iso], "amount": [amt]}
    ref = {"invoice_no": inv, "vendor": v[0], "date": iso, "amount": amt}
    return "invoice", keys, text, fields, ref


GENERATORS = [_order, _contact, _appointment, _invoice]


def build() -> List[Task]:
    r = rng_for(PACK)
    tasks: List[Task] = []
    idx = 0
    for gen in GENERATORS:
        for i in range(PER_TYPE):
            idx += 1
            subtype, keys, text, fields, ref = gen(r, i)
            en_id = "%s-%04d-en" % (PACK, idx)
            for lang in ("en", "hi", "hinglish"):
                prompt = INTRO[lang] % (_keys(lang, keys), text[lang])
                tasks.append(Task(
                    id="%s-%04d-%s" % (PACK, idx, lang), pack=PACK, category="extraction", lang=lang,
                    modality="text", prompt=prompt, reference=dict(ref),
                    scorer={"type": "json_fields", "fields": {k: list(v) for k, v in fields.items()},
                            "numeric_tol": 0.01},
                    pair_id=None if lang == "en" else en_id,
                    meta={"group": en_id, "subtype": subtype, "source_text": text[lang]},
                ))
    return tasks
