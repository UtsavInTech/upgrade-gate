import { AnimatePresence, motion } from "motion/react";
import { Mic, Volume2 } from "lucide-react";
import { useState } from "react";
import type { AudioExample, E6 } from "../data";
import { BASE, CAND, LANG_LABEL, formatExpected, pval, shortModel } from "../data";
import { FailureChart } from "./FailureChart";
import { ModeChip, Reveal, Section, Stat, Verdict } from "./ui";

const KIND: Record<string, string> = {
  math: "Spoken maths",
  extract: "Order voice note",
  intent: "Customer request",
};

export function AudioSection({ e6 }: { e6: E6 }) {
  const acc = (m: string) => e6.accuracy[`${m}|audio`];
  const text = (m: string) => e6.accuracy[`${m}|text`];
  const silent = e6.tests.find((t) => t.flag === "confident wrong or blank" && t.lang === "all");
  const deny = e6.tests.find((t) => t.flag === "says it can't hear" && t.lang === "all");

  return (
    <Section
      id="audio"
      index="01"
      eyebrow="Voice notes · the finding"
      title={
        <>
          Same accuracy.
          <br />
          <span className="text-muted">Different failures.</span>
        </>
      }
      lede={
        <>
          Meta’s docs warn that audio in Spark 1.3 is “not fully supported”. We sent 135 voice clips in
          English, Hindi and Hinglish to both versions. 1.3 gets as many right, but when it misunderstands, it
          no longer says so.
        </>
      }
    >
      <Reveal className="grid gap-10 sm:grid-cols-3">
        <Stat
          value={
            <>
              {acc(BASE).correct} <span className="text-faint">vs</span> {acc(CAND).correct}
            </>
          }
          label="Correct audio answers"
          sub={`of ${acc(BASE).total} each. Same words as text: ${text(BASE).correct} and ${text(CAND).correct}.`}
        />
        {silent && (
          <Stat
            value={
              <>
                {silent[BASE]} <span className="text-faint">→</span>{" "}
                <span className="text-risk">{silent[CAND]}</span>
              </>
            }
            label="Tasks answered wrong or blank, with no warning"
            sub={`p = ${pval(silent.p)}, paired across ${silent.tasks} clips`}
          />
        )}
        {deny && (
          <Stat
            value={
              <>
                {deny[BASE]} <span className="text-faint">→</span> {deny[CAND]}
              </>
            }
            label="Tasks where it said “I can’t hear the audio”"
            sub={`p = ${pval(deny.p)}. 1.2 admits it; 1.3 never does.`}
          />
        )}
      </Reveal>

      <Reveal delay={0.05} className="mt-14">
        <FailureChart e6={e6} />
      </Reveal>

      <Reveal delay={0.05} className="mt-6 grid gap-4 md:grid-cols-2">
        <div className="rounded-2xl border border-line p-6">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold">Checking accuracy only</h3>
            <Verdict decision={e6.decision} />
          </div>
          <p className="mt-3 text-muted">
            Pass rates differ by a few answers, inside the noise. To decide on accuracy alone the gate would
            need about{" "}
            <span className="font-semibold text-fg">
              {(e6.tasks_needed ?? 0).toLocaleString("en-IN")} more clips
            </span>
            .
          </p>
        </div>
        <div className="rounded-2xl border border-risk/40 bg-risk-soft p-6">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold">Checking how it fails</h3>
            <Verdict decision="risk" />
          </div>
          <p className="mt-3 text-muted">
            With the same 135 clips, the switch from “I can’t hear” to silent wrong answers is clear (
            <span className="font-semibold text-fg">p = {silent ? pval(silent.p) : "–"}</span>). A voice bot
            on 1.3 would store wrong or empty order numbers without flagging them.
          </p>
        </div>
      </Reveal>

      <Reveal delay={0.05} className="mt-16">
        <Examples examples={e6.examples} />
      </Reveal>

      <p className="mt-8 text-sm text-faint">
        Synthetic voices (macOS text-to-speech), reasoning effort low, one run on 27 Oct 2026. The
        failure-type rules were written after reading the answers, so this is exploratory until it is repeated
        on fresh clips.
      </p>
    </Section>
  );
}

