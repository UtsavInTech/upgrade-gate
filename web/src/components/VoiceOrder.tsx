import { Check, Circle, Square, X } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { toWav16k } from "../audio";
import { LANG_LABEL, shortModel } from "../data";

type Sample = { id: string; lang: string; transcript: string; audio: string };
type Config = {
  shipping: string;
  candidate: string;
  pr: string;
  samples: Sample[];
  // Hosted site: no service, so saved answers come with the config.
  static?: boolean;
  results?: Record<string, Record<string, Result>>;
};
type Result = {
  model: string;
  text: string;
  error: string | null;
  order: Record<string, unknown> | null;
  checks: { status: "saved" | "rejected" | "ask_customer"; message: string; fields: Record<string, boolean> };
  cost_usd: number;
  reused: boolean;
  latency_ms: number | null;
  truth?: { correct: boolean; expected: Record<string, string> };
};

const FIELDS: [string, string][] = [
  ["order_number", "Order number"],
  ["pincode", "Pincode"],
  ["city", "City"],
];
const DEFAULT_SAMPLE = "audio-synth-extract-03-hi";

async function call(url: string, body?: Blob): Promise<Result> {
  const r = await fetch(url, { method: "POST", body, headers: body ? { "Content-Type": "audio/wav" } : {} });
  const data = await r.json().catch(() => ({ error: `HTTP ${r.status}` }));
  if (!r.ok) throw new Error(data.error ?? `HTTP ${r.status}`);
  return data;
}

