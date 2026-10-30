import { ArrowRight, Check, Circle, Minus, Square, Upload, X } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { toWav16k } from "../audio";
import type { Site } from "../data";
import { LANG_LABEL, pts } from "../data";
import type { Config, Result } from "../voiceorder";
import { DEFAULT_SAMPLE, FIELDS, fieldMatches, loadVoiceOrder, modelsOf, outcomeOf, roleOf } from "../voiceorder";
import { AudioButton } from "./AudioButton";
import { routeLabel } from "./SafeRouteSection";
import { gateBadges, stagesOf } from "./UpgradePath";
import { Verdict } from "./ui";

type Slot = Result | "loading" | { error: string };
const ROLE = { shipping: "Shipping today", candidate: "Proposed upgrade", route: "Alternative route" } as const;

async function post(url: string, body?: Blob): Promise<Result> {
  const r = await fetch(url, { method: "POST", body, headers: body ? { "Content-Type": "audio/wav" } : {} });
  const data = await r.json().catch(() => ({ error: `The server answered ${r.status}.` }));
  if (!r.ok) throw new Error(data.error ?? `The server answered ${r.status}.`);
  return data;
}

const canRecord = () =>
  typeof window !== "undefined" && "MediaRecorder" in window && !!navigator.mediaDevices?.getUserMedia && window.isSecureContext;

