import { ArrowRight } from "lucide-react";
import { useEffect, useState } from "react";
import type { Site } from "../data";
import { pts } from "../data";
import type { Config } from "../voiceorder";
import { DEFAULT_SAMPLE, loadVoiceOrder } from "../voiceorder";
import { routeLabel } from "./SafeRouteSection";
import { speakersText, UpgradePath } from "./UpgradePath";
import { Verdict } from "./ui";

type Decision = {
  decision: string;
  what: string;
  why: string;
  population: string;
  numbers: string;
  href: string;
  link: string;
};

function decisions(site: Site): Decision[] {
  const out: Decision[] = [];
  const e6 = site.e6;
  const audio = e6.behaviour?.by_input?.audio;
  if (audio) {
    out.push({
      decision: e6.gate_decision ?? e6.decision,
      what: "Spark 1.3 listening to voice notes",
      why: `Accuracy barely moved, but wrong or blank answers with no warning rose from ${audio.silent.baseline} to ${audio.silent.candidate}.`,
      population: `${audio.tasks} synthetic-voice notes in English, Hindi and Hinglish, 3 tries each.${
        site.e9?.sets?.real?.gates[site.e9.direct]
          ? ` Real voices (${site.e9.sets.real.describe[site.e9.baseline].clips} notes, ${speakersText(site.e9.sets.real.speakers)}): ${site.e9.sets.real.gates[site.e9.direct].decision.replace("-", " ")} on accuracy; the silent-failure rise didn’t repeat for the second speaker.`
          : ""
      }`,
      numbers: `Said “I can’t hear”: ${audio.abstain.baseline} → ${audio.abstain.candidate}`,
      href: "#/report/e6-audio",
      link: "View failing examples",
    });
  }
  const e9 = site.e9;
  const synth = e9?.sets?.synth;
  if (e9?.status === "done" && synth?.overall) {
    const r = synth.describe[e9.route];
    const b = synth.describe[e9.baseline];
    const real = e9.sets.real;
    out.push({
      decision: synth.gates[e9.route]?.decision ?? "inconclusive",
      what: routeLabel(e9.route),
      why: `${pts(synth.overall.delta)} points more notes right than today’s app (95% range ${pts(synth.overall.ci_low)} to ${pts(synth.overall.ci_high)}), with no rise in silent failures.`,
      population: `${b.clips} synthetic-voice notes.${real ? ` Real voice (${real.describe[e9.baseline].clips} notes, ${speakersText(real.speakers)}): ${(real.gates[e9.route]?.decision ?? "").replace("-", " ")}.` : ""}`,
      numbers: `$${r.usd_per_1000_clips.toFixed(2)} vs $${b.usd_per_1000_clips.toFixed(2)} per 1,000 notes · slowest 10% ${((r.latency_ms_p90 ?? 0) / 1000).toFixed(0)} s vs ${((b.latency_ms_p90 ?? 0) / 1000).toFixed(0)} s`,
      href: "#/report/e9-route-synth",
      link: "Compare routes",
    });
  }
  const e3 = site.e3;
  if (e3.status === "done" && e3.cost_per_1000 && e3.standard && e3.contributor) {
    const std = e3.cost_per_1000[e3.standard];
    const con = e3.cost_per_1000[e3.contributor];
    out.push({
      decision: e3.decision ?? "inconclusive",
      what: "Spark 1.3 Contributor on text and documents",
      why: "Passed and failed exactly the same tasks as Standard (scores compared, not answer text).",
      population: "1,325 text, invoice and PDF tasks in English, Hindi and Hinglish",
      numbers: `About ${Math.round((1 - con / std) * 100)}% lower measured cost: $${con.toFixed(2)} vs $${std.toFixed(2)} per 1,000 tasks. Customer data is a separate policy decision.`,
      href: "#/report/e3-contributor",
      link: "View the tasks",
    });
  }
  return out;
}

