# Findings Log

Pre-register each hypothesis **before** running it. See [../RESEARCH_GUIDE.md](../RESEARCH_GUIDE.md).

Status values: `planned` · `scouting` · `promising` · `confirmed` · `dropped`

> **Literature check done Oct 27, 2026.** Sources are listed under each hypothesis. Items marked _(secondary)_ came from blogs or summaries, not the paper itself. Read the primary source before quoting them.

---

## ⚠️ Plan-level finding: Muse Spark 1.1 is deprecated

Artificial Analysis marks **Muse Spark 1.1 as deprecated** ("This model is deprecated"), with 1.2 as the successor. No retirement date is given. 1.1 pricing: $1.25 in / $4.25 out per 1M tokens. ([source](https://artificialanalysis.ai/models/muse-spark-1-1))

- **Risk:** 1.1 may disappear from the API mid-hackathon, which would break any 1.1-vs-1.3 comparison.
- **Action on first API call:** check whether 1.1 is still callable and whether Meta's docs give a shutdown date. If it's going away, run the 1.1 baseline **first** and save every output.
- **Opportunity:** "Your pinned model is being retired. Here's what changes when you move" is itself a strong, timely demo story.

- **Oct 27 first call:** 1.1 still answers. Note: at `max_completion_tokens=200`, 1.1 and 1.3 returned *empty* answers because reasoning used 190–198 of the 200 tokens. Token limits must leave room for reasoning.

---

## E1 result: Spark 1.2 → 1.3, and a scorer that invented an improvement

- **Run:** Oct 27, 1,325 tasks × 2 versions × 3 repeats = 7,950 calls, reasoning effort low, $14.55, 0 API errors. Run dir `results/e1-upgrade`, tables in [../experiments/out/e1_upgrade.md](../experiments/out/e1_upgrade.md).
- **First scoring said:** 1.3 is **+1.1 pts** overall (p = 6e-5), driven by Hindi (+1.8) and Hinglish (+2.8) math. That looked like a clean "1.3 fixes Hindi" story.
- **Reading the failed answers showed it was mostly the scorer.** 1.2 wrote correct answers in other spellings (`Somwar` vs key `Somvar`, `Budhwar` vs `Budhvar`, `साई` vs `साईं`) or wrapped a correct answer (`**बुधवार**`, `Ravivar (Sunday)`, working shown then `= **रविवार**`).
- **Fix:** two scores. *Content* = correct answer; spelling variants fold (case, bold, nasal marks/nukta, w/v, doubled vowels), and a clear answer inside extra text counts. *Strict* = correct **and** in the exact format asked. The canary keeps its original strict rules. Rescoring needed no new API calls.
- **After the fix:** content score is **identical** (Δ +0.0 on every slice; per answer 3,968 vs 3,971 of 3,975 correct). Strict format: 1.2 slipped 16 more times than 1.3, all on Hindi/Hinglish math (bold, explanation, "(Monday)" after "only write the day"); after majority vote over 3 repeats that is +0.6 pts on math, p = 0.5, not significant. Gate: **GO**.
- **Checked against the images:** the answer key was right. Both models read `केटरर्स` as `केटर्स` (a dropped letter, still scored wrong) and one invoice number as `RS11996`; these misses are shared, so they don't affect the comparison.
- **Other observation:** once, 1.2 refused to copy a phone number and email from the Hindi message it was given ("privacy"), returning masked values. 1.3 never did. n = 1, so it's only a lead for an over-refusal check.
- **What this means:**
  1. At low effort on these packs, 1.2 → 1.3 is a safe upgrade with no measurable quality change; English is at ceiling (100%) for both.
  2. **The headline lesson is about evaluation itself:** a strict exact-match scorer turned format and spelling habits in Hindi into a significant-looking "+1.1 pt" model improvement. Upgrade gates that score non-English output strictly can report changes that aren't there. This is a demo point: show the before/after table.
  3. The packs are too easy to separate the versions. Next: harder tasks, lower effort (`minimal`), Contributor mode (E2–E4).

---

## E3 result: Contributor mode scores the same at ~1/18 the cost

- **Run:** Oct 27. Spark 1.3 Standard vs Spark 1.3 Contributor, effort low, 1,325 tasks × 3 repeats. The Standard half reused E1's saved answers (same tasks, same settings), so the run cost **$0.40**.
- **Result:** the same pass/fail on every task: 3,971 / 3,975 answers correct for both, Δ 0.0 pts on every slice. We compared scores, not answer text, so this doesn't show the answers are word-for-word identical. Gate: **GO**; equivalent within ±2 pts.
- **Cost per 1,000 tasks** (billed tokens in this run): Standard **$1.80**, Contributor **$0.10**, about 18× cheaper.
- **Caveat:** Contributor mode lets Meta use the traffic for training. Fine for synthetic or public data; for customer data it's a policy decision, not a quality one. The Standard answers were collected a few hours earlier than the Contributor ones.

---

## E4 result: more reasoning effort makes 1.3 worse at listening

- **Pilot (text, 28 Oct, $0.02):** maths, instructions and extraction scored 100% at every effort level (minimal → xhigh) with no cut-offs. Extra thinking only cost more (196 → 751 output tokens). So the full run moved to the voice clips, where the model struggles.
- **Run:** Spark 1.3 Contributor, 135 synthetic voice clips × 5 effort levels × 3 tries, same 16,000-token limit at every level (fixes the old 4,000 limit that could cut off high effort). 2,025 calls, **$0.62**.
- **Result:** correct answers fall at every step: **72.8% (minimal) → 68.9 → 64.2 → 63.7 → 58.5% (xhigh)**, counting cut-offs as wrong. Minimal vs xhigh per clip: **−11.9 pts (95% range −18.7 to −5.2), p = 0.0009**, 19 clips worse, 3 better; similar in English, Hindi and Hinglish. Cost per 1,000 clips $0.09 → $0.53.
- **Why:** with more thinking the model increasingly decides it can't hear the clip: "I can't hear the audio" goes **0 → 2 → 27 → 29 → 44** answers (of 405); blank answers 1 → 33–47; token-limit cut-offs 0 → 17. At minimal effort it just transcribes and answers.
- **Takeaway:** for voice input on Spark 1.3, use `reasoning_effort: "minimal"`: more accurate and ~6× cheaper than xhigh.
- **Limits:** synthetic voices, Contributor mode (E3 showed it matches Standard on text), one run. The minimal-vs-xhigh comparison was chosen after seeing the results (not pre-registered), so treat p = 0.0009 as a strong trend; neighbouring steps are not individually significant. A frozen rerun (e.g. on real voices) would confirm it.

## E2 result: no judge-version bias when the judge has a reference answer

- **Design change (28 Oct):** the text packs gave only 9 wrong answers in total, too few to measure a false-pass rate. E2 instead judged the saved E6 voice-note answers (~250 wrong answers from both versions) with Spark 1.2 and 1.3 Contributor judges. No new answers; 1,620 judge calls, **$0.06**.
- **Result:** **0 false passes** for both judges on both versions' wrong answers (0/125 and 0/124 each). No sign that a judge goes easier on its own version. The gate decision is the same with either judge as with fixed-rule scoring.
- **Detail:** both judges marked ~4% of 1.2's correct answers as wrong; 22 of those 24 votes were answers that say "I can't hear the audio" and then answer anyway. A reasonable call.
- **Limits:** the judges saw the reference answer, which makes grading easy. Bias may still appear in reference-free judging of open-ended answers; not tested.

---

## E8 (pre-registered 28 Oct 2026, before any clip was generated or run): spoken self-corrections

- **Lead:** using VoiceOrder, Utsav corrected himself mid-note ("… sorry, …") and saw Spark 1.2 use the corrected
  number while 1.3 kept the first one. Anecdotal (those notes were not stored), so this is a hypothesis.
- **Clips:** 15 order voice notes × 3 languages (English, Hindi, Hinglish), each in two versions with the same
  final details:
  - **correction**: one number is said, then taken back and replaced ("order number 9 3 4 3 7… sorry, no,
    9 3 4 7 3"); 8 items correct the order number, 7 the pincode;
  - **control**: the same note saying only the final number.
  macOS text-to-speech, same voices and prompt as E6's order notes (`audio-synth` extract). Plus a real-voice subset:
  Utsav records the 15 correction lines of items 0–4 (all three languages).
- **Models and settings:** Spark 1.2 vs 1.3, reasoning effort low, 3 tries, same prompt and scorer as E6.
- **Primary test:** on correction clips, correct answers (all three fields right), majority of 3 tries, grouped
  by item (the three languages of one item count as one): **prediction: 1.3 is right less often than 1.2,
  sign test across items p < 0.05.**
- **Secondary:** (a) "kept the taken-back number": the answer contains the corrected-away value; prediction: more
  often on 1.3. (b) Control: on the no-correction twins the gap is smaller, so the effect is about corrections,
  not hearing numbers in general. (c) Real-voice subset, reported with its n, no test promised.
- **If it doesn't hold:** reported as "no measurable difference on self-corrections", and VoiceOrder gets no
  self-correction claim.
- Script: `experiments/e8_corrections.py`; clips: `scripts/build_corrections.py`. Budget cap $3.

---

## E7 result: with a real voice, accuracy drops and blanks appear; the silent-failure rise is borderline by item

- **Pre-registered** on 27 Oct, before any recording: same models and settings as E6, same failure-type rules unchanged; prediction "1.3 gives more confident-wrong-or-blank answers than 1.2 (paired, majority of 3 tries), p < 0.05".
- **Run:** 28 Oct. One speaker (Utsav) read 45 of the E6 lines (15 English, 15 Hindi, 15 Hinglish; 15 each of order voice note, spoken maths, customer request) into a laptop microphone via `web/#/record`. 270 calls, **$0.78**, 1 answer cut off by the token limit (1.3).
- **Result:** **CONFIRMED.** Wrong or blank with no warning (called "confident wrong or blank" in the frozen E6 rules; it does not measure confidence): **6 → 13 of 45 clips, p = 0.016.** Answers with every field blank: **0 → 18** of 135. Unlike the synthetic voices, accuracy also fell: **−11.1 pts (95% range −20.0 to −2.2)**, all of it in voice-note extraction (−33 pts; 5 clips lost, 0 gained). Gate: **NO-GO** on both counts (silent failures, and accuracy past the 2-pt drop limit).
- **Difference from E6:** with the real voice, 1.2 rarely said "I can't hear the audio" (7 answers vs 65 on synthetic voices). So on real speech the story is mostly "1.3 hands back blank fields and mishears more digits", not "1.3 stopped admitting it can't hear".
- **Checked by hand:** every failed extraction is a real misheard number (digits added, dropped or repeated) or a 1.3 blank. A few numbers were misheard identically by both versions (e.g. pincode 452089 as 540289), which may be reading slips; they count against both versions equally in the paired test. Blanks can't be explained by misreading.
- **Item-level check (28 Oct, added after the council review):** the 45 clips are 15 items × 3 languages, which aren't independent. Grouped by item, the wrong-or-blank rise is **5 items worse, 0 better, p = 0.062: borderline**, and counting only filled-in wrong answers it's **1 vs 1: nothing**. So the real-voice confirmation rests on blank answers. E6 (synthetic) stays robust: 18 vs 1 items, p = 0.00008 (filled-in wrong only: 14 vs 1, p = 0.001). The E7 gate is still NO-GO because accuracy fell past the limit.
- **Limits:** one speaker, one microphone, 45 clips. Recordings are kept private (not committed); results and answers are in the report.

---

## E6 result: 1.3 hears about as well as 1.2, but fails silently instead of saying so

- **Why we ran it:** Meta's docs say audio understanding in Muse Spark 1.3 "is currently not fully supported" and quality "may be degraded". We wanted to see whether an upgrade gate catches that on its own.
- **Run:** Oct 27. 135 synthetic voice clips (45 each English, Hindi, Hinglish; spoken math, a customer voice note with order number + pincode + city, intent of a voice note) made with macOS text-to-speech (voices Tara, Rishi, Lekha), each with a **text twin** of the same words. Spark 1.2 vs 1.3, effort low, 3 repeats: 1,620 calls, **$3.34**, 9 answers cut off by the 4,000-token limit (7 on 1.3). Tables: [../experiments/out/e6_audio.md](../experiments/out/e6_audio.md).
- **Text twins:** both versions 100% correct. So every audio failure is a listening problem, not a reasoning one.
- **Accuracy on audio:** basically the same: 278 vs 274 of 405 answers correct. Per task: -2.2 pts, CI -9.7 to +5.2. The gate says **INCONCLUSIVE** and would need ~9,000 more tasks to decide on accuracy alone. Slices: Hindi -11.1 pts (p = 0.13), voice-note extraction -18.2 pts (p = 0.06), both not significant.
- **What changed is how they fail** (per task, majority of 3 repeats, exact McNemar):
  - "Confident wrong or blank" answers: **18 → 42 tasks, p = 3e-6.** 1.3 returns wrong digits, or JSON with every field empty (`{"order_number": "", "pincode": "", "city": ""}`), with no warning.
  - "I can't listen to audio": **23 → 0 tasks, p = 2e-7.** 1.2 often says it can't hear the clip. In 11 answers it says that **and then quotes the spoken words and answers correctly** ("based on the text you provided…"). It hears the audio but believes the user typed it.
  - 1.2 never says this on Hindi clips; it happens on English (14 tasks) and Hinglish (9).
- **What this means:**
  1. On accuracy the upgrade looks neutral. In a product it isn't: 1.2's failures can be detected (it says it can't hear) while 1.3's look like valid answers. A voice-note bot on 1.3 would store wrong or empty order numbers without flagging anything.
  2. **Accuracy-only gates miss this.** The failure-type shift is significant with 135 tasks, where the accuracy test needs about 9,000. Upgrade gates should track *abstain vs confident-wrong*, not just pass rate.
  3. It is consistent with Meta's warning, but the problem we measured is not "1.3 hears worse". It is "1.3 stopped admitting when it hasn't understood".
- **Caveats:**
  - The failure-type rules (the "can't hear" pattern, "all fields blank") were written after reading the answers. That makes this exploratory. To confirm it, rerun on fresh clips (new seed, different speaking rate) with the rules frozen first. Cost ≈ $3.
  - Synthetic TTS voices are cleaner than real voice notes. One run on one day, effort low only.
  - Holm over the 8 failure-type tests leaves the two "all" results significant (3e-6 and 2e-7); the per-language ones are supporting detail.

- **Confirmed with a real voice (E7, 28 Oct):** see the E7 section below.

---

## H1: Judge-version bias in upgrade gates

- **Status:** planned (sharpened after literature check)
- **Original idea:** a same-family judge forgives same-family errors. **This alone is not new.** It's well published (see below).
- **Sharpened hypothesis:** in an upgrade gate, **which version you pick as the judge changes the go/no-go decision.** A Spark 1.3 judge rates 1.3 outputs higher relative to 1.2 than ground truth supports (and vice versa), so the gate is biased toward approving the upgrade.
- **Belief it challenges:** "using the newest, strongest model as the judge is the safe default for upgrade testing."
- **Prediction (confidence %):** _fill in before running_
- **Surprising result:** the gate's decision flips depending on the judge version, or a cross-family / open-weights judge gives a measurably more correct verdict against ground-truth labels.
- **Boring result:** judge-version effect smaller than the noise floor; all judges agree with ground truth.
- **Design:**
  1. Tasks with ground-truth labels (so judge accuracy is measurable, not just judge agreement).
  2. Candidates: Spark 1.2 vs 1.3 outputs on the same inputs.
  3. Judges: Spark 1.2, Spark 1.3, Muse Spark Open (open weights), and one non-Meta judge if budget allows.
  4. Measure per judge: false-pass rate (wrong answer marked right), false-fail rate, and a **version-preference score** controlled for quality. Copy the "fix candidate family, compare judges" estimator from Awuni et al. so quality doesn't confound it.
  5. Run both A/B orders. Position flips were 55% in one study, so they must be controlled.
- **Sample size + cost:** _fill in after pilot_
- **Literature:**
  - Preference Leakage (Li et al., ICLR 2026): judges favour related student models, in three relationships: same model, inheritance, same family. [arXiv 2502.01534](https://arxiv.org/abs/2502.01534)
  - Who Judges Matters (Awuni et al., Sep 2026): same-family lift of 3.4–8.4 points across Llama/Qwen/Gemma/Yi; 55.4% of AB/BA pairs reverse; panel makeup changes 18.5% of outcomes. **Families only, not versions.** [arXiv 2609.17857](https://arxiv.org/abs/2609.17857)
  - Nine Judges, Two Effective Votes (May 2026): a 9-judge panel is worth about 2 independent votes; cross-family isn't much less correlated than same-family. [arXiv 2605.29800](https://arxiv.org/abs/2605.29800)
  - Correlated Errors in LLMs (Kim et al.): judges mark wrong answers right when they share the same wrong answer, and underrate models stronger than themselves. [arXiv 2506.07962](https://arxiv.org/abs/2506.07962)
  - Measuring Self-Preference (EMNLP 2025): the DBG metric separates bias from quality and is applied across judge versions and sizes. **Read this one closely — it's the closest prior work.** [ACL Anthology](https://aclanthology.org/2025.emnlp-main.86.pdf)
  - Counterpoint: one 2026 study says self-preference mostly disappears once quality and judge severity are controlled. [arXiv 2604.22891](https://arxiv.org/html/2604.22891v4)
- **Gap I could find:** no study of the **upgrade-gate setting** — old vs new version of one model, judged by either version, scored against ground truth. Also none on Muse Spark.
- **Claim we can make if true:** "first measurement of judge-version bias in upgrade decisions, on Muse Spark." Don't claim we discovered self-preference.

---

## H5: Pinned model ID changes behaviour over days (canary)

- **Status:** suite ready ([canary/](../canary/README.md)) — **start Oct 28** (needs ~8 days of data)
- **Belief it challenges:** "pinning a model version gives stable behaviour."
- **Sub-hypothesis H5b (new):** output varies with **server load / time of day**. Reason: GPU batching makes even temperature-0 outputs depend on what else is in the batch, so busy hours may give different answers than quiet hours. IST night is US daytime peak.
- **Prediction (confidence %):** _fill in before running_
- **Surprising result:** a step change on a specific day (silent update) **or** a measurable time-of-day pattern in answers, format errors or length.
- **Boring result:** day-to-day variation no larger than within-hour variation.
- **Design:**
  1. Fixed suite of ~50 prompts with deterministic checks (JSON parse OK, exact-match answer, output length, refusal yes/no). Include ~10 Hindi prompts so H6 gets free time-series data.
  2. Run on a schedule: **4× a day** (e.g. 03:00, 09:00, 15:00, 21:00 IST), each prompt repeated 3× per run so within-run noise is measured.
  3. Log model ID, every response header, timestamp, latency, token counts.
  4. Analysis: compare between-day and between-hour variation against within-run noise. Run a change-point detector (ADWIN from the River library, fresh code) on daily pass rates.
  5. Same suite on 1.2 and 1.3 (and 1.1 while it lasts).
- **Cost:** 50 prompts × 3 repeats × 4 runs × 8 days × 2–3 models ≈ 10–14K calls. Keep prompts short. Use Contributor mode if allowed for public prompts.
- **Literature:**
  - Chen, Zaharia & Zou (2023): GPT-4 under the same name dropped from 84% to 51% on prime identification between March and June 2023. [arXiv 2307.09009](https://arxiv.org/abs/2307.09009)
  - (Why) Is My Prompt Getting Worse? (2023): gpt-3.5-turbo snapshot change gave −9.6% on one prompt and +5.1% on another. [arXiv 2311.11123](https://arxiv.org/pdf/2311.11123)
  - Longitudinal study of 63 commercial ML APIs: over 60% changed substantially over time (cited in [arXiv 2407.12220](https://arxiv.org/pdf/2407.12220)).
  - Thinking Machines Lab, "Defeating Nondeterminism in LLM Inference": 1,000 temperature-0 samples on Qwen3-235B gave 80 different completions; the cause is batch-dependent numerics. _(secondary — read the primary post)_ [summary](https://www.spheron.network/blog/vllm-batch-invariance-why-temperature-0-isnt-deterministic/)
  - Practitioner canary + change-point method, and a reported 2025 Anthropic infrastructure incident. _(secondary, unverified)_ [dev.to](https://dev.to/aiwithmohit/your-llm-is-lying-to-you-silently-4-statistical-signals-that-catch-drift-before-users-do-4cg2)
- **Gap I could find:** no recent peer-reviewed longitudinal study of a **pinned** model version, none that separates day-to-day drift from time-of-day/load effects, and nothing on Muse Spark.

---

## H6: An upgrade improves English but quietly hurts Hindi / Hinglish

- **Status:** planned
- **Belief it challenges:** "if a new version scores better overall, it's better for every language."
- **Prediction (confidence %):** _fill in before running_
- **Surprising result:** 1.3 vs 1.2 change is positive on English but flat or negative on the matched Hindi items, beyond the noise floor.
- **Boring result:** the change has the same sign and size in both languages.
- **Design:**
  1. **Matched pairs**: the same item in English and Hindi, so the only difference is language. Use parallel datasets (Hindi IFEval / GSM8K versions below).
  2. Add a small Hinglish (code-mixed) set: write ~50 items yourself with known answers. That's your "Build for Your World" angle, and no benchmark covers it well.
  3. Two prompt conditions: English instructions vs Hindi instructions. One study found instruction language alone shifts Hindi accuracy, so control it.
  4. Deterministic scoring wherever possible (exact match for math, rule checks for IFEval). Use judges only where unavoidable, and remember H1.
  5. Report the **interaction**: (Δ Hindi) − (Δ English) with a paired bootstrap CI.
- **Candidate datasets (check licenses before use):**
  - Hindi IFEval / MT-Bench / GSM8K / BFCL (NVIDIA-led, "Benchmarking Hindi LLMs", 2025). Parallel to the English originals, so good for matched pairs. [ACL Anthology](https://preview.aclanthology.org/setup/2025.bhasha-1.5)
  - MILU (AI4Bharat): 150K+ multiple-choice questions from Indian exams, 11 languages. [arXiv 2411.02538](https://arxiv.org/abs/2411.02538)
  - IndicGenBench (Google): 29 Indic languages, parallel generation tasks. [GitHub](https://github.com/google-research-datasets/indic-gen-bench/)
- **Literature:**
  - Indic VLMs: average drops of 8.3 points for Hindi and 5.5 for Telugu vs English. [ACL 2026](https://aclanthology.org/2026.alvr-main.26/)
  - Hindi analogy study: models do better on Hindi questions when instructions are in English. [Pith summary](https://pith.science/paper/2507.13238)
  - Reordering / voice changes in Hindi and Malayalam math problems cause significant accuracy drops. [Pith summary](https://pith.science/paper/2609.03511)
- **Gap I could find:** studies show Hindi lags English **within one model**. I found no study measuring whether a **version upgrade** changes that gap, and **no public Hindi results for Muse Spark at all**. Meta's eval methodology PDF lists English-centric benchmarks (HLE, ARC-AGI-2, SWE-bench, etc.). I couldn't extract its full text, so check it by hand for any multilingual section.

---

## Priority after literature check

| # | Novelty after search | Cost | Verdict |
|---|---|---|---|
| H5 canary (+ H5b load) | Gap is clear on Muse Spark and pinned versions | Low, but needs days | **Start Oct 28, no matter what** |
| H6 Hindi upgrade gap | Gap is clear, and it's your own story | Low-medium | **Run first among one-off experiments** |
| H1 judge-version bias | Narrow gap; general effect already known | Low | Run, but frame carefully |
| — 1.1 deprecation | Not a hypothesis, a risk | — | Check on first API call |

<!-- Template for new hypotheses:
## H<n>: <one-line hypothesis>
- Status:
- Belief it challenges:
- Prediction (confidence %):
- Surprising result:
- Boring result:
- Design:
- Sample size + cost:
- Literature:
- Gap:
- Results:
-->