export function VoiceOrder() {
  const [cfg, setCfg] = useState<Config | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<"sample" | "record">("sample");
  const [sampleId, setSampleId] = useState(DEFAULT_SAMPLE);
  const [lang, setLang] = useState("hi");
  const [results, setResults] = useState<Record<string, Result | "loading" | { error: string }>>({});
  const [recState, setRecState] = useState<"idle" | "recording" | "ready">("idle");
  const [take, setTake] = useState<{ url: string; wav: Blob } | null>(null);
  const rec = useRef<MediaRecorder | null>(null);

  useEffect(() => {
    const json = (r: Response) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`)));
    fetch("/api/voiceorder/config")
      .then(json)
      // No service (hosted site, or the dev server isn't running it): fall back to the saved answers.
      .catch(() => fetch("data/voiceorder.json").then(json))
      .then(setCfg)
      .catch(() =>
        setError(
          "The VoiceOrder service isn’t running. Start the site with `npm --prefix web run dev`; it starts the service too.",
        ),
      );
  }, []);

  const models = cfg ? [cfg.shipping, cfg.candidate] : [];

  const run = useCallback(
    async (source: { sample: string } | { wav: Blob }) => {
      if (!cfg) return;
      if (cfg.static) {
        const saved = "sample" in source ? cfg.results?.[source.sample] : undefined;
        setResults(Object.fromEntries(models.map((m) => [m, saved?.[m] ?? { error: "No saved answer for this note." }])));
        return;
      }
      setResults(Object.fromEntries(models.map((m) => [m, "loading"])));
      await Promise.all(
        models.map(async (m) => {
          const q = `/api/voiceorder/parse?model=${encodeURIComponent(m)}`;
          try {
            const res =
              "sample" in source
                ? await call(`${q}&sample=${encodeURIComponent(source.sample)}`)
                : await call(q, source.wav);
            setResults((r) => ({ ...r, [m]: res }));
          } catch (e) {
            setResults((r) => ({ ...r, [m]: { error: (e as Error).message } }));
          }
        }),
      );
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [cfg],
  );

  useEffect(() => {
    if (cfg && mode === "sample") run({ sample: sampleId });
  }, [cfg, sampleId, mode, run]);

  const startRec = async () => {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const parts: Blob[] = [];
      const r = new MediaRecorder(stream);
      r.ondataavailable = (e) => e.data.size && parts.push(e.data);
      r.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const wav = await toWav16k(new Blob(parts, { type: r.mimeType }));
        setTake({ url: URL.createObjectURL(wav), wav });
        setRecState("ready");
      };
      rec.current = r;
      r.start();
      setRecState("recording");
      setResults({});
    } catch {
      setError("Microphone access was blocked. Allow it in the address bar and try again.");
    }
  };

  const sample = cfg?.samples.find((s) => s.id === sampleId);
  const shown = cfg?.samples.filter((s) => s.lang === lang) ?? [];

  return (
    <div className="mx-auto max-w-6xl px-4 pt-10 pb-24 sm:px-8">
      <header className="grid gap-8 lg:grid-cols-[minmax(0,7fr)_minmax(0,5fr)] lg:items-end">
        <div>
          <p className="text-sm font-medium text-muted">Example app protected by Upgrade Gate</p>
          <h1 className="mt-2 text-4xl font-semibold tracking-tight">VoiceOrder</h1>
          <p className="mt-3 max-w-xl text-lg leading-relaxed text-muted text-pretty">
            Customers of an Indian online shop leave a voice note in Hindi, Hinglish or English with their
            order number, pincode and city. VoiceOrder turns it into an order with Meta Muse Spark and runs
            the shop’s usual checks before saving it.
          </p>
        </div>
        {cfg && (
          <dl className="divide-y divide-line rounded-lg border border-line text-sm">
            <div className="flex items-center justify-between gap-4 px-4 py-3">
              <dt className="text-muted">Shipping today</dt>
              <dd className="font-mono">
                {cfg.shipping} <span className="text-faint">(release/model.json)</span>
              </dd>
            </div>
            <div className="flex items-center justify-between gap-4 px-4 py-3">
              <dt className="text-muted">Proposed upgrade</dt>
              <dd className="font-mono">{cfg.candidate}</dd>
            </div>
            <div className="flex items-center justify-between gap-4 bg-risk-soft px-4 py-3 text-risk">
              <dt className="font-semibold">Upgrade blocked by Upgrade Gate</dt>
              <dd>
                <a href={cfg.pr} target="_blank" rel="noreferrer" className="underline underline-offset-2">
                  See the pull request
                </a>
              </dd>
            </div>
          </dl>
        )}
      </header>

      {error && <p className="mt-8 rounded-md bg-hold-soft px-4 py-3 text-hold">{error}</p>}

      {cfg && (
        <div className="mt-12 grid gap-8 lg:grid-cols-[340px_minmax(0,1fr)]">
          <section aria-labelledby="note-h">
            <h2 id="note-h" className="text-lg font-semibold">
              Voice note
            </h2>
            <div role="tablist" className="mt-3 flex gap-1 rounded-md bg-surface p-1 text-sm">
              {(["sample", "record"] as const).map((m) => (
                <button
                  key={m}
                  role="tab"
                  aria-selected={mode === m}
                  onClick={() => (setMode(m), setResults({}))}
                  className={`flex-1 rounded px-3 py-1.5 font-medium ${mode === m ? "bg-bg text-fg shadow-sm" : "text-muted"}`}
                >
                  {m === "sample" ? "Sample notes" : "Record your own"}
                </button>
              ))}
            </div>

            {mode === "sample" ? (
              <>
                <div className="mt-4 flex gap-1 text-sm" role="tablist" aria-label="Language">
                  {["hi", "hinglish", "en"].map((l) => (
                    <button
                      key={l}
                      role="tab"
                      aria-selected={lang === l}
                      onClick={() => setLang(l)}
                      className={`rounded-md px-3 py-1.5 ${lang === l ? "bg-fg text-bg" : "text-muted hover:text-fg"}`}
                    >
                      {LANG_LABEL[l]}
                    </button>
                  ))}
                </div>
                <ol className="mt-3 max-h-80 overflow-y-auto rounded-lg border border-line">
                  {shown.map((s) => (
                    <li key={s.id}>
                      <button
                        onClick={() => setSampleId(s.id)}
                        aria-current={s.id === sampleId ? "true" : undefined}
                        className={`block w-full border-b border-line px-4 py-2.5 text-left text-sm last:border-0 ${
                          s.id === sampleId ? "bg-accent-soft" : "hover:bg-surface"
                        }`}
                      >
                        <span className="line-clamp-2">{s.transcript}</span>
                      </button>
                    </li>
                  ))}
                </ol>
                {sample && (
                  <div className="mt-4">
                    <audio controls src={sample.audio} className="w-full" />
                    <p className="mt-2 text-xs text-faint">
                      Synthetic voice from the test set. Answers come from the saved run, so nothing is spent.
                    </p>
                  </div>
                )}
              </>
            ) : cfg?.static ? (
              <div className="mt-4 rounded-lg border border-line p-4 text-sm text-muted">
                <p>
                  Recording your own note sends it to Meta’s API, so it only works when you run VoiceOrder on
                  your machine:
                </p>
                <pre className="mt-3 rounded bg-surface p-3 font-mono text-xs break-all whitespace-pre-wrap text-fg">
                  {"git clone https://github.com/UtsavInTech/upgrade-gate\ncd upgrade-gate && npm --prefix web run dev"}
                </pre>
                <p className="mt-3">The sample notes on the other tab use the answers each model gave in our test.</p>
              </div>
            ) : (
              <div className="mt-4 rounded-lg border border-line p-4">
                <p className="text-sm text-muted">
                  Say an order number digit by digit, a 6-digit pincode and your city. The note is sent to
                  Meta for both models (about $0.01) and not stored.
                </p>
                <div className="mt-4 flex flex-wrap items-center gap-3">
                  {recState === "recording" ? (
                    <button
                      onClick={() => rec.current?.stop()}
                      className="inline-flex items-center gap-2 rounded-md bg-risk px-4 py-2.5 font-semibold text-white"
                    >
                      <Square aria-hidden className="size-4 fill-current" /> Stop
                    </button>
                  ) : (
                    <button
                      onClick={startRec}
                      className="inline-flex items-center gap-2 rounded-md bg-fg px-4 py-2.5 font-semibold text-bg"
                    >
                      <Circle aria-hidden className="size-4 fill-[var(--risk)] text-[var(--risk)]" />
                      {take ? "Record again" : "Record"}
                    </button>
                  )}
                  {take && recState === "ready" && (
                    <button
                      onClick={() => run({ wav: take.wav })}
                      className="rounded-md bg-accent px-4 py-2.5 font-semibold text-accent-ink"
                    >
                      Turn into an order
                    </button>
                  )}
                </div>
                {take && <audio controls src={take.url} className="mt-3 w-full" />}
              </div>
            )}
          </section>

          <section aria-labelledby="orders-h">
            <h2 id="orders-h" className="text-lg font-semibold">
              What each model would save
            </h2>
            {mode === "sample" && sample && (
              <p className="mt-1 text-sm text-muted">
                The customer said: <span className="text-fg">{sample.transcript}</span>
              </p>
            )}
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              {models.map((m, i) => (
                <OrderCard
                  key={m}
                  label={i === 0 ? "Shipping today" : "Proposed upgrade"}
                  model={m}
                  r={results[m]}
                />
              ))}
            </div>
            <p className="mt-6 max-w-2xl text-sm text-muted">
              The shop’s checks only see the shape of an order: a 6-digit pincode looks fine whether or not
              it’s the one the customer said. Upgrade Gate replayed 135 notes like these on both models and
              blocked the upgrade because wrong-or-blank answers with no warning rose from 18 to 42.{" "}
              <a href="#/report/e6-audio" className="text-accent underline underline-offset-2">
                Open the report
              </a>
            </p>
          </section>
        </div>
      )}
    </div>
  );
}

function OrderCard({
  label,
  model,
  r,
}: {
  label: string;
  model: string;
  r?: Result | "loading" | { error: string };
}) {
  const head = (
    <div className="flex items-baseline justify-between gap-2 border-b border-line pb-3">
      <span className="text-sm text-muted">{label}</span>
      <span className="font-semibold">{shortModel(model)}</span>
    </div>
  );
  if (!r)
    return (
      <div className="rounded-lg border border-line p-5">
        {head}
        <p className="mt-4 text-sm text-faint">Choose a note.</p>
      </div>
    );
  if (r === "loading")
    return (
      <div className="rounded-lg border border-line p-5" aria-busy="true">
        {head}
        <div className="mt-4 h-24 animate-pulse rounded bg-surface" />
      </div>
    );
  if ("error" in r && !("checks" in r))
    return (
      <div className="rounded-lg border border-line p-5">
        {head}
        <p className="mt-4 text-sm text-risk">{r.error}</p>
      </div>
    );
  const res = r as Result;
  const wrongSaved = res.checks.status === "saved" && res.truth && !res.truth.correct;
  const verdict = wrongSaved
    ? { text: "WRONG ORDER SAVED", cls: "text-risk" }
    : res.checks.status === "saved"
      ? { text: res.truth ? "CORRECT ORDER SAVED" : "ORDER SAVED", cls: "text-go" }
      : res.checks.status === "ask_customer"
        ? { text: "ASKS THE CUSTOMER", cls: "text-hold" }
        : { text: "ORDER LOST", cls: "text-risk" };
  const order = res.order ?? {};
  return (
    <article className={`rounded-lg border p-5 ${wrongSaved ? "border-risk/60" : "border-line"}`}>
      {head}
      <p className={`mt-4 text-xs font-bold tracking-[0.08em] ${verdict.cls}`}>{verdict.text}</p>
      <p className="mt-1 text-sm text-muted">{res.checks.message}</p>
      <dl className="mt-4 divide-y divide-line text-sm">
        {FIELDS.map(([k, name]) => {
          const val = String(order[k] ?? "");
          const shapeOk = res.checks.fields[k];
          const exp = res.truth?.expected[k];
          const right = exp !== undefined && val.trim().toLowerCase() === String(exp).toLowerCase();
          return (
            <div key={k} className="grid grid-cols-[110px_minmax(0,1fr)_auto] items-center gap-2 py-2">
              <dt className="text-muted">{name}</dt>
              <dd className={`font-mono ${exp !== undefined && !right && val ? "text-risk" : ""}`}>
                {val || <span className="text-faint">(blank)</span>}
              </dd>
              <dd className="text-right text-xs text-faint" title="Passes the shop's format check">
                {shapeOk === undefined ? null : shapeOk ? (
                  <Check aria-label="format ok" className="inline size-4 text-go" />
                ) : (
                  <X aria-label="format fails" className="inline size-4 text-risk" />
                )}
              </dd>
            </div>
          );
        })}
      </dl>
      {res.truth && !res.truth.correct && (
        <p className="mt-3 text-xs text-muted">
          The customer said:{" "}
          <span className="font-mono text-fg">
            {FIELDS.map(([k]) => res.truth!.expected[k])
              .filter(Boolean)
              .join(" · ")}
          </span>
        </p>
      )}
      <details className="mt-3 text-xs text-muted">
        <summary className="cursor-pointer">Model reply</summary>
        <p className="mt-2 font-mono break-words whitespace-pre-wrap">{res.text || res.error || "(empty)"}</p>
      </details>
      <p className="mt-3 text-xs text-faint">
        {res.reused
          ? "Saved answer, $0"
          : `$${res.cost_usd.toFixed(4)} · ${((res.latency_ms ?? 0) / 1000).toFixed(1)} s`}
      </p>
    </article>
  );
}
