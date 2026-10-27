// Shapes of web/public/data/site.json, written by scripts/export_web.py.

export const BASE = "spark-1.2@low";
export const CAND = "spark-1.3@low";

export type Comparison = {
  slice: string;
  n: number;
  delta: number;
  ci: [number, number];
  regressions: number;
  improvements: number;
  p: number;
};

export type Tally = { correct: number; total: number };

export type E1Example = {
  task_id: string;
  candidate: string;
  lang: string;
  category: string;
  prompt: string;
  answer: string;
  accepted: unknown;
  old: string;
  new: string;
  strict: boolean | null;
};

export type E1 = {
  calls: number;
  fresh_cost_usd: number;
  decision: string;
  before: Comparison | null;
  after: Comparison;
  strict: Comparison;
  per_answer: Record<string, Tally>;
  slices: { key: string; value: string; n: number; before?: Comparison; after?: Comparison }[];
  examples: E1Example[];
};

export type Mode =
  "correct" | "says it can't hear" | "confident wrong" | "silent blank" | "no answer (token limit)" | "mixed";

export type AudioAnswer = { text: string; mode: Mode; says_cant_hear: boolean };

export type AudioExample = {
  task_id: string;
  why: "silent" | "denies-but-hears";
  kind: "math" | "extract" | "intent";
  lang: string;
  voice: string;
  transcript: string;
  prompt: string;
  expected: unknown;
  audio: string;
  answers: Record<string, AudioAnswer[]>;
};

export type FailureTest = {
  flag: string;
  lang: string;
  tasks: number;
  p: number;
  [model: string]: string | number;
};

export type Behaviour = {
  tasks: number;
  flagged: boolean;
  reason?: string;
  silent: { baseline: number; candidate: number; p: number };
  abstain: { baseline: number; candidate: number; p: number };
};

export type E6 = {
  calls: number;
  fresh_cost_usd: number;
  decision: string;
  gate_reason: string;
  tasks_needed: number | null;
  accuracy: Record<string, Tally>;
  modes: Mode[];
  mode_counts: Record<string, number>;
  deny_with_answer: Record<string, number>;
  tests: FailureTest[];
  examples: AudioExample[];
  gate_decision?: string;
  behaviour?: Behaviour;
  clips: ({ id: string; lang: string; kind: string } & Record<string, string>)[];
};

export type E3 = {
  status: "done" | "running" | "not run";
  standard?: string;
  contributor?: string;
  calls?: number;
  fresh_cost_usd?: number;
  decision?: string;
  overall?: Comparison;
  per_answer?: Record<string, Tally>;
  cost_per_1000?: Record<string, number>;
};

export type Site = {
  generated_utc: string;
  spend: { total_usd: number; limit_usd: number };
  e1: E1;
  e6: E6;
  e3: E3;
};

export async function loadSite(): Promise<Site> {
  const res = await fetch("data/site.json", { cache: "no-store" });
  if (!res.ok) throw new Error(`site.json: HTTP ${res.status}`);
  return res.json();
}

export const LANG_LABEL: Record<string, string> = {
  en: "English",
  hi: "Hindi",
  hinglish: "Hinglish",
  all: "All",
};

export function pts(delta: number, digits = 1): string {
  const v = delta * 100;
  const s = v.toFixed(digits);
  return (v > 0 ? "+" : v === 0 ? "" : "") + (s === "-0.0" ? "0.0" : s);
}

export function pval(p: number): string {
  if (p >= 0.01) return p.toFixed(2);
  if (p >= 0.001) return p.toFixed(3);
  const [m, e] = p.toExponential(1).split("e");
  return `${m} × 10${superscript(e)}`;
}

function superscript(e: string): string {
  const map: Record<string, string> = {
    "-": "⁻",
    "0": "⁰",
    "1": "¹",
    "2": "²",
    "3": "³",
    "4": "⁴",
    "5": "⁵",
    "6": "⁶",
    "7": "⁷",
    "8": "⁸",
    "9": "⁹",
  };
  return e
    .replace("+", "")
    .split("")
    .map((c) => map[c] ?? c)
    .join("");
}

export function shortModel(id: string): string {
  return id.replace("spark-", "Spark ").replace("@low", "").replace("-c", " Contributor");
}

export function formatExpected(v: unknown): string {
  if (v && typeof v === "object" && !Array.isArray(v)) {
    return Object.entries(v as Record<string, unknown>)
      .map(([k, x]) => `${k}: ${Array.isArray(x) ? x[0] : String(x)}`)
      .join(" · ");
  }
  if (Array.isArray(v)) return v.join(" / ");
  return String(v);
}
