# Gate your own model upgrade

You need a Meta Model API key and a file of tasks your product actually handles, each with a known
correct answer. Fifty tasks is enough to start; a few hundred gives clear answers per slice.

## 1. Write the tasks

One JSON object per line in a `.jsonl` file. See [examples/my_tasks.jsonl](../examples/my_tasks.jsonl).

```json
{"id": "refund-01", "category": "support", "lang": "en",
 "prompt": "Classify this message as one of: refund, delivery, cancel. Reply with the label only.\n\nI sent the shoes back last week and still have no money.",
 "scorer": {"type": "label", "value": "refund", "labels": ["refund", "delivery", "cancel"]}}
```

| Field | Required | Meaning |
|---|---|---|
| `prompt` | yes | What the model is asked |
| `scorer` | yes, or `reference` | How an answer is checked (below). A bare `reference` means exact match |
| `id` | no | Stable id; defaults to file name + line number |
| `category`, `lang` | no | Slices the report breaks results down by (default `custom`, `en`) |
| `attachments` | no | Paths to images, PDFs or audio (`.wav`/`.mp3`) sent with the prompt |

Useful scorer types:

| Type | Use it for | Example |
|---|---|---|
| `number` | a numeric answer | `{"type": "number", "value": 308, "tol": 0.01}` |
| `label` | classification | `{"type": "label", "value": "refund", "labels": ["refund", "delivery"]}` |
| `json_fields` | extraction | `{"type": "json_fields", "fields": {"order_number": ["58213", 58213]}}` |
| `one_of` | short answers with several right spellings | `{"type": "one_of", "values": ["Monday", "सोमवार", "Somvar"]}` |
| `exact` | one exact string | `{"type": "exact", "value": "Jaipur"}` |
| `ifeval` | format rules | `{"type": "ifeval", "rules": [{"type": "bullet_count", "value": 3, "prefix": "-"}]}` |

Every answer gets two marks: **correct** (spelling variants and clear answers inside an explanation count)
and **correct format** (exactly what was asked).

## 2. Run the gate

```bash
.venv/bin/upgrade-gate estimate --packs my_tasks.jsonl -b spark-1.2@low -c spark-1.3@low   # free
.venv/bin/upgrade-gate all --packs my_tasks.jsonl -b spark-1.2@low -c spark-1.3@low --budget 5 --yes
```

Exit code: **0** GO, **2** NO-GO, **3** inconclusive. The decision covers accuracy per slice *and* whether the
new version started failing silently (wrong or blank answers where the old one said it couldn't answer).
Every call is checked against the spending cap in `.env` before it is sent.

## 3. Read the report

```bash
npm --prefix web run data && npm --prefix web run dev
```

Add your run to `RUNS` in `scripts/export_web.py` to see it in the report view, or open
`results/<run>/report.html` directly.
