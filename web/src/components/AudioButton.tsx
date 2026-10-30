import { Pause, Play } from "lucide-react";
import { useEffect, useRef, useState } from "react";

const fmt = (s: number) => (Number.isFinite(s) ? `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}` : "–:––");

/** Compact play/pause with elapsed and total time. Never autoplays. */
export function AudioButton({ src, label = "Play the voice note" }: { src: string; label?: string }) {
  const ref = useRef<HTMLAudioElement>(null);
  const [playing, setPlaying] = useState(false);
  const [t, setT] = useState(0);
  const [d, setD] = useState(NaN);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    setPlaying(false);
    setT(0);
    setD(NaN);
    setFailed(false);
  }, [src]);

  const toggle = () => {
    const a = ref.current;
    if (!a) return;
    if (a.paused) a.play().catch(() => setFailed(true));
    else a.pause();
  };

  return (
    <span className="inline-flex items-center gap-2">
      <audio
        ref={ref}
        src={src}
        preload="metadata"
        onPlay={() => setPlaying(true)}
        onPause={() => setPlaying(false)}
        onEnded={() => (setPlaying(false), setT(0))}
        onTimeUpdate={(e) => setT(e.currentTarget.currentTime)}
        onLoadedMetadata={(e) => setD(e.currentTarget.duration)}
        onError={() => setFailed(true)}
      />
      <button
        type="button"
        onClick={toggle}
        disabled={failed}
        aria-label={playing ? "Pause" : label}
        className="inline-flex size-9 items-center justify-center rounded-full bg-fg text-bg transition-opacity duration-150 hover:opacity-90 disabled:opacity-40"
      >
        {playing ? <Pause aria-hidden className="size-4 fill-current" /> : <Play aria-hidden className="ml-0.5 size-4 fill-current" />}
      </button>
      <span className="font-mono text-xs text-muted tabular-nums" aria-live="off">
        {failed ? "Audio unavailable" : `${fmt(t)} / ${fmt(d)}`}
      </span>
    </span>
  );
}
