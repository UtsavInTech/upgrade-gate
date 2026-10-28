import { MotionConfig } from "motion/react";
import { useCallback, useEffect, useState } from "react";
import { Audit } from "./components/Audit";
import { VoiceOrder } from "./components/VoiceOrder";
import { AudioSection } from "./components/AudioSection";
import { CostSection } from "./components/CostSection";
import { EffortSection } from "./components/EffortSection";
import { Header, Logo } from "./components/Header";
import { Hero } from "./components/Hero";
import { HowSection } from "./components/HowSection";
import { Record } from "./components/Record";
import { Report } from "./components/Report";
import { ScoringSection } from "./components/ScoringSection";
import type { Site } from "./data";
import { loadSite } from "./data";

type Theme = "light" | "dark";
export type Route =
  | { page: "home" }
  | { page: "report"; run: string; task: string | null }
  | { page: "record"; set: "main" | "corrections" }
  | { page: "audit" }
  | { page: "voiceorder" };

function initialTheme(): Theme {
  const set = document.documentElement.dataset.theme;
  if (set === "light" || set === "dark") return set;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

// Hash routes keep the static build working from any folder: #/report/<run>, #/record.
// Plain anchors like #audio stay on the home page.
function parseRoute(): Route {
  const h = window.location.hash;
  const m = h.match(/^#\/report(?:\/([\w-]+))?(?:\/([\w-]+))?/);
  if (m) return { page: "report", run: m[1] ?? "e6-audio", task: m[2] ?? null };
  if (h.startsWith("#/record")) return { page: "record", set: h.startsWith("#/record/corrections") ? "corrections" : "main" };
  if (h.startsWith("#/audit")) return { page: "audit" };
  if (h.startsWith("#/voiceorder")) return { page: "voiceorder" };
  return { page: "home" };
}

export default function App() {
  const [site, setSite] = useState<Site | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [theme, setTheme] = useState<Theme>(initialTheme);
  const [route, setRoute] = useState<Route>(parseRoute);

  useEffect(() => {
    loadSite().then(setSite, (e: Error) => setError(e.message));
  }, []);

  useEffect(() => {
    const onHash = () => {
      const next = parseRoute();
      setRoute((prev) => {
        if (
          prev.page !== next.page ||
          (next.page === "report" && prev.page === "report" && prev.run !== next.run)
        ) {
          window.scrollTo(0, 0);
        }
        return next;
      });
    };
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  const toggleTheme = useCallback(() => {
    setTheme((t) => {
      const next = t === "dark" ? "light" : "dark";
      document.documentElement.dataset.theme = next;
      try {
        localStorage.setItem("ug-theme", next);
      } catch {
        /* private mode: the theme just isn't remembered */
      }
      return next;
    });
  }, []);

  return (
    <MotionConfig reducedMotion="user">
      <Header theme={theme} onToggleTheme={toggleTheme} route={route} />
      <main>
        {route.page === "report" && <Report run={route.run} task={route.task} />}
        {route.page === "record" && <Record key={route.set} set={route.set} />}
        {route.page === "audit" && <Audit />}
        {route.page === "voiceorder" && <VoiceOrder />}
        {route.page === "home" && (
          <>
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
                <AudioSection e6={site.e6} e7={site.e7} />
                {site.e4?.status === "done" && <EffortSection e4={site.e4} />}
                <ScoringSection e1={site.e1} />
                <CostSection e3={site.e3} />
                <HowSection />
              </>
            )}
          </>
        )}
      </main>
      {route.page === "home" && (
        <footer className="border-t border-line">
          <div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-12 text-sm text-muted sm:flex-row sm:items-center sm:justify-between sm:px-8">
            <div className="flex items-center gap-2.5">
              <Logo />
              <span>Upgrade Gate. Every number on this page comes from saved API runs.</span>
            </div>
            <div className="flex gap-5">
              <a className="hover:text-fg" href="#/report/e6-audio">
                Report
              </a>
              <a className="hover:text-fg" href="https://github.com/UtsavInTech/upgrade-gate">
                GitHub
              </a>
              <a
                className="hover:text-fg"
                href="https://github.com/UtsavInTech/upgrade-gate/blob/main/findings/LOG.md"
              >
                Findings log
              </a>
            </div>
          </div>
        </footer>
      )}
    </MotionConfig>
  );
}
