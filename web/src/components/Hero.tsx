import { motion } from "motion/react";
import { ArrowDown, ArrowRight } from "lucide-react";
import type { Site } from "../data";
import { BASE, CAND } from "../data";
import { Verdict } from "./ui";

export function Hero({ site }: { site: Site }) {
  const { e1, e6, e3 } = site;
  const silent = e6.tests.find((t) => t.flag === "confident wrong or blank" && t.lang === "all");
  const calls = e1.calls + e6.calls + (e3.calls ?? 0);
  const ratio =
    e3.cost_per_1000 && e3.standard && e3.contributor
      ? Math.round(e3.cost_per_1000[e3.standard] / e3.cost_per_1000[e3.contributor])
      : null;

  const checks = [
    {
      href: "#audio",
      area: "Voice notes",
      detail: "English, Hindi, Hinglish audio",
      finding: silent ? `Silent failures ${silent[BASE]} → ${silent[CAND]} tasks` : "—",
      decision: "risk",
    },
    {
      href: "#scoring",
      area: "Text, documents, Hindi",
      detail: "1,325 tasks after fixing the scorer",
      finding: "No change in correct answers",
      decision: e1.decision,
    },
    {
      href: "#cost",
      area: "Contributor mode",
      detail: "Same model, cheaper serving mode",
      finding: ratio ? `Same answers at 1/${ratio} the cost` : "Running",
      decision: e3.decision ?? "inconclusive",
    },
  ];

  return (
    <section id="top" data-slide className="relative overflow-hidden">
      <div className="mx-auto grid max-w-6xl gap-14 px-4 pt-16 pb-20 sm:px-8 sm:pt-24 lg:grid-cols-[minmax(0,6fr)_minmax(0,5fr)] lg:gap-16 lg:pb-28">
        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.2, 0.7, 0.2, 1] }}
        >
          <p className="mb-6 inline-flex items-center gap-2 rounded-full bg-accent-soft px-3 py-1 text-sm font-medium text-accent">
            Meta Muse Spark 1.2 → 1.3
          </p>
          <h1 className="text-[clamp(2.6rem,6.4vw,4.9rem)] leading-[1.02] font-semibold tracking-[-0.035em] text-balance">
            Before you upgrade a model, check <span className="text-accent">how</span> it fails.
          </h1>
          <p className="mt-7 max-w-xl text-lg leading-relaxed text-muted text-pretty sm:text-xl">
            Upgrade Gate replays the same tasks on the old and new model, scores every answer against a known
            result, and gives a GO or NO-GO with the exact cases behind it. Average accuracy hides the
            failures your users will notice.
          </p>
          <div className="mt-9 flex flex-wrap items-center gap-3">
            <a
              href="#audio"
              className="inline-flex items-center gap-2 rounded-lg bg-accent px-5 py-3 font-semibold text-accent-ink transition-transform active:scale-[0.98]"
            >
              See what we found
              <ArrowDown aria-hidden className="size-4" />
            </a>
            <a
              href="https://github.com/UtsavInTech/upgrade-gate"
              className="inline-flex items-center gap-2 rounded-lg px-4 py-3 font-medium text-fg transition-colors hover:bg-surface"
            >
              Source on GitHub
              <ArrowRight aria-hidden className="size-4" />
            </a>
          </div>
        </motion.div>

        <motion.aside
          aria-label="Release checklist"
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.15, ease: [0.2, 0.7, 0.2, 1] }}
          className="self-end rounded-2xl border border-line bg-surface p-2"
        >
          <div className="flex items-baseline justify-between px-4 pt-3 pb-4">
            <h2 className="text-sm font-semibold">Release checklist</h2>
            <span className="font-mono text-xs text-faint">1.2 → 1.3</span>
          </div>
          <ol className="space-y-1.5">
            {checks.map((c, i) => (
              <motion.li
                key={c.area}
                initial={{ opacity: 0, x: 12 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.4, delay: 0.35 + i * 0.12 }}
              >
                <a
                  href={c.href}
                  className="group grid grid-cols-[1fr_auto] items-center gap-x-4 gap-y-1 rounded-xl bg-bg px-4 py-4 transition-colors hover:bg-surface-2"
                >
                  <span className="font-semibold">{c.area}</span>
                  <span className="row-span-2">
                    <Verdict decision={c.decision} />
                  </span>
                  <span className="text-sm text-muted">
                    {c.finding} <span className="text-faint">· {c.detail}</span>
                  </span>
                </a>
              </motion.li>
            ))}
          </ol>
          <dl className="grid grid-cols-3 gap-2 px-4 pt-5 pb-3 text-sm">
            <div>
              <dt className="text-faint">API calls</dt>
              <dd className="font-semibold">{calls.toLocaleString("en-IN")}</dd>
            </div>
            <div>
              <dt className="text-faint">Total spend</dt>
              <dd className="font-semibold">${site.spend.total_usd.toFixed(2)}</dd>
            </div>
            <div>
              <dt className="text-faint">Languages</dt>
              <dd className="font-semibold">EN · HI · Hinglish</dd>
            </div>
          </dl>
        </motion.aside>
      </div>
    </section>
  );
}
