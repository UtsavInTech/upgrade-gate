import { ArrowRight, Check, X } from "lucide-react";
import type { Site } from "../data";
import { LANG_LABEL } from "../data";
import type { Config, Result } from "../voiceorder";
import { FIELDS, fieldMatches, modelsOf, outcomeOf, roleOf } from "../voiceorder";
import { AudioButton } from "./AudioButton";
import { routeLabel } from "./SafeRouteSection";
import { Verdict } from "./ui";

const ROLE_LABEL = { shipping: "Shipping today", candidate: "Proposed upgrade", route: "Alternative route" } as const;

/** Stages a note passes through on each route, shown as small chips. */
export function stagesOf(model: string): string[] {
  return model.startsWith("transcribe+") ? ["Voice Transcribe", routeLabel(model).split("→ ")[1]] : [routeLabel(model).replace(" listens", "")];
}

export const speakersText = (n?: number | null) => (n === 1 ? "one speaker" : `${n ?? "several"} speakers`);

export type GateBadge = { decision: string; note: string; short: string };

/** The gate's verdicts for each role, from the saved runs (site.json). The baseline has none. */
export function gateBadges(site: Site | null, cfg: Config): Record<string, GateBadge[]> {
  const out: Record<string, GateBadge[]> = {};
  if (!site) return out;
  const silent = site.e6.behaviour?.by_input?.audio?.silent;
  out[cfg.candidate] = [
    {
      decision: site.e6.gate_decision ?? site.e6.decision,
      note: silent ? `Silent failures ${silent.baseline} → ${silent.candidate} of ${site.e6.behaviour?.by_input?.audio?.tasks} notes` : "",
      short: "",
    },
  ];
  const e9 = site.e9;
  if (cfg.route && e9?.status === "done") {
    const synth = e9.sets.synth;
    const real = e9.sets.real;
    out[cfg.route] = [
      {
        decision: synth?.gates[cfg.route]?.decision ?? "inconclusive",
        note: `${synth?.describe[e9.baseline]?.clips ?? ""} synthetic-voice notes`,
        short: "synthetic",
      },
      ...(real
        ? [
            {
              decision: real.gates[cfg.route]?.decision ?? "inconclusive",
              note: `${real.describe[e9.baseline]?.clips} real-voice notes, ${speakersText(real.speakers)}`,
              short: "real voice",
            },
          ]
        : []),
    ];
  }
  return out;
}

/** The field that tells the story for this note: the first one any route gets wrong. */
export function keyField(results: Record<string, Result>): [string, string] {
  for (const f of FIELDS) if (Object.values(results).some((r) => fieldMatches(r, f[0]) === false)) return f;
  return FIELDS[1];
}

