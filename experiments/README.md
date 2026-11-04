# Experiments (pre-registered in findings/LOG.md)

Every script does a dry run by default: it prints the task count and cost estimate and spends nothing. Add `--yes` to spend. `--budget` is a hard stop.

| Script | Hypothesis | Compares |
|---|---|---|
| `e1_upgrade.py` | headline gate | spark-1.2 vs 1.3, every pack, sliced by category / language / modality |
| `e2_judge_version.py` | H1 judge-version bias | judges 1.2, 1.3, Wonder (+ Spark Open with `--open`) vs ground truth |
| `e3_contributor.py` | H3 Contributor = Standard? | 1.3 vs 1.3-contributor, equivalence margin ±2 pts |
| `e4_effort.py` | H4 more effort ever worse? | 1.3 at minimal → max |
| `e5_hindi.py` | H6 upgrade gap by language | matched en/hi/hinglish pairs, interaction CI |
| `e6_audio.py` | does 1.3 listen worse? | 1.2 vs 1.3 on 135 synthetic voice notes, each with a text twin |
| `e7_real_voices.py` | does E6 hold for a real voice? | the same 45 lines read by a person |
| `e8_corrections.py` | does 1.3 keep a number the speaker took back? | spoken self-corrections vs control notes |
| `e9_route.py` | is transcribe-first a safe upgrade? | 1.2 listening vs Voice Transcribe → 1.3 (and → 1.2) |
| `e10_new_speakers.py` | do E7 and E9 hold for another speaker? | new speaker alone, then pooled with E7 |

```bash
python3 experiments/e1_upgrade.py --n 40          # dry run
python3 experiments/e1_upgrade.py --n 40 --yes    # real
python3 experiments/e1_upgrade.py --run-dir results/e1-upgrade   # re-analyse only
```
Results go to `experiments/out/<name>.md` and `.json`. Each prediction is written in findings/LOG.md before the run.
