import { Check, Circle, Download, Square } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { toWav16k } from "../audio";
import { LANG_LABEL } from "../data";
import { listTakes, putTake } from "../takes";
import { makeZip } from "../zip";

type Voice = "" | "female" | "male";

// Personal links: #/record?name=riya&voice=female fills in the form for a friend.
function linkParams(): { name: string; voice: Voice } {
  const q = new URLSearchParams(window.location.hash.split("?")[1] ?? "");
  const name = (q.get("name") ?? "").toLowerCase().trim();
  const v = q.get("voice");
  return { name: /^[a-z0-9-]{1,32}$/.test(name) ? name : "", voice: v === "female" || v === "male" ? v : "" };
}

function remembered(key: string): string {
  try {
    return localStorage.getItem(key) ?? "";
  } catch {
    return "";
  }
}

function remember(key: string, value: string) {
  try {
    localStorage.setItem(key, value);
  } catch {
    /* not remembered */
  }
}

type Line = { clip_id: string; item: string; kind: string; lang: string; transcript: string };

const KIND: Record<string, string> = {
  math: "Spoken maths",
  extract: "Order voice note",
  intent: "Customer request",
  correction: "Voice note with a correction",
};

export function Record({ set = "main" }: { set?: "main" | "corrections" }) {
  const link = useState(linkParams)[0];
  const [lines, setLines] = useState<Line[]>([]);
  const [speaker, setSpeaker] = useState(() => link.name || remembered("ug-speaker"));
  const [voice, setVoice] = useState<Voice>(() => link.voice || (remembered("ug-voice") as Voice));
  const [consent, setConsent] = useState(() => remembered("ug-consent") === "yes");
  // null until we know; false on the public site, where takes stay on this device.
  const [server, setServer] = useState<boolean | null>(null);
  const [done, setDone] = useState<Set<string>>(new Set());
  const [i, setI] = useState(0);
  const [state, setState] = useState<"idle" | "recording" | "review" | "saving">("idle");
  const [take, setTake] = useState<{ url: string; wav: Blob } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const rec = useRef<MediaRecorder | null>(null);

  const valid = /^[a-z0-9-]{1,32}$/.test(speaker);

  useEffect(() => {
    fetch(set === "corrections" ? "data/record-corrections.json" : "data/record.json")
      .then((r) => r.json())
      .then(setLines, () => setError("Couldn’t load the lines to record."));
  }, []);

  useEffect(() => {
    if (!valid) return;
    remember("ug-speaker", speaker);
    let live = true;
    fetch(`/api/recorded?speaker=${speaker}`)
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((ids: string[]) => {
        if (!Array.isArray(ids)) throw new Error();
        if (live) (setServer(true), setDone(new Set(ids)));
      })
      .catch(async () => {
        const takes = await listTakes(speaker);
        if (live) (setServer(false), setDone(new Set(takes.keys())));
      });
    return () => {
      live = false;
    };
  }, [speaker, valid]);

  useEffect(() => remember("ug-voice", voice), [voice]);
  useEffect(() => remember("ug-consent", consent ? "yes" : ""), [consent]);

  const downloadAll = async () => {
    const takes = await listTakes(speaker);
    const files = await Promise.all(
      [...takes].map(async ([clip, wav]) => ({
        name: `${speaker}/${clip}.wav`,
        data: new Uint8Array(await wav.arrayBuffer()),
      })),
    );
    const meta = {
      speaker,
      voice: voice || null,
      consent: "Recordings may be used in a private test of AI models and will not be published.",
      clips: takes.size,
      exported: new Date().toISOString(),
    };
    files.push({ name: `${speaker}/speaker.json`, data: new TextEncoder().encode(JSON.stringify(meta, null, 2)) });
    const url = URL.createObjectURL(makeZip(files));
    const a = document.createElement("a");
    a.href = url;
    a.download = `voice-notes-${speaker}.zip`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 10_000);
  };

  const line = lines[i];

  const start = useCallback(async () => {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: true },
      });
      const parts: Blob[] = [];
      const r = new MediaRecorder(stream);
      r.ondataavailable = (e) => e.data.size && parts.push(e.data);
      r.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        try {
          const wav = await toWav16k(new Blob(parts, { type: r.mimeType }));
          setTake({ url: URL.createObjectURL(wav), wav });
          setState("review");
        } catch {
          setError("Couldn’t process the recording. Try again.");
          setState("idle");
        }
      };
      rec.current = r;
      r.start();
      setState("recording");
    } catch {
      setError("Microphone access was blocked. Allow it in the browser’s address bar and try again.");
    }
  }, []);

  const stop = () => rec.current?.state === "recording" && rec.current.stop();

  const save = async () => {
    if (!take || !line) return;
    setState("saving");
    try {
      if (server) {
        const r = await fetch(`/api/record?speaker=${speaker}&clip=${line.clip_id}`, {
          method: "POST",
          body: take.wav,
        });
        if (!r.ok) throw new Error(await r.text());
      } else {
        // Public site: keep the take on this device; "Download all" hands them back as one file.
        await putTake(speaker, line.clip_id, take.wav);
      }
      const nextDone = new Set(done).add(line.clip_id);
      setDone(nextDone);
      URL.revokeObjectURL(take.url);
      setTake(null);
      setState("idle");
      const next = lines.findIndex((l, k) => k > i && !nextDone.has(l.clip_id));
      const wrap = lines.findIndex((l) => !nextDone.has(l.clip_id));
      if (next >= 0) setI(next);
      else if (wrap >= 0) setI(wrap);
    } catch {
      setError("Couldn’t save this line. Try Save again.");
      setState("review");
    }
  };

  const allDone = lines.length > 0 && lines.every((l) => done.has(l.clip_id));

  return (
    <div className="mx-auto max-w-6xl px-4 pt-10 pb-24 sm:px-8">
      <header className="max-w-2xl">
        <h1 className="text-3xl font-semibold tracking-tight">
          {set === "corrections" ? "Record voice notes with a correction" : "Record real voice notes"}
        </h1>
        {set === "corrections" ? (
          <p className="mt-3 text-muted">
            Each line says a number, takes it back and says it again. Read it the way you would really
            correct yourself: a short pause, then “sorry, no” and the right number. Read digits one by one.
            15 lines, about five minutes.
          </p>
        ) : (
          <p className="mt-3 text-muted">
            Read each line the way you’d send a voice note: normal speed, your own accent, in a normal room.
            Read digits one by one. Each line takes about ten seconds; all 45 take around ten minutes. More
            speakers make the test stronger, so ask a friend to record with their own name too.
          </p>
        )}
      </header>

      <div className="mt-8 flex max-w-2xl flex-col gap-5 sm:flex-row sm:items-end">
        <label className="block flex-1 text-sm">
          <span className="font-medium">Speaker name</span>
          <span className="block text-xs text-faint">
            Lowercase letters, numbers and dashes, e.g. utsav or friend-1
          </span>
          <input
            value={speaker}
            onChange={(e) => setSpeaker(e.target.value.toLowerCase().trim())}
            className="mt-2 w-full rounded-md border border-line bg-bg px-3 py-2 outline-none focus:border-accent"
            placeholder="utsav"
          />
        </label>
        <label className="block text-sm sm:w-48">
          <span className="font-medium">Voice</span>
          <span className="block text-xs text-faint">Optional, helps compare voices</span>
          <select
            value={voice}
            onChange={(e) => setVoice(e.target.value as Voice)}
            className="mt-2 w-full rounded-md border border-line bg-bg px-3 py-2 outline-none focus:border-accent"
          >
            <option value="">Prefer not to say</option>
            <option value="female">Female</option>
            <option value="male">Male</option>
          </select>
        </label>
      </div>
      <label className="mt-5 flex max-w-2xl items-start gap-3 text-sm">
        <input
          type="checkbox"
          checked={consent}
          onChange={(e) => setConsent(e.target.checked)}
          className="mt-0.5 size-4 accent-[var(--accent)]"
        />
        <span>
          I agree that my recordings may be used in a private test of AI models. They won’t be published or
          shared.
        </span>
      </label>

      {server === false && valid && done.size > 0 && (
        <div className="mt-8 flex max-w-2xl flex-col gap-4 rounded-lg border border-line bg-surface p-5 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm">
            <span className="font-semibold">
              {done.size} of {lines.length} recorded
            </span>{" "}
            <span className="text-muted">
              {allDone
                ? "· All done, thank you! Download the file and send it back."
                : "· Saved on this device. You can stop and come back later on the same phone."}
            </span>
          </p>
          <button
            onClick={downloadAll}
            className={`inline-flex shrink-0 items-center justify-center gap-2 rounded-md px-4 py-2.5 text-sm font-semibold ${
              allDone ? "bg-accent text-accent-ink" : "border border-line bg-bg text-fg"
            }`}
          >
            <Download aria-hidden className="size-4" />
            Download all ({done.size})
          </button>
        </div>
      )}

      <div className="mt-10 grid gap-8 lg:grid-cols-[300px_minmax(0,1fr)]">
        <ol
          className="order-last max-h-[40vh] overflow-y-auto rounded-lg border border-line lg:order-none lg:max-h-[60vh]"
          aria-label="Lines to record"
        >
          {lines.map((l, k) => (
            <li key={l.clip_id}>
              <button
                onClick={() => (setI(k), setTake(null), setState("idle"))}
                aria-current={k === i ? "true" : undefined}
                className={`flex w-full items-center gap-3 border-b border-line px-4 py-2.5 text-left text-sm last:border-0 ${
                  k === i ? "bg-accent-soft" : "hover:bg-surface"
                }`}
              >
                {done.has(l.clip_id) ? (
                  <Check aria-label="Recorded" className="size-4 shrink-0 text-go" />
                ) : (
                  <span className="size-4 shrink-0 text-center font-mono text-[11px] text-faint">
                    {k + 1}
                  </span>
                )}
                <span className="min-w-0">
                  <span className="block truncate font-medium">{KIND[l.kind]}</span>
                  <span className="block text-xs text-faint">{LANG_LABEL[l.lang]}</span>
                </span>
              </button>
            </li>
          ))}
        </ol>

        {line && (
          <section className="rounded-lg border border-line p-6 sm:p-8" aria-live="polite">
            <p className="text-sm text-muted">
              Line {i + 1} of {lines.length} · {LANG_LABEL[line.lang]} · {KIND[line.kind]} ·{" "}
              <span className="font-semibold text-fg">{done.size}</span> recorded
            </p>
            <p
              className="mt-6 text-2xl leading-relaxed font-medium text-pretty sm:text-3xl"
              lang={line.lang === "hi" ? "hi" : "en"}
            >
              {line.transcript}
            </p>

            <div className="mt-8 flex flex-wrap items-center gap-3">
              {state === "recording" ? (
                <button
                  onClick={stop}
                  className="inline-flex items-center gap-2 rounded-md bg-risk px-5 py-3 font-semibold text-white"
                >
                  <Square aria-hidden className="size-4 fill-current" /> Stop
                </button>
              ) : (
                <button
                  onClick={start}
                  disabled={!valid || !consent || state === "saving"}
                  className="inline-flex items-center gap-2 rounded-md bg-fg px-5 py-3 font-semibold text-bg disabled:opacity-40"
                >
                  <Circle aria-hidden className="size-4 fill-[var(--risk)] text-[var(--risk)]" />
                  {take ? "Record again" : "Record"}
                </button>
              )}
              {take && state !== "recording" && (
                <>
                  <audio controls src={take.url} className="h-10" />
                  <button
                    onClick={save}
                    disabled={state === "saving"}
                    className="rounded-md bg-accent px-5 py-3 font-semibold text-accent-ink disabled:opacity-50"
                  >
                    {state === "saving" ? "Saving…" : "Save and next"}
                  </button>
                </>
              )}
            </div>
            {!valid && <p className="mt-4 text-sm text-hold">Enter a speaker name first.</p>}
            {valid && !consent && (
              <p className="mt-4 text-sm text-hold">Tick the agreement above to start recording.</p>
            )}
            {state === "recording" && (
              <p className="mt-4 text-sm text-risk">Recording… press Stop when you finish the line.</p>
            )}
            {error && <p className="mt-4 text-sm text-risk">{error}</p>}
          </section>
        )}
      </div>
    </div>
  );
}
