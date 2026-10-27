import { AnimatePresence } from "motion/react";
import { ArrowDown, ArrowUp, Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import type { Site } from "../data";
import { loadSite, shortModel } from "../data";
import type { RunData, RunIndex, Status, TaskRow } from "../report";
import { CATEGORY_LABEL, loadRun, loadRuns, matchesSlice, pct, signedPts, sliceLabel } from "../report";
import { ClipGrid } from "./ClipGrid";
import { TaskDrawer } from "./TaskDrawer";
import { MODE_STYLE, Verdict } from "./ui";

const FILTERS: { key: Status | "all"; label: string }[] = [
  { key: "regression", label: "Regressions" },
  { key: "improvement", label: "Improvements" },
  { key: "both fail", label: "Both fail" },
  { key: "both pass", label: "Both pass" },
  { key: "all", label: "All" },
];
const PAGE = 40;

export function Report({ run, task }: { run: string; task: string | null }) {
  const [runs, setRuns] = useState<RunIndex[]>([]);
  const [data, setData] = useState<RunData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<Status | "all">("regression");
  const [slice, setSlice] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(0);
  const [site, setSite] = useState<Site | null>(null);

  useEffect(() => {
    loadRuns().then(setRuns, () => setRuns([]));
    loadSite().then(setSite, () => setSite(null));
  }, []);

  useEffect(() => {
    setData(null);
    setError(null);
    setSlice(null);
    setQuery("");
    setPage(0);
    loadRun(run).then(
      (d) => {
        setData(d);
        const c = d.meta.counts;
        setFilter(
          c.regression ? "regression" : c.improvement ? "improvement" : c["both fail"] ? "both fail" : "all",
        );
      },
      (e: Error) => setError(e.message),
    );
  }, [run]);

  const rows = useMemo(() => {
    if (!data) return [];
    const q = query.trim().toLowerCase();
    return data.tasks.filter(
      (t) =>
        (filter === "all" || t.status === filter) &&
        matchesSlice(t, slice) &&
        (!q ||
          t.id.toLowerCase().includes(q) ||
          t.prompt.toLowerCase().includes(q) ||
          (t.transcript ?? "").toLowerCase().includes(q)),
    );
  }, [data, filter, slice, query]);

  const counts = useMemo(() => {
    const c: Record<string, number> = { all: 0 };
    data?.tasks.forEach((t) => {
      if (!matchesSlice(t, slice)) return;
      c[t.status] = (c[t.status] ?? 0) + 1;
      c.all += 1;
    });
    return c;
  }, [data, slice]);

  const open = task && data ? (data.tasks.find((t) => t.id === task) ?? null) : null;

  if (error) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-32 text-center">
        <h1 className="text-2xl font-semibold">Couldn’t load this report</h1>
        <p className="mt-3 text-muted">{error}</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl px-4 pt-8 pb-24 sm:px-8">
      <nav aria-label="Reports" className="-mx-1 flex gap-1 overflow-x-auto border-b border-line">
        {(runs.length ? runs : [{ run, title: run, decision: "" } as RunIndex]).map((r) => (
          <a
            key={r.run}
            href={`#/report/${r.run}`}
            aria-current={r.run === run ? "page" : undefined}
            className={`-mb-px flex shrink-0 items-center gap-2.5 border-b-2 px-3 py-3 text-sm transition-colors ${
              r.run === run
                ? "border-fg font-semibold text-fg"
                : "border-transparent text-muted hover:text-fg"
            }`}
          >
            {r.title}
            {r.decision && <Verdict decision={r.decision} />}
          </a>
        ))}
      </nav>

      {!data ? (
        <div className="py-16" aria-busy="true">
          <div className="h-10 w-1/2 animate-pulse rounded bg-surface" />
          <div className="mt-6 h-32 animate-pulse rounded bg-surface" />
        </div>
      ) : (
        <>
          <RunHeader data={data} />
          {run === "e6-audio" && site?.e6?.clips?.length ? (
            <section aria-labelledby="types-h" className="mt-12">
              <h2 id="types-h" className="text-lg font-semibold">
                How the answers failed
              </h2>
              <p className="mb-4 text-sm text-muted">
                Pass rates barely move, but the kind of failure does. Click a square to open that clip.
              </p>
              <ClipGrid e6={site.e6} />
            </section>
          ) : null}
          <SliceTable
            data={data}
            active={slice}
            onPick={(s) => (setSlice(s === slice ? null : s), setPage(0))}
          />

          <section aria-labelledby="tasks-h" className="mt-12">
            <div className="flex flex-wrap items-end justify-between gap-4">
              <div>
                <h2 id="tasks-h" className="text-lg font-semibold">
                  Tasks
                </h2>
                <p className="text-sm text-muted">
                  Majority of three tries per version. Open a row to read every answer.
                  {slice && (
                    <>
                      {" "}
                      Filtered to <span className="font-medium text-fg">{sliceLabel(slice)}</span>.{" "}
                      <button
                        className="text-accent underline-offset-2 hover:underline"
                        onClick={() => setSlice(null)}
                      >
                        Clear
                      </button>
                    </>
                  )}
                </p>
              </div>
              <label className="flex w-full items-center gap-2 rounded-md border border-line px-3 py-2 text-sm sm:w-72">
                <Search aria-hidden className="size-4 text-faint" />
                <span className="sr-only">Search tasks</span>
                <input
                  value={query}
                  onChange={(e) => (setQuery(e.target.value), setPage(0))}
                  placeholder="Search prompts, transcripts, ids"
                  className="w-full bg-transparent outline-none placeholder:text-faint"
                />
              </label>
            </div>

            <div role="tablist" aria-label="Filter tasks" className="mt-4 flex flex-wrap gap-1">
              {FILTERS.map((f) => (
                <button
                  key={f.key}
                  role="tab"
                  aria-selected={filter === f.key}
                  onClick={() => (setFilter(f.key), setPage(0))}
                  className={`rounded-md px-3 py-1.5 text-sm transition-colors ${
                    filter === f.key ? "bg-fg text-bg" : "text-muted hover:bg-surface hover:text-fg"
                  }`}
                >
                  {f.label} <span className="opacity-70">{counts[f.key] ?? 0}</span>
                </button>
              ))}
            </div>

            <TaskTable
              rows={rows.slice(page * PAGE, (page + 1) * PAGE)}
              meta={data.meta}
              runId={run}
              activeId={task}
            />

            {rows.length > PAGE && (
              <div className="mt-4 flex items-center justify-between text-sm text-muted">
                <span>
                  {page * PAGE + 1}–{Math.min(rows.length, (page + 1) * PAGE)} of {rows.length}
                </span>
                <div className="flex gap-2">
                  <button
                    disabled={page === 0}
                    onClick={() => setPage((p) => p - 1)}
                    className="rounded-md border border-line px-3 py-1.5 disabled:opacity-40"
                  >
                    Previous
                  </button>
                  <button
                    disabled={(page + 1) * PAGE >= rows.length}
                    onClick={() => setPage((p) => p + 1)}
                    className="rounded-md border border-line px-3 py-1.5 disabled:opacity-40"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </section>
        </>
      )}

      <AnimatePresence>
        {open && data && (
          <TaskDrawer
            key={open.id}
            task={open}
            meta={data.meta}
            onClose={() => (window.location.hash = `#/report/${run}`)}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

function RunHeader({ data }: { data: RunData }) {
  const m = data.meta;
  const o = m.overall;
  const reg = m.counts.regression ?? 0;
  const imp = m.counts.improvement ?? 0;
  return (
    <header className="pt-8">
      <div className="flex flex-wrap items-start justify-between gap-6">
        <div className="min-w-0">
          <h1 className="text-3xl font-semibold tracking-tight">{m.title}</h1>
          <p className="mt-1 text-muted">{m.blurb}</p>
          <p className="mt-3 font-mono text-[13px] text-muted">
            {shortModel(m.baseline)} → {shortModel(m.candidate)} · reasoning low · 3 tries per task ·{" "}
            {m.calls.toLocaleString("en-IN")} calls · ${m.fresh_cost_usd.toFixed(2)}
            {m.created_utc && <> · {m.created_utc.slice(0, 10)}</>}
          </p>
        </div>
        <div className="sm:text-right">
          <p className="text-xs text-faint">Gate decision</p>
          <p className="mt-1 text-2xl">
            <Verdict decision={m.decision} />
          </p>
        </div>
      </div>
      {m.reasons[0] && <p className="mt-4 max-w-3xl text-sm text-muted">{m.reasons[0]}</p>}

      <dl className="mt-8 grid grid-cols-2 gap-px overflow-hidden rounded-lg border border-line bg-line sm:grid-cols-4">
        <Metric label="Pass rate">
          {pct(o.base_rate)} <span className="text-faint">→</span> {pct(o.cand_rate)}
        </Metric>
        <Metric label="Change (95% range)">
          {signedPts(o.delta)} pts{" "}
          <span className="text-sm font-normal text-muted">
            {signedPts(o.ci_low)} to {signedPts(o.ci_high)}
          </span>
        </Metric>
        <Metric label="Got worse">
          <span className={reg ? "text-risk" : ""}>
            <ArrowDown aria-hidden className="mr-1 inline size-5 align-[-3px]" />
            {reg}
          </span>{" "}
          <span className="text-sm font-normal text-muted">tasks</span>
        </Metric>
        <Metric label="Got better">
          <span className={imp ? "text-go" : ""}>
            <ArrowUp aria-hidden className="mr-1 inline size-5 align-[-3px]" />
            {imp}
          </span>{" "}
          <span className="text-sm font-normal text-muted">tasks</span>
        </Metric>
      </dl>
    </header>
  );
}

function Metric({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="bg-bg px-5 py-4">
      <dt className="text-xs text-faint">{label}</dt>
      <dd className="mt-1 text-xl font-semibold tracking-tight">{children}</dd>
    </div>
  );
}

function SliceTable({
  data,
  active,
  onPick,
}: {
  data: RunData;
  active: string | null;
  onPick: (s: string) => void;
}) {
  const slices = data.meta.slices;
  const maxAbs = Math.max(0.05, ...slices.map((s) => Math.max(Math.abs(s.ci_low), Math.abs(s.ci_high))));
  return (
    <section aria-labelledby="slices-h" className="mt-12">
      <h2 id="slices-h" className="text-lg font-semibold">
        Where it changed
      </h2>
      <p className="text-sm text-muted">
        Each slice is tested on its own, with Holm correction. Click a row to filter the tasks.
      </p>
      <div className="mt-4 overflow-x-auto rounded-lg border border-line">
        <table className="w-full min-w-[760px] text-sm">
          <thead className="bg-surface text-left text-xs text-muted">
            <tr>
              <th className="px-4 py-2.5 font-medium">Slice</th>
              <th className="px-4 py-2.5 text-right font-medium">Tasks</th>
              <th className="px-4 py-2.5 text-right font-medium">{shortModel(data.meta.baseline)}</th>
              <th className="px-4 py-2.5 text-right font-medium">{shortModel(data.meta.candidate)}</th>
              <th className="w-[30%] px-4 py-2.5 font-medium">Change and 95% range</th>
              <th className="px-4 py-2.5 text-right font-medium">Worse / better</th>
              <th className="px-4 py-2.5 text-right font-medium">p (adjusted)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {slices.map((s) => {
              const on = active === s.slice;
              const [k] = s.slice.split("=");
              return (
                <tr
                  key={s.slice}
                  onClick={() => onPick(s.slice)}
                  className={`cursor-pointer transition-colors ${on ? "bg-accent-soft" : "hover:bg-surface"}`}
                >
                  <td className="px-4 py-2.5">
                    <button className="text-left font-medium" aria-pressed={on}>
                      {sliceLabel(s.slice)}
                    </button>
                    <span className="ml-2 text-xs text-faint">
                      {k === "category" ? "task" : k === "lang" ? "language" : "input"}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-right text-muted">{s.n}</td>
                  <td className="px-4 py-2.5 text-right">{pct(s.base_rate)}</td>
                  <td className="px-4 py-2.5 text-right">{pct(s.cand_rate)}</td>
                  <td className="px-4 py-2.5">
                    <RangeBar s={s} max={maxAbs} />
                  </td>
                  <td className="px-4 py-2.5 text-right">
                    <span className={s.b ? "text-risk" : "text-faint"}>{s.b}</span>
                    <span className="text-faint"> / </span>
                    <span className={s.c ? "text-go" : "text-faint"}>{s.c}</span>
                  </td>
                  <td className="px-4 py-2.5 text-right font-mono text-xs text-muted">
                    {s.p_adjusted == null ? "–" : s.p_adjusted < 0.001 ? "<0.001" : s.p_adjusted.toFixed(2)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function RangeBar({ s, max }: { s: { delta: number; ci_low: number; ci_high: number }; max: number }) {
  const x = (v: number) => 50 + (v / max) * 50;
  const worse = s.ci_high < 0;
  const better = s.ci_low > 0;
  const color = worse ? "var(--risk)" : better ? "var(--go)" : "var(--faint)";
  return (
    <div className="flex items-center gap-3">
      <div className="relative h-4 flex-1" aria-hidden>
        <div className="absolute inset-y-0 left-1/2 w-px bg-line" />
        <div
          className="absolute top-1/2 h-[3px] -translate-y-1/2 rounded-full opacity-60"
          style={{
            left: `${x(s.ci_low)}%`,
            width: `${Math.max(0.8, x(s.ci_high) - x(s.ci_low))}%`,
            background: color,
          }}
        />
        <div
          className="absolute top-1/2 size-2.5 -translate-x-1/2 -translate-y-1/2 rounded-full"
          style={{ left: `${x(s.delta)}%`, background: color }}
        />
      </div>
      <span className="w-14 text-right font-mono text-xs">{signedPts(s.delta)}</span>
    </div>
  );
}

function TaskTable({
  rows,
  meta,
  runId,
  activeId,
}: {
  rows: TaskRow[];
  meta: RunData["meta"];
  runId: string;
  activeId: string | null;
}) {
  if (!rows.length) {
    return (
      <p className="mt-6 rounded-lg border border-dashed border-line px-5 py-10 text-center text-muted">
        No tasks match.
      </p>
    );
  }
  return (
    <div className="mt-4 overflow-x-auto rounded-lg border border-line">
      <table className="w-full min-w-[820px] table-fixed text-sm">
        <thead className="bg-surface text-left text-xs text-muted">
          <tr>
            <th className="w-[34%] px-4 py-2.5 font-medium">Task</th>
            <th className="px-4 py-2.5 font-medium">{shortModel(meta.baseline)}</th>
            <th className="px-4 py-2.5 font-medium">{shortModel(meta.candidate)}</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-line">
          {rows.map((t) => (
            <tr
              key={t.id}
              className={`cursor-pointer align-top transition-colors ${activeId === t.id ? "bg-accent-soft" : "hover:bg-surface"}`}
              onClick={() => (window.location.hash = `#/report/${runId}/${t.id}`)}
            >
              <td className="px-4 py-3">
                <a
                  href={`#/report/${runId}/${t.id}`}
                  className="font-mono text-xs text-accent"
                  onClick={(e) => e.stopPropagation()}
                >
                  {t.id}
                </a>
                <p className="mt-0.5 text-xs text-faint">
                  {CATEGORY_LABEL[t.category] ?? t.category} · {sliceLabel(`lang=${t.lang}`)} · {t.modality}
                </p>
                <p className="mt-1.5 line-clamp-2 text-muted">{t.transcript ?? t.prompt}</p>
              </td>
              <SideCell side={t.base} />
              <SideCell side={t.cand} />
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SideCell({ side }: { side: TaskRow["base"] }) {
  const first = side.answers.find((a) => a.passed === side.pass) ?? side.answers[0];
  const mode = side.mode && side.mode !== "error" ? MODE_STYLE[side.mode] : null;
  const passes = side.answers.filter((a) => a.passed).length;
  return (
    <td className="px-4 py-3">
      <div className="flex items-center gap-2">
        <span className={`text-xs font-bold tracking-[0.06em] ${side.pass ? "text-go" : "text-risk"}`}>
          {side.pass ? "PASS" : "FAIL"}
        </span>
        <span className="text-xs text-faint">
          {passes}/{side.answers.length} tries
        </span>
        {mode && !side.pass && (
          <span className="flex items-center gap-1.5 text-xs text-muted">
            <span
              aria-hidden
              className={`size-2 rounded-[2px] ${mode.hatch ? "hatch" : ""}`}
              style={{ backgroundColor: mode.color }}
            />
            {mode.short}
          </span>
        )}
      </div>
      <p className="mt-1.5 line-clamp-3 font-mono text-[12.5px] leading-relaxed break-words text-fg/85">
        {first?.text || <span className="text-faint">(empty)</span>}
      </p>
    </td>
  );
}
