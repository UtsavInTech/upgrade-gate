"""E8 — when a customer corrects a number mid-note, which version saves the corrected one?

Pre-registered in findings/LOG.md (28 Oct 2026) before any clip was generated or run:
  - 15 order voice notes × en/hi/hinglish. Correction clip: a number is said, taken back, said again.
    Control clip: the same note with only the final number. Same voices and prompt as E6 extract.
  - spark-1.2@low vs spark-1.3@low, 3 tries, majority per clip (ties count as fail).
  - Primary: synthetic correction clips, all three fields right. Items compared with a sign test
    (one item = its three languages). Prediction: 1.3 is right less often, p < 0.05.
  - Secondary: 1.3 keeps the taken-back number more often; the gap on control clips is smaller;
    real-voice takes are reported separately with their n.

  python3 experiments/e8_corrections.py                  # dry run, prints cost
  python3 experiments/e8_corrections.py --yes --budget 3
"""
from __future__ import annotations

import collections
import json
import os
import re

from common import base_args, compare, majority, mcnemar_exact, pairs, run_and_score, table, tasks_by_id, write_result
from upgrade_gate.behaviour import _sign_test
from upgrade_gate.schema import read_jsonl

PACKS = ["audio-corrections"]
A, B = "spark-1.2@low", "spark-1.3@low"


def saved_field(text: str, field: str):
    """Digits the answer gives for `field`, or None if there is no JSON object with it."""
    m = re.search(r"\{.*\}", text or "", re.S)
    try:
        obj = json.loads(m.group(0)) if m else None
    except ValueError:
        return None
    if not isinstance(obj, dict):
        return None
    for k, v in obj.items():
        if k.strip().lower() == field:
            return re.sub(r"\D", "", str(v))
    return None


def kept_first(run_dir: str, tasks):
    """(task, candidate) -> [bool per try]: the answer saved the number the customer took back."""
    out = collections.defaultdict(list)
    for r in read_jsonl(os.path.join(run_dir, "responses.jsonl")):
        t = tasks.get(r["task_id"])
        if not t or t["meta"]["variant"] != "corr":
            continue
        out[(r["task_id"], r["candidate"])].append(saved_field(r.get("text") or "", t["meta"]["field"]) == t["meta"]["first"])
    return out


def by_item(maj, ids, tasks):
    """Item -> (clips right for A, clips right for B), over the item's languages."""
    acc = collections.defaultdict(lambda: [0, 0])
    for i in ids:
        if (i, A) in maj and (i, B) in maj:
            acc[tasks[i]["meta"]["item"]][0] += maj[(i, A)]
            acc[tasks[i]["meta"]["item"]][1] += maj[(i, B)]
    return dict(acc)


def item_test(items) -> dict:
    worse = sum(1 for a, b in items.values() if b < a)
    better = sum(1 for a, b in items.values() if b > a)
    return {"items": len(items), "worse": worse, "better": better, "p": _sign_test(worse, better),
            A: sum(a for a, _ in items.values()), B: sum(b for _, b in items.values())}


