import { motion } from "motion/react";
import { Check, X } from "lucide-react";
import type { E1 } from "../data";
import { LANG_LABEL, pts, pval } from "../data";
import { ScorerExplainer } from "./ScorerExplainer";
import { Reveal, Section, Verdict } from "./ui";

export function ScoringSection({ e1 }: { e1: E1 }) {
  const before = e1.before;
  const langs = e1.slices.filter((s) => s.key === "lang" && s.before && s.after);
  const max = Math.max(0.03, ...langs.map((s) => Math.abs(s.before!.delta)));

  return (
    <Section
      id="scoring"
      eyebrow="Text, documents and Hindi · 7,950 calls"
      title="Our own scorer invented an improvement."
      lede={
        <>
          The first run said 1.3 was clearly better at Hindi. Reading the answers showed 1.2 had been right in
          a different spelling. We split <em>correct</em> from <em>correct format</em> and rescored the saved
          answers, with no new calls.
        </>
      }
    >
      <Reveal className="grid items-stretch gap-4 md:grid-cols-[1fr_auto_1fr]">
        <div className="rounded-lg border border-line p-6 sm:p-8">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-muted">Before: exact-match scorer</p>
            <span className="text-xs font-bold tracking-[0.08em] text-risk">NOT REAL</span>
          </div>
          <p className="mt-3 text-[clamp(3rem,7vw,5rem)] leading-none font-semibold tracking-[-0.04em] text-faint">
            {before ? pts(before.delta, 2) : "–"}
            <span className="ml-1 text-2xl tracking-normal">pts</span>
          </p>
          <p className="mt-4 text-sm text-muted">
            1.3 “better”, p = {before ? pval(before.p) : "–"}. Looks significant.
          </p>
        </div>
        <div className="hidden items-center text-3xl text-faint md:flex" aria-hidden>
          →
        </div>
        <div className="rounded-lg border border-line bg-surface p-6 sm:p-8">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-muted">After: correct answers, any spelling</p>
            <Verdict decision={e1.decision} />
          </div>
          <p className="mt-3 text-[clamp(3rem,7vw,5rem)] leading-none font-semibold tracking-[-0.04em]">
            {pts(e1.after.delta, 2)}
            <span className="ml-1 text-2xl tracking-normal text-muted">pts</span>
          </p>
          <p className="mt-4 text-sm text-muted">
            {e1.per_answer["spark-1.2@low"]?.correct.toLocaleString("en-IN")} vs{" "}
            {e1.per_answer["spark-1.3@low"]?.correct.toLocaleString("en-IN")} of{" "}
            {e1.per_answer["spark-1.2@low"]?.total.toLocaleString("en-IN")} answers correct.
          </p>
        </div>
      </Reveal>

      <ScorerExplainer e1={e1} />

      <div className="mt-14 grid gap-10 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
        <Reveal>
          <figure>
            <figcaption className="mb-5">
              <h3 className="text-lg font-semibold">Where the fake gain came from</h3>
              <p className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted">
                <span>1.3 minus 1.2, points</span>
                <span className="inline-flex items-center gap-1.5">
                  <span className="inline-block h-2.5 w-4 rounded-[3px] bg-faint/45" aria-hidden /> old scorer
                </span>
                <span className="inline-flex items-center gap-1.5">
                  <span className="inline-block h-3 w-[3px] rounded-full bg-accent" aria-hidden /> corrected
                </span>
              </p>
            </figcaption>
            <ul className="space-y-5">
              {langs.map((s, k) => {
                const b = s.before!.delta;
                const a = s.after!.delta;
                return (
                  <li key={s.value} className="grid grid-cols-[76px_minmax(0,1fr)_92px] items-center gap-3">
                    <span className="text-sm font-medium">{LANG_LABEL[s.value]}</span>
                    <div className="relative h-7 rounded-md bg-surface" aria-hidden>
                      <motion.div
                        className="absolute inset-y-1 left-1 rounded-[4px] bg-faint/45"
                        initial={{ width: 0 }}
                        whileInView={{ width: `max(0px, calc(${(b / max) * 100}% - 8px))` }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.7, delay: 0.1 * k }}
                      />
                      <span
                        className="absolute inset-y-0.5 w-[3px] rounded-full bg-accent"
                        style={{ left: `calc(${(a / max) * 100}% + 4px)` }}
                      />
                    </div>
                    <span className="text-right text-sm">
                      <span className="text-faint">{pts(b)}</span>
                      <span className="text-faint"> → </span>
                      <span className="font-semibold">{pts(a)}</span>
                    </span>
                  </li>
                );
              })}
            </ul>
            <p className="mt-5 text-sm text-muted">
              English was at 100% for both versions, so it could not move.
            </p>
          </figure>
        </Reveal>

        <Reveal delay={0.05}>
          <h3 className="mb-5 text-lg font-semibold">Answers the old scorer rejected</h3>
          <ul className="divide-y divide-line rounded-lg border border-line">
            {e1.examples.slice(0, 5).map((ex) => (
              <li
                key={ex.task_id + ex.candidate}
                className="grid gap-3 p-4 sm:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]"
              >
                <div className="min-w-0">
                  <p className="text-xs text-faint">
                    {LANG_LABEL[ex.lang]} · {ex.category}
                  </p>
                  <p className="mt-1 font-mono text-sm break-words">
                    {ex.answer.length > 90 ? ex.answer.slice(0, 90) + "…" : ex.answer}
                  </p>
                </div>
                <div className="space-y-1.5 text-sm">
                  <p className="flex items-start gap-2 text-muted">
                    <X aria-hidden className="mt-0.5 size-4 shrink-0 text-risk" />
                    <span>Old: rejected</span>
                  </p>
                  <p className="flex items-start gap-2">
                    <Check aria-hidden className="mt-0.5 size-4 shrink-0 text-go" />
                    <span>
                      Now: correct
                      {ex.strict === false ? <span className="text-muted">, format not exact</span> : ""}
                    </span>
                  </p>
                </div>
              </li>
            ))}
          </ul>
        </Reveal>
      </div>
    </Section>
  );
}
