"""Build data/audio-synth/: spoken English / Hindi / Hinglish clips with known answers.

Uses macOS `say` (voices Tara, Rishi: en_IN; Lekha: hi_IN) and `afconvert` to write 16 kHz mono
WAV files, plus manifest.jsonl with the transcript and the answer for every clip. All content
is invented. Re-running gives the same clips (fixed seed).

    PYTHONPATH=. python3 scripts/build_audio.py
"""
from __future__ import annotations

import json
import os
import random
import subprocess
import sys
import tempfile

from upgrade_gate.packs._common import CITIES, NAMES

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "audio-synth")
SEED = 20261027
LANGS = ("en", "hi", "hinglish")
INTENT_LABELS = ["address_change", "cancel_order", "delivery_status", "payment_failed", "refund_request"]


def spaced(digits: str) -> str:
    return " ".join(digits)


# ---------------------------------------------------------------- math: (en, hi, hinglish, answer)

def math_items(rng: random.Random):
    items = []
    for _ in range(3):
        qty, rate = rng.randint(2, 6), rng.choice([42, 56, 64, 75, 88])
        note = 500 if qty * rate < 500 else 1000
        n = rng.choice(NAMES)
        items.append(dict(
            en="%s bought %d kilos of rice at %d rupees per kilo and paid with a %d rupee note. "
               "How much change should %s get back?" % (n[0].split()[0], qty, rate, note, n[0].split()[0]),
            hi="%s ने %d रुपये प्रति किलो के भाव से %d किलो चावल ख़रीदे और %d रुपये का नोट दिया। "
               "%s को कितने रुपये वापस मिलने चाहिए?" % (n[1].split()[0], rate, qty, note, n[1].split()[0]),
            hinglish="%s ne %d rupaye kilo ke bhaav se %d kilo chawal kharide aur %d rupaye ka note diya. "
                     "%s ko kitne rupaye wapas milne chahiye?" % (n[0].split()[0], rate, qty, note, n[0].split()[0]),
            answer=note - qty * rate))
    for _ in range(3):
        trips, kids, days = rng.randint(2, 5), rng.randint(21, 48), rng.randint(3, 7)
        items.append(dict(
            en="A school bus makes %d trips a day and carries %d children on each trip. "
               "How many children does it carry in %d days?" % (trips, kids, days),
            hi="एक स्कूल बस दिन में %d चक्कर लगाती है और हर चक्कर में %d बच्चे ले जाती है। "
               "%d दिनों में वह कुल कितने बच्चे ले जाती है?" % (trips, kids, days),
            hinglish="Ek school bus din mein %d chakkar lagati hai aur har chakkar mein %d bachche le jaati hai. "
                     "%d dinon mein woh kul kitne bachche le jaati hai?" % (trips, kids, days),
            answer=trips * kids * days))
    for _ in range(3):
        have, a, b = rng.randint(200, 480), rng.randint(35, 95), rng.randint(20, 60)
        n = rng.choice(NAMES)
        items.append(dict(
            en="%s had %d rupees, spent %d rupees on lunch and %d rupees on a bus ticket. "
               "How many rupees are left?" % (n[0].split()[0], have, a, b),
            hi="%s के पास %d रुपये थे। %d रुपये खाने पर और %d रुपये बस टिकट पर ख़र्च हुए। "
               "अब कितने रुपये बचे हैं?" % (n[1].split()[0], have, a, b),
            hinglish="%s ke paas %d rupaye the. %d rupaye khaane par aur %d rupaye bus ticket par kharch hue. "
                     "Ab kitne rupaye bache hain?" % (n[0].split()[0], have, a, b),
            answer=have - a - b))
    for _ in range(3):
        price, pct = rng.choice([400, 600, 800, 1200, 1500, 2000]), rng.choice([10, 20, 25, 50])
        items.append(dict(
            en="A shirt costs %d rupees and there is a %d percent discount. "
               "What is the price after the discount?" % (price, pct),
            hi="एक कमीज़ की क़ीमत %d रुपये है और उस पर %d प्रतिशत की छूट है। "
               "छूट के बाद क़ीमत कितनी होगी?" % (price, pct),
            hinglish="Ek shirt ki keemat %d rupaye hai aur us par %d percent ki chhoot hai. "
                     "Chhoot ke baad keemat kitni hogi?" % (price, pct),
            answer=price * (100 - pct) // 100))
    for _ in range(3):
        rate, mins = rng.choice([25, 40, 50, 75, 80]), rng.randint(8, 24)
        litres = rate * mins
        items.append(dict(
            en="A water tank holds %d litres. It fills at %d litres per minute. "
               "How many minutes does it take to fill completely?" % (litres, rate),
            hi="एक टंकी में %d लीटर पानी आता है। वह हर मिनट %d लीटर की रफ़्तार से भरती है। "
               "टंकी को पूरा भरने में कितने मिनट लगेंगे?" % (litres, rate),
            hinglish="Ek tanki mein %d litre paani aata hai. Woh har minute %d litre ki raftaar se bharti hai. "
                     "Tanki ko poora bharne mein kitne minute lagenge?" % (litres, rate),
            answer=mins))
    return items


# ---------------------------------------------------------------- voice-note extraction

def extract_items(rng: random.Random):
    items = []
    for _ in range(15):
        n, c = rng.choice(NAMES), rng.choice(CITIES)
        order, pin = str(rng.randint(10000, 99999)), str(rng.randint(110000, 859999))
        bol = "rahi" if n[2] == "f" else "raha"
        bol_hi = "रही" if n[2] == "f" else "रहा"
        items.append(dict(
            en="Hello, this is %s calling from %s. My order number is %s. My pincode is %s. "
               "Please call me back." % (n[0], c[0], spaced(order), spaced(pin)),
            hi="नमस्ते, मैं %s %s से बोल %s हूँ। मेरा ऑर्डर नंबर %s है। मेरा पिनकोड %s है। "
               "कृपया मुझे वापस कॉल करें।" % (n[1], c[1], bol_hi, spaced(order), spaced(pin)),
            hinglish="Hello, main %s %s se bol %s hoon. Mera order number %s hai. Mera pincode %s hai. "
                     "Please mujhe call back kijiye." % (n[0], c[0], bol, spaced(order), spaced(pin)),
            answer={"order_number": order, "pincode": pin, "city": [c[0], c[1]]}, gender=n[2]))
    return items


# ---------------------------------------------------------------- voice-note intent

INTENTS = {
    "refund_request": [
        ("I returned the shoes from order {o} last week, but the money has not come back to my account yet. I want my refund.",
         "मैंने पिछले हफ़्ते ऑर्डर {o} के जूते वापस कर दिए थे, लेकिन पैसे अभी तक मेरे खाते में नहीं आए। मुझे मेरा रिफ़ंड चाहिए।",
         "Maine pichhle hafte order {o} ke joote wapas kar diye the, lekin paise abhi tak mere account mein nahi aaye. Mujhe mera refund chahiye."),
        ("The mixer I got in order {o} was broken, so I sent it back. Please return my money.",
         "ऑर्डर {o} में आया मिक्सर टूटा हुआ था, इसलिए मैंने उसे वापस भेज दिया। कृपया मेरे पैसे लौटा दीजिए।",
         "Order {o} mein aaya mixer toota hua tha, isliye maine use wapas bhej diya. Please mere paise lauta dijiye."),
        ("I sent back everything from order {o}. When will I get the amount back?",
         "मैंने ऑर्डर {o} का सारा सामान लौटा दिया है। मेरी रक़म वापस कब मिलेगी?",
         "Maine order {o} ka saara saamaan lauta diya hai. Meri rakam wapas kab milegi?"),
    ],
    "delivery_status": [
        ("Where is my order {o}? It was supposed to arrive yesterday and I have no update.",
         "मेरा ऑर्डर {o} कहाँ है? उसे कल आना था और अभी तक कोई ख़बर नहीं है।",
         "Mera order {o} kahan hai? Use kal aana tha aur abhi tak koi update nahi hai."),
        ("Can you tell me when order {o} will be delivered? The tracking page is not changing.",
         "क्या आप बता सकते हैं कि ऑर्डर {o} कब डिलीवर होगा? ट्रैकिंग पेज पर कुछ नहीं बदल रहा।",
         "Kya aap bata sakte hain ki order {o} kab deliver hoga? Tracking page par kuch change nahi ho raha."),
        ("My parcel for order {o} is late. Has it left the warehouse yet?",
         "ऑर्डर {o} का मेरा पार्सल देर से आ रहा है। क्या वह गोदाम से निकल चुका है?",
         "Order {o} ka mera parcel late ho gaya hai. Kya woh warehouse se nikal chuka hai?"),
    ],
    "cancel_order": [
        ("I placed order {o} by mistake. Please cancel it before it ships.",
         "मैंने ग़लती से ऑर्डर {o} कर दिया। कृपया भेजने से पहले इसे रद्द कर दीजिए।",
         "Maine galti se order {o} place kar diya. Please ship hone se pehle ise cancel kar dijiye."),
        ("I don't want order {o} anymore. Please stop it, I don't need it.",
         "मुझे अब ऑर्डर {o} नहीं चाहिए। कृपया इसे रोक दीजिए।",
         "Mujhe ab order {o} nahi chahiye. Please ise rok dijiye."),
        ("Please cancel order {o}, I found it cheaper in a local shop.",
         "कृपया ऑर्डर {o} रद्द कर दीजिए, मुझे यह पास की दुकान में सस्ता मिल गया।",
         "Please order {o} cancel kar dijiye, mujhe yeh paas ki dukaan mein sasta mil gaya."),
    ],
    "address_change": [
        ("For order {o}, I have moved house. Please deliver it to my new address instead.",
         "ऑर्डर {o} के लिए बता दूँ, मैंने घर बदल लिया है। कृपया इसे मेरे नए पते पर भेजिए।",
         "Order {o} ke liye bata doon, maine ghar badal liya hai. Please ise mere naye address par bhejiye."),
        ("I entered the wrong flat number for order {o}. Can you update the delivery address?",
         "ऑर्डर {o} में मैंने ग़लत फ़्लैट नंबर डाल दिया। क्या आप डिलीवरी का पता बदल सकते हैं?",
         "Order {o} mein maine galat flat number daal diya. Kya aap delivery address update kar sakte hain?"),
        ("Please send order {o} to my office address, not my home.",
         "कृपया ऑर्डर {o} मेरे घर के बजाय मेरे दफ़्तर के पते पर भेजिए।",
         "Please order {o} mere ghar ki jagah mere office ke address par bhejiye."),
    ],
    "payment_failed": [
        ("My card payment for order {o} keeps failing. I tried three times and it shows an error every time.",
         "ऑर्डर {o} के लिए मेरा कार्ड पेमेंट बार-बार फ़ेल हो रहा है। मैंने तीन बार कोशिश की, हर बार एरर आता है।",
         "Order {o} ke liye mera card payment baar baar fail ho raha hai. Maine teen baar try kiya, har baar error aata hai."),
        ("I cannot complete the payment for order {o}. The UPI screen just closes and the order stays unpaid.",
         "मैं ऑर्डर {o} का पेमेंट पूरा नहीं कर पा रहा। UPI स्क्रीन बंद हो जाती है और ऑर्डर का भुगतान नहीं होता।",
         "Main order {o} ka payment complete nahi kar pa raha. UPI screen band ho jaati hai aur order unpaid reh jaata hai."),
        ("The payment page for order {o} gives an error every time I press pay.",
         "ऑर्डर {o} का पेमेंट पेज हर बार पे दबाने पर एरर देता है।",
         "Order {o} ka payment page har baar pay dabane par error deta hai."),
    ],
}


def intent_items(rng: random.Random):
    items = []
    for label in INTENT_LABELS:
        for en, hi, hl in INTENTS[label]:
            o = spaced(str(rng.randint(10000, 99999)))
            items.append(dict(en=en.format(o=o), hi=hi.format(o=o), hinglish=hl.format(o=o), answer=label))
    return items


# ---------------------------------------------------------------- speech

def voice(lang: str, gender: str) -> str:
    if lang == "hi":
        return "Lekha"
    return "Rishi" if gender == "m" else "Tara"


def speak(text: str, v: str, path: str) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        aiff = os.path.join(tmp, "x.aiff")
        subprocess.run(["say", "-v", v, "-r", "170", "-o", aiff, text], check=True)
        subprocess.run(["afconvert", "-f", "WAVE", "-d", "LEI16@16000", "-c", "1", aiff, path], check=True)


def main() -> None:
    if sys.platform != "darwin":
        sys.exit("needs macOS `say` and `afconvert`")
    rng = random.Random(SEED)
    os.makedirs(OUT, exist_ok=True)
    kinds = [("math", math_items(rng)), ("extract", extract_items(rng)), ("intent", intent_items(rng))]
    rows = []
    for kind, items in kinds:
        for i, it in enumerate(items):
            gender = it.get("gender") or rng.choice("mf")
            for lang in LANGS:
                cid = "audio-%s-%02d-%s" % (kind, i, lang)
                rel = os.path.join("data", "audio-synth", cid + ".wav")
                v = voice(lang, gender)
                if not os.path.exists(os.path.join(ROOT, rel)):
                    speak(it[lang], v, os.path.join(ROOT, rel))
                rows.append({"clip_id": cid, "kind": kind, "item": "%s-%02d" % (kind, i), "lang": lang,
                             "voice": v, "transcript": it[lang], "answer": it["answer"], "wav": rel})
            print("%s-%02d done" % (kind, i), flush=True)
    with open(os.path.join(OUT, "manifest.jsonl"), "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("wrote %d clips to %s" % (len(rows), os.path.relpath(OUT, ROOT)))


if __name__ == "__main__":
    main()
