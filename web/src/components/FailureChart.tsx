import { AnimatePresence, LayoutGroup, motion } from "motion/react";
import { Table2, BarChart3 } from "lucide-react";
import { useState } from "react";
import type { E6, Mode } from "../data";
import { BASE, CAND, LANG_LABEL, shortModel } from "../data";
import { MODE_STYLE } from "./ui";

const LANGS = ["all", "en", "hi", "hinglish"];
// Stack order: what users can see first (correct, an honest "can't hear"), then what they can't.
const ORDER: Mode[] = [
  "correct",
  "says it can't hear",
  "no answer (token limit)",
  "confident wrong",
  "silent blank",
];

export function FailureChart({ e6 }: { e6: E6 }) {
  const [lang, setLang] = useState("all");
  const [asTable, setAsTable] = useState(false);
  const [hover, setHover] = useState<{ model: string; mode: Mode } | null>(null);
  const count = (model: string, mode: Mode) => e6.mode_counts[`${model}|${lang}|${mode}`] ?? 0;
  const total = (model: string) => ORDER.reduce((s, m) => s + count(model, m), 0);

  return (
    <figure className="rounded-lg border border-line bg-surface p-5 sm:p-7">
      <figcaption className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold">How every audio answer turned out</h3>
          <p className="text-sm text-muted">405 answers per version: 135 clips × 3 repeats</p>
        </div>
        <div className="flex items-center gap-2">
          <LayoutGroup id="lang">
            <div role="tablist" aria-label="Language" className="flex rounded-lg bg-bg p-1">
              {LANGS.map((l) => (
                <button
                  key={l}
                  role="tab"
                  aria-selected={lang === l}
                  onClick={() => setLang(l)}
                  className={`relative rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                    lang === l ? "text-fg" : "text-muted hover:text-fg"
                  }`}
                >
                  {lang === l && (
                    <motion.span
                      layoutId="lang-pill"
                      className="absolute inset-0 rounded-md bg-surface-2"
                      transition={{ type: "spring", stiffness: 420, damping: 34 }}
                    />
                  )}
                  <span className="relative">{LANG_LABEL[l]}</span>
                </button>
              ))}
            </div>
          </LayoutGroup>
          <button
            type="button"
            onClick={() => setAsTable((v) => !v)}
            aria-pressed={asTable}
            className="inline-flex size-9 items-center justify-center rounded-lg border border-line bg-bg text-muted hover:text-fg"
            aria-label={asTable ? "Show as chart" : "Show as table"}
          >
            {asTable ? (
              <BarChart3 aria-hidden className="size-4" />
            ) : (
              <Table2 aria-hidden className="size-4" />
            )}
          </button>
        </div>
      </figcaption>

      {asTable ? (
        <div className="mt-6 overflow-x-auto">
          <table className="w-full min-w-[520px] text-sm">
            <thead>
              <tr className="border-b border-line text-left text-muted">
                <th className="py-2 pr-4 font-medium">Answer type</th>
                {[BASE, CAND].map((m) => (
                  <th key={m} className="py-2 pr-4 text-right font-medium">
                    {shortModel(m)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {ORDER.map((mode) => (
                <tr key={mode} className="border-b border-line/60">
                  <td className="py-2.5 pr-4">{MODE_STYLE[mode].label}</td>
                  {[BASE, CAND].map((m) => (
                    <td key={m} className="py-2.5 pr-4 text-right font-semibold">
                      {count(m, mode)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="mt-8 space-y-6">
          {[BASE, CAND].map((model) => {
            const t = total(model) || 1;
            return (
              <div key={model}>
                <div className="mb-2 flex items-baseline justify-between text-sm">
                  <span className="font-semibold">{shortModel(model)}</span>
                  <span className="text-muted">
                    {count(model, "correct")} of {total(model)} correct
                  </span>
                </div>
                <div
                  className="flex h-11 gap-[2px] overflow-hidden rounded-[6px]"
                  role="img"
                  aria-label={`${shortModel(model)}: ${ORDER.map((m) => `${MODE_STYLE[m].label} ${count(model, m)}`).join(", ")}`}
                >
                  {ORDER.map((mode) => {
                    const n = count(model, mode);
                    const w = (n / t) * 100;
                    const st = MODE_STYLE[mode];
                    const active = hover && hover.model === model && hover.mode === mode;
                    return (
                      <motion.div
                        key={mode}
                        initial={false}
                        animate={{ width: `${w}%`, opacity: hover && !active ? 0.55 : 1 }}
                        transition={{ type: "spring", stiffness: 160, damping: 26 }}
                        onMouseEnter={() => setHover({ model, mode })}
                        onMouseLeave={() => setHover(null)}
                        className={`relative flex min-w-0 items-center justify-center ${st.hatch ? "hatch" : ""}`}
                        style={{ backgroundColor: st.color }}
                      >
                        {w > 6 && <span className="text-xs font-semibold text-white">{n}</span>}
                      </motion.div>
                    );
                  })}
                </div>
              </div>
            );
          })}
          <div className="min-h-6 text-sm" aria-live="polite">
            <AnimatePresence mode="wait">
              {hover && (
                <motion.p
                  key={hover.model + hover.mode}
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.15 }}
                  className="text-muted"
                >
                  <span className="font-semibold text-fg">{shortModel(hover.model)}</span> ·{" "}
                  {MODE_STYLE[hover.mode].label}:{" "}
                  <span className="font-semibold text-fg">{count(hover.model, hover.mode)}</span> answers (
                  {Math.round((count(hover.model, hover.mode) / (total(hover.model) || 1)) * 100)}%)
                </motion.p>
              )}
            </AnimatePresence>
          </div>
        </div>
      )}

      <ul className="mt-2 flex flex-wrap gap-x-5 gap-y-2" aria-label="Legend">
        {ORDER.map((mode) => {
          const st = MODE_STYLE[mode];
          return (
            <li key={mode} className="flex items-center gap-2 text-sm text-muted">
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
    </figure>
  );
}
