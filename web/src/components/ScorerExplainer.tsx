import { Check, X } from "lucide-react";
import type { E1 } from "../data";

// Walks through one real rescored answer so the idea of a "scorer" is concrete.
export function ScorerExplainer({ e1 }: { e1: E1 }) {
  const ex = e1.examples.find((x) => x.answer.trim() === "Somwar") ?? e1.examples[0];
  const accepted = Array.isArray(ex?.accepted) ? (ex.accepted as string[]) : [];

  const steps = [
    {
      title: "What a scorer is",
      body: "Every task has a known answer. After the model replies, a small rule compares the reply with it and marks pass or fail. Thousands of these marks become the pass rate the gate tests.",
    },
    {
      title: "How it went wrong",
      body: "Our first rule wanted an exact match from a short list. Hindi written in English letters has no single spelling, so correct answers like “Somwar” failed. 1.2 used those spellings more often than 1.3.",
    },
    {
      title: "What we changed",
      body: "Each answer now gets two marks: correct (any spelling, or a clear answer inside an explanation) and correct format (exactly what was asked). Both are saved, so either can be gated on.",
    },
    {
      title: "Why it matters to you",
      body: "Every evaluation uses rules like this. A strict one turns writing habits into a model difference, and the statistics will call it significant. The report shows rejected answers beside the score so you can check the rule first.",
    },
  ];

  return (
    <div className="mt-16 grid gap-10 lg:grid-cols-[minmax(0,6fr)_minmax(0,5fr)]">
      <ol className="grid gap-x-8 gap-y-8 sm:grid-cols-2">
        {steps.map((s, i) => (
          <li key={s.title}>
            <p className="font-mono text-xs text-faint">{String(i + 1).padStart(2, "0")}</p>
            <h3 className="mt-1 font-semibold">{s.title}</h3>
            <p className="mt-2 text-sm leading-relaxed text-muted">{s.body}</p>
          </li>
        ))}
      </ol>

      {ex && (
        <div className="rounded-lg border border-line">
          <p className="border-b border-line px-5 py-3 text-xs font-semibold tracking-wide text-faint uppercase">
            One real task from the run
          </p>
          <dl className="divide-y divide-line text-sm">
            <div className="px-5 py-4">
              <dt className="text-xs text-faint">Question (Hinglish)</dt>
              <dd className="mt-1 leading-relaxed">{ex.prompt}</dd>
            </div>
            <div className="px-5 py-4">
              <dt className="text-xs text-faint">Answers the rule accepted</dt>
              <dd className="mt-1 font-mono text-[13px]">{accepted.join(" · ")}</dd>
            </div>
            <div className="px-5 py-4">
              <dt className="text-xs text-faint">Spark 1.2 replied</dt>
              <dd className="mt-1 font-mono text-base">{ex.answer}</dd>
            </div>
            <div className="grid grid-cols-2 gap-4 px-5 py-4">
              <div>
                <dt className="text-xs text-faint">Old rule</dt>
                <dd className="mt-1 flex items-center gap-1.5 font-semibold text-risk">
                  <X aria-hidden className="size-4" /> Fail
                </dd>
                <dd className="mt-1 text-xs text-muted">“Somwar” isn’t on the list</dd>
              </div>
              <div>
                <dt className="text-xs text-faint">New rule</dt>
                <dd className="mt-1 flex items-center gap-1.5 font-semibold text-go">
                  <Check aria-hidden className="size-4" /> Correct
                </dd>
                <dd className="mt-1 text-xs text-muted">w and v, aa and a fold together</dd>
              </div>
            </div>
          </dl>
        </div>
      )}
    </div>
  );
}
