// Shapes of web/public/data/runs/<run>.json (scripts/export_web.py → run_detail).
import type { Mode } from "./data";

export type GateSlice = {
  slice: string;
  n: number;
  base_rate: number;
  cand_rate: number;
  delta: number;
  ci_low: number;
  ci_high: number;
  b: number;
  c: number;
  p_value: number;
  p_adjusted: number | null;
  verdict: string;
};

export type Attempt = {
  repeat: number;
  passed: boolean | null;
  strict: boolean | null;
  detail: string;
  mode: Mode | "error";
  text: string;
};

export type Side = { pass: boolean | null; mode: Mode | "error" | null; answers: Attempt[] };

export type Status = "regression" | "improvement" | "both fail" | "both pass";

export type TaskRow = {
  id: string;
  category: string;
  lang: string;
  modality: string;
  prompt: string;
  transcript: string | null;
  expected: string;
  attachment: string | null;
  status: Status;
  base: Side;
  cand: Side;
};

export type RunMeta = {
  run: string;
  title: string;
  blurb: string;
  baseline: string;
  candidate: string;
  decision: string;
  reasons: string[];
  created_utc: string | null;
  overall: GateSlice;
  slices: GateSlice[];
  calls: number;
  fresh_cost_usd: number;
  reused_answers: number;
  counts: Partial<Record<Status, number>>;
  accuracy_decision?: string;
  behaviour?: import("./data").Behaviour | null;
};

export type RunIndex = Pick<
  RunMeta,
  | "run"
  | "title"
  | "blurb"
  | "baseline"
  | "candidate"
  | "decision"
  | "calls"
  | "fresh_cost_usd"
  | "created_utc"
  | "counts"
>;

export type RunData = { meta: RunMeta; tasks: TaskRow[] };

const cache = new Map<string, Promise<RunData>>();

export function loadRun(run: string): Promise<RunData> {
  if (!cache.has(run)) {
    cache.set(
      run,
      fetch(`data/runs/${run}.json`).then((r) => {
        if (!r.ok) throw new Error(`${run}: HTTP ${r.status}`);
        return r.json();
      }),
    );
  }
  return cache.get(run)!;
}

export async function loadRuns(): Promise<RunIndex[]> {
  const r = await fetch("data/runs.json", { cache: "no-store" });
  if (!r.ok) throw new Error(`runs.json: HTTP ${r.status}`);
  return r.json();
}

export function pct(x: number, digits = 1): string {
  return `${(x * 100).toFixed(digits)}%`;
}

export function signedPts(x: number): string {
  const v = (x * 100).toFixed(1);
  return x > 0 ? `+${v}` : v === "-0.0" ? "0.0" : v;
}

export const CATEGORY_LABEL: Record<string, string> = {
  math: "Maths",
  extraction: "Extraction",
  classification: "Intent",
  instruction: "Instructions",
  "doc-image": "Invoices",
};

export function sliceLabel(s: string): string {
  const [k, v] = s.split("=");
  if (!v) return "Overall";
  if (k === "lang") return { en: "English", hi: "Hindi", hinglish: "Hinglish" }[v] ?? v;
  if (k === "category") return CATEGORY_LABEL[v] ?? v;
  if (k === "modality")
    return { text: "Text input", image: "Image input", pdf: "PDF input", audio: "Audio input" }[v] ?? v;
  return v;
}

export function matchesSlice(t: TaskRow, slice: string | null): boolean {
  if (!slice) return true;
  const [k, v] = slice.split("=");
  return (t as unknown as Record<string, string>)[k] === v;
}
