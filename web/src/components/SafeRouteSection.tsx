import { Reveal, Section, Verdict } from "./ui";

// Numbers from experiments/out/e9_route.json and experiments/out/loss_scenario_e9-route-*.json
// (E9, 31 Oct 2026, pre-registered in findings/LOG.md). Every try counted unless it says "clips".
type Route = {
  name: string;
  how: string;
  decision: "go" | "no-go" | null;
  clips: number;
  order: number;
  pin: number;
  silent: number;
  cantHear: number;
  p90: number;
  usd: number;
};

const ROUTES: Route[] = [
  { name: "Spark 1.2 listens", how: "Today’s app", decision: null, clips: 93, order: 85, pin: 83, silent: 18, cantHear: 21, p90: 21.2, usd: 2.44 },
  { name: "Spark 1.3 listens", how: "The plain upgrade", decision: "no-go", clips: 90, order: 68, pin: 56, silent: 42, cantHear: 0, p90: 26.9, usd: 3.5 },
  { name: "Voice Transcribe → Spark 1.3", how: "Write it down first, then read", decision: "go", clips: 110, order: 111, pin: 104, silent: 20, cantHear: 0, p90: 10.1, usd: 3.0 },
];

const ROWS: { label: string; get: (r: Route) => string }[] = [
  { label: "Notes right (most of 3 tries)", get: (r) => `${r.clips} / 135` },
  { label: "Order number right", get: (r) => `${r.order} / 135` },
  { label: "Pincode right", get: (r) => `${r.pin} / 135` },
  { label: "Wrong or blank, no warning", get: (r) => `${r.silent} / 135` },
  { label: "Said “I can’t hear”", get: (r) => `${r.cantHear}` },
  { label: "Slowest 10% take", get: (r) => `${r.p90.toFixed(1)} s` },
  { label: "Cost per 1,000 notes", get: (r) => `$${r.usd.toFixed(2)}` },
];

export function SafeRouteSection() {
  return (
    <Section
      id="safe-route"
      eyebrow="Voice notes · the way through · 1,620 calls · $2.95"
      title="Blocked isn’t the end. The same gate approved a safe way to upgrade."
      lede={
        <>
          Meta’s docs point audio work to its speech model, Muse Voice Transcribe. We tested that advice on the same
          Hindi, Hinglish and English notes, with the rules written down before the first call, and let the
          unchanged gate and release policy decide.
        </>
      }
    >
      <Reveal className="overflow-x-auto rounded-lg border border-line">
        <table className="w-full min-w-[620px] border-collapse text-left text-sm">
          <thead className="bg-surface">
            <tr>
              <th scope="col" className="px-5 py-4 font-medium">
                <span className="sr-only">Measure</span>
                <span className="text-xs text-faint">135 synthetic-voice notes, 3 tries each</span>
              </th>
              {ROUTES.map((r) => (
                <th key={r.name} scope="col" className={`px-5 py-4 ${r.decision === "go" ? "bg-go-soft" : ""}`}>
                  <span className="block font-semibold">{r.name}</span>
                  <span className="mt-0.5 flex items-center gap-2 text-xs font-normal text-muted">
                    {r.how}
                    {r.decision && <Verdict decision={r.decision} />}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {ROWS.map((row) => (
              <tr key={row.label} className="border-t border-line">
                <th scope="row" className="px-5 py-3 font-normal text-muted">
                  {row.label}
                </th>
                {ROUTES.map((r) => (
                  <td key={r.name} className={`px-5 py-3 font-medium ${r.decision === "go" ? "bg-go-soft/60" : ""}`}>
                    {row.get(r)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </Reveal>
      <p className="mt-3 text-sm text-muted">
        Against today’s app the gate measured <span className="font-semibold text-fg">+12.8 points</span> correct (95% range
        +5.3 to +20.3) and no significant rise in silent failures (18 → 20, p = 0.8):{" "}
        <span className="font-semibold text-go">GO</span>. Spark 1.3 listening directly stays NO-GO in the same run.
      </p>

      <div className="mt-12 grid gap-6 lg:grid-cols-3">
        <div className="rounded-lg border border-line p-6">
          <p className="text-sm text-muted">With a real voice (45 notes, one speaker)</p>
          <p className="mt-2 text-3xl font-semibold">
            24 → 41 <span className="text-base font-normal text-muted">of 45</span>
          </p>
          <p className="mt-1 text-sm text-muted">order numbers right. Notes right 36 → 38.</p>
          <p className="mt-3 text-sm">
            Gate: <Verdict decision="inconclusive" /> <span className="text-muted">— not worse, too few notes to call it
            better. Our rule allowed the switch only if this wasn’t NO-GO.</span>
          </p>
        </div>
        <div className="rounded-lg border border-line p-6">
          <p className="text-sm text-muted">Wrong orders that pass the shop’s checks, per 1,000</p>
          <p className="mt-2 text-3xl font-semibold">
            185 → 52 <span className="text-base font-normal text-muted">synthetic</span>
          </p>
          <p className="mt-1 text-sm text-muted">400 → 89 with the real voice.</p>
          <p className="mt-3 text-sm text-muted">
            Scenario: if each one is a failed delivery at ₹180–240 (logistics only, an industry estimate), that is
            about ₹33,000–44,000 → ₹9,000–12,000 per 1,000 orders. More notes are now rejected by the form (185 → 289)
            and need a follow-up; we count those, we don’t price them.
          </p>
        </div>
        <div className="rounded-lg border border-line p-6">
          <p className="text-sm text-muted">What the route gives up</p>
          <p className="mt-2 text-sm">
            It never says “I can’t hear”: a transcript always has words. Its mistakes come from the transcript
            instead, mostly repeated digits (“छह छह छह छह” makes pincode 266697 into 2666697). A wrong digit count
            fails the shop’s format check, so most of these are caught rather than shipped.
          </p>
          <p className="mt-3 text-sm text-muted">Median time 5.9 s vs 5.1 s today; cost +23%.</p>
        </div>
      </div>

      <div className="mt-12 rounded-lg bg-surface p-6 sm:p-8">
        <h3 className="font-semibold">One gate, three decisions on Spark 1.3</h3>
        <ul className="mt-4 grid gap-4 text-sm sm:grid-cols-3">
          <li>
            <Verdict decision="no-go" />
            <p className="mt-1 text-muted">Letting 1.3 listen to voice notes: silent failures rose 18 → 42.</p>
          </li>
          <li>
            <Verdict decision="go" />
            <p className="mt-1 text-muted">1.3 behind Voice Transcribe: +12.8 points, no rise in silent failures.</p>
          </li>
          <li>
            <Verdict decision="go" />
            <p className="mt-1 text-muted">
              1.3 Contributor on text and documents: identical observed pass/fail on 1,325 tasks at about 94% lower
              measured inference cost (customer data is a separate policy decision).
            </p>
          </li>
        </ul>
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
