"""Deterministic, synthetic demo data; no model calls or measured model claims.

Run from the repo root: .venv/bin/python tests/fixtures/make_fixture.py
300 paired tasks, 3 repeats: +8/300 overall, -10/100 document images,
-6/100 Hindi tasks, and approximately 30% more candidate output tokens.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent / 'run_demo'


def generate():
    rng = random.Random(73)
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / 'assets').mkdir(exist_ok=True)
    tasks, responses, scores = [], [], []
    categories = ['doc-image'] * 100 + [c for c in ['classification', 'extraction', 'instruction', 'math'] for _ in range(50)]
    # Six Hindi losses, four English/Hinglish losses; all ten are documents.
    losses = {0, 3, 6, 9, 12, 15, 1, 2, 4, 5}
    wins = set(i for i in range(100, 300) if i % 3 != 0)
    wins = set(sorted(wins)[::7][:18])
    for i, category in enumerate(categories):
        task_id = 'demo-%03d' % i
        lang = ['hi', 'en', 'hinglish'][i % 3]
        amount = 1200 + i * 17
        if category == 'doc-image':
            reference = {'invoice_id': 'INV-%04d' % i, 'total_inr': amount}
            prompt = {'en': 'Read the attached invoice. Return invoice_id and total_inr as JSON.', 'hi': 'संलग्न चालान पढ़ें। invoice_id और total_inr JSON में दें।', 'hinglish': 'Invoice image padho aur invoice_id, total_inr JSON mein do.'}[lang]
            asset = 'tests/fixtures/run_demo/assets/%s.svg' % task_id
            (ROOT / 'assets' / (task_id + '.svg')).write_text('<svg xmlns="http://www.w3.org/2000/svg" width="560" height="260" viewBox="0 0 560 260"><rect width="560" height="260" fill="#f6f3ea"/><g fill="#252525" font-family="monospace"><text x="32" y="48" font-size="24">KIRANA / TAX INVOICE</text><text x="32" y="100" font-size="20">Invoice: INV-%04d</text><text x="32" y="145" font-size="18">Office supplies / paid</text><text x="32" y="210" font-size="26">TOTAL INR %d</text></g></svg>' % (i, amount), encoding='utf-8')
            attachments = [asset]
        elif category == 'classification':
            reference = 'refund'
            prompt = {'en': 'Classify this request as refund, balance, or transfer: I was charged twice; please return the extra payment. Reply with the label only.', 'hi': 'श्रेणी चुनें: refund, balance या transfer। मेरे खाते से दो बार पैसे कटे, अतिरिक्त भुगतान वापस करें। केवल लेबल दें।', 'hinglish': 'Label choose karo: refund, balance, transfer. Do baar charge hua, extra payment wapas chahiye. Sirf label do.'}[lang]
            attachments = []
        elif category == 'extraction':
            reference = {'order_id': 'ORD-%04d' % i, 'quantity': i % 8 + 1}
            prompt = 'Extract order_id and quantity as JSON: Order ORD-%04d contains %d notebooks.' % (i, i % 8 + 1)
            if lang == 'hi':
                prompt = 'JSON में order_id और quantity निकालें: ऑर्डर ORD-%04d में %d नोटबुक हैं।' % (i, i % 8 + 1)
            elif lang == 'hinglish':
                prompt = 'JSON mein order_id aur quantity nikalo: order ORD-%04d mein %d notebooks hain.' % (i, i % 8 + 1)
            attachments = []
        elif category == 'instruction':
            reference = 'READY'
            prompt = {'en': 'Reply with exactly READY in uppercase, without punctuation or explanation.', 'hi': 'केवल बड़े अक्षरों में READY लिखें। कोई विराम चिह्न या व्याख्या न दें।', 'hinglish': 'Sirf uppercase READY likho, punctuation ya explanation mat do.'}[lang]
            attachments = []
        else:
            reference = str((i + 17) * 3)
            prompt = {'en': 'Compute (%d + 17) × 3. Reply with the integer only.', 'hi': '(%d + 17) × 3 की गणना करें। केवल पूर्णांक दें।', 'hinglish': '(%d + 17) × 3 calculate karo. Sirf integer do.'}[lang] % i
            attachments = []
        tasks.append(dict(id=task_id, pack='synthetic-demo', category=category, lang=lang, modality='image' if attachments else 'text', prompt=prompt, reference=reference, scorer={'type': 'json_fields' if isinstance(reference, dict) else 'exact_cs'}, attachments=attachments, pair_id=None, meta={'synthetic': True}))
        base_pass = i % 5 != 0
        if i in losses:
            base_pass = True
        if i in wins:
            base_pass = False
        for candidate in ['spark-1.2', 'spark-1.3']:
            passed = base_pass if candidate == 'spark-1.2' else (True if i in wins else False if i in losses else base_pass)
            for repeat in range(3):
                outcome = not passed if repeat == 2 and rng.random() < .07 else passed
                error = repeat == 2 and rng.random() < .008
                good_text = json.dumps(reference, ensure_ascii=False) if isinstance(reference, dict) else str(reference)
                bad_text = json.dumps(dict(reference, total_inr=amount + 100)) if category == 'doc-image' else ('{"order_id":"unknown","quantity":0}' if category == 'extraction' else 'balance' if category == 'classification' else 'Ready.' if category == 'instruction' else str(int(reference) + 3))
                output_tokens = rng.randint(30, 100)
                if candidate == 'spark-1.3':
                    output_tokens = round(output_tokens * 1.3)
                usage = dict(input_tokens=220 if attachments else 75, output_tokens=output_tokens, reasoning_tokens=0)
                responses.append(dict(run_id='run_demo', task_id=task_id, candidate=candidate, repeat=repeat, text=None if error else good_text if outcome else bad_text, usage=usage, cost_usd=0 if error else usage['input_tokens'] * .000001 + output_tokens * .000004, latency_ms=rng.randint(450, 1300), error='synthetic timeout' if error else None, ts_utc='2026-10-27T08:00:00Z', returned_model=candidate, cached=False))
                scores.append(dict(run_id='run_demo', task_id=task_id, candidate=candidate, repeat=repeat, passed=None if error else outcome, score=None if error else float(outcome), method='deterministic', detail='Synthetic reference comparison', judge_votes=[], cost_usd=0.0))
    run = dict(run_id='run_demo', created_utc='2026-10-27T08:00:00Z', candidates=[dict(name=c, model_id=c, params={}) for c in ['spark-1.2', 'spark-1.3']], baseline='spark-1.2', packs=['synthetic-demo'], n_tasks=len(tasks), repeats=3, budget_usd=None, notes='SYNTHETIC fixture — planted effects, not measured model performance.')
    (ROOT / 'run.json').write_text(json.dumps(run, indent=2) + '\n', encoding='utf-8')
    for name, rows in [('tasks', tasks), ('responses', responses), ('scores', scores)]:
        (ROOT / (name + '.jsonl')).write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows), encoding='utf-8')


if __name__ == '__main__':
    generate()
