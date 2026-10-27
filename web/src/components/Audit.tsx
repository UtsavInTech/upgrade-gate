import { useCallback, useEffect, useState } from "react";

type Item = { id: string; said: string; instruction: string; expected: string; answer: string };

const LABELS: { key: string; value: string; label: string; help: string }[] = [
  {
    key: "1",
    value: "correct",
    label: "Correct",
    help: "Gives the right answer (spelling and extra words don't matter).",
  },
  {
    key: "2",
    value: "abstain",
    label: "Says it can't answer",
    help: "Says it can't hear, can't access the audio, isn't sure, or refuses, and does not give a usable answer.",
  },
  {
    key: "3",
    value: "blank",
    label: "Blank",
    help: 'Answers, but the answer is empty (e.g. every field is "").',
  },
  {
    key: "4",
    value: "wrong",
    label: "Wrong, no warning",
    help: "Gives a filled-in answer that is wrong, without saying it might be.",
  },
  { key: "5", value: "unsure", label: "Can't tell", help: "You can't decide from what's shown." },
];

function loadName(): string {
  try {
    return localStorage.getItem("ug-labeler") ?? "";
  } catch {
    return "";
  }
}

export function Audit() {
  const [items, setItems] = useState<Item[]>([]);
  const [name, setName] = useState(loadName);
  const [labels, setLabels] = useState<Record<string, string>>({});
  const [i, setI] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const valid = /^[a-z0-9-]{1,32}$/.test(name);

  useEffect(() => {
    fetch("data/audit.json")
      .then((r) => r.json())
      .then(setItems, () => setError("Couldn’t load the audit sample."));
  }, []);

  useEffect(() => {
    if (!valid) return;
    try {
      localStorage.setItem("ug-labeler", name);
    } catch {
      /* not remembered */
    }
    fetch(`/api/audit?labeler=${name}`)
      .then((r) => r.json())
      .then((l: Record<string, string>) => setLabels(l))
      .catch(() => setLabels({}));
  }, [name, valid]);

  const item = items[i];
  const done = items.filter((x) => labels[x.id]).length;

  const choose = useCallback(
    async (value: string) => {
      if (!item || !valid) return;
      setError(null);
      try {
        const r = await fetch(`/api/audit?labeler=${name}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ id: item.id, label: value }),
        });
        if (!r.ok) throw new Error(await r.text());
        setLabels((l) => ({ ...l, [item.id]: value }));
        const next = items.findIndex((x, k) => k > i && !labels[x.id]);
        setI(next >= 0 ? next : Math.min(i + 1, items.length - 1));
      } catch {
        setError("Couldn’t save. Is the dev server running (npm --prefix web run dev)?");
      }
    },
    [item, valid, name, items, i, labels],
  );

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.target as HTMLElement)?.tagName === "INPUT") return;
      const l = LABELS.find((x) => x.key === e.key);
      if (l) choose(l.value);
      if (e.key === "ArrowRight") setI((k) => Math.min(k + 1, items.length - 1));
      if (e.key === "ArrowLeft") setI((k) => Math.max(k - 1, 0));
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [choose, items.length]);

  return (
    <div className="mx-auto max-w-5xl px-4 pt-10 pb-24 sm:px-8">
      <header className="max-w-2xl">
        <h1 className="text-3xl font-semibold tracking-tight">Label audit</h1>
        <p className="mt-3 text-muted">
          60 answers to voice notes, in random order. You don’t see which model wrote them or how the rules
          labelled them. For each one, pick what the answer actually is. Your labels are compared with the
          automatic rules afterwards (Cohen’s κ), and every disagreement is listed. Keys 1–5 choose, ← → move.
        </p>
      </header>

      <label className="mt-8 block max-w-sm text-sm">
        <span className="font-medium">Your name</span>
        <input
          value={name}
          onChange={(e) => setName(e.target.value.toLowerCase().trim())}
          className="mt-2 w-full rounded-md border border-line bg-bg px-3 py-2 outline-none focus:border-accent"
          placeholder="utsav"
        />
      </label>

      {item && (
        <section className="mt-8 rounded-lg border border-line" aria-live="polite">
          <div className="flex items-center justify-between border-b border-line px-5 py-3 text-sm text-muted">
            <span>
              Answer {i + 1} of {items.length}
            </span>
            <span>
              <span className="font-semibold text-fg">{done}</span> labelled
            </span>
          </div>
          <dl className="grid gap-5 p-5 sm:grid-cols-2 sm:p-7">
            <div>
              <dt className="text-xs font-semibold tracking-wide text-faint uppercase">What the clip says</dt>
              <dd className="mt-1 leading-relaxed">{item.said || "(not available)"}</dd>
            </div>
            <div>
              <dt className="text-xs font-semibold tracking-wide text-faint uppercase">Correct answer</dt>
              <dd className="mt-1 font-mono text-sm leading-relaxed">{item.expected}</dd>
              <dt className="mt-4 text-xs font-semibold tracking-wide text-faint uppercase">
                The model was asked
              </dt>
              <dd className="mt-1 text-sm text-muted">{item.instruction}</dd>
            </div>
            <div className="sm:col-span-2">
              <dt className="text-xs font-semibold tracking-wide text-faint uppercase">The model replied</dt>
              <dd className="mt-1 rounded-md bg-surface p-4 font-mono text-[13px] leading-relaxed break-words whitespace-pre-wrap">
                {item.answer || "(empty reply)"}
              </dd>
            </div>
          </dl>
          <div className="grid gap-2 border-t border-line p-5 sm:grid-cols-5">
            {LABELS.map((l) => (
              <button
                key={l.value}
                onClick={() => choose(l.value)}
                disabled={!valid}
                title={l.help}
                className={`rounded-md border px-3 py-3 text-left text-sm transition-colors disabled:opacity-40 ${
                  labels[item.id] === l.value
                    ? "border-accent bg-accent-soft"
                    : "border-line hover:bg-surface"
                }`}
              >
                <span className="font-mono text-xs text-faint">{l.key}</span>
                <span className="mt-0.5 block font-semibold">{l.label}</span>
              </button>
            ))}
          </div>
          <ul className="space-y-1 px-5 pb-5 text-xs text-muted">
            {LABELS.map((l) => (
              <li key={l.value}>
                <span className="font-semibold text-fg">{l.label}:</span> {l.help}
              </li>
            ))}
          </ul>
        </section>
      )}
      {!valid && <p className="mt-4 text-sm text-hold">Enter your name first.</p>}
      {error && <p className="mt-4 text-sm text-risk">{error}</p>}
      {items.length > 0 && done === items.length && (
        <p className="mt-6 rounded-md bg-go-soft px-4 py-3 text-go">
          All {items.length} labelled. Run{" "}
          <code className="font-mono">PYTHONPATH=. python3 scripts/audit_report.py</code> to see the
          agreement.
        </p>
      )}
    </div>
  );
}
