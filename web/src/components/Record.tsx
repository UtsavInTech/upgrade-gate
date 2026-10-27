import { Check, Circle, Square } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { LANG_LABEL } from "../data";

type Line = { clip_id: string; item: string; kind: string; lang: string; transcript: string };

const KIND: Record<string, string> = {
  math: "Spoken maths",
  extract: "Order voice note",
  intent: "Customer request",
};

// Decode whatever the browser recorded, mix to mono, resample to 16 kHz and write 16-bit PCM WAV:
// the same format as the synthetic clips, so the experiment changes only the voice.
async function toWav16k(blob: Blob): Promise<Blob> {
  const ctx = new AudioContext();
  const decoded = await ctx.decodeAudioData(await blob.arrayBuffer());
  await ctx.close();
  const rate = 16000;
  const off = new OfflineAudioContext(1, Math.ceil(decoded.duration * rate), rate);
  const src = off.createBufferSource();
  src.buffer = decoded;
  src.connect(off.destination);
  src.start();
  const pcm = (await off.startRendering()).getChannelData(0);
  const buf = new ArrayBuffer(44 + pcm.length * 2);
  const v = new DataView(buf);
  const str = (o: number, s: string) => [...s].forEach((c, i) => v.setUint8(o + i, c.charCodeAt(0)));
  str(0, "RIFF");
  v.setUint32(4, 36 + pcm.length * 2, true);
  str(8, "WAVE");
  str(12, "fmt ");
  v.setUint32(16, 16, true);
  v.setUint16(20, 1, true);
  v.setUint16(22, 1, true);
  v.setUint32(24, rate, true);
  v.setUint32(28, rate * 2, true);
  v.setUint16(32, 2, true);
  v.setUint16(34, 16, true);
  str(36, "data");
  v.setUint32(40, pcm.length * 2, true);
  pcm.forEach((x, i) => v.setInt16(44 + i * 2, Math.max(-1, Math.min(1, x)) * 0x7fff, true));
  return new Blob([buf], { type: "audio/wav" });
}

function loadSpeaker(): string {
  try {
    return localStorage.getItem("ug-speaker") ?? "";
  } catch {
    return "";
  }
}

export function Record() {
  const [lines, setLines] = useState<Line[]>([]);
  const [speaker, setSpeaker] = useState(loadSpeaker);
  const [done, setDone] = useState<Set<string>>(new Set());
  const [i, setI] = useState(0);
  const [state, setState] = useState<"idle" | "recording" | "review" | "saving">("idle");
  const [take, setTake] = useState<{ url: string; wav: Blob } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const rec = useRef<MediaRecorder | null>(null);

  const valid = /^[a-z0-9-]{1,32}$/.test(speaker);

  useEffect(() => {
    fetch("data/record.json")
      .then((r) => r.json())
      .then(setLines, () => setError("Couldn’t load the lines to record."));
  }, []);

  useEffect(() => {
    if (!valid) return;
    try {
      localStorage.setItem("ug-speaker", speaker);
    } catch {
      /* not remembered */
    }
    fetch(`/api/recorded?speaker=${speaker}`)
      .then((r) => r.json())
      .then((ids: string[]) => setDone(new Set(ids)))
      .catch(() => setDone(new Set()));
  }, [speaker, valid]);

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
      const r = await fetch(`/api/record?speaker=${speaker}&clip=${line.clip_id}`, {
        method: "POST",
        body: take.wav,
      });
      if (!r.ok) throw new Error(await r.text());
      setDone((d) => new Set(d).add(line.clip_id));
      URL.revokeObjectURL(take.url);
      setTake(null);
      setState("idle");
      const next = lines.findIndex((l, k) => k > i && !done.has(l.clip_id));
      if (next >= 0) setI(next);
    } catch {
      // Static build (no dev server): fall back to a download the user can drop into data/audio-real/.
      const a = document.createElement("a");
      a.href = take.url;
      a.download = `${speaker}__${line.clip_id}.wav`;
      a.click();
      setError("Saved as a download (the dev server isn’t running). Move it into data/audio-real/.");
      setState("review");
    }
  };

  return (
    <div className="mx-auto max-w-6xl px-4 pt-10 pb-24 sm:px-8">
      <header className="max-w-2xl">
        <h1 className="text-3xl font-semibold tracking-tight">Record real voice notes</h1>
        <p className="mt-3 text-muted">
          Read each line the way you’d send a voice note: normal speed, your own accent, in a normal room.
          Read digits one by one. Each line takes about ten seconds; all 45 take around ten minutes. More
          speakers make the test stronger, so ask a friend to record with their own name too.
        </p>
      </header>

      <label className="mt-8 block max-w-sm text-sm">
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

      <div className="mt-10 grid gap-8 lg:grid-cols-[300px_minmax(0,1fr)]">
        <ol
          className="max-h-[60vh] overflow-y-auto rounded-lg border border-line"
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
                  disabled={!valid || state === "saving"}
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
