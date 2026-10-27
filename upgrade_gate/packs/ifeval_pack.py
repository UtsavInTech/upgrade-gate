"""ifeval: verifiable-instruction prompts (IFEval style), en + hi.

Each prompt = a writing task on a topic + 1-2 checkable rules. The 50 Hindi items mirror 50
English items (same topic, same rule parameters) and add a devanagari_ratio_min rule.
"""
from __future__ import annotations

from typing import List

from ..schema import Task
from ._common import rng_for

PACK = "ifeval"
N_EN = 100
N_HI = 50
DEVANAGARI_MIN = 0.75

# en topic, hi topic, en keyword, hi keyword
TOPICS = [
    ("the monsoon season", "मानसून का मौसम", "rain", "बारिश"),
    ("learning to cook", "खाना बनाना सीखना", "kitchen", "रसोई"),
    ("public libraries", "सार्वजनिक पुस्तकालय", "books", "किताब"),
    ("saving money", "पैसे बचाना", "budget", "बजट"),
    ("morning walks", "सुबह की सैर", "air", "हवा"),
    ("train journeys", "रेल यात्रा", "station", "स्टेशन"),
    ("growing vegetables at home", "घर पर सब्ज़ियाँ उगाना", "soil", "मिट्टी"),
    ("playing cricket", "क्रिकेट खेलना", "team", "टीम"),
    ("the importance of sleep", "नींद का महत्व", "rest", "आराम"),
    ("online shopping", "ऑनलाइन ख़रीदारी", "delivery", "डिलीवरी"),
    ("street food", "स्ट्रीट फ़ूड", "taste", "स्वाद"),
    ("learning a new language", "नई भाषा सीखना", "practice", "अभ्यास"),
    ("drinking enough water", "पर्याप्त पानी पीना", "health", "सेहत"),
    ("celebrating festivals with family", "परिवार के साथ त्योहार मनाना", "together", "मिलकर"),
    ("working from home", "घर से काम करना", "routine", "दिनचर्या"),
    ("keeping a city clean", "शहर को साफ़ रखना", "waste", "कचरा"),
    ("riding a bicycle", "साइकिल चलाना", "helmet", "हेलमेट"),
    ("reading the newspaper", "अख़बार पढ़ना", "news", "समाचार"),
    ("planting trees", "पेड़ लगाना", "shade", "छाया"),
    ("using a smartphone wisely", "स्मार्टफ़ोन का समझदारी से इस्तेमाल", "screen", "स्क्रीन"),
    ("preparing for exams", "परीक्षा की तैयारी", "time", "समय"),
    ("visiting the mountains", "पहाड़ों की यात्रा", "cold", "ठंड"),
    ("taking care of pets", "पालतू जानवरों की देखभाल", "food", "खाना"),
    ("practising yoga", "योग करना", "body", "शरीर"),
    ("saving electricity at home", "घर में बिजली बचाना", "bill", "बिल"),
]

FORMS = {
    "para": (["Write a short paragraph about %s.", "Explain %s to a ten-year-old.", "Describe %s in your own words."],
             ["%s के बारे में एक छोटा अनुच्छेद लिखिए।", "%s को दस साल के बच्चे को समझाइए।", "%s का अपने शब्दों में वर्णन कीजिए।"]),
    "list": (["Give some practical tips about %s.", "List a few benefits of %s."],
             ["%s के बारे में कुछ काम के सुझाव दीजिए।", "%s के कुछ फ़ायदे बताइए।"]),
    "json": (["Summarise %s.", "Write a brief note about %s."],
             ["%s का सार लिखिए।", "%s पर एक छोटा नोट लिखिए।"]),
}

WORD_RANGES = [(20, 40), (30, 50), (50, 80), (80, 120)]
START_WORDS = [("Today", "आज"), ("Interestingly", "दरअसल"), ("Remember", "याद रखें"), ("Honestly", "सच कहूँ तो")]
END_PHRASES = [("Thank you for reading", "पढ़ने के लिए धन्यवाद"), ("That is all for today", "आज के लिए इतना ही"),
               ("Stay curious", "जिज्ञासु बने रहें")]
BANNED = [("very", "बहुत"), ("really", "सचमुच"), ("important", "महत्वपूर्ण")]


def _r_words(r, t):
    a, b = r.choice(WORD_RANGES)
    return ("Your answer must be between %d and %d words long." % (a, b),
            "आपका उत्तर %d से %d शब्दों के बीच होना चाहिए।" % (a, b),
            {"type": "word_count_between", "min": a, "max": b}, None)


def _r_nocomma(r, t):
    return ("Do not use any commas in your answer.", "उत्तर में कहीं भी कॉमा (,) का प्रयोग न करें।",
            {"type": "no_commas"}, None)


def _r_caps(r, t):
    return ("Write your entire answer in capital letters only.", None, {"type": "all_caps"}, None)