function Examples({ examples }: { examples: AudioExample[] }) {
  const [i, setI] = useState(0);
  const ex = examples[i];
  if (!ex) return null;
  return (
    <div>
      <div className="mb-6 flex items-end justify-between gap-4">
        <div>
          <h3 className="text-2xl font-semibold tracking-tight">Listen for yourself</h3>
          <p className="text-muted">Real clips from the run, with every answer each version gave.</p>
        </div>
      </div>
      <div className="grid gap-4 lg:grid-cols-[280px_minmax(0,1fr)]">
        <div
          role="tablist"
          aria-label="Examples"
          className="flex gap-2 overflow-x-auto pb-1 lg:flex-col lg:overflow-visible"
        >
          {examples.map((e, k) => (
            <button
              key={e.task_id}
              role="tab"
              aria-selected={k === i}
              onClick={() => setI(k)}
              className={`shrink-0 rounded-xl border px-4 py-3 text-left transition-colors ${
                k === i ? "border-accent bg-accent-soft" : "border-line hover:bg-surface"
              }`}
            >
              <span className="block text-sm font-semibold">{KIND[e.kind]}</span>
              <span className="block text-xs text-muted">
                {LANG_LABEL[e.lang]} ·{" "}
                {e.why === "silent" ? "1.3 fails silently" : "1.2 “can’t hear”, still answers"}
              </span>
            </button>
          ))}
        </div>

        <AnimatePresence mode="wait">
          <motion.article
            key={ex.task_id}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.22 }}
            className="rounded-2xl border border-line bg-surface p-5 sm:p-7"
          >
            <div className="flex flex-wrap items-center gap-3 text-sm text-muted">
              <Mic aria-hidden className="size-4" />
              <span>
                {LANG_LABEL[ex.lang]} · voice “{ex.voice}”
              </span>
              <span className="font-mono text-xs text-faint">{ex.task_id}</span>
            </div>
            <audio controls preload="none" src={ex.audio} className="mt-4 w-full">
              <a href={ex.audio}>Download the clip</a>
            </audio>
            <div className="mt-5 grid gap-4 sm:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
              <div>
                <p className="mb-1 flex items-center gap-1.5 text-xs font-semibold tracking-wide text-faint uppercase">
                  <Volume2 aria-hidden className="size-3.5" /> What the clip says
                </p>
                <p className="leading-relaxed">{ex.transcript}</p>
              </div>
              <div>
                <p className="mb-1 text-xs font-semibold tracking-wide text-faint uppercase">
                  Correct answer
                </p>
                <p className="font-mono text-sm leading-relaxed">{formatExpected(ex.expected)}</p>
              </div>
            </div>
            <div className="mt-6 grid gap-4 md:grid-cols-2">
              {[BASE, CAND].map((m) => (
                <div key={m} className="rounded-xl bg-bg p-4">
                  <p className="mb-3 font-semibold">{shortModel(m)}</p>
                  <ol className="space-y-3">
                    {ex.answers[m].map((a, k) => (
                      <li key={k} className="border-t border-line pt-3 first:border-0 first:pt-0">
                        <div className="mb-1 flex items-center justify-between gap-2">
                          <span className="text-xs text-faint">Try {k + 1}</span>
                          <ModeChip mode={a.mode} />
                        </div>
                        <p className="font-mono text-[13px] leading-relaxed break-words text-fg/90">
                          {a.text.length > 220 ? a.text.slice(0, 220) + "…" : a.text || "(empty)"}
                        </p>
                        {a.says_cant_hear && a.mode === "correct" && (
                          <p className="mt-1 text-xs text-hold">
                            Says it can’t hear the audio, then answers from it.
                          </p>
                        )}
                      </li>
                    ))}
                  </ol>
                </div>
              ))}
            </div>
          </motion.article>
        </AnimatePresence>
      </div>
    </div>
  );
}
