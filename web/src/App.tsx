import { MotionConfig } from "motion/react";
import { useCallback, useEffect, useState } from "react";
import { AudioSection } from "./components/AudioSection";
import { CostSection } from "./components/CostSection";
import { Header, Logo } from "./components/Header";
import { Hero } from "./components/Hero";
import { HowSection } from "./components/HowSection";
import { ScoringSection } from "./components/ScoringSection";
import type { Site } from "./data";
import { loadSite } from "./data";

type Theme = "light" | "dark";

function initialTheme(): Theme {
  const set = document.documentElement.dataset.theme;
  if (set === "light" || set === "dark") return set;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export default function App() {
  const [site, setSite] = useState<Site | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [theme, setTheme] = useState<Theme>(initialTheme);
  const [presenting, setPresenting] = useState(false);

  useEffect(() => {
    loadSite().then(setSite, (e: Error) => setError(e.message));
  }, []);

  const toggleTheme = useCallback(() => {
    setTheme((t) => {
      const next = t === "dark" ? "light" : "dark";
      document.documentElement.dataset.theme = next;
      try {
        localStorage.setItem("ug-theme", next);
      } catch {
        /* private mode: theme just won't be remembered */
      }
      return next;
    });
  }, []);

  // Presenter mode: each section is one screen; arrows / space move, Esc leaves.
  useEffect(() => {
    document.documentElement.classList.toggle("presenting", presenting);
    if (!presenting) return;
    const slides = () => Array.from(document.querySelectorAll<HTMLElement>("[data-slide]"));
    const current = () => {
      const y = window.scrollY + window.innerHeight / 3;
      const s = slides();
      let idx = 0;
      s.forEach((el, i) => {
        if (el.offsetTop <= y) idx = i;
      });
      return idx;
    };
    const go = (d: number) => {
      const s = slides();
      const next = Math.min(s.length - 1, Math.max(0, current() + d));
      s[next]?.scrollIntoView({ behavior: "smooth" });
    };
    const onKey = (e: KeyboardEvent) => {
      if (["ArrowRight", "ArrowDown", "PageDown", " "].includes(e.key)) {
        e.preventDefault();
        go(1);
      } else if (["ArrowLeft", "ArrowUp", "PageUp"].includes(e.key)) {
        e.preventDefault();
        go(-1);
      } else if (e.key === "Escape") {
        setPresenting(false);
      }
    };
    slides()[0]?.scrollIntoView();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [presenting]);

  return (
    <MotionConfig reducedMotion="user">
      <a
        href="#audio"
        className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus:rounded-md focus:bg-accent focus:px-3 focus:py-2 focus:text-accent-ink"
      >
        Skip to findings
      </a>
      <Header theme={theme} onToggleTheme={toggleTheme} onPresent={() => setPresenting((p) => !p)} />
      {presenting && (
        <p className="fixed right-4 bottom-4 z-50 rounded-md bg-fg px-3 py-2 text-xs text-bg shadow-lg">
          Presenting · ← → to move · Esc to exit
        </p>
      )}
      <main>
        {error && (
          <div className="mx-auto max-w-3xl px-4 py-32 text-center">
            <h1 className="text-2xl font-semibold">Couldn’t load the results</h1>
            <p className="mt-3 text-muted">
              {error}. Run <code className="font-mono">npm run data</code> in{" "}
              <code className="font-mono">web/</code> to export the saved runs.
            </p>
          </div>
        )}
        {!site && !error && (
          <div className="mx-auto max-w-6xl px-4 py-32 sm:px-8" aria-busy="true">
            <div className="h-16 w-3/4 animate-pulse rounded-lg bg-surface" />
            <div className="mt-6 h-6 w-1/2 animate-pulse rounded bg-surface" />
          </div>
        )}
        {site && (
          <>
            <Hero site={site} />
            <AudioSection e6={site.e6} />
            <ScoringSection e1={site.e1} />
            <CostSection e3={site.e3} />
            <HowSection />
          </>
        )}
      </main>
      <footer className="border-t border-line">
        <div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-12 text-sm text-muted sm:flex-row sm:items-center sm:justify-between sm:px-8">
          <div className="flex items-center gap-2.5">
            <Logo />
            <span>
              Built by Utsav with Claude Code and Codex. Every number here comes from saved API runs.
            </span>
          </div>
          <div className="flex gap-5">
            <a className="hover:text-fg" href="https://github.com/UtsavInTech/upgrade-gate">
              GitHub
            </a>
            <a
              className="hover:text-fg"
              href="https://github.com/UtsavInTech/upgrade-gate/blob/main/findings/LOG.md"
            >
              Findings log
            </a>
            {site && <span className="text-faint">Data exported {site.generated_utc.slice(0, 10)}</span>}
          </div>
        </div>
      </footer>
    </MotionConfig>
  );
}