def _r_lower(r, t):
    return ("Write your entire answer in lowercase letters only, with no capital letters at all.", None,
            {"type": "all_lower"}, None)


def _r_start(r, t):
    en, hi = r.choice(START_WORDS)
    return ("Begin your answer with the word '%s'." % en, "अपना उत्तर '%s' से शुरू करें।" % hi,
            {"type": "starts_with", "value": en}, {"type": "starts_with", "value": hi})


def _r_end(r, t):
    en, hi = r.choice(END_PHRASES)
    return ("End your answer with the exact phrase '%s' and write nothing after it." % en,
            "अपना उत्तर ठीक इस वाक्यांश से ख़त्म करें: '%s'। उसके बाद कुछ न लिखें।" % hi,
            {"type": "ends_with", "value": en}, {"type": "ends_with", "value": hi})


def _r_lines(r, t):
    n = r.randint(3, 6)
    return ("Write exactly %d lines." % n, "ठीक %d पंक्तियाँ लिखें।" % n, {"type": "line_count", "value": n}, None)


def _r_bullets(r, t):
    n = r.randint(3, 6)
    return ("Give exactly %d bullet points, each on its own line starting with '- ', and nothing else." % n,
            "ठीक %d बुलेट पॉइंट लिखें, हर एक नई पंक्ति में '- ' से शुरू हो, और इसके अलावा कुछ न लिखें।" % n,
            {"type": "bullet_count", "value": n, "prefix": "-"}, None)


def _r_include(r, t):
    return ("Include the word '%s' at least once." % t[2], "उत्तर में '%s' शब्द कम से कम एक बार ज़रूर लिखें।" % t[3],
            {"type": "must_include", "values": [t[2]]}, {"type": "must_include", "values": [t[3]]})


def _r_exclude(r, t):
    en, hi = r.choice(BANNED)
    return ("Do not use the word '%s' anywhere in your answer." % en, "उत्तर में '%s' शब्द का प्रयोग कहीं भी न करें।" % hi,
            {"type": "must_not_include", "values": [en]}, {"type": "must_not_include", "values": [hi]})


def _r_json(r, t):
    return ('Reply with only a JSON object with exactly two keys, "title" and "summary", and no other text.',
            'केवल एक JSON object लिखें जिसमें ठीक दो keys हों, "title" और "summary"; इसके अलावा कुछ न लिखें।',
            {"type": "json_parseable", "keys": ["title", "summary"]}, None)


# (form, rule makers, hindi-compatible)
COMBOS = [
    ("para", [_r_words], True),
    ("para", [_r_nocomma, _r_words], True),
    ("para", [_r_caps], False),
    ("para", [_r_lower, _r_include], False),
    ("para", [_r_start, _r_words], True),
    ("para", [_r_end], True),
    ("list", [_r_lines], True),
    ("list", [_r_bullets], True),
    ("list", [_r_bullets, _r_exclude], True),
    ("para", [_r_include, _r_exclude], True),
    ("json", [_r_json], True),
    ("para", [_r_start, _r_end], True),
    ("list", [_r_nocomma, _r_lines], True),
    ("list", [_r_caps, _r_bullets], False),
]


def build() -> List[Task]:
    r = rng_for(PACK)
    tasks: List[Task] = []
    hi_left = N_HI
    for i in range(N_EN):
        t = TOPICS[i % len(TOPICS)]
        form, makers, hi_ok = COMBOS[i % len(COMBOS)]
        fi = r.randrange(len(FORMS[form][0]))
        en_parts = [FORMS[form][0][fi] % t[0]]
        hi_parts = [FORMS[form][1][fi] % t[1]]
        en_rules, hi_rules = [], []
        for mk in makers:
            en_txt, hi_txt, en_rule, hi_rule = mk(r, t)
            en_parts.append(en_txt)
            en_rules.append(en_rule)
            if hi_txt is not None:
                hi_parts.append(hi_txt)
                hi_rules.append(hi_rule if hi_rule is not None else dict(en_rule))
        en_id = "%s-%04d-en" % (PACK, i + 1)
        tasks.append(_task(en_id, "en", " ".join(en_parts), en_rules, None, en_id, t[0]))
        if hi_ok and hi_left > 0:
            hi_left -= 1
            hi_parts.append("पूरा उत्तर हिंदी (देवनागरी) में लिखें।")
            hi_rules.append({"type": "devanagari_ratio_min", "value": DEVANAGARI_MIN})
            tasks.append(_task("%s-%04d-hi" % (PACK, i + 1), "hi", " ".join(hi_parts), hi_rules, en_id, en_id, t[0]))
    return tasks


def _task(tid, lang, prompt, rules, pair_id, group, topic) -> Task:
    return Task(id=tid, pack=PACK, category="instruction", lang=lang, modality="text", prompt=prompt,
                reference={"rules": rules}, scorer={"type": "ifeval", "rules": rules},
                pair_id=pair_id, meta={"group": group, "topic": topic, "rule_types": [x["type"] for x in rules]})
