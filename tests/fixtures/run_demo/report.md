# NO-GO — Upgrade Gate

category=doc-image regressed -10.0 pts (95% CI -16.0 to -5.0, Holm p=0.01758); overall changed +2.7 pts.

> SYNTHETIC fixture — planted effects, not measured model performance.

## Headline numbers

- 300 paired tasks; 0 unpaired tasks; 4 null score rows.
- Overall change: +2.7 pts (95% CI -0.7 to +6.3).
- Pass rates: 76.3% → 79.0%; repeat noise floor 7.0%.

## Slices — worst first

| Slice | n | Delta (pts) | CI (pts) | Holm p | Verdict |
|---|---:|---:|---|---:|---|
| category=doc-image | 100 | -10.0 | -16.0 to -5.0 | 0.01758 | regression |
| modality=image | 100 | -10.0 | -16.0 to -5.0 | 0.01758 | regression |
| lang=hi | 100 | -6.0 | -11.0 to -2.0 | 0.2188 | inconclusive |
| category=math | 50 | +6.0 | +0.0 to +14.0 | 0.375 | inconclusive |
| lang=en | 100 | +7.0 | +1.0 to +14.0 | 0.375 | inconclusive |
| lang=hinglish | 100 | +7.0 | +1.0 to +14.0 | 0.375 | inconclusive |
| modality=text | 200 | +9.0 | +5.5 to +13.0 | 7.629e-05 | improvement |
| category=classification | 50 | +10.0 | +2.0 to +18.0 | 0.375 | inconclusive |
| category=extraction | 50 | +10.0 | +2.0 to +18.0 | 0.375 | inconclusive |
| category=instruction | 50 | +10.0 | +2.0 to +18.0 | 0.375 | inconclusive |

The HTML companion includes an inline SVG confidence-interval forest chart.

## Cost comparison

| Candidate | Model + judge USD | Input tokens | Output tokens |
|---|---:|---:|---:|
| spark-1.2 | 0.342804 | 111000 | 58273 |
| spark-1.3 | 0.414920 | 111000 | 75980 |

Combined judging component: $0.000000.

## Top regressions

### demo-000 · doc-image · hi

Prompt:
```
संलग्न चालान पढ़ें। invoice_id और total_inr JSON में दें।
```

Reference:
```
{
  "invoice_id": "INV-0000",
  "total_inr": 1200
}
```

Old answer:
```
{"invoice_id": "INV-0000", "total_inr": 1200}
```

New answer:
```
{"invoice_id": "INV-0000", "total_inr": 1300}
```

### demo-001 · doc-image · en

Prompt:
```
Read the attached invoice. Return invoice_id and total_inr as JSON.
```

Reference:
```
{
  "invoice_id": "INV-0001",
  "total_inr": 1217
}
```

Old answer:
```
{"invoice_id": "INV-0001", "total_inr": 1217}
```

New answer:
```
{"invoice_id": "INV-0001", "total_inr": 1317}
```

### demo-002 · doc-image · hinglish

Prompt:
```
Invoice image padho aur invoice_id, total_inr JSON mein do.
```

Reference:
```
{
  "invoice_id": "INV-0002",
  "total_inr": 1234
}
```

Old answer:
```
{"invoice_id": "INV-0002", "total_inr": 1234}
```

New answer:
```
{"invoice_id": "INV-0002", "total_inr": 1334}
```

### demo-004 · doc-image · en

Prompt:
```
Read the attached invoice. Return invoice_id and total_inr as JSON.
```

Reference:
```
{
  "invoice_id": "INV-0004",
  "total_inr": 1268
}
```

Old answer:
```
{"invoice_id": "INV-0004", "total_inr": 1268}
```

New answer:
```
{"invoice_id": "INV-0004", "total_inr": 1368}
```

### demo-005 · doc-image · hinglish

Prompt:
```
Invoice image padho aur invoice_id, total_inr JSON mein do.
```

Reference:
```
{
  "invoice_id": "INV-0005",
  "total_inr": 1285
}
```

Old answer:
```
{"invoice_id": "INV-0005", "total_inr": 1285}
```

New answer:
```
{"invoice_id": "INV-0005", "total_inr": 1385}
```

### demo-006 · doc-image · hi

Prompt:
```
संलग्न चालान पढ़ें। invoice_id और total_inr JSON में दें।
```

Reference:
```
{
  "invoice_id": "INV-0006",
  "total_inr": 1302
}
```

Old answer:
```
{"invoice_id": "INV-0006", "total_inr": 1302}
```

New answer:
```
{"invoice_id": "INV-0006", "total_inr": 1402}
```

### demo-009 · doc-image · hi

Prompt:
```
संलग्न चालान पढ़ें। invoice_id और total_inr JSON में दें।
```

Reference:
```
{
  "invoice_id": "INV-0009",
  "total_inr": 1353
}
```

Old answer:
```
{"invoice_id": "INV-0009", "total_inr": 1353}
```

New answer:
```
{"invoice_id": "INV-0009", "total_inr": 1453}
```

### demo-012 · doc-image · hi

Prompt:
```
संलग्न चालान पढ़ें। invoice_id और total_inr JSON में दें।
```

Reference:
```
{
  "invoice_id": "INV-0012",
  "total_inr": 1404
}
```

Old answer:
```
{"invoice_id": "INV-0012", "total_inr": 1404}
```

New answer:
```
{"invoice_id": "INV-0012", "total_inr": 1504}
```

### demo-015 · doc-image · hi

Prompt:
```
संलग्न चालान पढ़ें। invoice_id और total_inr JSON में दें।
```

Reference:
```
{
  "invoice_id": "INV-0015",
  "total_inr": 1455
}
```

Old answer:
```
{"invoice_id": "INV-0015", "total_inr": 1455}
```

New answer:
```
{"invoice_id": "INV-0015", "total_inr": 1555}
```

### demo-003 · doc-image · hi

Prompt:
```
संलग्न चालान पढ़ें। invoice_id और total_inr JSON में दें।
```

Reference:
```
{
  "invoice_id": "INV-0003",
  "total_inr": 1251
}
```

Old answer:
```
{"invoice_id": "INV-0003", "total_inr": 1251}
```

New answer:
```
{"invoice_id": "INV-0003", "total_inr": 1351}
```

## Method notes

Each task contributes one paired observation after majority voting over scored repeats; ties fail, null scores are excluded, and tasks missing either side are dropped. Exact two-sided McNemar tests use discordant pairs. Pointwise percentile bootstrap intervals resample paired tasks (10,000 draws, seed 0). Holm adjustment controls familywise error across all eligible slices (at least 10 pairs), including overlapping slices. Noise floor is the fraction of task/candidate groups with at least two scored repeats that disagree. This is a fixed-horizon decision; repeated peeking at these intervals is not valid sequential inference. The separate sequential_test uses mixture betting e-processes. Inconclusive sample-size estimates are approximate, not stopping guarantees. Regressed cases are majority-vote disagreements; confirmed exports additionally require supporting slice or overall statistical evidence. Cost includes model and judge charges; judge cost is a component, not an extra amount to add. Missing/error calls can bias the scored population; inspect exclusion counts. A GO clears the drop margin and the tested slices; it does not prove that every subpopulation is safe.

Configured drop limit: 2.0 pts; alpha: 0.05; minimum paired tasks: 30.
