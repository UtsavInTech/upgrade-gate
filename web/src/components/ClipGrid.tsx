import { Table2, LayoutGrid } from "lucide-react";
import { useMemo, useState } from "react";
import type { E6, Mode } from "../data";
import { BASE, CAND, LANG_LABEL, shortModel } from "../data";
import { MODE_STYLE } from "./ui";

const ORDER: Mode[] = [
  "correct",
  "says it can't hear",
  "no answer (token limit)",
  "mixed",
  "confident wrong",
  "silent blank",
];
const LANGS = ["en", "hi", "hinglish"];
const KIND: Record<string, string> = {
  math: "spoken maths",
  extract: "order voice note",
  intent: "customer request",
};

// One square per voice clip, same position for both versions, coloured by the answer type the
// version gave most often over three tries (ties count as the worse type).
export function ClipGrid({ e6 }: { e6: E6 }) {
  const [hover, setHover] = useState<string | null>(null);
  const [asTable, setAsTable] = useState(false);
  const clips = e6.clips;
  const byId = useMemo(() => Object.fromEntries(clips.map((c) => [c.id, c])), [clips]);
  const count = (model: string, mode: Mode) => clips.filter((c) => c[model] === mode).length;
  const h = hover ? byId[hover] : null;

  return (
    <figure className="rounded-lg border border-line p-5 sm:p-7">
      <figcaption className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold">Every voice note, both versions</h3>
          <p className="text-sm text-muted">
            One square per clip ({clips.length} in total), coloured by what that version did in at least 2 of
            3 tries. Same clip, same position on both sides.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setAsTable((v) => !v)}
          aria-pressed={asTable}
          aria-label={asTable ? "Show as grid" : "Show as table"}
          className="inline-flex size-9 items-center justify-center rounded-md border border-line text-muted hover:text-fg"
        >
          {asTable ? (
            <LayoutGrid aria-hidden className="size-4" />
          ) : (
            <Table2 aria-hidden className="size-4" />
          )}
        </button>
      </figcaption>

      {asTable ? (
        <div className="mt-6 overflow-x-auto">
          <table className="w-full min-w-[480px] text-sm">
            <thead>
              <tr className="border-b border-line text-left text-muted">
                <th className="py-2 pr-4 font-medium">Most common answer per clip</th>
                <th className="py-2 pr-4 text-right font-medium">{shortModel(BASE)}</th>
                <th className="py-2 text-right font-medium">{shortModel(CAND)}</th>
              </tr>
            </thead>
            <tbody>
              {ORDER.map((m) => (
                <tr key={m} className="border-b border-line/60">
                  <td className="py-2.5 pr-4">{MODE_STYLE[m].label}</td>
                  <td className="py-2.5 pr-4 text-right font-semibold">{count(BASE, m)}</td>
                  <td className="py-2.5 text-right font-semibold">{count(CAND, m)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="mt-7 grid gap-8 md:grid-cols-2 md:gap-10">
          {[BASE, CAND].map((model) => (
            <div key={model}>
              <div className="mb-3 flex items-baseline justify-between">
                <span className="font-semibold">{shortModel(model)}</span>
                <span className="text-sm text-muted">
                  <span className="font-semibold text-fg">{count(model, "correct")}</span> right ·{" "}
                  <span className="font-semibold text-risk">
                    {count(model, "confident wrong") + count(model, "silent blank")}
                  </span>{" "}
                  wrong without warning
                </span>
              </div>
              <div className="space-y-3">
                {LANGS.map((lang) => (
                  <div key={lang} className="grid grid-cols-[64px_minmax(0,1fr)] items-center gap-3">
                    <span className="text-xs text-muted">{LANG_LABEL[lang]}</span>
                    <div className="grid grid-cols-[repeat(15,minmax(0,1fr))] gap-[3px]">
                      {clips
                        .filter((c) => c.lang === lang)
                        .map((c) => {
                          const m = c[model] as Mode;
                          const st = MODE_STYLE[m] ?? MODE_STYLE.mixed;
                          const dim = hover && hover !== c.id;
                          return (
                            <a
                              key={c.id}
                              href={`#/report/e6-audio/${c.id}`}
                              aria-label={`${c.id}: ${st.label}`}
                              onMouseEnter={() => setHover(c.id)}
                              onMouseLeave={() => setHover(null)}
                              onFocus={() => setHover(c.id)}
                              onBlur={() => setHover(null)}
                              className={`aspect-square rounded-[3px] transition-opacity duration-150 ${
                                st.hatch ? "hatch" : ""
                              } ${dim ? "opacity-35" : ""} ${
                                hover === c.id ? "ring-2 ring-fg ring-offset-1 ring-offset-bg" : ""
                              }`}
                              style={{ backgroundColor: st.color }}
                            />
                          );
                        })}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="mt-6 min-h-12 border-t border-line pt-4 text-sm" aria-live="polite">
        {h ? (
          <p className="text-muted">
            <span className="font-mono text-xs text-faint">{h.id}</span> · {LANG_LABEL[h.lang]} {KIND[h.kind]}
            . {shortModel(BASE)}: <span className="text-fg">{(MODE_STYLE[h[BASE] as Mode] ?? MODE_STYLE.mixed).label}</span>.{" "}
            {shortModel(CAND)}: <span className="text-fg">{(MODE_STYLE[h[CAND] as Mode] ?? MODE_STYLE.mixed).label}</span>. Click to
            open the answers.
          </p>
        ) : (
          <ul className="flex flex-wrap gap-x-5 gap-y-2" aria-label="Legend">
            {ORDER.map((m) => {
              const st = MODE_STYLE[m] ?? MODE_STYLE.mixed;
              return (
                <li key={m} className="flex items-center gap-2 text-muted">
                  <span
                    aria-hidden
                    className={`size-3 rounded-[3px] ${st.hatch ? "hatch" : ""}`}
                    style={{ backgroundColor: st.color }}
                  />
                  {st.label}
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </figure>
  );
}