export function VoiceOrder({ site }: { site: Site | null }) {
  const [cfg, setCfg] = useState<Config | null>(null);
  const [loadError, setLoadError] = useState(false);
  const [mode, setMode] = useState<"sample" | "record">("sample");
  const [sampleId, setSampleId] = useState(DEFAULT_SAMPLE);
  const [lang, setLang] = useState("hi");
  const [live, setLive] = useState<Record<string, Slot>>({});
  const [recState, setRecState] = useState<"idle" | "recording" | "ready">("idle");
  const [take, setTake] = useState<{ url: string; wav: Blob } | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const rec = useRef<MediaRecorder | null>(null);

  const load = useCallback(() => {
    setLoadError(false);
    loadVoiceOrder().then(setCfg, () => setLoadError(true));
  }, []);
  useEffect(load, [load]);

  const models = useMemo(() => (cfg ? modelsOf(cfg) : []), [cfg]);
  const sample = cfg?.samples.find((s) => s.id === sampleId);
  const shown = cfg?.samples.filter((s) => s.lang === lang) ?? [];
  const results: Record<string, Slot> = useMemo(() => {
    if (!cfg) return {};
    if (mode === "record") return live;
    const saved = cfg.results?.[sampleId] ?? {};
    return Object.fromEntries(models.map((m) => [m, saved[m] ?? { error: "No saved answer for this note." }]));
  }, [cfg, models, mode, sampleId, live]);

  const runLive = async (wav: Blob) => {
    setLive(Object.fromEntries(models.map((m) => [m, "loading"])));
    await Promise.all(
      models.map(async (m) => {
        try {
          const res = await post(`/api/voiceorder/parse?model=${encodeURIComponent(m)}`, wav);
          setLive((r) => ({ ...r, [m]: res }));
        } catch (e) {
          setLive((r) => ({ ...r, [m]: { error: (e as Error).message } }));
        }
      }),
    );
  };

  const startRec = async () => {
    setNotice(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const parts: Blob[] = [];
      const r = new MediaRecorder(stream);
      r.ondataavailable = (e) => e.data.size && parts.push(e.data);
      r.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        try {
          const wav = await toWav16k(new Blob(parts, { type: r.mimeType }));
          setTake({ url: URL.createObjectURL(wav), wav });
          setRecState("ready");
        } catch {
          setNotice("This browser couldn’t decode the recording. Try uploading a file instead.");
          setRecState("idle");
        }
      };
      rec.current = r;
      r.start();
      setRecState("recording");
      setLive({});
    } catch (e) {
      const name = (e as DOMException)?.name;
      setNotice(
        name === "NotFoundError"
          ? "No microphone was found. Upload a recording instead."
          : "Microphone access was blocked. Allow it in the address bar, or upload a recording instead.",
      );
    }
  };

  const onFile = async (f: File | undefined) => {
    if (!f) return;
    setNotice(null);
    try {
      const wav = await toWav16k(f);
      setTake({ url: URL.createObjectURL(wav), wav });
      setRecState("ready");
      setLive({});
    } catch {
      setNotice("That file couldn’t be read as audio. Try a WAV, MP3 or M4A file.");
    }
  };

  if (loadError) {
    return (
      <div className="mx-auto max-w-xl px-4 py-24 text-center">
        <h1 className="text-2xl font-semibold">VoiceOrder couldn’t load</h1>
        <p className="mt-3 text-muted">The saved examples didn’t download. Check your connection and try again.</p>
        <button onClick={load} className="mt-6 rounded-md bg-fg px-4 py-2.5 text-sm font-semibold text-bg">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl px-4 pt-8 pb-16 sm:px-8">
      <header className="max-w-2xl">
        <p className="text-sm font-medium text-muted">Example app protected by Upgrade Gate</p>
        <h1 className="mt-1 text-3xl font-semibold tracking-tight">VoiceOrder</h1>
        <p className="mt-2 text-muted text-pretty">
          An Indian shop turns customers’ voice notes into orders. Each route hears the same note; the shop’s form only
          checks the format before saving.
        </p>
      </header>

      {!cfg ? (
        <div className="mt-8 grid gap-6 lg:grid-cols-[320px_minmax(0,1fr)]" aria-busy="true">
          <div className="h-80 animate-pulse rounded-xl bg-surface" />
          <div className="h-80 animate-pulse rounded-xl bg-surface" />
        </div>
      ) : (
        <div className="mt-8 grid grid-cols-[minmax(0,1fr)] gap-6 lg:grid-cols-[320px_minmax(0,1fr)]">
          {/* Input panel: quiet */}
          <section aria-labelledby="note-h" className="rounded-xl border border-line bg-card p-4 lg:self-start">
            <h2 id="note-h" className="sr-only">
              Voice note
            </h2>
            <div role="tablist" aria-label="Note source" className="flex gap-1 rounded-lg bg-surface p-1 text-sm">
              {(["sample", "record"] as const).map((m) => (
                <button
                  key={m}
                  role="tab"
                  aria-selected={mode === m}
                  onClick={() => setMode(m)}
                  className={`flex-1 rounded-md px-3 py-2 font-medium transition-colors duration-150 ${
                    mode === m ? "bg-card text-fg shadow-sm" : "text-muted hover:text-fg"
                  }`}
                >
                  {m === "sample" ? "Saved examples" : "Record a note"}
                </button>
              ))}
            </div>

            {mode === "sample" ? (
              <>
                <div className="mt-4 flex gap-1" role="radiogroup" aria-label="Language">
                  {["hi", "hinglish", "en"].map((l) => (
                    <button
                      key={l}
                      role="radio"
                      aria-checked={lang === l}
                      onClick={() => {
                        setLang(l);
                        const first = cfg.samples.find((s) => s.lang === l);
                        if (first) setSampleId(first.id);
                      }}
                      className={`rounded-md px-3 py-1.5 text-sm transition-colors duration-150 ${
                        lang === l ? "bg-fg text-bg" : "text-muted hover:bg-surface hover:text-fg"
                      }`}
                    >
                      {LANG_LABEL[l]}
                    </button>
                  ))}
                </div>
                <label htmlFor="sample-select" className="mt-4 block text-xs text-faint">
                  Note ({shown.length} saved in {LANG_LABEL[lang]})
                </label>
                <select
                  id="sample-select"
                  value={sampleId}
                  onChange={(e) => setSampleId(e.target.value)}
                  className="mt-1 w-full rounded-md border border-line bg-card px-3 py-2 text-sm"
                >
                  {shown.map((s, i) => (
                    <option key={s.id} value={s.id}>
                      Note {i + 1}: {s.transcript.slice(0, 44)}…
                    </option>
                  ))}
                </select>
                {sample && (
                  <div className="mt-4 border-t border-line pt-4">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <AudioButton src={sample.audio} />
                      <span className="text-xs text-faint">Saved example · Synthetic voice</span>
                    </div>
                    <p className="mt-3 text-sm leading-relaxed" lang={sample.lang === "hi" ? "hi" : "en"}>
                      {sample.transcript}
                    </p>
                    <p className="mt-3 text-xs text-muted">Answers come from the saved test run. Nothing is sent or spent.</p>
                  </div>
                )}
              </>
            ) : cfg.live ? (
              <div className="mt-4 space-y-4 text-sm">
                <p className="text-muted">
                  Say an order number digit by digit, a 6-digit pincode and your city. Your note goes to each route once
                  (about $0.02) and isn’t stored.
                </p>
                <div className="flex flex-wrap items-center gap-2">
                  {canRecord() ? (
                    recState === "recording" ? (
                      <button
                        onClick={() => rec.current?.stop()}
                        className="inline-flex items-center gap-2 rounded-md bg-risk px-4 py-2.5 font-semibold text-white"
                      >
                        <Square aria-hidden className="size-4 fill-current" /> Stop
                      </button>
                    ) : (
                      <button onClick={startRec} className="inline-flex items-center gap-2 rounded-md bg-fg px-4 py-2.5 font-semibold text-bg">
                        <Circle aria-hidden className="size-4 fill-[var(--risk)] text-[var(--risk)]" />
                        {take ? "Record again" : "Record"}
                      </button>
                    )
                  ) : (
                    <p className="text-hold">Recording isn’t available in this browser. Upload a file instead.</p>
                  )}
                  <label className="inline-flex cursor-pointer items-center gap-2 rounded-md border border-line px-4 py-2.5 font-medium hover:bg-surface">
                    <Upload aria-hidden className="size-4" /> Upload
                    <input type="file" accept="audio/*" className="sr-only" onChange={(e) => onFile(e.target.files?.[0])} />
                  </label>
                </div>
                {take && <audio controls src={take.url} className="w-full" />}
                {take && recState === "ready" && (
                  <button onClick={() => runLive(take.wav)} className="w-full rounded-md bg-accent px-4 py-2.5 font-semibold text-accent-ink">
                    Turn into an order
                  </button>
                )}
                {notice && (
                  <p role="alert" className="text-hold">
                    {notice}
                  </p>
                )}
                <p className="text-xs text-faint">A new recording has no known answer, so routes are checked for format only.</p>
              </div>
            ) : (
              <div className="mt-4 space-y-3 text-sm text-muted">
                <p>Live requests are off on this demo, so the saved examples cost nothing and always work.</p>
                <p>
                  To try your own voice, run VoiceOrder locally:{" "}
                  <code className="rounded bg-surface px-1 font-mono text-xs text-fg">npm --prefix web run dev</code>
                </p>
                <p>
                  Want to help the research instead?{" "}
                  <a href="#/record" className="text-accent underline-offset-2 hover:underline">
                    Record the 45 test lines
                  </a>
                </p>
              </div>
            )}
          </section>

          {/* Comparison */}
          <section aria-labelledby="routes-h">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <h2 id="routes-h" className="text-lg font-semibold">
                What each route saves
              </h2>
              <p className="text-xs text-faint">Previewing routes here doesn’t change the shipped model.</p>
            </div>
            {mode === "record" && !Object.keys(live).length ? (
              <p className="mt-4 rounded-xl border border-dashed border-line px-5 py-12 text-center text-sm text-muted">
                {cfg.live ? "Record or upload a note to compare the routes." : "Choose a saved example to compare the routes."}
              </p>
            ) : (
              <div className="mt-4 grid gap-4 md:grid-cols-3" aria-live="polite">
                {models.map((m) => (
                  <RouteColumn key={m} cfg={cfg} model={m} r={results[m]} />
                ))}
              </div>
            )}
            <DecisionPanel cfg={cfg} site={site} />
          </section>
        </div>
      )}
    </div>
  );
}

