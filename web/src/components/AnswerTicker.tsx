import { useEffect, useState } from "react";
import type { RunData } from "../report";
import { DigitDiff } from "./TextFx";

type Said = { id: string; lang: string; text: string };
type Got = { id: string; lang: string; order: string; pin: string; wantOrder: string; wantPin: string };

const LANG: Record<string, string> = { en: "English", hi: "Hindi", hinglish: "Hinglish" };

function firstSentence(t: string) {
  const s = t.replace(/\s+/g, " ").trim();
  const m = s.match(/^.{20,170}?[.!?](\s|$)/);
  return m ? m[0].trim() : s.slice(0, 150) + "…";
}

function field(s: string, name: string) {
  const m = s.match(new RegExp(`${name}:\\s*([^·]+)`));
  return m ? m[1].trim() : "";
}

/** Real answers from the saved E6 run. */
function pick(run: RunData) {
  const said: Said[] = [];
  const got: Got[] = [];
  const seen = new Set<string>();
  for (const t of run.tasks) {
    for (const a of t.base.answers) {
      if (a.mode !== "says it can't hear") continue;
      const text = firstSentence(a.text);
      if (seen.has(text)) continue;
      seen.add(text);
      said.push({ id: t.id, lang: t.lang, text });
      break;
    }
    if (t.category !== "extract" && !t.id.includes("extract")) continue;
    for (const a of t.cand.answers) {
      if (a.mode !== "confident wrong" && a.mode !== "silent blank") continue;
      try {
        const j = JSON.parse(a.text) as Record<string, string>;
        const g = {
          id: t.id,
          lang: t.lang,
          order: String(j.order_number ?? ""),
          pin: String(j.pincode ?? ""),
          wantOrder: field(t.expected, "order_number"),
          wantPin: field(t.expected, "pincode"),
        };
        const key = `${g.order}|${g.pin}`;
        if (seen.has(key) || (g.order === g.wantOrder && g.pin === g.wantPin)) continue;
        seen.add(key);
        got.push(g);
        break;
      } catch {
        /* not JSON: skip */
      }
    }
  }
  return { said: said.slice(0, 12), got: got.slice(0, 14) };
}

function Row({ children, seconds, reverse }: { children: React.ReactNode; seconds: number; reverse?: boolean }) {
  // Two copies, so the -50% loop is seamless.
  return (
    <div className="marquee-wrap overflow-hidden" tabIndex={0} aria-label="Scrolling examples; hover or focus to pause">
      <div
        className="marquee py-2"
        style={{ ["--marquee-s" as string]: `${seconds}s`, animationDirection: reverse ? "reverse" : "normal" }}
      >
        <ul className="flex items-start gap-4 pr-4">{children}</ul>
        <ul aria-hidden className="flex items-start gap-4 pr-4">
          {children}
        </ul>
      </div>
    </div>
  );
}

export function AnswerTicker() {
  const [data, setData] = useState<ReturnType<typeof pick> | null>(null);
  useEffect(() => {
    let live = true;
    fetch("data/runs/e6-audio.json")
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((run: RunData) => live && setData(pick(run)))
      .catch(() => live && setData({ said: [], got: [] }));
    return () => {
      live = false;
    };
  }, []);

  if (!data) return <div className="h-[196px]" aria-busy="true" />;
  if (!data.said.length && !data.got.length) return null;

  return (
    <div className="space-y-3">
      <div>
        <p className="stamp mb-1 px-4 sm:px-8">
          <span className="mr-2 inline-block size-2 rounded-[2px] align-middle" style={{ background: "var(--s-deny)" }} />
          Spark 1.2, when it struggled · it says so
        </p>
        <Row seconds={95}>
          {data.said.map((s) => (
            <li
              key={s.id}
              className="w-[min(78vw,26rem)] shrink-0 rounded-sm border-l-2 bg-card px-4 py-3"
              style={{ borderColor: "var(--s-deny)" }}
            >
              <q className="prose-serif text-[15px] leading-snug italic">{s.text}</q>
              <span className="stamp mt-2 block">
                {LANG[s.lang] ?? s.lang} voice note · {s.id.replace("audio-synth-", "")}
              </span>
            </li>
          ))}
        </Row>
      </div>
      <div>
        <p className="stamp mb-1 px-4 sm:px-8">
          <span className="mr-2 inline-block size-2 rounded-[2px] align-middle" style={{ background: "var(--s-wrong)" }} />
          Spark 1.3 on the same kind of note · it saves this, no warning
        </p>
        <Row seconds={80} reverse>
          {data.got.map((g) => (
            <li
              key={`${g.id}-${g.pin}`}
              className="w-[min(78vw,21rem)] shrink-0 rounded-sm border-l-2 bg-card px-4 py-3 font-mono text-[13px]"
              style={{ borderColor: "var(--s-wrong)" }}
            >
              <span className="block">
                <span className="text-faint">order </span>
                <DigitDiff got={g.order} want={g.wantOrder} />
                <span className="text-faint"> · pin </span>
                <DigitDiff got={g.pin} want={g.wantPin} />
              </span>
              <span className="mt-1 block text-faint">
                said: {g.wantOrder} · {g.wantPin}
              </span>
              <span className="stamp mt-2 block">
                {LANG[g.lang] ?? g.lang} voice note · {g.id.replace("audio-synth-", "")}
              </span>
            </li>
          ))}
        </Row>
      </div>
    </div>
  );
}
