import { useEffect } from "react";
import type { Site } from "../data";
import { AudioSection } from "./AudioSection";
import { CompareSection } from "./CompareSection";
import { CostSection } from "./CostSection";
import { EffortSection } from "./EffortSection";
import { HowSection } from "./HowSection";
import { SafeRouteSection } from "./SafeRouteSection";
import { ScoringSection } from "./ScoringSection";

/** Switches between the two halves of Evidence: the run explorer and the written findings. */
export function EvidenceTabs({ active }: { active: "runs" | "findings" }) {
  const tab = (key: "runs" | "findings", href: string, label: string) => (
    <a
      href={href}
      aria-current={active === key ? "page" : undefined}
      className={`rounded-md px-3 py-1.5 text-sm transition-colors duration-150 ${
        active === key ? "bg-card font-semibold text-fg shadow-sm" : "text-muted hover:text-fg"
      }`}
    >
      {label}
    </a>
  );
  return (
    <div className="flex flex-wrap items-center justify-between gap-3">
      <h1 className="text-2xl font-semibold tracking-tight">Evidence</h1>
      <nav aria-label="Evidence" className="flex gap-1 rounded-lg bg-surface p-1">
        {tab("runs", "#/report/e6-audio", "Runs and tasks")}
        {tab("findings", "#/findings", "Findings and methods")}
      </nav>
    </div>
  );
}

const SECTIONS = [
  ["#audio", "Voice notes"],
  ["#safe-route", "Safe route"],
  ["#effort", "Reasoning effort"],
  ["#scoring", "Scoring"],
  ["#cost", "Contributor mode"],
  ["#compare", "Compared with other tools"],
  ["#how", "How it works"],
];

export function Findings({ site }: { site: Site }) {
  // #/findings/<section> opens this page at that section (hash routes can't carry a plain #anchor too).
  useEffect(() => {
    const m = window.location.hash.match(/^#\/findings\/([\w-]+)/) ?? window.location.hash.match(/^#([\w-]+)$/);
    if (m) requestAnimationFrame(() => document.getElementById(m[1])?.scrollIntoView());
  }, []);
  return (
    <>
      <div className="mx-auto max-w-6xl px-4 pt-8 sm:px-8">
        <EvidenceTabs active="findings" />
        <nav aria-label="On this page" className="mt-6 flex flex-wrap gap-x-4 gap-y-2 text-sm">
          {SECTIONS.map(([href, label]) => (
            <a key={href} href={href} className="text-accent underline-offset-2 hover:underline">
              {label}
            </a>
          ))}
        </nav>
      </div>
      <AudioSection e6={site.e6} e7={site.e7} />
      <SafeRouteSection e9={site.e9} e6={site.e6} />
      {site.e4?.status === "done" && <EffortSection e4={site.e4} />}
      <ScoringSection e1={site.e1} />
      <CostSection e3={site.e3} />
      <CompareSection />
      <HowSection />
    </>
  );
}
