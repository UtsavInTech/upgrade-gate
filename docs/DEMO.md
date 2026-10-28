# Demo script (3 minutes)

Have two tabs ready at 1440×900, light mode, volume up:
1. The GitHub pull request `upgrade/spark-1.3` with its checks finished.
2. The site: `npm --prefix web run dev`, then http://127.0.0.1:5191/#/report/e6-audio.

| Time | Screen | Say |
|---|---|---|
| 0:00 | Site `#/voiceorder`, the Hindi Ahmedabad note selected, play 3 s of it | "This is VoiceOrder, a voice-order helper for an Indian shop on Meta's Muse Spark. A customer says their order number and pincode in Hindi." |
| 0:12 | The two order cards | "Today's model saves 452089, which is right. The new version, 1.3, saves 380015: a real Ahmedabad pincode, just the wrong one. The shop's checks pass both. That parcel goes to the wrong address." |
| 0:25 | GitHub PR "Upgrade to Muse Spark 1.3", the one-line diff in `release/model.json` | "Upgrading is one line. This pull request moves VoiceOrder from 1.2 to 1.3." |
| 0:35 | The checks box: two red, one green, **deploy skipped** | "Upgrade Gate replays our saved tasks on both versions. Text and documents pass. Voice notes fail, and the deploy step never runs." |
| 0:30 | Click `upgrade-gate / voice-notes` → the job summary | "Accuracy alone was inconclusive: about the same number right. What changed is how it fails. On 135 voice notes, answers that are wrong or blank with no warning went from 18 to 42. 1.2 often said 'I can't hear this'; 1.3 never does." |
| 0:55 | Scroll to **One failing case** | "A customer leaves a Hindi voice note with their pincode. 1.2 gets it right. 1.3 returns 380015, a real Ahmedabad pincode, just the wrong one. It's correctly shaped, so a schema check passes it. That's the failure that reaches your database." |
| 1:15 | Switch to the site report, Voice notes tab, the clip grid | "Every square is one voice note. Yellow is 1.2 saying it can't hear. On 1.3 that becomes red: wrong, and no warning." Click one red square, play the clip, show both versions' three tries. |
| 1:45 | **Real voices** tab | "Synthetic voices are clean, so we wrote the prediction down first and recorded 45 lines in a real voice. Accuracy fell 11 points, which alone blocks the upgrade, and 1.3 started returning blanks. The silent-failure rise itself is borderline at that size; we say so on the page." |
| 2:05 | Home → "More thinking, worse listening" chart | "Spark 1.3 lets you set reasoning effort. On voice notes, more thinking was worse: 73% at minimal, 59% at the highest, at six times the cost. It talks itself into 'I can't hear this'. That comparison was picked after seeing the data, so it's a strong trend, worth testing on your own clips." |
| 2:25 | Home → scorer section ("Somwar") | "We also caught our own mistake: our first scorer said 1.3 was significantly better at Hindi. It was spelling. The tool shows rejected answers next to every score so you can check the rule." |
| 2:40 | Report → Contributor mode tab | "And Contributor mode scored the same on every task at a tenth of a dollar per thousand tasks instead of $1.80." |
| 2:50 | Back to the PR checks | "Upgrade Gate: before you upgrade a model, check how it fails. Open source; bring your own tasks as a JSONL file." |

**Before recording:** make the repo public and add a branch-protection rule on `main` requiring the three
`upgrade-gate / …` checks, so the PR page also shows *Merging is blocked*. Hide the bookmarks bar, zoom to 110%,
record at 1080p, keep the cursor still while talking.
