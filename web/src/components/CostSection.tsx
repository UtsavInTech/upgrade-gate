import { motion } from "motion/react";
import type { E3 } from "../data";
import { pts, shortModel } from "../data";
import { Reveal, Section, Verdict } from "./ui";

export function CostSection({ e3 }: { e3: E3 }) {
  if (e3.status !== "done" || !e3.cost_per_1000 || !e3.standard || !e3.contributor) {
    return (
      <Section id="cost" eyebrow="Contributor mode" title="Cost comparison is still running.">
        <p className="text-muted">This section fills in when the saved run is exported.</p>
      </Section>
    );
  }
  const std = e3.cost_per_1000[e3.standard];
  const con = e3.cost_per_1000[e3.contributor];
  const ratio = Math.round(std / con);
  const rows = [
    { id: e3.standard, label: shortModel(e3.standard) + " Standard", cost: std },
    { id: e3.contributor, label: "Spark 1.3 Contributor", cost: con },
  ];
  const tally = e3.per_answer ?? {};

  return (
    <Section
      id="cost"
      eyebrow="Contributor mode · 7,950 calls"
      title={
        <>
          Same answers, <span className="text-go">1/{ratio}</span> of the cost.
        </>
      }
      lede={
        <>
          Contributor mode serves the same Spark 1.3 at a lower price, in exchange for letting Meta learn from
          the traffic. On our 1,325 tasks it gave exactly the same results. For synthetic or public data that
          is a free saving; for customer data it is a policy decision.
        </>
      }
    >
      <Reveal className="grid gap-10 lg:grid-cols-[minmax(0,7fr)_minmax(0,5fr)]">
        <figure className="rounded-lg border border-line p-6 sm:p-8">
          <figcaption className="mb-6">
            <h3 className="text-lg font-semibold">Cost per 1,000 tasks</h3>
            <p className="text-sm text-muted">
              Measured from billed tokens in this run, reasoning effort low
            </p>
          </figcaption>
          <ul className="space-y-6">
            {rows.map((r, k) => (
              <li key={r.id}>
                <div className="mb-2 flex items-baseline justify-between text-sm">
                  <span className="font-medium">{r.label}</span>
                  <span className="text-lg font-semibold">${r.cost.toFixed(2)}</span>
                </div>
                <div className="h-9 rounded-[6px] bg-surface">
                  <motion.div
                    className="h-full rounded-[4px] bg-[var(--s-correct)]"
                    initial={{ width: 0 }}
                    whileInView={{ width: `${Math.max(1.5, (r.cost / std) * 100)}%` }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.8, delay: 0.15 * k, ease: [0.2, 0.7, 0.2, 1] }}
                  />
                </div>
              </li>
            ))}
          </ul>
        </figure>

        <div className="flex flex-col justify-between gap-6 rounded-lg bg-surface p-6 sm:p-8">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold">Quality gate</h3>
            <Verdict decision={e3.decision ?? "inconclusive"} />
          </div>
          <dl className="space-y-4">
            {rows.map((r) => (
              <div key={r.id} className="flex items-baseline justify-between gap-4">
                <dt className="text-muted">{r.label}</dt>
                <dd className="font-semibold whitespace-nowrap">
                  {tally[r.id]?.correct.toLocaleString("en-IN")} /{" "}
                  {tally[r.id]?.total.toLocaleString("en-IN")} correct
                </dd>
              </div>
            ))}
            <div className="flex items-baseline justify-between gap-4 border-t border-line pt-4">
              <dt className="text-muted">Difference on every slice</dt>
              <dd className="font-semibold">{e3.overall ? pts(e3.overall.delta) : "–"} pts</dd>
            </div>
          </dl>
          <p className="text-sm text-muted">
            The Standard answers were reused from the first experiment, so this comparison cost $
            {(e3.fresh_cost_usd ?? 0).toFixed(2)}.
          </p>
        </div>
      </Reveal>
    </Section>
  );
}
