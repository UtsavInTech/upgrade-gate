// VoiceOrder data: the server's config (serve.py / voiceorder/server.py) or, on a static host, the
// committed export web/public/data/voiceorder.json. Saved examples never trigger a model call.

export type Sample = { id: string; lang: string; transcript: string; audio: string };

export type Result = {
  model: string;
  text: string;
  error: string | null;
  order: Record<string, unknown> | null;
  checks: { status: "saved" | "rejected" | "ask_customer"; message: string; fields: Record<string, boolean> };
  cost_usd: number;
  reused: boolean;
  latency_ms: number | null;
  truth?: { correct: boolean; expected: Record<string, string> }; // saved examples only: a known answer
  transcript?: string | null; // transcribe route only: what Voice Transcribe heard
};

export type Config = {
  shipping: string; // read from release/model.json, never assumed
  candidate: string;
  route?: string;
  route_url?: string;
  pr: string;
  samples: Sample[];
  static?: boolean; // samples come with saved answers
  live?: boolean; // the server accepts new recordings (paid, capped)
  results?: Record<string, Record<string, Result>>;
};

export const FIELDS: [string, string][] = [
  ["order_number", "Order number"],
  ["pincode", "Pincode"],
  ["city", "City"],
];

export const DEFAULT_SAMPLE = "audio-synth-extract-03-hi";

let cached: Promise<Config> | null = null;

export function loadVoiceOrder(): Promise<Config> {
  if (!cached) {
    const json = (r: Response) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`)));
    cached = fetch("/api/voiceorder/config")
      .then(json)
      .then((c: Config) => (c.results ? c : fetch("data/voiceorder.json").then(json).then((s: Config) => ({ ...s, ...c, results: s.results, static: true }))))
      .catch(() => fetch("data/voiceorder.json").then(json));
    cached.catch(() => (cached = null));
  }
  return cached;
}

/** The role each model plays, read from the config rather than hardcoded. */
export function roleOf(cfg: Config, m: string): "shipping" | "candidate" | "route" {
  if (m === cfg.shipping) return "shipping";
  if (m === cfg.route) return "route";
  return "candidate";
}

export function modelsOf(cfg: Config): string[] {
  return [...new Set([cfg.shipping, cfg.candidate, ...(cfg.route ? [cfg.route] : [])])];
}

/** Does a saved field match what the customer said? undefined when there is no reference (a new recording). */
export function fieldMatches(r: Result, key: string): boolean | undefined {
  const exp = r.truth?.expected[key];
  if (exp === undefined) return undefined;
  const got = String(r.order?.[key] ?? "").trim();
  if (key === "city") return got.toLowerCase() === String(exp).toLowerCase();
  return got.replace(/\D/g, "") === String(exp);
}

export type Outcome = { label: string; tone: "go" | "risk" | "hold" | "muted"; detail: string };

export function outcomeOf(r: Result): Outcome {
  if (r.checks.status === "ask_customer")
    return { label: "Asks the customer", tone: "hold", detail: "The model said it couldn’t hear the note." };
  if (r.checks.status === "rejected")
    return { label: "Order rejected", tone: "risk", detail: "Fails the shop’s format check, so the order is lost unless someone follows up." };
  if (!r.truth) return { label: "Order saved", tone: "muted", detail: "Passes the format check. A new recording has no known answer to compare with." };
  return r.truth.correct
    ? { label: "Correct order saved", tone: "go", detail: "Passes the format check and matches what the customer said." }
    : { label: "Wrong order saved", tone: "risk", detail: "Passes the format check, but a value doesn’t match what the customer said." };
}