function RouteColumn({ cfg, model, r }: { cfg: Config; model: string; r?: Slot }) {
  const role = roleOf(cfg, model);
  const stages = stagesOf(model);
  const head = (
    <div className="border-b border-line pb-3 md:min-h-[84px]">
      <p className="text-xs text-faint">{ROLE[role]}</p>
      <p className="mt-1 flex flex-wrap items-center gap-1 text-sm font-semibold">
        <span className="rounded bg-surface px-1.5 py-0.5 text-xs font-medium text-muted">Audio</span>
        {stages.map((s, i) => (
          <span key={s} className="inline-flex items-center gap-1">
            <ArrowRight aria-label="then" className="size-3.5 text-faint" />
            <span className={i === 0 && stages.length > 1 ? "rounded bg-accent-soft px-1.5 py-0.5 text-xs text-accent" : ""}>{s}</span>
          </span>
        ))}
      </p>
    </div>
  );
  if (!r || r === "loading")
    return (
      <article className="rounded-xl border border-line bg-card p-4" aria-busy="true">
        {head}
        <div className="mt-4 h-28 animate-pulse rounded bg-surface" />
      </article>
    );
  if ("error" in r && !("checks" in r))
    return (
      <article className="rounded-xl border border-line bg-card p-4">
        {head}
        <p className="mt-4 text-sm text-risk">{r.error}</p>
      </article>
    );
  const res = r as Result;
  const o = outcomeOf(res);
  const tone = { go: "text-go", risk: "text-risk", hold: "text-hold", muted: "text-muted" }[o.tone];
  const border = o.tone === "risk" ? "border-risk/50" : o.tone === "go" ? "border-go/40" : "border-line";
  return (
    <article className={`flex flex-col rounded-xl border bg-card p-4 ${border}`}>
      {head}
      <dl className="mt-1 divide-y divide-line text-sm">
        {FIELDS.map(([k, name]) => {
          const val = String(res.order?.[k] ?? "");
          const match = fieldMatches(res, k);
          const fmt = res.checks.fields[k];
          return (
            <div key={k} className="py-2">
              <div className="flex items-center justify-between gap-2">
                <dt className="text-xs text-muted">{name}</dt>
                <dd className="flex items-center gap-2 text-[11px] text-faint">
                  {fmt !== undefined && (
                    <span className="inline-flex items-center gap-0.5" title={fmt ? "Passes the format check" : "Fails the format check"}>
                      {fmt ? <Check aria-hidden className="size-3 text-go" /> : <X aria-hidden className="size-3 text-risk" />}
                      <span className="sr-only">{fmt ? "passes" : "fails"} the</span> format
                    </span>
                  )}
                  <span
                    className="inline-flex items-center gap-0.5"
                    title={match === undefined ? "No known answer" : match ? "Matches what was said" : "Doesn’t match what was said"}
                  >
                    {match === undefined ? (
                      <Minus aria-hidden className="size-3" />
                    ) : match ? (
                      <Check aria-hidden className="size-3 text-go" />
                    ) : (
                      <X aria-hidden className="size-3 text-risk" />
                    )}
                    <span className="sr-only">{match === undefined ? "no known answer to" : match ? "" : "does not"}</span> matches
                  </span>
                </dd>
              </div>
              <dd className={`mt-0.5 font-mono text-[15px] whitespace-nowrap ${match === false ? "font-semibold text-risk" : ""}`}>
                {val || <span className="font-sans text-sm text-faint">(blank)</span>}
              </dd>
            </div>
          );
        })}
      </dl>
      <div className="mt-2 border-t border-line pt-3">
        <p className={`text-sm font-bold ${tone}`}>{o.label}</p>
        <p className="mt-1 text-xs text-muted">{o.detail}</p>
      </div>
      {res.truth && !res.truth.correct && (
        <p className="mt-2 text-xs text-muted">
          Customer said{" "}
          <span className="font-mono text-fg">
            {FIELDS.map(([k]) => res.truth!.expected[k])
              .filter(Boolean)
              .join(" · ")}
          </span>
        </p>
      )}
      <div className="mt-auto space-y-1 pt-3 text-xs text-muted">
        {res.transcript && (
          <details>
            <summary className="cursor-pointer">What Voice Transcribe heard</summary>
            <p className="mt-1 break-words text-fg">{res.transcript}</p>
          </details>
        )}
        <details>
          <summary className="cursor-pointer">Model reply</summary>
          <p className="mt-1 font-mono break-words whitespace-pre-wrap text-fg">{res.text || res.error || "(empty)"}</p>
        </details>
        <p className="pt-1 text-faint">
          {res.reused || res.latency_ms == null
            ? "Saved answer · no cost"
            : `Live request · $${res.cost_usd.toFixed(4)} · ${(res.latency_ms / 1000).toFixed(1)} s`}
        </p>
      </div>
    </article>
  );
}

