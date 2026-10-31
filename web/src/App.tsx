import { MotionConfig } from "motion/react";
import { useCallback, useEffect, useState } from "react";
import { Audit } from "./components/Audit";
import { VoiceOrder } from "./components/VoiceOrder";
import { Findings } from "./components/Findings";
import { Header, Logo } from "./components/Header";
import { Overview } from "./components/Overview";
import { Record } from "./components/Record";
import { Report } from "./components/Report";
import type { Site } from "./data";
import { loadSite } from "./data";

type Theme = "light" | "dark";
export type Route =
  | { page: "home" }
  | { page: "report"; run: string; task: string | null }
  | { page: "findings" }
  | { page: "record"; set: "main" | "corrections" }
  | { page: "audit" }
  | { page: "voiceorder" };

function initialTheme(): Theme {
  const set = document.documentElement.dataset.theme;
  if (set === "light" || set === "dark") return set;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

// Hash routes keep the static build working from any folder: #/report/<run>/<task>, #/record, ...
// Plain anchors like #how stay on the page they belong to.
function parseRoute(): Route {
  const h = window.location.hash;
  const m = h.match(/^#\/report(?:\/([\w-]+))?(?:\/([\w-]+))?/);
  if (m) return { page: "report", run: m[1] ?? "e6-audio", task: m[2] ?? null };
  if (h.startsWith("#/evidence")) return { page: "report", run: "e6-audio", task: null };
  if (h.startsWith("#/findings")) return { page: "findings" };
  if (h.startsWith("#/record")) return { page: "record", set: h.startsWith("#/record/corrections") ? "corrections" : "main" };
  if (h.startsWith("#/audit")) return { page: "audit" };
  if (h.startsWith("#/voiceorder")) return { page: "voiceorder" };
  // Old section anchors from the long home page now live on the findings page.
  if (/^#(audio|effort|scoring|cost|compare|safe-route|how)$/.test(h)) return { page: "findings" };
  return { page: "home" };
}

const TITLES: Record<Route["page"], string> = {
  home: "Upgrade Gate",
  voiceorder: "Try VoiceOrder · Upgrade Gate",
  report: "Evidence · Upgrade Gate",
  findings: "Findings and methods · Upgrade Gate",
  record: "Record voice notes · Upgrade Gate",
  audit: "Label audit · Upgrade Gate",
};

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
        if (prev.page !== next.page || (next.page === "report" && prev.page === "report" && prev.run !== next.run)) {
          // Keep an in-page anchor (e.g. #how on the findings page) in view; otherwise start at the top.
          if (!/^#[a-z-]+$/.test(window.location.hash)) window.scrollTo(0, 0);
        }
        return next;
      });
    };
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  useEffect(() => {
    document.title = TITLES[route.page];
  }, [route.page]);

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

  const needsSite = route.page === "home" || route.page === "findings";

  return (
    <MotionConfig reducedMotion="user">
      <a
        href="#main"
        onClick={(e) => (e.preventDefault(), document.getElementById("main")?.focus())}
        className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-50 focus:rounded-md focus:bg-card focus:px-3 focus:py-2"
      >
        Skip to content
      </a>
      <Header theme={theme} onToggleTheme={toggleTheme} route={route} />
      <main id="main" tabIndex={-1} className="outline-none">
        {route.page === "report" && <Report run={route.run} task={route.task} />}
        {route.page === "record" && <Record key={route.set} set={route.set} />}
        {route.page === "audit" && <Audit />}
        {route.page === "voiceorder" && <VoiceOrder site={site} />}
        {needsSite && error && (
          <div className="mx-auto max-w-3xl px-4 py-32 text-center">
            <h1 className="text-2xl font-semibold">Couldn’t load the results</h1>
            <p className="mt-3 text-muted">
              {error}. Reload the page to try again.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="mt-6 rounded-md bg-fg px-4 py-2.5 text-sm font-semibold text-bg"
            >
              Retry
            </button>
          </div>
        )}
        {needsSite && !site && !error && (
          <div className="mx-auto max-w-6xl px-4 py-24 sm:px-8" aria-busy="true">
            <div className="h-12 w-2/3 animate-pulse rounded-lg bg-surface" />
            <div className="mt-6 h-64 animate-pulse rounded-lg bg-surface" />
          </div>
        )}
        {route.page === "home" && site && <Overview site={site} />}
        {route.page === "findings" && site && <Findings site={site} />}
      </main>
      <footer className="mt-16 border-t border-line">
        <div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-10 text-sm text-muted sm:flex-row sm:items-center sm:justify-between sm:px-8">
          <div className="flex items-center gap-2.5">
            <Logo className="size-5" />
            <span>Every number on this site comes from saved API runs.</span>
          </div>
          <nav aria-label="More" className="flex flex-wrap gap-x-5 gap-y-2">
            <a className="hover:text-fg" href="#/findings">
              Findings and methods
            </a>
            <a className="hover:text-fg" href="#/record">
              Record a note
            </a>
            <a className="hover:text-fg" href="#/audit">
              Label audit
            </a>
            <a className="hover:text-fg" href="https://github.com/UtsavInTech/upgrade-gate/blob/main/findings/LOG.md">
              Findings log
            </a>
            <a className="hover:text-fg" href="https://github.com/UtsavInTech/upgrade-gate">
              GitHub
            </a>
          </nav>
        </div>
      </footer>
    </MotionConfig>
  );
}
