"""math-pairs: programmatic word problems with exact answers, in en / hi / hinglish.

Every item is generated once from shared numbers and then phrased in three languages, so the
only difference between the members of a pair is the language. Answers are computed in code.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from ..schema import Task
from ._common import DAYS_EN, DAYS_HI, DAYS_ROMAN, NAMES, first, rng_for

PACK = "math-pairs"
PER_TYPE = 20  # 6 types x 20 = 120 per language

ONLY_NUM = {"en": "Reply with only the number.", "hi": "केवल संख्या लिखें।", "hinglish": "Sirf number likho."}

# en phrase, hi phrase, hinglish phrase, (min price, max price, step)
ITEMS = [
    ("{q} notebooks at ₹{p} each", "{q} कॉपी (₹{p} प्रति कॉपी)", "{q} copy (₹{p} per copy)", (25, 90, 5)),
    ("{q} pens at ₹{p} each", "{q} पेन (₹{p} प्रति पेन)", "{q} pen (₹{p} per pen)", (5, 40, 1)),
    ("{q} kg of rice at ₹{p} per kg", "{q} किलो चावल (₹{p} प्रति किलो)", "{q} kilo chawal (₹{p} per kilo)", (40, 120, 2)),
    ("{q} litres of milk at ₹{p} per litre", "{q} लीटर दूध (₹{p} प्रति लीटर)", "{q} litre doodh (₹{p} per litre)", (50, 70, 1)),
    ("{q} dozen bananas at ₹{p} per dozen", "{q} दर्जन केले (₹{p} प्रति दर्जन)", "{q} darjan kele (₹{p} per darjan)", (40, 90, 5)),
    ("{q} packets of biscuits at ₹{p} per packet", "{q} पैकेट बिस्कुट (₹{p} प्रति पैकेट)", "{q} packet biscuit (₹{p} per packet)", (10, 45, 5)),
    ("{q} bars of soap at ₹{p} each", "{q} साबुन (₹{p} प्रति साबुन)", "{q} sabun (₹{p} per sabun)", (20, 60, 2)),
    ("{q} kg of sugar at ₹{p} per kg", "{q} किलो चीनी (₹{p} प्रति किलो)", "{q} kilo cheeni (₹{p} per kilo)", (40, 50, 1)),
    ("{q} T-shirts at ₹{p} each", "{q} टी-शर्ट (₹{p} प्रति टी-शर्ट)", "{q} T-shirt (₹{p} per T-shirt)", (199, 499, 50)),
    ("{q} kg of tomatoes at ₹{p} per kg", "{q} किलो टमाटर (₹{p} प्रति किलो)", "{q} kilo tamatar (₹{p} per kilo)", (20, 60, 4)),
]


def _join(parts: List[str], lang: str) -> str:
    conj = {"en": "and", "hi": "और", "hinglish": "aur"}[lang]
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + " " + conj + " " + parts[-1]


def _shopping(r, i) -> Tuple[str, Dict[str, Tuple[str, object, dict]]]:
    nm = r.choice(NAMES)
    en_name, hi_name = first(nm[0]), first(nm[1])
    k = r.choice([2, 2, 3])
    items = r.sample(ITEMS, k)
    parts = {"en": [], "hi": [], "hinglish": []}
    total = 0
    for it in items:
        q = r.randint(2, 6)
        lo, hi, step = it[3]
        p = r.randrange(lo, hi + 1, step)
        total += q * p
        parts["en"].append(it[0].format(q=q, p=p))
        parts["hi"].append(it[1].format(q=q, p=p))
        parts["hinglish"].append(it[2].format(q=q, p=p))
    variant = i % 3  # 0 total, 1 change from a note, 2 discount
    out = {}
    if variant == 0:
        ans = total
        out["en"] = "%s buys %s. How much does %s pay in total, in rupees? %s" % (
            en_name, _join(parts["en"], "en"), en_name, ONLY_NUM["en"])
        out["hi"] = "%s ने %s ख़रीदे। उसे कुल कितने रुपये देने होंगे? %s" % (
            hi_name, _join(parts["hi"], "hi"), ONLY_NUM["hi"])
        out["hinglish"] = "%s ne %s kharide. Total kitne rupaye dene honge? %s" % (
            en_name, _join(parts["hinglish"], "hinglish"), ONLY_NUM["hinglish"])
    elif variant == 1:
        note = next(n for n in (500, 1000, 2000, 5000) if n > total)
        ans = note - total
        out["en"] = "%s buys %s and pays with a ₹%d note. How much change, in rupees, should %s get back? %s" % (
            en_name, _join(parts["en"], "en"), note, en_name, ONLY_NUM["en"])
        out["hi"] = "%s ने %s ख़रीदे और ₹%d का नोट दिया। उसे कितने रुपये वापस मिलने चाहिए? %s" % (
            hi_name, _join(parts["hi"], "hi"), note, ONLY_NUM["hi"])
        out["hinglish"] = "%s ne %s kharide aur ₹%d ka note diya. Kitne rupaye wapas milne chahiye? %s" % (
            en_name, _join(parts["hinglish"], "hinglish"), note, ONLY_NUM["hinglish"])
    else:
        disc = next((d for d in (10, 20, 5, 25) if (total * d) % 100 == 0), None)
        if disc is None:  # make the bill divisible: add one more cheap item until a discount is integral
            disc = 10
        ans = round(total * (100 - disc) / 100.0, 2)
        out["en"] = "%s buys %s. The shop gives a %d%% discount on the whole bill. How much does %s pay, in rupees? %s" % (
            en_name, _join(parts["en"], "en"), disc, en_name, ONLY_NUM["en"])
        out["hi"] = "%s ने %s ख़रीदे। दुकानदार ने पूरे बिल पर %d%% की छूट दी। उसे कितने रुपये देने होंगे? %s" % (
            hi_name, _join(parts["hi"], "hi"), disc, ONLY_NUM["hi"])
        out["hinglish"] = "%s ne %s kharide. Dukaandaar ne poore bill pe %d%% discount diya. Kitne rupaye dene honge? %s" % (
            en_name, _join(parts["hinglish"], "hinglish"), disc, ONLY_NUM["hinglish"])
    return "shopping", {L: (p, ans, {"type": "number", "value": ans}) for L, p in out.items()}


def _percent(r, i):
    v = i % 4
    out = {}
    if v == 0:
        p = r.randrange(5, 95, 5)
        y = r.randrange(20, 5000, 20)
        ans = p * y / 100.0
        out["en"] = "What is %d%% of %d? %s" % (p, y, ONLY_NUM["en"])
        out["hi"] = "%d का %d%% कितना होता है? %s" % (y, p, ONLY_NUM["hi"])
        out["hinglish"] = "%d ka %d%% kitna hota hai? %s" % (y, p, ONLY_NUM["hinglish"])
    elif v in (1, 2):
        price = r.randrange(500, 50000, 100)
        p = r.choice([5, 8, 10, 12, 15, 18, 20, 25, 30, 40])
        up = v == 1
        ans = price * (100 + p) / 100.0 if up else price * (100 - p) / 100.0
        if up:
            out["en"] = "A phone costs ₹%d. Its price goes up by %d%%. What is the new price in rupees? %s" % (price, p, ONLY_NUM["en"])
            out["hi"] = "एक फ़ोन की क़ीमत ₹%d है। उसकी क़ीमत %d%% बढ़ जाती है। नई क़ीमत कितने रुपये होगी? %s" % (price, p, ONLY_NUM["hi"])
            out["hinglish"] = "Ek phone ki keemat ₹%d hai. Uski keemat %d%% badh jaati hai. Nayi keemat kitne rupaye hogi? %s" % (price, p, ONLY_NUM["hinglish"])
        else:
            out["en"] = "A fridge costs ₹%d. It is on sale at %d%% off. What is the sale price in rupees? %s" % (price, p, ONLY_NUM["en"])
            out["hi"] = "एक फ़्रिज की क़ीमत ₹%d है। सेल में उस पर %d%% की छूट है। सेल में उसकी क़ीमत कितने रुपये होगी? %s" % (price, p, ONLY_NUM["hi"])
            out["hinglish"] = "Ek fridge ki keemat ₹%d hai. Sale mein us par %d%% off hai. Sale price kitne rupaye hogi? %s" % (price, p, ONLY_NUM["hinglish"])
    else:
        while True:
            b = r.choice([20, 25, 40, 50, 80, 120, 150, 200])
            a = r.randint(1, b - 1)
            if (a * 100) % b == 0:
                break
        ans = a * 100 / b
        out["en"] = "A student scored %d marks out of %d. What percentage is that? %s" % (a, b, ONLY_NUM["en"])
        out["hi"] = "एक छात्र को %d में से %d अंक मिले। यह कितने प्रतिशत हुआ? %s" % (b, a, ONLY_NUM["hi"])
        out["hinglish"] = "Ek student ko %d mein se %d marks mile. Yeh kitne percent hua? %s" % (b, a, ONLY_NUM["hinglish"])
    return "percentage", {L: (q, ans, {"type": "number", "value": ans}) for L, q in out.items()}


def _hhmm(m: int) -> str:
    return "%02d:%02d" % (m // 60, m % 60)


def _time(r, i):
    out = {}
    if i % 2 == 0:
        start = r.randrange(5 * 60, 14 * 60, 5)
        dur = r.randrange(35, 8 * 60, 5)
        end = start + dur
        h, m = divmod(dur, 60)
        ans = _hhmm(end)
        accepted = [ans]
        if ans.startswith("0"):
            accepted.append(ans[1:])
        fmt = {"en": "Reply with only the time in 24-hour HH:MM format.",
               "hi": "जवाब केवल 24-घंटे वाले HH:MM फ़ॉर्मेट में लिखें।",
               "hinglish": "Sirf 24-hour HH:MM format mein time likho."}
        dur_en = ("%d hours %d minutes" % (h, m)) if h else ("%d minutes" % m)
        dur_hi = ("%d घंटे %d मिनट" % (h, m)) if h else ("%d मिनट" % m)
        dur_hg = ("%d ghante %d minute" % (h, m)) if h else ("%d minute" % m)
        if h == 1:
            dur_en = dur_en.replace("1 hours", "1 hour")
        out["en"] = "A bus leaves at %s and the journey takes %s. At what time does it arrive? %s" % (_hhmm(start), dur_en, fmt["en"])
        out["hi"] = "एक बस %s बजे चलती है और सफ़र में %s लगते हैं। बस कितने बजे पहुँचेगी? %s" % (_hhmm(start), dur_hi, fmt["hi"])
        out["hinglish"] = "Ek bus %s baje chalti hai aur safar mein %s lagte hain. Bus kitne baje pahunchegi? %s" % (_hhmm(start), dur_hg, fmt["hinglish"])
        spec = {"type": "one_of", "values": accepted}
        return "time", {L: (q, ans, spec) for L, q in out.items()}
    start = r.randrange(6 * 60, 13 * 60, 5)
    dur = r.randrange(25, 9 * 60, 5)
    end = start + dur
    out["en"] = "A meeting started at %s and ended at %s. How many minutes did it last? %s" % (_hhmm(start), _hhmm(end), ONLY_NUM["en"])
    out["hi"] = "एक मीटिंग %s बजे शुरू होकर %s बजे ख़त्म हुई। मीटिंग कितने मिनट चली? %s" % (_hhmm(start), _hhmm(end), ONLY_NUM["hi"])
    out["hinglish"] = "Ek meeting %s baje shuru hokar %s baje khatam hui. Meeting kitne minute chali? %s" % (_hhmm(start), _hhmm(end), ONLY_NUM["hinglish"])
    return "time", {L: (q, dur, {"type": "number", "value": dur}) for L, q in out.items()}


# (from en, to en, from hi, to hi, from hinglish, to hinglish, factor)
UNITS = [
    ("kilometres", "metres", "किलोमीटर", "मीटर", "kilometre", "metre", 1000),
    ("kilograms", "grams", "किलोग्राम", "ग्राम", "kilogram", "gram", 1000),
    ("litres", "millilitres", "लीटर", "मिलीलीटर", "litre", "millilitre", 1000),
    ("hours", "minutes", "घंटे", "मिनट", "ghante", "minute", 60),
    ("metres", "centimetres", "मीटर", "सेंटीमीटर", "metre", "centimetre", 100),
    ("minutes", "seconds", "मिनट", "सेकंड", "minute", "second", 60),
    ("days", "hours", "दिन", "घंटे", "din", "ghante", 24),
    ("tonnes", "kilograms", "टन", "किलोग्राम", "ton", "kilogram", 1000),
]


def _units(r, i):
    u = UNITS[i % len(UNITS)]
    if r.random() < 0.5:
        x = r.randint(2, 40) + 0.5
        xs = "%.1f" % x
    else:
        x = r.randint(2, 75)
        xs = str(x)
    ans = x * u[6]
    out = {}
    if (i // len(UNITS)) % 2 == 0:
        out["en"] = "How many %s are there in %s %s? %s" % (u[1], xs, u[0], ONLY_NUM["en"])
        out["hi"] = "%s %s में कितने %s होते हैं? %s" % (xs, u[2], u[3], ONLY_NUM["hi"])
        out["hinglish"] = "%s %s mein kitne %s hote hain? %s" % (xs, u[4], u[5], ONLY_NUM["hinglish"])
    else:
        out["en"] = "Convert %s %s to %s. %s" % (xs, u[0], u[1], ONLY_NUM["en"])
        out["hi"] = "%s %s को %s में बदलें। %s" % (xs, u[2], u[3], ONLY_NUM["hi"])
        out["hinglish"] = "%s %s ko %s mein convert karo. %s" % (xs, u[4], u[5], ONLY_NUM["hinglish"])
    return "units", {L: (q, ans, {"type": "number", "value": ans}) for L, q in out.items()}


def _weekday(r, i):
    d = r.randrange(7)
    k = r.randint(9, 400)
    after = i % 3 != 2
    t = (d + k) % 7 if after else (d - k) % 7
    accepted = [DAYS_EN[t], DAYS_HI[t]] + DAYS_ROMAN[t]
    out = {}
    if after:
        out["en"] = "If today is %s, what day of the week will it be %d days from now? Reply with only the day name." % (DAYS_EN[d], k)
        out["hi"] = "अगर आज %s है, तो %d दिन बाद कौन-सा दिन होगा? केवल दिन का नाम लिखें।" % (DAYS_HI[d], k)
        out["hinglish"] = "Agar aaj %s hai, toh %d din baad kaunsa din hoga? Sirf din ka naam likho." % (DAYS_EN[d], k)
    else:
        out["en"] = "If today is %s, what day of the week was it %d days ago? Reply with only the day name." % (DAYS_EN[d], k)
        out["hi"] = "अगर आज %s है, तो %d दिन पहले कौन-सा दिन था? केवल दिन का नाम लिखें।" % (DAYS_HI[d], k)
        out["hinglish"] = "Agar aaj %s hai, toh %d din pehle kaunsa din tha? Sirf din ka naam likho." % (DAYS_EN[d], k)
    refs = {"en": DAYS_EN[t], "hi": DAYS_HI[t], "hinglish": DAYS_EN[t]}
    spec = {"type": "one_of", "values": accepted}
    return "weekday", {L: (q, refs[L], spec) for L, q in out.items()}


def _interest(r, i):
    p = r.randrange(1000, 100000, 500)
    rate = r.choice([4, 5, 6, 7, 8, 9, 10, 12])
    t = r.randint(2, 6)
    interest = p * rate * t / 100.0
    total = i % 2 == 1
    ans = p + interest if total else interest
    out = {}
    if not total:
        out["en"] = "What is the simple interest on ₹%d at %d%% per year for %d years, in rupees? %s" % (p, rate, t, ONLY_NUM["en"])
        out["hi"] = "₹%d पर %d%% सालाना साधारण ब्याज की दर से %d साल का ब्याज कितने रुपये होगा? %s" % (p, rate, t, ONLY_NUM["hi"])
        out["hinglish"] = "₹%d par %d%% saalana simple interest se %d saal ka byaaj kitne rupaye hoga? %s" % (p, rate, t, ONLY_NUM["hinglish"])
    else:
        out["en"] = "₹%d is invested at %d%% per year simple interest for %d years. What is the total amount (principal plus interest) at the end, in rupees? %s" % (p, rate, t, ONLY_NUM["en"])
        out["hi"] = "₹%d को %d%% सालाना साधारण ब्याज पर %d साल के लिए जमा किया गया। अंत में कुल राशि (मूलधन + ब्याज) कितने रुपये होगी? %s" % (p, rate, t, ONLY_NUM["hi"])
        out["hinglish"] = "₹%d ko %d%% saalana simple interest par %d saal ke liye jama kiya. End mein total amount (principal + byaaj) kitne rupaye hoga? %s" % (p, rate, t, ONLY_NUM["hinglish"])
    return "simple_interest", {L: (q, ans, {"type": "number", "value": ans}) for L, q in out.items()}


GENERATORS = [_shopping, _percent, _time, _units, _weekday, _interest]


def _clean(v):
    if isinstance(v, float) and v.is_integer():
        return int(v)
    return v


def build() -> List[Task]:
    r = rng_for(PACK)
    tasks: List[Task] = []
    idx = 0
    for gen in GENERATORS:
        for i in range(PER_TYPE):
            idx += 1
            subtype, by_lang = gen(r, i)
            en_id = "%s-%04d-en" % (PACK, idx)
            for lang in ("en", "hi", "hinglish"):
                prompt, ans, spec = by_lang[lang]
                spec = dict(spec)
                if "value" in spec:
                    spec["value"] = _clean(spec["value"])
                tasks.append(Task(
                    id="%s-%04d-%s" % (PACK, idx, lang), pack=PACK, category="math", lang=lang,
                    modality="text", prompt=prompt, reference=_clean(ans), scorer=spec,
                    pair_id=None if lang == "en" else en_id,
                    meta={"group": en_id, "subtype": subtype},
                ))
    return tasks
