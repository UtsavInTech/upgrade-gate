import { ArrowRight } from "lucide-react";
import { useEffect, useState } from "react";
import type { Site } from "../data";
import { pts } from "../data";
import type { Config } from "../voiceorder";
import { DEFAULT_SAMPLE, loadVoiceOrder } from "../voiceorder";
import { routeLabel } from "./SafeRouteSection";
import { speakersText, UpgradePath } from "./UpgradePath";
import { AnswerTicker } from "./AnswerTicker";
import { Mark, Odometer, Strike } from "./TextFx";

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

function fmt(n: number) {
  return n.toLocaleString("en-US");
}

export function Overview({ site }: { site: Site }) {
  const [cfg, setCfg] = useState<Config | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    loadVoiceOrder().then(setCfg, () => setFailed(true));
  }, []);
  const ds = decisions(site);
  const e6 = site.e6;
  const audio = e6.behaviour?.by_input?.audio;
  const acc12 = e6.accuracy?.["spark-1.2@low|audio"];
  const acc13 = e6.accuracy?.["spark-1.3@low|audio"];
  const real = site.e9?.sets?.real;
  const realDecision = site.e9 ? real?.gates[site.e9.direct]?.decision : undefined;

  return (
    <>
      {/* ---------- Hero ---------- */}
      <section className="mx-auto grid max-w-6xl grid-cols-[minmax(0,1fr)] items-center gap-10 px-4 pt-10 pb-16 sm:px-8 lg:grid-cols-[minmax(0,6fr)_minmax(0,6fr)] lg:gap-14 lg:pt-16">
        <div>
          <p className="stamp">Field report · Meta Muse Spark 1.2 → 1.3 · 27–31 Oct 2026</p>
          <h1 className="mt-5 text-[clamp(2.4rem,5vw,4rem)] leading-[1.02] text-balance">
            Spark 1.3 scored the same. <em>It just stopped saying</em>{" "}
            <Strike delay={700} label="no longer says:">“I can’t hear the audio.”</Strike>
            <a href="#note-1" className="fn" aria-label="Note 1">
              1
            </a>
          </h1>
          <p className="mt-6 max-w-lg text-lg leading-relaxed text-muted text-pretty">
            Upgrade Gate replays your tasks on the old and new model,{" "}
            <Mark delay={1300}>
              <span className="text-fg">blocks upgrades that start failing silently</span>
            </Mark>
            , and checks safer ways to ship.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <a
              href="#/voiceorder"
              className="group inline-flex items-center gap-2 rounded-full bg-fg px-5 py-3 font-semibold text-bg transition-transform duration-150 hover:-translate-y-px"
            >
              Try the example{" "}
              <ArrowRight aria-hidden className="size-4 transition-transform duration-150 group-hover:translate-x-0.5" />
            </a>
            <a
              href="#/report/e6-audio"
              className="inline-flex items-center rounded-full border border-fg/25 px-5 py-3 font-semibold transition-colors duration-150 hover:border-fg hover:bg-card"
            >
              Explore evidence
            </a>
          </div>
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

      {/* ---------- The two numbers ---------- */}
      {audio && acc12 && acc13 && (
        <section aria-labelledby="numbers-h" className="border-t border-line">
          <div className="mx-auto max-w-6xl px-4 py-16 sm:px-8 lg:py-24">
            <p className="stamp">
              Exhibit A · {audio.tasks} synthetic voice notes in English, Hindi and Hinglish · 3 tries each
            </p>
            <h2 id="numbers-h" className="mt-4 max-w-3xl text-[clamp(1.9rem,3.6vw,2.9rem)] leading-[1.08] text-balance">
              The number everyone checks barely moved. <em>The one that matters more than doubled.</em>
            </h2>

            <div className="mt-12 grid gap-10 border-y border-line py-10 sm:grid-cols-2 sm:gap-0">
              <figure className="sm:border-r sm:border-line sm:pr-10">
                <p className="display text-[clamp(3.2rem,8vw,6rem)] leading-none text-muted">
                  <Odometer value={acc12.correct} />
                  <span className="mx-3 text-faint">→</span>
                  <Odometer value={acc13.correct} delay={250} />
                </p>
                <figcaption className="mt-4 max-w-sm text-muted">
                  answers right, out of {fmt(acc12.total)}. Accuracy alone says{" "}
                  <span className="font-semibold text-hold">INCONCLUSIVE</span> and wants about{" "}
                  {fmt(Math.round((e6.tasks_needed ?? 0) / 100) * 100)} more clips to decide.
                  <a href="#note-2" className="fn" aria-label="Note 2">
                    2
                  </a>
                </figcaption>
              </figure>
              <figure className="sm:pl-10">
                <p className="display text-[clamp(3.2rem,8vw,6rem)] leading-none text-risk">
                  <Odometer value={audio.silent.baseline} delay={500} />
                  <span className="mx-3 opacity-60">→</span>
                  <Odometer value={audio.silent.candidate} delay={750} />
                </p>
                <figcaption className="mt-4 max-w-sm text-muted">
                  voice notes answered <span className="font-semibold text-fg">wrong or blank, with no warning</span>.
                  Paired exact test, p = 3 × 10⁻⁶. The gate says{" "}
                  <span className="font-semibold text-risk">NO-GO</span> with the same {audio.tasks} clips.
                </figcaption>
              </figure>
            </div>

            <div className="mt-12 grid gap-10 lg:grid-cols-[minmax(0,1fr)_17rem] lg:gap-16">
              <p className="prose-serif max-w-[38rem] text-[clamp(1.15rem,1.9vw,1.4rem)] leading-[1.6] text-pretty first-letter:float-left first-letter:mt-1 first-letter:mr-2 first-letter:font-[family-name:var(--font-display)] first-letter:text-[3.4em] first-letter:leading-[0.8] first-letter:text-risk">
                Spark 1.2 failed out loud. On {audio.abstain.baseline} notes it said it couldn’t hear the clip,
                sometimes while quoting the spoken words back. Spark 1.3 said that{" "}
                <Mark>{audio.abstain.candidate === 0 ? "not once" : `${audio.abstain.candidate} times`}</Mark>. It
                returned a pincode instead: correctly shaped, often a real one, and wrong. A shop’s format checks pass it,
                and the parcel goes to the wrong city. That is why Upgrade Gate counts <em>how</em> answers fail, not only
                how many.
              </p>
              <aside className="space-y-6 border-t border-line pt-6 text-sm leading-relaxed text-muted lg:border-t-0 lg:border-l lg:pt-0 lg:pl-6">
                <p id="note-1" className="scroll-mt-24">
                  <span className="fn mr-1 align-baseline text-[11px]">1</span>
                  On synthetic voices. With real people reading the same notes
                  {real && site.e9 ? ` (${real.describe[site.e9.baseline].clips} clips, ${speakersText(real.speakers)})` : ""}, 1.3’s
                  accuracy fell enough that the gate still says{" "}
                  <span className="font-semibold">{(realDecision ?? "no-go").toUpperCase()}</span>, but the
                  silent-failure rise did not repeat for the second speaker.
                </p>
                <p id="note-2" className="scroll-mt-24">
                  <span className="fn mr-1 align-baseline text-[11px]">2</span>
                  Normal approximation at 80% power; an estimate, not a guarantee.{" "}
                  <a href="#/findings" className="text-accent underline underline-offset-2">
                    Methods
                  </a>
                </p>
              </aside>
            </div>
          </div>
        </section>
      )}

      {/* ---------- Real answers ---------- */}
      <section aria-labelledby="words-h" className="border-t border-line bg-surface/60 py-16 lg:py-20">
        <div className="mx-auto mb-8 max-w-6xl px-4 sm:px-8">
          <p className="stamp">Exhibit B · straight from the saved run, unedited</p>
          <h2 id="words-h" className="mt-4 text-[clamp(1.9rem,3.6vw,2.9rem)] leading-[1.08]">
            In their <em>own</em> words.
          </h2>
          <p className="mt-3 max-w-2xl text-muted">
            Digits <span className="font-mono text-risk underline decoration-2 underline-offset-[3px]">underlined</span>{" "}
            are the ones the model got wrong; the line below each card is what the voice note actually said.
          </p>
        </div>
        <AnswerTicker />
      </section>

      {/* ---------- Decisions ---------- */}
      <section aria-labelledby="decisions-h" className="border-t border-line">
        <div className="mx-auto max-w-6xl px-4 py-16 sm:px-8 lg:py-24">
          <p className="stamp">One release policy, three ways to use Spark 1.3</p>
          <h2 id="decisions-h" className="mt-4 text-[clamp(1.9rem,3.6vw,2.9rem)] leading-[1.08]">
            One gate, three decisions <em>on the same upgrade.</em>
          </h2>
          <ol className="mt-10 border-t border-fg/80">
            {ds.map((d, i) => (
              <li
                key={d.what}
                className="grid gap-4 border-b border-line py-8 md:grid-cols-[3rem_minmax(0,11rem)_minmax(0,1fr)_minmax(0,16rem)] md:gap-8"
              >
                <span className="display text-2xl text-faint">{String(i + 1).padStart(2, "0")}</span>
                <p
                  className={`display text-[1.9rem] leading-none italic ${
                    d.decision === "no-go" ? "text-risk" : d.decision === "go" ? "text-go" : "text-hold"
                  }`}
                >
                  {d.decision === "no-go" ? "No-go" : d.decision === "go" ? "Go" : "Inconclusive"}
                </p>
                <div>
                  <h3 className="text-lg font-semibold">{d.what}</h3>
                  <p className="mt-2 leading-relaxed">{d.why}</p>
                  <p className="mt-3 text-sm leading-relaxed text-muted">{d.population}</p>
                </div>
                <div className="flex flex-col gap-3 text-sm text-muted md:border-l md:border-line md:pl-6">
                  <p className="font-mono text-[12.5px] leading-relaxed">{d.numbers}</p>
                  <a
                    href={d.href}
                    className="inline-flex items-center gap-1 font-medium text-fg underline decoration-fg/30 underline-offset-4 hover:decoration-fg"
                  >
                    {d.link} <ArrowRight aria-hidden className="size-3.5" />
                  </a>
                </div>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* ---------- Use it ---------- */}
      <section aria-labelledby="use-h" className="border-t border-line">
        <div className="mx-auto grid max-w-6xl gap-10 px-4 py-16 sm:px-8 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)] lg:py-24">
          <div>
            <p className="stamp">Five minutes, from an empty repo</p>
            <h2 id="use-h" className="mt-4 text-[clamp(1.9rem,3.6vw,2.9rem)] leading-[1.08]">
              Run it on your <em>own</em> tasks.
            </h2>
            <ol className="mt-8 space-y-5">
              {[
                ["Set up", "One command writes the model, the release policy, example tasks and a PR check."],
                ["Add your tasks", "20–50 real inputs from your app, each with its known answer."],
                ["Open a PR", "Change the model. The check replays both versions and fails on NO-GO."],
              ].map(([t, b], i) => (
                <li key={t} className="grid grid-cols-[2.25rem_1fr] gap-2">
                  <span className="display text-[1.7rem] leading-none text-accent italic">{i + 1}</span>
                  <span>
                    <span className="font-semibold">{t}.</span> <span className="text-muted">{b}</span>
                  </span>
                </li>
              ))}
            </ol>
            <p className="mt-8 text-sm text-muted">
              Already use Promptfoo or Braintrust?{" "}
              <a href="#/findings/compare" className="text-fg underline decoration-fg/30 underline-offset-4 hover:decoration-fg">
                How this differs
              </a>
            </p>
          </div>
          <pre className="self-start overflow-x-auto rounded-lg bg-[#1d1a16] p-6 font-mono text-[13px] leading-relaxed text-[#e9e2d3] ring-1 ring-black/5">
            <code>
              <span className="text-[#9a9081]"># five minutes, from an empty repo</span>
              {"\n"}pip install "git+https://github.com/UtsavInTech/upgrade-gate"
              {"\n"}upgrade-gate init --model spark-1.2@low
              {"\n"}upgrade-gate all --packs tasks/my_tasks.jsonl \{"\n"}  -b spark-1.2@low -c spark-1.3@low --budget 1 --yes
              {"\n\n"}
              <span className="text-[#9a9081]"># exit code: </span>
              <span className="text-[#7fd1a2]">0 GO</span>
              <span className="text-[#9a9081]"> · </span>
              <span className="text-[#ff9a85]">2 NO-GO</span>
              <span className="text-[#9a9081]"> · </span>
              <span className="text-[#f0c060]">3 INCONCLUSIVE</span>
            </code>
          </pre>
        </div>
      </section>
    </>
  );
}