export function Overview({ site }: { site: Site }) {
  const [cfg, setCfg] = useState<Config | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    loadVoiceOrder().then(setCfg, () => setFailed(true));
  }, []);
  const ds = decisions(site);

  return (
    <>
      <section className="mx-auto grid max-w-6xl grid-cols-[minmax(0,1fr)] items-center gap-10 px-4 pt-10 pb-16 sm:px-8 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)] lg:gap-12 lg:pt-14">
        <div>
          <p className="text-sm font-medium text-muted">Release checks for AI model upgrades</p>
          <h1 className="mt-3 text-[clamp(2.25rem,4.4vw,3.5rem)] leading-[1.05] font-semibold tracking-[-0.03em] text-balance">
            Test the upgrade. Choose the route.
          </h1>
          <p className="mt-5 max-w-md text-lg leading-relaxed text-muted text-pretty">
            Upgrade Gate replays your tasks on the old and new model, blocks upgrades that start failing silently, and
            checks safer ways to ship.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <a
              href="#/voiceorder"
              className="inline-flex items-center gap-2 rounded-md bg-accent px-5 py-3 font-semibold text-accent-ink transition-opacity duration-150 hover:opacity-90"
            >
              Try the example <ArrowRight aria-hidden className="size-4" />
            </a>
            <a
              href="#/report/e6-audio"
              className="inline-flex items-center rounded-md border border-line bg-card px-5 py-3 font-semibold transition-colors duration-150 hover:bg-surface"
            >
              Explore evidence
            </a>
          </div>
          <p className="mt-6 text-sm text-faint">Tested on Meta Muse Spark 1.2 → 1.3, 27–31 October 2026.</p>
        </div>
        <div>
          {cfg ? (
            <UpgradePath cfg={cfg} sampleId={DEFAULT_SAMPLE} site={site} compact />
          ) : failed ? (
            <div className="rounded-xl border border-line bg-card p-6 text-sm text-muted">
              The saved example couldn’t load.{" "}
              <button className="font-medium text-accent underline" onClick={() => window.location.reload()}>
                Retry
              </button>
            </div>
          ) : (
            <div className="h-[420px] animate-pulse rounded-xl bg-surface" aria-busy="true" />
          )}
        </div>
      </section>

      <section aria-labelledby="decisions-h" className="border-t border-line bg-card/50">
        <div className="mx-auto max-w-6xl px-4 py-16 sm:px-8">
          <h2 id="decisions-h" className="text-2xl font-semibold tracking-tight">
            One gate, three decisions on the same upgrade
          </h2>
          <p className="mt-2 max-w-2xl text-muted">
            The same release policy, applied to different ways of using Spark 1.3.
          </p>
          <ul className="mt-8 grid gap-5 lg:grid-cols-3">
            {ds.map((d) => (
              <li
                key={d.what}
                className={`flex flex-col rounded-xl border bg-card p-6 ${
                  d.decision === "no-go" ? "border-risk/40" : d.decision === "go" ? "border-go/40" : "border-line"
                }`}
              >
                <p className="flex items-center gap-2 text-lg">
                  <Verdict decision={d.decision} large />
                </p>
                <h3 className="mt-2 font-semibold">{d.what}</h3>
                <p className="mt-2 text-sm leading-relaxed">{d.why}</p>
                <dl className="mt-4 space-y-2 border-t border-line pt-4 text-sm">
                  <div>
                    <dt className="sr-only">Tested on</dt>
                    <dd className="text-muted">{d.population}</dd>
                  </div>
                  <div>
                    <dt className="sr-only">Cost and other numbers</dt>
                    <dd className="text-muted">{d.numbers}</dd>
                  </div>
                </dl>
                <a href={d.href} className="mt-auto inline-flex items-center gap-1 pt-5 text-sm font-medium text-accent hover:underline">
                  {d.link} <ArrowRight aria-hidden className="size-3.5" />
                </a>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section aria-labelledby="use-h" className="border-t border-line">
        <div className="mx-auto grid max-w-6xl gap-10 px-4 py-16 sm:px-8 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
          <div>
            <h2 id="use-h" className="text-2xl font-semibold tracking-tight">
              Run it on your own tasks
            </h2>
            <ol className="mt-6 space-y-4 text-sm">
              {[
                ["Set up", "One command writes the model, the release policy, example tasks and a PR check."],
                ["Add your tasks", "20–50 real inputs from your app, each with its known answer."],
                ["Open a PR", "Change the model. The check replays both versions and fails on NO-GO."],
              ].map(([t, b], i) => (
                <li key={t} className="flex gap-3">
                  <span className="mt-0.5 inline-flex size-6 shrink-0 items-center justify-center rounded-full bg-accent-soft text-xs font-semibold text-accent">
                    {i + 1}
                  </span>
                  <span>
                    <span className="font-semibold">{t}.</span> <span className="text-muted">{b}</span>
                  </span>
                </li>
              ))}
            </ol>
            <p className="mt-6 text-sm text-muted">
              Already use Promptfoo or Braintrust?{" "}
              <a href="#/findings/compare" className="text-accent underline-offset-2 hover:underline">
                How this differs
              </a>
            </p>
          </div>
          <pre className="overflow-x-auto rounded-xl bg-[#11181f] p-5 font-mono text-[13px] leading-relaxed text-[#d6dee6]">
            <code>
              <span className="text-[#7d8a96]"># five minutes, from an empty repo</span>
              {"\n"}pip install "git+https://github.com/UtsavInTech/upgrade-gate"
              {"\n"}upgrade-gate init --model spark-1.2@low
              {"\n"}upgrade-gate all --packs tasks/my_tasks.jsonl \{"\n"}  -b spark-1.2@low -c spark-1.3@low --budget 1 --yes
              {"\n\n"}
              <span className="text-[#7d8a96]"># exit code: 0 GO · 2 NO-GO · 3 INCONCLUSIVE</span>
            </code>
          </pre>
        </div>
      </section>
    </>
  );
}