export function UpgradePath({
  cfg,
  sampleId,
  site,
  compact = false,
}: {
  cfg: Config;
  sampleId: string;
  site: Site | null;
  compact?: boolean;
}) {
  const sample = cfg.samples.find((s) => s.id === sampleId);
  const results = cfg.results?.[sampleId] ?? {};
  const models = modelsOf(cfg).filter((m) => results[m]);
  const badges = gateBadges(site, cfg);
  const [fKey, fLabel] = keyField(results);
  const expected = Object.values(results)[0]?.truth?.expected[fKey];

  if (!sample || !models.length) {
    return (
      <div className="rounded-xl border border-line bg-card p-6 text-sm text-muted">
        This saved example isn’t available. Choose another note.
      </div>
    );
  }

  return (
    <figure className="overflow-hidden rounded-xl border border-line bg-card shadow-[0_1px_2px_rgba(16,24,40,0.04),0_12px_32px_-24px_rgba(16,24,40,0.25)]">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line px-5 py-4">
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="rounded-full bg-surface px-2.5 py-1 font-medium text-muted">Saved example</span>
          <span className="rounded-full bg-surface px-2.5 py-1 font-medium text-muted">Synthetic voice</span>
          <span className="rounded-full bg-surface px-2.5 py-1 font-medium text-muted">{LANG_LABEL[sample.lang]}</span>
        </div>
        <AudioButton src={sample.audio} />
      </div>
      <div className="px-5 pt-4">
        <p className="text-sm leading-relaxed text-pretty" lang={sample.lang === "hi" ? "hi" : "en"}>
          {sample.transcript}
        </p>
        {expected && (
          <p className="mt-2 text-xs text-muted">
            The customer said {fLabel.toLowerCase()} <span className="font-mono text-fg">{expected}</span>
          </p>
        )}
      </div>

      {/* The rail: one voice note branching into each route. */}
      <ol className="relative mt-4 ml-5 border-l-2 border-accent/25 pr-5 pb-2 pl-5" aria-label="What each route saves">
        {models.map((m) => {
          const r = results[m];
          const role = roleOf(cfg, m);
          const o = outcomeOf(r);
          const match = fieldMatches(r, fKey);
          const value = String(r.order?.[fKey] ?? "") || "(blank)";
          const fmtOk = r.checks.fields[fKey];
          return (
            <li
              key={m}
              className="relative grid grid-cols-[minmax(0,1fr)_auto] items-center gap-x-4 gap-y-2 border-t border-line py-3 before:absolute before:top-1/2 before:-left-5 before:h-0.5 before:w-3.5 before:bg-accent/25 first:border-t-0 sm:grid-cols-[minmax(0,1.25fr)_auto_minmax(0,1fr)]"
            >
              <div className="min-w-0">
                <p className="text-xs text-faint">{ROLE_LABEL[role]}</p>
                <p className="mt-0.5 flex flex-wrap items-center gap-1 text-sm font-semibold">
                  {stagesOf(m).map((s, i) => (
                    <span key={s} className="inline-flex items-center gap-1">
                      {i > 0 && <ArrowRight aria-label="then" className="size-3.5 text-faint" />}
                      <span className={i === 0 && stagesOf(m).length > 1 ? "rounded bg-accent-soft px-1.5 py-0.5 text-xs text-accent" : ""}>
                        {s}
                      </span>
                    </span>
                  ))}
                </p>
              </div>
              <div className="text-right sm:text-left">
                <p
                  className={`font-mono text-base font-medium tabular-nums ${match === false ? "text-risk" : ""}`}
                  aria-label={`${fLabel} ${value}${match === false ? ", does not match" : match ? ", matches" : ""}`}
                >
                  {value}
                </p>
                <p className="mt-0.5 flex items-center gap-2 text-[11px] text-muted sm:justify-start">
                  <span className="inline-flex items-center gap-0.5">
                    {fmtOk ? <Check aria-hidden className="size-3 text-go" /> : <X aria-hidden className="size-3 text-risk" />}
                    format
                  </span>
                  {match !== undefined && (
                    <span className="inline-flex items-center gap-0.5">
                      {match ? <Check aria-hidden className="size-3 text-go" /> : <X aria-hidden className="size-3 text-risk" />}
                      matches
                    </span>
                  )}
                </p>
              </div>
              <div className="col-span-2 flex flex-wrap items-center justify-between gap-2 sm:col-span-1 sm:justify-end">
                <span
                  className={`text-xs font-semibold ${
                    o.tone === "go" ? "text-go" : o.tone === "risk" ? "text-risk" : o.tone === "hold" ? "text-hold" : "text-muted"
                  }`}
                >
                  {o.label}
                </span>
                {!compact || badges[m] ? (
                  <span className="flex flex-wrap items-center justify-end gap-1.5">
                    {(badges[m] ?? []).map((b) => (
                      <span key={b.note} className="inline-flex items-center gap-1 rounded-md border border-line px-1.5 py-0.5" title={b.note}>
                        <Verdict decision={b.decision} />
                        {b.short && <span className="text-[11px] text-muted">{b.short}</span>}
                      </span>
                    ))}
                  </span>
                ) : null}
              </div>
            </li>
          );
        })}
      </ol>
      <figcaption className="border-t border-line bg-surface/60 px-5 py-3 text-xs text-muted">
        Gate decisions come from the full saved runs, not this one note.{" "}
        <a href="#/report/e9-route-synth" className="font-medium text-accent underline-offset-2 hover:underline">
          Why these decisions?
        </a>
      </figcaption>
    </figure>
  );
}
