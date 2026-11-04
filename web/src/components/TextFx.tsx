import type { ReactNode } from "react";
import { useEffect, useRef, useState } from "react";

/** True once the element has scrolled into view (and stays true). Immediately true without IntersectionObserver. */
export function useInView<T extends HTMLElement>(margin = "0px 0px -15% 0px") {
  const ref = useRef<T>(null);
  const [on, setOn] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el || typeof IntersectionObserver === "undefined") return setOn(true);
    const io = new IntersectionObserver(
      ([e]) => {
        if (e.isIntersecting) {
          setOn(true);
          io.disconnect();
        }
      },
      { rootMargin: margin },
    );
    io.observe(el);
    return () => io.disconnect();
  }, [margin]);
  return [ref, on] as const;
}

/** Delays `on` a little so effects play in sequence after the element appears. */
function useDelayed(on: boolean, ms: number) {
  const [late, setLate] = useState(false);
  useEffect(() => {
    if (!on) return;
    const t = window.setTimeout(() => setLate(true), ms);
    return () => window.clearTimeout(t);
  }, [on, ms]);
  return late;
}

/** Highlighter stroke that sweeps under the text when it scrolls into view. */
export function Mark({ children, delay = 0 }: { children: ReactNode; delay?: number }) {
  const [ref, inView] = useInView<HTMLSpanElement>();
  const on = useDelayed(inView, delay);
  return (
    <span ref={ref} className={`mark ${on ? "on" : ""}`}>
      {children}
    </span>
  );
}

/** A phrase that gets struck through once it's in view: the thing the new model stopped saying. */
export function Strike({ children, delay = 0, label }: { children: ReactNode; delay?: number; label?: string }) {
  const [ref, inView] = useInView<HTMLSpanElement>();
  const on = useDelayed(inView, delay);
  return (
    <span ref={ref} className={`strike ${on ? "on" : ""}`}>
      {label && <span className="sr-only">{label} </span>}
      {children}
    </span>
  );
}

/** Rolling-digit counter. The final number is in the DOM for screen readers and copy-paste. */
export function Odometer({ value, delay = 0 }: { value: number; delay?: number }) {
  const [ref, inView] = useInView<HTMLSpanElement>();
  const on = useDelayed(inView, delay);
  const digits = String(value).split("");
  return (
    <span ref={ref} className="inline-flex">
      <span className="sr-only">{value}</span>
      <span aria-hidden className="inline-flex">
        {digits.map((d, i) => (
          <span key={i} className="odometer">
            <span
              style={{
                transform: `translateY(-${on ? Number(d) : 0}em)`,
                transitionDelay: `${(digits.length - i) * 90}ms`,
              }}
            >
              {Array.from({ length: 10 }, (_, n) => (
                <span key={n} className="block h-[1em] shrink-0">
                  {n}
                </span>
              ))}
            </span>
          </span>
        ))}
      </span>
    </span>
  );
}

/** Words fade up one after another, once. Text is a plain string so it stays readable without JS effects. */
export function Words({ text, className = "", step = 45 }: { text: string; className?: string; step?: number }) {
  const [ref, on] = useInView<HTMLSpanElement>();
  return (
    <span ref={ref} className={className} aria-label={text}>
      {text.split(" ").map((w, i) => (
        <span
          key={i}
          aria-hidden
          className="inline-block transition-[opacity,transform] duration-500 ease-out"
          style={{
            opacity: on ? 1 : 0,
            transform: on ? "none" : "translateY(0.35em)",
            transitionDelay: `${i * step}ms`,
          }}
        >
          {w}
          {" "}
        </span>
      ))}
    </span>
  );
}

/** Shows `got` against `want` digit by digit; digits that differ are marked. */
export function DigitDiff({ got, want }: { got: string; want: string }) {
  if (!got) return <span className="text-risk italic">""</span>;
  return (
    <span className="font-mono">
      {got.split("").map((c, i) => {
        const bad = c !== want[i];
        return (
          <span key={i} className={bad ? "text-risk underline decoration-2 underline-offset-[3px]" : ""}>
            {c}
          </span>
        );
      })}
      {got.length !== want.length && (
        <span className="sr-only"> ({got.length} digits, expected {want.length})</span>
      )}
    </span>
  );
}