function DecisionPanel({ cfg, site }: { cfg: Config; site: Site | null }) {
  const badges = gateBadges(site, cfg);
  const e9 = site?.e9;
  const synth = e9?.sets?.synth;
  const audio = site?.e6.behaviour?.by_input?.audio;
  if (!site) return null;
  return (
    <section aria-labelledby="decision-h" className="mt-6 rounded-xl border border-line bg-card p-5 shadow-[0_1px_2px_rgba(16,24,40,0.05)] sm:p-6">
      <h2 id="decision-h" className="font-semibold">
        What the gate decided
      </h2>
      <p className="mt-1 text-sm text-muted">From the full saved runs, not this single note.</p>
      <ul className="mt-2 divide-y divide-line">
        <li className="grid gap-2 py-4 sm:grid-cols-[170px_minmax(0,1fr)]">
          <span>
            {(badges[cfg.candidate] ?? []).map((b) => (
              <Verdict key={b.note} decision={b.decision} large />
            ))}
          </span>
          <div className="text-sm">
            <p className="font-semibold">{routeLabel(cfg.candidate)}</p>
            {audio && (
              <p className="mt-1 text-muted">
                Wrong or blank with no warning rose {audio.silent.baseline} → {audio.silent.candidate} of {audio.tasks} notes while
                accuracy barely moved. “I can’t hear” answers went {audio.abstain.baseline} → {audio.abstain.candidate}.
              </p>
            )}
            <a href="#/report/e6-audio" className="mt-2 inline-flex items-center gap-1 font-medium text-accent hover:underline">
              View failing examples <ArrowRight aria-hidden className="size-3.5" />
            </a>
          </div>
        </li>
        {cfg.route && e9 && synth?.overall && (
          <li className="grid gap-2 py-4 sm:grid-cols-[170px_minmax(0,1fr)]">
            <span className="flex flex-col gap-2">
              {(badges[cfg.route] ?? []).map((b) => (
                <span key={b.note} className="flex flex-col">
                  <Verdict decision={b.decision} large />
                  <span className="text-[11px] text-muted">{b.note}</span>
                </span>
              ))}
            </span>
            <div className="text-sm">
              <p className="font-semibold">{routeLabel(cfg.route)}</p>
              <p className="mt-1 text-muted">
                {pts(synth.overall.delta)} points more notes right than today (95% range {pts(synth.overall.ci_low)} to{" "}
                {pts(synth.overall.ci_high)}); silent failures {synth.overall.silent.baseline} → {synth.overall.silent.candidate}. With
                one real speaker the gate can’t decide yet: the policy allows the switch because that isn’t NO-GO, which is
                not the same as GO for every voice.
              </p>
              <p className="mt-1 text-muted">
                ${synth.describe[e9.route].usd_per_1000_clips.toFixed(2)} vs ${synth.describe[e9.baseline].usd_per_1000_clips.toFixed(2)} per
                1,000 notes.
              </p>
              <a href="#/report/e9-route-synth" className="mt-2 inline-flex items-center gap-1 font-medium text-accent hover:underline">
                Compare routes <ArrowRight aria-hidden className="size-3.5" />
              </a>
            </div>
          </li>
        )}
      </ul>
    </section>
  );
}
