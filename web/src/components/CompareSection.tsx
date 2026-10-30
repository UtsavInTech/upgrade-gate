import { Check, Minus } from "lucide-react";
import type { ReactNode } from "react";
import { Reveal, Section } from "./ui";

type Cell = string | boolean;

const COLUMNS = ["Model leaderboards", "Eval tools (Promptfoo, Braintrust)", "Upgrade Gate"];

// Each eval-tool cell says what those tools offer out of the box, not "No": most of this
// can be built on them with custom checks. Keep claims to what their docs show.
const ROWS: { feature: string; cells: [Cell, Cell, Cell] }[] = [
  { feature: "Whose tasks", cells: ["Public benchmarks", "Yours", "Yours"] },
  {
    feature: "What it reports",
    cells: ["A score per model", "Scores and pass rates, side by side", "How the failures change"],
  },
  {
    feature: "Separates blank, wrong-with-no-warning and “can’t answer”",
    cells: [false, "Possible with custom checks you write", "Built in, for every answer"],
  },
  {
    feature: "Paired tests, related items grouped, corrected across input types",
    cells: [false, "Score differences; the statistics are up to you", "Built in"],
  },
  {
    feature: "Release rule",
    cells: [false, "Pass/fail thresholds you set", "A policy file that says why, in plain words"],
  },
  {
    feature: "Fails the pull request",
    cells: [false, "Yes, in CI", "Yes, with the failing answers in the check"],
  },
];

function CellValue({ value }: { value: Cell }): ReactNode {
  if (value === true)
    return (
      <span className="inline-flex items-center gap-1.5 font-medium text-go">
        <Check aria-hidden className="size-4" />
        Yes
      </span>
    );
  if (value === false)
    return (
      <span className="inline-flex items-center gap-1.5 text-muted">
        <Minus aria-hidden className="size-4" />
        No
      </span>
    );
  return <>{value}</>;
}

export function CompareSection() {
  return (
    <Section
      id="compare"
      eyebrow="Why not a leaderboard or an eval tool?"
      title="They tell you which model scores higher. We tell you how it fails on your tasks."
      lede="Upgrade Gate is a decision layer for one model change: your tasks, how the answers fail, and a release policy that can stop the merge."
    >
      <Reveal className="overflow-hidden rounded-lg border border-line">
        {/* Phones: one card per feature, so the Upgrade Gate column is never off-screen. */}
        <ul className="divide-y divide-line sm:hidden">
          {ROWS.map((r) => (
            <li key={r.feature} className="p-5">
              <p className="mb-3 font-medium">{r.feature}</p>
              <dl className="space-y-2 text-sm">
                {COLUMNS.map((c, i) => (
                  <div key={c} className="flex items-baseline justify-between gap-4">
                    <dt className={i === 2 ? "font-semibold text-accent" : "text-muted"}>{c}</dt>
                    <dd className={`text-right ${i === 2 ? "font-medium text-fg" : "text-muted"}`}>
                      <CellValue value={r.cells[i]} />
                    </dd>
                  </div>
                ))}
              </dl>
            </li>
          ))}
        </ul>
        <table className="hidden w-full border-collapse text-left text-sm sm:table">
          <thead className="bg-surface">
            <tr>
              <th scope="col" className="px-5 py-4 font-medium">
                <span className="sr-only">Feature</span>
              </th>
              {COLUMNS.map((c, i) => (
                <th
                  key={c}
                  scope="col"
                  className={`px-5 py-4 font-semibold ${i === 2 ? "bg-accent/10 text-accent" : ""}`}
                >
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {ROWS.map((r) => (
              <tr key={r.feature} className="border-t border-line">
                <th scope="row" className="px-5 py-4 font-normal">
                  {r.feature}
                </th>
                {r.cells.map((v, i) => (
                  <td
                    key={i}
                    className={`px-5 py-4 ${i === 2 ? "bg-accent/5 font-medium text-fg" : "text-muted"}`}
                  >
                    <CellValue value={v} />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </Reveal>
      <p className="mt-6 text-sm text-muted">
        Eval tools do more than we do in many ways: dashboards, many model providers, tracing, team
        workflows. Upgrade Gate is narrower: one model change, and whether the way it fails got worse.
      </p>
      <p className="mt-2 text-sm text-muted">
        Already use Promptfoo? <code className="font-mono text-fg">upgrade-gate export</code> writes the
        failing cases as a Promptfoo config and pytest checks.
      </p>
    </Section>
  );
}
