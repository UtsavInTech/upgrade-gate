import { motion } from "motion/react";
import { Reveal, Section } from "./ui";

const STEPS = [
  {
    title: "Same tasks",
    body: "Text, invoices, PDFs and voice clips with known answers, in English, Hindi and Hinglish.",
  },
  {
    title: "Both versions, 3 tries",
    body: "Every task goes to the old and new model three times, so we can see how much answers wobble.",
  },
  {
    title: "Fixed-rule scoring",
    body: "A correct answer and a correctly formatted answer are scored separately. No AI judge needed.",
  },
  {
    title: "Paired statistics",
    body: "Exact McNemar tests, bootstrap intervals and Holm correction across every slice.",
  },
  {
    title: "Decision + evidence",
    body: "GO, NO-GO or INCONCLUSIVE, with the failing answers and the cost of the run.",
  },
];

export function HowSection() {
  return (
    <Section
      id="how"
      eyebrow="How it works"
      title="A release check that fits in CI."
      lede="Every paid call reserves its worst-case cost first, and a lifetime spending cap stops runs before they go over budget."
    >
      <ol className="relative grid gap-8 md:grid-cols-5 md:gap-5">
        <motion.span
          aria-hidden
          className="absolute top-4 left-4 hidden h-px origin-left bg-accent md:block"
          style={{ right: "1rem" }}
          initial={{ scaleX: 0 }}
          whileInView={{ scaleX: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 1.1, ease: [0.2, 0.7, 0.2, 1] }}
        />
        {STEPS.map((s, i) => (
          <Reveal key={s.title} delay={0.12 * i} className="relative">
            <span className="relative z-10 flex size-8 items-center justify-center rounded-full border border-accent bg-bg font-mono text-sm text-accent">
              {i + 1}
            </span>
            <h3 className="mt-4 font-semibold">{s.title}</h3>
            <p className="mt-1.5 text-sm leading-relaxed text-muted">{s.body}</p>
          </Reveal>
        ))}
      </ol>

      <Reveal delay={0.1} className="mt-16 grid gap-6 lg:grid-cols-[minmax(0,7fr)_minmax(0,5fr)]">
        <pre className="overflow-x-auto rounded-lg bg-[#0d1117] p-6 font-mono text-[13px] leading-7 text-[#d6dde4]">
          <code>
            <span className="text-[#7d8a96]"># one command: run, score, gate, report</span>
            {"\n"}upgrade-gate all --packs audio-synth \{"\n"}
            {"    "}-b spark-1.2@low -c spark-1.3@low \{"\n"}
            {"    "}--budget 8 --yes{"\n\n"}
            <span className="text-[#7d8a96]"># exit code gates the deploy</span>
            {"\n"}
            <span className="text-[#4fc489]">0</span> GO{"   "}
            <span className="text-[#ff8069]">2</span> NO-GO{"   "}
            <span className="text-[#e6ad45]">3</span> INCONCLUSIVE
          </code>
        </pre>
        <ul className="space-y-4 text-muted">
          <li>
            <span className="font-semibold text-fg">Meta-specific by design.</span> Pins Muse Spark versions,
            compares Standard and Contributor serving, sweeps reasoning effort, and can use Muse Wonder or
            Spark Open as a judge.
          </li>
          <li>
            <span className="font-semibold text-fg">Cheap to rerun.</span> Answers are cached, so rescoring
            and new slices cost nothing. The three experiments here cost under $20 in total.
          </li>
          <li>
            <span className="font-semibold text-fg">Honest about limits.</span> A GO covers the tasks you
            tested, not every user. Small slices stay inconclusive instead of guessing.
          </li>
        </ul>
      </Reveal>
    </Section>
  );
}
