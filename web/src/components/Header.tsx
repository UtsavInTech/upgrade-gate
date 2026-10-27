import { motion, useScroll, useSpring } from "motion/react";
import { Moon, Presentation, Sun } from "lucide-react";

const NAV = [
  { href: "#audio", label: "Voice notes" },
  { href: "#scoring", label: "Scoring" },
  { href: "#cost", label: "Cost" },
  { href: "#how", label: "How it works" },
];

export function Logo() {
  // Two posts and a bar: a gate, drawn with the same stroke weight as the icons.
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
  onPresent,
}: {
  theme: "light" | "dark";
  onToggleTheme: () => void;
  onPresent: () => void;
}) {
  const { scrollYProgress } = useScroll();
  const progress = useSpring(scrollYProgress, { stiffness: 140, damping: 30, mass: 0.3 });
  return (
    <header className="sticky top-0 z-40 border-b border-line bg-bg/85 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center gap-6 px-4 sm:px-8">
        <a href="#top" className="flex items-center gap-2.5 font-semibold tracking-tight">
          <Logo />
          <span className="text-[17px]">Upgrade Gate</span>
        </a>
        <nav aria-label="Sections" className="ml-4 hidden items-center gap-1 md:flex">
          {NAV.map((n) => (
            <a
              key={n.href}
              href={n.href}
              className="rounded-md px-3 py-2 text-sm text-muted transition-colors hover:bg-surface hover:text-fg"
            >
              {n.label}
            </a>
          ))}
        </nav>
        <div className="ml-auto flex items-center gap-2">
          <button
            type="button"
            onClick={onPresent}
            className="hidden items-center gap-2 rounded-md border border-line px-3 py-2 text-sm font-medium transition-colors hover:bg-surface sm:inline-flex"
          >
            <Presentation aria-hidden className="size-4" />
            Present
          </button>
          <button
            type="button"
            onClick={onToggleTheme}
            aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
            className="inline-flex size-10 items-center justify-center rounded-md border border-line transition-colors hover:bg-surface"
          >
            {theme === "dark" ? (
              <Sun aria-hidden className="size-4" />
            ) : (
              <Moon aria-hidden className="size-4" />
            )}
          </button>
        </div>
      </div>
      <motion.div
        aria-hidden
        className="absolute bottom-[-1px] left-0 h-[2px] w-full origin-left bg-accent"
        style={{ scaleX: progress }}
      />
    </header>
  );
}
