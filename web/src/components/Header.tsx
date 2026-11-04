import { Github, Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";
import type { Route } from "../App";

const REPO = "https://github.com/UtsavInTech/upgrade-gate";

export function Logo({ className = "size-7" }: { className?: string }) {
  return (
    <svg viewBox="0 0 64 64" className={`${className} text-accent`} aria-hidden>
      <path
        fill="currentColor"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
        d="M32 60.4 L21.2 57 L45.6 42.8 L46.8 41.2 L46.8 28.2 L50.8 28.2 L43.6 18.4 L36.2 28.2 L40.1 28.2 L40.1 38.8 L39.4 39.8 L11.6 54.3 L2.6 50.5 L2.6 16.2 L19.4 9.1 L19.4 41.8 L20.8 42.9 L31.1 37.4 L32 36 L32 5.4 L34.4 3.7 L61.4 14.7 L61.4 50.9 Z"
      />
    </svg>
  );
}

const NAV: { href: string; label: string; match: (r: Route) => boolean }[] = [
  { href: "#/", label: "Overview", match: (r) => r.page === "home" },
  { href: "#/voiceorder", label: "Try VoiceOrder", match: (r) => r.page === "voiceorder" },
  { href: "#/report/e6-audio", label: "Evidence", match: (r) => r.page === "report" || r.page === "findings" },
];

export function Header({
  theme,
  onToggleTheme,
  route,
}: {
  theme: "light" | "dark";
  onToggleTheme: () => void;
  route: Route;
}) {
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const on = () => setScrolled(window.scrollY > 8);
    on();
    window.addEventListener("scroll", on, { passive: true });
    return () => window.removeEventListener("scroll", on);
  }, []);
  const links = NAV.map((n) => {
    const active = n.match(route);
    return (
      <a
        key={n.href}
        href={n.href}
        aria-current={active ? "page" : undefined}
        className={`rounded-md px-3 py-2 text-sm whitespace-nowrap transition-colors duration-150 ${
          active ? "font-semibold text-fg underline decoration-2 decoration-accent underline-offset-[10px]" : "text-muted hover:text-fg"
        }`}
      >
        {n.label}
      </a>
    );
  });
  return (
    <header
      className={`sticky top-0 z-40 border-b transition-colors duration-300 ${
        scrolled ? "border-line bg-bg/85 backdrop-blur-lg" : "border-transparent bg-transparent"
      }`}
    >
      <div className="mx-auto flex h-16 max-w-6xl items-center gap-4 px-4 sm:px-8">
        <a href="#/" className="flex shrink-0 items-center gap-2.5" aria-label="Upgrade Gate, overview">
          <Logo />
          <span className="display text-[21px] whitespace-nowrap">
            Upgrade <em>Gate</em>
          </span>
        </a>
        <nav aria-label="Main" className="ml-4 hidden items-center gap-1 md:flex">
          {links}
        </nav>
        <div className="ml-auto flex items-center gap-1">
          <a
            href={REPO}
            className="inline-flex size-10 items-center justify-center rounded-md text-muted transition-colors hover:text-fg"
            aria-label="Source code on GitHub"
          >
            <Github aria-hidden className="size-[18px]" />
          </a>
          <button
            type="button"
            onClick={onToggleTheme}
            aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
            className="inline-flex size-10 items-center justify-center rounded-md text-muted transition-colors hover:text-fg"
          >
            {theme === "dark" ? <Sun aria-hidden className="size-[18px]" /> : <Moon aria-hidden className="size-[18px]" />}
          </button>
        </div>
      </div>
      <nav aria-label="Main" className="flex justify-between gap-1 border-t border-line px-2 py-1.5 md:hidden">
        {links}
      </nav>
    </header>
  );
}
