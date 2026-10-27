import { motion } from "motion/react";
import { X } from "lucide-react";
import { useEffect, useRef } from "react";
import { shortModel } from "../data";
import type { RunMeta, TaskRow } from "../report";
import { CATEGORY_LABEL, sliceLabel } from "../report";
import { MODE_STYLE } from "./ui";

const STATUS_TEXT: Record<TaskRow["status"], { text: string; cls: string }> = {
  regression: { text: "Got worse", cls: "text-risk" },
  improvement: { text: "Got better", cls: "text-go" },
  "both fail": { text: "Both fail", cls: "text-hold" },
  "both pass": { text: "Both pass", cls: "text-muted" },
};

export function TaskDrawer({ task, meta, onClose }: { task: TaskRow; meta: RunMeta; onClose: () => void }) {
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    closeRef.current?.focus();
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = prev;
    };
  }, [onClose]);

  const st = STATUS_TEXT[task.status];
  const att = task.attachment;

  return (
    <div className="fixed inset-0 z-50" role="dialog" aria-modal="true" aria-labelledby="drawer-title">
      <motion.button
        aria-label="Close"
        tabIndex={-1}
        onClick={onClose}
        className="absolute inset-0 bg-black/30"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
      />
      <motion.aside
        initial={{ x: "100%" }}
        animate={{ x: 0 }}
        exit={{ x: "100%" }}
        transition={{ type: "spring", stiffness: 380, damping: 40 }}
        className="absolute inset-y-0 right-0 flex w-full max-w-3xl flex-col border-l border-line bg-bg shadow-2xl"
      >
        <div className="flex items-start justify-between gap-4 border-b border-line px-5 py-4 sm:px-7">
          <div className="min-w-0">
            <p className={`text-xs font-bold tracking-[0.06em] uppercase ${st.cls}`}>{st.text}</p>
            <h2 id="drawer-title" className="mt-1 truncate font-mono text-sm">
              {task.id}
            </h2>
            <p className="mt-0.5 text-xs text-faint">
              {CATEGORY_LABEL[task.category] ?? task.category} · {sliceLabel(`lang=${task.lang}`)} ·{" "}
              {task.modality}
            </p>
          </div>
          <button
            ref={closeRef}
            onClick={onClose}
            aria-label="Close task"
            className="inline-flex size-9 shrink-0 items-center justify-center rounded-md border border-line text-muted hover:text-fg"
          >
            <X aria-hidden className="size-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-6 sm:px-7">
          {att && att.endsWith(".m4a") && (
            <audio controls src={att} className="mb-5 w-full">
              <a href={att}>Download the clip</a>
            </audio>
          )}
          {att && /\.(png|jpe?g|webp)$/i.test(att) && (
            <a
              href={att}
              target="_blank"
              rel="noreferrer"
              className="mb-5 block overflow-hidden rounded-md border border-line"
            >
              <img
                src={att}
                alt="The attached document"
                className="max-h-80 w-full object-contain object-top"
              />
            </a>
          )}
          {att && att.endsWith(".pdf") && (
            <p className="mb-5 text-sm">
              <a
                href={att}
                target="_blank"
                rel="noreferrer"
                className="text-accent underline underline-offset-2"
              >
                Open the attached PDF
              </a>
            </p>
          )}

          <dl className="grid gap-5 text-sm sm:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
            <div>
              <dt className="text-xs font-semibold tracking-wide text-faint uppercase">
                {task.transcript ? "What the clip says" : "Prompt"}
              </dt>
              <dd className="mt-1 leading-relaxed whitespace-pre-wrap">{task.transcript ?? task.prompt}</dd>
              {task.transcript && (
                <dd className="mt-2 text-xs leading-relaxed text-muted">Instruction: {task.prompt}</dd>
              )}
            </div>
            <div>
              <dt className="text-xs font-semibold tracking-wide text-faint uppercase">Correct answer</dt>
              <dd className="mt-1 font-mono text-[13px] leading-relaxed break-words">{task.expected}</dd>
            </div>
          </dl>

          <div className="mt-8 grid gap-6 md:grid-cols-2">
            {(["base", "cand"] as const).map((k) => {
              const side = task[k];
              return (
                <section key={k}>
                  <h3 className="flex items-baseline justify-between border-b border-line pb-2">
                    <span className="font-semibold">
                      {shortModel(k === "base" ? meta.baseline : meta.candidate)}
                    </span>
                    <span
                      className={`text-xs font-bold tracking-[0.06em] ${side.pass ? "text-go" : "text-risk"}`}
                    >
                      {side.pass ? "PASS" : "FAIL"} · {side.answers.filter((a) => a.passed).length}/
                      {side.answers.length}
                    </span>
                  </h3>
                  <ol className="divide-y divide-line">
                    {side.answers.map((a) => {
                      const m = a.mode !== "error" ? MODE_STYLE[a.mode] : null;
                      return (
                        <li key={a.repeat} className="py-3">
                          <div className="flex items-center justify-between gap-2 text-xs">
                            <span className="text-faint">Try {a.repeat + 1}</span>
                            <span className="flex items-center gap-1.5 text-muted">
                              {m && (
                                <span
                                  aria-hidden
                                  className={`size-2 rounded-[2px] ${m.hatch ? "hatch" : ""}`}
                                  style={{ backgroundColor: m.color }}
                                />
                              )}
                              {m ? m.label : "Error"}
                              {a.passed && a.strict === false && (
                                <span className="text-faint">· format not exact</span>
                              )}
                            </span>
                          </div>
                          <p className="mt-1.5 font-mono text-[12.5px] leading-relaxed break-words whitespace-pre-wrap">
                            {a.text || <span className="text-faint">(empty)</span>}
                          </p>
                          {a.detail && !a.passed && (
                            <p className="mt-1 text-xs text-muted">Scorer: {a.detail}</p>
                          )}
                        </li>
                      );
                    })}
                  </ol>
                </section>
              );
            })}
          </div>
        </div>
      </motion.aside>
    </div>
  );
}
