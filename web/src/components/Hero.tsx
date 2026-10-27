import { CircleAlert, CircleCheck } from "lucide-react";
import type { Site } from "../data";
import { BASE, CAND } from "../data";

type Check = {
  name: string;
  state: "pass" | "review";
  summary: string;
  href: string;
};

export function Hero({ site }: { site: Site }) {
  const { e1, e6, e3 } = site;
  const silent = e6.tests.find((t) => t.flag === "confident wrong or blank" && t.lang === "all");
  const std = e3.cost_per_1000 && e3.standard ? e3.cost_per_1000[e3.standard] : null;
  const con = e3.cost_per_1000 && e3.contributor ? e3.cost_per_1000[e3.contributor] : null;

  // Accuracy alone is inconclusive for voice notes; the failure-type shift is why a person must look.
  const checks: Check[] = [
    {
      name: "upgrade-gate / voice-notes",
      state: "review",
      summary: silent
        ? `Accuracy inconclusive. Wrong or blank with no warning: ${silent[BASE]} → ${silent[CAND]} of ${silent.tasks} clips.`
        : "Accuracy inconclusive.",
      href: "#/report/e6-audio",
    },
    {
      name: "upgrade-gate / text-and-documents",
      state: e1.decision === "go" ? "pass" : "review",
      summary: `${e1.after.n.toLocaleString("en-IN")} tasks in English, Hindi and Hinglish. No change in correct answers.`,
      href: "#/report/e1-upgrade",
    },
    {
      name: "upgrade-gate / contributor-mode",
      state: e3.decision === "go" ? "pass" : "review",
      summary:
        std && con
          ? `Same answers on every task. $${con.toFixed(2)} vs $${std.toFixed(2)} per 1,000 tasks.`
          : "Running.",
      href: "#/report/e3-contributor",
    },
  ];
  const review = checks.filter((c) => c.state === "review").length;

  return (
    <section id="top" className="relative">
      <div className="mx-auto grid max-w-6xl gap-14 px-4 pt-16 pb-20 sm:px-8 sm:pt-24 lg:grid-cols-[minmax(0,6fr)_minmax(0,5fr)] lg:gap-16 lg:pb-28">
        <div>
          <p className="mb-6 text-sm font-medium text-muted">
            Meta Muse Spark 1.2 → 1.3 · tested 27 October 2026
          </p>
          <h1 className="text-[clamp(2.6rem,6.4vw,4.9rem)] leading-[1.02] font-semibold tracking-[-0.035em] text-balance">
            Before you upgrade a model, check how it fails.
          </h1>
          <p className="mt-7 max-w-xl text-lg leading-relaxed text-muted text-pretty sm:text-xl">
            Upgrade Gate replays the same tasks on the old and new model, scores every answer against a known
            result, and holds the release with the exact cases behind it. Average accuracy hides the failures
            your users will notice.
          </p>
          <div className="mt-9 flex flex-wrap items-center gap-3">
            <a href="#audio" className="rounded-md bg-accent px-5 py-3 font-semibold text-accent-ink">
              See what we found
            </a>
            <a
              href="https://github.com/UtsavInTech/upgrade-gate"
              className="px-4 py-3 font-medium text-fg underline decoration-line underline-offset-4 transition-colors hover:decoration-fg"
            >
              Source on GitHub
            </a>
          </div>
        </div>

        <figure className="self-end">
          <div className="overflow-hidden rounded-lg border border-line bg-bg shadow-[0_12px_32px_-20px_rgba(16,24,40,0.35)]">
            <div className="flex items-center justify-between gap-3 border-b border-line px-4 py-3">
              <p className="min-w-0 truncate text-sm">
                <span className="font-semibold">Upgrade model</span>{" "}
                <span className="font-mono text-[13px] text-muted">
                  {BASE.replace("@low", "")} → {CAND.replace("@low", "")}
                </span>
              </p>
              <span className="shrink-0 text-xs text-faint">{checks.length} checks</span>
            </div>
            <ul className="divide-y divide-line">
              {checks.map((c) => (
                <li key={c.name}>
                  <a href={c.href} className="flex gap-3 px-4 py-3.5 transition-colors hover:bg-surface">
                    {c.state === "pass" ? (
                      <CircleCheck aria-label="Passed" className="mt-0.5 size-[18px] shrink-0 text-go" />
                    ) : (
                      <CircleAlert
                        aria-label="Review required"
                        className="mt-0.5 size-[18px] shrink-0 text-hold"
                      />
                    )}
                    <span className="min-w-0 flex-1">
                      <span className="flex items-baseline justify-between gap-3">
                        <span className="truncate font-mono text-[13px] font-medium">{c.name}</span>
                        <span className="shrink-0 text-xs text-accent">Details</span>
                      </span>
                      <span className="mt-0.5 block text-sm leading-snug text-muted">{c.summary}</span>
                    </span>
                  </a>
                </li>
              ))}
            </ul>
            <div
              className={`border-t border-line px-4 py-3 text-sm ${
                review ? "bg-hold-soft text-hold" : "bg-go-soft text-go"
              }`}
            >
              <span className="font-semibold">{review ? "Review required" : "All checks passed"}</span>
              {review > 0 && (
                <span className="opacity-80">
                  {" "}
                  · {review} check needs someone to read the failing answers
                </span>
              )}
            </div>
          </div>
          <figcaption className="mt-3 text-xs text-faint">
            The three runs on this page as they would appear on a pull request. Open a check to see its
            report.
          </figcaption>
        </figure>
      </div>
    </section>
  );
}
