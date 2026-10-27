# Demo script (3 minutes)

Run `npm --prefix web run dev`, open http://127.0.0.1:5191 in a clean browser window at 1440×900, light mode.
Have the volume up for the clip. Times are targets, not rules.

| Time | Screen | Say |
|---|---|---|
| 0:00 | Home, top | "Companies upgrade models the way they upgrade libraries: the new version scores a bit better, so they ship it. We built a gate that checks *how* the new version fails before you ship." |
| 0:15 | Point at the pull-request checks on the right | "This is what a team sees on the pull request that bumps Meta's Muse Spark from 1.2 to 1.3. Two checks pass. Voice notes needs review. Let's open it." Click **Details** on `voice-notes`. |
| 0:30 | Report, top | "135 voice notes in English, Hindi and Hinglish, three tries each on both versions, $3. Pass rate: 84.8 to 83.6. On accuracy alone the gate says inconclusive; it would need about 9,000 more clips." |
| 0:50 | Scroll to the clip grid | "So we look at how each version fails. Every square is one voice note. Yellow is 1.2 saying 'I can't hear this audio'. On 1.3 that's gone, and the red and striped squares are answers that are wrong or blank with no warning. 18 clips became 42. That's significant with just 135 clips." |
| 1:20 | Click a striped square in the Hinglish row of Spark 1.3 (e.g. `audio-synth-extract-02-hinglish`) | Play the clip. "A customer reads out an order number. 1.2 gets it right twice and once says it can't hear. 1.3 returns blank fields three times, as if everything were fine. A support bot on 1.3 would save an empty order number and nobody would know." |
| 1:50 | Close the panel. Click the **Text, documents, Hindi** tab | "Second lesson: check the scorer before trusting the p-value. Our first scorer said 1.3 was 1.1 points better at Hindi, p of 0.00006." |
| 2:05 | Back to Home → Scoring section, the "Somwar" example | "1.2 had written 'Somwar'; our answer key said 'Somvar'. Same word. Once we scored correctness and format separately, the improvement went to zero." |
| 2:25 | Click the **Contributor mode** tab in the report | "Third: Meta's Contributor mode. Same answers on all 1,325 tasks at a tenth of a dollar per thousand tasks instead of $1.80." |
| 2:40 | Home → How it works | "It runs from one command in CI. Exit code 0 ships, 2 blocks, 3 asks for more evidence, and every decision links to the answers behind it. Every paid call is checked against a spending cap first." |
| 2:55 | Back to the PR checks | "Upgrade Gate: before you upgrade a model, check how it fails." |

**If E7 (real voices) is done before recording:** at 1:40 add one line with its result, e.g. "We repeated this with real recorded voices and the same pattern held" (or say plainly that it didn't).

**Recording tips:** hide the bookmarks bar, zoom the browser to 110% so text reads on small screens, record the screen at 1080p, and keep the cursor still while talking.
