import { motion } from "motion/react";
import { AlertTriangle, Ban, CheckCircle2, CircleDashed, EarOff, HelpCircle, XCircle } from "lucide-react";
import type { ReactNode } from "react";
import type { Mode } from "../data";

export function Section({
  id,
  index,
  eyebrow,
  title,
  lede,
  children,
}: {
  id: string;
  index: string;
  eyebrow: string;
  title: ReactNode;
  lede?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section id={id} data-slide className="border-t border-line py-20 sm:py-28">
      <div className="mx-auto w-full max-w-6xl px-4 sm:px-8">
        <motion.header
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.5, ease: [0.2, 0.7, 0.2, 1] }}
          className="mb-12 grid gap-6 lg:grid-cols-[minmax(0,7fr)_minmax(0,5fr)] lg:items-end"
        >
          <div>
            <p className="mb-4 flex items-center gap-3 text-sm font-medium text-muted">
              <span className="font-mono text-xs text-faint">{index}</span>
              <span className="h-px w-8 bg-line" aria-hidden />
              {eyebrow}
            </p>
            <h2 className="text-[clamp(2rem,4.6vw,3.4rem)] leading-[1.05] font-semibold tracking-[-0.025em] text-balance">
              {title}
            </h2>
          </div>
          {lede && <div className="text-lg leading-relaxed text-muted text-pretty">{lede}</div>}
        </motion.header>
        {children}
      </div>
    </section>
  );
}

export function Reveal({
  children,
  delay = 0,
  className = "",
}: {
  children: ReactNode;
  delay?: number;
  className?: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.45, delay, ease: [0.2, 0.7, 0.2, 1] }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

const VERDICT: Record<string, { label: string; cls: string; Icon: typeof CheckCircle2 }> = {
  go: { label: "GO", cls: "bg-go-soft text-go", Icon: CheckCircle2 },
  "no-go": { label: "NO-GO", cls: "bg-risk-soft text-risk", Icon: XCircle },
  inconclusive: { label: "INCONCLUSIVE", cls: "bg-hold-soft text-hold", Icon: HelpCircle },
  risk: { label: "RISK FOUND", cls: "bg-risk-soft text-risk", Icon: AlertTriangle },
};

export function Verdict({ decision, size = "sm" }: { decision: string; size?: "sm" | "lg" }) {
  const v = VERDICT[decision] ?? VERDICT.inconclusive;
  const big = size === "lg";
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-md font-semibold tracking-wide ${v.cls} ${
        big ? "px-3 py-1.5 text-sm" : "px-2 py-0.5 text-xs"
      }`}
    >
      <v.Icon aria-hidden className={big ? "size-4" : "size-3.5"} strokeWidth={2.4} />
      {v.label}
    </span>
  );
}

export const MODE_STYLE: Record<
  Mode,
  { color: string; label: string; short: string; Icon: typeof CheckCircle2; hatch?: boolean }
> = {
  correct: { color: "var(--s-correct)", label: "Correct", short: "Correct", Icon: CheckCircle2 },
  "says it can't hear": {
    color: "var(--s-deny)",
    label: "Says it can't hear",
    short: "Can't hear",
    Icon: EarOff,
  },
  "no answer (token limit)": {
    color: "var(--s-none)",
    label: "No answer (ran out of tokens)",
    short: "No answer",
    Icon: CircleDashed,
  },
  "confident wrong": { color: "var(--s-wrong)", label: "Confidently wrong", short: "Wrong", Icon: XCircle },
  "silent blank": {
    color: "var(--s-blank)",
    label: "Blank fields, no warning",
    short: "Blank",
    Icon: Ban,
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
      <m.Icon aria-hidden className="size-3.5" />
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