def analyse(run_dir: str) -> None:
    tasks = tasks_by_id(run_dir)
    maj = majority(os.path.join(run_dir, "scores.jsonl"))

    def ids(variant, synthetic=True):
        return [i for i, t in tasks.items() if t["meta"]["variant"] == variant
                and (t["meta"]["speaker"] == "synthetic") == synthetic]

    corr, ctrl, real = ids("corr"), ids("ctrl"), ids("corr", synthetic=False)
    rows = [compare(pairs(maj, corr, A, B), "correction clips"), compare(pairs(maj, ctrl, A, B), "control clips")]
    for lang in ("en", "hi", "hinglish"):
        rows.append(compare(pairs(maj, [i for i in corr if tasks[i]["lang"] == lang], A, B), "correction, %s" % lang))
    for f in ("order_number", "pincode"):
        rows.append(compare(pairs(maj, [i for i in corr if tasks[i]["meta"]["field"] == f], A, B),
                            "correction, %s corrected" % f))
    if real:
        rows.append(compare(pairs(maj, real, A, B), "correction, real voice"))

    it_corr, it_ctrl = by_item(maj, corr, tasks), by_item(maj, ctrl, tasks)
    primary, control = item_test(it_corr), item_test(it_ctrl)
    # Difference in difference per item: did 1.3 lose more on the correction clip than on its control?
    dd = {k: (it_corr[k][1] - it_corr[k][0]) - (it_ctrl[k][1] - it_ctrl[k][0]) for k in it_corr if k in it_ctrl}
    dd_test = {"worse": sum(v < 0 for v in dd.values()), "better": sum(v > 0 for v in dd.values())}
    dd_test["p"] = _sign_test(dd_test["worse"], dd_test["better"])

    kf = kept_first(run_dir, tasks)
    kf_rows = []
    for label, sub in (("synthetic", corr), ("real voice", real)):
        if not sub:
            continue
        tries = {c: sum(sum(kf.get((i, c), [])) for i in sub) for c in (A, B)}
        n_tries = {c: sum(len(kf.get((i, c), [])) for i in sub) for c in (A, B)}
        mj = {c: {i: sum(kf[(i, c)]) * 2 > len(kf[(i, c)]) for i in sub if kf.get((i, c))} for c in (A, B)}
        only_a = sum(1 for i in sub if mj[A].get(i) and not mj[B].get(i))
        only_b = sum(1 for i in sub if mj[B].get(i) and not mj[A].get(i))
        kf_rows.append({"set": label, "clips": len(sub), "tries": n_tries, "kept_tries": tries,
                        A: sum(mj[A].values()), B: sum(mj[B].values()), "only_" + A: only_a, "only_" + B: only_b,
                        "p": mcnemar_exact(only_a, only_b)})

    held = primary["worse"] > primary["better"] and primary["p"] < 0.05
    lines = [
        "# E8 — spoken self-corrections: %s vs %s" % (A, B), "", "Run: `%s` · clips: %d synthetic correction, "
        "%d control, %d real-voice correction" % (run_dir, len(corr), len(ctrl), len(real)), "",
        "## Pre-registered test (items = one note in three languages, sign test)", "",
        "| Clips | Items | %s right | %s right | items worse on 1.3 | items better | p |" % (A, B),
        "|---|---|---|---|---|---|---|",
        "| correction | %d | %d | %d | %d | %d | %.2g |" % (primary["items"], primary[A], primary[B], primary["worse"],
                                                        primary["better"], primary["p"]),
        "| control | %d | %d | %d | %d | %d | %.2g |" % (control["items"], control[A], control[B], control["worse"],
                                                     control["better"], control["p"]), "",
        "Did 1.3 lose more on the correction clip than on the same note without one? items worse %d, better %d, "
        "p = %.2g." % (dd_test["worse"], dd_test["better"], dd_test["p"]), "",
        "**Prediction %s:** on correction clips 1.3 got %d of %d right vs %d for 1.2; %d items worse, %d better, "
        "p = %.2g." % ("CONFIRMED" if held else "NOT CONFIRMED", primary[B], len(corr), primary[A], primary["worse"],
                        primary["better"], primary["p"]), "",
        "## Kept the number the customer took back", "",
        "| Set | Clips | %s tries | %s tries | %s clips (majority) | %s clips | only 1.2 | only 1.3 | p |" % (A, B, A, B),
        "|---|---|---|---|---|---|---|---|---|"]
    for r in kf_rows:
        lines.append("| %s | %d | %d / %d | %d / %d | %d | %d | %d | %d | %.2g |" % (
            r["set"], r["clips"], r["kept_tries"][A], r["tries"][A], r["kept_tries"][B], r["tries"][B], r[A], r[B],
            r["only_" + A], r["only_" + B], r["p"]))
    lines += ["", "## All fields right, by slice (per clip, McNemar)", "", table(rows)]
    write_result("e8_corrections", "\n".join(lines), {
        "run_dir": run_dir, "primary": primary, "control": control, "diff_in_diff": dd_test, "kept_first": kf_rows,
        "rows": rows, "items_correction": it_corr, "items_control": it_ctrl, "confirmed": held})


if __name__ == "__main__":
    args = base_args(__doc__).parse_args()
    rd = args.run_dir or run_and_score(PACKS, [A, B], args.n, args.repeats, args.budget, args.yes, "e8-corrections")
    analyse(rd)
