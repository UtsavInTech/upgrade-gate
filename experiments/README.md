# Experiments (pre-registered in findings/LOG.md)

Every script does a dry run by default: it prints the task count and cost estimate and spends nothing. Add `--yes` to spend. `--budget` is a hard stop.

| Script | Hypothesis | Compares |
|---|---|---|
| `e1_upgrade.py` | headline gate | spark-1.2 vs 1.3, every pack, sliced by category / language / modality |
| `e2_judge_version.py` | H1 judge-version bias | judges 1.2, 1.3, Wonder (+ Spark Open with `--open`) vs ground truth |
| `e3_contributor.py` | H3 Contributor = Standard? | 1.3 vs 1.3-contributor, equivalence margin ±2 pts |
| `e4_effort.py` | H4 more effort ever worse? | 1.3 at minimal → max |
| `e5_hindi.py` | H6 upgrade gap by language | matched en/hi/hinglish pairs, interaction CI |

```bash
python3 experiments/e1_upgrade.py --n 40          # dry run
python3 experiments/e1_upgrade.py --n 40 --yes    # real
python3 experiments/e1_upgrade.py --run-dir results/e1-upgrade   # re-analyse only
```
Results go to `experiments/out/<name>.md` and `.json`. Before running, fill in your prediction in findings/LOG.md.
