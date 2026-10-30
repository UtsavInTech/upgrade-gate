import { motion, useScroll, useSpring } from "motion/react";
import { Moon, Sun } from "lucide-react";
import type { Route } from "../App";

const NAV = [
  { href: "#audio", label: "Voice notes" },
  { href: "#effort", label: "Effort" },
  { href: "#scoring", label: "Scoring" },
  { href: "#cost", label: "Cost" },
  { href: "#compare", label: "Compare" },
  { href: "#how", label: "How it works" },
];

export function Logo() {
  // Two posts and a bar: a gate.
  return (
    <svg viewBox="0 0 28 28" className="size-7" aria-hidden>
      <rect x="4" y="5" width="4" height="18" rx="2" fill="var(--accent)" />
      <rect x="20" y="5" width="4" height="18" rx="2" fill="var(--accent)" />
      <rect x="8" y="11" width="12" height="3.5" rx="1.75" fill="var(--fg)" />
    </svg>
  );
}

export function Header({
  theme,
  onToggleTheme,
  route,
}: {
  theme: "light" | "dark";
  onToggleTheme: () => void;
  route: Route;
}) {
  const { scrollYProgress } = useScroll();
  const progress = useSpring(scrollYProgress, { stiffness: 140, damping: 30, mass: 0.3 });
  const home = route.page === "home";
  return (
    <header className="sticky top-0 z-40 border-b border-line bg-bg/90 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center gap-6 px-4 sm:px-8">
        <a href="#/" className="flex items-center gap-2.5 font-semibold tracking-tight">
          <Logo />
          <span className="text-[17px] whitespace-nowrap">Upgrade Gate</span>
        </a>
        <nav aria-label="Sections" className="ml-4 hidden items-center gap-1 lg:flex">
          {home ? (
            NAV.map((n) => (
              <a
                key={n.href}
                href={n.href}
                className="rounded-md px-3 py-2 text-sm whitespace-nowrap text-muted transition-colors hover:text-fg"
              >
                {n.label}
              </a>
            ))
          ) : (
            <a href="#/" className="rounded-md px-3 py-2 text-sm text-muted transition-colors hover:text-fg">
              Findings
            </a>
          )}
        </nav>
        <div className="ml-auto flex items-center gap-2">
          <a
            href="#/voiceorder"
            className="hidden rounded-md px-3 py-2 text-sm font-medium whitespace-nowrap text-fg transition-colors hover:bg-surface sm:inline-block"
          >
            VoiceOrder app
          </a>
          {route.page !== "report" && (
            <a
              href="#/report/e6-audio"
              className="rounded-md bg-fg px-3.5 py-2 text-sm font-semibold whitespace-nowrap text-bg transition-opacity hover:opacity-90"
            >
              Open report
            </a>
          )}
          <button
            type="button"
            onClick={onToggleTheme}
            aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
            className="inline-flex size-9 items-center justify-center rounded-md border border-line text-muted transition-colors hover:text-fg"
          >
            {theme === "dark" ? (
              <Sun aria-hidden className="size-4" />
            ) : (
              <Moon aria-hidden className="size-4" />
            )}
          </button>
        </div>
      </div>
      {home && (
        <motion.div
          aria-hidden
          className="absolute bottom-[-1px] left-0 h-[2px] w-full origin-left bg-accent"
          style={{ scaleX: progress }}
        />
      )}
    </header>
  );
}
