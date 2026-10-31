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
  by_input?: Record<string, Omit<Behaviour, "by_input"> & { label: string }>;
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

export type E7 = {
  status: "done" | "not run";
  speakers?: string[];
  clips?: number;
  confirmed?: boolean;
  silent?: { baseline: number; candidate: number; p: number };
  blank_answers?: Record<string, number>;
  items?: { n: number; worse: number; better: number; p: number };
  blank_clips?: { baseline: number; candidate: number; p: number };
  wrong_only_clips?: { baseline: number; candidate: number };
  accuracy?: Comparison | null;
  decision?: string;
  fresh_cost_usd?: number;
};

export type E4 = {
  status: "done" | "not run";
  clips: number;
  calls: number;
  fresh_cost_usd: number;
  levels: {
    level: string;
    answers: number;
    correct: number;
    modes: Record<string, number>;
    cost_per_1000: number;
    avg_output_tokens: number;
  }[];
  minimal_vs_xhigh: Comparison;
};

export type E9Describe = {
  answers: number;
  correct: number;
  clips_correct_majority: number;
  clips: number;
  types: Record<string, number>;
  order_number_right: string;
  pincode_right: string;
  latency_ms_median: number | null;
  latency_ms_p90: number | null;
  usd_per_1000_clips: number;
  asr_usd_per_1000_clips: number;
};

export type E9Set = {
  run: string;
  speakers?: number | null; // real-voice sets: how many people recorded
  describe: Record<string, E9Describe>;
  gates: Record<string, { decision: string; reasons: string[] }>;
  overall: {
    delta: number;
    ci_low: number;
    ci_high: number;
    n: number;
    silent: { baseline: number; candidate: number };
    silent_items_p: number;
  } | null;
  loss: {
    assumption: string;
    order_notes: number;
    by_route: Record<string, { per_1000: Record<string, number>; inr_per_1000: [number, number] }>;
  } | null;
};

// E9: the transcribe route. synth = 135 text-to-speech notes (primary); real = every real speaker pooled (E10).
export type E9 = { status: "done" | "missing"; route: string; baseline: string; direct: string; sets: Record<string, E9Set> };

export type Site = {
  generated_utc: string;
  spend: { total_usd: number; limit_usd: number };
  e1: E1;
  e6: E6;
  e3: E3;
  e7?: E7;
  e4?: E4;
  e9?: E9;
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
  // "transcribe+spark-1.3@low" is the E9 route: Voice Transcribe, then Spark on the transcript.
  if (id.startsWith("transcribe+")) return "Transcribe → " + shortModel(id.slice("transcribe+".length));
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
