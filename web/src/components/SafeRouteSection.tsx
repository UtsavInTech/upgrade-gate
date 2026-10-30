import type { E6, E9 } from "../data";
import { pts, shortModel } from "../data";
import { Reveal, Section, Verdict } from "./ui";

// Every number here comes from site.json (scripts/export_web.py: e6 and e9, which read the saved
// gate files and experiments/out/e9_route.json + loss_scenario_*.json).

export function routeLabel(id: string): string {
  return id.startsWith("transcribe+") ? "Voice Transcribe → " + shortModel(id.slice(11)) : shortModel(id) + " listens";
}

export function SafeRouteSection({ e9, e6 }: { e9?: E9; e6: E6 }) {
  const synth = e9?.sets?.synth;
  const real = e9?.sets?.real;
  if (!e9 || e9.status !== "done" || !synth?.overall) return null;
  const silent6 = e6.behaviour?.by_input?.audio?.silent;
  const cols = [
    { id: e9.baseline, how: "Today’s app", decision: null as string | null, silent: silent6?.baseline },
    { id: e9.direct, how: "The plain upgrade", decision: synth.gates[e9.direct]?.decision ?? null, silent: silent6?.candidate },
    { id: e9.route, how: "Write it down, then read", decision: synth.gates[e9.route]?.decision ?? null, silent: synth.overall.silent.candidate },
  ];
  const n = synth.describe[e9.baseline]?.clips ?? 0;
  const rows: { label: string; get: (id: string, silent?: number) => string }[] = [
    { label: "Notes right (most of 3 tries)", get: (id) => `${synth.describe[id].clips_correct_majority} / ${n}` },
    { label: "Order number right", get: (id) => synth.describe[id].order_number_right.replace("/", " / ") },
    { label: "Pincode right", get: (id) => synth.describe[id].pincode_right.replace("/", " / ") },
    { label: "Wrong or blank, no warning", get: (_, s) => (s === undefined ? "–" : `${s} / ${n}`) },
    { label: "Said “I can’t hear”", get: (id) => String(synth.describe[id].types.abstain ?? 0) },
    { label: "Slowest 10% take", get: (id) => `${((synth.describe[id].latency_ms_p90 ?? 0) / 1000).toFixed(1)} s` },
    { label: "Cost per 1,000 notes", get: (id) => `$${synth.describe[id].usd_per_1000_clips.toFixed(2)}` },
  ];
  const loss = synth.loss?.by_route;
  const lossReal = real?.loss?.by_route;
  const realD = real?.describe;
  const inr = (v?: [number, number]) => (v ? `₹${v[0].toLocaleString("en-IN")}–${v[1].toLocaleString("en-IN")}` : "–");

  return (
    <Section
      id="safe-route"
      eyebrow="Voice notes · the way through"
      title="Blocked isn’t the end. The same gate approved a safer route."
      lede={
        <>
          Meta’s docs point audio work to Muse Voice Transcribe. We tested that on the same notes, with the rules
          written down before the first call, and let the unchanged gate and policy decide.
        </>
      }
    >
      <Reveal className="overflow-x-auto rounded-lg border border-line bg-card">
        <table className="w-full min-w-[620px] border-collapse text-left text-sm">
          <caption className="sr-only">Three ways to read the same {n} synthetic voice notes, 3 tries each</caption>
          <thead>
            <tr className="border-b border-line">
              <th scope="col" className="px-5 py-4 text-xs font-normal text-faint">
                {n} synthetic-voice notes, 3 tries each
              </th>
              {cols.map((c) => (
                <th key={c.id} scope="col" className={`px-5 py-4 ${c.decision === "go" ? "bg-go-soft" : ""}`}>
                  <span className="block font-semibold">{routeLabel(c.id)}</span>
                  <span className="mt-0.5 flex items-center gap-2 text-xs font-normal text-muted">
                    {c.how}
                    {c.decision && <Verdict decision={c.decision} />}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.label} className="border-t border-line">
                <th scope="row" className="px-5 py-3 font-normal text-muted">
                  {row.label}
                </th>
                {cols.map((c) => (
                  <td key={c.id} className={`px-5 py-3 font-medium tabular-nums ${c.decision === "go" ? "bg-go-soft/50" : ""}`}>
                    {row.get(c.id, c.silent)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </Reveal>
      <p className="mt-3 text-sm text-muted">
        Against today’s app: <span className="font-semibold text-fg">{pts(synth.overall.delta)} points</span> correct (95% range{" "}
        {pts(synth.overall.ci_low)} to {pts(synth.overall.ci_high)}), wrong-or-blank {synth.overall.silent.baseline} →{" "}
        {synth.overall.silent.candidate} (p = {synth.overall.silent_items_p.toFixed(1)}): <Verdict decision="go" />. Spark 1.3
        listening directly stays <Verdict decision="no-go" /> in the same run.
      </p>

      <div className="mt-12 grid gap-6 lg:grid-cols-3">
        {real && realD && (
          <div className="rounded-lg border border-line bg-card p-6">
            <p className="text-sm text-muted">Real voice: {realD[e9.baseline].clips} notes, one speaker</p>
            <p className="mt-2 text-3xl font-semibold tabular-nums">
              {realD[e9.baseline].order_number_right.split("/")[0]} → {realD[e9.route].order_number_right.split("/")[0]}
              <span className="text-base font-normal text-muted"> of {realD[e9.baseline].clips}</span>
            </p>
            <p className="mt-1 text-sm text-muted">
              order numbers right. Notes right {realD[e9.baseline].clips_correct_majority} → {realD[e9.route].clips_correct_majority}.
            </p>
            <p className="mt-3 text-sm">
              Gate: <Verdict decision={real.gates[e9.route]?.decision ?? "inconclusive"} />{" "}
              <span className="text-muted">Not worse, but too few notes to call it better.</span>
            </p>
          </div>
        )}
        {loss && (
          <div className="rounded-lg border border-line bg-card p-6">
            <p className="text-sm text-muted">Wrong orders that pass the shop’s checks, per 1,000</p>
            <p className="mt-2 text-3xl font-semibold tabular-nums">
              {loss[e9.baseline]?.per_1000["wrong but saved"] ?? 0} → {loss[e9.route]?.per_1000["wrong but saved"] ?? 0}
              <span className="text-base font-normal text-muted"> synthetic</span>
            </p>
            {lossReal && (
              <p className="mt-1 text-sm text-muted">
                {lossReal[e9.baseline]?.per_1000["wrong but saved"] ?? 0} → {lossReal[e9.route]?.per_1000["wrong but saved"] ?? 0} with
                the real voice.
              </p>
            )}
            <p className="mt-3 text-sm text-muted">
              <span className="font-medium text-fg">Scenario, not a measurement:</span> at ₹180–240 per failed delivery
              (logistics only, an industry estimate), {inr(loss[e9.baseline]?.inr_per_1000)} →{" "}
              {inr(loss[e9.route]?.inr_per_1000)} per 1,000 orders. Rejected notes rise{" "}
              {loss[e9.baseline]?.per_1000.rejected ?? 0} → {loss[e9.route]?.per_1000.rejected ?? 0}; counted, not priced.
            </p>
          </div>
        )}
        <div className="rounded-lg border border-line bg-card p-6">
          <p className="text-sm text-muted">What the route gives up</p>
          <p className="mt-2 text-sm">
            It never says “I can’t hear”: a transcript always has words. Its mistakes come from the transcript,
            mostly repeated digits (“छह छह छह छह” turns 266697 into 2666697). A wrong digit count fails the format
            check, so most are caught rather than shipped.
          </p>
          <p className="mt-3 text-sm text-muted">
            Median time {((synth.describe[e9.route].latency_ms_median ?? 0) / 1000).toFixed(1)} s vs{" "}
            {((synth.describe[e9.baseline].latency_ms_median ?? 0) / 1000).toFixed(1)} s today.
          </p>
        </div>
      </div>

      <p className="mt-6 text-sm text-muted">
        Limits: synthetic voices are cleaner than real notes; one real speaker; one line of the transcript prompt was
        written after seeing a single transcript.{" "}
        <a
          className="text-accent underline underline-offset-2"
          href="https://github.com/UtsavInTech/upgrade-gate/blob/main/findings/LOG.md#e9-result-transcribe-first-then-spark-13--the-gate-says-go"
        >
          Pre-registration and full result
        </a>
      </p>
    </Section>
  );
}
