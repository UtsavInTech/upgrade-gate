# Outreach drafts

Edit freely; these are starting points in your voice. Post the X thread with the clip-grid screenshot
(`web/screenshots/report.png`, cropped to the grid) and a 20-second screen recording of one clip.

## 1. Hackathon Discord (ask 2–3 people to try it)

> Hey all, I'm building **Upgrade Gate** for the Meta hackathon: a check you run before switching to a new
> Muse Spark version. It replays your own tasks on both versions and tells you GO / NO-GO with the failing
> answers attached.
>
> First result surprised me: on voice notes (English, Hindi, Hinglish), Spark 1.3 gets about as many right
> as 1.2, but when it misunderstands it **stops saying "I can't hear this"** and returns wrong or blank
> answers instead (18 → 42 of 135 clips). I re-ran it on my own recorded voice with the prediction written
> down first, and it held (6 → 13 of 45). It runs as a GitHub check: the PR that bumps the model fails and
> the deploy step is skipped.
>
> If you're already calling Spark in your project, could you try it on 20–50 of your own prompts? It takes
> about 10 minutes and costs a few cents on Contributor mode. Guide: `docs/BRING_YOUR_OWN_TASKS.md` in
> <repo link>. I'd love one line back on whether the result was useful or wrong. Happy to help set it up.

## 2. X thread

**Post 1** (attach the grid image)
> We tested Meta's Muse Spark 1.3 against 1.2 on 135 voice notes in English, Hindi and Hinglish.
>
> Same accuracy. But 1.3 stopped saying "I can't hear this audio", and started returning wrong or empty
> answers instead: 18 → 42 clips. Each square below is one voice note.

**Post 2** (attach the 20-second clip recording)
> Example: a customer leaves a Hindi voice note with their pincode, 452089. 1.2 gets it right.
> 1.3 answers 380015, a real Ahmedabad pincode, just the wrong one, three times out of three.
>
> It's correctly shaped, so a format check passes it. That's the error that reaches your database.

**Post 3**
> An accuracy-only check calls this upgrade "inconclusive". It would need ~9,000 more clips to decide.
> Checking *how* answers fail makes it clear with 135 (p ≈ 3 × 10⁻⁶).
>
> Bonus lesson: our own scorer first claimed 1.3 was "significantly better" at Hindi. It was spelling:
> Somwar vs Somvar.

**Post 4**
> Then we recorded 45 of the lines in a real voice, with the prediction written down first. It held:
> wrong-or-blank 6 → 13, and accuracy fell 11 points.
>
> Also: on voice notes, giving 1.3 *more* reasoning effort made it worse (73% → 59%) at 6× the cost.
> It talks itself into "I can't hear this". For voice input, use minimal effort.

**Post 5** (attach a screenshot of the PR checks: two red, one green, deploy skipped)
> It runs as a GitHub check. The PR that bumps the model fails, and the deploy never runs.
> Built for the @Meta AI developer hackathon. Open source: <repo link>. Bring your own tasks as a JSONL file.

Before posting: make the repo public so the link works. Keep the caveats when people ask: one speaker
for the real-voice run, synthetic voices for the main run.
