"""Shared helpers and vocabularies for the synthetic packs (all data is invented)."""
from __future__ import annotations

import random
from typing import List, Tuple

# (english/latin, devanagari, gender) -- gender only used where Hindi verbs need it
NAMES: List[Tuple[str, str, str]] = [
    ("Riya Sharma", "रिया शर्मा", "f"),
    ("Aman Gupta", "अमन गुप्ता", "m"),
    ("Priya Nair", "प्रिया नायर", "f"),
    ("Rahul Verma", "राहुल वर्मा", "m"),
    ("Neha Joshi", "नेहा जोशी", "f"),
    ("Arjun Reddy", "अर्जुन रेड्डी", "m"),
    ("Sunita Yadav", "सुनीता यादव", "f"),
    ("Vikram Singh", "विक्रम सिंह", "m"),
    ("Kavya Iyer", "काव्या अय्यर", "f"),
    ("Rohan Mehta", "रोहन मेहता", "m"),
    ("Anjali Patel", "अंजलि पटेल", "f"),
    ("Suresh Kumar", "सुरेश कुमार", "m"),
    ("Meera Kapoor", "मीरा कपूर", "f"),
    ("Imran Khan", "इमरान ख़ान", "m"),
    ("Farah Siddiqui", "फ़राह सिद्दीक़ी", "f"),
    ("Harpreet Kaur", "हरप्रीत कौर", "f"),
    ("Deepak Mishra", "दीपक मिश्रा", "m"),
    ("Pooja Agarwal", "पूजा अग्रवाल", "f"),
    ("Karan Malhotra", "करण मल्होत्रा", "m"),
    ("Sneha Kulkarni", "स्नेहा कुलकर्णी", "f"),
    ("Manoj Tiwari", "मनोज तिवारी", "m"),
    ("Ayesha Begum", "आयशा बेगम", "f"),
    ("Nikhil Chauhan", "निखिल चौहान", "m"),
    ("Lakshmi Rao", "लक्ष्मी राव", "f"),
]

CITIES: List[Tuple[str, str]] = [
    ("Pune", "पुणे"), ("Delhi", "दिल्ली"), ("Mumbai", "मुंबई"), ("Jaipur", "जयपुर"),
    ("Lucknow", "लखनऊ"), ("Bhopal", "भोपाल"), ("Patna", "पटना"), ("Indore", "इंदौर"),
    ("Kanpur", "कानपुर"), ("Nagpur", "नागपुर"), ("Varanasi", "वाराणसी"), ("Chandigarh", "चंडीगढ़"),
    ("Ahmedabad", "अहमदाबाद"), ("Kolkata", "कोलकाता"), ("Dehradun", "देहरादून"), ("Agra", "आगरा"),
]

VENDORS: List[Tuple[str, str]] = [
    ("Mehta Traders", "मेहता ट्रेडर्स"), ("Sharma General Store", "शर्मा जनरल स्टोर"),
    ("Gupta Electronics", "गुप्ता इलेक्ट्रॉनिक्स"), ("Shree Ganesh Hardware", "श्री गणेश हार्डवेयर"),
    ("Annapurna Caterers", "अन्नपूर्णा केटरर्स"), ("Verma Stationers", "वर्मा स्टेशनर्स"),
    ("Krishna Medical Store", "कृष्णा मेडिकल स्टोर"), ("Lakshmi Textiles", "लक्ष्मी टेक्सटाइल्स"),
    ("Bharat Auto Parts", "भारत ऑटो पार्ट्स"), ("Sai Kirana Bhandar", "साईं किराना भंडार"),
    ("Royal Furniture House", "रॉयल फ़र्नीचर हाउस"), ("Patel Agro Supplies", "पटेल एग्रो सप्लाइज़"),
    ("Jain Book Depot", "जैन बुक डिपो"), ("Singh Sweets", "सिंह स्वीट्स"),
    ("Nova Computers", "नोवा कंप्यूटर्स"), ("Ganga Dairy", "गंगा डेयरी"),
]

MONTHS_EN = ["January", "February", "March", "April", "May", "June", "July", "August",
             "September", "October", "November", "December"]
MONTHS_HI = ["जनवरी", "फ़रवरी", "मार्च", "अप्रैल", "मई", "जून", "जुलाई", "अगस्त",
             "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर"]

DAYS_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DAYS_HI = ["सोमवार", "मंगलवार", "बुधवार", "गुरुवार", "शुक्रवार", "शनिवार", "रविवार"]
DAYS_ROMAN = [["Somvar", "Somvaar"], ["Mangalvar", "Mangalvaar"], ["Budhvar", "Budhvaar"],
              ["Guruvar", "Guruvaar", "Veervar"], ["Shukravar", "Shukravaar"],
              ["Shanivar", "Shanivaar"], ["Ravivar", "Ravivaar", "Itvaar"]]


def rng_for(pack: str, salt: int = 0) -> random.Random:
    """Fixed per-pack generator so a pack's content never depends on the caller's seed."""
    return random.Random("%s:%d" % (pack, salt))


def first(name: str) -> str:
    return name.split()[0]


def fmt_inr(x, decimals: int = 0) -> str:
    """Indian digit grouping: 1234567.5 -> 12,34,567.50"""
    neg = x < 0
    x = abs(x)
    s = ("%." + str(decimals) + "f") % x
    if "." in s:
        whole, frac = s.split(".")
    else:
        whole, frac = s, ""
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        whole = ",".join(parts) + "," + tail
    out = whole + ("." + frac if frac else "")
    return ("-" if neg else "") + out


def numval(x):
    """Return int if x is integral, else float rounded to 2 dp (for JSON references)."""
    f = float(x)
    if abs(f - round(f)) < 1e-9:
        return int(round(f))
    return round(f, 2)
