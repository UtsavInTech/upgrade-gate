import { motion } from "motion/react";
import type { E4 } from "../data";
import { pts, pval } from "../data";
import { Section, Stat } from "./ui";

// One bar per effort level: share of answers that were correct. Under it, how often the model said it
// couldn't hear the clip, and the cost. Bars start at zero so the drop isn't exaggerated.
export function EffortSection({ e4 }: { e4: E4 }) {
  const levels = e4.levels;
  const first = levels[0];
  const last = levels[levels.length - 1];
  const pct = (l: E4["levels"][number]) => (l.correct / Math.max(1, l.answers)) * 100;
  const deny = (l: E4["levels"][number]) => l.modes["says it can't hear"] ?? 0;
  const maxDeny = Math.max(1, ...levels.map(deny));
  const end = e4.minimal_vs_xhigh;

  return (
    <Section
      id="effort"
      eyebrow={`Reasoning effort · ${e4.calls.toLocaleString("en-IN")} calls · $${e4.fresh_cost_usd.toFixed(2)}`}
      title="More thinking, worse listening."
      lede={
        <>
          Spark 1.3 lets you choose how long it thinks before answering. On the same {e4.clips} voice notes,
          every step up in effort cost more and got fewer right. Given more time, it increasingly decides it
          can’t hear the clip at all.
        </>
      }
    >
      <div className="grid gap-10 sm:grid-cols-3">
        <Stat
          value={
            <>
              {pct(first).toFixed(1)}% <span className="text-faint">→</span>{" "}
              <span className="text-risk">{pct(last).toFixed(1)}%</span>
            </>
          }
          label={`Correct, ${first.level} → ${last.level} effort`}
          sub={`${pts(end.delta)} pts per clip, p = ${pval(end.p)} (${end.regressions} clips worse, ${end.improvements} better)`}
        />
        <Stat
          value={
            <>
              {deny(first)} <span className="text-faint">→</span> {deny(last)}
            </>
          }
          label="Answers saying “I can’t hear the audio”"
          sub={`of ${last.answers} answers at each level`}
        />
        <Stat
          value={
            <>
              ${first.cost_per_1000.toFixed(2)} <span className="text-faint">→</span> $
              {last.cost_per_1000.toFixed(2)}
            </>
          }
          label="Cost per 1,000 clips"
          sub={`${first.avg_output_tokens} → ${last.avg_output_tokens} output tokens per answer`}
        />
      </div>

      <figure className="mt-14 rounded-lg border border-line p-5 sm:p-7">
        <figcaption>
          <h3 className="text-lg font-semibold">Correct answers at each effort level</h3>
          <p className="text-sm text-muted">
            Spark 1.3 Contributor, {e4.clips} clips × 3 tries per level. Answers cut off by the token limit
            count as wrong here.
          </p>
        </figcaption>
        <div className="mt-8 grid grid-cols-5 gap-3 sm:gap-6">
          {levels.map((l, i) => (
            <div key={l.level} className="flex flex-col items-center">
              <div className="relative flex h-56 w-full max-w-24 items-end rounded-md bg-surface">
                <motion.div
                  className="w-full rounded-[4px] bg-[var(--s-correct)]"
                  initial={{ height: 0 }}
                  whileInView={{ height: `${pct(l)}%` }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.7, delay: i * 0.08, ease: [0.2, 0.7, 0.2, 1] }}
                />
                <span className="absolute inset-x-0 top-2 text-center text-sm font-semibold">
                  {pct(l).toFixed(1)}%
                </span>
              </div>
              <p className="mt-3 text-sm font-semibold capitalize">{l.level}</p>
              <div className="mt-3 h-1.5 w-full max-w-24 overflow-hidden rounded-full bg-surface" aria-hidden>
                <div
                  className="h-full rounded-full bg-[var(--s-deny)]"
                  style={{ width: `${(deny(l) / maxDeny) * 100}%` }}
                />
              </div>
              <p className="mt-1 text-center text-xs text-muted">
                {deny(l)} “can’t hear”
                <br />${l.cost_per_1000.toFixed(2)} / 1k
              </p>
            </div>
          ))}
        </div>
      </figure>

      <div className="mt-10 grid gap-8 md:grid-cols-2">
        <div className="border-t-2 border-go pt-5">
          <h3 className="font-semibold">What to do with it</h3>
          <p className="mt-3 text-muted">
            For voice input, set{" "}
            <code className="font-mono text-sm text-fg">reasoning_effort: "minimal"</code>. On these clips it
            was the most accurate setting and about six times cheaper than the highest.
          </p>
        </div>
        <div className="border-t-2 border-line pt-5">
          <h3 className="font-semibold">How far it goes</h3>
          <p className="mt-3 text-muted">
            Text-to-speech clips, Contributor mode (the same model served more cheaply), one run on 28 October
            2026. On text tasks every effort level scored 100%, so this is about listening, not reasoning in
            general.
          </p>
        </div>
      </div>
    </Section>
  );
}
