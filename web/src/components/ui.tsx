import type { ReactNode } from "react";
import type { Mode } from "../data";

export function Section({
  id,
  eyebrow,
  title,
  lede,
  children,
}: {
  id: string;
  index?: string;
  eyebrow: string;
  title: ReactNode;
  lede?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section id={id} data-slide className="border-t border-line py-20 sm:py-28">
      <div className="mx-auto w-full max-w-6xl px-4 sm:px-8">
        <header className="mb-12 grid gap-6 lg:grid-cols-[minmax(0,7fr)_minmax(0,5fr)] lg:items-end">
          <div>
            <p className="mb-4 text-sm font-medium text-muted">{eyebrow}</p>
            <h2 className="text-[clamp(2rem,4.6vw,3.4rem)] leading-[1.05] font-semibold tracking-[-0.025em] text-balance">
              {title}
            </h2>
          </div>
          {lede && <div className="text-lg leading-relaxed text-muted text-pretty">{lede}</div>}
        </header>
        {children}
      </div>
    </section>
  );
}

export function Reveal({
  children,
  className = "",
}: {
  children: ReactNode;
  delay?: number;
  className?: string;
}) {
  return <div className={className}>{children}</div>;
}

// The decision is a word, not a badge: colour reinforces it, the text carries it.
const VERDICT: Record<string, { label: string; cls: string }> = {
  go: { label: "GO", cls: "text-go" },
  "no-go": { label: "NO-GO", cls: "text-risk" },
  inconclusive: { label: "INCONCLUSIVE", cls: "text-hold" },
  risk: { label: "RISK", cls: "text-risk" },
};

export function Verdict({ decision }: { decision: string }) {
  const v = VERDICT[decision] ?? VERDICT.inconclusive;
  return <span className={`text-xs font-bold tracking-[0.08em] ${v.cls}`}>{v.label}</span>;
}

export const MODE_STYLE: Record<Mode, { color: string; label: string; short: string; hatch?: boolean }> = {
  correct: { color: "var(--s-correct)", label: "Correct", short: "Correct" },
  "says it can't hear": {
    color: "var(--s-deny)",
    label: "Says it can't hear",
    short: "Can't hear",
  },
  "no answer (token limit)": {
    color: "var(--s-none)",
    label: "No answer (ran out of tokens)",
    short: "No answer",
  },
  "confident wrong": { color: "var(--s-wrong)", label: "Wrong, no warning", short: "Wrong" },
  mixed: { color: "var(--s-muted)", label: "Mixed (no answer type in 2 of 3 tries)", short: "Mixed" },
  "silent blank": {
    color: "var(--s-blank)",
    label: "Blank fields, no warning",
    short: "Blank",
    hatch: true,
  },
};

export function ModeChip({ mode }: { mode: Mode }) {
  const m = MODE_STYLE[mode];
  return (
    <span className="inline-flex items-center gap-1.5 text-xs font-medium text-muted">
      <span
        aria-hidden
        className={`inline-block size-2.5 rounded-[3px] ${m.hatch ? "hatch" : ""}`}
        style={{ backgroundColor: m.color }}
      />
      {m.label}
    </span>
  );
}

export function Stat({ value, label, sub }: { value: ReactNode; label: string; sub?: ReactNode }) {
  return (
    <div>
      <div className="text-[clamp(2rem,4vw,2.8rem)] leading-none font-semibold tracking-[-0.03em]">
        {value}
      </div>
      <div className="mt-2 text-sm font-medium text-fg">{label}</div>
      {sub && <div className="mt-1 text-sm text-muted">{sub}</div>}
    </div>
  );
}
